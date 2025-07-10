"""
示例：使用Redis缓存优化的API视图
演示如何在AnsFlow中使用新的缓存装饰器
"""

from django.http import JsonResponse
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from utils.cache import api_cache, pipeline_cache, invalidate_pipeline_cache, CacheManager


class PipelineViewSet(ModelViewSet):
    """Pipeline视图集 - 使用缓存优化"""
    
    @api_cache(timeout=600, key_prefix='pipeline_list')  # 10分钟缓存
    def list(self, request):
        """获取Pipeline列表 - 带缓存"""
        pipelines = self.get_queryset()
        serializer = self.get_serializer(pipelines, many=True)
        return Response(serializer.data)
    
    @api_cache(timeout=1800, key_prefix='pipeline_detail')  # 30分钟缓存
    def retrieve(self, request, pk=None):
        """获取Pipeline详情 - 带缓存"""
        pipeline = self.get_object()
        serializer = self.get_serializer(pipeline)
        return Response(serializer.data)
    
    def create(self, request):
        """创建Pipeline - 清除相关缓存"""
        response = super().create(request)
        if response.status_code == 201:
            # 清除列表缓存
            from django.core.cache import caches
            caches['api'].delete_pattern('*pipeline_list*')
        return response
    
    def update(self, request, pk=None):
        """更新Pipeline - 清除相关缓存"""
        response = super().update(request, pk)
        if response.status_code == 200:
            # 清除特定Pipeline的缓存
            invalidate_pipeline_cache(int(pk))
        return response
    
    @pipeline_cache(timeout=3600, key_prefix='pipeline_status')  # 1小时缓存
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """获取Pipeline状态 - 使用pipeline专用缓存"""
        pipeline = self.get_object()
        status_data = {
            'id': pipeline.id,
            'status': pipeline.status,
            'last_run': pipeline.last_run,
            'success_rate': pipeline.calculate_success_rate(),
        }
        return Response(status_data)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行Pipeline - 不缓存，清除状态缓存"""
        pipeline = self.get_object()
        # 执行Pipeline逻辑
        result = pipeline.execute()
        
        # 清除状态相关缓存
        invalidate_pipeline_cache(int(pk))
        
        return Response({'execution_id': result.id})


class ProjectViewSet(ModelViewSet):
    """项目视图集 - 使用缓存优化"""
    
    @api_cache(timeout=300, key_prefix='project_dashboard')  # 5分钟缓存
    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """项目Dashboard - 短时缓存，数据变化频繁"""
        project = self.get_object()
        dashboard_data = {
            'pipelines_count': project.pipelines.count(),
            'executions_today': project.get_executions_today(),
            'success_rate': project.calculate_success_rate(),
            'recent_executions': project.get_recent_executions()[:10],
        }
        return Response(dashboard_data)
    
    @api_cache(timeout=1800, key_prefix='project_analytics', vary_on_params=True)  # 30分钟缓存
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """项目分析数据 - 根据查询参数缓存"""
        project = self.get_object()
        
        # 获取查询参数
        time_range = request.GET.get('time_range', '7d')
        metric_type = request.GET.get('metric', 'executions')
        
        # 根据参数生成分析数据
        analytics_data = project.get_analytics(time_range, metric_type)
        
        return Response(analytics_data)


class SystemAPIView:
    """系统API - 缓存管理"""
    
    @api_cache(timeout=120, key_prefix='system_status')  # 2分钟缓存
    def status(self, request):
        """系统状态 - 短时缓存"""
        from django.db import connection
        from django.core.cache import caches
        
        status_data = {
            'database': self._check_database_connection(),
            'cache': self._check_cache_connection(),
            'celery': self._check_celery_status(),
            'redis': self._check_redis_status(),
        }
        
        return JsonResponse(status_data)
    
    def cache_stats(self, request):
        """缓存统计 - 不缓存，实时数据"""
        stats = CacheManager.get_cache_stats()
        return JsonResponse(stats)
    
    def flush_cache(self, request):
        """清空缓存 - 管理员功能"""
        if not request.user.is_superuser:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        cache_alias = request.POST.get('cache', 'default')
        
        if cache_alias == 'all':
            results = CacheManager.flush_all_caches()
            return JsonResponse({'message': 'All caches flushed', 'results': results})
        else:
            success = CacheManager.flush_cache(cache_alias)
            return JsonResponse({
                'message': f'Cache {cache_alias} flushed',
                'success': success
            })
    
    def _check_database_connection(self):
        """检查数据库连接"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {'status': 'connected'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _check_cache_connection(self):
        """检查缓存连接"""
        try:
            from django.core.cache import caches
            cache = caches['default']
            cache.set('health_check', 'ok', 10)
            result = cache.get('health_check')
            return {'status': 'connected' if result == 'ok' else 'error'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _check_celery_status(self):
        """检查Celery状态"""
        try:
            from ansflow.celery import app
            # 检查Celery worker
            inspect = app.control.inspect()
            stats = inspect.stats()
            return {'status': 'connected' if stats else 'no_workers'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _check_redis_status(self):
        """检查Redis状态"""
        try:
            from django.core.cache import caches
            cache = caches['default']
            if hasattr(cache, '_cache') and hasattr(cache._cache, 'get_client'):
                client = cache._cache.get_client()
                info = client.info()
                return {
                    'status': 'connected',
                    'memory_usage': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                }
            return {'status': 'connected'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
