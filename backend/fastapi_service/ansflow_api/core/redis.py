"""
Redis连接和缓存管理模块 - AnsFlow FastAPI服务
提供异步Redis客户端和缓存功能（简化版本）
"""

import json
import asyncio
from typing import Any, Optional, Dict, List, Union
from datetime import timedelta
import logging  # 使用标准logging替代structlog
from contextlib import asynccontextmanager

# 暂时注释掉aioredis导入，使用模拟实现
# import aioredis
# from aioredis import Redis

try:
    from ..config.settings import settings
except ImportError:
    # 如果settings模块不存在，使用默认值
    class MockSettings:
        class redis:
            default_url = "redis://localhost:6379/1"
            api_url = "redis://localhost:6379/4"
            pipeline_url = "redis://localhost:6379/5"
            session_url = "redis://localhost:6379/3"
    settings = MockSettings()

logger = logging.getLogger(__name__)


class MockRedisClient:
    """模拟Redis客户端（用于开发阶段）"""
    
    def __init__(self):
        self._storage = {}
    
    async def get(self, key: str):
        return self._storage.get(key)
    
    async def set(self, key: str, value: Any):
        self._storage[key] = value
        return True
    
    async def setex(self, key: str, ttl: int, value: Any):
        self._storage[key] = value
        # 简化实现：不处理TTL
        return True
    
    async def delete(self, *keys):
        deleted = 0
        for key in keys:
            if key in self._storage:
                del self._storage[key]
                deleted += 1
        return deleted
    
    async def exists(self, key: str):
        return 1 if key in self._storage else 0
    
    async def keys(self, pattern: str):
        # 简化模式匹配
        if pattern.endswith('*'):
            prefix = pattern[:-1]
            return [k for k in self._storage.keys() if k.startswith(prefix)]
        return [k for k in self._storage.keys() if k == pattern]
    
    async def incrby(self, key: str, amount: int):
        current = self._storage.get(key, 0)
        if isinstance(current, (int, str)):
            try:
                new_value = int(current) + amount
                self._storage[key] = new_value
                return new_value
            except ValueError:
                pass
        return 0
    
    async def expire(self, key: str, ttl: int):
        # 简化实现：不处理TTL
        return True if key in self._storage else False
    
    async def ttl(self, key: str):
        return 300 if key in self._storage else -1
    
    async def info(self):
        return {
            'keyspace_hits': 100,
            'keyspace_misses': 20,
            'used_memory_human': '1MB',
            'connected_clients': 1,
            'total_commands_processed': 1000
        }
    
    async def close(self):
        pass


class AsyncRedisManager:
    """异步Redis管理器（使用模拟客户端）"""
    
    def __init__(self):
        self._default_pool: Optional[MockRedisClient] = None
        self._api_pool: Optional[MockRedisClient] = None
        self._pipeline_pool: Optional[MockRedisClient] = None
        self._session_pool: Optional[MockRedisClient] = None
        
    async def initialize(self):
        """初始化Redis连接池"""
        try:
            # 使用模拟客户端
            self._default_pool = MockRedisClient()
            self._api_pool = MockRedisClient()
            self._pipeline_pool = MockRedisClient()
            self._session_pool = MockRedisClient()
            
            logger.info("Mock Redis connections initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Redis connections", error=str(e))
            raise
    
    async def close(self):
        """关闭所有Redis连接"""
        pools = [self._default_pool, self._api_pool, self._pipeline_pool, self._session_pool]
        for pool in pools:
            if pool:
                await pool.close()
        logger.info("Redis connections closed")
    
    @property
    def default(self) -> MockRedisClient:
        if not self._default_pool:
            raise RuntimeError("Redis default pool not initialized")
        return self._default_pool
    
    @property
    def api(self) -> MockRedisClient:
        if not self._api_pool:
            raise RuntimeError("Redis API pool not initialized")
        return self._api_pool
    
    @property
    def pipeline(self) -> MockRedisClient:
        if not self._pipeline_pool:
            raise RuntimeError("Redis pipeline pool not initialized")
        return self._pipeline_pool
    
    @property
    def session(self) -> MockRedisClient:
        if not self._session_pool:
            raise RuntimeError("Redis session pool not initialized")
        return self._session_pool


