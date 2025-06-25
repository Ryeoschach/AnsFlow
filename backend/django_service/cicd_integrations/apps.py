from django.apps import AppConfig


class CicdIntegrationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cicd_integrations'
    verbose_name = 'CI/CD Integrations'
    
    def ready(self):
        """应用启动时的初始化"""
        pass
