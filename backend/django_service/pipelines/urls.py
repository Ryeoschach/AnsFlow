"""
URL configuration for pipelines app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'pipelines', views.PipelineViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('health/', views.pipeline_health, name='pipeline-health'),
]
