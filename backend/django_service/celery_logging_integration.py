"""
Celery与AnsFlow统一日志系统集成
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 导入Django配置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from common.logging_config import AnsFlowLoggingConfig, AnsFlowJSONFormatter, RedisLogHandler
from settings_management.models import GlobalConfig
from django.conf import settings


class CeleryLoggingIntegration:
    """Celery日志系统集成"""
    
    def __init__(self):
        self.service_name = 'celery'
        self.logger = logging.getLogger(f'ansflow.{self.service_name}')
        
    def setup_unified_logging(self):
        """设置统一日志系统"""
        try:
            # 获取保存的日志配置
            config = self._get_log_config_from_db()
            
            # 设置基础日志级别
            log_level = config.get('LOGGING_LEVEL', 'INFO')
            
            # 配置Celery日志
            self._configure_celery_logging(log_level, config)
            
            print(f"✅ Celery统一日志系统初始化成功 - 级别: {log_level}")
            
        except Exception as e:
            print(f"⚠️  Celery统一日志初始化失败: {e}")
            self._setup_basic_celery_logging()
            
    def _get_log_config_from_db(self) -> Dict[str, str]:
        """从数据库获取日志配置"""
        config = {}
        
        try:
            config_keys = [
                'LOGGING_LEVEL', 'LOGGING_ENABLE_REDIS', 
                'REDIS_HOST', 'REDIS_PORT', 'REDIS_DB'
            ]
            
            configs = GlobalConfig.objects.filter(key__in=config_keys)
            for cfg in configs:
                config[cfg.key] = cfg.value
                
        except Exception as e:
            print(f"从数据库获取配置失败: {e}")
            # 使用环境变量作为备用
            config = {
                'LOGGING_LEVEL': os.getenv('LOGGING_LEVEL', 'INFO'),
                'LOGGING_ENABLE_REDIS': os.getenv('LOGGING_ENABLE_REDIS', 'true'),
                'REDIS_HOST': os.getenv('REDIS_HOST', 'localhost'),
                'REDIS_PORT': os.getenv('REDIS_PORT', '6379'),
                'REDIS_DB': os.getenv('REDIS_DB', '5'),
            }
        
        return config
    
    def _configure_celery_logging(self, log_level: str, config: Dict[str, str]):
        """配置Celery日志系统"""
        
        # 获取Celery相关的loggers
        celery_loggers = [
            'celery',
            'celery.app',
            'celery.task',
            'celery.worker',
            'celery.beat',
            f'ansflow.{self.service_name}',
        ]
        
        for logger_name in celery_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(getattr(logging, log_level))
            
            # 清除现有处理器
            logger.handlers.clear()
            
            # 添加控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(AnsFlowJSONFormatter(service_name=self.service_name))
            logger.addHandler(console_handler)
            
            # 添加文件处理器
            file_handler = self._create_file_handler(logger_name)
            logger.addHandler(file_handler)
            
            # 添加Redis处理器（如果启用）
            if config.get('LOGGING_ENABLE_REDIS', 'false').lower() == 'true':
                redis_handler = self._create_redis_handler(config)
                if redis_handler:
                    logger.addHandler(redis_handler)
                    
    def _create_file_handler(self, logger_name: str) -> logging.Handler:
        """创建文件日志处理器"""
        log_dir = Path('/Users/creed/Workspace/OpenSource/ansflow/logs/services/celery')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 为不同的celery组件创建不同的日志文件
        if 'worker' in logger_name:
            log_file = log_dir / 'worker.log'
        elif 'beat' in logger_name:
            log_file = log_dir / 'beat.log'
        elif 'task' in logger_name:
            log_file = log_dir / 'task.log'
        else:
            log_file = log_dir / 'celery.log'
        
        # 使用时间轮转处理器
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(log_file),
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        
        handler.setFormatter(AnsFlowJSONFormatter(service_name=self.service_name))
        return handler
    
    def _create_redis_handler(self, config: Dict[str, str]) -> logging.Handler:
        """创建Redis日志处理器"""
        try:
            import redis
            
            redis_client = redis.Redis(
                host=config.get('REDIS_HOST', 'localhost'),
                port=int(config.get('REDIS_PORT', 6379)),
                db=int(config.get('REDIS_DB', 5)),
                decode_responses=False
            )
            
            # 测试Redis连接
            redis_client.ping()
            
            # 创建Redis处理器
            redis_handler = RedisLogHandler(
                redis_client=redis_client,
                stream_name='ansflow:logs:stream',
                max_len=10000
            )
            redis_handler.setFormatter(AnsFlowJSONFormatter(service_name=self.service_name))
            
            print(f"✅ Celery Redis日志处理器已启用 - DB: {config.get('REDIS_DB', 5)}")
            return redis_handler
            
        except Exception as e:
            print(f"⚠️  Celery Redis日志处理器初始化失败: {e}")
            return None
    
    def _setup_basic_celery_logging(self):
        """设置基本Celery日志配置（当统一日志系统不可用时）"""
        
        # Celery基本日志配置
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(
                    '/Users/creed/Workspace/OpenSource/ansflow/logs/celery_basic.log'
                )
            ]
        )
        
        print("✅ Celery基本日志系统初始化完成")


def configure_celery_logging():
    """配置Celery日志系统的主函数"""
    celery_integration = CeleryLoggingIntegration()
    celery_integration.setup_unified_logging()
    return celery_integration


# 在Celery启动时自动配置日志
if __name__ != '__main__':
    # 自动配置日志，除非是直接执行此文件
    configure_celery_logging()
