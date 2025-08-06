"""
FastAPI 服务统一日志配置模块
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
import structlog
from fastapi import Request, Response
import time


class FastAPIJSONFormatter(logging.Formatter):
    """FastAPI 专用 JSON 格式化器"""
    
    def __init__(self, service_name="fastapi"):
        super().__init__()
        self.service_name = service_name
        
    def format(self, record):
        """格式化日志记录为统一的JSON格式"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "level": record.levelname,
            "service": self.service_name,
            "component": getattr(record, 'component', 'unknown'),
            "module": record.name,
            "message": record.getMessage(),
        }
        
        # 添加追踪信息
        if hasattr(record, 'trace_id'):
            log_data['trace_id'] = record.trace_id
            
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
            
        # 添加HTTP请求信息
        if hasattr(record, 'method'):
            log_data['method'] = record.method
            
        if hasattr(record, 'path'):
            log_data['path'] = record.path
            
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
            
        if hasattr(record, 'response_time_ms'):
            log_data['response_time_ms'] = record.response_time_ms
            
        # 添加用户信息
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
            
        # 添加客户端信息
        if hasattr(record, 'client_ip'):
            log_data['client_ip'] = record.client_ip
            
        if hasattr(record, 'user_agent'):
            log_data['user_agent'] = record.user_agent
            
        # 添加额外数据
        if hasattr(record, 'extra') and isinstance(record.extra, dict):
            log_data['extra'] = record.extra
            
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
            
        return json.dumps(log_data, ensure_ascii=False)


class FastAPILoggingConfig:
    """FastAPI 统一日志配置"""
    
    def __init__(self):
        self.service_name = 'fastapi'
        self.log_dir = Path(os.getenv('LOG_DIR', '/Users/creed/Workspace/OpenSource/ansflow/logs'))
        self.service_log_dir = self.log_dir / 'services' / self.service_name
        self.service_log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_format = os.getenv('LOG_FORMAT', 'json')
        self.log_retention_days = int(os.getenv('LOG_RETENTION_DAYS', '30'))
        
    def setup_logging(self):
        """设置 FastAPI 日志配置"""
        # 创建日志处理器
        handlers = self._create_handlers()
        
        # 配置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level))
        
        # 清除现有处理器
        root_logger.handlers.clear()
        
        # 添加新处理器
        for handler in handlers.values():
            root_logger.addHandler(handler)
            
        # 配置 FastAPI 相关日志器
        self._configure_loggers(handlers)
        
        # 配置 structlog
        self._setup_structlog()
        
    def _create_handlers(self) -> Dict[str, logging.Handler]:
        """创建日志处理器"""
        handlers = {}
        
        # 主日志处理器
        handlers['main'] = self._create_file_handler(
            f'{self.service_name}_main.log',
            level=self.log_level
        )
        
        # 错误日志处理器
        handlers['error'] = self._create_file_handler(
            f'{self.service_name}_error.log',
            level='ERROR'
        )
        
        # 访问日志处理器
        handlers['access'] = self._create_file_handler(
            f'{self.service_name}_access.log',
            level='INFO'
        )
        
        # 性能日志处理器
        if os.getenv('ENABLE_PERFORMANCE_LOGGING', 'false').lower() == 'true':
            handlers['performance'] = self._create_file_handler(
                f'{self.service_name}_performance.log',
                level='INFO'
            )
            
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.log_level))
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        handlers['console'] = console_handler
        
        return handlers
        
    def _create_file_handler(self, filename: str, level: str) -> logging.Handler:
        """创建文件处理器"""
        file_path = self.service_log_dir / filename
        
        handler = logging.handlers.TimedRotatingFileHandler(
            file_path,
            when='midnight',
            interval=1,
            backupCount=self.log_retention_days,
            encoding='utf-8'
        )
        
        handler.setLevel(getattr(logging, level))
        
        # 设置格式化器
        if self.log_format == 'json':
            formatter = FastAPIJSONFormatter(self.service_name)
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
            )
        handler.setFormatter(formatter)
        
        return handler
        
    def _configure_loggers(self, handlers: Dict[str, logging.Handler]):
        """配置特定日志器"""
        # FastAPI 应用日志器
        app_logger = logging.getLogger('fastapi')
        app_logger.setLevel(getattr(logging, self.log_level))
        app_logger.handlers = [handlers['main'], handlers['error'], handlers['console']]
        app_logger.propagate = False
        
        # Uvicorn 日志器
        uvicorn_logger = logging.getLogger('uvicorn')
        uvicorn_logger.setLevel(getattr(logging, self.log_level))
        uvicorn_logger.handlers = [handlers['main'], handlers['console']]
        uvicorn_logger.propagate = False
        
        # Uvicorn 访问日志器
        uvicorn_access_logger = logging.getLogger('uvicorn.access')
        uvicorn_access_logger.setLevel(logging.INFO)
        uvicorn_access_logger.handlers = [handlers['access']]
        uvicorn_access_logger.propagate = False
        
        # AnsFlow 应用日志器
        ansflow_logger = logging.getLogger('ansflow')
        ansflow_logger.setLevel(getattr(logging, self.log_level))
        ansflow_logger.handlers = [handlers['main'], handlers['error'], handlers['console']]
        ansflow_logger.propagate = False
        
        # 性能日志器
        if 'performance' in handlers:
            perf_logger = logging.getLogger('ansflow.performance')
            perf_logger.setLevel(logging.INFO)
            perf_logger.handlers = [handlers['performance']]
            perf_logger.propagate = False
            
    def _setup_structlog(self):
        """配置 structlog"""
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ]
        
        if self.log_format == "json":
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())
            
        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )


