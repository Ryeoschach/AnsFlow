# RabbitMQ 异步任务优化方案

## 当前问题
- Celery使用Redis作为Broker
- RabbitMQ闲置，资源浪费
- 缺少任务优先级和路由

## 优化后的消息队列架构

### 1. Celery迁移到RabbitMQ
```python
# settings/base.py 中的Celery配置更新
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='amqp://ansflow:ansflow_rabbitmq_123@localhost:5672//')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')

# 使用RabbitMQ作为Broker，Redis作为结果存储
# 这样可以获得RabbitMQ的高级路由功能和Redis的快速结果查询
```

### 2. 任务队列分类
```python
# celery.py 中的队列配置
from kombu import Queue, Exchange

app.conf.task_routes = {
    # 高优先级任务队列
    'cicd_integrations.tasks.execute_pipeline_async': {'queue': 'pipeline_execution'},
    'kubernetes_integration.tasks.deploy_application': {'queue': 'deployment'},
    'ansible_integration.tasks.run_playbook': {'queue': 'configuration'},
    
    # 普通优先级任务队列
    'cicd_integrations.tasks.health_check_tools': {'queue': 'monitoring'},
    'settings_management.tasks.backup_data': {'queue': 'maintenance'},
    
    # 低优先级任务队列
    'cicd_integrations.tasks.cleanup_old_executions': {'queue': 'cleanup'},
    'audit.tasks.cleanup_old_logs': {'queue': 'cleanup'},
}

app.conf.task_default_queue = 'default'
app.conf.task_queues = (
    # 高优先级队列
    Queue('pipeline_execution', Exchange('pipeline'), routing_key='pipeline.execution', priority=10),
    Queue('deployment', Exchange('ops'), routing_key='ops.deploy', priority=9),
    Queue('configuration', Exchange('ops'), routing_key='ops.config', priority=8),
    
    # 普通优先级队列
    Queue('monitoring', Exchange('system'), routing_key='system.monitor', priority=5),
    Queue('maintenance', Exchange('system'), routing_key='system.maintenance', priority=5),
    
    # 低优先级队列
    Queue('cleanup', Exchange('system'), routing_key='system.cleanup', priority=1),
    Queue('default', Exchange('default'), routing_key='default', priority=3),
)
```

### 3. 任务分类和优先级

#### 高优先级任务 (RabbitMQ)
- 流水线执行任务
- 实时部署任务
- 紧急通知任务
- 用户交互响应任务

#### 中等优先级任务 (RabbitMQ)
- 定时监控检查
- 数据备份任务
- 报告生成任务
- 系统维护任务

#### 低优先级任务 (RabbitMQ)
- 日志清理任务
- 历史数据归档
- 统计分析任务
- 缓存预热任务

### 4. 消息持久化和可靠性
```python
# Celery配置增强
app.conf.update(
    # 消息持久化
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # 任务确认和重试
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # 结果存储
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    },
    
    # 路由配置
    task_routes={
        'critical.*': {'queue': 'critical'},
        'normal.*': {'queue': 'normal'},
        'low.*': {'queue': 'low'},
    }
)
```

## 优势分析

### RabbitMQ优势
1. **高级路由** - 支持复杂的消息路由和交换机
2. **任务优先级** - 原生支持任务优先级队列
3. **消息持久化** - 可靠的消息存储和恢复
4. **监控管理** - 丰富的管理界面和监控指标
5. **集群支持** - 更好的高可用性支持

### Redis优势
1. **快速存储** - 结果存储和临时数据
2. **数据结构** - 丰富的数据结构支持
3. **过期机制** - 自动数据清理
4. **原子操作** - 支持复杂的原子操作

## 迁移步骤

### 第一步：配置更新
1. 更新Celery Broker配置
2. 设置RabbitMQ队列和交换机
3. 配置任务路由规则

### 第二步：逐步迁移
1. 先迁移非关键任务
2. 监控任务执行情况
3. 逐步迁移关键任务

### 第三步：优化调整
1. 根据监控数据调整队列优先级
2. 优化worker数量配置
3. 调整任务重试策略
