#!/bin/bash
# AnsFlow UV 工作流程便捷别名配置
# 将以下内容添加到 ~/.zshrc 或 ~/.bashrc

echo "正在配置 AnsFlow UV 便捷别名..."

# AnsFlow 项目路径
export ANSFLOW_ROOT="/Users/creed/Workspace/OpenSource/ansflow"

# 快速导航别名
alias ansflow="cd $ANSFLOW_ROOT"
alias ansflow-django="cd $ANSFLOW_ROOT/backend/django_service"
alias ansflow-fastapi="cd $ANSFLOW_ROOT/backend/fastapi_service"
alias ansflow-docs="cd $ANSFLOW_ROOT/docs"

# UV 便捷命令
alias uvr="uv run"
alias uvs="uv sync"
alias uva="uv add"
alias uvd="uv add --dev"
alias uvt="uv tree"
alias uvi="uv info"

# AnsFlow 服务启动
alias ansflow-start-django="cd $ANSFLOW_ROOT/backend/django_service && uv run python manage.py runserver"
alias ansflow-start-fastapi="cd $ANSFLOW_ROOT/backend/fastapi_service && uv run uvicorn main:app --reload"
alias ansflow-start-all="$ANSFLOW_ROOT/start_optimized.sh"

# AnsFlow 测试和检查
alias ansflow-test="cd $ANSFLOW_ROOT && uv run python test_optimization.py"
alias ansflow-check-django="cd $ANSFLOW_ROOT/backend/django_service && uv run python manage.py check"
alias ansflow-check-fastapi="cd $ANSFLOW_ROOT/backend/fastapi_service && uv run python -c 'from ansflow_api.main import app; print(\"✅ FastAPI 配置正常\")'"

# 缓存测试
alias ansflow-test-redis="cd $ANSFLOW_ROOT/backend/django_service && DJANGO_SETTINGS_MODULE=ansflow.settings.base uv run python -c 'import django; django.setup(); from django.core.cache import cache; cache.set(\"test\", \"works\"); print(\"✅ Redis 缓存:\", cache.get(\"test\"))'"

# 依赖管理
alias ansflow-sync-all="cd $ANSFLOW_ROOT/backend/django_service && uv sync && cd ../fastapi_service && uv sync && echo '✅ 所有服务依赖已同步'"
alias ansflow-update-all="cd $ANSFLOW_ROOT/backend/django_service && uv sync --upgrade && cd ../fastapi_service && uv sync --upgrade && echo '✅ 所有依赖已更新'"

# 日志查看
alias ansflow-logs="tail -f $ANSFLOW_ROOT/logs/*.log"

# 快速帮助
alias ansflow-help="echo '
🚀 AnsFlow UV 快捷命令:

📁 导航:
  ansflow          - 进入项目根目录
  ansflow-django   - 进入 Django 服务目录
  ansflow-fastapi  - 进入 FastAPI 服务目录

🔧 UV 命令:
  uvr <command>    - uv run <command>
  uvs              - uv sync
  uva <package>    - uv add <package>
  uvd <package>    - uv add --dev <package>

🚀 服务启动:
  ansflow-start-django   - 启动 Django 服务
  ansflow-start-fastapi  - 启动 FastAPI 服务
  ansflow-start-all      - 启动所有服务

🧪 测试:
  ansflow-test           - 运行性能优化测试
  ansflow-test-redis     - 测试 Redis 缓存
  ansflow-check-django   - Django 健康检查
  ansflow-check-fastapi  - FastAPI 健康检查

📦 依赖管理:
  ansflow-sync-all       - 同步所有服务依赖
  ansflow-update-all     - 更新所有依赖

📚 更多帮助: 查看 $ANSFLOW_ROOT/docs/UV_QUICK_REFERENCE.md
'"

echo "✅ AnsFlow UV 别名配置完成！"
echo ""
echo "使用方法："
echo "1. source ~/.zshrc  # 重新加载配置"
echo "2. ansflow-help     # 查看所有可用命令"
echo "3. ansflow-test     # 运行性能测试验证优化效果"
echo ""
echo "🎉 现在您可以使用便捷命令进行 AnsFlow 开发了！"
