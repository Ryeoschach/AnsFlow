"""
Celery tasks for pipeline operations
处理流水线和原子步骤的异步执行
"""
from celery import shared_task
from django.utils import timezone
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def execute_atomic_step_task(self, step_id: int, parameters: Dict[str, Any] = None):
    """
    异步执行单个原子步骤
    
    Args:
        step_id: 原子步骤ID
        parameters: 执行参数
    
    Returns:
        Dict: 执行结果
    """
    try:
        from pipelines.models import AtomicStep
        
        # 获取原子步骤
        step = AtomicStep.objects.get(id=step_id)
        
        logger.info(f"开始执行原子步骤: {step.name} (ID: {step_id})")
        
        # 更新步骤状态为运行中
        step.status = 'running'
        step.start_time = timezone.now()
        step.save(update_fields=['status', 'start_time'])
        
        # 模拟步骤执行
        import time
        import random
        
        # 模拟执行时间（1-5秒）
        execution_time = random.randint(1, 5)
        time.sleep(execution_time)
        
        # 模拟执行结果
        success_rate = 0.9  # 90%成功率
        is_success = random.random() < success_rate
        
        if is_success:
            # 执行成功
            step.status = 'completed'
            step.end_time = timezone.now()
            step.output = f"步骤 {step.name} 执行成功\\n执行时间: {execution_time}秒"
            step.save(update_fields=['status', 'end_time', 'output'])
            
            logger.info(f"原子步骤 {step.name} 执行成功")
            
            return {
                'success': True,
                'step_id': step_id,
                'step_name': step.name,
                'execution_time': execution_time,
                'output': step.output
            }
        else:
            # 执行失败
            step.status = 'failed'
            step.end_time = timezone.now()
            step.error_message = f"步骤 {step.name} 执行失败 (模拟错误)"
            step.save(update_fields=['status', 'end_time', 'error_message'])
            
            logger.error(f"原子步骤 {step.name} 执行失败")
            
            return {
                'success': False,
                'step_id': step_id,
                'step_name': step.name,
                'execution_time': execution_time,
                'error': step.error_message
            }
        
    except Exception as e:
        logger.error(f"执行原子步骤 {step_id} 时发生异常: {e}")
        
        # 尝试更新步骤状态
        try:
            from pipelines.models import AtomicStep
            step = AtomicStep.objects.get(id=step_id)
            step.status = 'failed'
            step.end_time = timezone.now()
            step.error_message = f"执行异常: {str(e)}"
            step.save(update_fields=['status', 'end_time', 'error_message'])
        except Exception as save_error:
            logger.error(f"保存步骤状态失败: {save_error}")
        
        return {
            'success': False,
            'step_id': step_id,
            'error': str(e)
        }


@shared_task(bind=True)
def execute_pipeline_task(self, pipeline_id: int, parameters: Dict[str, Any] = None):
    """
    异步执行完整流水线
    
    Args:
        pipeline_id: 流水线ID
        parameters: 执行参数
    
    Returns:
        Dict: 执行结果
    """
    try:
        from pipelines.models import Pipeline
        
        # 获取流水线
        pipeline = Pipeline.objects.get(id=pipeline_id)
        
        logger.info(f"开始执行流水线: {pipeline.name} (ID: {pipeline_id})")
        
        # 获取所有原子步骤
        atomic_steps = pipeline.atomic_steps.all().order_by('order')
        
        results = []
        
        for step in atomic_steps:
            # 执行步骤
            result = execute_atomic_step_task.delay(step.id, parameters)
            result_data = result.get()  # 等待步骤完成
            results.append(result_data)
            
            # 如果步骤失败，停止执行
            if not result_data.get('success', False):
                logger.error(f"流水线 {pipeline.name} 执行失败，停止在步骤 {step.name}")
                break
        
        # 统计结果
        success_count = sum(1 for r in results if r.get('success', False))
        total_count = len(results)
        
        logger.info(f"流水线 {pipeline.name} 执行完成: {success_count}/{total_count} 步骤成功")
        
        return {
            'success': success_count == total_count,
            'pipeline_id': pipeline_id,
            'pipeline_name': pipeline.name,
            'total_steps': total_count,
            'success_steps': success_count,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"执行流水线 {pipeline_id} 时发生异常: {e}")
        
        return {
            'success': False,
            'pipeline_id': pipeline_id,
            'error': str(e)
        }


@shared_task(bind=True)
def execute_parallel_group_task(self, group_id: str, step_ids: list, parameters: Dict[str, Any] = None):
    """
    异步执行并行组中的步骤
    
    Args:
        group_id: 并行组ID
        step_ids: 步骤ID列表
        parameters: 执行参数
    
    Returns:
        Dict: 执行结果
    """
    try:
        logger.info(f"开始执行并行组 {group_id}，包含 {len(step_ids)} 个步骤")
        
        # 并行执行所有步骤
        from celery import group
        
        # 创建并行任务组
        job = group(execute_atomic_step_task.s(step_id, parameters) for step_id in step_ids)
        result = job.apply_async()
        
        # 等待所有任务完成
        results = result.get()
        
        # 统计结果
        success_count = sum(1 for r in results if r.get('success', False))
        total_count = len(results)
        
        logger.info(f"并行组 {group_id} 执行完成: {success_count}/{total_count} 步骤成功")
        
        return {
            'success': success_count == total_count,
            'group_id': group_id,
            'total_steps': total_count,
            'success_steps': success_count,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"执行并行组 {group_id} 时发生异常: {e}")
        
        return {
            'success': False,
            'group_id': group_id,
            'error': str(e)
        }
