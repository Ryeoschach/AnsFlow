"""
实时日志WebSocket服务
提供实时日志流推送功能
"""
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass, asdict

try:
    from channels.generic.websocket import AsyncWebsocketConsumer
    from channels.exceptions import DenyConnection
    CHANNELS_AVAILABLE = True
except ImportError:
    # 如果Django Channels不可用，创建基础WebSocket接口
    CHANNELS_AVAILABLE = False
    
    class AsyncWebsocketConsumer:
        """基础WebSocket消费者接口"""
        pass


@dataclass
class LogFilter:
    """日志过滤器配置"""
    levels: List[str] = None  # ['ERROR', 'WARNING', 'INFO', 'DEBUG']
    services: List[str] = None  # ['django', 'fastapi']
    keywords: List[str] = None  # 关键字搜索
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    user_id: Optional[int] = None
    
    def __post_init__(self):
        if self.levels is None:
            self.levels = ['ERROR', 'WARNING', 'INFO']
        if self.services is None:
            self.services = []
        if self.keywords is None:
            self.keywords = []
    
    def matches(self, log_entry: Dict[str, Any]) -> bool:
        """检查日志条目是否匹配过滤条件"""
        # 检查日志级别
        if self.levels and log_entry.get('level') not in self.levels:
            return False
            
        # 检查服务
        if self.services and log_entry.get('service') not in self.services:
            return False
            
        # 检查关键字
        if self.keywords:
            message = log_entry.get('message', '').lower()
            if not any(keyword.lower() in message for keyword in self.keywords):
                return False
                
        # 检查时间范围
        if self.start_time or self.end_time:
            try:
                log_time = datetime.fromisoformat(log_entry.get('timestamp', ''))
                if self.start_time and log_time < self.start_time:
                    return False
                if self.end_time and log_time > self.end_time:
                    return False
            except (ValueError, TypeError):
                pass
                
        # 检查用户ID
        if self.user_id and log_entry.get('user_id') != self.user_id:
            return False
            
        return True


class BufferedLogManager:
    """缓冲日志管理器"""
    
    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self.log_buffer: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    def add_log(self, log_entry: Dict[str, Any]):
        """添加日志到缓冲区"""
        self.log_buffer.append(log_entry)
        
        # 保持缓冲区大小
        if len(self.log_buffer) > self.buffer_size:
            self.log_buffer.pop(0)
    
    def get_recent_logs(self, count: int = 50, log_filter: LogFilter = None) -> List[Dict[str, Any]]:
        """获取最近的日志"""
        logs = self.log_buffer[-count:] if count else self.log_buffer[:]
        
        # 应用过滤器
        if log_filter:
            logs = [log for log in logs if log_filter.matches(log)]
        
        return logs
    
    def clear_buffer(self):
        """清空缓冲区"""
        self.log_buffer.clear()
    
    def get_buffer_stats(self) -> Dict[str, Any]:
        """获取缓冲区统计信息"""
        return {
            'buffer_size': len(self.log_buffer),
            'max_size': self.buffer_size,
            'usage_percent': (len(self.log_buffer) / self.buffer_size) * 100
        }


