#!/bin/bash

# AnsFlow 统一日志系统服务启动脚本
# 确保所有服务（Django、FastAPI、Celery）都能正确集成统一日志系统

set -e

echo "🚀 启动 AnsFlow 统一日志系统集成服务..."

# 项目根目录
PROJECT_ROOT="/Users/creed/Workspace/OpenSource/ansflow"
cd "$PROJECT_ROOT"

# 创建日志目录
echo "📁 创建日志目录结构..."
mkdir -p logs/services/{django,fastapi,celery}
mkdir -p logs/realtime

# 检查Redis服务状态
echo "🔍 检查Redis服务状态..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis 服务已启动"
else
    echo "⚠️  Redis 服务未启动，请先启动Redis服务"
    echo "   启动命令: brew services start redis"
    exit 1
fi

# 检查MySQL服务状态  
echo "🔍 检查MySQL服务状态..."
if mysqladmin ping > /dev/null 2>&1; then
    echo "✅ MySQL 服务已启动"
else
    echo "⚠️  MySQL 服务未启动，请先启动MySQL服务"
    echo "   启动命令: brew services start mysql"
    exit 1
fi

# 启动Django服务
echo "🔧 启动Django服务（统一日志系统）..."
cd "$PROJECT_ROOT/backend/django_service"

if [ ! -d ".venv" ]; then
    echo "📦 创建Python虚拟环境..."
    uv venv
fi

# 激活虚拟环境并启动Django
echo "🌐 启动Django开发服务器..."
uv run python manage.py runserver 8000 &
DJANGO_PID=$!
echo "✅ Django服务已启动 (PID: $DJANGO_PID)"

# 等待Django服务启动
sleep 3

# 启动Celery Worker
echo "⚙️  启动Celery Worker..."
cd "$PROJECT_ROOT/backend/django_service"
uv run celery -A ansflow worker -l info --queues=high_priority,medium_priority,low_priority &
CELERY_WORKER_PID=$!
echo "✅ Celery Worker已启动 (PID: $CELERY_WORKER_PID)"

# 启动Celery Beat
echo "📅 启动Celery Beat..."
uv run celery -A ansflow beat -l info &
CELERY_BEAT_PID=$!
echo "✅ Celery Beat已启动 (PID: $CELERY_BEAT_PID)"

# 启动FastAPI服务
echo "⚡ 启动FastAPI服务..."
cd "$PROJECT_ROOT/backend/fastapi_service"

if [ ! -d ".venv" ]; then
    echo "📦 创建FastAPI Python虚拟环境..."
    uv venv
fi

# 启动FastAPI服务
uv run uvicorn ansflow_api.main:app --host 0.0.0.0 --port 8001 --reload &
FASTAPI_PID=$!
echo "✅ FastAPI服务已启动 (PID: $FASTAPI_PID)"

# 等待所有服务启动
sleep 5

# 验证服务状态
echo ""
echo "🔍 验证服务状态..."

# 检查Django服务
if curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
    echo "✅ Django服务 (8000) - 运行正常"
else
    echo "❌ Django服务 (8000) - 启动失败"
fi

# 检查FastAPI服务
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ FastAPI服务 (8001) - 运行正常"
else
    echo "❌ FastAPI服务 (8001) - 启动失败"
fi

# 检查Celery服务
if kill -0 $CELERY_WORKER_PID > /dev/null 2>&1; then
    echo "✅ Celery Worker - 运行正常"
else
    echo "❌ Celery Worker - 启动失败"
fi

if kill -0 $CELERY_BEAT_PID > /dev/null 2>&1; then
    echo "✅ Celery Beat - 运行正常"
else
    echo "❌ Celery Beat - 启动失败"
fi

echo ""
echo "🎉 AnsFlow 统一日志系统集成服务启动完成!"
echo ""
echo "📊 服务访问地址:"
echo "   Django管理后台: http://localhost:8000/admin/"
echo "   Django API: http://localhost:8000/api/"
echo "   FastAPI文档: http://localhost:8001/docs"
echo "   实时日志监控: http://localhost:8000/monitoring/realtime-logs/"
echo ""
echo "📝 日志文件位置:"
echo "   Django: logs/services/django/"
echo "   FastAPI: logs/services/fastapi/"
echo "   Celery: logs/services/celery/"
echo ""
echo "🛑 停止所有服务:"
echo "   kill $DJANGO_PID $FASTAPI_PID $CELERY_WORKER_PID $CELERY_BEAT_PID"
echo ""

# 创建停止脚本
cat > "$PROJECT_ROOT/stop_services.sh" << EOF
#!/bin/bash
echo "🛑 停止AnsFlow服务..."

# 停止所有相关进程
if kill $DJANGO_PID 2>/dev/null; then
    echo "✅ Django服务已停止"
fi

if kill $FASTAPI_PID 2>/dev/null; then
    echo "✅ FastAPI服务已停止"
fi

if kill $CELERY_WORKER_PID 2>/dev/null; then
    echo "✅ Celery Worker已停止"
fi

if kill $CELERY_BEAT_PID 2>/dev/null; then
    echo "✅ Celery Beat已停止"
fi

echo "🎯 所有AnsFlow服务已停止"
EOF

chmod +x "$PROJECT_ROOT/stop_services.sh"

echo "💡 提示: 使用 './stop_services.sh' 停止所有服务"

# 保持脚本运行，等待手动终止
echo "⌨️  按 Ctrl+C 停止所有服务"
wait
