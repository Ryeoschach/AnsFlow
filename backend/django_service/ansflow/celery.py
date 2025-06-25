"""
Celery configuration for AnsFlow Django service.
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

app = Celery('ansflow')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule configuration
app.conf.beat_schedule = {
    # CI/CD related tasks
    'health-check-tools': {
        'task': 'cicd_integrations.tasks.health_check_tools',
        'schedule': 300.0,  # 5 minutes
    },
    'cleanup-old-executions': {
        'task': 'cicd_integrations.tasks.cleanup_old_executions',
        'schedule': 86400.0,  # 24 hours
    },
    'generate-execution-reports': {
        'task': 'cicd_integrations.tasks.generate_execution_reports',
        'schedule': 3600.0,  # 1 hour
    },
    'monitor-long-running-executions': {
        'task': 'cicd_integrations.tasks.monitor_long_running_executions',
        'schedule': 1800.0,  # 30 minutes
    },
    'backup-pipeline-configurations': {
        'task': 'cicd_integrations.tasks.backup_pipeline_configurations',
        'schedule': 43200.0,  # 12 hours
    },
    # Legacy tasks (if they exist)
    'cleanup-old-logs': {
        'task': 'audit.tasks.cleanup_old_logs',
        'schedule': 86400.0,  # 24 hours
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
