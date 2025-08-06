"""
AnsFlow 统一日志配置模块 v2.0
实现方案一：统一日志目录 + 标准化命名
"""
import os
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import structlog


class AnsFlowJSONFormatter(logging.Formatter):
    """AnsFlow 统一 JSON 格式化器"""
    
    def __init__(self, service_name: str = "unknown"):
        super().__init__()
        self.service_name = service_name
        
    def format(self, record):
        """格式化日志记录为统一的JSON格式"""
        # 统一日志结构
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
            
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
            
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
            
        # 添加额外数据
        if hasattr(record, 'extra') and isinstance(record.extra, dict):
            log_data['extra'] = self._filter_sensitive_data(record.extra)
            
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
            
        return json.dumps(log_data, ensure_ascii=False)
    
    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤敏感信息"""
        sensitive_keys = {
            'password', 'passwd', 'pwd', 'token', 'key', 'secret', 
            'authorization', 'cookie', 'session', 'csrf'
        }
        
        filtered_data = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                if isinstance(value, str) and len(value) > 8:
                    filtered_data[key] = value[:3] + '*' * (len(value) - 3)
                else:
                    filtered_data[key] = '******'
            elif isinstance(value, dict):
                filtered_data[key] = self._filter_sensitive_data(value)
            else:
                filtered_data[key] = value
                
        return filtered_data


class AnsFlowLogManager:
    """AnsFlow 日志管理器"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.log_dir = Path(os.getenv('LOG_DIR', '/Users/creed/Workspace/OpenSource/ansflow/logs'))
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_format = os.getenv('LOG_FORMAT', 'json')
        self.log_rotation = os.getenv('LOG_ROTATION', 'daily')
        self.log_retention_days = int(os.getenv('LOG_RETENTION_DAYS', '30'))
        
        # 确保日志目录存在
        self.service_log_dir = self.log_dir / 'services' / service_name
        self.service_log_dir.mkdir(parents=True, exist_ok=True)
        
        # 聚合日志目录
        self.aggregated_log_dir = self.log_dir / 'aggregated'
        self.aggregated_log_dir.mkdir(parents=True, exist_ok=True)
        
    def get_file_handler(self, log_type: str = 'main', level: str = None) -> logging.Handler:
        """获取文件处理器"""
        if level:
            log_file = self.service_log_dir / f"{self.service_name}_{level.lower()}.log"
        else:
            log_file = self.service_log_dir / f"{self.service_name}_{log_type}.log"
        
        # 配置日志轮转
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
                when='W0',
                interval=1,
                backupCount=self.log_retention_days // 7,
                encoding='utf-8'
            )
            
        # 设置格式化器
        if self.log_format == 'json':
            handler.setFormatter(AnsFlowJSONFormatter(self.service_name))
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
        return handler
    
    def setup_logger(self, logger_name: str = None, component: str = None) -> logging.Logger:
        """设置日志器"""
        if logger_name is None:
            logger_name = f"ansflow.{self.service_name}"
            
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, self.log_level))
        
        # 清除现有处理器
        logger.handlers.clear()
        
        # 添加主日志处理器
        main_handler = self.get_file_handler('main')
        logger.addHandler(main_handler)
        
        # 添加错误级别专用处理器
        error_handler = self.get_file_handler(level='error')
        error_handler.setLevel(logging.ERROR)
        error_handler.addFilter(lambda record: record.levelno >= logging.ERROR)
        logger.addHandler(error_handler)
        
        # 添加访问日志处理器（如果是Web服务）
        if self.service_name in ['django', 'fastapi']:
            access_handler = self.get_file_handler('access')
            access_handler.setLevel(logging.INFO)
            access_handler.addFilter(lambda record: hasattr(record, 'method'))
            logger.addHandler(access_handler)
        
        # 添加性能日志处理器
        if os.getenv('ENABLE_PERFORMANCE_LOGGING', 'false').lower() == 'true':
            perf_handler = self.get_file_handler('performance')
            perf_handler.setLevel(logging.INFO)
            perf_handler.addFilter(lambda record: hasattr(record, 'response_time_ms'))
            logger.addHandler(perf_handler)
        
        # 添加组件信息到所有记录
        if component:
            class ComponentFilter:
                def __init__(self, component_name):
                    self.component_name = component_name
                    
                def filter(self, record):
                    record.component = self.component_name
                    return True
                    
            logger.addFilter(ComponentFilter(component))
        
        return logger
    
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


# 便捷函数
def get_logger(service_name: str, component: str = None, logger_name: str = None) -> logging.Logger:
    """获取配置好的日志器"""
    manager = AnsFlowLogManager(service_name)
    return manager.setup_logger(logger_name, component)


def setup_service_logging(service_name: str):
    """为服务设置日志"""
    manager = AnsFlowLogManager(service_name)
    manager.setup_structlog()
    return manager.setup_logger()


# 日志聚合工具
class LogAggregator:
    """日志聚合器"""
    
    def __init__(self):
        self.log_dir = Path(os.getenv('LOG_DIR', '/Users/creed/Workspace/OpenSource/ansflow/logs'))
        self.services_dir = self.log_dir / 'services'
        self.aggregated_dir = self.log_dir / 'aggregated'
        
    def aggregate_logs(self, services: List[str] = None):
        """聚合服务日志"""
        if services is None:
            services = ['django', 'fastapi', 'system']
            
        # 聚合所有服务的主日志
        self._aggregate_by_type(services, 'main', 'all_services.log')
        
        # 聚合错误日志
        self._aggregate_by_type(services, 'error', 'errors_only.log')
        
        # 聚合访问日志
        self._aggregate_by_type(['django', 'fastapi'], 'access', 'access_combined.log')
        
    def _aggregate_by_type(self, services: List[str], log_type: str, output_file: str):
        """按类型聚合日志"""
        output_path = self.aggregated_dir / output_file
        
        with open(output_path, 'a', encoding='utf-8') as output:
            for service in services:
                service_dir = self.services_dir / service
                log_files = list(service_dir.glob(f"{service}_{log_type}.log"))
                
                for log_file in log_files:
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                output.write(line)
                    except Exception as e:
                        print(f"聚合日志失败 {log_file}: {e}")
