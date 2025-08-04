"""
统一的 CI/CD 执行引擎服务
"""
import logging
from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db import transaction
from celery import shared_task
from asgiref.sync import sync_to_async

from .models import CICDTool, PipelineExecution, StepExecution, AtomicStep
from .adapters import AdapterFactory, PipelineDefinition, ExecutionResult
from pipelines.models import Pipeline
from .executors import PipelineExecutor, ExecutionContext, DependencyResolver, StepExecutor
from .executors.sync_pipeline_executor import SyncPipelineExecutor

logger = logging.getLogger(__name__)


class UnifiedCICDEngine:
    """统一 CI/CD 执行引擎"""
    
    def __init__(self):
        self.active_executions: Dict[str, Any] = {}
    
    async def register_tool(self, tool_data: Dict[str, Any], user) -> CICDTool:
        """注册 CI/CD 工具"""
        try:
            tool = await sync_to_async(CICDTool.objects.create)(
                name=tool_data['name'],
                tool_type=tool_data['tool_type'],
                base_url=tool_data['base_url'],
                username=tool_data.get('username', ''),
                token=tool_data['token'],
                config=tool_data.get('config', {}),
                metadata=tool_data.get('metadata', {}),
                project_id=tool_data['project_id'],
                created_by=user
            )
            
            # 执行健康检查
            await self.health_check_tool(tool)
            
            logger.info(f"CI/CD tool registered: {tool.name} ({tool.tool_type})")
            return tool
        
        except Exception as e:
            logger.error(f"Failed to register CI/CD tool: {e}")
            raise
    
    async def health_check_tool(self, tool: CICDTool) -> bool:
        """检查工具健康状态"""
        try:
            adapter = AdapterFactory.create_adapter(
                tool.tool_type,
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            async with adapter:
                is_healthy = await adapter.health_check()
                
                # 更新健康检查时间和状态
                tool.last_health_check = timezone.now()
                tool.status = 'active' if is_healthy else 'error'
                await sync_to_async(tool.save)(update_fields=['last_health_check', 'status'])
                
                return is_healthy
        
        except Exception as e:
            logger.error(f"Health check failed for tool {tool.name}: {e}")
            tool.status = 'error'
            tool.last_health_check = timezone.now()
            await sync_to_async(tool.save)(update_fields=['last_health_check', 'status'])
            return False
    
    async def execute_pipeline(
        self,
        pipeline: Pipeline,
        tool: CICDTool,
        trigger_type: str = 'manual',
        triggered_by=None,
        parameters: Dict[str, Any] = None
    ) -> PipelineExecution:
        """在指定工具上执行流水线"""
        
        if parameters is None:
            parameters = {}
        
        try:
            # 创建执行记录
            execution = await sync_to_async(PipelineExecution.objects.create)(
                pipeline=pipeline,
                cicd_tool=tool,
                status='pending',
                trigger_type=trigger_type,
                triggered_by=triggered_by,
                definition=pipeline.config,
                parameters=parameters,
                trigger_data={
                    'timestamp': timezone.now().isoformat(),
                    'user': triggered_by.username if triggered_by else 'system'
                }
            )
            
            # 启动异步执行任务
            from .tasks import execute_pipeline_async
            execute_pipeline_async.delay(execution.id)
            
            logger.info(f"Pipeline execution started: {execution.id}")
            return execution
        
        except Exception as e:
            logger.error(f"Failed to start pipeline execution: {e}")
            raise
    
    async def execute_atomic_steps_locally(
        self,
        pipeline: Pipeline,
        trigger_type: str = 'manual',
        triggered_by=None,
        parameters: Dict[str, Any] = None
    ) -> PipelineExecution:
        """本地执行原子步骤（不依赖外部CI/CD工具）"""
        
        if parameters is None:
            parameters = {}
        
        try:
            # 创建执行记录
            execution = await sync_to_async(PipelineExecution.objects.create)(
                pipeline=pipeline,
                cicd_tool=None,  # 本地执行不需要外部工具
                status='pending',
                trigger_type=trigger_type,
                triggered_by=triggered_by,
                definition=pipeline.config,
                parameters=parameters,
                trigger_data={
                    'timestamp': timezone.now().isoformat(),
                    'user': triggered_by.username if triggered_by else 'system',
                    'execution_mode': 'local'
                }
            )
            
            # 启动异步执行任务
            from .tasks import execute_pipeline_async
            execute_pipeline_async.delay(execution.id)
            
            logger.info(f"Local pipeline execution started: {execution.id}")
            return execution
        
        except Exception as e:
            logger.error(f"Failed to start local pipeline execution: {e}")
            raise
    
    def _perform_execution(self, execution_id: int):
        """执行流水线的核心逻辑（同步版本供Celery使用）"""
        try:
            execution = PipelineExecution.objects.select_related(
                'pipeline', 'cicd_tool'
            ).get(id=execution_id)
            
            logger.info(f"Starting pipeline execution {execution_id}")
            logger.info(f"Pipeline execution mode: {execution.pipeline.execution_mode}")
            logger.info(f"Associated CI/CD tool: {execution.cicd_tool}")
            
            # 根据执行模式和工具类型决定执行方式
            if execution.cicd_tool and execution.cicd_tool.tool_type == 'local':
                # 本地执行器：直接执行原子步骤
                logger.info("Using local executor for execution")
                return self._perform_local_execution(execution)
            elif execution.pipeline.execution_mode == 'remote' and execution.cicd_tool:
                # 远程执行：在外部CI/CD工具上执行
                logger.info(f"Using remote execution mode with {execution.cicd_tool.tool_type}")
                return self._perform_remote_execution(execution)
            else:
                # 本地执行：直接执行原子步骤
                logger.info("Using local execution mode")
                return self._perform_local_execution(execution)
        
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            # 更新执行状态为失败
            try:
                execution = PipelineExecution.objects.get(id=execution_id)
                execution.status = 'failed'
                execution.completed_at = timezone.now()
                execution.logs = f"Execution failed: {str(e)}"
                execution.save()
            except Exception as save_error:
                logger.error(f"Failed to save error state: {save_error}")
    
    def _perform_local_execution(self, execution: PipelineExecution):
        """本地执行流水线步骤"""
        logger.info(f"Performing local execution for {execution.id}")
        
        # 获取流水线的PipelineStep
        pipeline_steps = list(
            execution.pipeline.steps.all().order_by('order')
        )
        
        # 获取流水线的AtomicStep（向后兼容）
        atomic_steps = list(
            execution.pipeline.atomic_steps.all().order_by('order')
        )
        
        # 检查是否有步骤
        if not pipeline_steps and not atomic_steps:
            logger.warning(f"No pipeline steps or atomic steps found for pipeline {execution.pipeline.id}")
            execution.status = 'failed'
            execution.completed_at = timezone.now()
            execution.logs = "No pipeline steps or atomic steps found in pipeline"
            execution.save()
            return
        
        logger.info(f"本地执行: 获取到 {len(pipeline_steps)} 个PipelineStep, {len(atomic_steps)} 个AtomicStep")
        
        # 检查并行组 - 同时检查PipelineStep和AtomicStep
        parallel_groups = set()
        
        # 检查PipelineStep的并行组
        for step in pipeline_steps:
            if step.parallel_group:
                parallel_groups.add(step.parallel_group)
                logger.info(f"PipelineStep '{step.name}': parallel_group = '{step.parallel_group}'")
        
        # 检查AtomicStep的并行组
        for step in atomic_steps:
            if step.parallel_group:
                parallel_groups.add(step.parallel_group)
                logger.info(f"AtomicStep '{step.name}': parallel_group = '{step.parallel_group}'")
        
        logger.info(f"本地执行: 检测到 {len(parallel_groups)} 个并行组")
        
        # 如果有并行组，使用我们的并行执行引擎
        if parallel_groups:
            logger.info(f"Using parallel execution engine for {len(parallel_groups)} parallel groups")
            
            # 导入并行执行服务
            from pipelines.services.parallel_execution import parallel_execution_service
            
            # 根据步骤类型选择合适的执行方法
            if pipeline_steps:
                # 有PipelineStep，使用新的执行方法
                logger.info("Using PipelineStep execution method")
                execution_plan = parallel_execution_service.analyze_pipeline_step_execution_plan(execution.pipeline)
                result = parallel_execution_service.execute_pipeline_step_with_parallel_support(
                    execution.pipeline,
                    execution,
                    execution_plan
                )
            else:
                # 只有AtomicStep，使用旧的执行方法
                logger.info("Using AtomicStep execution method")
                execution_plan = parallel_execution_service.analyze_pipeline_execution_plan(execution.pipeline)
                
                # 创建一个临时的PipelineRun对象来兼容接口
                class TempPipelineRun:
                    def __init__(self, pipeline_execution):
                        self.pipeline_execution = pipeline_execution
                        self.pipeline = pipeline_execution.pipeline
                        self.parameters = pipeline_execution.parameters
                        self.triggered_by = pipeline_execution.triggered_by
                        self.trigger_data = pipeline_execution.trigger_data
                
                temp_run = TempPipelineRun(execution)
                result = parallel_execution_service.execute_pipeline_with_parallel_support(
                    execution.pipeline,
                    temp_run,
                    execution_plan
                )
            
            # 更新执行状态
            if result.get('success', False):
                execution.status = 'success'
                execution.completed_at = timezone.now()
                execution.logs = f"Parallel execution completed successfully: {result.get('message', '')}"
            else:
                execution.status = 'failed'
                execution.completed_at = timezone.now()
                execution.logs = f"Parallel execution failed: {result.get('message', '')}"
            
            execution.save()
            
            logger.info(f"Parallel pipeline execution completed: {execution.id} - {execution.status}")
            return result
        
        else:
            # 没有并行组，也使用并行执行服务来确保失败中断功能
            logger.info(f"No parallel groups found, using parallel execution service for {len(pipeline_steps)} steps with failure interruption")
            
            # 导入并行执行服务
            from pipelines.services.parallel_execution import parallel_execution_service
            
            # 根据步骤类型选择合适的执行方法
            if pipeline_steps:
                # 有PipelineStep，使用新的执行方法
                logger.info("Using PipelineStep execution method with failure interruption")
                execution_plan = parallel_execution_service.analyze_pipeline_step_execution_plan(execution.pipeline)
                result = parallel_execution_service.execute_pipeline_step_with_parallel_support(
                    execution.pipeline,
                    execution,
                    execution_plan
                )
            else:
                # 只有AtomicStep，使用AtomicStep执行方法
                logger.info("Using AtomicStep execution method with failure interruption")
                execution_plan = parallel_execution_service.analyze_pipeline_execution_plan(execution.pipeline)
                
                # 创建一个临时的PipelineRun对象来兼容接口
                class TempPipelineRun:
                    def __init__(self, pipeline_execution):
                        self.pipeline_execution = pipeline_execution
                        self.pipeline = pipeline_execution.pipeline
                        self.parameters = pipeline_execution.parameters
                        self.triggered_by = pipeline_execution.triggered_by
                        self.trigger_data = pipeline_execution.trigger_data
                
                temp_run = TempPipelineRun(execution)
                result = parallel_execution_service.execute_pipeline_with_parallel_support(
                    execution.pipeline,
                    temp_run,
                    execution_plan
                )
            
            # 更新执行状态
            if result.get('success', False):
                execution.status = 'success'
                execution.completed_at = timezone.now()
                execution.logs = f"Sequential execution with failure interruption completed successfully: {result.get('message', '')}"
            else:
                execution.status = 'failed'
                execution.completed_at = timezone.now()
                execution.logs = f"Sequential execution with failure interruption failed: {result.get('message', '')}"
            
            execution.save()
            
            success = result.get('success', False)
            logger.info(f"Local pipeline execution with failure interruption completed: {execution.id} - {'success' if success else 'failed'}")
            return result
    
    def _perform_remote_execution(self, execution: PipelineExecution):
        """在外部CI/CD工具上执行流水线"""
        logger.info(f"Performing remote execution for {execution.id} using {execution.cicd_tool.tool_type}")
        
        try:
            # 创建适配器
            from .adapters import AdapterFactory
            adapter = AdapterFactory.create_adapter(
                execution.cicd_tool.tool_type,
                base_url=execution.cicd_tool.base_url,
                username=execution.cicd_tool.username,
                token=execution.cicd_tool.token,
                **execution.cicd_tool.config
            )
            
            # 构建流水线定义
            pipeline_definition = self._build_pipeline_definition_from_atomic_steps(execution)
            
            # 在外部工具上创建并执行流水线
            logger.info(f"Creating pipeline in {execution.cicd_tool.tool_type}")
            
            # 运行异步代码
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 创建并执行流水线
                result = loop.run_until_complete(self._async_remote_execution(adapter, execution, pipeline_definition))
                return result
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Remote execution failed for {execution.id}: {e}", exc_info=True)
            # 更新执行状态
            execution.status = 'failed'
            execution.completed_at = timezone.now()
            execution.logs = f"Remote execution failed: {str(e)}"
            execution.save()
            return {'success': False, 'error_message': str(e)}
    
    async def _async_remote_execution(self, adapter, execution: PipelineExecution, pipeline_definition):
        """异步执行远程流水线"""
        async with adapter:
            # 创建步骤执行记录（为原子步骤）
            await self._create_step_executions_for_remote(execution)
            
            # 先创建或更新流水线
            job_name = await adapter.create_pipeline(pipeline_definition)
            
            # 然后触发执行
            execution_result = await adapter.trigger_pipeline(pipeline_definition)
            
            if execution_result and execution_result.success:
                # 从执行结果中获取外部ID
                external_id = execution_result.external_id
                
                # 更新执行记录的外部ID
                execution.external_id = external_id
                execution.status = 'running'
                execution.started_at = timezone.now()
                await sync_to_async(execution.save)(update_fields=['external_id', 'status', 'started_at'])
                
                logger.info(f"Pipeline created and triggered in {execution.cicd_tool.tool_type} with external ID: {external_id}")
                
                # 启动监控任务（在后台异步监控）
                from .tasks import monitor_remote_execution
                monitor_remote_execution.delay(execution.id)
                
                return {'success': True, 'external_id': external_id}
            else:
                error_msg = execution_result.error if hasattr(execution_result, 'error') else execution_result.message if execution_result else "Unknown error"
                logger.error(f"Failed to start pipeline execution: {error_msg}")
                return {'success': False, 'error_message': error_msg}
    
    async def _create_step_executions_for_remote(self, execution: PipelineExecution):
        """为远程执行创建步骤执行记录"""
        # 获取原子步骤
        atomic_steps = await sync_to_async(list)(
            AtomicStep.objects.filter(
                pipeline=execution.pipeline
            ).order_by('order')
        )
        
        logger.info(f"Creating step execution records for {len(atomic_steps)} atomic steps")
        
        # 为每个原子步骤创建 StepExecution 记录
        for index, atomic_step in enumerate(atomic_steps):
            step_execution = await sync_to_async(StepExecution.objects.create)(
                pipeline_execution=execution,
                atomic_step=atomic_step,
                status='pending',
                order=index + 1
            )
            logger.debug(f"Created step execution record: {step_execution.id} for step {atomic_step.name}")
    
    def _build_pipeline_definition_from_atomic_steps(self, execution: PipelineExecution):
        """从流水线步骤构建流水线定义"""
        # 获取流水线步骤而不是原子步骤
        pipeline_steps = list(
            execution.pipeline.steps.all()
            .select_related('ansible_playbook', 'ansible_inventory', 'ansible_credential')
            .order_by('order')
        )
        
        logger.info(f"构建流水线定义: 获取到 {len(pipeline_steps)} 个PipelineStep")
        
        # 转换为流水线定义格式
        steps = []
        for pipeline_step in pipeline_steps:
            # 获取步骤的基本信息
            step = {
                'name': pipeline_step.name,
                'type': pipeline_step.step_type,
                'parameters': pipeline_step.environment_vars.copy() if pipeline_step.environment_vars else {},
                'description': pipeline_step.description or '',
                'parallel_group': pipeline_step.parallel_group or ''  # 添加并行组字段
            }
            
            # 添加command字段到parameters中，这样Jenkins适配器可以访问到
            if pipeline_step.command:
                step['parameters']['command'] = pipeline_step.command
                logger.info(f"步骤 '{pipeline_step.name}': 添加command = '{pipeline_step.command}'")
            
            logger.info(f"步骤 '{pipeline_step.name}': parallel_group = '{step['parallel_group']}'")
            
            # 对于ansible步骤，添加特殊的参数处理
            if pipeline_step.step_type == 'ansible':
                ansible_params = {}
                
                # 添加Ansible特有的参数
                if pipeline_step.ansible_playbook:
                    # 可以是playbook文件路径或内容
                    ansible_params['playbook_path'] = pipeline_step.ansible_playbook.name
                    ansible_params['playbook'] = pipeline_step.ansible_playbook.name
                
                if pipeline_step.ansible_inventory:
                    # inventory文件路径或内容
                    ansible_params['inventory_path'] = 'hosts'  # 默认inventory文件名
                    ansible_params['inventory'] = 'hosts'
                
                if pipeline_step.ansible_credential:
                    # 可以添加认证相关的环境变量或参数
                    ansible_params['ansible_user'] = pipeline_step.ansible_credential.username
                
                # 合并ansible特有参数到step参数中
                step['parameters'].update(ansible_params)
            
            steps.append(step)
        
        pipeline_definition = PipelineDefinition(
            name=execution.pipeline.name,
            steps=steps,
            triggers=execution.pipeline.config.get('triggers', {}) if execution.pipeline.config else {},
            environment=execution.parameters,
            artifacts=execution.pipeline.config.get('artifacts', []) if execution.pipeline.config else [],
            timeout=execution.pipeline.config.get('timeout', 3600) if execution.pipeline.config else 3600
        )
        
        logger.info(f"Built pipeline definition with {len(steps)} steps for {execution.pipeline.name}")
        return pipeline_definition
    
    def _build_pipeline_definition(self, execution: PipelineExecution) -> PipelineDefinition:
        """构建流水线定义（保留用于外部工具兼容性）"""
        pipeline_config = execution.definition
        
        # 从原子步骤构建步骤列表
        steps = []
        for step_config in pipeline_config.get('steps', []):
            step = {
                'name': step_config.get('name', 'Unknown Step'),
                'type': step_config.get('type', 'custom'),
                'parameters': step_config.get('parameters', {})
            }
            steps.append(step)
        
        return PipelineDefinition(
            name=execution.pipeline.name,
            steps=steps,
            triggers=pipeline_config.get('triggers', {}),
            environment=pipeline_config.get('environment', {}),
            artifacts=pipeline_config.get('artifacts', []),
            timeout=pipeline_config.get('timeout', 3600)
        )
    
    async def _monitor_execution(self, execution: PipelineExecution, adapter):
        """监控外部CI/CD工具的流水线执行状态"""
        max_checks = 360  # 最多检查6小时 (每分钟检查一次)
        check_count = 0
        
        while check_count < max_checks:
            try:
                status_data = await adapter.get_pipeline_status(execution.external_id)
                current_status = status_data.get('status', 'unknown')
                
                # 更新执行状态
                if current_status != execution.status:
                    execution.status = current_status
                    
                    if current_status in ['success', 'failed', 'cancelled']:
                        execution.completed_at = timezone.now()
                        
                        # 获取日志
                        try:
                            logs = await adapter.get_logs(execution.external_id)
                            execution.logs = logs
                        except Exception as e:
                            logger.warning(f"Failed to get logs: {e}")
                    
                    await sync_to_async(execution.save)()
                
                # 如果执行完成，退出监控
                if current_status in ['success', 'failed', 'cancelled', 'timeout']:
                    logger.info(f"Pipeline execution completed: {execution.id} - {current_status}")
                    break
                
                # 等待一分钟后再次检查
                import asyncio
                await asyncio.sleep(60)
                check_count += 1
            
            except Exception as e:
                logger.error(f"Error monitoring execution {execution.id}: {e}")
                check_count += 1
                import asyncio
                await asyncio.sleep(60)
        
        # 如果超时仍未完成，标记为超时
        if check_count >= max_checks:
            execution.status = 'timeout'
            execution.completed_at = timezone.now()
            await sync_to_async(execution.save)()
    
    async def cancel_execution(self, execution_id: int) -> bool:
        """取消流水线执行"""
        try:
            execution = await sync_to_async(PipelineExecution.objects.select_related)(
                'cicd_tool'
            ).aget(id=execution_id)
            
            if execution.status not in ['pending', 'running']:
                return False
            
            # 创建适配器并取消执行
            tool = execution.cicd_tool
            adapter = AdapterFactory.create_adapter(
                tool.tool_type,
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            async with adapter:
                success = await adapter.cancel_pipeline(execution.external_id)
                
                if success:
                    execution.status = 'cancelled'
                    execution.completed_at = timezone.now()
                    await sync_to_async(execution.save)()
                
                return success
        
        except Exception as e:
            logger.error(f"Failed to cancel execution {execution_id}: {e}")
            return False
    
    async def get_execution_logs(self, execution_id: int) -> str:
        """获取执行日志"""
        try:
            execution = await sync_to_async(
                lambda: PipelineExecution.objects.select_related('cicd_tool').get(id=execution_id)
            )()
            
            # 首先尝试合并步骤日志
            step_executions = await sync_to_async(
                lambda: list(execution.step_executions.select_related('atomic_step', 'pipeline_step').all().order_by('order'))
            )()
            
            if step_executions:
                combined_logs = []
                for step in step_executions:
                    if step.logs and step.logs.strip():
                        # 支持 pipeline_step 和 atomic_step
                        step_name = await sync_to_async(lambda: step.step_name)()
                        
                        combined_logs.append(f"=== {step_name} ===")
                        combined_logs.append(step.logs.strip())
                        combined_logs.append("")
                
                if combined_logs:
                    logs = "\n".join(combined_logs)
                    # 保存合并后的日志
                    def save_logs():
                        execution.logs = logs
                        execution.save(update_fields=['logs'])
                    
                    await sync_to_async(save_logs)()
                    return logs
            
            # 如果没有步骤日志，但有执行日志，返回执行日志
            if execution.logs:
                return execution.logs
            
            # 如果是远程执行且有外部ID，从外部工具获取
            if execution.cicd_tool and execution.external_id:
                tool = execution.cicd_tool
                adapter = AdapterFactory.create_adapter(
                    tool.tool_type,
                    base_url=tool.base_url,
                    username=tool.username,
                    token=tool.token,
                    **tool.config
                )
                
                async with adapter:
                    logs = await adapter.get_logs(execution.external_id)
                    
                    # 更新日志
                    execution.logs = logs
                    await sync_to_async(execution.save)(update_fields=['logs'])
                    
                    return logs
            
            return "暂无日志信息"
                
        except Exception as e:
            logger.error(f"Failed to get execution logs {execution_id}: {e}")
            return f"Error getting logs: {str(e)}"
    
    async def test_tool_connection(self, tool: CICDTool) -> Dict[str, Any]:
        """测试工具连接"""
        try:
            adapter = AdapterFactory.create_adapter(
                tool.tool_type,
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            async with adapter:
                is_connected = await adapter.health_check()
                
                if is_connected:
                    # 更新工具状态
                    tool.status = 'active'
                    tool.last_health_check = timezone.now()
                    await sync_to_async(tool.save)(update_fields=['status', 'last_health_check'])
                    
                    return {
                        'success': True,
                        'message': f'Successfully connected to {tool.tool_type} at {tool.base_url}',
                        'status': 'online',
                        'response_time': 'OK'
                    }
                else:
                    tool.status = 'error'
                    await sync_to_async(tool.save)(update_fields=['status'])
                    return {
                        'success': False,
                        'message': f'Failed to connect to {tool.tool_type} at {tool.base_url}',
                        'status': 'offline',
                        'error': 'Connection failed'
                    }
        
        except Exception as e:
            logger.error(f"Connection test failed for tool {tool.name}: {e}")
            tool.status = 'error'
            await sync_to_async(tool.save)(update_fields=['status'])
            return {
                'success': False,
                'message': f'Connection test failed: {str(e)}',
                'status': 'error',
                'error': str(e)
            }


# Celery 任务
@shared_task
def execute_pipeline_task(execution_id: int):
    """异步执行流水线任务"""
    engine = UnifiedCICDEngine()
    
    # 直接调用同步方法
    engine._perform_execution(execution_id)


@shared_task
def health_check_all_tools():
    """定期健康检查所有工具"""
    import asyncio
    from .models import CICDTool
    
    async def check_all():
        engine = UnifiedCICDEngine()
        tools = await sync_to_async(list)(CICDTool.objects.filter(status='active'))
        
        for tool in tools:
            try:
                await engine.health_check_tool(tool)
            except Exception as e:
                logger.error(f"Health check failed for tool {tool.name}: {e}")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(check_all())
    finally:
        loop.close()


# 全局引擎实例
cicd_engine = UnifiedCICDEngine()
