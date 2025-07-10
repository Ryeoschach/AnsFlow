"""
Redis缓存工具模块 - AnsFlow微服务优化
提供API缓存装饰器和缓存管理功能
"""

import hashlib
import json
from functools import wraps
from typing import Any, Optional, Callable, Union
from django.core.cache import caches
from django.http import JsonResponse
from rest_framework.response import Response
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    生成缓存键
    :param prefix: 缓存键前缀
    :param args: 位置参数
    :param kwargs: 关键字参数
    :return: 生成的缓存键
    """
    # 创建参数的哈希值
    params_str = json.dumps([args, sorted(kwargs.items())], sort_keys=True, default=str)
    hash_value = hashlib.md5(params_str.encode()).hexdigest()[:12]
    return f"{prefix}:{hash_value}"


def api_cache(
    cache_alias: str = 'api',
    timeout: Optional[int] = None,
    key_prefix: str = 'api_view',
    vary_on_user: bool = True,
    vary_on_params: bool = True
):
    """
    API缓存装饰器
    :param cache_alias: 缓存别名（default, api, pipeline等）
    :param timeout: 缓存超时时间（秒），None使用默认值
    :param key_prefix: 缓存键前缀
    :param vary_on_user: 是否根据用户区分缓存
    :param vary_on_params: 是否根据请求参数区分缓存
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # 获取缓存实例
            cache = caches[cache_alias]
            
            # 构建缓存键
            cache_key_parts = [key_prefix, func.__name__]
            
            if vary_on_user and hasattr(request, 'user') and request.user.is_authenticated:
                cache_key_parts.append(f"user_{request.user.id}")
            
            if vary_on_params:
                # 包含URL参数
                if args:
                    cache_key_parts.extend([str(arg) for arg in args])
                
                # 包含查询参数
                if request.method == 'GET' and request.GET:
                    query_params = sorted(request.GET.items())
                    cache_key_parts.append(f"query_{hashlib.md5(str(query_params).encode()).hexdigest()[:8]}")
                
                # 包含POST数据
                elif request.method == 'POST' and hasattr(request, 'data'):
                    post_data = getattr(request, 'data', {})
                    if post_data:
                        cache_key_parts.append(f"post_{hashlib.md5(str(sorted(post_data.items())).encode()).hexdigest()[:8]}")
            
            cache_key = ':'.join(cache_key_parts)
            
            # 尝试从缓存获取
            try:
                cached_response = cache.get(cache_key)
                if cached_response is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    if isinstance(cached_response, dict):
                        return Response(cached_response)
                    return cached_response
            except Exception as e:
                logger.warning(f"Cache get error for key {cache_key}: {e}")
            
            # 缓存未命中，执行原函数
            response = func(self, request, *args, **kwargs)
            
            # 缓存响应
            try:
                if isinstance(response, Response) and response.status_code == 200:
                    cache_timeout = timeout or cache.default_timeout or 300
                    cache.set(cache_key, response.data, timeout=cache_timeout)
                    logger.debug(f"Cached response for key: {cache_key}, timeout: {cache_timeout}")
                elif isinstance(response, JsonResponse) and response.status_code == 200:
                    cache_timeout = timeout or cache.default_timeout or 300
                    cache.set(cache_key, json.loads(response.content), timeout=cache_timeout)
                    logger.debug(f"Cached JSON response for key: {cache_key}, timeout: {cache_timeout}")
            except Exception as e:
                logger.warning(f"Cache set error for key {cache_key}: {e}")
            
            return response
        
        return wrapper
    return decorator


def pipeline_cache(timeout: int = 1800, key_prefix: str = 'pipeline'):
    """
    Pipeline特定的缓存装饰器
    :param timeout: 缓存超时时间，默认30分钟
    :param key_prefix: 缓存键前缀
    """
    return api_cache(
        cache_alias='pipeline',
        timeout=timeout,
        key_prefix=key_prefix,
        vary_on_user=True,
        vary_on_params=True
    )


def invalidate_cache_pattern(pattern: str, cache_alias: str = 'default'):
    """
    按模式删除缓存
    :param pattern: 缓存键模式，支持通配符
    :param cache_alias: 缓存别名
    """
    try:
        cache = caches[cache_alias]
        if hasattr(cache, 'delete_pattern'):
            deleted_count = cache.delete_pattern(pattern)
            logger.info(f"Invalidated {deleted_count} cache entries matching pattern: {pattern}")
            return deleted_count
        else:
            logger.warning(f"Cache backend does not support pattern deletion")
            return 0
    except Exception as e:
        logger.error(f"Error invalidating cache pattern {pattern}: {e}")
        return 0


def invalidate_user_cache(user_id: int, cache_alias: str = 'api'):
    """
    删除特定用户的缓存
    :param user_id: 用户ID
    :param cache_alias: 缓存别名
    """
    pattern = f"*user_{user_id}*"
    return invalidate_cache_pattern(pattern, cache_alias)


def invalidate_pipeline_cache(pipeline_id: int):
    """
    删除特定Pipeline的缓存
    :param pipeline_id: Pipeline ID
    """
    pattern = f"*pipeline*{pipeline_id}*"
    invalidate_cache_pattern(pattern, 'pipeline')
    invalidate_cache_pattern(pattern, 'api')


class CacheManager:
    """缓存管理器"""
    
    @staticmethod
    def get_cache_stats():
        """获取所有缓存的统计信息"""
        stats = {}
        for cache_name in ['default', 'session', 'api', 'pipeline']:
            try:
                cache = caches[cache_name]
                # 尝试获取Redis统计信息
                if hasattr(cache, '_cache') and hasattr(cache._cache, 'get_client'):
                    client = cache._cache.get_client()
                    info = client.info()
                    stats[cache_name] = {
                        'keyspace_hits': info.get('keyspace_hits', 0),
                        'keyspace_misses': info.get('keyspace_misses', 0),
                        'used_memory': info.get('used_memory_human', 'Unknown'),
                        'connected_clients': info.get('connected_clients', 0),
                    }
                else:
                    stats[cache_name] = {'status': 'available'}
            except Exception as e:
                stats[cache_name] = {'error': str(e)}
        
        return stats
    
    @staticmethod
    def flush_cache(cache_alias: str = 'default'):
        """清空指定缓存"""
        try:
            cache = caches[cache_alias]
            cache.clear()
            logger.info(f"Flushed cache: {cache_alias}")
            return True
        except Exception as e:
            logger.error(f"Error flushing cache {cache_alias}: {e}")
            return False
    
    @staticmethod
    def flush_all_caches():
        """清空所有缓存"""
        results = {}
        for cache_name in ['default', 'session', 'api', 'pipeline']:
            results[cache_name] = CacheManager.flush_cache(cache_name)
        return results


# 常用缓存装饰器快捷方式
short_cache = lambda func: api_cache(timeout=300)(func)  # 5分钟
medium_cache = lambda func: api_cache(timeout=1800)(func)  # 30分钟
long_cache = lambda func: api_cache(timeout=3600)(func)  # 1小时
