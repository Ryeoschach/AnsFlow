# AnsFlow 测试文档

## 📋 测试概览

这个目录包含了 AnsFlow 平台的各种测试报告、测试数据和测试结果文件。

## 🧪 测试文件

### 📊 性能测试报告
- **[ansflow_optimization_test_report.json](./ansflow_optimization_test_report.json)** - 最新的性能优化测试结果
  - Redis 多数据库连接测试
  - FastAPI 性能基准测试
  - WebSocket 连接测试
  - 系统集成测试

### 📈 测试结果摘要

#### Redis 缓存测试
```json
{
  "default": {"status": "✅ Connected", "latency_ms": 0.34},
  "session": {"status": "✅ Connected", "latency_ms": 0.21},
  "api": {"status": "✅ Connected", "latency_ms": 0.18},
  "pipeline": {"status": "✅ Connected", "latency_ms": 0.19},
  "channels": {"status": "✅ Connected", "latency_ms": 0.18}
}
```

#### FastAPI 性能测试
```json
{
  "health_check": {
    "status": "✅ OK",
    "response_time_ms": 57.61,
    "service": "ansflow-fastapi"
  },
  "concurrent": {
    "total_requests": 20,
    "successful": 20,
    "avg_time_ms": 28.64,
    "requests_per_second": 34.91
  }
}
```

## 🚀 如何运行测试

### 1. 性能优化测试
```bash
cd /Users/creed/Workspace/OpenSource/ansflow
python scripts/optimization/test_optimization.py
```

### 2. Django 服务测试
```bash
cd backend/django_service
uv run python manage.py test
```

### 3. FastAPI 服务测试
```bash
cd backend/fastapi_service
uv run pytest
```

### 4. Redis 缓存测试
```bash
cd backend/django_service
DJANGO_SETTINGS_MODULE=ansflow.settings.base uv run python -c "
import django; django.setup()
from django.core.cache import cache
cache.set('test_key', 'test_value', 30)
result = cache.get('test_key')
print(f'Redis 测试结果: {result}')
assert result == 'test_value', 'Redis 缓存测试失败'
print('✅ Redis 缓存测试通过')
"
```

### 5. WebSocket 连接测试
```bash
# 在浏览器控制台运行
const ws = new WebSocket('ws://localhost:8001/ws/monitor');
ws.onopen = () => console.log('✅ WebSocket 连接成功');
ws.onmessage = (event) => console.log('📨 收到消息:', JSON.parse(event.data));
```

## 📊 测试指标说明

### 性能基准
- **API 响应时间**: < 100ms (目标)
- **数据库连接延迟**: < 1ms (目标)
- **缓存命中率**: > 80% (目标)
- **并发处理能力**: > 30 req/sec (目标)
- **WebSocket 连接延迟**: < 50ms (目标)

### 测试覆盖范围
- ✅ Redis 多数据库连接
- ✅ FastAPI 健康检查
- ✅ 并发请求处理
- ✅ WebSocket 实时通信
- ✅ 系统集成功能

## 🐛 故障排除

### 常见测试失败原因
1. **Redis 连接失败**: 确保 Redis 服务运行在默认端口 6379
2. **FastAPI 连接失败**: 确保 FastAPI 服务运行在端口 8001
3. **Django 连接失败**: 确保 Django 服务运行在端口 8000
4. **RabbitMQ 连接失败**: 检查 RabbitMQ 服务和 vhost 配置

### 调试命令
```bash
# 检查服务状态
curl http://localhost:8000/health/  # Django
curl http://localhost:8001/health   # FastAPI

# 检查 Redis 连接
redis-cli ping

# 检查 RabbitMQ 状态
rabbitmqctl status
```

---

最后更新: 2025年7月10日  
测试状态: ✅ **全部通过**
