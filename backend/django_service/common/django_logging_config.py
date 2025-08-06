"""
AnsFlow Django 服务统一日志配置模块
基于方案一的标准化日志配置
"""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

# 导入统一日志配置
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow')
try:
    from common.unified_logging import AnsFlowJSONFormatter, AnsFlowLogManager
except ImportError:
    # 如果无法导入，使用本地实现
    class AnsFlowJSONFormatter(logging.Formatter):
        def __init__(self, service_name="django"):
            super().__init__()
            self.service_name = service_name
            
        def format(self, record):
            log_data = {
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "level": record.levelname,
                "service": self.service_name,
                "component": getattr(record, 'component', 'unknown'),
                "module": record.name,
                "message": record.getMessage(),
            }
            
            # 添加HTTP请求信息
            if hasattr(record, 'method'):
                log_data['method'] = record.method
            if hasattr(record, 'path'):
                log_data['path'] = record.path
            if hasattr(record, 'status_code'):
                log_data['status_code'] = record.status_code
            if hasattr(record, 'response_time_ms'):
                log_data['response_time_ms'] = record.response_time_ms
                
            # 添加异常信息
            if record.exc_info:
                log_data['exception'] = {
                    'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                    'message': str(record.exc_info[1]),
                    'traceback': self.formatException(record.exc_info)
                }
                
            return json.dumps(log_data, ensure_ascii=False)


class DjangoLoggingConfig:
    """Django 统一日志配置"""
    
    def __init__(self):
        self.service_name = 'django'
        self.log_dir = Path(os.getenv('LOG_DIR', '/Users/creed/Workspace/OpenSource/ansflow/logs'))
        self.service_log_dir = self.log_dir / 'services' / self.service_name
        self.service_log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_format = os.getenv('LOG_FORMAT', 'json')
        self.log_retention_days = int(os.getenv('LOG_RETENTION_DAYS', '30'))
        
    def get_logging_config(self):
        """获取 Django LOGGING 配置字典"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'json': {
                    '()': AnsFlowJSONFormatter,
                    'service_name': self.service_name,
                },
                'verbose': {
                    'format': '{asctime} - {name} - {levelname} - [{funcName}:{lineno}] - {message}',
                    'style': '{',
                },
                'simple': {
                    'format': '{asctime} - {levelname} - {message}',
                    'style': '{',
                },
            },
            'handlers': {
                # 主日志文件
                'main_file': {
                    'class': 'logging.handlers.TimedRotatingFileHandler',
                    'filename': str(self.service_log_dir / f'{self.service_name}_main.log'),
                    'when': 'midnight',
                    'interval': 1,
                    'backupCount': self.log_retention_days,
                    'formatter': 'json' if self.log_format == 'json' else 'verbose',
                    'encoding': 'utf-8',
                },
                # 错误日志文件
                'error_file': {
                    'class': 'logging.handlers.TimedRotatingFileHandler',
                    'filename': str(self.service_log_dir / f'{self.service_name}_error.log'),
                    'when': 'midnight',
                    'interval': 1,
                    'backupCount': self.log_retention_days,
                    'formatter': 'json' if self.log_format == 'json' else 'verbose',
                    'level': 'ERROR',
                    'encoding': 'utf-8',
                },
                # 访问日志文件
                'access_file': {
                    'class': 'logging.handlers.TimedRotatingFileHandler',
                    'filename': str(self.service_log_dir / f'{self.service_name}_access.log'),
                    'when': 'midnight',
                    'interval': 1,
                    'backupCount': self.log_retention_days,
                    'formatter': 'json' if self.log_format == 'json' else 'verbose',
                    'encoding': 'utf-8',
                },
                # 性能日志文件
                'performance_file': {
                    'class': 'logging.handlers.TimedRotatingFileHandler',
                    'filename': str(self.service_log_dir / f'{self.service_name}_performance.log'),
                    'when': 'midnight',
                    'interval': 1,
                    'backupCount': self.log_retention_days,
                    'formatter': 'json' if self.log_format == 'json' else 'verbose',
                    'encoding': 'utf-8',
                },
                # 控制台输出
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'simple',
                    'level': 'DEBUG' if self.log_level == 'DEBUG' else 'INFO',
                },
            },
            'loggers': {
                # Django 框架日志
                'django': {
                    'handlers': ['main_file', 'console'],
                    'level': self.log_level,
                    'propagate': False,
                },
                # Django 请求日志
                'django.request': {
                    'handlers': ['access_file', 'error_file'],
                    'level': 'INFO',
                    'propagate': False,
                },
                # Django 数据库日志
                'django.db.backends': {
                    'handlers': ['main_file'] if self.log_level != 'DEBUG' else ['main_file', 'console'],
                    'level': 'WARNING' if self.log_level != 'DEBUG' else 'DEBUG',
                    'propagate': False,
                },
                # AnsFlow 应用日志
                'ansflow': {
                    'handlers': ['main_file', 'error_file', 'console'],
                    'level': self.log_level,
                    'propagate': False,
                },
                # AnsFlow 性能日志
                'ansflow.performance': {
                    'handlers': ['performance_file'],
                    'level': 'INFO',
                    'propagate': False,
                },
            },
            'root': {
                'handlers': ['console', 'main_file'],
                'level': self.log_level,
            },
        }


class RequestLoggingMiddleware:
    """Django 请求日志中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('django.request')
        
    def __call__(self, request):
        # 记录请求开始时间
        start_time = datetime.now()
        
        # 获取请求信息
        method = request.method
        path = request.path
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        remote_addr = self._get_client_ip(request)
        
        # 处理请求
        response = self.get_response(request)
        
        # 计算响应时间
        end_time = datetime.now()
        response_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # 创建日志记录
        log_record = logging.LogRecord(
            name='django.request',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg=f"{method} {path} - {response.status_code} ({response_time_ms}ms)",
            args=(),
            exc_info=None
        )
        
        # 添加额外信息
        log_record.method = method
        log_record.path = path
        log_record.status_code = response.status_code
        log_record.response_time_ms = response_time_ms
        log_record.user_agent = user_agent
        log_record.remote_addr = remote_addr
        log_record.component = 'middleware'
        
        # 添加用户信息（如果已认证）
        if hasattr(request, 'user') and request.user.is_authenticated:
            log_record.user_id = str(request.user.id)
            
        # 记录日志
        self.logger.handle(log_record)
        
        return response
    
    def _get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip


