"""
FastAPI服务与AnsFlow统一日志系统集成
"""
import logging
import logging.handlers
import sys
import os
import json
from datetime import datetime
from pathlib import Path
import structlog
from typing import Dict, Any, Optional

# 添加Django服务路径以导入统一日志配置
current_dir = Path(__file__).parent
django_service_dir = current_dir.parent / 'django_service'
if django_service_dir.exists():
    sys.path.insert(0, str(django_service_dir))

# 初始化Django环境
try:
    import django
    from django.conf import settings as django_settings
    
    # 设置Django环境变量
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
    
    # 如果Django没有配置，则配置它
    if not django_settings.configured:
        django.setup()
    
    from common.logging_config import AnsFlowLoggingConfig, AnsFlowJSONFormatter, RedisLogHandler
    from settings_management.models import GlobalConfig
    HAS_DJANGO_LOGGING = True
except (ImportError, Exception) as e:
    HAS_DJANGO_LOGGING = False
    print(f"Warning: Django统一日志配置不可用: {e}，使用基本日志配置")
    
    # 定义本地版本的AnsFlowJSONFormatter
    class AnsFlowJSONFormatter(logging.Formatter):
        """AnsFlow JSON日志格式化器"""
        
        def __init__(self, service_name: str = "fastapi"):
            super().__init__()
            self.service_name = service_name
        
        def format(self, record: logging.LogRecord) -> str:
            # 创建基本日志字典
            log_dict = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'service': getattr(record, 'service', self.service_name),
                'module': record.module,
                'funcName': record.funcName,
                'lineno': record.lineno,
            }
            
            # 添加异常信息
            if record.exc_info:
                log_dict['exception'] = self.formatException(record.exc_info)
            
            return json.dumps(log_dict, ensure_ascii=False)


