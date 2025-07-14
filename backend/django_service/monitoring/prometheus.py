"""
Django Prometheus metrics collection for AnsFlow platform.

This module extends django-prometheus with custom business metrics for better
insight into the Django service performance and usage patterns.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from django.http import HttpResponse
from django.views import View
import time
import logging

logger = logging.getLogger(__name__)

# Custom Django metrics
django_requests_total = Counter(
    'django_requests_total',
    'Total Django requests',
    ['method', 'endpoint', 'status_code']
)

django_request_duration_seconds = Histogram(
    'django_request_duration_seconds',
    'Django request duration in seconds',
    ['method', 'endpoint']
)

django_active_sessions = Gauge(
    'django_active_sessions_total',
    'Total active Django sessions'
)

django_database_connections = Gauge(
    'django_database_connections_total',
    'Total database connections',
    ['database']
)

django_cache_operations = Counter(
    'django_cache_operations_total',
    'Total cache operations',
    ['operation', 'backend']
)

django_task_queue_size = Gauge(
    'django_task_queue_size',
    'Current task queue size',
    ['queue_name']
)

django_background_tasks = Counter(
    'django_background_tasks_total',
    'Total background tasks',
    ['task_name', 'status']
)

# Custom business metrics
ansflow_pipelines_total = Counter(
    'ansflow_pipelines_total',
    'Total pipeline executions',
    ['project', 'status']
)

ansflow_pipeline_duration_seconds = Histogram(
    'ansflow_pipeline_duration_seconds',
    'Pipeline execution duration in seconds',
    ['project', 'pipeline_type']
)

ansflow_active_projects = Gauge(
    'ansflow_active_projects_total',
    'Total active projects'
)

ansflow_user_activity = Counter(
    'ansflow_user_activity_total',
    'User activity events',
    ['action', 'user_type']
)

ansflow_api_calls = Counter(
    'ansflow_api_calls_total',
    'Total API calls',
    ['endpoint', 'method', 'status']
)

ansflow_integration_calls = Counter(
    'ansflow_integration_calls_total',
    'Integration service calls',
    ['integration_type', 'status']
)


class DjangoMetricsCollector:
    """Collector for Django-specific metrics."""
    
    @staticmethod
    def collect_session_metrics():
        """Collect session-related metrics."""
        try:
            from django.contrib.sessions.models import Session
            from django.utils import timezone
            
            active_sessions = Session.objects.filter(
                expire_date__gt=timezone.now()
            ).count()
            django_active_sessions.set(active_sessions)
            
        except Exception as e:
            logger.warning(f"Failed to collect session metrics: {e}")
    
    @staticmethod
    def collect_database_metrics():
        """Collect database connection metrics."""
        try:
            from django.db import connections
            
            for alias in connections:
                connection = connections[alias]
                if hasattr(connection, 'queries_logged'):
                    django_database_connections.labels(database=alias).set(
                        len(connection.queries_logged)
                    )
                    
        except Exception as e:
            logger.warning(f"Failed to collect database metrics: {e}")
    
    @staticmethod
    def collect_cache_metrics():
        """Collect cache-related metrics."""
        try:
            from django.core.cache import caches
            from django.core.cache.backends.redis import RedisCache
            
            for cache_name in caches:
                cache = caches[cache_name]
                if isinstance(cache, RedisCache):
                    # Redis-specific metrics would go here
                    pass
                    
        except Exception as e:
            logger.warning(f"Failed to collect cache metrics: {e}")
    
    @staticmethod
    def collect_business_metrics():
        """Collect business-specific metrics."""
        try:
            # Collect pipeline metrics
            from pipelines.models import Pipeline
            
            active_projects_count = Pipeline.objects.values('project_id').distinct().count()
            ansflow_active_projects.set(active_projects_count)
            
        except Exception as e:
            logger.warning(f"Failed to collect business metrics: {e}")


class MetricsMiddleware:
    """Custom middleware for collecting request metrics."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        # Get response
        response = self.get_response(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        method = request.method
        path = request.path
        status_code = str(response.status_code)
        
        django_requests_total.labels(
            method=method,
            endpoint=path,
            status_code=status_code
        ).inc()
        
        django_request_duration_seconds.labels(
            method=method,
            endpoint=path
        ).observe(duration)
        
        # Record API-specific metrics
        if path.startswith('/api/'):
            ansflow_api_calls.labels(
                endpoint=path,
                method=method,
                status=status_code
            ).inc()
        
        return response


class CustomMetricsView(View):
    """Custom metrics endpoint with additional Django metrics."""
    
    def get(self, request):
        """Return Prometheus metrics."""
        # Collect current metrics
        collector = DjangoMetricsCollector()
        collector.collect_session_metrics()
        collector.collect_database_metrics()
        collector.collect_cache_metrics()
        collector.collect_business_metrics()
        
        # Generate metrics response
        metrics_data = generate_latest()
        return HttpResponse(
            metrics_data,
            content_type='text/plain; version=0.0.4; charset=utf-8'
        )


# Helper functions for business logic integration
def record_pipeline_execution(project_name, status, duration=None, pipeline_type=None):
    """Record pipeline execution metrics."""
    ansflow_pipelines_total.labels(
        project=project_name,
        status=status
    ).inc()
    
    if duration is not None and pipeline_type is not None:
        ansflow_pipeline_duration_seconds.labels(
            project=project_name,
            pipeline_type=pipeline_type
        ).observe(duration)


def record_user_activity(action, user_type='regular'):
    """Record user activity metrics."""
    ansflow_user_activity.labels(
        action=action,
        user_type=user_type
    ).inc()


def record_integration_call(integration_type, status):
    """Record integration service call metrics."""
    ansflow_integration_calls.labels(
        integration_type=integration_type,
        status=status
    ).inc()


def record_cache_operation(operation, backend='default'):
    """Record cache operation metrics."""
    django_cache_operations.labels(
        operation=operation,
        backend=backend
    ).inc()


def record_background_task(task_name, status):
    """Record background task metrics."""
    django_background_tasks.labels(
        task_name=task_name,
        status=status
    ).inc()


def update_task_queue_size(queue_name, size):
    """Update task queue size metric."""
    django_task_queue_size.labels(queue_name=queue_name).set(size)
