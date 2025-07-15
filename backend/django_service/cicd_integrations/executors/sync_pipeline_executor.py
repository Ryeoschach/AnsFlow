"""
同步流水线执行器
专为Celery任务设计的同步版本，避免异步调用问题
"""
import time
import logging
import threading
from typing import Dict, Any, List, Set, Optional
from datetime import datetime
from django.utils import timezone
from django.db import transaction

from ..models import AtomicStep, PipelineExecution, StepExecution
from .execution_context import ExecutionContext
from .dependency_resolver import DependencyResolver, StepNode
from .sync_step_executor import SyncStepExecutor

# WebSocket通知支持
try:
    from realtime.notifications import WebSocketNotifier
    WEBSOCKET_AVAILABLE = True
except ImportError:
    logger.warning("WebSocket notifications not available - realtime app not configured")
    WEBSOCKET_AVAILABLE = False
    WebSocketNotifier = None

logger = logging.getLogger(__name__)

class SyncPipelineExecutionError(Exception):
    """同步流水线执行错误"""
    pass

class SyncPipelineExecutor:
    """同步流水线执行器"""
    
    def __init__(self):
        self.max_parallel_steps = 3  # 降低并行数以便调试
        self.step_timeout = 1800  # 单步超时时间（秒）
        self.check_interval = 2  # 状态检查间隔
        self.notifier = None  # WebSocket通知器
    
    def execute_pipeline(
        self,
        execution_id: int,
        steps_config: Optional[List[Dict[str, Any]]] = None,
        tool_config: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行完整流水线（同步版本）
        
        Args:
            execution_id: 流水线执行ID
            steps_config: 步骤配置列表（可选，会从数据库读取）
            tool_config: CI/CD工具配置
            parameters: 执行参数
        
        Returns:
            执行结果
        """
        pipeline_execution = None
        context = None
        
        try:
            # 初始化WebSocket通知器（暂时禁用以避免错误）
            # TODO: 修复WebSocket消息处理器错误后重新启用
            self.notifier = None
            # if WEBSOCKET_AVAILABLE and WebSocketNotifier:
            #     self.notifier = WebSocketNotifier(execution_id)
            #     self.notifier.send_execution_update('starting', {
            #         'message': '流水线执行开始准备'
            #     })
            
            # 获取流水线执行记录
            try:
                pipeline_execution = PipelineExecution.objects.get(id=execution_id)
            except PipelineExecution.DoesNotExist:
                raise SyncPipelineExecutionError(f"流水线执行记录不存在: {execution_id}")
            
            # 从数据库获取原子步骤配置
            if not steps_config:
                steps_config = self._get_steps_config_from_db(pipeline_execution)
            
            # 创建执行上下文
            context = ExecutionContext(
                execution_id=execution_id,
                pipeline_name=pipeline_execution.pipeline.name,
                trigger_type=pipeline_execution.trigger_type,
                triggered_by=pipeline_execution.triggered_by.username if pipeline_execution.triggered_by else "system",
                parameters=parameters or {},
                environment=self._build_environment(pipeline_execution, tool_config or {})
            )
            
            # 更新执行状态
            self._update_pipeline_status(pipeline_execution, 'running', context)
            
            # 发送WebSocket通知
            if self.notifier:
                self.notifier.send_execution_update('running', {
                    'pipeline_name': pipeline_execution.pipeline.name,
                    'total_steps': len(steps_config),
                    'message': f'开始执行流水线: {pipeline_execution.pipeline.name}'
                })
                self.notifier.send_log_update(f"开始执行流水线: {pipeline_execution.pipeline.name} (ID: {execution_id})")
            
            logger.info(f"开始执行流水线: {pipeline_execution.pipeline.name} (ID: {execution_id})")
            
            # 构建依赖图
            resolver = self._build_dependency_graph(steps_config)
            
            # 验证依赖关系
            validation_errors = resolver.validate_dependencies()
            if validation_errors:
                if self.notifier:
                    self.notifier.send_error_update(f"依赖关系验证失败: {', '.join(validation_errors)}")
                raise SyncPipelineExecutionError(f"依赖关系验证失败: {', '.join(validation_errors)}")
            
            # 执行流水线
            execution_result = self._execute_pipeline_steps(
                resolver, context, tool_config or {}
            )
            
            # 更新最终状态
            final_status = 'success' if execution_result['success'] else 'failed'
            self._update_pipeline_status(pipeline_execution, final_status, context)
            
            # 发送最终状态通知
            if self.notifier:
                self.notifier.send_execution_update(final_status, {
                    'total_steps': execution_result.get('total_steps', 0),
                    'successful_steps': execution_result.get('successful_steps', 0),
                    'failed_steps': execution_result.get('failed_steps', 0),
                    'execution_time': execution_result.get('execution_time', 0),
                    'message': f'流水线执行{final_status}: {pipeline_execution.pipeline.name}'
                })
                self.notifier.send_log_update(f"流水线执行完成: {pipeline_execution.pipeline.name} - {final_status}")
            
            logger.info(f"流水线执行完成: {pipeline_execution.pipeline.name} - {final_status}")
            
            return execution_result
        
        except Exception as e:
            logger.error(f"流水线执行异常: {str(e)}", exc_info=True)
            
            if pipeline_execution:
                self._update_pipeline_status(pipeline_execution, 'failed', context, str(e))
            
            return {
                'success': False,
                'error_message': str(e),
                'completed_steps': context.step_results if context else {},
                'execution_time': 0
            }
    
    def _get_steps_config_from_db(self, pipeline_execution: PipelineExecution) -> List[Dict[str, Any]]:
        """从数据库获取步骤配置"""
        # 首先尝试获取PipelineStep（新系统）
        pipeline_steps = pipeline_execution.pipeline.steps.all().order_by('order')
        
        steps_config = []
        for step in pipeline_steps:
            config = {
                'id': step.id,
                'name': step.name,
                'type': step.step_type,
                'order': step.order,
                'dependencies': [],  # PipelineStep暂时不支持依赖关系
                'config': step.environment_vars or {},  # 使用environment_vars作为config
                'timeout': getattr(step, 'timeout', 3600),  # 默认超时
                'retry_count': getattr(step, 'retry_count', 0),  # 默认不重试
                'conditions': {},
                'priority': step.order,
                'parallel_group': getattr(step, 'parallel_group', None)
            }
            steps_config.append(config)
        
        # 如果没有PipelineStep，则尝试获取AtomicStep（兼容性）
        if not steps_config:
            try:
                from cicd_integrations.models import AtomicStep
                atomic_steps = AtomicStep.objects.filter(
                    pipeline=pipeline_execution.pipeline
                ).order_by('order')
                
                for step in atomic_steps:
                    config = {
                        'id': step.id,
                        'name': step.name,
                        'type': step.step_type,
                        'order': step.order,
                        'dependencies': step.dependencies or [],
                        'config': step.config or {},
                        'timeout': step.timeout,
                        'retry_count': step.retry_count,
                        'conditions': {},
                        'priority': step.order
                    }
                    steps_config.append(config)
            except ImportError:
                # AtomicStep模型不存在，跳过
                pass
        
        logger.info(f"从数据库加载了 {len(steps_config)} 个步骤配置")
        return steps_config
    
    def _build_environment(
        self, 
        pipeline_execution: PipelineExecution,
        tool_config: Dict[str, Any]
    ) -> Dict[str, str]:
        """构建执行环境变量"""
        env = {
            'PIPELINE_ID': str(pipeline_execution.pipeline.id),
            'PIPELINE_NAME': pipeline_execution.pipeline.name,
            'EXECUTION_ID': str(pipeline_execution.id),
            'TRIGGER_TYPE': pipeline_execution.trigger_type,
            'BUILD_NUMBER': str(pipeline_execution.id),
            'CI': 'true',
            'ANSFLOW': 'true'
        }
        
        # 添加工具特定的环境变量
        if tool_config.get('tool_type') == 'jenkins':
            env.update({
                'JENKINS_URL': tool_config.get('base_url', ''),
                'BUILD_URL': f"{tool_config.get('base_url', '')}/job/{pipeline_execution.pipeline.name}/{pipeline_execution.id}/"
            })
        elif tool_config.get('tool_type') == 'gitlab':
            env.update({
                'GITLAB_CI': 'true',
                'CI_PROJECT_ID': tool_config.get('project_id', ''),
                'CI_PIPELINE_ID': str(pipeline_execution.id)
            })
        
        # 合并用户定义的环境变量
        if pipeline_execution.parameters:
            env.update(pipeline_execution.parameters.get('environment', {}))
        
        return env
    
    def _build_dependency_graph(
        self, 
        steps_config: List[Dict[str, Any]]
    ) -> DependencyResolver:
        """构建步骤依赖图"""
        resolver = DependencyResolver()
        
        # 首先建立名称到ID的映射
        name_to_id = {}
        for step_config in steps_config:
            step_name = step_config.get('name')
            step_id = step_config.get('id')
            if step_name and step_id:
                name_to_id[step_name] = step_id
        
        # 构建步骤节点
        for step_config in steps_config:
            step_id = step_config.get('id')
            step_name = step_config.get('name')
            
            # 解析依赖关系 - 将名称转换为ID
            dependencies = []
            for dep_name in step_config.get('dependencies', []):
                if dep_name in name_to_id:
                    dependencies.append(name_to_id[dep_name])
                else:
                    logger.warning(f"步骤 {step_name} 的依赖 {dep_name} 未找到对应的ID")
            
            # 创建步骤节点
            step_node = StepNode(
                step_id=step_id,
                step_name=step_name,
                step_type=step_config.get('type'),
                dependencies=dependencies,
                conditions=step_config.get('conditions', {}),
                parallel_group=step_config.get('parallel_group'),
                priority=step_config.get('priority', 0)
            )
            
            resolver.add_step(step_node)
        
        return resolver
    
    def _execute_pipeline_steps(
        self,
        resolver: DependencyResolver,
        context: ExecutionContext,
        tool_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行流水线步骤（同步版本）"""
        start_time = timezone.now()
        completed_steps: Set[int] = set()
        running_steps: Dict[int, threading.Thread] = {}
        failed_steps: Set[int] = set()
        
        # 统计信息
        total_steps = len(resolver.steps)
        successful_steps = 0
        
        try:
            while len(completed_steps) < total_steps:
                # 清理已完成的线程
                self._cleanup_completed_threads(running_steps, completed_steps, failed_steps, context)
                
                # 获取可以执行的步骤
                ready_steps = resolver.get_ready_steps(completed_steps, set(running_steps.keys()))
                
                if not ready_steps and not running_steps:
                    # 没有可执行的步骤，且没有正在运行的步骤
                    remaining_steps = total_steps - len(completed_steps)
                    if remaining_steps > 0:
                        logger.warning(f"检测到无法执行的步骤，可能存在依赖问题。剩余步骤: {remaining_steps}")
                    break
                
                # 启动新的步骤执行（控制并发数）
                while (ready_steps and len(running_steps) < self.max_parallel_steps):
                    step_id = ready_steps.pop(0)
                    
                    # 创建并启动线程
                    thread = threading.Thread(
                        target=self._execute_single_step_thread,
                        args=(step_id, resolver, context, tool_config),
                        name=f"Step-{step_id}"
                    )
                    thread.daemon = True
                    thread.start()
                    
                    running_steps[step_id] = thread
                    logger.info(f"启动步骤执行线程: {step_id}")
                
                # 等待检查间隔
                if running_steps:
                    time.sleep(self.check_interval)
                
                # 检查是否有失败的关键步骤需要停止流水线
                if self._should_stop_pipeline(resolver, failed_steps, context):
                    logger.warning("检测到关键步骤失败，停止流水线执行")
                    # 等待当前运行的步骤完成
                    self._wait_for_running_steps(running_steps)
                    break
            
            # 等待所有运行中的步骤完成
            self._wait_for_running_steps(running_steps)
            
            # 最终清理
            self._cleanup_completed_threads(running_steps, completed_steps, failed_steps, context)
            
            # 计算成功步骤数
            successful_steps = sum(
                1 for step_name, result in context.step_results.items()
                if result.get('status') == 'success'
            )
            
            execution_time = (timezone.now() - start_time).total_seconds()
            
            success = len(failed_steps) == 0 and successful_steps > 0
            
            return {
                'success': success,
                'total_steps': total_steps,
                'successful_steps': successful_steps,
                'failed_steps': len(failed_steps),
                'completed_steps': context.step_results,
                'execution_time': execution_time
            }
        
        except Exception as e:
            logger.error(f"流水线步骤执行异常: {str(e)}", exc_info=True)
            execution_time = (timezone.now() - start_time).total_seconds()
            
            return {
                'success': False,
                'error_message': str(e),
                'total_steps': total_steps,
                'successful_steps': successful_steps,
                'failed_steps': len(failed_steps),
                'completed_steps': context.step_results,
                'execution_time': execution_time
            }
    
    def _cleanup_completed_threads(
        self,
        running_steps: Dict[int, threading.Thread],
        completed_steps: Set[int],
        failed_steps: Set[int],
        context: ExecutionContext
    ):
        """清理已完成的线程"""
        completed_threads = []
        
        for step_id, thread in running_steps.items():
            if not thread.is_alive():
                completed_threads.append(step_id)
                
                # 检查步骤执行结果
                step_result = context.step_results.get(f"step_{step_id}")
                if step_result:
                    if step_result.get('status') == 'success':
                        completed_steps.add(step_id)
                        logger.info(f"步骤 {step_id} 执行成功")
                    else:
                        failed_steps.add(step_id)
                        logger.error(f"步骤 {step_id} 执行失败")
                else:
                    # 没有结果记录，可能是异常退出
                    failed_steps.add(step_id)
                    logger.error(f"步骤 {step_id} 没有执行结果，可能异常退出")
        
        # 移除已完成的线程
        for step_id in completed_threads:
            del running_steps[step_id]
    
    def _wait_for_running_steps(self, running_steps: Dict[int, threading.Thread]):
        """等待所有运行中的步骤完成"""
        for step_id, thread in running_steps.items():
            try:
                thread.join(timeout=self.step_timeout)
                if thread.is_alive():
                    logger.warning(f"步骤 {step_id} 执行超时")
            except Exception as e:
                logger.error(f"等待步骤 {step_id} 完成时出错: {str(e)}")
    
    def _execute_single_step_thread(
        self,
        step_id: int,
        resolver: DependencyResolver,
        context: ExecutionContext,
        tool_config: Dict[str, Any]
    ) -> None:
        """线程中执行单个步骤"""
        step_node = resolver.steps[step_id]
        step_key = f"step_{step_id}"
        
        try:
            logger.info(f"开始执行步骤: {step_node.step_name} (ID: {step_id})")
            
            # 发送步骤开始通知
            if self.notifier:
                self.notifier.send_step_update(step_node.step_name, 'running', {
                    'step_id': step_id,
                    'step_type': step_node.step_type,
                    'message': f'开始执行步骤: {step_node.step_name}'
                })
                self.notifier.send_log_update(f"[步骤] 开始执行: {step_node.step_name}", step_name=step_node.step_name)
            
            # 获取步骤对象
            try:
                # 首先尝试获取PipelineStep（新系统）
                from pipelines.models import PipelineStep
                pipeline_step = PipelineStep.objects.get(id=step_id)
                
                # 直接使用PipelineStep，不再创建AtomicStep
                step_obj = pipeline_step
                
            except (ImportError, PipelineStep.DoesNotExist):
                # 回退到AtomicStep（兼容性）
                try:
                    from cicd_integrations.models import AtomicStep
                    step_obj = AtomicStep.objects.get(id=step_id)
                except (ImportError, AtomicStep.DoesNotExist):
                    error_msg = f'步骤不存在: {step_id}'
                    logger.error(error_msg)
                    
                    # 发送失败通知
                    if self.notifier:
                        self.notifier.send_step_update(step_node.step_name, 'failed', {
                            'step_id': step_id,
                            'error_message': error_msg
                        })
                        self.notifier.send_log_update(f"[错误] {error_msg}", level='error', step_name=step_node.step_name)
                    
                    context.step_results[step_key] = {
                        'status': 'failed',
                        'error_message': error_msg,
                        'start_time': timezone.now().isoformat(),
                        'end_time': timezone.now().isoformat()
                    }
                    return
            
            # 创建步骤执行器
            step_executor = SyncStepExecutor(context)
            
            # 执行步骤
            result = step_executor.execute_step(step_obj, tool_config)
            
            # 保存结果
            context.step_results[step_key] = result
            
            # 发送步骤完成通知
            final_status = result.get('status', 'unknown')
            if self.notifier:
                self.notifier.send_step_update(step_node.step_name, final_status, {
                    'step_id': step_id,
                    'execution_time': result.get('execution_time', 0),
                    'output': result.get('output', ''),
                    'error_message': result.get('error_message')
                })
                
                if final_status == 'success':
                    self.notifier.send_log_update(
                        f"[步骤] 执行成功: {step_node.step_name} ({result.get('execution_time', 0):.2f}s)",
                        step_name=step_node.step_name
                    )
                else:
                    self.notifier.send_log_update(
                        f"[步骤] 执行失败: {step_node.step_name} - {result.get('error_message', 'Unknown error')}",
                        level='error',
                        step_name=step_node.step_name
                    )
            
            logger.info(f"步骤执行完成: {step_node.step_name} - {final_status}")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"步骤执行异常: {step_node.step_name} - {error_msg}", exc_info=True)
            
            # 发送异常通知
            if self.notifier:
                self.notifier.send_step_update(step_node.step_name, 'failed', {
                    'step_id': step_id,
                    'error_message': error_msg
                })
                self.notifier.send_log_update(
                    f"[异常] 步骤执行异常: {step_node.step_name} - {error_msg}",
                    level='error',
                    step_name=step_node.step_name
                )
            
            context.step_results[step_key] = {
                'status': 'failed',
                'error_message': error_msg,
                'start_time': timezone.now().isoformat(),
                'end_time': timezone.now().isoformat()
            }
    
    def _should_stop_pipeline(
        self,
        resolver: DependencyResolver,
        failed_steps: Set[int],
        context: ExecutionContext
    ) -> bool:
        """检查是否应该停止流水线执行"""
        # 如果有任何步骤失败，暂停执行（可以后续改为更智能的策略）
        return len(failed_steps) > 0
    
    def _update_pipeline_status(
        self,
        pipeline_execution: PipelineExecution,
        status: str,
        context: Optional[ExecutionContext] = None,
        error_message: Optional[str] = None
    ):
        """更新流水线执行状态"""
        try:
            with transaction.atomic():
                pipeline_execution.status = status
                pipeline_execution.updated_at = timezone.now()
                
                if status == 'running':
                    pipeline_execution.started_at = timezone.now()
                elif status in ['success', 'failed']:
                    pipeline_execution.completed_at = timezone.now()
                    if context:
                        pipeline_execution.result = context.step_results
                
                if error_message:
                    if not pipeline_execution.result:
                        pipeline_execution.result = {}
                    pipeline_execution.result['error_message'] = error_message
                
                pipeline_execution.save()
                
                logger.info(f"更新流水线状态: {pipeline_execution.id} -> {status}")
                
        except Exception as e:
            logger.error(f"更新流水线状态失败: {str(e)}")