class FastAPIRedisLoggingIntegration:
    """FastAPI Redis日志集成"""
    
    def __init__(self):
        self.service_name = 'fastapi'
        self.logger = logging.getLogger(f'ansflow.{self.service_name}')
        self.redis_handler = None
        
    def setup_unified_logging(self):
        """设置统一日志系统"""
        if not HAS_DJANGO_LOGGING:
            self._setup_basic_logging()
            return
            
        try:
            # 获取保存的日志配置
            config = self._get_log_config_from_db()
            
            # 设置基础日志级别
            log_level = config.get('LOGGING_LEVEL', 'INFO')
            self.logger.setLevel(getattr(logging, log_level))
            
            # 清除现有处理器
            self.logger.handlers.clear()
            
            # 添加控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(AnsFlowJSONFormatter(service_name=self.service_name))
            self.logger.addHandler(console_handler)
            
            # 添加文件处理器
            file_handler = self._create_file_handler()
            self.logger.addHandler(file_handler)
            
            # 添加Redis处理器（如果启用）
            if config.get('LOGGING_ENABLE_REDIS', 'false').lower() == 'true':
                self._setup_redis_handler(config)
                
            print(f"✅ FastAPI统一日志系统初始化成功 - 级别: {log_level}")
            
        except Exception as e:
            print(f"⚠️  FastAPI统一日志初始化失败: {e}")
            self._setup_basic_logging()
    
    def _get_log_config_from_db(self) -> Dict[str, str]:
        """从数据库获取日志配置"""
        config = {}
        
        try:
            # 导入Django ORM需要先配置Django
            import django
            from django.conf import settings as django_settings
            
            if not django_settings.configured:
                # 基本Django配置用于访问数据库
                django_settings.configure(
                    DEBUG=True,
                    DATABASES={
                        'default': {
                            'ENGINE': 'django.db.backends.mysql',
                            'NAME': os.getenv('DB_NAME', 'ansflow'),
                            'USER': os.getenv('DB_USER', 'root'),
                            'PASSWORD': os.getenv('DB_PASSWORD', ''),
                            'HOST': os.getenv('DB_HOST', 'localhost'),
                            'PORT': os.getenv('DB_PORT', '3306'),
                        }
                    },
                    INSTALLED_APPS=[
                        'django.contrib.contenttypes',
                        'django.contrib.auth',
                        'settings_management',
                    ],
                    USE_TZ=True,
                )
                
            django.setup()
            
            # 获取日志配置项
            from settings_management.models import GlobalConfig
            
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
    
    def _setup_redis_handler(self, config: Dict[str, str]):
        """设置Redis日志处理器"""
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
            
            # 使用新的直接Redis处理器，写入到Redis Stream
            self.redis_handler = DirectRedisHandler(
                redis_client=redis_client,
                stream_name='ansflow:logs:stream'
            )
            
            # 添加到logger
            self.logger.addHandler(self.redis_handler)
            
            print(f"✅ FastAPI Redis Stream处理器已启用 - DB: {config.get('REDIS_DB', 5)}")
            
        except Exception as e:
            print(f"⚠️  FastAPI Redis日志处理器初始化失败: {e}")
    
    def _create_file_handler(self) -> logging.Handler:
        """创建文件日志处理器"""
        log_dir = Path('/Users/creed/Workspace/OpenSource/ansflow/logs/services/fastapi')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f'{self.service_name}.log'
        
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
    
    def _setup_basic_logging(self):
        """设置基本日志配置（当统一日志系统不可用时）"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(
                    '/Users/creed/Workspace/OpenSource/ansflow/logs/fastapi_basic.log'
                )
            ]
        )
        print("✅ FastAPI基本日志系统初始化完成")
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """获取配置好的logger"""
        if name:
            return logging.getLogger(f'ansflow.{self.service_name}.{name}')
        return self.logger


import redis
import uuid
from typing import Dict, Any

class DirectRedisHandler(logging.Handler):
    """直接写入Redis Stream的日志处理器"""
    
    def __init__(self, redis_client, stream_name='ansflow:logs:stream'):
        super().__init__()
        self.redis_client = redis_client
        self.stream_name = stream_name
        self.service_name = 'fastapi'
    
    def emit(self, record: logging.LogRecord):
        """将日志直接写入Redis Stream"""
        try:
            # 生成唯一ID
            log_id = f"fastapi-{int(datetime.now().timestamp() * 1000)}-{uuid.uuid4().hex[:8]}"
            
            # 构造日志字段
            fields = {
                'log_id': log_id,
                'timestamp': datetime.now().isoformat(),
                'level': record.levelname,
                'service': getattr(record, 'service', self.service_name),
                'component': record.name.split('.')[-1],
                'module': record.module,
                'message': record.getMessage(),
            }
            
            # 添加执行ID（如果有）
            if hasattr(record, 'execution_id') and record.execution_id:
                fields['execution_id'] = str(record.execution_id)
                
            # 添加额外数据
            if hasattr(record, 'extra_data') and record.extra_data:
                fields['extra_data'] = json.dumps(record.extra_data)
            
            # 写入Redis Stream
            self.redis_client.xadd(self.stream_name, fields)
            
        except Exception:
            self.handleError(record)


class StructlogToLoggingHandler(logging.Handler):
    """将structlog输出桥接到标准logging的处理器"""
    
    def __init__(self, service_name: str = 'fastapi'):
        super().__init__()
        self.service_name = service_name
        # 不使用统一logging系统，直接创建独立的handler避免循环
        self._setup_direct_handlers()
        
    def _setup_direct_handlers(self):
        """直接设置处理器，避免循环依赖"""
        self.handlers = []
        
        # 控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.handlers.append(console_handler)
        
        # 文件输出
        try:
            log_dir = Path('/Users/creed/Workspace/OpenSource/ansflow/logs/services/fastapi')
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f'{self.service_name}_structlog.log'
            
            file_handler = logging.handlers.TimedRotatingFileHandler(
                filename=str(log_file),
                when='midnight',
                interval=1,
                backupCount=7,
                encoding='utf-8'
            )
            file_handler.setFormatter(AnsFlowJSONFormatter(service_name=self.service_name))
            self.handlers.append(file_handler)
        except Exception as e:
            print(f"⚠️  Structlog文件日志处理器创建失败: {e}")
        
    def emit(self, record: logging.LogRecord):
        """直接处理记录，避免循环"""
        try:
            # 添加服务标识
            record.service = self.service_name
            
            # 直接使用handlers处理记录
            for handler in self.handlers:
                if record.levelno >= handler.level:
                    handler.emit(record)
                    
        except Exception:
            self.handleError(record)


def setup_structlog_integration():
    """设置structlog与统一日志系统的集成"""
    
    # 初始化FastAPI日志集成
    fastapi_logging = FastAPIRedisLoggingIntegration()
    fastapi_logging.setup_unified_logging()
    
    # 创建桥接处理器
    bridge_handler = StructlogToLoggingHandler('fastapi')
    
    # 配置structlog以使用标准logging后端
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 为structlog的根logger添加我们的处理器
    structlog_root = logging.getLogger()
    
    # 检查是否已经添加了我们的处理器
    has_bridge = any(isinstance(h, StructlogToLoggingHandler) for h in structlog_root.handlers)
    if not has_bridge:
        structlog_root.addHandler(bridge_handler)
        
    print("✅ Structlog与统一日志系统集成完成")
    
    return fastapi_logging


# 全局实例
fastapi_log_integration = None

def get_fastapi_logger(name: str = None) -> logging.Logger:
    """获取集成了统一日志系统的FastAPI logger"""
    global fastapi_log_integration
    
    if fastapi_log_integration is None:
        fastapi_log_integration = setup_structlog_integration()
    
    return fastapi_log_integration.get_logger(name)
