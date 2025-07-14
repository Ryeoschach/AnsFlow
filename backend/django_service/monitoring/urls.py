"""
Monitoring URLs for Django service.
"""

from django.urls import path
from .health import HealthCheckView, DetailedHealthView
from .prometheus import CustomMetricsView

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health'),
    path('health/detailed/', DetailedHealthView.as_view(), name='detailed-health'),
    path('metrics/custom/', CustomMetricsView.as_view(), name='custom-metrics'),
]
