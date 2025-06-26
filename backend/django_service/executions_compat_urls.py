"""
executions API 兼容性路由配置
为了支持前端直接访问 /api/v1/executions/ 路径
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from cicd_integrations.views import PipelineExecutionViewSet

# 为executions创建独立的路由器
executions_router = DefaultRouter()
executions_router.register(r'executions', PipelineExecutionViewSet)

urlpatterns = [
    path('', include(executions_router.urls)),
]
