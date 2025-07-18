"""
Celery tasks for CI/CD operations
Implement background processing for pipeline execution, tool management, and notifications
"""
from django.utils import timezone
from django.db import transaction
from typing import Dict, Any, List, Optional
import logging
import asyncio
import json
from datetime import datetime, timedelta

from .models import (
    CICDTool, PipelineExecution, AtomicStep, StepExecution
)
from pipelines.models import Pipeline
from .services import UnifiedCICDEngine
from .adapters import get_adapter
from celery import shared_task

logger = logging.getLogger(__name__)


# RabbitMQ任务优先级装饰器和工具
from functools import wraps

def high_priority_task(bind=True, **options):
    """高优先级任务装饰器 - 用于Pipeline执行等关键任务"""
    options.setdefault('queue', 'high_priority')
    options.setdefault('retry_kwargs', {'max_retries': 3, 'countdown': 60})
    return shared_task(bind=bind, **options)

def medium_priority_task(bind=False, **options):
    """中等优先级任务装饰器 - 用于监控和报告任务"""
    options.setdefault('queue', 'medium_priority')
    options.setdefault('retry_kwargs', {'max_retries': 2, 'countdown': 120})
    return shared_task(bind=bind, **options)

def low_priority_task(bind=False, **options):
    """低优先级任务装饰器 - 用于清理和备份任务"""
    options.setdefault('queue', 'low_priority')
    options.setdefault('retry_kwargs', {'max_retries': 1, 'countdown': 300})
    return shared_task(bind=bind, **options)