# 便捷函数
def setup_django_logging():
    """设置 Django 日志配置"""
    config = DjangoLoggingConfig()
    return config.get_logging_config()


def get_logger(name: str = 'ansflow', component: str = None):
    """获取配置好的日志器"""
    logger = logging.getLogger(name)
    
    if component:
        # 创建适配器来添加组件信息
        class ComponentAdapter(logging.LoggerAdapter):
            def process(self, msg, kwargs):
                # 确保 extra 字典存在
                if 'extra' not in kwargs:
                    kwargs['extra'] = {}
                kwargs['extra']['component'] = self.extra['component']
                return msg, kwargs
                
        logger = ComponentAdapter(logger, {'component': component})
    
    return logger


# 性能监控装饰器
def log_performance(logger_name='ansflow.performance'):
    """性能日志装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger = logging.getLogger(logger_name)
            
            try:
                result = func(*args, **kwargs)
                end_time = datetime.now()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                
                # 创建性能日志记录
                log_record = logging.LogRecord(
                    name=logger_name,
                    level=logging.INFO,
                    pathname='',
                    lineno=0,
                    msg=f"Function {func.__name__} executed successfully",
                    args=(),
                    exc_info=None
                )
                
                log_record.function_name = func.__name__
                log_record.response_time_ms = duration_ms
                log_record.component = 'performance'
                log_record.success = True
                
                logger.handle(log_record)
                return result
                
            except Exception as e:
                end_time = datetime.now()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                
                # 记录异常日志
                log_record = logging.LogRecord(
                    name=logger_name,
                    level=logging.ERROR,
                    pathname='',
                    lineno=0,
                    msg=f"Function {func.__name__} failed with error: {str(e)}",
                    args=(),
                    exc_info=sys.exc_info()
                )
                
                log_record.function_name = func.__name__
                log_record.response_time_ms = duration_ms
                log_record.component = 'performance'
                log_record.success = False
                
                logger.handle(log_record)
                raise
                
        return wrapper
    return decorator
