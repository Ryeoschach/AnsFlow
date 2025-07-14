"""
Django apps configuration for monitoring module.
"""

from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    """Monitoring app configuration."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitoring'
    verbose_name = 'AnsFlow Monitoring'
    
    def ready(self):
        """Initialize monitoring when app is ready."""
        # Import signal handlers if any
        # from . import signals
        pass
