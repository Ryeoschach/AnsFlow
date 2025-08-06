"""
Redis日志流处理模块
实现Redis Streams异步日志写入和实时日志流功能
"""
import json
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

try:
    import redis
    from redis.exceptions import RedisError, ConnectionError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@dataclass
class LogStreamConfig:
    """日志流配置"""
    stream_name: str = 'ansflow:logs'
    consumer_group: str = 'log_processors'
    batch_size: int = 100
    max_len: int = 10000
    retention_hours: int = 24
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'stream_name': self.stream_name,
            'consumer_group': self.consumer_group,
            'batch_size': self.batch_size,
            'max_len': self.max_len,
            'retention_hours': self.retention_hours
        }
    
    
class RedisLogStreams:
    """Redis日志流管理器"""
    
    def __init__(self, config: LogStreamConfig = None):
        self.config = config or LogStreamConfig()
        self.redis_client: Optional[redis.Redis] = None
        self.logger = logging.getLogger(__name__)
        self._connected = False
        
    def connect(self, redis_config: Dict[str, Any] = None) -> bool:
        """连接到Redis"""
        if not REDIS_AVAILABLE:
            self.logger.warning("Redis库不可用，跳过Redis日志流集成")
            return False
            
        try:
            redis_config = redis_config or {
                'host': 'localhost',
                'port': 6379,
                'db': 1,  # 使用数据库1专门存储日志流
                'decode_responses': False,
                'socket_timeout': 5,
                'socket_connect_timeout': 5,
                'retry_on_timeout': True,
                'health_check_interval': 30
            }
            
            self.redis_client = redis.Redis(**redis_config)
            
            # 测试连接
            self.redis_client.ping()
            
            # 创建消费者组（如果不存在）
            try:
                self.redis_client.xgroup_create(
                    self.config.stream_name,
                    self.config.consumer_group,
                    id='0',
                    mkstream=True
                )
            except redis.exceptions.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise
                    
            self._connected = True
            self.logger.info(f"Redis日志流连接成功: {self.config.stream_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Redis日志流连接失败: {e}")
            self._connected = False
            return False
    
    async def write_log_async(self, log_data: Dict[str, Any]) -> bool:
        """异步写入日志到Redis流"""
        if not self._connected or not self.redis_client:
            return False
            
        try:
            # 准备数据
            stream_data = {
                'timestamp': str(time.time()),
                'data': json.dumps(log_data, ensure_ascii=False)
            }
            
            # 写入流，使用MAXLEN限制流长度
            self.redis_client.xadd(
                self.config.stream_name,
                stream_data,
                maxlen=self.config.max_len,
                approximate=True
            )
            
            return True
            
        except RedisError as e:
            self.logger.error(f"Redis日志写入失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"日志序列化失败: {e}")
            return False
    
    async def log_async(self, level: str, message: str, service: str = 'unknown', 
                       source: str = 'unknown', **kwargs) -> bool:
        """便捷的异步日志记录方法"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': level.upper(),
            'service': service,
            'source': source,
            'message': message,
            **kwargs
        }
        return await self.write_log_async(log_data)
    
    def write_log_sync(self, log_data: Dict[str, Any]) -> bool:
        """同步写入日志到Redis流"""
        if not self._connected or not self.redis_client:
            return False
            
        try:
            # 准备数据
            stream_data = {
                'timestamp': str(time.time()),
                'data': json.dumps(log_data, ensure_ascii=False)
            }
            
            # 写入流
            self.redis_client.xadd(
                self.config.stream_name,
                stream_data,
                maxlen=self.config.max_len,
                approximate=True
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Redis日志写入失败: {e}")
            return False
    
    def read_logs_stream(self, count: int = 100, start_id: str = '$') -> List[Dict[str, Any]]:
        """读取日志流数据"""
        if not self._connected or not self.redis_client:
            return []
            
        try:
            # 从流中读取数据
            messages = self.redis_client.xread({
                self.config.stream_name: start_id
            }, count=count, block=1000)  # 阻塞1秒
            
            logs = []
            for stream_name, stream_messages in messages:
                for message_id, fields in stream_messages:
                    try:
                        log_data = json.loads(fields[b'data'].decode('utf-8'))
                        log_data['_stream_id'] = message_id.decode('utf-8')
                        logs.append(log_data)
                    except (json.JSONDecodeError, KeyError) as e:
                        self.logger.warning(f"解析日志消息失败: {e}")
                        
            return logs
            
        except Exception as e:
            self.logger.error(f"读取日志流失败: {e}")
            return []
    
    def get_stream_info(self) -> Dict[str, Any]:
        """获取流信息"""
        if not self._connected or not self.redis_client:
            return {}
            
        try:
            info = self.redis_client.xinfo_stream(self.config.stream_name)
            return {
                'length': info.get('length', 0),
                'first_entry': info.get('first-entry'),
                'last_entry': info.get('last-entry'),
                'consumer_groups': info.get('groups', 0)
            }
        except Exception as e:
            self.logger.error(f"获取流信息失败: {e}")
            return {}
    
    def cleanup_old_logs(self, max_age_hours: int = None) -> int:
        """清理旧日志"""
        if not self._connected or not self.redis_client:
            return 0
            
        max_age_hours = max_age_hours or self.config.retention_hours
        cutoff_timestamp = time.time() - (max_age_hours * 3600)
        cutoff_id = f"{int(cutoff_timestamp * 1000)}-0"
        
        try:
            # 删除指定时间戳之前的消息
            deleted = self.redis_client.xtrim(
                self.config.stream_name,
                minid=cutoff_id,
                approximate=True
            )
            
            self.logger.info(f"清理了 {deleted} 条过期日志")
            return deleted
            
        except Exception as e:
            self.logger.error(f"清理日志失败: {e}")
            return 0
    
    def close(self):
        """关闭连接"""
        if self.redis_client:
            try:
                self.redis_client.close()
                self.logger.info("Redis日志流连接已关闭")
            except Exception as e:
                self.logger.error(f"关闭Redis连接失败: {e}")
        
        self._connected = False


class AsyncRedisLogHandler(logging.Handler):
    """异步Redis日志处理器（更新版）"""
    
    def __init__(self, redis_streams: RedisLogStreams):
        super().__init__()
        self.redis_streams = redis_streams
        self.logger = logging.getLogger(f"{__name__}.AsyncRedisLogHandler")
        
    def emit(self, record: logging.LogRecord):
        """发送日志记录到Redis流"""
        try:
            # 格式化日志记录
            log_data = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
            }
            
            # 添加额外信息
            if hasattr(record, 'trace_id'):
                log_data['trace_id'] = record.trace_id
            if hasattr(record, 'user_id'):
                log_data['user_id'] = record.user_id
            if hasattr(record, 'service'):
                log_data['service'] = record.service
            if hasattr(record, 'extra'):
                log_data['extra'] = record.extra
            if hasattr(record, 'labels'):
                log_data['labels'] = record.labels
                
            # 异步写入Redis流
            self.redis_streams.write_log_sync(log_data)
            
        except Exception as e:
            self.logger.error(f"Redis日志处理失败: {e}")


# 全局Redis日志流实例
_redis_log_streams: Optional[RedisLogStreams] = None


def get_redis_log_streams() -> Optional[RedisLogStreams]:
    """获取全局Redis日志流实例"""
    global _redis_log_streams
    
    if _redis_log_streams is None:
        _redis_log_streams = RedisLogStreams()
        
        # 尝试连接Redis
        from django.conf import settings
        redis_config = getattr(settings, 'REDIS_LOG_CONFIG', {
            'host': getattr(settings, 'REDIS_HOST', 'localhost'),
            'port': getattr(settings, 'REDIS_PORT', 6379),
            'db': getattr(settings, 'REDIS_LOG_DB', 1),
        })
        
        if not _redis_log_streams.connect(redis_config):
            _redis_log_streams = None
            
    return _redis_log_streams


def setup_redis_logging():
    """设置Redis日志记录"""
    redis_streams = get_redis_log_streams()
    if redis_streams:
        # 创建Redis日志处理器
        redis_handler = AsyncRedisLogHandler(redis_streams)
        redis_handler.setLevel(logging.INFO)
        
        # 添加到根日志器
        root_logger = logging.getLogger()
        root_logger.addHandler(redis_handler)
        
        return True
    return False
