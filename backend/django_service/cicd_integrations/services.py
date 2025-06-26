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
            execute_pipeline_task.delay(execution.id)
            
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
            execute_pipeline_task.delay(execution.id)
            
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
            
            # 获取流水线的原子步骤
            atomic_steps = list(
                AtomicStep.objects.filter(
                    pipeline=execution.pipeline
                ).order_by('order')
            )
            
            if not atomic_steps:
                logger.warning(f"No atomic steps found for pipeline {execution.pipeline.id}")
                execution.status = 'failed'
                execution.completed_at = timezone.now()
                execution.logs = "No atomic steps found in pipeline"
                execution.save()
                return
            
            logger.info(f"Found {len(atomic_steps)} atomic steps to execute")
            
            # 使用同步执行器
            sync_executor = SyncPipelineExecutor()
            
            # 准备工具配置
            tool_config = {}
            if execution.cicd_tool:
                tool_config = {
                    'tool_type': execution.cicd_tool.tool_type,
                    'base_url': execution.cicd_tool.base_url,
                    'project_id': execution.cicd_tool.project_id,
                    'config': execution.cicd_tool.config
                }
            
            # 执行流水线
            result = sync_executor.execute_pipeline(
                execution_id=execution_id,
                tool_config=tool_config,
                parameters=execution.parameters
            )
            
            logger.info(f"Pipeline execution completed: {execution.id} - {'success' if result['success'] else 'failed'}")
        
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
            execution = await sync_to_async(PipelineExecution.objects.select_related)(
                'cicd_tool'
            ).aget(id=execution_id)
            
            # 如果已有日志，直接返回
            if execution.logs:
                return execution.logs
            
            # 否则从外部工具获取
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
        
        except Exception as e:
            logger.error(f"Failed to get execution logs {execution_id}: {e}")
            return f"Error getting logs: {str(e)}"


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
