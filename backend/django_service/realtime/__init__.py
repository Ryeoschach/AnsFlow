"""
Realtime monitoring application for AnsFlow.
Handles WebSocket connections for pipeline execution monitoring.
"""

from django.apps import AppConfig


class RealtimeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'realtime'
    verbose_name = 'Real-time Monitoring'
