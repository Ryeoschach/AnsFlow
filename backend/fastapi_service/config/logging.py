"""
FastAPI应用日志配置
集成AnsFlow日志系统
"""
import logging
import sys
from pathlib import Path

# 添加common模块到Python路径
current_dir = Path(__file__).parent
django_service_dir = current_dir.parent.parent / 'django_service'
if django_service_dir.exists():
    sys.path.insert(0, str(django_service_dir))

try:
    from common.logging_config import AnsFlowLoggingConfig
except ImportError:
    # 如果导入失败，创建简单的配置类
    class AnsFlowLoggingConfig:
        @staticmethod
        def setup_logging(service_name='fastapi', log_level='INFO'):
            logging.basicConfig(
                level=getattr(logging, log_level),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )


class FastAPILoggingConfig:
    """FastAPI日志配置管理器"""
    
    def __init__(self, service_name: str = 'fastapi_service'):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        
    def setup_logging(self, config: dict = None):
        """设置FastAPI应用的日志配置"""
        if config is None:
            config = self.get_default_config()
        
        # 使用AnsFlow统一日志配置
        AnsFlowLoggingConfig.setup_logging(
            service_name=self.service_name,
            log_level=config.get('level', 'INFO'),
            log_file=config.get('file'),
            enable_redis=config.get('enable_redis', False),
            redis_config=config.get('redis_config')
        )
        
        # 设置FastAPI相关日志器
        self.setup_fastapi_loggers(config.get('level', 'INFO'))
        
        return self.logger
    
    def setup_fastapi_loggers(self, log_level: str):
        """配置FastAPI相关的日志器"""
        loggers = [
            'fastapi',
            'uvicorn',
            'uvicorn.access',
            'uvicorn.error',
            'starlette'
        ]
        
        for logger_name in loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(getattr(logging, log_level.upper()))
    
    def get_default_config(self) -> dict:
        """获取默认日志配置"""
        return {
            'level': 'INFO',
            'file': f'/Users/creed/Workspace/OpenSource/ansflow/logs/{self.service_name}.log',
            'enable_redis': False,
            'redis_config': {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'stream_name': 'ansflow_logs'
            }
        }
    
    def log_startup_info(self):
        """记录应用启动信息"""
        self.logger.info(
            f"FastAPI服务 {self.service_name} 启动",
            extra={
                'service': self.service_name,
                'event': 'startup',
                'labels': ['fastapi', 'startup', 'system']
            }
        )
    
    def log_shutdown_info(self):
        """记录应用关闭信息"""
        self.logger.info(
            f"FastAPI服务 {self.service_name} 关闭",
            extra={
                'service': self.service_name,
                'event': 'shutdown',
                'labels': ['fastapi', 'shutdown', 'system']
            }
        )


def setup_fastapi_logging(app, config: dict = None):
    """
    为FastAPI应用设置日志
    
    Args:
        app: FastAPI应用实例
        config: 日志配置字典
    """
    from .logging import LoggingMiddleware
    
    # 初始化日志配置
    logging_config = FastAPILoggingConfig('fastapi_service')
    logger = logging_config.setup_logging(config)
    
    # 添加日志中间件
    app.add_middleware(LoggingMiddleware)
    
    # 添加启动和关闭事件处理
    @app.on_event("startup")
    async def startup_event():
        logging_config.log_startup_info()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logging_config.log_shutdown_info()
    
    return logger


# 用于API路由的日志装饰器
def log_api_call(operation: str = None, level: str = 'INFO'):
    """
    API调用日志装饰器
    
    Args:
        operation: 操作描述
        level: 日志级别
    """
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            logger = logging.getLogger('fastapi_service')
            
            # 记录API调用开始
            logger.log(
                getattr(logging, level.upper()),
                f"API调用开始: {operation or func.__name__}",
                extra={
                    'operation': operation or func.__name__,
                    'function': func.__name__,
                    'labels': ['fastapi', 'api', 'start']
                }
            )
            
            try:
                result = await func(*args, **kwargs)
                
                # 记录API调用成功
                execution_time = int((time.time() - start_time) * 1000)
                logger.log(
                    getattr(logging, level.upper()),
                    f"API调用成功: {operation or func.__name__}",
                    extra={
                        'operation': operation or func.__name__,
                        'function': func.__name__,
                        'execution_time_ms': execution_time,
                        'labels': ['fastapi', 'api', 'success']
                    }
                )
                
                return result
                
            except Exception as e:
                # 记录API调用错误
                execution_time = int((time.time() - start_time) * 1000)
                logger.error(
                    f"API调用错误: {operation or func.__name__} - {str(e)}",
                    extra={
                        'operation': operation or func.__name__,
                        'function': func.__name__,
                        'execution_time_ms': execution_time,
                        'exception_type': e.__class__.__name__,
                        'exception_message': str(e),
                        'labels': ['fastapi', 'api', 'error']
                    }
                )
                raise
        
        return wrapper
    return decorator


# 示例使用
if __name__ == "__main__":
    # 这只是示例，实际使用时在FastAPI应用中调用
    config = FastAPILoggingConfig()
    logger = config.setup_logging()
    logger.info("FastAPI日志配置测试")