class AsyncCacheService:
    """异步缓存服务"""
    
    def __init__(self, redis_manager: AsyncRedisManager):
        self.redis = redis_manager
    
    async def get(
        self, 
        key: str, 
        cache_type: str = 'api',
        default: Any = None
    ) -> Any:
        """
        获取缓存值
        :param key: 缓存键
        :param cache_type: 缓存类型 (api, pipeline, session, default)
        :param default: 默认值
        """
        try:
            client = getattr(self.redis, cache_type)
            value = await client.get(key)
            
            if value is None:
                return default
            
            # 尝试解析JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.warning("Cache get error", key=key, error=str(e))
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        cache_type: str = 'api'
    ) -> bool:
        """
        设置缓存值
        :param key: 缓存键
        :param value: 缓存值
        :param ttl: 过期时间（秒）
        :param cache_type: 缓存类型
        """
        try:
            client = getattr(self.redis, cache_type)
            
            # 序列化值
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            if ttl:
                await client.setex(key, ttl, value)
            else:
                await client.set(key, value)
            
            return True
            
        except Exception as e:
            logger.error("Cache set error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str, cache_type: str = 'api') -> bool:
        """删除缓存"""
        try:
            client = getattr(self.redis, cache_type)
            result = await client.delete(key)
            return result > 0
        except Exception as e:
            logger.error("Cache delete error", key=key, error=str(e))
            return False
    
    async def exists(self, key: str, cache_type: str = 'api') -> bool:
        """检查缓存是否存在"""
        try:
            client = getattr(self.redis, cache_type)
            result = await client.exists(key)
            return result > 0
        except Exception as e:
            logger.error("Cache exists error", key=key, error=str(e))
            return False
    
    async def get_pattern(
        self, 
        pattern: str, 
        cache_type: str = 'api'
    ) -> List[str]:
        """获取匹配模式的所有键"""
        try:
            client = getattr(self.redis, cache_type)
            keys = await client.keys(pattern)
            return keys
        except Exception as e:
            logger.error("Cache get_pattern error", pattern=pattern, error=str(e))
            return []
    
    async def delete_pattern(
        self, 
        pattern: str, 
        cache_type: str = 'api'
    ) -> int:
        """删除匹配模式的所有键"""
        try:
            keys = await self.get_pattern(pattern, cache_type)
            if keys:
                client = getattr(self.redis, cache_type)
                result = await client.delete(*keys)
                return result
            return 0
        except Exception as e:
            logger.error("Cache delete_pattern error", pattern=pattern, error=str(e))
            return 0
    
    async def increment(
        self, 
        key: str, 
        amount: int = 1,
        cache_type: str = 'api'
    ) -> int:
        """递增计数器"""
        try:
            client = getattr(self.redis, cache_type)
            result = await client.incrby(key, amount)
            return result
        except Exception as e:
            logger.error("Cache increment error", key=key, error=str(e))
            return 0
    
    async def expire(
        self, 
        key: str, 
        ttl: int,
        cache_type: str = 'api'
    ) -> bool:
        """设置键过期时间"""
        try:
            client = getattr(self.redis, cache_type)
            result = await client.expire(key, ttl)
            return result
        except Exception as e:
            logger.error("Cache expire error", key=key, error=str(e))
            return False
    
    async def get_ttl(self, key: str, cache_type: str = 'api') -> int:
        """获取键的剩余过期时间"""
        try:
            client = getattr(self.redis, cache_type)
            ttl = await client.ttl(key)
            return ttl
        except Exception as e:
            logger.error("Cache get_ttl error", key=key, error=str(e))
            return -1
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {}
        cache_types = ['default', 'api', 'pipeline', 'session']
        
        for cache_type in cache_types:
            try:
                client = getattr(self.redis, cache_type)
                info = await client.info()
                stats[cache_type] = {
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'used_memory_human': info.get('used_memory_human', 'Unknown'),
                    'connected_clients': info.get('connected_clients', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0),
                }
                
                # 计算命中率
                hits = stats[cache_type]['keyspace_hits']
                misses = stats[cache_type]['keyspace_misses']
                total = hits + misses
                stats[cache_type]['hit_rate'] = hits / total if total > 0 else 0
                
            except Exception as e:
                stats[cache_type] = {'error': str(e)}
        
        return stats


# 缓存装饰器
def async_cache(
    ttl: int = 300,  # 5分钟默认TTL
    key_prefix: str = "fastapi",
    cache_type: str = "api",
    vary_on_user: bool = True
):
    """
    异步缓存装饰器
    :param ttl: 缓存时间（秒）
    :param key_prefix: 缓存键前缀
    :param cache_type: 缓存类型
    :param vary_on_user: 是否根据用户区分缓存
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_service = kwargs.get('cache_service')
            if not cache_service:
                return await func(*args, **kwargs)
            
            # 构建缓存键
            cache_key_parts = [key_prefix, func.__name__]
            
            # 添加函数参数到缓存键
            if args:
                cache_key_parts.extend([str(arg) for arg in args])
            if kwargs:
                # 排除服务依赖参数
                filtered_kwargs = {k: v for k, v in kwargs.items() 
                                 if not k.endswith('_service') and not k.endswith('_manager')}
                if filtered_kwargs:
                    cache_key_parts.append(f"kwargs_{hash(tuple(sorted(filtered_kwargs.items())))}")
            
            cache_key = ":".join(cache_key_parts)
            
            # 尝试获取缓存
            cached_result = await cache_service.get(cache_key, cache_type)
            if cached_result is not None:
                logger.debug("Cache hit", key=cache_key)
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            await cache_service.set(cache_key, result, ttl, cache_type)
            logger.debug("Cache set", key=cache_key, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


# 全局Redis管理器实例
redis_manager = AsyncRedisManager()
cache_service = AsyncCacheService(redis_manager)