class LoggingMiddleware:
    """FastAPI 日志中间件"""
    
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger('uvicorn.access')
        
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取请求信息
        method = scope.get("method", "")
        path = scope.get("path", "")
        query_string = scope.get("query_string", b"").decode()
        client = scope.get("client", ("unknown", 0))
        client_ip = client[0] if client else "unknown"
        
        # 获取请求头
        headers = dict(scope.get("headers", []))
        user_agent = headers.get(b"user-agent", b"").decode()
        
        # 处理响应
        status_code = 500
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
            
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            status_code = 500
            # 记录异常
            self.logger.error(
                f"Request failed: {method} {path}",
                extra={
                    'method': method,
                    'path': path,
                    'status_code': status_code,
                    'client_ip': client_ip,
                    'user_agent': user_agent,
                    'component': 'middleware',
                    'exception': str(e)
                },
                exc_info=True
            )
            raise
        finally:
            # 计算响应时间
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            # 创建日志记录
            log_record = logging.LogRecord(
                name='uvicorn.access',
                level=logging.INFO,
                pathname='',
                lineno=0,
                msg=f"{method} {path} - {status_code} ({response_time_ms}ms)",
                args=(),
                exc_info=None
            )
            
            # 添加额外信息
            log_record.method = method
            log_record.path = path + ("?" + query_string if query_string else "")
            log_record.status_code = status_code
            log_record.response_time_ms = response_time_ms
            log_record.client_ip = client_ip
            log_record.user_agent = user_agent
            log_record.component = 'middleware'
            
            # 记录访问日志
            self.logger.handle(log_record)


# 便捷函数
def setup_fastapi_logging():
    """设置 FastAPI 日志配置"""
    config = FastAPILoggingConfig()
    config.setup_logging()
    return structlog.get_logger("ansflow")


def get_logger(name: str = 'ansflow', component: str = None):
    """获取配置好的日志器"""
    logger = structlog.get_logger(name)
    
    if component:
        logger = logger.bind(component=component)
    
    return logger


# 性能监控装饰器
def log_performance(logger_name='ansflow.performance'):
    """性能日志装饰器"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            logger = logging.getLogger(logger_name)
            
            try:
                if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                    
                end_time = time.time()
                duration_ms = int((end_time - start_time) * 1000)
                
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
                end_time = time.time()
                duration_ms = int((end_time - start_time) * 1000)
                
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
                
        # 对于同步函数
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            logger = logging.getLogger(logger_name)
            
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                duration_ms = int((end_time - start_time) * 1000)
                
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
                end_time = time.time()
                duration_ms = int((end_time - start_time) * 1000)
                
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
        
        # 检查是否为协程函数
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator
