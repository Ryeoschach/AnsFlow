"""
系统监控日志配置模块
用于监控系统资源、Docker容器状态等
"""

import os
import json
import psutil
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import time


class SystemMonitorLogger:
    """系统监控日志器"""
    
    def __init__(self):
        self.service_name = 'system'
        self.log_dir = Path(os.getenv('LOG_DIR', '/Users/creed/Workspace/OpenSource/ansflow/logs'))
        self.service_log_dir = self.log_dir / 'services' / self.service_name
        self.service_log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_format = os.getenv('LOG_FORMAT', 'json')
        self.log_retention_days = int(os.getenv('LOG_RETENTION_DAYS', '30'))
        
        # 设置日志器
        self._setup_logger()
        
    def _setup_logger(self):
        """设置系统监控日志器"""
        self.logger = logging.getLogger('ansflow.system')
        self.logger.setLevel(getattr(logging, self.log_level))
        
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 主日志处理器
        main_handler = self._create_handler('main')
        self.logger.addHandler(main_handler)
        
        # 性能日志处理器
        if os.getenv('ENABLE_PERFORMANCE_LOGGING', 'false').lower() == 'true':
            perf_handler = self._create_handler('performance')
            self.logger.addHandler(perf_handler)
            
        # 错误日志处理器
        error_handler = self._create_handler('error')
        error_handler.setLevel(logging.ERROR)
        self.logger.addHandler(error_handler)
        
    def _create_handler(self, log_type: str) -> logging.Handler:
        """创建日志处理器"""
        file_path = self.service_log_dir / f"{self.service_name}_{log_type}.log"
        
        handler = logging.handlers.TimedRotatingFileHandler(
            file_path,
            when='midnight',
            interval=1,
            backupCount=self.log_retention_days,
            encoding='utf-8'
        )
        
        # 设置格式化器
        if self.log_format == 'json':
            formatter = SystemJSONFormatter(self.service_name)
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        handler.setFormatter(formatter)
        
        return handler
        
    def log_system_metrics(self):
        """记录系统指标"""
        metrics = self._collect_system_metrics()
        
        # 创建日志记录
        log_record = logging.LogRecord(
            name='ansflow.system',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg="System metrics collected",
            args=(),
            exc_info=None
        )
        
        # 添加指标数据
        log_record.component = 'system_monitor'
        log_record.metrics = metrics
        log_record.metric_type = 'system'
        
        self.logger.handle(log_record)
        
    def log_docker_metrics(self):
        """记录Docker容器指标"""
        try:
            import docker
            client = docker.from_env()
            
            containers = client.containers.list(all=True)
            container_metrics = []
            
            for container in containers:
                try:
                    stats = container.stats(stream=False)
                    
                    # 计算CPU使用率
                    cpu_usage = self._calculate_cpu_usage(stats)
                    
                    # 获取内存使用情况
                    memory_stats = stats.get('memory_stats', {})
                    memory_usage_mb = memory_stats.get('usage', 0) / 1024 / 1024
                    memory_limit_mb = memory_stats.get('limit', 0) / 1024 / 1024
                    
                    container_info = {
                        'name': container.name,
                        'id': container.short_id,
                        'status': container.status,
                        'image': container.image.tags[0] if container.image.tags else 'unknown',
                        'cpu_usage_percent': round(cpu_usage, 2),
                        'memory_usage_mb': round(memory_usage_mb, 2),
                        'memory_limit_mb': round(memory_limit_mb, 2),
                        'memory_usage_percent': round((memory_usage_mb / memory_limit_mb) * 100, 2) if memory_limit_mb > 0 else 0
                    }
                    
                    container_metrics.append(container_info)
                    
                except Exception as e:
                    self.logger.error(f"获取容器 {container.name} 指标失败: {e}")
                    
            # 记录Docker指标日志
            log_record = logging.LogRecord(
                name='ansflow.system',
                level=logging.INFO,
                pathname='',
                lineno=0,
                msg=f"Docker metrics collected for {len(container_metrics)} containers",
                args=(),
                exc_info=None
            )
            
            log_record.component = 'docker_monitor'
            log_record.metrics = container_metrics
            log_record.metric_type = 'docker'
            
            self.logger.handle(log_record)
            
        except ImportError:
            self.logger.warning("Docker Python客户端未安装，跳过Docker指标收集")
        except Exception as e:
            self.logger.error(f"Docker指标收集失败: {e}")
            
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        # CPU指标
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # 内存指标
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # 磁盘指标
        disk_usage = psutil.disk_usage('/')
        
        # 网络指标
        net_io = psutil.net_io_counters()
        
        # 进程指标
        process_count = len(psutil.pids())
        
        return {
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count,
                'frequency_mhz': cpu_freq.current if cpu_freq else None
            },
            'memory': {
                'total_gb': round(memory.total / 1024**3, 2),
                'available_gb': round(memory.available / 1024**3, 2),
                'used_gb': round(memory.used / 1024**3, 2),
                'percent': memory.percent
            },
            'swap': {
                'total_gb': round(swap.total / 1024**3, 2),
                'used_gb': round(swap.used / 1024**3, 2),
                'percent': swap.percent
            },
            'disk': {
                'total_gb': round(disk_usage.total / 1024**3, 2),
                'used_gb': round(disk_usage.used / 1024**3, 2),
                'free_gb': round(disk_usage.free / 1024**3, 2),
                'percent': round((disk_usage.used / disk_usage.total) * 100, 2)
            },
            'network': {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            },
            'processes': {
                'count': process_count
            }
        }
        
    def _calculate_cpu_usage(self, stats: Dict) -> float:
        """计算容器CPU使用率"""
        try:
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})
            
            cpu_usage = cpu_stats.get('cpu_usage', {})
            precpu_usage = precpu_stats.get('cpu_usage', {})
            
            cpu_delta = cpu_usage.get('total_usage', 0) - precpu_usage.get('total_usage', 0)
            system_delta = cpu_stats.get('system_cpu_usage', 0) - precpu_stats.get('system_cpu_usage', 0)
            
            if system_delta > 0 and cpu_delta >= 0:
                cpu_count = len(cpu_usage.get('percpu_usage', []))
                if cpu_count == 0:
                    cpu_count = 1
                return (cpu_delta / system_delta) * cpu_count * 100.0
                
        except Exception as e:
            print(f"CPU使用率计算失败: {e}")
            
        return 0.0
        
    def log_application_metrics(self, service_name: str, metrics: Dict[str, Any]):
        """记录应用程序指标"""
        log_record = logging.LogRecord(
            name='ansflow.system',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg=f"Application metrics for {service_name}",
            args=(),
            exc_info=None
        )
        
        log_record.component = 'app_monitor'
        log_record.service_name = service_name
        log_record.metrics = metrics
        log_record.metric_type = 'application'
        
        self.logger.handle(log_record)
        
    def log_error(self, error_msg: str, error_type: str = 'system', **kwargs):
        """记录系统错误"""
        log_record = logging.LogRecord(
            name='ansflow.system',
            level=logging.ERROR,
            pathname='',
            lineno=0,
            msg=error_msg,
            args=(),
            exc_info=None
        )
        
        log_record.component = 'system_monitor'
        log_record.error_type = error_type
        
        # 添加额外的错误信息
        for key, value in kwargs.items():
            setattr(log_record, key, value)
            
        self.logger.handle(log_record)


