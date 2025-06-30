#!/bin/bash

# 🔍 AnsFlow 系统状态检查脚本
# 用途: 快速检查AnsFlow平台的各项服务和功能状态
# 使用: ./scripts/check_system_status.sh

set -e

echo "🚀 AnsFlow 系统状态检查开始..."
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查函数
check_service() {
    local service_name=$1
    local port=$2
    local url=$3
    
    echo -n "🔍 检查 $service_name (端口 $port)... "
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 运行正常${NC}"
        return 0
    else
        echo -e "${RED}❌ 无法访问${NC}"
        return 1
    fi
}

check_database() {
    echo -n "🔍 检查数据库连接... "
    
    if docker-compose exec django python manage.py check --deploy > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 数据库连接正常${NC}"
        return 0
    else
        echo -e "${RED}❌ 数据库连接失败${NC}"
        return 1
    fi
}

check_redis() {
    echo -n "🔍 检查Redis服务... "
    
    if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis服务正常${NC}"
        return 0
    else
        echo -e "${RED}❌ Redis服务异常${NC}"
        return 1
    fi
}

check_celery() {
    echo -n "🔍 检查Celery工作进程... "
    
    if docker-compose exec django celery -A django_service inspect active > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Celery工作正常${NC}"
        return 0
    else
        echo -e "${RED}❌ Celery工作异常${NC}"
        return 1
    fi
}

# 检查Docker容器状态
echo "📦 Docker容器状态检查"
echo "----------------------------------------"
docker-compose ps

echo -e "\n🌐 服务可用性检查"
echo "----------------------------------------"

# 检查各项服务
services_ok=0
total_services=6

# 前端服务
if check_service "前端服务" "3000" "http://localhost:3000"; then
    ((services_ok++))
fi

# Django管理服务
if check_service "Django管理服务" "8000" "http://localhost:8000/admin/"; then
    ((services_ok++))
fi

# FastAPI高性能服务
if check_service "FastAPI服务" "8001" "http://localhost:8001/docs"; then
    ((services_ok++))
fi

# 数据库检查
if check_database; then
    ((services_ok++))
fi

# Redis检查
if check_redis; then
    ((services_ok++))
fi

# Celery检查
if check_celery; then
    ((services_ok++))
fi

echo -e "\n📊 API端点健康检查"
echo "----------------------------------------"

# 检查关键API端点
api_ok=0
total_apis=5

echo -n "🔍 检查流水线列表API... "
if curl -s "http://localhost:8000/api/pipelines/" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 正常${NC}"
    ((api_ok++))
else
    echo -e "${RED}❌ 异常${NC}"
fi

echo -n "🔍 检查工具列表API... "
if curl -s "http://localhost:8000/api/tools/" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 正常${NC}"
    ((api_ok++))
else
    echo -e "${RED}❌ 异常${NC}"
fi

echo -n "🔍 检查WebSocket健康检查... "
if curl -s "http://localhost:8000/ws/health/" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 正常${NC}"
    ((api_ok++))
else
    echo -e "${RED}❌ 异常${NC}"
fi

echo -n "🔍 检查FastAPI文档... "
if curl -s "http://localhost:8001/docs" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 正常${NC}"
    ((api_ok++))
else
    echo -e "${RED}❌ 异常${NC}"
fi

echo -n "🔍 检查FastAPI健康检查... "
if curl -s "http://localhost:8001/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 正常${NC}"
    ((api_ok++))
else
    echo -e "${RED}❌ 异常${NC}"
fi

echo -e "\n🧪 核心功能快速测试"
echo "----------------------------------------"

echo -n "🔍 检查用户认证功能... "
# 尝试访问需要认证的页面
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/user/profile/" | grep -q "401\|403"; then
    echo -e "${GREEN}✅ 认证机制正常${NC}"
else
    echo -e "${YELLOW}⚠️  认证检查异常${NC}"
fi

echo -n "🔍 检查数据库迁移状态... "
if docker-compose exec django python manage.py showmigrations --plan | grep -q '\[X\]'; then
    echo -e "${GREEN}✅ 迁移已应用${NC}"
else
    echo -e "${RED}❌ 迁移未完成${NC}"
fi

echo -e "\n📈 系统资源使用情况"
echo "----------------------------------------"
echo "🖥️  内存使用:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo -e "\n📋 检查结果汇总"
echo "========================================"
echo -e "服务状态: ${GREEN}$services_ok${NC}/$total_services 正常"
echo -e "API状态: ${GREEN}$api_ok${NC}/$total_apis 正常"

# 计算总体健康度
total_checks=$((total_services + total_apis))
total_ok=$((services_ok + api_ok))
health_percentage=$((total_ok * 100 / total_checks))

echo -e "总体健康度: ${GREEN}$health_percentage%${NC}"

if [ $health_percentage -ge 90 ]; then
    echo -e "\n🎉 ${GREEN}系统状态优秀！所有核心功能正常运行。${NC}"
elif [ $health_percentage -ge 70 ]; then
    echo -e "\n⚠️  ${YELLOW}系统状态良好，但有部分服务需要注意。${NC}"
else
    echo -e "\n🚨 ${RED}系统状态异常，请检查日志并修复问题。${NC}"
fi

echo -e "\n📚 快速链接"
echo "----------------------------------------"
echo "🌐 前端界面: http://localhost:3000"
echo "🔧 Django管理: http://localhost:8000/admin/"
echo "📡 FastAPI文档: http://localhost:8001/docs"
echo "📊 流水线管理: http://localhost:3000/pipelines"
echo "🔗 工具集成: http://localhost:3000/tools"

echo -e "\n🔧 故障排除建议"
echo "----------------------------------------"
if [ $services_ok -lt $total_services ]; then
    echo "• 服务异常: 运行 'docker-compose logs [service-name]' 查看日志"
    echo "• 重启服务: 运行 'docker-compose restart [service-name]'"
fi

if [ $api_ok -lt $total_apis ]; then
    echo "• API异常: 检查后端服务日志和数据库连接"
    echo "• 数据库问题: 运行 'make db-migrate' 应用迁移"
fi

echo -e "\n✅ 系统状态检查完成！"
