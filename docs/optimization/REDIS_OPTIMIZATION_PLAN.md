# Redis 缓存优化方案

## 当前Redis使用情况
- Database 0: Celery Broker & Results
- Database 1: Django Cache (少量使用)

## 优化后的Redis数据库分配

```python
# 在 settings/base.py 中优化Redis配置
REDIS_DATABASES = {
    'celery': 0,           # Celery任务队列
    'cache': 1,            # Django应用缓存
    'sessions': 2,         # 用户会话
    'realtime': 3,         # 实时数据缓存
    'api_cache': 4,        # API响应缓存
    'temp_data': 5,        # 临时数据存储
}

# 更新缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'ansflow_cache',
        'TIMEOUT': 300,  # 5分钟默认超时
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'ansflow_session',
        'TIMEOUT': 86400,  # 24小时
    },
    'api_responses': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/4',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'ansflow_api',
        'TIMEOUT': 600,  # 10分钟
    },
    'realtime': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/3',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'ansflow_rt',
        'TIMEOUT': 60,  # 1分钟，实时数据
    }
}
```

## 应该缓存的数据类型

### 1. API响应缓存
- 用户权限信息
- API端点列表
- 系统配置信息
- 流水线模板数据

### 2. 实时数据缓存
- 流水线执行状态
- 系统监控指标
- 在线用户列表
- WebSocket连接状态

### 3. 会话和认证缓存
- 用户认证状态
- JWT Token黑名单
- 用户偏好设置
- 最近访问记录

### 4. 计算结果缓存
- 复杂查询结果
- 统计报表数据
- 系统健康检查结果
- API测试结果

## 缓存实现示例

```python
# 在views中使用缓存
from django.core.cache import caches

class APIEndpointViewSet(viewsets.ModelViewSet):
    def list(self, request):
        cache = caches['api_responses']
        cache_key = f"api_endpoints_list_{request.user.id}"
        
        result = cache.get(cache_key)
        if result is None:
            # 计算数据
            result = self.get_serializer(self.get_queryset(), many=True).data
            cache.set(cache_key, result, timeout=300)  # 5分钟缓存
        
        return Response(result)
```
