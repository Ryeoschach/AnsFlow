"""
WebSocket URL routing for real-time monitoring.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Pipeline execution monitoring
    re_path(
        r'ws/executions/(?P<execution_id>\d+)/$',
        consumers.PipelineMonitorConsumer.as_asgi()
    ),
    
    # Global system monitoring
    re_path(
        r'ws/monitor/$',
        consumers.GlobalMonitorConsumer.as_asgi()
    ),
]
