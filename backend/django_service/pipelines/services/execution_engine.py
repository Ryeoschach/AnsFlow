"""
流水线执行引擎
支持三种执行模式：local、remote、hybrid
"""
import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from ..models import Pipeline, PipelineRun, PipelineToolMapping
from cicd_integrations.models import CICDTool
from .jenkins_sync import JenkinsPipelineSyncService

logger = logging.getLogger(__name__)


class PipelineExecutionEngine:
    """流水线执行引擎"""
    
    def __init__(self):
        self.execution_modes = {
            'local': self._execute_local,
            'remote': self._execute_remote,
            'hybrid': self._execute_hybrid
        }
    
    def execute_pipeline(self, pipeline: Pipeline, user, trigger_data: Dict[str, Any] = None) -> PipelineRun:
        """
        执行流水线
        
        Args:
            pipeline: 流水线对象
            user: 触发用户
            trigger_data: 触发数据
            
        Returns:
            PipelineRun: 流水线运行记录
        """
        # 创建流水线运行记录
        run_number = pipeline.runs.count() + 1
        pipeline_run = PipelineRun.objects.create(
            pipeline=pipeline,
            run_number=run_number,
            triggered_by=user,
            trigger_type=trigger_data.get('trigger_type', 'manual'),
            trigger_data=trigger_data or {},
            started_at=timezone.now()
        )
        
        try:
            # 根据执行模式选择执行方法
            execution_mode = pipeline.execution_mode or 'local'
            execution_func = self.execution_modes.get(execution_mode)
            
            if not execution_func:
                raise ValueError(f"Unsupported execution mode: {execution_mode}")
            
            logger.info(f"Executing pipeline {pipeline.id} in {execution_mode} mode")
            
            # 执行流水线
            result = execution_func(pipeline, pipeline_run, trigger_data or {})
            
            # 更新运行状态
            if result.get('success', False):
                pipeline_run.status = 'running'
            else:
                pipeline_run.status = 'failed'
                pipeline_run.completed_at = timezone.now()
            
            pipeline_run.save()
            
            return pipeline_run
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            pipeline_run.status = 'failed'
            pipeline_run.completed_at = timezone.now()
            pipeline_run.save()
            raise
    
    def _execute_local(self, pipeline: Pipeline, pipeline_run: PipelineRun, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        本地Celery执行模式（原有方式）
        """
        logger.info(f"Executing pipeline {pipeline.id} locally using Celery")
        
        try:
            # 导入Celery任务（避免循环导入）
            from cicd_integrations.tasks import execute_pipeline_task
            
            # 异步执行流水线
            task_result = execute_pipeline_task.delay(
                pipeline_id=pipeline.id,
                run_id=pipeline_run.id,
                trigger_data=trigger_data
            )
            
            # 更新运行记录的任务ID
            pipeline_run.trigger_data.update({
                'celery_task_id': task_result.id,
                'execution_mode': 'local'
            })
            pipeline_run.save()
            
            return {
                'success': True,
                'message': 'Pipeline started locally',
                'task_id': task_result.id,
                'execution_mode': 'local'
            }
            
        except Exception as e:
            logger.error(f"Local execution failed: {e}")
            return {
                'success': False,
                'message': f'Local execution failed: {str(e)}',
                'execution_mode': 'local'
            }
    
    def _execute_remote(self, pipeline: Pipeline, pipeline_run: PipelineRun, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        完全在外部CI/CD工具执行
        """
        logger.info(f"Executing pipeline {pipeline.id} remotely using {pipeline.execution_tool}")
        
        if not pipeline.execution_tool:
            raise ValueError("No execution tool configured for remote execution")
        
        tool = pipeline.execution_tool
        
        # 根据工具类型选择执行方式
        if tool.tool_type == 'jenkins':
            return self._execute_remote_jenkins(pipeline, pipeline_run, trigger_data)
        elif tool.tool_type == 'gitlab':
            return self._execute_remote_gitlab(pipeline, pipeline_run, trigger_data)
        elif tool.tool_type == 'github':
            return self._execute_remote_github(pipeline, pipeline_run, trigger_data)
        else:
            raise ValueError(f"Unsupported tool type for remote execution: {tool.tool_type}")
    
    def _execute_remote_jenkins(self, pipeline: Pipeline, pipeline_run: PipelineRun, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        在Jenkins中远程执行流水线
        """
        try:
            tool = pipeline.execution_tool
            jenkins_service = JenkinsPipelineSyncService(tool)
            
            # 检查是否已存在Jenkins作业
            if not pipeline.tool_job_name:
                # 如果没有作业名，先同步流水线到Jenkins
                sync_result = jenkins_service.sync_pipeline_to_jenkins(pipeline)
                if not sync_result['success']:
                    return sync_result
            
            # 准备构建参数
            build_parameters = trigger_data.get('parameters', {})
            build_parameters.update({
                'ANSFLOW_PIPELINE_ID': pipeline.id,
                'ANSFLOW_RUN_ID': pipeline_run.id,
                'ANSFLOW_TRIGGER_TYPE': trigger_data.get('trigger_type', 'manual')
            })
            
            # 触发Jenkins构建
            build_result = jenkins_service.trigger_jenkins_build(
                pipeline=pipeline,
                parameters=build_parameters
            )
            
            if build_result['success']:
                # 更新运行记录
                pipeline_run.trigger_data.update({
                    'jenkins_queue_id': build_result.get('queue_id'),
                    'jenkins_build_url': build_result.get('build_url'),
                    'execution_mode': 'remote',
                    'tool_id': tool.id
                })
                pipeline_run.save()
                
                # 创建或更新工具映射
                mapping, created = PipelineToolMapping.objects.get_or_create(
                    pipeline=pipeline,
                    tool=tool,
                    defaults={
                        'external_job_id': pipeline.tool_job_name,
                        'external_job_name': pipeline.tool_job_name,
                        'auto_sync': True,
                        'sync_status': 'synced'
                    }
                )
                if not created:
                    mapping.last_sync_at = timezone.now()
                    mapping.sync_status = 'synced'
                    mapping.save()
            
            return build_result
            
        except Exception as e:
            logger.error(f"Remote Jenkins execution failed: {e}")
            return {
                'success': False,
                'message': f'Remote Jenkins execution failed: {str(e)}',
                'execution_mode': 'remote'
            }
    
    def _execute_remote_gitlab(self, pipeline: Pipeline, pipeline_run: PipelineRun, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        在GitLab CI中远程执行流水线
        TODO: 实现GitLab CI集成
        """
        # 这里是GitLab CI的执行逻辑
        return {
            'success': False,
            'message': 'GitLab CI remote execution not implemented yet',
            'execution_mode': 'remote'
        }
    
    def _execute_remote_github(self, pipeline: Pipeline, pipeline_run: PipelineRun, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        在GitHub Actions中远程执行流水线
        TODO: 实现GitHub Actions集成
        """
        # 这里是GitHub Actions的执行逻辑
        return {
            'success': False,
            'message': 'GitHub Actions remote execution not implemented yet',
            'execution_mode': 'remote'
        }
    
    def _execute_hybrid(self, pipeline: Pipeline, pipeline_run: PipelineRun, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        混合模式执行（部分本地，部分远程）
        """
        logger.info(f"Executing pipeline {pipeline.id} in hybrid mode")
        
        try:
            # 分析流水线步骤，决定哪些在本地执行，哪些在远程执行
            local_steps = []
            remote_steps = []
            
            for step in pipeline.atomic_steps.all():
                # 根据步骤类型决定执行位置
                if self._should_execute_locally(step):
                    local_steps.append(step)
                else:
                    remote_steps.append(step)
            
            # 如果有远程步骤，确保工具配置正确
            if remote_steps and not pipeline.execution_tool:
                return {
                    'success': False,
                    'message': 'No execution tool configured for remote steps in hybrid mode',
                    'execution_mode': 'hybrid'
                }
            
            # 创建混合执行计划
            execution_plan = {
                'local_steps': [step.id for step in local_steps],
                'remote_steps': [step.id for step in remote_steps],
                'execution_order': self._create_hybrid_execution_order(local_steps, remote_steps)
            }
            
            # 启动混合执行
            from cicd_integrations.tasks import execute_hybrid_pipeline_task
            
            task_result = execute_hybrid_pipeline_task.delay(
                pipeline_id=pipeline.id,
                run_id=pipeline_run.id,
                execution_plan=execution_plan,
                trigger_data=trigger_data
            )
            
            # 更新运行记录
            pipeline_run.trigger_data.update({
                'celery_task_id': task_result.id,
                'execution_mode': 'hybrid',
                'execution_plan': execution_plan
            })
            pipeline_run.save()
            
            return {
                'success': True,
                'message': f'Hybrid pipeline started (Local: {len(local_steps)}, Remote: {len(remote_steps)})',
                'task_id': task_result.id,
                'execution_mode': 'hybrid',
                'execution_plan': execution_plan
            }
            
        except Exception as e:
            logger.error(f"Hybrid execution failed: {e}")
            return {
                'success': False,
                'message': f'Hybrid execution failed: {str(e)}',
                'execution_mode': 'hybrid'
            }
    
    def _should_execute_locally(self, step) -> bool:
        """
        判断步骤是否应该在本地执行
        
        本地执行的步骤类型：
        - database_query: 数据库查询
        - api_call: API调用
        - notification: 通知发送
        - approval: 审批节点
        
        远程执行的步骤类型：
        - build: 构建
        - test: 测试
        - deploy: 部署
        - docker_build: Docker构建
        """
        local_step_types = [
            'database_query',
            'api_call', 
            'notification',
            'approval',
            'webhook',
            'email'
        ]
        
        return step.step_type in local_step_types
    
    def _create_hybrid_execution_order(self, local_steps, remote_steps) -> list:
        """
        创建混合执行顺序
        根据步骤的order字段和依赖关系确定执行顺序
        """
        all_steps = list(local_steps) + list(remote_steps)
        all_steps.sort(key=lambda x: x.order)
        
        execution_order = []
        for step in all_steps:
            execution_order.append({
                'step_id': step.id,
                'step_name': step.name,
                'step_type': step.step_type,
                'execution_location': 'local' if step in local_steps else 'remote',
                'order': step.order
            })
        
        return execution_order


# 全局执行引擎实例
execution_engine = PipelineExecutionEngine()