class SystemJSONFormatter(logging.Formatter):
    """系统监控专用JSON格式化器"""
    
    def __init__(self, service_name="system"):
        super().__init__()
        self.service_name = service_name
        
    def format(self, record):
        """格式化日志记录为JSON格式"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "level": record.levelname,
            "service": self.service_name,
            "component": getattr(record, 'component', 'unknown'),
            "module": record.name,
            "message": record.getMessage(),
        }
        
        # 添加指标数据
        if hasattr(record, 'metrics'):
            log_data['metrics'] = record.metrics
            
        if hasattr(record, 'metric_type'):
            log_data['metric_type'] = record.metric_type
            
        if hasattr(record, 'service_name'):
            log_data['monitored_service'] = record.service_name
            
        if hasattr(record, 'error_type'):
            log_data['error_type'] = record.error_type
            
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
            
        return json.dumps(log_data, ensure_ascii=False)


# 便捷函数
def get_system_logger() -> SystemMonitorLogger:
    """获取系统监控日志器"""
    return SystemMonitorLogger()


# 系统指标收集装饰器
def monitor_system_resource(metric_name: str = None):
    """系统资源监控装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            system_logger = get_system_logger()
            
            # 收集开始时的系统状态
            start_metrics = system_logger._collect_system_metrics()
            
            try:
                result = func(*args, **kwargs)
                
                # 收集结束时的系统状态
                end_time = time.time()
                end_metrics = system_logger._collect_system_metrics()
                
                # 计算资源使用变化
                execution_metrics = {
                    'function_name': func.__name__,
                    'metric_name': metric_name or func.__name__,
                    'execution_time_seconds': round(end_time - start_time, 3),
                    'cpu_usage_before': start_metrics['cpu']['percent'],
                    'cpu_usage_after': end_metrics['cpu']['percent'],
                    'memory_used_before_gb': start_metrics['memory']['used_gb'],
                    'memory_used_after_gb': end_metrics['memory']['used_gb'],
                    'success': True
                }
                
                system_logger.log_application_metrics('system_monitor', execution_metrics)
                return result
                
            except Exception as e:
                end_time = time.time()
                end_metrics = system_logger._collect_system_metrics()
                
                # 记录异常情况下的系统状态
                execution_metrics = {
                    'function_name': func.__name__,
                    'metric_name': metric_name or func.__name__,
                    'execution_time_seconds': round(end_time - start_time, 3),
                    'cpu_usage_before': start_metrics['cpu']['percent'],
                    'cpu_usage_after': end_metrics['cpu']['percent'],
                    'memory_used_before_gb': start_metrics['memory']['used_gb'],
                    'memory_used_after_gb': end_metrics['memory']['used_gb'],
                    'success': False,
                    'error': str(e)
                }
                
                system_logger.log_application_metrics('system_monitor', execution_metrics)
                raise
                
        return wrapper
    return decorator
