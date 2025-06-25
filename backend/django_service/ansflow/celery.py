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
    'cleanup-old-logs': {
        'task': 'audit.tasks.cleanup_old_logs',
        'schedule': 86400.0,  # 24 hours
    },
    'check-pipeline-health': {
        'task': 'pipelines.tasks.check_pipeline_health',
        'schedule': 300.0,  # 5 minutes
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
