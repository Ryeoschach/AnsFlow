"""
本地Celery执行器 - 在AnsFlow服务器上执行原子步骤
"""
import logging
from typing import Dict, Any
from django.utils import timezone
from celery import group, chain

from ..models import Pipeline, PipelineRun
from cicd_integrations.models import AtomicStep
from ..tasks import execute_atomic_step_task

logger = logging.getLogger(__name__)


class LocalPipelineExecutor:
    """本地Celery执行器 - 原有的执行方式"""
    
    def execute(self, pipeline: Pipeline, pipeline_run: PipelineRun, 
               parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        在本地使用Celery执行流水线中的原子步骤
        
        Args:
            pipeline: 流水线对象
            pipeline_run: 流水线运行记录
            parameters: 执行参数
            
        Returns:
            执行结果字典
        """
        logger.info(f"开始本地执行流水线: {pipeline.name}")
        
        try:
            # 获取流水线的原子步骤，按order排序
            atomic_steps = pipeline.atomic_steps.filter(is_active=True).order_by('order')
            
            if not atomic_steps.exists():
                pipeline_run.status = 'success'
                pipeline_run.completed_at = timezone.now()
                pipeline_run.save()
                
                return {
                    'message': '流水线没有配置步骤，直接完成',
                    'steps_executed': 0
                }
            
            # 更新流水线运行状态
            pipeline_run.status = 'running'
            pipeline_run.save()
            
            # 构建Celery任务链
            task_chain = self._build_task_chain(atomic_steps, pipeline_run, parameters)
            
            # 执行任务链
            result = task_chain.apply_async()
            
            return {
                'message': f'成功启动本地执行，共{atomic_steps.count()}个步骤',
                'celery_task_id': result.id,
                'steps_count': atomic_steps.count(),
                'execution_mode': 'local'
            }
            
        except Exception as e:
            logger.error(f"本地执行失败: {e}")
            pipeline_run.status = 'failed'
            pipeline_run.completed_at = timezone.now()
            pipeline_run.save()
            
            return {
                'message': f'本地执行失败: {str(e)}',
                'error': str(e)
            }
    
    def _build_task_chain(self, atomic_steps, pipeline_run, parameters):
        """构建Celery任务链"""
        tasks = []
        
        for step in atomic_steps:
            # 合并流水线参数和步骤参数
            step_params = {
                **parameters or {},
                **step.parameters or {}
            }
            
            # 创建步骤执行任务
            task = execute_atomic_step_task.s(
                step_id=step.id,
                pipeline_run_id=pipeline_run.id,
                parameters=step_params
            )
            tasks.append(task)
        
        # 根据依赖关系决定是串行还是并行执行
        if self._has_dependencies(atomic_steps):
            # 有依赖关系，串行执行
            return chain(*tasks)
        else:
            # 无依赖关系，并行执行
            return group(tasks)
    
    def _has_dependencies(self, atomic_steps):
        """检查步骤是否有依赖关系"""
        for step in atomic_steps:
            if step.dependencies.exists():
                return True
        return False
    
    def execute_single_step(self, step: AtomicStep, pipeline_run: PipelineRun,
                           parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行单个原子步骤（用于混合模式）
        
        Args:
            step: 原子步骤
            pipeline_run: 流水线运行记录
            parameters: 执行参数
            
        Returns:
            执行结果
        """
        logger.info(f"本地执行单个步骤: {step.name}")
        
        try:
            # 执行步骤
            result = execute_atomic_step_task.delay(
                step_id=step.id,
                pipeline_run_id=pipeline_run.id,
                parameters=parameters or {}
            )
            
            return {
                'success': True,
                'task_id': result.id,
                'step_name': step.name,
                'execution_type': 'local'
            }
            
        except Exception as e:
            logger.error(f"单步本地执行失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'step_name': step.name
            }
