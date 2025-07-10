#!/bin/bash

# AnsFlow微服务优化启动和测试脚本
# 用于启动服务并测试优化效果

set -e

echo "🚀 AnsFlow微服务优化启动脚本"
echo "================================="

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 检查docker-compose是否可用
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose未安装"
    exit 1
fi

echo "✅ Docker环境检查通过"

# 进入项目目录
cd "$(dirname "$0")"

echo "📁 当前目录: $(pwd)"

# 启动服务
echo ""
echo "🔧 启动AnsFlow服务..."
echo "====================="

# 构建并启动服务
docker-compose up -d

echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo ""
echo "🔍 检查服务状态..."
echo "=================="

services=("ansflow_mysql" "ansflow_redis" "ansflow_rabbitmq" "ansflow_django" "ansflow_fastapi")

for service in "${services[@]}"; do
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$service.*Up"; then
        echo "✅ $service: 运行中"
    else
        echo "❌ $service: 未运行"
    fi
done

# 等待Django迁移完成
echo ""
echo "⏳ 等待Django服务完全启动..."
timeout=60
while [ $timeout -gt 0 ]; do
    if curl -s http://localhost:8000/admin/ > /dev/null 2>&1; then
        echo "✅ Django服务已启动"
        break
    fi
    sleep 2
    timeout=$((timeout - 2))
done

if [ $timeout -le 0 ]; then
    echo "⚠️  Django服务启动超时，但继续测试..."
fi

# 等待FastAPI服务启动
echo "⏳ 等待FastAPI服务启动..."
timeout=30
while [ $timeout -gt 0 ]; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ FastAPI服务已启动"
        break
    fi
    sleep 2
    timeout=$((timeout - 2))
done

if [ $timeout -le 0 ]; then
    echo "⚠️  FastAPI服务启动超时，但继续测试..."
fi

# 显示服务访问地址
echo ""
echo "🌐 服务访问地址"
echo "=============="
echo "Django Admin:   http://localhost:8000/admin/"
echo "Django API:     http://localhost:8000/api/v1/"
echo "FastAPI Docs:   http://localhost:8001/docs"
echo "FastAPI Health: http://localhost:8001/health"
echo "RabbitMQ管理:    http://localhost:15672 (ansflow/ansflow_rabbitmq_123)"
echo "Prometheus:     http://localhost:9090"
echo "Grafana:        http://localhost:3001 (admin/admin123)"

# 运行基本测试
echo ""
echo "🧪 运行基本功能测试..."
echo "===================="

# 测试Redis连接
echo "🔍 测试Redis连接..."
if docker exec ansflow_redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis连接正常"
else
    echo "❌ Redis连接失败"
fi

# 测试MySQL连接
echo "🔍 测试MySQL连接..."
if docker exec ansflow_mysql mysql -u root -proot_password_123 -e "SELECT 1" > /dev/null 2>&1; then
    echo "✅ MySQL连接正常"
else
    echo "❌ MySQL连接失败"
fi

# 测试RabbitMQ连接
echo "🔍 测试RabbitMQ连接..."
if docker exec ansflow_rabbitmq rabbitmqctl status > /dev/null 2>&1; then
    echo "✅ RabbitMQ运行正常"
else
    echo "❌ RabbitMQ状态异常"
fi

# 测试Django API
echo "🔍 测试Django API..."
if curl -s http://localhost:8000/api/v1/ > /dev/null 2>&1; then
    echo "✅ Django API响应正常"
else
    echo "❌ Django API无响应"
fi

# 测试FastAPI
echo "🔍 测试FastAPI..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ FastAPI响应正常"
else
    echo "❌ FastAPI无响应"
fi

# 显示缓存性能测试建议
echo ""
echo "📊 性能测试建议"
echo "=============="
echo "1. 缓存性能测试:"
echo "   curl -w '%{time_total}\\n' http://localhost:8000/api/v1/settings/api-endpoints/"
echo ""
echo "2. 重复请求测试缓存效果:"
echo "   for i in {1..5}; do curl -w '%{time_total}\\n' -o /dev/null -s http://localhost:8000/api/v1/settings/api-endpoints/; done"
echo ""
echo "3. FastAPI性能测试:"
echo "   curl -w '%{time_total}\\n' http://localhost:8001/health"
echo ""
echo "4. 查看Redis缓存键:"
echo "   docker exec ansflow_redis redis-cli --scan --pattern 'ansflow:*'"
echo ""
echo "5. 查看RabbitMQ队列:"
echo "   docker exec ansflow_rabbitmq rabbitmqctl list_queues"

# 运行Python测试脚本（如果存在）
if [ -f "test_optimization.py" ]; then
    echo ""
    echo "🐍 运行Python优化测试..."
    echo "======================"
    
    # 检查Python依赖
    echo "📦 检查Python依赖..."
    missing_deps=()
    
    python3 -c "import requests" 2>/dev/null || missing_deps+=("requests")
    python3 -c "import aiohttp" 2>/dev/null || missing_deps+=("aiohttp")
    python3 -c "import redis" 2>/dev/null || missing_deps+=("redis")
    python3 -c "import pika" 2>/dev/null || missing_deps+=("pika")
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo "⚠️  缺少Python依赖: ${missing_deps[*]}"
        echo "💡 安装依赖: pip install ${missing_deps[*]}"
        echo "🔧 或者运行: pip install -r requirements.txt"
    else
        echo "✅ Python依赖已满足"
        echo "🚀 运行测试脚本..."
        python3 test_optimization.py
    fi
else
    echo "⚠️  测试脚本 test_optimization.py 不存在"
fi

echo ""
echo "🎉 AnsFlow微服务优化部署完成！"
echo "================================"
echo ""
echo "📋 后续步骤："
echo "1. 访问各服务验证功能"
echo "2. 观察缓存命中率提升"
echo "3. 监控RabbitMQ队列处理"
echo "4. 测试FastAPI实时功能"
echo ""
echo "🛠️  如需停止服务: docker-compose down"
echo "📊 查看日志: docker-compose logs -f [service_name]"
