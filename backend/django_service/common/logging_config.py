"""
AnsFlow Django 服务日志配置模块
基于统一日志标准的 Django 专用配置
"""

import logging
import json
import redis
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from django.conf import settings
from pathlib import Path

# 导入统一日志配置
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow')
from common.unified_logging import get_logger, AnsFlowLogManager, AnsFlowJSONFormatter
import os
import json
import logging
import logging.handlers
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

import structlog
import redis
from django.conf import settings


class SensitiveDataFilter:
    """敏感信息过滤器"""
    
    SENSITIVE_FIELDS = {
        'password', 'passwd', 'pwd', 'token', 'key', 'secret', 
        'authorization', 'cookie', 'session', 'csrf'
    }
    
    def filter(self, record):
        """Django日志过滤器接口"""
        # 过滤日志记录中的敏感数据
        if hasattr(record, 'extra') and isinstance(record.extra, dict):
            record.extra = self.filter_sensitive_data(record.extra)
        
        # 过滤日志消息中的敏感信息
        if hasattr(record, 'args') and record.args:
            # 将args转换为字符串进行检查
            args_str = str(record.args)
            for sensitive_field in self.SENSITIVE_FIELDS:
                if sensitive_field in args_str.lower():
                    # 如果发现敏感信息，标记这条记录需要特殊处理
                    record.sensitive_detected = True
                    break
        
        return True  # 仍然允许记录通过，但已进行敏感数据处理
    
    @classmethod
    def filter_sensitive_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤敏感信息"""
        if not isinstance(data, dict):
            return data
            
        filtered_data = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            # 检查是否为敏感字段
            if any(sensitive in key_lower for sensitive in cls.SENSITIVE_FIELDS):
                if isinstance(value, str) and len(value) > 8:
                    # 保留前3位，其余用*代替
                    filtered_data[key] = value[:3] + '*' * (len(value) - 3)
                else:
                    filtered_data[key] = '******'
            elif isinstance(value, dict):
                filtered_data[key] = cls.filter_sensitive_data(value)
            elif isinstance(value, list):
                filtered_data[key] = [
                    cls.filter_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                filtered_data[key] = value
                
        return filtered_data


class AnsFlowJSONFormatter(logging.Formatter):
    """AnsFlow自定义JSON格式化器"""
    
    def __init__(self, service_name='django'):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record):
        # 基础日志结构
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'service': getattr(record, 'service', self.service_name),
            'module': record.name,
            'message': record.getMessage(),
        }
        
        # 添加请求上下文信息
        if hasattr(record, 'request_id'):
            log_data['trace_id'] = f"req_{record.request_id}"
            
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
            
        if hasattr(record, 'user_name'):
            log_data['user_name'] = record.user_name
            
        if hasattr(record, 'ip'):
            log_data['ip'] = record.ip
            
        if hasattr(record, 'method'):
            log_data['method'] = record.method
            
        if hasattr(record, 'path'):
            log_data['path'] = record.path
            
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
            
        if hasattr(record, 'response_time_ms'):
            log_data['response_time_ms'] = record.response_time_ms
            
        # 添加额外信息
        if hasattr(record, 'extra'):
            extra_data = SensitiveDataFilter.filter_sensitive_data(record.extra)
            log_data['extra'] = extra_data
            
        # 添加标签
        if hasattr(record, 'labels'):
            log_data['labels'] = record.labels
            
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)


class RedisLogHandler(logging.Handler):
    """Redis日志处理器 - 直接写入统一日志Stream"""
    
    def __init__(self, redis_client=None, stream_name='ansflow:logs:stream', max_len=10000):
        super().__init__()
        
        # 如果没有提供redis_client，尝试从数据库配置创建
        if redis_client is None:
            try:
                # 延迟导入，避免在Django应用加载前导入模型
                from django.apps import apps
                from django.conf import settings
                
                # 检查Django应用是否已加载
                if not apps.ready:
                    # 如果应用未加载，使用默认配置
                    redis_config = {
                        'LOGGING_REDIS_HOST': 'localhost',
                        'LOGGING_REDIS_PORT': 6379,
                        'LOGGING_REDIS_DB': 5
                    }
                    logging.getLogger(__name__).warning("Django应用未完全加载，使用默认Redis配置")
                else:
                    # 应用已加载，从数据库获取配置
                    from settings_management.models import GlobalConfig
                    redis_config = GlobalConfig.get_config_dict()
                
                redis_client = redis.Redis(
                    host=redis_config.get('LOGGING_REDIS_HOST', 'localhost'),
                    port=int(redis_config.get('LOGGING_REDIS_PORT', 6379)),
                    db=int(redis_config.get('LOGGING_REDIS_DB', 5)),  # 使用统一日志DB
                    decode_responses=False
                )
                # 测试连接
                redis_client.ping()
                logging.getLogger(__name__).info(f"Django Redis日志处理器连接成功: db={redis_config.get('LOGGING_REDIS_DB', 5)}")
            except Exception as e:
                # Redis不可用时，设置为None
                redis_client = None
                logging.getLogger(__name__).warning(f"Django Redis连接失败，将跳过Redis日志: {e}")
        
        self.redis_client = redis_client
        self.stream_name = stream_name
        self.max_len = max_len
        self.service_name = 'django_service'
        
    def emit(self, record):
        try:
            # 如果Redis不可用，直接返回
            if self.redis_client is None:
                return
                
            # 生成唯一日志ID
            import uuid
            log_id = f"django-{int(datetime.now().timestamp() * 1000)}-{uuid.uuid4().hex[:8]}"
            
            # 构造统一格式的日志字段
            fields = {
                'log_id': log_id,
                'timestamp': datetime.now().isoformat(),
                'level': record.levelname,
                'service': getattr(record, 'service', self.service_name),
                'component': record.name.split('.')[-1] if '.' in record.name else record.name,
                'module': record.module or record.name,
                'message': record.getMessage(),
            }
            
            # 添加执行ID（如果有）
            if hasattr(record, 'execution_id') and record.execution_id:
                fields['execution_id'] = str(record.execution_id)
                
            # 添加额外数据
            if hasattr(record, 'extra') and record.extra:
                fields['extra_data'] = json.dumps(record.extra, ensure_ascii=False)
            
            # 写入Redis Stream（使用统一格式）
            result = self.redis_client.xadd(
                self.stream_name,
                fields,
                maxlen=self.max_len,
                approximate=True
            )
            
        except Exception as e:
            # 日志写入失败时，记录错误但不影响主业务
            error_logger = logging.getLogger(__name__)
            error_logger.error(f"Django Redis日志写入失败: {e}")
            pass


class AnsFlowLoggingConfig:
    """AnsFlow日志配置管理"""
    
    def __init__(self):
        self.log_level = getattr(settings, 'LOG_LEVEL', 'INFO')
        self.log_dir = Path(getattr(settings, 'LOG_DIR', '/Users/creed/Workspace/OpenSource/ansflow/logs'))
        self.log_format = getattr(settings, 'LOG_FORMAT', 'json')
        self.redis_enabled = getattr(settings, 'LOGGING_ENABLE_REDIS', False)
        self.websocket_enabled = getattr(settings, 'LOGGING_ENABLE_WEBSOCKET', True)
        self.log_rotation = getattr(settings, 'LOG_ROTATION', 'daily')
        self.log_retention_days = getattr(settings, 'LOG_RETENTION_DAYS', 30)
        
        # 确保日志目录存在
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def get_file_handler(self, service_name: str, level: str) -> logging.Handler:
        """获取文件处理器"""
        log_file = self.log_dir / f"{service_name}_{level.lower()}.log"
        
        if self.log_rotation == 'daily':
            handler = logging.handlers.TimedRotatingFileHandler(
                log_file,
                when='midnight',
                interval=1,
                backupCount=self.log_retention_days,
                encoding='utf-8'
            )
        elif self.log_rotation == 'hourly':
            handler = logging.handlers.TimedRotatingFileHandler(
                log_file,
                when='H',
                interval=1,
                backupCount=self.log_retention_days * 24,
                encoding='utf-8'
            )
        else:  # weekly
            handler = logging.handlers.TimedRotatingFileHandler(
                log_file,
                when='W0',  # Monday
                interval=1,
                backupCount=self.log_retention_days // 7,
                encoding='utf-8'
            )
            
        # 设置日志格式
        if self.log_format == 'json':
            handler.setFormatter(AnsFlowJSONFormatter())
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
        return handler
        
    def get_redis_handler(self) -> Optional[logging.Handler]:
        """获取Redis处理器"""
        if not self.redis_enabled:
            return None
            
        try:
            redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_LOG_DB', 1),
                decode_responses=False
            )
            # 测试连接
            redis_client.ping()
            return RedisLogHandler(redis_client)
        except Exception:
            # Redis不可用时，继续使用文件日志
            return None
    
    def setup_logging(self):
        """设置日志配置"""
        # 获取根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level))
        
        # 清除现有处理器
        root_logger.handlers.clear()
        
        # 添加文件处理器 - 分级别存储
        for level in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
            if getattr(logging, level) >= getattr(logging, self.log_level):
                handler = self.get_file_handler('django', level)
                handler.setLevel(getattr(logging, level))
                
                # 只记录当前级别的日志
                handler.addFilter(lambda record, lvl=level: record.levelname == lvl)
                root_logger.addHandler(handler)
        
        # 添加Redis处理器（如果可用）
        if self.redis_enabled:
            try:
                from .redis_logging import setup_redis_logging
                if setup_redis_logging():
                    logging.getLogger(__name__).info("Redis日志流已启用")
            except ImportError as e:
                logging.getLogger(__name__).warning(f"Redis日志流不可用: {e}")
        
        # 添加WebSocket处理器（如果可用）
        if self.websocket_enabled:
            try:
                from .websocket_logging import setup_websocket_logging
                if setup_websocket_logging():
                    logging.getLogger(__name__).info("WebSocket日志推送已启用")
            except ImportError as e:
                logging.getLogger(__name__).warning(f"WebSocket日志推送不可用: {e}")
        
        # 添加控制台处理器（开发环境）
        if settings.DEBUG:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            
            if self.log_format == 'json':
                console_handler.setFormatter(AnsFlowJSONFormatter())
            else:
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                console_handler.setFormatter(formatter)
                
            root_logger.addHandler(console_handler)
        
        # 配置第三方库日志级别
        logging.getLogger('django.db.backends').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)


# 全局日志配置实例
logging_config = AnsFlowLoggingConfig()


def get_logger(name: str) -> logging.Logger:
    """获取日志器"""
    return logging.getLogger(name)


def log_with_context(logger: logging.Logger, level: str, message: str, 
                    request=None, extra: Dict[str, Any] = None, 
                    labels: list = None):
    """带上下文信息的日志记录"""
    record_extra = {}
    
    # 添加请求上下文
    if request:
        record_extra.update({
            'request_id': getattr(request, 'id', None),
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            'user_name': getattr(request.user, 'username', None) if hasattr(request, 'user') else None,
            'ip': get_client_ip(request),
            'method': getattr(request, 'method', None),
            'path': getattr(request, 'path', None),
        })
    
    # 添加额外信息
    if extra:
        record_extra['extra'] = extra
        
    # 添加标签
    if labels:
        record_extra['labels'] = labels
    
    # 记录日志
    getattr(logger, level.lower())(message, extra=record_extra)


def get_client_ip(request) -> Optional[str]:
    """获取客户端IP地址"""
    if not request:
        return None
        
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
