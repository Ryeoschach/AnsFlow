"""
CI/CD 集成应用 URL 配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CICDToolViewSet, AtomicStepViewSet, PipelineExecutionViewSet, GitCredentialViewSet

# 创建路由器
router = DefaultRouter()
router.register(r'tools', CICDToolViewSet)
router.register(r'atomic-steps', AtomicStepViewSet)
router.register(r'executions', PipelineExecutionViewSet)
router.register(r'git-credentials', GitCredentialViewSet)

app_name = 'cicd_integrations'

urlpatterns = [
    path('', include(router.urls)),
]
