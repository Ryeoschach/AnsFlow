"""
流水线执行器
负责整个流水线的执行编排、依赖管理、并行执行等
"""
import asyncio
import logging
from typing import Dict, Any, List, Set, Optional
from datetime import datetime
from django.utils import timezone
from asgiref.sync import sync_to_async

from ..models import AtomicStep, PipelineExecution, CICDTool
from .execution_context import ExecutionContext
from .dependency_resolver import DependencyResolver, StepNode
from .step_executor import StepExecutor

logger = logging.getLogger(__name__)

class PipelineExecutionError(Exception):
    """流水线执行错误"""
    pass

class PipelineExecutor:
    """流水线执行器"""
    
    def __init__(self):
        self.max_parallel_steps = 5  # 最大并行步骤数
        self.step_timeout = 3600  # 单步超时时间（秒）
    
    async def execute_pipeline(
        self,
        execution_id: int,
        steps_config: List[Dict[str, Any]],
        tool_config: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行完整流水线
        
        Args:
            execution_id: 流水线执行ID
            steps_config: 步骤配置列表
            tool_config: CI/CD工具配置
            parameters: 执行参数
        
        Returns:
            执行结果
        """
        pipeline_execution = None
        context = None
        
        try:
            # 获取流水线执行记录
            pipeline_execution = await sync_to_async(PipelineExecution.objects.get)(
                id=execution_id
            )
            
            # 创建执行上下文
            context = ExecutionContext(
                execution_id=execution_id,
                pipeline_name=pipeline_execution.pipeline.name,
                trigger_type=pipeline_execution.trigger_type,
                triggered_by=pipeline_execution.triggered_by.username if pipeline_execution.triggered_by else None,
                parameters=parameters or {},
                environment=self._build_environment(pipeline_execution, tool_config)
            )
            
            # 更新执行状态
            await self._update_pipeline_status(pipeline_execution, 'running', context)
            
            logger.info(f"开始执行流水线: {pipeline_execution.pipeline.name} (ID: {execution_id})")
            
            # 构建依赖图
            resolver = await self._build_dependency_graph(steps_config)
            
            # 验证依赖关系
            validation_errors = resolver.validate_dependencies()
            if validation_errors:
                raise PipelineExecutionError(f"依赖关系验证失败: {', '.join(validation_errors)}")
            
            # 执行流水线
            execution_result = await self._execute_pipeline_steps(
                resolver, context, tool_config
            )
            
            # 更新最终状态
            final_status = 'success' if execution_result['success'] else 'failed'
            await self._update_pipeline_status(pipeline_execution, final_status, context)
            
            logger.info(f"流水线执行完成: {pipeline_execution.pipeline.name} - {final_status}")
            
            return execution_result
        
        except Exception as e:
            logger.error(f"流水线执行异常: {str(e)}")
            
            if pipeline_execution:
                await self._update_pipeline_status(pipeline_execution, 'failed', context, str(e))
            
            return {
                'success': False,
                'error_message': str(e),
                'completed_steps': context.step_results if context else {},
                'execution_time': 0
            }
    
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
    
    async def _build_dependency_graph(
        self, 
        steps_config: List[Dict[str, Any]]
    ) -> DependencyResolver:
        """构建步骤依赖图"""
        resolver = DependencyResolver()
        
        # 收集步骤ID映射
        step_id_map = {}
        
        for i, step_config in enumerate(steps_config):
            step_id = step_config.get('id')
            if step_id is None:
                step_id = i + 1  # 使用索引作为ID
            
            step_id_map[step_config.get('name', f'step_{i}')] = step_id
        
        # 构建步骤节点
        for i, step_config in enumerate(steps_config):
            step_id = step_id_map.get(step_config.get('name', f'step_{i}'), i + 1)
            
            # 解析依赖关系
            dependencies = []
            if 'dependencies' in step_config:
                for dep_name in step_config['dependencies']:
                    if dep_name in step_id_map:
                        dependencies.append(step_id_map[dep_name])
            
            # 创建步骤节点
            step_node = StepNode(
                step_id=step_id,
                step_name=step_config.get('name', f'step_{i}'),
                step_type=step_config.get('type', 'custom'),
                dependencies=dependencies,
                conditions=step_config.get('conditions', {}),
                parallel_group=step_config.get('parallel_group'),
                priority=step_config.get('priority', 0)
            )
            
            resolver.add_step(step_node)
        
        return resolver
    
    async def _execute_pipeline_steps(
        self,
        resolver: DependencyResolver,
        context: ExecutionContext,
        tool_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行流水线步骤"""
        start_time = timezone.now()
        completed_steps: Set[int] = set()
        running_steps: Set[int] = set()
        failed_steps: Set[int] = set()
        
        # 统计信息
        total_steps = len(resolver.steps)
        successful_steps = 0
        
        try:
            while len(completed_steps) < total_steps:
                # 获取可以执行的步骤
                ready_steps = resolver.get_ready_steps(completed_steps, running_steps)
                
                if not ready_steps and not running_steps:
                    # 没有可执行的步骤，且没有正在运行的步骤
                    remaining_steps = total_steps - len(completed_steps)
                    if remaining_steps > 0:
                        logger.warning(f"检测到无法执行的步骤，可能存在依赖问题。剩余步骤: {remaining_steps}")
                    break
                
                # 启动新的步骤执行（控制并发数）
                while (ready_steps and 
                       len(running_steps) < self.max_parallel_steps):
                    
                    step_id = ready_steps.pop(0)
                    running_steps.add(step_id)
                    
                    # 异步执行步骤
                    asyncio.create_task(
                        self._execute_single_step(
                            step_id, resolver, context, tool_config,
                            completed_steps, running_steps, failed_steps
                        )
                    )
                
                # 等待至少一个步骤完成
                if running_steps:
                    await asyncio.sleep(1)  # 检查间隔
                
                # 检查是否有失败的关键步骤需要停止流水线
                if await self._should_stop_pipeline(resolver, failed_steps, context):
                    logger.warning("检测到关键步骤失败，停止流水线执行")
                    break
            
            # 等待所有运行中的步骤完成
            while running_steps:
                await asyncio.sleep(1)
            
            # 计算成功步骤数
            successful_steps = sum(
                1 for step_name, result in context.step_results.items()
                if result['status'] == 'success'
            )
            
            execution_time = (timezone.now() - start_time).total_seconds()
            
            success = len(failed_steps) == 0 and successful_steps > 0
            
            return {
                'success': success,
                'total_steps': total_steps,
                'successful_steps': successful_steps,
                'failed_steps': len(failed_steps),
                'completed_steps': context.step_results,
                'execution_time': execution_time,
                'critical_path': resolver.get_critical_path()
            }
        
        except Exception as e:
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
    
    async def _execute_single_step(
        self,
        step_id: int,
        resolver: DependencyResolver,
        context: ExecutionContext,
        tool_config: Dict[str, Any],
        completed_steps: Set[int],
        running_steps: Set[int],
        failed_steps: Set[int]
    ) -> None:
        """执行单个步骤"""
        step_node = resolver.steps[step_id]
        
        try:
            # 获取原子步骤对象
            atomic_step = await self._get_atomic_step_by_name(step_node.step_name)
            if not atomic_step:
                logger.error(f"未找到原子步骤: {step_node.step_name}")
                failed_steps.add(step_id)
                return
            
            # 创建步骤执行器
            step_executor = StepExecutor(context)
            
            # 执行步骤
            result = await asyncio.wait_for(
                step_executor.execute_step(atomic_step, tool_config),
                timeout=self.step_timeout
            )
            
            # 处理执行结果
            if result['status'] == 'success':
                logger.info(f"步骤执行成功: {step_node.step_name}")
            elif result['status'] == 'skipped':
                logger.info(f"步骤被跳过: {step_node.step_name}")
            else:
                logger.error(f"步骤执行失败: {step_node.step_name} - {result.get('error_message', '')}")
                failed_steps.add(step_id)
        
        except asyncio.TimeoutError:
            logger.error(f"步骤执行超时: {step_node.step_name}")
            failed_steps.add(step_id)
            context.set_step_result(step_node.step_name, {
                'status': 'failed',
                'error_message': '执行超时',
                'started_at': timezone.now(),
                'completed_at': timezone.now(),
            })
        
        except Exception as e:
            logger.error(f"步骤执行异常: {step_node.step_name} - {str(e)}")
            failed_steps.add(step_id)
            context.set_step_result(step_node.step_name, {
                'status': 'failed',
                'error_message': str(e),
                'started_at': timezone.now(),
                'completed_at': timezone.now(),
            })
        
        finally:
            # 从运行列表中移除，添加到完成列表
            running_steps.discard(step_id)
            completed_steps.add(step_id)
    
    async def _get_atomic_step_by_name(self, step_name: str) -> Optional[AtomicStep]:
        """根据名称获取原子步骤"""
        try:
            return await sync_to_async(AtomicStep.objects.get)(name=step_name)
        except AtomicStep.DoesNotExist:
            return None
    
    async def _should_stop_pipeline(
        self,
        resolver: DependencyResolver,
        failed_steps: Set[int],
        context: ExecutionContext
    ) -> bool:
        """判断是否应该停止流水线执行"""
        if not failed_steps:
            return False
        
        # 检查失败的步骤是否是关键路径上的步骤
        critical_path = resolver.get_critical_path()
        
        for failed_step_id in failed_steps:
            if failed_step_id in critical_path:
                logger.warning(f"关键路径上的步骤失败: {failed_step_id}")
                return True
        
        # 检查是否配置了"失败时停止"
        stop_on_failure = context.get_parameter('stop_on_failure', True)
        if stop_on_failure:
            return True
        
        return False
    
    async def _update_pipeline_status(
        self,
        pipeline_execution: PipelineExecution,
        status: str,
        context: Optional[ExecutionContext] = None,
        error_message: str = ''
    ) -> None:
        """更新流水线执行状态"""
        pipeline_execution.status = status
        
        if status == 'running' and not pipeline_execution.started_at:
            pipeline_execution.started_at = timezone.now()
            if context:
                context.status = 'running'
                context.started_at = timezone.now()
        
        elif status in ['success', 'failed', 'cancelled']:
            pipeline_execution.completed_at = timezone.now()
            if context:
                context.status = status
                context.completed_at = timezone.now()
        
        if error_message:
            pipeline_execution.logs = (pipeline_execution.logs or '') + f"\n{error_message}"
        
        # 保存执行上下文
        if context:
            pipeline_execution.metadata = pipeline_execution.metadata or {}
            pipeline_execution.metadata['execution_context'] = context.to_dict()
        
        await sync_to_async(pipeline_execution.save)()
    
    async def cancel_pipeline(self, execution_id: int) -> bool:
        """取消流水线执行"""
        try:
            pipeline_execution = await sync_to_async(PipelineExecution.objects.get)(
                id=execution_id
            )
            
            if pipeline_execution.status not in ['pending', 'running']:
                return False
            
            await self._update_pipeline_status(pipeline_execution, 'cancelled')
            logger.info(f"流水线执行已取消: {execution_id}")
            
            return True
        
        except PipelineExecution.DoesNotExist:
            logger.error(f"流水线执行不存在: {execution_id}")
            return False
        except Exception as e:
            logger.error(f"取消流水线执行失败: {execution_id} - {str(e)}")
            return False
    
    async def get_execution_progress(self, execution_id: int) -> Dict[str, Any]:
        """获取流水线执行进度"""
        try:
            pipeline_execution = await sync_to_async(PipelineExecution.objects.get)(
                id=execution_id
            )
            
            # 获取步骤执行统计
            from ..models import StepExecution
            step_executions = await sync_to_async(list)(
                StepExecution.objects.filter(pipeline_execution=pipeline_execution)
            )
            
            total_steps = len(step_executions)
            completed_steps = sum(
                1 for step in step_executions 
                if step.status in ['success', 'failed', 'skipped']
            )
            successful_steps = sum(
                1 for step in step_executions 
                if step.status == 'success'
            )
            
            progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
            
            return {
                'execution_id': execution_id,
                'status': pipeline_execution.status,
                'progress_percentage': round(progress_percentage, 2),
                'total_steps': total_steps,
                'completed_steps': completed_steps,
                'successful_steps': successful_steps,
                'failed_steps': total_steps - successful_steps,
                'started_at': pipeline_execution.started_at,
                'current_step': self._get_current_running_step(step_executions)
            }
        
        except PipelineExecution.DoesNotExist:
            return {'error': f'流水线执行不存在: {execution_id}'}
        except Exception as e:
            return {'error': f'获取执行进度失败: {str(e)}'}
    
    def _get_current_running_step(self, step_executions: List) -> Optional[str]:
        """获取当前正在执行的步骤"""
        for step in step_executions:
            if step.status == 'running':
                return step.atomic_step.name
        return None
