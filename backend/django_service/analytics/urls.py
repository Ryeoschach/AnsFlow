from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('execution-stats/', views.execution_stats, name='execution_stats'),
    path('execution-trends/', views.execution_trends, name='execution_trends'),
    path('pipeline-stats/', views.pipeline_stats, name='pipeline_stats'),
    path('recent-executions/', views.recent_executions, name='recent_executions'),
]
