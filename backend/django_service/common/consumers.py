"""
WebSocket消费者模块
从websocket_logging导入实际的Consumer类
"""
from .websocket_logging import RealTimeLogConsumer

# 导出消费者类
__all__ = ['RealTimeLogConsumer']