class RealTimeLogConsumer(AsyncWebsocketConsumer):
    """实时日志WebSocket消费者"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = "logs_realtime"
        self.log_filter = LogFilter()
        self.logger = logging.getLogger(__name__)
        self.is_authenticated = False
        self.user_permissions = set()
        
    async def connect(self):
        """WebSocket连接处理"""
        try:
            # 检查用户权限
            if not await self.check_permissions():
                await self.close(code=4003)  # 权限不足
                return
                
            # 加入房间组
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            self.is_authenticated = True
            
            # 发送连接成功消息
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': '实时日志连接已建立',
                'timestamp': datetime.now().isoformat()
            }))
            
            self.logger.info(f"WebSocket日志连接建立: {self.channel_name}")
            
        except Exception as e:
            self.logger.error(f"WebSocket连接失败: {e}")
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """WebSocket断开处理"""
        if self.is_authenticated:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
        self.logger.info(f"WebSocket日志连接断开: {self.channel_name}, 代码: {close_code}")
    
    async def receive(self, text_data):
        """接收WebSocket消息"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'update_filter':
                await self.update_filter(data.get('filter', {}))
            elif message_type == 'get_recent_logs':
                await self.send_recent_logs(data.get('count', 50))
            elif message_type == 'ping':
                await self.send_pong()
            else:
                self.logger.warning(f"未知消息类型: {message_type}")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"WebSocket消息解析失败: {e}")
            await self.send_error("消息格式错误")
        except Exception as e:
            self.logger.error(f"WebSocket消息处理失败: {e}")
            await self.send_error("消息处理失败")
    
    async def check_permissions(self) -> bool:
        """检查用户权限"""
        try:
            user = self.scope.get('user')
            if not user or not user.is_authenticated:
                return False
                
            # 检查是否有查看日志的权限
            if user.is_superuser:
                self.user_permissions.add('view_all_logs')
                return True
                
            # 检查具体权限
            if user.has_perm('logs.view_logs'):
                self.user_permissions.add('view_logs')
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"权限检查失败: {e}")
            return False
    
    async def update_filter(self, filter_data: Dict[str, Any]):
        """更新日志过滤器"""
        try:
            # 解析过滤条件
            self.log_filter = LogFilter(
                levels=filter_data.get('levels', ['ERROR', 'WARNING', 'INFO']),
                services=filter_data.get('services', []),
                keywords=filter_data.get('keywords', []),
                user_id=filter_data.get('user_id')
            )
            
            # 处理时间范围
            if filter_data.get('start_time'):
                self.log_filter.start_time = datetime.fromisoformat(filter_data['start_time'])
            if filter_data.get('end_time'):
                self.log_filter.end_time = datetime.fromisoformat(filter_data['end_time'])
            
            await self.send(text_data=json.dumps({
                'type': 'filter_updated',
                'message': '过滤条件已更新',
                'filter': asdict(self.log_filter)
            }))
            
            self.logger.info(f"日志过滤器已更新: {self.channel_name}")
            
        except Exception as e:
            self.logger.error(f"更新过滤器失败: {e}")
            await self.send_error("过滤器更新失败")
    
    async def send_recent_logs(self, count: int = 50):
        """发送最近的日志"""
        try:
            # 从Redis日志流或文件中获取最近的日志
            from .redis_logging import get_redis_log_streams
            
            redis_streams = get_redis_log_streams()
            if redis_streams:
                recent_logs = redis_streams.read_logs_stream(count=count, start_id='0')
            else:
                # 如果Redis不可用，从文件中读取
                recent_logs = await self.read_logs_from_file(count)
            
            # 应用过滤器
            filtered_logs = [
                log for log in recent_logs 
                if self.log_filter.matches(log)
            ]
            
            await self.send(text_data=json.dumps({
                'type': 'recent_logs',
                'logs': filtered_logs[-count:],  # 最新的count条
                'total': len(filtered_logs)
            }))
            
        except Exception as e:
            self.logger.error(f"获取最近日志失败: {e}")
            await self.send_error("获取日志失败")
    
    async def send_pong(self):
        """发送pong响应"""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': datetime.now().isoformat()
        }))
    
    async def send_error(self, message: str):
        """发送错误消息"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }))
    
    async def read_logs_from_file(self, count: int = 50) -> List[Dict[str, Any]]:
        """从日志文件读取最近的日志"""
        logs = []
        try:
            # 这里简化实现，实际应该从日志文件中读取
            import os
            from pathlib import Path
            
            log_dir = Path('/Users/creed/Workspace/OpenSource/ansflow/logs')
            if log_dir.exists():
                # 读取最新的日志文件
                log_files = sorted(log_dir.glob('*.log'), key=os.path.getmtime, reverse=True)
                
                for log_file in log_files[:3]:  # 最多读取3个文件
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()[-count:]  # 读取最后count行
                            
                            for line in lines:
                                try:
                                    log_entry = json.loads(line.strip())
                                    logs.append(log_entry)
                                except json.JSONDecodeError:
                                    pass
                                    
                    except Exception as e:
                        self.logger.warning(f"读取日志文件失败 {log_file}: {e}")
                        
        except Exception as e:
            self.logger.error(f"从文件读取日志失败: {e}")
            
        return logs[-count:]  # 返回最新的count条
    
    # 接收来自房间组的消息
    async def log_message(self, event):
        """处理来自房间组的日志消息"""
        try:
            log_data = event['log_data']
            
            # 应用过滤器
            if self.log_filter.matches(log_data):
                await self.send(text_data=json.dumps({
                    'type': 'new_log',
                    'log': log_data,
                    'timestamp': datetime.now().isoformat()
                }))
                
        except Exception as e:
            self.logger.error(f"发送日志消息失败: {e}")


class LogWebSocketService:
    """日志WebSocket服务管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_connections: Set[str] = set()
        
    async def broadcast_log(self, log_data: Dict[str, Any]):
        """广播日志到所有连接的客户端"""
        if not CHANNELS_AVAILABLE:
            return
            
        try:
            from channels.layers import get_channel_layer
            
            channel_layer = get_channel_layer()
            if channel_layer:
                await channel_layer.group_send(
                    "logs_realtime",
                    {
                        'type': 'log_message',
                        'log_data': log_data
                    }
                )
                
        except Exception as e:
            self.logger.error(f"广播日志失败: {e}")
    
    def get_connection_count(self) -> int:
        """获取活跃连接数"""
        return len(self.active_connections)


