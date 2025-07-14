"""
Example integration of monitoring metrics in business logic.

This module shows how to integrate Prometheus metrics into existing
Django business logic across different modules.
"""

from .prometheus import (
    record_pipeline_execution,
    record_user_activity,
    record_integration_call,
    record_background_task,
    update_task_queue_size
)
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)


def monitor_pipeline_execution(func):
    """Decorator to monitor pipeline execution."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        project_name = getattr(self, 'project_name', 'unknown')
        pipeline_type = getattr(self, 'pipeline_type', 'default')
        
        try:
            result = func(self, *args, **kwargs)
            
            # Record successful execution
            duration = time.time() - start_time
            record_pipeline_execution(
                project_name=project_name,
                status='success',
                duration=duration,
                pipeline_type=pipeline_type
            )
            
            return result
            
        except Exception as e:
            # Record failed execution
            duration = time.time() - start_time
            record_pipeline_execution(
                project_name=project_name,
                status='failed',
                duration=duration,
                pipeline_type=pipeline_type
            )
            
            logger.error(f"Pipeline execution failed: {e}")
            raise
    
    return wrapper


def monitor_api_view(view_name):
    """Decorator to monitor API view calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            user_type = 'authenticated' if request.user.is_authenticated else 'anonymous'
            
            try:
                response = func(request, *args, **kwargs)
                
                # Record successful API call
                record_user_activity(f'api_{view_name}', user_type)
                
                return response
                
            except Exception as e:
                # Record failed API call
                record_user_activity(f'api_{view_name}_failed', user_type)
                logger.error(f"API view {view_name} failed: {e}")
                raise
        
        return wrapper
    return decorator


def monitor_integration_call(integration_type):
    """Decorator to monitor external integration calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                record_integration_call(integration_type, 'success')
                return result
                
            except Exception as e:
                record_integration_call(integration_type, 'failed')
                logger.error(f"{integration_type} integration failed: {e}")
                raise
        
        return wrapper
    return decorator


class MonitoredCeleryTask:
    """Base class for monitored Celery tasks."""
    
    def __init__(self, task_name):
        self.task_name = task_name
    
    def apply_async(self, *args, **kwargs):
        """Override apply_async to record queue metrics."""
        try:
            # Record task queued
            record_background_task(self.task_name, 'queued')
            
            # Get current queue size (this would need actual queue inspection)
            # For now, we'll use a placeholder
            update_task_queue_size('default', 10)  # This should be dynamic
            
            # Call original apply_async
            result = super().apply_async(*args, **kwargs)
            
            return result
            
        except Exception as e:
            record_background_task(self.task_name, 'queue_failed')
            raise
    
    def run(self, *args, **kwargs):
        """Override run to record execution metrics."""
        try:
            record_background_task(self.task_name, 'started')
            
            # Run the actual task
            result = super().run(*args, **kwargs)
            
            record_background_task(self.task_name, 'completed')
            return result
            
        except Exception as e:
            record_background_task(self.task_name, 'failed')
            logger.error(f"Background task {self.task_name} failed: {e}")
            raise


# Example usage in views
class ExampleAPIViewMixin:
    """Mixin to add monitoring to API views."""
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to add monitoring."""
        view_name = self.__class__.__name__
        user_type = 'authenticated' if request.user.is_authenticated else 'anonymous'
        
        try:
            response = super().dispatch(request, *args, **kwargs)
            record_user_activity(f'view_{view_name}', user_type)
            return response
            
        except Exception as e:
            record_user_activity(f'view_{view_name}_failed', user_type)
            raise


# Example integration for pipeline models
class MonitoredPipelineManager:
    """Example manager class with monitoring integration."""
    
    @monitor_pipeline_execution
    def execute_pipeline(self, pipeline_config):
        """Execute a pipeline with monitoring."""
        # Simulate pipeline execution
        time.sleep(0.1)  # Simulate work
        
        if pipeline_config.get('should_fail'):
            raise Exception("Simulated pipeline failure")
        
        return {'status': 'completed', 'result': 'success'}
    
    @monitor_integration_call('kubernetes')
    def deploy_to_kubernetes(self, deployment_config):
        """Deploy to Kubernetes with monitoring."""
        # Simulate K8s deployment
        time.sleep(0.05)
        return {'deployment_id': 'dep-123', 'status': 'deployed'}
    
    @monitor_integration_call('docker')
    def build_docker_image(self, image_config):
        """Build Docker image with monitoring."""
        # Simulate Docker build
        time.sleep(0.2)
        return {'image_id': 'img-456', 'status': 'built'}


# Example middleware for comprehensive request monitoring
class MetricsLoggingMiddleware:
    """Additional middleware for detailed request logging."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        # Log request start
        user_type = 'authenticated' if request.user.is_authenticated else 'anonymous'
        record_user_activity('request_received', user_type)
        
        response = self.get_response(request)
        
        # Log request completion
        duration = time.time() - start_time
        
        if duration > 1.0:  # Slow request threshold
            logger.warning(f"Slow request detected: {request.path} took {duration:.2f}s")
            record_user_activity('slow_request', user_type)
        
        return response
