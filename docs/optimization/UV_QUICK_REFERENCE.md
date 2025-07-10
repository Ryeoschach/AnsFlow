# AnsFlow UV 快速参考指南

## 🚀 快速开始

### 一键环境设置
```bash
cd /Users/creed/Workspace/OpenSource/ansflow
./uv-setup.sh  # 设置所有服务环境
```

### 激活服务环境
```bash
# Django 服务
cd backend/django_service
source .venv/bin/activate  # 或直接使用 uv run

# FastAPI 服务  
cd backend/fastapi_service
source .venv/bin/activate  # 或直接使用 uv run
```

## 📦 依赖管理

### 安装新包
```bash
# 生产依赖
uv add redis
uv add fastapi
uv add celery

# 开发依赖
uv add --dev pytest
uv add --dev black
uv add --dev mypy

# 特定版本
uv add "django>=4.2,<5.0"
```

### 同步和更新
```bash
uv sync                 # 同步锁定的依赖
uv sync --upgrade       # 更新所有依赖到最新版本
uv sync --dev           # 包含开发依赖
```

### 查看依赖
```bash
uv tree                 # 显示依赖树
uv list                 # 列出所有包
uv list --outdated      # 显示过期包
```

## 🔧 运行命令

### 推荐使用 uv run (无需激活虚拟环境)
```bash
# Django 服务
cd backend/django_service
uv run python manage.py runserver
uv run python manage.py migrate  
uv run python manage.py test
uv run python manage.py shell

# FastAPI 服务
cd backend/fastapi_service  
uv run uvicorn main:app --reload
uv run pytest
uv run python -m ansflow_api.main
```

### 性能测试和优化
```bash
# 运行完整的优化测试
cd /Users/creed/Workspace/OpenSource/ansflow
uv run python test_optimization.py

# Django 健康检查
cd backend/django_service
uv run python manage.py check

# 缓存功能测试
uv run python manage.py shell -c "
from django.core.cache import cache
cache.set('test', 'works', 30)
print('缓存测试:', cache.get('test'))
"
```

## 🐛 故障排除

### 常见问题解决
```bash
# 依赖冲突
uv lock --resolution lowest   # 使用最低兼容版本
uv lock --resolution highest  # 使用最高版本

# 清除缓存重建
uv cache clean
uv sync --refresh

# 检查环境信息
uv info
uv python list               # 显示可用 Python 版本
```

### 重置环境
```bash
# 删除虚拟环境重建
rm -rf .venv
uv venv
uv sync
```

## 🔍 项目状态检查

### 当前优化状态验证
```bash
# 1. 检查 Redis 缓存
cd backend/django_service
uv run python -c "
from django.core.cache import cache
from django.conf import settings
settings.configure()
print('Redis 缓存数据库:')
for name, config in settings.CACHES.items():
    print(f'  {name}: {config[\"LOCATION\"]}')
"

# 2. 检查 Celery 配置
uv run python -c "
import os
from ansflow.celery import app
print('Celery Broker:', app.conf.broker_url)
print('Result Backend:', app.conf.result_backend)
"

# 3. 验证 FastAPI 服务
cd ../fastapi_service
uv run python -c "
from ansflow_api.main import app
print('FastAPI 服务配置正常')
print('可用路由数量:', len(app.routes))
"
```

### 性能基准测试
```bash
# API 响应时间测试
curl -w "响应时间: %{time_total}s\n" -o /dev/null -s "http://localhost:8000/api/v1/settings/api-endpoints/"

# FastAPI 性能测试
curl -w "响应时间: %{time_total}s\n" -o /dev/null -s "http://localhost:8080/health"
```

## 📊 监控和日志

### 实时监控
```bash
# Django 开发服务器 (带调试)
cd backend/django_service
uv run python manage.py runserver --settings=ansflow.settings.development

# FastAPI 开发服务器 (带重载)
cd backend/fastapi_service
uv run uvicorn main:app --reload --log-level debug

# Celery Worker 监控
cd backend/django_service  
uv run celery -A ansflow worker --loglevel=info

# 查看 RabbitMQ 队列状态
rabbitmqctl list_queues
```

### 日志查看
```bash
# Django 应用日志
tail -f logs/django.log

# FastAPI 访问日志  
tail -f logs/fastapi.log

# Celery 任务日志
tail -f logs/celery.log
```

## 🎯 开发工作流程

### 日常开发循环
```bash
# 1. 拉取最新代码
git pull origin main

# 2. 同步依赖  
cd backend/django_service && uv sync
cd ../fastapi_service && uv sync

# 3. 运行测试
cd backend/django_service
uv run python manage.py test

# 4. 启动开发服务
uv run python manage.py runserver &
cd ../fastapi_service  
uv run uvicorn main:app --reload &

# 5. 性能验证
cd ../..
uv run python test_optimization.py
```

### 部署前检查
```bash
# 1. 代码质量检查
cd backend/django_service
uv run black . --check
uv run isort . --check-only  
uv run flake8 .

# 2. 安全检查
uv run python manage.py check --deploy

# 3. 依赖审计
uv tree --verbose
```

## 🔄 CI/CD 集成

### Docker 构建 (使用 UV)
```dockerfile
# 在 Dockerfile 中使用 UV
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache
```

### GitHub Actions 示例
```yaml
- name: Install dependencies  
  run: |
    curl -LsSf https://astral.sh/uv/install.sh | sh
    uv sync
    
- name: Run tests
  run: uv run pytest
```

## 📚 有用的别名

### 添加到 ~/.zshrc 或 ~/.bashrc
```bash
# AnsFlow UV 快捷命令
alias ansflow-django="cd /Users/creed/Workspace/OpenSource/ansflow/backend/django_service"
alias ansflow-fastapi="cd /Users/creed/Workspace/OpenSource/ansflow/backend/fastapi_service"
alias ansflow-test="cd /Users/creed/Workspace/OpenSource/ansflow && uv run python test_optimization.py"

# UV 快捷命令
alias uvr="uv run"
alias uvs="uv sync"  
alias uva="uv add"
alias uvt="uv tree"
```

## 🎉 成功指标

### 验证优化效果
如果以下命令都能正常执行，说明优化成功：

```bash
# 1. 缓存测试通过
cd backend/django_service
uv run python -c "from django.core.cache import cache; cache.set('test',1); print('缓存:', cache.get('test'))"

# 2. FastAPI 服务响应
curl -s http://localhost:8080/health | grep -q "healthy"

# 3. 任务队列正常
cd backend/django_service
uv run python -c "from ansflow.celery import app; print('Celery:', app.control.ping())"

# 4. 性能指标达标  
cd ../..
uv run python test_optimization.py | grep -E "(响应时间|缓存命中)"
```

---

## 💡 小贴士

1. **始终使用 `uv run`** 而不是激活虚拟环境，这样更可靠
2. **定期运行 `uv sync`** 保持依赖同步  
3. **使用 `uv add --dev`** 区分开发和生产依赖
4. **运行 `test_optimization.py`** 验证性能改进

这个指南覆盖了所有常用的 UV 工作流程，让您可以高效地管理和优化 AnsFlow 项目！
