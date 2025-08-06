"""
AnsFlow FastAPI 服务统一日志配置模块
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

# 导入统一日志配置
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow')
try:
    from common.unified_logging import AnsFlowJSONFormatter, AnsFlowLogManager
except ImportError:
    # 如果无法导入，使用本地实现
    class AnsFlowJSONFormatter(logging.Formatter):
        def __init__(self, service_name="fastapi"):
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
        # 配置根日志器
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            force=True
        )
        
        # 获取应用日志器
        logger = logging.getLogger("ansflow.fastapi")
        logger.setLevel(getattr(logging, self.log_level))
        
        # 清除现有处理器
        logger.handlers.clear()
        
        # 添加主日志处理器
        main_handler = self._create_file_handler('main')
        logger.addHandler(main_handler)
        
        # 添加错误级别专用处理器
        error_handler = self._create_file_handler('error')
        error_handler.setLevel(logging.ERROR)
        error_handler.addFilter(lambda record: record.levelno >= logging.ERROR)
        logger.addHandler(error_handler)
        
        # 添加访问日志处理器
        access_handler = self._create_file_handler('access')
        access_handler.setLevel(logging.INFO)
        access_handler.addFilter(lambda record: hasattr(record, 'method'))
        logger.addHandler(access_handler)
        
        # 添加性能日志处理器
        if os.getenv('ENABLE_PERFORMANCE_LOGGING', 'false').lower() == 'true':
            perf_handler = self._create_file_handler('performance')
            perf_handler.setLevel(logging.INFO)
            perf_handler.addFilter(lambda record: hasattr(record, 'response_time_ms'))
            logger.addHandler(perf_handler)
        
        # 配置 uvicorn 访问日志
        uvicorn_access = logging.getLogger("uvicorn.access")
        uvicorn_access.handlers = []
        uvicorn_access.addHandler(access_handler)
        
        # 配置 uvicorn 错误日志
        uvicorn_error = logging.getLogger("uvicorn.error")
        uvicorn_error.handlers = []
        uvicorn_error.addHandler(main_handler)
        uvicorn_error.addHandler(error_handler)
        
        return logger
    
    def _create_file_handler(self, log_type: str) -> logging.Handler:
        """创建文件处理器"""
        log_file = self.service_log_dir / f"{self.service_name}_{log_type}.log"
        
        # 配置日志轮转
        handler = logging.handlers.TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=self.log_retention_days,
            encoding='utf-8'
        )
        
        # 设置格式化器
        if self.log_format == 'json':
            handler.setFormatter(AnsFlowJSONFormatter(self.service_name))
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
            )
            handler.setFormatter(formatter)
            
        return handler
    
    def setup_structlog(self):
        """设置 structlog 配置"""
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


# FastAPI 请求日志中间件
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time
import uuid

class RequestLoggingMiddleware:
    """FastAPI 请求日志中间件"""
    
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger('ansflow.fastapi')
        
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取请求信息
        request = Request(scope, receive)
        method = request.method
        path = request.url.path
        query_params = str(request.query_params)
        user_agent = request.headers.get('user-agent', '')
        remote_addr = self._get_client_ip(request)
        request_id = str(uuid.uuid4())
        
        # 添加请求ID到scope
        scope['request_id'] = request_id
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # 计算响应时间
                end_time = time.time()
                response_time_ms = int((end_time - start_time) * 1000)
                
                # 记录访问日志
                log_record = logging.LogRecord(
                    name='ansflow.fastapi',
                    level=logging.INFO,
                    pathname='',
                    lineno=0,
                    msg=f"{method} {path} - {message.get('status', 500)} ({response_time_ms}ms)",
                    args=(),
                    exc_info=None
                )
                
                # 添加额外信息
                log_record.method = method
                log_record.path = path
                log_record.status_code = message.get('status', 500)
                log_record.response_time_ms = response_time_ms
                log_record.user_agent = user_agent
                log_record.remote_addr = remote_addr
                log_record.request_id = request_id
                log_record.component = 'middleware'
                
                if query_params:
                    log_record.query_params = query_params
                    
                # 记录日志
                self.logger.handle(log_record)
                
            await send(message)
            
        await self.app(scope, receive, send_wrapper)
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.client.host if request.client else 'unknown'


# 便捷函数
def setup_fastapi_logging():
    """设置 FastAPI 日志配置"""
    config = FastAPILoggingConfig()
    config.setup_structlog()
    return config.setup_logging()


def get_logger(name: str = 'ansflow.fastapi', component: str = None):
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


# structlog 便捷函数
def get_structured_logger(name: str = "ansflow.fastapi"):
    """获取 structlog 日志器"""
    return structlog.get_logger(name)


# 性能监控装饰器
def log_performance(logger_name='ansflow.fastapi'):
    """性能日志装饰器"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            logger = logging.getLogger(logger_name)
            
            try:
                if hasattr(func, '__await__'):
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
        
        # 根据函数类型返回不同的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator
