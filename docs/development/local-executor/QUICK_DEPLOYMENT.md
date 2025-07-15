# 本地执行器快速部署指南

## 概述

这是 AnsFlow 本地执行器工具的快速部署指南，包含所有必需的步骤来部署和激活本地执行器功能。

## 快速步骤

### 1. 数据库更新（必需）

```bash
# 进入后端目录
cd backend/django_service

# 运行数据库迁移
python manage.py migrate

# 验证迁移成功
python manage.py showmigrations cicd_integrations
```

### 2. 创建本地执行器（必需）

```bash
# 运行管理命令
python manage.py setup_local_executor

# 预期输出：
# 正在创建本地执行器工具...
# 本地执行器工具创建成功！
```

### 3. 重启服务（必需）

```bash
# 重启后端服务
# 根据你的部署方式选择：

# 开发环境
python manage.py runserver

# 生产环境（例如 gunicorn）
sudo systemctl restart ansflow-backend

# 或使用 PM2
pm2 restart ansflow-backend
```

### 4. 前端部署（必需）

```bash
# 进入前端目录
cd frontend

# 构建生产版本
npm run build

# 部署到服务器
# 根据你的部署方式选择合适的命令
```

## 验证部署

### 1. 后端验证

```bash
# 检查本地执行器是否创建成功
python manage.py shell

# 在 shell 中运行：
>>> from cicd_integrations.models import CICDTool
>>> local_tool = CICDTool.objects.filter(tool_type='local').first()
>>> print(f"本地执行器: {local_tool.name}, 状态: {local_tool.status}")
>>> exit()
```

### 2. 前端验证

1. 打开浏览器访问 AnsFlow 前端
2. 进入流水线页面
3. 创建新流水线
4. 在 CI/CD 工具选择中应该看到"Local Executor"选项
5. 选择"Local Executor"应该显示为已认证状态

### 3. 功能验证

```bash
# 运行快速测试
cd tests/scripts/local-executor
python test_local_executor_simple.py

# 预期输出应该显示测试通过
```

## 故障排除

### 问题1：迁移失败

```bash
# 检查迁移状态
python manage.py showmigrations cicd_integrations

# 如果有未应用的迁移，手动应用
python manage.py migrate cicd_integrations

# 检查数据库连接
python manage.py dbshell
```

### 问题2：本地执行器创建失败

```bash
# 检查错误日志
python manage.py setup_local_executor --verbosity=2

# 手动检查数据库
python manage.py shell
>>> from cicd_integrations.models import CICDTool
>>> CICDTool.objects.filter(tool_type='local').count()
```

### 问题3：前端显示问题

1. 检查浏览器控制台是否有错误
2. 清除浏览器缓存
3. 检查网络请求是否正常
4. 验证后端 API 响应

### 问题4：执行失败

```bash
# 检查执行日志
cd tests/utils
python view_execution_logs.py

# 检查系统日志
tail -f /var/log/ansflow/backend.log
```

## 生产环境配置

### 1. 环境变量

```bash
# 确保以下环境变量已设置
export DJANGO_SETTINGS_MODULE=ansflow.settings.production
export DATABASE_URL=postgresql://...
export SECRET_KEY=your-secret-key
```

### 2. 权限设置

```bash
# 确保应用有足够的权限执行命令
# 但不要给予过多权限
chown -R ansflow:ansflow /path/to/ansflow
chmod 755 /path/to/ansflow
```

### 3. 日志配置

```python
# 在 settings.py 中配置日志
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/ansflow/backend.log',
        },
    },
    'loggers': {
        'cicd_integrations': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 性能优化

### 1. 数据库索引

```sql
-- 为新字段创建索引
CREATE INDEX idx_stepexecution_pipeline_step_id 
ON cicd_integrations_stepexecution(pipeline_step_id);

-- 为常用查询创建复合索引
CREATE INDEX idx_stepexecution_status_created 
ON cicd_integrations_stepexecution(status, created_at);
```

### 2. 缓存设置

```python
# 在 settings.py 中配置 Redis 缓存
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## 监控设置

### 1. 健康检查

```python
# 创建健康检查端点
# 在 views.py 中添加：
def health_check(request):
    try:
        local_tool = CICDTool.objects.filter(tool_type='local').first()
        return JsonResponse({
            'status': 'healthy',
            'local_executor': bool(local_tool),
            'database': 'connected'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)
```

### 2. 日志监控

```bash
# 使用 logrotate 管理日志
sudo vim /etc/logrotate.d/ansflow

# 内容：
/var/log/ansflow/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 ansflow ansflow
}
```

## 备份策略

### 1. 数据库备份

```bash
# 创建备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump ansflow > /backups/ansflow_$DATE.sql
```

### 2. 代码备份

```bash
# 创建代码快照
git tag -a v1.0-local-executor -m "Local executor implementation"
git push origin v1.0-local-executor
```

## 支持联系

如果在部署过程中遇到问题，请：

1. 检查本文档的故障排除部分
2. 运行测试脚本验证功能
3. 查看系统日志获取详细错误信息
4. 联系技术支持团队

---

**部署指南版本**: v1.0  
**创建日期**: 2025年7月15日  
**适用版本**: AnsFlow v1.0.0  
**维护者**: 开发团队
