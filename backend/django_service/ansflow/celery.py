"""
Celery configuration for AnsFlow Django service.
优化版本 - 支持RabbitMQ队列路由和任务优先级
"""

import os
from celery import Celery
from kombu import Queue

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

app = Celery('ansflow')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# RabbitMQ 队列配置
app.conf.task_queues = [
    Queue('high_priority', routing_key='high_priority'),
    Queue('medium_priority', routing_key='medium_priority'),
    Queue('low_priority', routing_key='low_priority'),
]

# 默认交换机和路由配置
app.conf.task_default_exchange = 'ansflow'
app.conf.task_default_exchange_type = 'direct'
app.conf.task_default_routing_key = 'medium_priority'

# Celery beat schedule configuration - 优化任务调度
app.conf.beat_schedule = {
    # 高优先级监控任务
    'health-check-tools': {
        'task': 'cicd_integrations.tasks.health_check_tools',
        'schedule': 300.0,  # 5 minutes
        'options': {'queue': 'medium_priority'},
    },
    'monitor-long-running-executions': {
        'task': 'cicd_integrations.tasks.monitor_long_running_executions',
        'schedule': 1800.0,  # 30 minutes
        'options': {'queue': 'medium_priority'},
    },
    
    # 中等优先级报告任务
    'generate-execution-reports': {
        'task': 'cicd_integrations.tasks.generate_execution_reports',
        'schedule': 3600.0,  # 1 hour
        'options': {'queue': 'medium_priority'},
    },
    
    # 低优先级清理任务
    'cleanup-old-executions': {
        'task': 'cicd_integrations.tasks.cleanup_old_executions',
        'schedule': 86400.0,  # 24 hours
        'options': {'queue': 'low_priority'},
    },
    'backup-pipeline-configurations': {
        'task': 'cicd_integrations.tasks.backup_pipeline_configurations',
        'schedule': 43200.0,  # 12 hours
        'options': {'queue': 'low_priority'},
    },
    'cleanup-old-logs': {
        'task': 'audit.tasks.cleanup_old_logs',
        'schedule': 86400.0,  # 24 hours
        'options': {'queue': 'low_priority'},
    },
}

app.conf.timezone = 'UTC'

# 任务执行优化配置
app.conf.worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
app.conf.worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# 错误处理配置
app.conf.task_reject_on_worker_lost = True
app.conf.task_ignore_result = False

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
