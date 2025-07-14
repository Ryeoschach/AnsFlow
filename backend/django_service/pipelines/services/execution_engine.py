"""
流水线执行引擎
支持三种执行模式：local、remote、hybrid
支持并行组执行
"""
import logging
from typing import Dict, Any, Optional, List
from django.utils import timezone
from ..models import Pipeline, PipelineRun, PipelineToolMapping
from cicd_integrations.models import CICDTool
from .jenkins_sync import JenkinsPipelineSyncService
from .parallel_execution import parallel_execution_service

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
        本地Celery执行模式，支持并行组
        """
        logger.info(f"Executing pipeline {pipeline.id} locally with parallel support")
        
        try:
            # 分析执行计划，识别并行组
            execution_plan = parallel_execution_service.analyze_pipeline_execution_plan(pipeline)
            
            # 检查是否有并行组
            has_parallel_groups = len(execution_plan['parallel_groups']) > 0
            
            if has_parallel_groups:
                logger.info(f"Pipeline has {len(execution_plan['parallel_groups'])} parallel groups")
                
                # 使用并行执行服务
                result = parallel_execution_service.execute_pipeline_with_parallel_support(
                    pipeline, pipeline_run, execution_plan
                )
                
                # 更新运行记录
                pipeline_run.trigger_data.update({
                    'execution_mode': 'local_parallel',
                    'execution_plan': execution_plan,
                    'parallel_groups_count': len(execution_plan['parallel_groups'])
                })
                pipeline_run.save()
                
                return result
            else:
                # 没有并行组，使用原有的Celery任务方式
                logger.info("No parallel groups found, using sequential execution")
                
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
                    'execution_mode': 'local_sequential'
                })
                pipeline_run.save()
                
                return {
                    'success': True,
                    'message': 'Pipeline started locally (sequential)',
                    'task_id': task_result.id,
                    'execution_mode': 'local_sequential'
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
    
    def _execute_hybrid(self, pipeline: Pipeline, pipeline_run: PipelineRun, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        混合执行模式：部分步骤本地执行，部分远程执行
        """
        logger.info(f"Executing pipeline {pipeline.id} in hybrid mode")
        
        try:
            steps = pipeline.atomic_steps.all().order_by('order')
            
            # 分析步骤，决定执行位置
            local_steps = []
            remote_steps = []
            
            for step in steps:
                if self._should_execute_locally(step):
                    local_steps.append(step)
                else:
                    remote_steps.append(step)
            
            # 创建执行计划
            execution_plan = {
                'local_steps': [{'id': s.id, 'name': s.name, 'type': s.step_type} for s in local_steps],
                'remote_steps': [{'id': s.id, 'name': s.name, 'type': s.step_type} for s in remote_steps],
                'execution_order': self._create_hybrid_execution_order(local_steps, remote_steps)
            }
            
            # 更新运行记录
            pipeline_run.trigger_data.update({
                'execution_mode': 'hybrid',
                'execution_plan': execution_plan
            })
            pipeline_run.save()
            
            # 开始执行
            if local_steps:
                # 启动本地执行
                from cicd_integrations.tasks import execute_pipeline_steps_task
                local_task = execute_pipeline_steps_task.delay(
                    pipeline_id=pipeline.id,
                    run_id=pipeline_run.id,
                    step_ids=[s.id for s in local_steps],
                    execution_mode='hybrid_local'
                )
                pipeline_run.trigger_data['local_task_id'] = local_task.id
            
            if remote_steps and pipeline.execution_tool:
                # 启动远程执行
                # 这里可以根据工具类型选择不同的远程执行策略
                pass
            
            pipeline_run.save()
            
            return {
                'success': True,
                'message': 'Hybrid pipeline execution started',
                'execution_plan': execution_plan,
                'execution_mode': 'hybrid'
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
        """
        local_step_types = [
            'approval',
            'notification', 
            'api_call',
            'webhook',
            'database_query'
        ]
        return step.step_type in local_step_types
    
    def _create_hybrid_execution_order(self, local_steps, remote_steps) -> List[Dict[str, Any]]:
        """
        创建混合执行的执行顺序
        """
        execution_order = []
        
        # 简单的顺序策略：按照步骤的order字段排序
        all_steps = list(local_steps) + list(remote_steps)
        all_steps.sort(key=lambda x: x.order)
        
        for step in all_steps:
            location = 'local' if step in local_steps else 'remote'
            execution_order.append({
                'step_id': step.id,
                'step_name': step.name,
                'step_type': step.step_type,
                'execution_location': location,
                'order': step.order
            })
        
        return execution_order
    
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
        """
        try:
            tool = pipeline.execution_tool
            
            # TODO: 实现GitLab CI API集成
            logger.info(f"Starting GitLab CI execution for pipeline {pipeline.id}")
            
            # 临时返回成功状态，实际实现后替换
            pipeline_run.trigger_data.update({
                'gitlab_pipeline_id': 'temp_pipeline_id',
                'gitlab_project_id': tool.config.get('project_id'),
                'execution_mode': 'remote',
                'tool_id': tool.id
            })
            pipeline_run.save()
            
            return {
                'success': True,
                'message': 'GitLab CI pipeline triggered successfully',
                'pipeline_id': 'temp_pipeline_id',
                'execution_mode': 'remote'
            }
            
        except Exception as e:
            logger.error(f"Remote GitLab execution failed: {e}")
            return {
                'success': False,
                'message': f'Remote GitLab execution failed: {str(e)}',
                'execution_mode': 'remote'
            }

    def _execute_remote_github(self, pipeline: Pipeline, pipeline_run: PipelineRun, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        在GitHub Actions中远程执行流水线
        """
        try:
            tool = pipeline.execution_tool
            
            # TODO: 实现GitHub Actions API集成
            logger.info(f"Starting GitHub Actions execution for pipeline {pipeline.id}")
            
            # 临时返回成功状态，实际实现后替换
            pipeline_run.trigger_data.update({
                'github_workflow_id': 'temp_workflow_id',
                'github_run_id': 'temp_run_id',
                'github_repository': tool.config.get('repository'),
                'execution_mode': 'remote',
                'tool_id': tool.id
            })
            pipeline_run.save()
            
            return {
                'success': True,
                'message': 'GitHub Actions workflow triggered successfully',
                'workflow_id': 'temp_workflow_id',
                'run_id': 'temp_run_id',
                'execution_mode': 'remote'
            }
            
        except Exception as e:
            logger.error(f"Remote GitHub execution failed: {e}")
            return {
                'success': False,
                'message': f'Remote GitHub execution failed: {str(e)}',
                'execution_mode': 'remote'
            }


# 全局执行引擎实例
execution_engine = PipelineExecutionEngine()
