"""
URL configuration for pipelines app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'pipelines', views.PipelineViewSet)
router.register(r'pipeline-mappings', views.PipelineToolMappingViewSet)
router.register(r'parallel-groups', views.ParallelGroupViewSet)
router.register(r'approval-requests', views.ApprovalRequestViewSet)
router.register(r'workflow-executions', views.WorkflowExecutionViewSet)
router.register(r'step-execution-history', views.StepExecutionHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('health/', views.pipeline_health, name='pipeline-health'),
]
