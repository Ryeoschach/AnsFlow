"""
Prometheus监控集成模块
提供FastAPI应用的全面性能监控
"""
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from fastapi import FastAPI, Response
import time
import psutil
import structlog

logger = structlog.get_logger(__name__)

# 自定义业务指标
# WebSocket连接指标
websocket_connections = Gauge(
    'ansflow_websocket_connections_total',
    'Total number of active WebSocket connections',
    ['endpoint', 'status']
)

websocket_messages = Counter(
    'ansflow_websocket_messages_total',
    'Total number of WebSocket messages',
    ['endpoint', 'direction', 'type']
)

# 流水线执行指标
pipeline_executions = Counter(
    'ansflow_pipeline_executions_total',
    'Total number of pipeline executions',
    ['status', 'pipeline_type']
)

pipeline_execution_duration = Histogram(
    'ansflow_pipeline_execution_duration_seconds',
    'Duration of pipeline executions',
    ['pipeline_type', 'status'],
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600]
)

# CI/CD工具集成指标
cicd_tool_requests = Counter(
    'ansflow_cicd_tool_requests_total',
    'Total number of CI/CD tool requests',
    ['tool_type', 'endpoint', 'status']
)

cicd_tool_response_time = Histogram(
    'ansflow_cicd_tool_response_duration_seconds',
    'Response time of CI/CD tool requests',
    ['tool_type', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1, 2.5, 5, 10]
)

# 缓存性能指标
cache_operations = Counter(
    'ansflow_cache_operations_total',
    'Total number of cache operations',
    ['cache_type', 'operation', 'status']
)

cache_hit_ratio = Gauge(
    'ansflow_cache_hit_ratio',
    'Cache hit ratio',
    ['cache_type']
)

# 数据库连接指标
database_connections = Gauge(
    'ansflow_database_connections_active',
    'Number of active database connections',
    ['database_type']
)

database_query_duration = Histogram(
    'ansflow_database_query_duration_seconds',
    'Database query execution time',
    ['database_type', 'operation'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5]
)

# 系统资源指标
system_cpu_usage = Gauge(
    'ansflow_system_cpu_usage_percent',
    'System CPU usage percentage'
)

system_memory_usage = Gauge(
    'ansflow_system_memory_usage_bytes',
    'System memory usage in bytes',
    ['type']
)

system_disk_usage = Gauge(
    'ansflow_system_disk_usage_bytes',
    'System disk usage in bytes',
    ['mount_point', 'type']
)

# 应用信息指标
app_info = Info(
    'ansflow_app_info',
    'Application information'
)

# 健康检查指标
health_check_status = Gauge(
    'ansflow_health_check_status',
    'Health check status (1=healthy, 0=unhealthy)',
    ['service', 'check_type']
)


class PrometheusMonitoring:
    """Prometheus监控管理器"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.instrumentator = None
        self._setup_instrumentator()
        self._setup_custom_metrics()
        self._setup_system_metrics()
    
    def _setup_instrumentator(self):
        """配置FastAPI Instrumentator"""
        self.instrumentator = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            should_respect_env_var=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=["/metrics", "/health", "/docs", "/redoc", "/openapi.json"],
            env_var_name="ENABLE_METRICS",
            inprogress_name="ansflow_requests_inprogress",
            inprogress_labels=True,
        )
        
        # 添加默认指标
        self.instrumentator.add(
            metrics.default(
                metric_namespace="ansflow",
                metric_subsystem="http"
            )
        )
        
        self.instrumentator.add(
            metrics.combined_size(
                should_include_handler=True,
                should_include_method=True,
                should_include_status=True,
                metric_namespace="ansflow",
                metric_subsystem="http",
            )
        )
    
    def _setup_custom_metrics(self):
        """设置自定义指标"""
        # 设置应用信息
        app_info.info({
            'version': '1.3.0',
            'service': 'ansflow-fastapi',
            'environment': 'development',  # 可从环境变量获取
            'component': 'api-gateway'
        })
        
        logger.info("Custom metrics initialized")
    
    def _setup_system_metrics(self):
        """设置系统指标监控"""
        # 这些指标将通过定期任务更新
        pass
    
    def instrument_app(self):
        """为FastAPI应用启用监控"""
        if self.instrumentator:
            self.instrumentator.instrument(self.app)
            self.instrumentator.expose(self.app, endpoint="/metrics")
            logger.info("FastAPI application instrumented with Prometheus metrics")
    
    def update_system_metrics(self):
        """更新系统资源指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            system_cpu_usage.set(cpu_percent)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            system_memory_usage.labels(type='total').set(memory.total)
            system_memory_usage.labels(type='used').set(memory.used)
            system_memory_usage.labels(type='available').set(memory.available)
            system_memory_usage.labels(type='percent').set(memory.percent)
            
            # 磁盘使用情况
            disk_usage = psutil.disk_usage('/')
            system_disk_usage.labels(mount_point='/', type='total').set(disk_usage.total)
            system_disk_usage.labels(mount_point='/', type='used').set(disk_usage.used)
            system_disk_usage.labels(mount_point='/', type='free').set(disk_usage.free)
            
        except Exception as e:
            logger.error("Failed to update system metrics", error=str(e))


# 业务指标更新函数
def track_websocket_connection(endpoint: str, status: str, delta: int = 1):
    """跟踪WebSocket连接"""
    websocket_connections.labels(endpoint=endpoint, status=status).inc(delta)

def track_websocket_message(endpoint: str, direction: str, message_type: str):
    """跟踪WebSocket消息"""
    websocket_messages.labels(endpoint=endpoint, direction=direction, type=message_type).inc()

def track_pipeline_execution(status: str, pipeline_type: str, duration: float = None):
    """跟踪流水线执行"""
    pipeline_executions.labels(status=status, pipeline_type=pipeline_type).inc()
    if duration is not None:
        pipeline_execution_duration.labels(pipeline_type=pipeline_type, status=status).observe(duration)

def track_cicd_tool_request(tool_type: str, endpoint: str, status: str, duration: float):
    """跟踪CI/CD工具请求"""
    cicd_tool_requests.labels(tool_type=tool_type, endpoint=endpoint, status=status).inc()
    cicd_tool_response_time.labels(tool_type=tool_type, endpoint=endpoint).observe(duration)

def track_cache_operation(cache_type: str, operation: str, status: str):
    """跟踪缓存操作"""
    cache_operations.labels(cache_type=cache_type, operation=operation, status=status).inc()

def update_cache_hit_ratio(cache_type: str, hit_ratio: float):
    """更新缓存命中率"""
    cache_hit_ratio.labels(cache_type=cache_type).set(hit_ratio)

def track_database_operation(database_type: str, operation: str, duration: float):
    """跟踪数据库操作"""
    database_query_duration.labels(database_type=database_type, operation=operation).observe(duration)

def update_database_connections(database_type: str, count: int):
    """更新数据库连接数"""
    database_connections.labels(database_type=database_type).set(count)

def update_health_check(service: str, check_type: str, is_healthy: bool):
    """更新健康检查状态"""
    health_check_status.labels(service=service, check_type=check_type).set(1 if is_healthy else 0)


# 导出的监控实例（将在main.py中使用）
monitoring = None

def init_monitoring(app: FastAPI) -> PrometheusMonitoring:
    """初始化监控系统"""
    global monitoring
    monitoring = PrometheusMonitoring(app)
    monitoring.instrument_app()
    logger.info("Prometheus monitoring system initialized")
    return monitoring

def get_monitoring() -> PrometheusMonitoring:
    """获取监控实例"""
    return monitoring
