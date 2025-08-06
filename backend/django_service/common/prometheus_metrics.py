"""
AnsFlow日志系统Prometheus指标收集器 - Phase 3
提供日志相关的指标暴露和监控功能
"""
import time
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import json

try:
    from prometheus_client import Counter as PrometheusCounter
    from prometheus_client import Histogram, Gauge, Info, generate_latest
    from prometheus_client import CollectorRegistry, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from django.conf import settings
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger(__name__)


class LogMetricsCollector:
    """日志指标收集器"""
    
    def __init__(self):
        self.log_dir = Path(getattr(settings, 'LOG_DIR', '/Users/creed/Workspace/OpenSource/ansflow/logs'))
        self.logger = logging.getLogger(__name__)
        
        if not PROMETHEUS_AVAILABLE:
            self.logger.warning("Prometheus客户端不可用，指标收集功能将被禁用")
            return
            
        # 创建自定义注册表
        self.registry = CollectorRegistry()
        
        # 定义指标
        self._setup_metrics()
    
    def _setup_metrics(self):
        """设置Prometheus指标"""
        if not PROMETHEUS_AVAILABLE:
            return
            
        # HTTP请求指标
        self.http_requests_total = PrometheusCounter(
            'ansflow_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'ansflow_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # 日志相关指标
        self.log_messages_total = PrometheusCounter(
            'ansflow_log_messages_total',
            'Total log messages',
            ['level', 'service'],
            registry=self.registry
        )
        
        self.log_write_errors_total = PrometheusCounter(
            'ansflow_log_write_errors_total',
            'Total log write errors',
            ['service'],
            registry=self.registry
        )
        
        # Pipeline执行指标
        self.pipeline_executions_total = PrometheusCounter(
            'ansflow_pipeline_executions_total',
            'Total pipeline executions',
            ['status', 'pipeline_type'],
            registry=self.registry
        )
        
        self.pipeline_duration = Histogram(
            'ansflow_pipeline_duration_seconds',
            'Pipeline execution duration in seconds',
            ['pipeline_type'],
            registry=self.registry
        )
        
        # 系统健康指标
        self.active_connections = Gauge(
            'ansflow_active_connections_current',
            'Current active connections',
            ['service'],
            registry=self.registry
        )
        
        self.log_buffer_size = Gauge(
            'ansflow_log_buffer_size_current',
            'Current log buffer size',
            registry=self.registry
        )
        
        self.disk_usage_percent = Gauge(
            'ansflow_disk_usage_percent',
            'Disk usage percentage',
            ['mount_point'],
            registry=self.registry
        )
        
        # 系统信息
        self.system_info = Info(
            'ansflow_system_info',
            'AnsFlow system information',
            registry=self.registry
        )
        
        # 设置系统信息
        self.system_info.info({
            'version': '1.0.0',
            'phase': '3',
            'features': 'real_time_monitoring,historical_analysis,trend_analysis'
        })
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """记录HTTP请求指标"""
        if not PROMETHEUS_AVAILABLE:
            return
            
        try:
            self.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code)
            ).inc()
            
            self.http_request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
        except Exception as e:
            self.logger.error(f"记录HTTP请求指标失败: {e}")
    
    def record_log_message(self, level: str, service: str):
        """记录日志消息指标"""
        if not PROMETHEUS_AVAILABLE:
            return
            
        try:
            self.log_messages_total.labels(
                level=level,
                service=service
            ).inc()
        except Exception as e:
            self.logger.error(f"记录日志消息指标失败: {e}")
    
    def record_log_write_error(self, service: str):
        """记录日志写入错误"""
        if not PROMETHEUS_AVAILABLE:
            return
            
        try:
            self.log_write_errors_total.labels(service=service).inc()
        except Exception as e:
            self.logger.error(f"记录日志写入错误指标失败: {e}")
    
    def record_pipeline_execution(self, status: str, pipeline_type: str, duration: float):
        """记录管道执行指标"""
        if not PROMETHEUS_AVAILABLE:
            return
            
        try:
            self.pipeline_executions_total.labels(
                status=status,
                pipeline_type=pipeline_type
            ).inc()
            
            self.pipeline_duration.labels(
                pipeline_type=pipeline_type
            ).observe(duration)
        except Exception as e:
            self.logger.error(f"记录管道执行指标失败: {e}")
    
    def update_active_connections(self, service: str, count: int):
        """更新活跃连接数"""
        if not PROMETHEUS_AVAILABLE:
            return
            
        try:
            self.active_connections.labels(service=service).set(count)
        except Exception as e:
            self.logger.error(f"更新活跃连接数指标失败: {e}")
    
    def update_log_buffer_size(self, size: int):
        """更新日志缓冲区大小"""
        if not PROMETHEUS_AVAILABLE:
            return
            
        try:
            self.log_buffer_size.set(size)
        except Exception as e:
            self.logger.error(f"更新日志缓冲区大小指标失败: {e}")
    
    def update_disk_usage(self, mount_point: str, usage_percent: float):
        """更新磁盘使用率"""
        if not PROMETHEUS_AVAILABLE:
            return
            
        try:
            self.disk_usage_percent.labels(mount_point=mount_point).set(usage_percent)
        except Exception as e:
            self.logger.error(f"更新磁盘使用率指标失败: {e}")
    
    def collect_log_metrics(self) -> Dict[str, Any]:
        """收集日志相关指标"""
        try:
            # 分析最近的日志文件
            metrics = {
                'collection_time': datetime.now().isoformat(),
                'log_files': 0,
                'total_size_bytes': 0,
                'by_level': Counter(),
                'by_service': Counter(),
                'by_hour': defaultdict(int),
                'errors_last_hour': 0
            }
            
            # 扫描日志目录
            for log_file in self.log_dir.rglob('*.log*'):
                if not log_file.is_file():
                    continue
                    
                try:
                    file_stat = log_file.stat()
                    metrics['log_files'] += 1
                    metrics['total_size_bytes'] += file_stat.st_size
                    
                    # 分析最近1小时的日志
                    cutoff_time = datetime.now() - timedelta(hours=1)
                    if datetime.fromtimestamp(file_stat.st_mtime) > cutoff_time:
                        file_metrics = self._analyze_log_file(log_file)
                        
                        for level, count in file_metrics['by_level'].items():
                            metrics['by_level'][level] += count
                        
                        for service, count in file_metrics['by_service'].items():
                            metrics['by_service'][service] += count
                            
                        metrics['errors_last_hour'] += file_metrics.get('errors', 0)
                        
                except Exception as e:
                    self.logger.warning(f"分析日志文件 {log_file} 失败: {e}")
            
            # 更新Prometheus指标
            if PROMETHEUS_AVAILABLE:
                self.update_disk_usage('/logs', (metrics['total_size_bytes'] / (1024**3)) * 100)  # 假设1GB限制
                
                # 更新日志级别统计
                for level, count in metrics['by_level'].items():
                    for service in ['django', 'fastapi', 'system']:
                        # 这里简化处理，实际应该从日志中解析
                        pass
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"收集日志指标失败: {e}")
            return {
                'collection_time': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _analyze_log_file(self, file_path: Path) -> Dict[str, Any]:
        """分析单个日志文件"""
        metrics = {
            'by_level': Counter(),
            'by_service': Counter(),
            'errors': 0
        }
        
        try:
            # 只读取文件的最后部分（最近的日志）
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 移动到文件末尾附近
                f.seek(max(0, file_path.stat().st_size - 10240))  # 读取最后10KB
                lines = f.readlines()
                
                for line in lines[-100:]:  # 只分析最后100行
                    try:
                        # 尝试解析JSON格式的日志
                        if line.strip().startswith('{'):
                            log_data = json.loads(line.strip())
                            level = log_data.get('level', 'INFO')
                            service = log_data.get('service', 'unknown')
                            
                            metrics['by_level'][level] += 1
                            metrics['by_service'][service] += 1
                            
                            if level in ['ERROR', 'CRITICAL']:
                                metrics['errors'] += 1
                                
                    except (json.JSONDecodeError, ValueError):
                        # 跳过无法解析的行
                        continue
                        
        except Exception as e:
            self.logger.warning(f"分析日志文件内容失败 {file_path}: {e}")
        
        return metrics
    
    def get_metrics_text(self) -> str:
        """获取Prometheus格式的指标文本"""
        if not PROMETHEUS_AVAILABLE:
            return "# Prometheus客户端不可用\n"
            
        try:
            # 收集最新的指标
            self.collect_log_metrics()
            
            # 生成Prometheus格式的指标
            return generate_latest(self.registry).decode('utf-8')
        except Exception as e:
            self.logger.error(f"生成Prometheus指标失败: {e}")
            return f"# 错误: {str(e)}\n"


# 全局指标收集器实例
metrics_collector = LogMetricsCollector()


class PrometheusMetricsView(APIView):
    """Prometheus指标暴露API"""
    permission_classes = []  # 允许Prometheus服务器访问
    
    def get(self, request):
        """返回Prometheus格式的指标"""
        if not PROMETHEUS_AVAILABLE:
            return HttpResponse(
                "# Prometheus客户端不可用\n",
                content_type="text/plain"
            )
        
        try:
            metrics_text = metrics_collector.get_metrics_text()
            return HttpResponse(
                metrics_text,
                content_type=CONTENT_TYPE_LATEST
            )
        except Exception as e:
            logger.error(f"获取Prometheus指标失败: {e}")
            return HttpResponse(
                f"# 错误: {str(e)}\n",
                content_type="text/plain",
                status=500
            )


class LogMetricsAPIView(APIView):
    """日志指标API - 提供JSON格式的指标数据"""
    permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(60))  # 缓存1分钟
    def get(self, request):
        """获取日志指标数据"""
        try:
            metrics = metrics_collector.collect_log_metrics()
            
            # 转换Counter对象为普通字典
            if 'by_level' in metrics:
                metrics['by_level'] = dict(metrics['by_level'])
            if 'by_service' in metrics:
                metrics['by_service'] = dict(metrics['by_service'])
            
            return Response({
                'success': True,
                'data': metrics
            })
        except Exception as e:
            logger.error(f"获取日志指标失败: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)


def record_http_request_metric(method: str, endpoint: str, status_code: int, duration: float):
    """便捷函数：记录HTTP请求指标"""
    metrics_collector.record_http_request(method, endpoint, status_code, duration)


def record_log_message_metric(level: str, service: str):
    """便捷函数：记录日志消息指标"""
    metrics_collector.record_log_message(level, service)


def record_pipeline_execution_metric(status: str, pipeline_type: str, duration: float):
    """便捷函数：记录管道执行指标"""
    metrics_collector.record_pipeline_execution(status, pipeline_type, duration)


# 中间件集成函数
def integrate_metrics_middleware():
    """集成指标收集到中间件"""
    pass  # 这个函数将在中间件中被调用
