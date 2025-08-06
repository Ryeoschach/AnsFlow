"""
日志管理URL配置 - Phase 3历史分析功能
"""

from django.urls import path
from .views_extra_logging import (
    LogFileIndexView,
    LogSearchView,
    LogAnalysisView,
    LogExportView,
    log_config_view,
    log_stats_view,
    PrometheusMetricsView,
    log_metrics_json_view
)

app_name = 'logging'

urlpatterns = [
    # Phase 3: 历史分析功能
    path('index/', LogFileIndexView.as_view(), name='log_index'),
    path('search/', LogSearchView.as_view(), name='log_search'),
    path('analysis/', LogAnalysisView.as_view(), name='log_analysis'),
    path('export/', LogExportView.as_view(), name='log_export'),
    
    # 配置和统计API
    path('config/', log_config_view, name='log_config'),
    path('stats/', log_stats_view, name='log_stats'),
    
    # Phase 3: Prometheus指标集成
    path('metrics/', PrometheusMetricsView.as_view(), name='prometheus_metrics'),
    path('metrics/json/', log_metrics_json_view, name='log_metrics_json'),
    
    # 兼容性路由（保持向后兼容）
    path('logs/', LogSearchView.as_view(), name='log_management'),
    path('stream/', log_stats_view, name='log_stream'),
]