@high_priority_task(bind=True)
def execute_pipeline_async(self, execution_id: int):
    """
    异步执行流水线任务
    
    Args:
        execution_id: PipelineExecution 的 ID
    """
    try:
        execution = PipelineExecution.objects.get(id=execution_id)
        execution.status = 'running'
        execution.started_at = timezone.now()
        execution.save(update_fields=['status', 'started_at'])
        
        logger.info(f"Starting pipeline execution {execution_id}")
        
        # 使用同步执行引擎
        engine = UnifiedCICDEngine()
        
        try:
            result = engine._perform_execution(execution_id)
            logger.info(f"Engine result type: {type(result)}, value: {result}")
        except Exception as engine_error:
            logger.error(f"Engine execution error: {engine_error}", exc_info=True)
            raise
        
        logger.info(f"Pipeline execution {execution_id} completed successfully")
        return {"status": "success", "execution_id": execution_id, "result": result}
        
    except PipelineExecution.DoesNotExist:
        logger.error(f"Pipeline execution {execution_id} not found")
        raise
    except Exception as e:
        logger.error(f"Pipeline execution {execution_id} failed: {e}")
        
        # 更新执行状态为失败
        try:
            execution = PipelineExecution.objects.get(id=execution_id)
            execution.status = 'failed'
            execution.completed_at = timezone.now()
            execution.logs = str(e)
            execution.save(update_fields=['status', 'completed_at', 'logs'])
        except:
            pass
        
        # 重试机制
        if self.request.retries < self.retry_kwargs['max_retries']:
            logger.info(f"Retrying pipeline execution {execution_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e)
        
        raise e


@medium_priority_task(bind=True)
def health_check_tools(self):
    """
    定期健康检查所有CI/CD工具
    """
    # 修复：使用正确的字段名和状态值
    tools = CICDTool.objects.filter(status__in=['active', 'authenticated'])
    results = []
    
    for tool in tools:
        try:
            adapter = get_adapter(tool.tool_type)(
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            # 创建异步事件循环进行健康检查
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            is_healthy = loop.run_until_complete(adapter.health_check())
            loop.close()
            
            # 更新工具状态
            tool.last_health_check = timezone.now()
            
            # 在 metadata 中存储健康状态
            if not tool.metadata:
                tool.metadata = {}
            tool.metadata['health_status'] = 'healthy' if is_healthy else 'unhealthy'
            tool.metadata['last_health_check_result'] = is_healthy
            
            # 根据健康检查结果更新 status
            if is_healthy:
                if tool.status not in ['active', 'authenticated']:
                    tool.status = 'authenticated'
            else:
                if tool.status not in ['offline', 'error']:
                    tool.status = 'needs_auth'
            
            tool.save(update_fields=['last_health_check', 'metadata', 'status'])
            
            results.append({
                'tool_id': tool.id,
                'tool_name': tool.name,
                'tool_type': tool.tool_type,
                'status': 'healthy' if is_healthy else 'unhealthy'
            })
            
            logger.info(f"Health check for tool {tool.name}: {'healthy' if is_healthy else 'unhealthy'}")
            
        except Exception as e:
            tool.last_health_check = timezone.now()
            
            # 在 metadata 中存储错误状态
            if not tool.metadata:
                tool.metadata = {}
            tool.metadata['health_status'] = 'error'
            tool.metadata['last_error'] = str(e)
            
            # 设置错误状态
            tool.status = 'error'
            tool.save(update_fields=['last_health_check', 'metadata', 'status'])
            
            results.append({
                'tool_id': tool.id,
                'tool_name': tool.name,
                'tool_type': tool.tool_type,
                'status': 'error',
                'error': str(e)
            })
            
            logger.error(f"Health check failed for tool {tool.name}: {e}")
    
    return {
        'timestamp': timezone.now().isoformat(),
        'total_tools': len(tools),
        'results': results
    }


@low_priority_task
def cleanup_old_executions():
    """
    清理旧的流水线执行记录
    """
    # 清理30天前的执行记录
    cutoff_date = timezone.now() - timedelta(days=30)
    
    old_executions = PipelineExecution.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['completed', 'failed', 'cancelled']
    )
    
    count = old_executions.count()
    
    # 批量删除
    old_executions.delete()
    
    logger.info(f"Cleaned up {count} old pipeline executions")
    return {"cleaned_executions": count, "cutoff_date": cutoff_date.isoformat()}


@shared_task
def sync_tool_jobs(tool_id: int):
    """
    同步工具中的作业/流水线信息
    
    Args:
        tool_id: CICDTool 的 ID
    """
    try:
        tool = CICDTool.objects.get(id=tool_id)
        
        adapter = get_adapter(tool.tool_type)(
            base_url=tool.base_url,
            username=tool.username,
            token=tool.token,
            **tool.config
        )
        
        # 创建异步事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 获取工具中的作业列表
        if tool.tool_type == 'jenkins':
            jobs = loop.run_until_complete(adapter.list_jobs())
        else:
            # 其他工具类型的同步逻辑
            jobs = []
        
        loop.close()
        
        synced_jobs = []
        for job in jobs:
            synced_jobs.append({
                'name': job.get('name'),
                'url': job.get('url'),
                'color': job.get('color'),
                'buildable': job.get('buildable', False)
            })
        
        # 更新工具的元数据
        tool.metadata = tool.metadata or {}
        tool.metadata['synced_jobs'] = synced_jobs
        tool.metadata['last_sync'] = timezone.now().isoformat()
        tool.save(update_fields=['metadata'])
        
        logger.info(f"Synced {len(synced_jobs)} jobs for tool {tool.name}")
        
        return {
            'tool_id': tool_id,
            'tool_name': tool.name,
            'synced_jobs_count': len(synced_jobs),
            'jobs': synced_jobs
        }
        
    except CICDTool.DoesNotExist:
        logger.error(f"Tool {tool_id} not found")
        raise
    except Exception as e:
        logger.error(f"Failed to sync jobs for tool {tool_id}: {e}")
        raise


@shared_task
def process_webhook_event(webhook_data: Dict[str, Any]):
    """
    处理Webhook事件并触发相应的流水线
    
    Args:
        webhook_data: Webhook事件数据
    """
    try:
        event_type = webhook_data.get('event_type')
        source = webhook_data.get('source')
        payload = webhook_data.get('payload', {})
        
        logger.info(f"Processing webhook event: {event_type} from {source}")
        
        # 根据事件类型和源处理不同的逻辑
        if source == 'github' and event_type == 'push':
            return _process_github_push_event(payload)
        elif source == 'gitlab' and event_type == 'push':
            return _process_gitlab_push_event(payload)
        elif source == 'jenkins' and event_type == 'build':
            return _process_jenkins_build_event(payload)
        else:
            logger.warning(f"Unhandled webhook event: {event_type} from {source}")
            return {"status": "ignored", "reason": "unhandled_event_type"}
        
    except Exception as e:
        logger.error(f"Failed to process webhook event: {e}")
        raise


def _process_github_push_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """处理GitHub push事件"""
    repository = payload.get('repository', {})
    repo_name = repository.get('name', '')
    branch = payload.get('ref', '').replace('refs/heads/', '')
    
    # 查找匹配的流水线
    pipelines = Pipeline.objects.filter(
        metadata__repository__icontains=repo_name,
        is_active=True
    )
    
    triggered_pipelines = []
    for pipeline in pipelines:
        # 检查分支匹配
        trigger_branches = pipeline.metadata.get('trigger_branches', ['main', 'master'])
        if branch in trigger_branches or '*' in trigger_branches:
            # 创建执行
            execution = PipelineExecution.objects.create(
                pipeline=pipeline,
                trigger_type='webhook',
                parameters={
                    'repository': repo_name,
                    'branch': branch,
                    'commit': payload.get('after', ''),
                    'pusher': payload.get('pusher', {}).get('name', ''),
                    'webhook_payload': payload
                }
            )
            
            # 异步执行流水线
            execute_pipeline_async.delay(execution.id)
            
            triggered_pipelines.append({
                'pipeline_id': pipeline.id,
                'pipeline_name': pipeline.name,
                'execution_id': execution.id
            })
    
    return {
        'status': 'processed',
        'repository': repo_name,
        'branch': branch,
        'triggered_pipelines': triggered_pipelines
    }


def _process_gitlab_push_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """处理GitLab push事件"""
    project = payload.get('project', {})
    repo_name = project.get('name', '')
    branch = payload.get('ref', '').replace('refs/heads/', '')
    
    # 类似GitHub的处理逻辑
    pipelines = Pipeline.objects.filter(
        metadata__repository__icontains=repo_name,
        is_active=True
    )
    
    triggered_pipelines = []
    for pipeline in pipelines:
        trigger_branches = pipeline.metadata.get('trigger_branches', ['main', 'master'])
        if branch in trigger_branches or '*' in trigger_branches:
            execution = PipelineExecution.objects.create(
                pipeline=pipeline,
                trigger_type='webhook',
                parameters={
                    'repository': repo_name,
                    'branch': branch,
                    'commit': payload.get('after', ''),
                    'pusher': payload.get('user_name', ''),
                    'webhook_payload': payload
                }
            )
            
            execute_pipeline_async.delay(execution.id)
            
            triggered_pipelines.append({
                'pipeline_id': pipeline.id,
                'pipeline_name': pipeline.name,
                'execution_id': execution.id
            })
    
    return {
        'status': 'processed',
        'repository': repo_name,
        'branch': branch,
        'triggered_pipelines': triggered_pipelines
    }


def _process_jenkins_build_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """处理Jenkins构建事件"""
    job_name = payload.get('name', '')
    build_number = payload.get('build', {}).get('number', 0)
    build_status = payload.get('build', {}).get('phase', 'UNKNOWN')
    
    logger.info(f"Jenkins build event: {job_name} #{build_number} - {build_status}")
    
    # 查找相关的流水线执行
    executions = PipelineExecution.objects.filter(
        external_id=str(build_number),
        status='running'
    )
    
    updated_executions = []
    for execution in executions:
        if build_status in ['COMPLETED', 'FINALIZED']:
            execution.status = 'completed' if payload.get('build', {}).get('status') == 'SUCCESS' else 'failed'
            execution.completed_at = timezone.now()
        elif build_status == 'STARTED':
            execution.status = 'running'
            execution.started_at = timezone.now()
        
        execution.logs = json.dumps(payload, indent=2)
        execution.save()
        
        updated_executions.append({
            'execution_id': execution.id,
            'pipeline_name': execution.pipeline.name,
            'status': execution.status
        })
    
    return {
        'status': 'processed',
        'job_name': job_name,
        'build_number': build_number,
        'build_status': build_status,
        'updated_executions': updated_executions
    }


@shared_task
def generate_execution_reports():
    """
    生成流水线执行报告
    """
    # 统计最近7天的执行情况
    week_ago = timezone.now() - timedelta(days=7)
    
    executions = PipelineExecution.objects.filter(created_at__gte=week_ago)
    
    stats = {
        'total_executions': executions.count(),
        'successful_executions': executions.filter(status='completed').count(),
        'failed_executions': executions.filter(status='failed').count(),
        'running_executions': executions.filter(status='running').count(),
        'cancelled_executions': executions.filter(status='cancelled').count(),
    }
    
    # 按流水线统计
    pipeline_stats = {}
    for execution in executions:
        pipeline_name = execution.pipeline.name
        if pipeline_name not in pipeline_stats:
            pipeline_stats[pipeline_name] = {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'average_duration': 0
            }
        
        pipeline_stats[pipeline_name]['total'] += 1
        if execution.status == 'completed':
            pipeline_stats[pipeline_name]['successful'] += 1
        elif execution.status == 'failed':
            pipeline_stats[pipeline_name]['failed'] += 1
    
    # 计算成功率
    if stats['total_executions'] > 0:
        stats['success_rate'] = (stats['successful_executions'] / stats['total_executions']) * 100
    else:
        stats['success_rate'] = 0
    
    report = {
        'period': f"Last 7 days ({week_ago.date()} - {timezone.now().date()})",
        'generated_at': timezone.now().isoformat(),
        'overall_stats': stats,
        'pipeline_stats': pipeline_stats
    }
    
    logger.info(f"Generated execution report: {stats['total_executions']} executions, {stats['success_rate']:.1f}% success rate")
    
    return report


@shared_task
def monitor_long_running_executions():
    """
    监控长时间运行的流水线执行
    """
    # 检查运行超过2小时的执行
    threshold = timezone.now() - timedelta(hours=2)
    
    long_running = PipelineExecution.objects.filter(
        status='running',
        started_at__lt=threshold
    )
    
    alerts = []
    for execution in long_running:
        duration = timezone.now() - execution.started_at
        alerts.append({
            'execution_id': execution.id,
            'pipeline_name': execution.pipeline.name,
            'started_at': execution.started_at.isoformat(),
            'duration_hours': duration.total_seconds() / 3600,
            'tool_name': execution.pipeline.tool.name if execution.pipeline.tool else 'Unknown'
        })
    
    if alerts:
        logger.warning(f"Found {len(alerts)} long-running pipeline executions")
    
    return {
        'threshold_hours': 2,
        'long_running_count': len(alerts),
        'executions': alerts
    }


@low_priority_task
def backup_pipeline_configurations():
    """
    备份流水线配置
    """
    pipelines = Pipeline.objects.filter(is_active=True)
    
    backup_data = []
    for pipeline in pipelines:
        backup_data.append({
            'id': pipeline.id,
            'name': pipeline.name,
            'description': pipeline.description,
            'tool_type': pipeline.tool.tool_type if pipeline.tool else None,
            'tool_name': pipeline.tool.name if pipeline.tool else None,
            'steps_count': pipeline.steps.count(),
            'metadata': pipeline.metadata,
            'created_at': pipeline.created_at.isoformat(),
            'updated_at': pipeline.updated_at.isoformat()
        })
    
    backup = {
        'backup_timestamp': timezone.now().isoformat(),
        'pipelines_count': len(backup_data),
        'pipelines': backup_data
    }
    
    logger.info(f"Backed up {len(backup_data)} pipeline configurations")
    
    return backup


@shared_task(bind=True, retry_kwargs={'max_retries': 3, 'countdown': 60})
def execute_pipeline_task(self, execution_id: int, pipeline_id: int, trigger_type: str, 
                         triggered_by_id: int, parameters: Dict[str, Any]):
    """
    执行流水线任务 - 支持同步和异步调用
    
    Args:
        execution_id: 流水线执行ID
        pipeline_id: 流水线ID
        trigger_type: 触发类型
        triggered_by_id: 触发用户ID
        parameters: 执行参数
    """
    try:
        from django.contrib.auth.models import User
        
        logger.info(f"开始执行流水线任务: execution_id={execution_id}, pipeline_id={pipeline_id}")
        
        # 获取执行记录
        execution = PipelineExecution.objects.get(id=execution_id)
        execution.status = 'running'
        execution.started_at = timezone.now()
        execution.save(update_fields=['status', 'started_at'])
        
        # 创建统一CICD引擎实例
        engine = UnifiedCICDEngine()
        
        # 直接调用同步方法，不需要asyncio
        result = engine._perform_execution(execution_id)
        
        # 更新执行状态
        execution.refresh_from_db()
        if execution.status not in ['success', 'failed']:
            final_status = 'success' if (result and result.get('success', False)) else 'failed'
            execution.status = final_status
            execution.completed_at = timezone.now()
            execution.save(update_fields=['status', 'completed_at'])
        
        logger.info(f"流水线任务执行完成: execution_id={execution_id}, success={result.get('success', False) if result else False}")
        
        return {
            "status": "success" if result and result.get('success', False) else "failed",
            "execution_id": execution_id,
            "pipeline_id": pipeline_id,
            "result": result
        }
        
    except PipelineExecution.DoesNotExist:
        logger.error(f"流水线执行记录不存在: {execution_id}")
        raise
    except Exception as e:
        logger.error(f"流水线任务执行失败: execution_id={execution_id}, error={str(e)}")
        
        # 更新执行状态为失败
        try:
            execution = PipelineExecution.objects.get(id=execution_id)
            execution.status = 'failed'
            execution.completed_at = timezone.now()
            execution.logs = (execution.logs or '') + f"\n任务执行错误: {str(e)}"
            execution.save(update_fields=['status', 'completed_at', 'logs'])
        except:
            pass
        
        # 重试机制
        if self.request.retries < self.retry_kwargs['max_retries']:
            logger.info(f"重试流水线任务: execution_id={execution_id} (尝试 {self.request.retries + 1})")
            raise self.retry(exc=e)
        
        raise e


@shared_task(bind=True, retry_kwargs={'max_retries': 3, 'countdown': 60})
def execute_pipeline_task(self, pipeline_id: int, run_id: int, trigger_data: Dict[str, Any]):
    """
    本地Celery执行流水线任务
    
    Args:
        pipeline_id: Pipeline ID
        run_id: PipelineRun ID  
        trigger_data: 触发数据
    """
    try:
        from pipelines.models import Pipeline, PipelineRun
        
        pipeline = Pipeline.objects.get(id=pipeline_id)
        pipeline_run = PipelineRun.objects.get(id=run_id)
        
        logger.info(f"Starting local execution for pipeline {pipeline_id}, run {run_id}")
        
        # 更新状态为运行中
        pipeline_run.status = 'running'
        pipeline_run.save()
        
        # 执行流水线的原子步骤
        success_count = 0
        total_steps = pipeline.atomic_steps.count()
        
        for step in pipeline.atomic_steps.order_by('order'):
            try:
                logger.info(f"Executing step: {step.name} ({step.step_type})")
                
                # 执行单个步骤
                step_result = execute_atomic_step_local(step, trigger_data)
                
                if step_result['success']:
                    success_count += 1
                    logger.info(f"Step {step.name} completed successfully")
                else:
                    logger.error(f"Step {step.name} failed: {step_result.get('message')}")
                    # 如果步骤失败，停止执行
                    break
                    
            except Exception as e:
                logger.error(f"Step {step.name} execution error: {e}")
                break
        
        # 更新最终状态
        if success_count == total_steps:
            pipeline_run.status = 'success'
            logger.info(f"Pipeline {pipeline_id} completed successfully")
        else:
            pipeline_run.status = 'failed'
            logger.error(f"Pipeline {pipeline_id} failed ({success_count}/{total_steps} steps completed)")
        
        pipeline_run.completed_at = timezone.now()
        pipeline_run.save()
        
        return {
            'success': success_count == total_steps,
            'completed_steps': success_count,
            'total_steps': total_steps
        }
        
    except Exception as e:
        logger.error(f"Pipeline execution task failed: {e}")
        
        # 更新状态为失败
        try:
            pipeline_run = PipelineRun.objects.get(id=run_id)
            pipeline_run.status = 'failed'
            pipeline_run.completed_at = timezone.now()
            pipeline_run.save()
        except:
            pass
        
        raise self.retry(exc=e)


@shared_task(bind=True, retry_kwargs={'max_retries': 3, 'countdown': 60})
def execute_hybrid_pipeline_task(self, pipeline_id: int, run_id: int, execution_plan: Dict[str, Any], trigger_data: Dict[str, Any]):
    """
    混合模式执行流水线任务
    
    Args:
        pipeline_id: Pipeline ID
        run_id: PipelineRun ID
        execution_plan: 执行计划
        trigger_data: 触发数据
    """
    try:
        from pipelines.models import Pipeline, PipelineRun
        
        pipeline = Pipeline.objects.get(id=pipeline_id)
        pipeline_run = PipelineRun.objects.get(id=run_id)
        
        logger.info(f"Starting hybrid execution for pipeline {pipeline_id}, run {run_id}")
        
        # 更新状态为运行中
        pipeline_run.status = 'running'
        pipeline_run.save()
        
        execution_order = execution_plan['execution_order']
        completed_steps = 0
        total_steps = len(execution_order)
        
        # 按顺序执行步骤
        for step_info in execution_order:
            step_id = step_info['step_id']
            execution_location = step_info['execution_location']
            
            try:
                step = AtomicStep.objects.get(id=step_id)
                logger.info(f"Executing step {step.name} ({execution_location})")
                
                if execution_location == 'local':
                    # 本地执行
                    result = execute_atomic_step_local(step, trigger_data)
                else:
                    # 远程执行 - 通过Jenkins或其他工具
                    result = execute_atomic_step_remote(step, pipeline.execution_tool, trigger_data)
                
                if result['success']:
                    completed_steps += 1
                    logger.info(f"Step {step.name} completed successfully")
                else:
                    logger.error(f"Step {step.name} failed: {result.get('message')}")
                    break
                    
            except Exception as e:
                logger.error(f"Step {step_id} execution error: {e}")
                break
        
        # 更新最终状态
        if completed_steps == total_steps:
            pipeline_run.status = 'success'
            logger.info(f"Hybrid pipeline {pipeline_id} completed successfully")
        else:
            pipeline_run.status = 'failed'
            logger.error(f"Hybrid pipeline {pipeline_id} failed ({completed_steps}/{total_steps} steps completed)")
        
        pipeline_run.completed_at = timezone.now()
        pipeline_run.save()
        
        return {
            'success': completed_steps == total_steps,
            'completed_steps': completed_steps,
            'total_steps': total_steps,
            'execution_mode': 'hybrid'
        }
        
    except Exception as e:
        logger.error(f"Hybrid pipeline execution task failed: {e}")
        
        # 更新状态为失败
        try:
            pipeline_run = PipelineRun.objects.get(id=run_id)
            pipeline_run.status = 'failed'
            pipeline_run.completed_at = timezone.now()
            pipeline_run.save()
        except:
            pass
        
        raise self.retry(exc=e)


def execute_atomic_step_local(step: AtomicStep, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    在本地执行原子步骤
    """
    try:
        logger.info(f"Executing step {step.name} locally")
        
        # 根据步骤类型执行不同的逻辑
        if step.step_type == 'shell_command':
            return execute_shell_command_step(step, trigger_data)
        elif step.step_type == 'api_call':
            return execute_api_call_step(step, trigger_data)
        elif step.step_type == 'database_query':
            return execute_database_query_step(step, trigger_data)
        elif step.step_type == 'notification':
            return execute_notification_step(step, trigger_data)
        elif step.step_type == 'approval':
            return execute_approval_step(step, trigger_data)
        else:
            return {
                'success': False,
                'message': f'Unsupported step type for local execution: {step.step_type}'
            }
            
    except Exception as e:
        logger.error(f"Local step execution failed: {e}")
        return {
            'success': False,
            'message': f'Local execution error: {str(e)}'
        }


def execute_atomic_step_remote(step: AtomicStep, tool: 'CICDTool', trigger_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    在远程CI/CD工具中执行原子步骤
    """
    try:
        logger.info(f"Executing step {step.name} remotely using {tool.name}")
        
        if tool.tool_type == 'jenkins':
            return execute_step_in_jenkins(step, tool, trigger_data)
        elif tool.tool_type == 'gitlab':
            return execute_step_in_gitlab(step, tool, trigger_data)
        elif tool.tool_type == 'github':
            return execute_step_in_github(step, tool, trigger_data)
        else:
            return {
                'success': False,
                'message': f'Unsupported tool type for remote execution: {tool.tool_type}'
            }
            
    except Exception as e:
        logger.error(f"Remote step execution failed: {e}")
        return {
            'success': False,
            'message': f'Remote execution error: {str(e)}'
        }


# 具体的步骤执行函数
def execute_shell_command_step(step: AtomicStep, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
    """执行Shell命令步骤"""
    import subprocess
    
    try:
        command = step.parameters.get('command', '')
        if not command:
            return {'success': False, 'message': 'No command specified'}
        
        # 执行命令
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=step.parameters.get('timeout', 300)
        )
        
        return {
            'success': result.returncode == 0,
            'message': f'Command completed with exit code {result.returncode}',
            'output': result.stdout,
            'error': result.stderr
        }
        
    except subprocess.TimeoutExpired:
        return {'success': False, 'message': 'Command timed out'}
    except Exception as e:
        return {'success': False, 'message': f'Command execution failed: {str(e)}'}


def execute_api_call_step(step: AtomicStep, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
    """执行API调用步骤"""
    import requests
    
    try:
        url = step.parameters.get('url', '')
        method = step.parameters.get('method', 'GET').upper()
        headers = step.parameters.get('headers', {})
        data = step.parameters.get('data', {})
        
        if not url:
            return {'success': False, 'message': 'No URL specified'}
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data if method in ['POST', 'PUT', 'PATCH'] else None,
            timeout=step.parameters.get('timeout', 30)
        )
        
        return {
            'success': response.status_code < 400,
            'message': f'API call completed with status {response.status_code}',
            'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }
        
    except requests.RequestException as e:
        return {'success': False, 'message': f'API call failed: {str(e)}'}


def execute_database_query_step(step: AtomicStep, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
    """执行数据库查询步骤"""
    from django.db import connection
    
    try:
        query = step.parameters.get('query', '')
        if not query:
            return {'success': False, 'message': 'No query specified'}
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                return {
                    'success': True,
                    'message': f'Query executed successfully, {len(results)} rows returned',
                    'results': results
                }
            else:
                return {
                    'success': True,
                    'message': f'Query executed successfully, {cursor.rowcount} rows affected'
                }
                
    except Exception as e:
        return {'success': False, 'message': f'Database query failed: {str(e)}'}


def execute_notification_step(step: AtomicStep, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
    """执行通知步骤"""
    try:
        notification_type = step.parameters.get('type', 'email')
        message = step.parameters.get('message', '')
        recipients = step.parameters.get('recipients', [])
        
        if notification_type == 'email':
            from django.core.mail import send_mail
            
            send_mail(
                subject=step.parameters.get('subject', 'Pipeline Notification'),
                message=message,
                from_email='noreply@ansflow.com',
                recipient_list=recipients
            )
        elif notification_type == 'slack':
            # Slack通知逻辑
            pass
        
        return {
            'success': True,
            'message': f'Notification sent to {len(recipients)} recipients'
        }
        
    except Exception as e:
        return {'success': False, 'message': f'Notification failed: {str(e)}'}


def execute_approval_step(step: AtomicStep, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
    """执行审批步骤"""
    try:
        # 创建审批请求
        # 这里应该集成审批工作流系统
        return {
            'success': True,
            'message': 'Approval request created',
            'pending_approval': True
        }
        
    except Exception as e:
        return {'success': False, 'message': f'Approval step failed: {str(e)}'}


def execute_step_in_jenkins(step: AtomicStep, tool: 'CICDTool', trigger_data: Dict[str, Any]) -> Dict[str, Any]:
    """在Jenkins中执行步骤"""
    try:
        from pipelines.services.jenkins_sync import JenkinsPipelineSyncService
        
        jenkins_service = JenkinsPipelineSyncService(tool)
        
        # 根据步骤类型创建Jenkins作业配置
        job_config = create_jenkins_job_config_for_step(step)
        
        # 创建临时Jenkins作业
        job_name = f"ansflow-step-{step.id}-{timezone.now().strftime('%Y%m%d-%H%M%S')}"
        
        # 这里应该调用Jenkins API创建并执行作业
        # 返回构建结果
        
        return {
            'success': True,
            'message': f'Step executed in Jenkins job: {job_name}',
            'jenkins_job': job_name
        }
        
    except Exception as e:
        return {'success': False, 'message': f'Jenkins execution failed: {str(e)}'}


def execute_step_in_gitlab(step: AtomicStep, tool: 'CICDTool', trigger_data: Dict[str, Any]) -> Dict[str, Any]:
    """在GitLab CI中执行步骤"""
    # TODO: 实现GitLab CI步骤执行
    return {'success': False, 'message': 'GitLab CI execution not implemented yet'}


def execute_step_in_github(step: AtomicStep, tool: 'CICDTool', trigger_data: Dict[str, Any]) -> Dict[str, Any]:
    """在GitHub Actions中执行步骤"""
    # TODO: 实现GitHub Actions步骤执行
    return {'success': False, 'message': 'GitHub Actions execution not implemented yet'}


def create_jenkins_job_config_for_step(step: AtomicStep) -> str:
    """为原子步骤创建Jenkins作业配置"""
    
    if step.step_type == 'build':
        return f"""
        <project>
            <builders>
                <hudson.tasks.Shell>
                    <command>{step.parameters.get('build_command', 'echo "Build step"')}</command>
                </hudson.tasks.Shell>
            </builders>
        </project>
        """
    elif step.step_type == 'test':
        return f"""
        <project>
            <builders>
                <hudson.tasks.Shell>
                    <command>{step.parameters.get('test_command', 'echo "Test step"')}</command>
                </hudson.tasks.Shell>
            </builders>
        </project>
        """
    elif step.step_type == 'deploy':
        return f"""
        <project>
            <builders>
                <hudson.tasks.Shell>
                    <command>{step.parameters.get('deploy_command', 'echo "Deploy step"')}</command>
                </hudson.tasks.Shell>
            </builders>
        </project>
        """
    else:
        return f"""
        <project>
            <builders>
                <hudson.tasks.Shell>
                    <command>echo "Executing {step.name} ({step.step_type})"</command>
                </hudson.tasks.Shell>
            </builders>
        </project>
        """


@shared_task(bind=True)
def monitor_remote_execution(self, execution_id: int):
    """
    监控远程CI/CD工具的流水线执行状态
    
    Args:
        execution_id: PipelineExecution 的 ID
    """
    try:
        execution = PipelineExecution.objects.select_related('cicd_tool').get(id=execution_id)
        
        if not execution.cicd_tool or not execution.external_id:
            logger.error(f"No CI/CD tool or external ID for execution {execution_id}")
            return
        
        logger.info(f"Starting monitoring for remote execution {execution_id} (external ID: {execution.external_id})")
        
        from .adapters import AdapterFactory
        
        # 创建适配器
        adapter = AdapterFactory.create_adapter(
            execution.cicd_tool.tool_type,
            base_url=execution.cicd_tool.base_url,
            username=execution.cicd_tool.username,
            token=execution.cicd_tool.token,
            **execution.cicd_tool.config
        )
        
        # 运行异步监控
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _async_monitor_remote_execution(adapter, execution)
            )
            return result
        finally:
            loop.close()
            
    except PipelineExecution.DoesNotExist:
        logger.error(f"Pipeline execution {execution_id} not found")
    except Exception as e:
        logger.error(f"Error monitoring remote execution {execution_id}: {e}", exc_info=True)
        
        # 如果监控失败，标记执行为失败状态
        try:
            execution = PipelineExecution.objects.get(id=execution_id)
            if execution.status in ['pending', 'running']:
                execution.status = 'failed'
                execution.completed_at = timezone.now()
                execution.logs = f"Monitoring failed: {str(e)}"
                execution.save()
        except:
            pass


async def _async_monitor_remote_execution(adapter, execution: PipelineExecution):
    """异步监控远程执行"""
    from asgiref.sync import sync_to_async
    
    max_checks = 360  # 最多检查6小时 (每分钟检查一次)
    check_count = 0
    
    async with adapter:
        while check_count < max_checks:
            try:
                # 获取执行状态
                status_data = await adapter.get_pipeline_status(execution.external_id)
                current_status = status_data.get('status', 'unknown')
                
                logger.info(f"Remote execution {execution.id} status: {current_status}")
                
                # 映射外部状态到内部状态
                internal_status = _map_external_status(current_status)
                
                # 更新执行状态
                if internal_status != execution.status:
                    execution.status = internal_status
                    
                    # 更新所有步骤的状态
                    await _update_step_executions_status(execution, internal_status)
                    
                    if internal_status in ['success', 'failed', 'cancelled']:
                        execution.completed_at = timezone.now()
                        
                        # 获取日志
                        try:
                            logs = await adapter.get_logs(execution.external_id)
                            execution.logs = logs
                        except Exception as e:
                            logger.warning(f"Failed to get logs for {execution.external_id}: {e}")
                            execution.logs = f"Execution completed but failed to get logs: {str(e)}"
                    
                    await sync_to_async(execution.save)()
                    logger.info(f"Updated execution {execution.id} status to {internal_status}")
                
                # 如果执行完成，退出监控
                if internal_status in ['success', 'failed', 'cancelled', 'timeout']:
                    logger.info(f"Remote execution monitoring completed: {execution.id} - {internal_status}")
                    return {'status': 'completed', 'final_status': internal_status}
                
                # 等待1分钟后再次检查
                await asyncio.sleep(60)
                check_count += 1
            
            except Exception as e:
                logger.error(f"Error checking remote execution status: {e}")
                check_count += 1
                await asyncio.sleep(60)
        
        # 如果超时仍未完成，标记为超时
        if check_count >= max_checks:
            logger.warning(f"Remote execution monitoring timeout: {execution.id}")
            execution.status = 'timeout'
            execution.completed_at = timezone.now()
            execution.logs = execution.logs + "\n\nExecution timed out after 6 hours"
            
            # 更新步骤状态为超时
            await _update_step_executions_status(execution, 'timeout')
            
            await sync_to_async(execution.save)()
            return {'status': 'timeout'}


def _map_external_status(external_status: str) -> str:
    """映射外部CI/CD工具的状态到内部状态"""
    status_mapping = {
        # Jenkins
        'SUCCESS': 'success',
        'FAILURE': 'failed',
        'ABORTED': 'cancelled',
        'UNSTABLE': 'failed',
        'IN_PROGRESS': 'running',
        'NOT_BUILT': 'pending',
        # GitLab CI
        'success': 'success',
        'failed': 'failed',
        'canceled': 'cancelled',
        'cancelled': 'cancelled',
        'running': 'running',
        'pending': 'pending',
        'created': 'pending',
        'manual': 'pending',
        # GitHub Actions
        'completed': 'success',
        'failure': 'failed',
        'cancelled': 'cancelled',
        'in_progress': 'running',
        'queued': 'pending',
        'requested': 'pending',
        # 通用状态
        'unknown': 'running',
        'error': 'failed'
    }
    
    return status_mapping.get(external_status.lower(), 'running')


async def _update_step_executions_status(execution: PipelineExecution, pipeline_status: str):
    """更新步骤执行状态"""
    from asgiref.sync import sync_to_async
    from .models import StepExecution
    
    try:
        logger.info(f"Updating step executions for pipeline {execution.id} to status {pipeline_status}")
        
        # 获取所有步骤执行记录（预取关联对象）
        step_executions = await sync_to_async(list)(
            StepExecution.objects.filter(pipeline_execution=execution)
            .select_related('atomic_step')
            .order_by('order')
        )
        
        if not step_executions:
            logger.info(f"No step executions found for pipeline execution {execution.id}")
            return
        
        logger.info(f"Found {len(step_executions)} step executions for pipeline {execution.id}")
        for i, step in enumerate(step_executions):
            # 由于我们使用了 select_related，atomic_step 已经预取，可以安全访问
            logger.info(f"  Step {i+1}: {step.atomic_step.name} - current status: {step.status}")
        
        # 根据流水线状态更新步骤状态
        if pipeline_status == 'running':
            # 如果流水线正在运行，将第一个步骤设为running，其他保持pending
            for i, step_exec in enumerate(step_executions):
                if i == 0 and step_exec.status == 'pending':
                    step_exec.status = 'running'
                    step_exec.started_at = timezone.now()
                    await sync_to_async(step_exec.save)()
                    logger.info(f"Updated step {step_exec.atomic_step.name} to running")
                    break
        
        elif pipeline_status in ['success', 'failed', 'cancelled', 'timeout']:
            # 如果流水线完成，更新所有步骤状态
            if pipeline_status == 'success':
                final_step_status = 'success'
            elif pipeline_status == 'timeout':
                final_step_status = 'timeout'
            else:
                final_step_status = 'failed'  # failed, cancelled 都映射为 failed
            
            logger.info(f"Setting all pending/running steps to {final_step_status}")
            
            updated_count = 0
            for step_exec in step_executions:
                if step_exec.status in ['pending', 'running']:
                    logger.info(f"Updating step {step_exec.atomic_step.name} from {step_exec.status} to {final_step_status}")
                    step_exec.status = final_step_status
                    step_exec.completed_at = timezone.now()
                    if not step_exec.started_at:
                        step_exec.started_at = step_exec.completed_at
                    await sync_to_async(step_exec.save)()
                    updated_count += 1
                    logger.info(f"Successfully updated step {step_exec.atomic_step.name} to {final_step_status}")
                else:
                    logger.info(f"Step {step_exec.atomic_step.name} already has final status {step_exec.status}")
            
            logger.info(f"Updated {updated_count} step executions to {final_step_status}")
        
        logger.info(f"Finished updating step executions for pipeline {execution.id}")
        
    except Exception as e:
        logger.error(f"Failed to update step execution status for pipeline {execution.id}: {e}", exc_info=True)
