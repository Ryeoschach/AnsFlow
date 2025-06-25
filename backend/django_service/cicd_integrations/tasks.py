"""
Celery tasks for CI/CD operations
Implement background processing for pipeline execution, tool management, and notifications
"""
from celery import shared_task
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

logger = logging.getLogger(__name__)


@shared_task(bind=True, retry_kwargs={'max_retries': 3, 'countdown': 60})
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
        
        # 创建异步事件循环执行流水线
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        engine = UnifiedCICDEngine()
        result = loop.run_until_complete(engine._perform_execution(execution_id))
        
        loop.close()
        
        logger.info(f"Pipeline execution {execution_id} completed successfully")
        return {"status": "success", "execution_id": execution_id}
        
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


@shared_task(bind=True)
def health_check_tools(self):
    """
    定期健康检查所有CI/CD工具
    """
    tools = CICDTool.objects.filter(is_active=True)
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
            tool.health_status = 'healthy' if is_healthy else 'unhealthy'
            tool.save(update_fields=['last_health_check', 'health_status'])
            
            results.append({
                'tool_id': tool.id,
                'tool_name': tool.name,
                'tool_type': tool.tool_type,
                'status': 'healthy' if is_healthy else 'unhealthy'
            })
            
            logger.info(f"Health check for tool {tool.name}: {'healthy' if is_healthy else 'unhealthy'}")
            
        except Exception as e:
            tool.health_status = 'error'
            tool.last_health_check = timezone.now()
            tool.save(update_fields=['health_status', 'last_health_check'])
            
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


@shared_task
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


@shared_task
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