# 全局WebSocket服务实例
_websocket_service: Optional[LogWebSocketService] = None


def get_websocket_service() -> LogWebSocketService:
    """获取全局WebSocket服务实例"""
    global _websocket_service
    
    if _websocket_service is None:
        _websocket_service = LogWebSocketService()
        
    return _websocket_service


# 自定义日志处理器，支持WebSocket推送
class WebSocketLogHandler(logging.Handler):
    """WebSocket日志处理器"""
    
    def __init__(self):
        super().__init__()
        self.websocket_service = get_websocket_service()
        self.logger = logging.getLogger(f"{__name__}.WebSocketLogHandler")
        
    def emit(self, record: logging.LogRecord):
        """发送日志记录到WebSocket"""
        try:
            # 格式化日志记录
            log_data = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'service': getattr(record, 'service', 'unknown'),
                'logger': record.name,
                'message': record.getMessage(),
            }
            
            # 添加额外信息
            if hasattr(record, 'trace_id'):
                log_data['trace_id'] = record.trace_id
            if hasattr(record, 'user_id'):
                log_data['user_id'] = record.user_id
            if hasattr(record, 'extra'):
                log_data['extra'] = record.extra
            if hasattr(record, 'labels'):
                log_data['labels'] = record.labels
                
            # 异步广播（如果可能）
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.websocket_service.broadcast_log(log_data))
                else:
                    asyncio.run(self.websocket_service.broadcast_log(log_data))
            except RuntimeError:
                # 没有运行的事件循环，跳过WebSocket推送
                pass
                
        except Exception as e:
            self.logger.error(f"WebSocket日志处理失败: {e}")


def setup_websocket_logging():
    """设置WebSocket日志推送"""
    if CHANNELS_AVAILABLE:
        # 创建WebSocket日志处理器
        ws_handler = WebSocketLogHandler()
        ws_handler.setLevel(logging.INFO)
        
        # 添加到根日志器
        root_logger = logging.getLogger()
        root_logger.addHandler(ws_handler)
        
        return True
    return False
