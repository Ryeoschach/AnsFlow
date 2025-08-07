#!/usr/bin/env python3
"""
FastAPI 独立日志系统
无需依赖Django，直接连接Redis Stream实现统一日志功能
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import redis
from pathlib import Path


class FastAPIRedisHandler(logging.Handler):
    """FastAPI专用Redis日志处理器 - 无Django依赖"""
    
    def __init__(self, 
                 redis_host: str = 'localhost', 
                 redis_port: int = 6379, 
                 redis_db: int = 5,
                 stream_name: str = 'ansflow:logs:stream'):
        super().__init__()
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.stream_name = stream_name
        self.service_name = 'fastapi_service'
        self.redis_client = None
        
        # 初始化Redis连接
        self._init_redis()
    
    def _init_redis(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=False,  # 保持字节格式以兼容Redis Stream
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # 测试连接
            self.redis_client.ping()
            print(f"✅ FastAPI Redis日志处理器连接成功 - {self.redis_host}:{self.redis_port} DB:{self.redis_db}")
            
        except Exception as e:
            print(f"⚠️ FastAPI Redis连接失败: {e}, 日志将只写入文件")
            self.redis_client = None
    
    def emit(self, record: logging.LogRecord):
        """发送日志到Redis Stream"""
        try:
            # 构造日志条目
            log_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': record.levelname,
                'service': self.service_name,
                'component': getattr(record, 'component', record.module or 'main'),
                'module': record.module or record.name.split('.')[-1],
                'message': record.getMessage(),
                'logger': record.name,
                'line': record.lineno,
                'function': record.funcName,
            }
            
            # 添加执行ID（如果存在）
            if hasattr(record, 'execution_id'):
                log_entry['execution_id'] = str(record.execution_id)
            
            # 添加追踪ID（如果存在）
            if hasattr(record, 'trace_id'):
                log_entry['trace_id'] = record.trace_id
            
            # 添加额外数据
            if hasattr(record, 'extra_data'):
                log_entry['extra_data'] = json.dumps(record.extra_data)
            
            # 添加异常信息
            if record.exc_info:
                log_entry['exception'] = self.formatException(record.exc_info)
            
            # 发送到Redis Stream
            if self.redis_client:
                try:
                    # 生成唯一ID
                    log_id = f"fastapi-{uuid.uuid4().hex[:8]}-{int(datetime.utcnow().timestamp() * 1000)}"
                    log_entry['log_id'] = log_id
                    
                    # 写入Redis Stream（带长度限制）
                    self.redis_client.xadd(
                        self.stream_name, 
                        log_entry,
                        maxlen=10000,  # 限制Stream最大长度
                        approximate=True  # 使用近似修剪以提高性能
                    )
                    
                except Exception as redis_error:
                    print(f"Redis写入失败: {redis_error}")
                    # Redis失败时不抛出异常，确保应用不受影响
        
        except Exception as e:
            # 处理器不应该影响应用运行
            print(f"FastAPI日志处理器错误: {e}")
            self.handleError(record)


class FastAPIJSONFormatter(logging.Formatter):
    """FastAPI JSON格式化器"""
    
    def __init__(self, service_name: str = "fastapi"):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        log_dict = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname.lower(),
            'service': self.service_name,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module or record.name.split('.')[-1],
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_dict['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_dict, ensure_ascii=False)


class StandaloneFastAPILogging:
    """FastAPI独立日志系统"""
    
    def __init__(self):
        self.service_name = 'fastapi_service'
        self.logger = None
        
        # 从环境变量获取配置
        self.config = {
            'redis_host': os.getenv('LOGGING_REDIS_HOST', 'localhost'),
            'redis_port': int(os.getenv('LOGGING_REDIS_PORT', 6379)),
            'redis_db': int(os.getenv('LOGGING_REDIS_DB', 5)),
            'log_level': os.getenv('LOGGING_LEVEL', 'INFO'),
            'enable_redis': os.getenv('LOGGING_ENABLE_REDIS', 'true').lower() == 'true',
        }
    
    def setup_logging(self) -> logging.Logger:
        """设置FastAPI独立日志系统"""
        
        # 创建主logger
        self.logger = logging.getLogger(f'ansflow.{self.service_name}')
        self.logger.setLevel(getattr(logging, self.config['log_level']))
        
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 1. 控制台处理器 - JSON格式
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(FastAPIJSONFormatter(self.service_name))
        self.logger.addHandler(console_handler)
        
        # 2. 文件处理器
        file_handler = self._create_file_handler()
        self.logger.addHandler(file_handler)
        
        # 3. Redis处理器（如果启用）
        if self.config['enable_redis']:
            redis_handler = FastAPIRedisHandler(
                redis_host=self.config['redis_host'],
                redis_port=self.config['redis_port'],
                redis_db=self.config['redis_db'],
                stream_name='ansflow:logs:stream'
            )
            self.logger.addHandler(redis_handler)
        
        # 4. 配置Uvicorn访问日志
        self._setup_uvicorn_logging()
        
        # 防止重复日志
        self.logger.propagate = False
        
        print(f"✅ FastAPI独立日志系统初始化成功 - 级别: {self.config['log_level']}")
        print(f"📡 Redis日志: {'启用' if self.config['enable_redis'] else '禁用'}")
        
        return self.logger
    
    def _create_file_handler(self) -> logging.Handler:
        """创建文件日志处理器"""
        log_dir = Path('/Users/creed/Workspace/OpenSource/ansflow/logs/services/fastapi')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f'{self.service_name}.log'
        
        # 使用轮转文件处理器
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        
        handler.setFormatter(FastAPIJSONFormatter(self.service_name))
        return handler
    
    def _setup_uvicorn_logging(self):
        """配置Uvicorn访问日志集成到统一日志系统"""
        
        # 获取Uvicorn的访问日志logger
        uvicorn_access_logger = logging.getLogger('uvicorn.access')
        uvicorn_logger = logging.getLogger('uvicorn')
        
        # 清除现有处理器
        uvicorn_access_logger.handlers.clear()
        uvicorn_logger.handlers.clear()
        
        # 创建Redis处理器（如果启用）
        handlers = []
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(FastAPIJSONFormatter('fastapi_service'))
        handlers.append(console_handler)
        
        # Redis处理器
        if self.config['enable_redis']:
            redis_handler = FastAPIRedisHandler(
                redis_host=self.config['redis_host'],
                redis_port=self.config['redis_port'],
                redis_db=self.config['redis_db'],
                stream_name='ansflow:logs:stream'
            )
            handlers.append(redis_handler)
        
        # 文件处理器
        file_handler = self._create_file_handler()
        handlers.append(file_handler)
        
        # 应用到Uvicorn loggers
        for handler in handlers:
            uvicorn_access_logger.addHandler(handler)
            uvicorn_logger.addHandler(handler)
        
        # 设置日志级别
        uvicorn_access_logger.setLevel(logging.INFO)
        uvicorn_logger.setLevel(logging.INFO)
        
        # 防止重复日志传播
        uvicorn_access_logger.propagate = False
        uvicorn_logger.propagate = False
        
        print("✅ Uvicorn访问日志集成到统一日志系统")
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """获取logger实例"""
        if name:
            return logging.getLogger(f'ansflow.{self.service_name}.{name}')
        return self.logger or logging.getLogger(f'ansflow.{self.service_name}')


# 全局实例
_logging_instance = None

def setup_standalone_logging() -> logging.Logger:
    """设置独立日志系统并返回logger"""
    global _logging_instance
    if _logging_instance is None:
        _logging_instance = StandaloneFastAPILogging()
        return _logging_instance.setup_logging()
    return _logging_instance.logger

def get_fastapi_logger(name: str = None) -> logging.Logger:
    """获取FastAPI logger"""
    global _logging_instance
    if _logging_instance is None:
        setup_standalone_logging()
    return _logging_instance.get_logger(name)


# 测试函数
def test_standalone_logging():
    """测试独立日志系统"""
    logger = setup_standalone_logging()
    
    # 测试不同级别的日志
    logger.debug("Debug message from FastAPI standalone logging")
    logger.info("Info message from FastAPI standalone logging")
    logger.warning("Warning message from FastAPI standalone logging") 
    logger.error("Error message from FastAPI standalone logging")
    
    # 测试结构化日志
    test_logger = get_fastapi_logger('test')
    test_logger.info("Test message with structured data", extra={
        'execution_id': 12345,
        'trace_id': 'test-trace-123',
        'extra_data': {'key': 'value', 'count': 42}
    })
    
    print("✅ FastAPI独立日志测试完成")


if __name__ == "__main__":
    test_standalone_logging()
