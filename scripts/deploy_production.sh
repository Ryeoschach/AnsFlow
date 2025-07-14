#!/bin/bash
# AnsFlow 生产环境部署脚本

set -e

echo "🚀 开始部署 AnsFlow 生产环境..."

# 检查环境变量文件
if [ ! -f .env.prod ]; then
    echo "❌ 错误: .env.prod 文件不存在"
    echo "请从 .env.prod.example 复制并配置生产环境变量"
    exit 1
fi

# 加载生产环境变量
source .env.prod

# 检查必需的环境变量
required_vars=("MYSQL_ROOT_PASSWORD" "MYSQL_PASSWORD" "DJANGO_SECRET_KEY" "RABBITMQ_USER" "RABBITMQ_PASSWORD" "ALLOWED_HOSTS")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ 错误: 环境变量 $var 未设置"
        exit 1
    fi
done

echo "✅ 环境变量检查通过"

# 构建生产镜像
echo "🔨 构建生产镜像..."
docker-compose -f docker-compose.prod.yml build --no-cache

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose -f docker-compose.prod.yml down

# 清理旧数据 (可选，谨慎使用)
if [ "$CLEAN_DATA" = "true" ]; then
    echo "🗑️ 清理旧数据..."
    docker volume prune -f
fi

# 启动生产服务
echo "🚀 启动生产服务..."
docker-compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 运行数据库迁移
echo "📊 执行数据库迁移..."
docker-compose -f docker-compose.prod.yml exec django_service uv run python manage.py migrate

# 收集静态文件
echo "📁 收集静态文件..."
docker-compose -f docker-compose.prod.yml exec django_service uv run python manage.py collectstatic --noinput

# 创建超级用户 (如果需要)
if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "👤 创建超级用户..."
    docker-compose -f docker-compose.prod.yml exec django_service uv run python manage.py createsuperuser --noinput --username admin --email admin@ansflow.dev
fi

# 健康检查
echo "🔍 执行健康检查..."
sleep 10

# 检查 Django 服务
if curl -f http://localhost:8000/api/v1/health/ > /dev/null 2>&1; then
    echo "✅ Django 服务健康检查通过"
else
    echo "❌ Django 服务健康检查失败"
fi

# 检查 FastAPI 服务
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ FastAPI 服务健康检查通过"
else
    echo "❌ FastAPI 服务健康检查失败"
fi

# 显示服务状态
echo "📊 服务状态:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🎉 AnsFlow 生产环境部署完成!"
echo ""
echo "📋 服务访问地址:"
echo "  - 前端界面: https://your-domain.com"
echo "  - Django API: http://your-domain.com:8000"
echo "  - FastAPI 服务: http://your-domain.com:8001"
echo "  - RabbitMQ 管理: http://your-domain.com:15672"
echo ""
echo "🔧 管理命令:"
echo "  - 查看日志: docker-compose -f docker-compose.prod.yml logs -f"
echo "  - 停止服务: docker-compose -f docker-compose.prod.yml down"
echo "  - 重启服务: docker-compose -f docker-compose.prod.yml restart"
echo ""
echo "📊 监控信息:"
echo "  - 运行性能测试: python scripts/optimization/test_optimization.py"
echo "  - 查看系统资源: docker stats"
