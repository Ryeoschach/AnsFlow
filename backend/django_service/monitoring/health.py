"""
Health check views with monitoring integration for Django service.
"""

from django.http import JsonResponse
from django.views import View
from django.db import connections
from django.core.cache import cache
from django.conf import settings
import time
import logging
from .prometheus import (
    record_user_activity,
    record_cache_operation,
    DjangoMetricsCollector
)

logger = logging.getLogger(__name__)


class HealthCheckView(View):
    """Enhanced health check with monitoring metrics."""
    
    def get(self, request):
        """Perform comprehensive health check."""
        start_time = time.time()
        health_status = {
            'status': 'healthy',
            'service': 'AnsFlow Django Service',
            'version': '1.0.0',
            'timestamp': int(time.time()),
            'checks': {}
        }
        
        overall_healthy = True
        
        # Database connectivity check
        try:
            self._check_database()
            health_status['checks']['database'] = {'status': 'healthy'}
        except Exception as e:
            health_status['checks']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_healthy = False
        
        # Cache connectivity check
        try:
            self._check_cache()
            health_status['checks']['cache'] = {'status': 'healthy'}
        except Exception as e:
            health_status['checks']['cache'] = {
                'status': 'unhealthy', 
                'error': str(e)
            }
            overall_healthy = False
        
        # Memory check
        try:
            memory_usage = self._check_memory()
            health_status['checks']['memory'] = {
                'status': 'healthy' if memory_usage < 80 else 'warning',
                'usage_percent': memory_usage
            }
        except Exception as e:
            health_status['checks']['memory'] = {
                'status': 'unknown',
                'error': str(e)
            }
        
        # Disk check
        try:
            disk_usage = self._check_disk()
            health_status['checks']['disk'] = {
                'status': 'healthy' if disk_usage < 80 else 'warning',
                'usage_percent': disk_usage
            }
        except Exception as e:
            health_status['checks']['disk'] = {
                'status': 'unknown',
                'error': str(e)
            }
        
        # Overall status
        if not overall_healthy:
            health_status['status'] = 'unhealthy'
        
        # Record health check metrics
        check_duration = time.time() - start_time
        health_status['response_time_ms'] = round(check_duration * 1000, 2)
        
        # Record activity
        record_user_activity('health_check', 'system')
        
        # Return response with appropriate status code
        status_code = 200 if overall_healthy else 503
        return JsonResponse(health_status, status=status_code)
    
    def _check_database(self):
        """Check database connectivity."""
        for alias in connections:
            connection = connections[alias]
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
    
    def _check_cache(self):
        """Check cache connectivity."""
        test_key = 'health_check_test'
        test_value = str(time.time())
        
        # Test cache write
        cache.set(test_key, test_value, timeout=10)
        record_cache_operation('set')
        
        # Test cache read
        cached_value = cache.get(test_key)
        record_cache_operation('get')
        
        if cached_value != test_value:
            raise Exception("Cache read/write test failed")
        
        # Cleanup
        cache.delete(test_key)
        record_cache_operation('delete')
    
    def _check_memory(self):
        """Check memory usage."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return memory.percent
        except ImportError:
            logger.warning("psutil not available for memory check")
            return 0
    
    def _check_disk(self):
        """Check disk usage."""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return (disk.used / disk.total) * 100
        except ImportError:
            logger.warning("psutil not available for disk check")
            return 0


class DetailedHealthView(View):
    """Detailed health check with system metrics."""
    
    def get(self, request):
        """Return detailed health information."""
        collector = DjangoMetricsCollector()
        
        health_data = {
            'service': 'AnsFlow Django Service',
            'status': 'healthy',
            'version': '1.0.0',
            'timestamp': int(time.time()),
            'system': {},
            'application': {},
            'database': {},
            'cache': {}
        }
        
        # System metrics
        try:
            import psutil
            
            # CPU info
            health_data['system']['cpu'] = {
                'usage_percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'load_average': list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
            }
            
            # Memory info
            memory = psutil.virtual_memory()
            health_data['system']['memory'] = {
                'total_mb': round(memory.total / 1024 / 1024),
                'available_mb': round(memory.available / 1024 / 1024),
                'used_mb': round(memory.used / 1024 / 1024),
                'usage_percent': memory.percent
            }
            
            # Disk info
            disk = psutil.disk_usage('/')
            health_data['system']['disk'] = {
                'total_gb': round(disk.total / 1024 / 1024 / 1024),
                'used_gb': round(disk.used / 1024 / 1024 / 1024),
                'free_gb': round(disk.free / 1024 / 1024 / 1024),
                'usage_percent': round((disk.used / disk.total) * 100, 2)
            }
            
        except ImportError:
            health_data['system']['error'] = 'psutil not available'
        
        # Application metrics
        try:
            collector.collect_session_metrics()
            collector.collect_business_metrics()
            
            health_data['application'] = {
                'active_sessions': 'collected',
                'active_projects': 'collected',
                'django_apps': len(settings.INSTALLED_APPS) if hasattr(settings, 'INSTALLED_APPS') else 0
            }
        except Exception as e:
            health_data['application']['error'] = str(e)
        
        # Database status
        try:
            for alias in connections:
                connection = connections[alias]
                with connection.cursor() as cursor:
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()[0] if cursor.rowcount > 0 else "Unknown"
                    
                health_data['database'][alias] = {
                    'status': 'connected',
                    'version': version
                }
        except Exception as e:
            health_data['database']['error'] = str(e)
        
        # Cache status
        try:
            cache.get('non_existent_key')  # Test cache connection
            health_data['cache'] = {
                'status': 'connected',
                'backend': str(type(cache))
            }
        except Exception as e:
            health_data['cache'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return JsonResponse(health_data)
