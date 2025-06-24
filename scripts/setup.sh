#!/bin/bash

# AnsFlow Project Setup Script
# 项目初始化脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "========================================"
echo "🚀 AnsFlow CI/CD Platform Setup"
echo "========================================"
echo -e "${NC}"

# 检查 Docker 安装
check_docker() {
    echo -e "${YELLOW}🔍 检查 Docker 安装...${NC}"
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装，请先安装 Docker${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose 未安装，请先安装 Docker Compose${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker 环境检查通过${NC}"
}

# 创建环境配置文件
setup_env() {
    echo -e "${YELLOW}⚙️  设置环境配置...${NC}"
    if [ ! -f .env ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ 已创建 .env 文件${NC}"
        echo -e "${YELLOW}📝 请根据需要修改 .env 文件中的配置${NC}"
    else
        echo -e "${BLUE}ℹ️  .env 文件已存在${NC}"
    fi
}

# 创建必要的目录
create_directories() {
    echo -e "${YELLOW}📁 创建必要的目录...${NC}"
    
    # 数据目录
    mkdir -p data/mysql
    mkdir -p data/redis
    mkdir -p data/rabbitmq
    mkdir -p data/grafana
    mkdir -p data/prometheus
    
    # 日志目录
    mkdir -p logs/django
    mkdir -p logs/fastapi
    mkdir -p logs/nginx
    
    # 备份目录
    mkdir -p backups
    
    # 媒体文件目录
    mkdir -p media
    
    echo -e "${GREEN}✅ 目录创建完成${NC}"
}

# 设置权限
setup_permissions() {
    echo -e "${YELLOW}🔒 设置目录权限...${NC}"
    
    # 设置数据目录权限
    chmod -R 755 data/
    chmod -R 755 logs/
    chmod -R 755 backups/
    chmod -R 755 media/
    
    # 设置脚本执行权限
    find scripts/ -name "*.sh" -exec chmod +x {} \;
    
    echo -e "${GREEN}✅ 权限设置完成${NC}"
}

# 构建和启动服务
start_services() {
    echo -e "${YELLOW}🏗️  构建和启动服务...${NC}"
    
    # 拉取基础镜像
    docker-compose pull
    
    # 构建自定义镜像
    docker-compose build
    
    # 启动服务
    docker-compose up -d
    
    echo -e "${GREEN}✅ 服务启动完成${NC}"
}

# 等待服务就绪
wait_for_services() {
    echo -e "${YELLOW}⏳ 等待服务就绪...${NC}"
    
    # 等待 MySQL 就绪
    echo "等待 MySQL 启动..."
    until docker-compose exec mysql mysqladmin ping -h"localhost" --silent; do
        sleep 2
    done
    
    # 等待 Redis 就绪
    echo "等待 Redis 启动..."
    until docker-compose exec redis redis-cli ping | grep PONG; do
        sleep 2
    done
    
    # 等待 RabbitMQ 就绪
    echo "等待 RabbitMQ 启动..."
    until docker-compose exec rabbitmq rabbitmqctl status; do
        sleep 2
    done
    
    echo -e "${GREEN}✅ 所有服务已就绪${NC}"
}

# 初始化数据库
init_database() {
    echo -e "${YELLOW}🗄️  初始化数据库...${NC}"
    
    # Django 数据库迁移
    docker-compose exec django_service python manage.py migrate
    
    # 创建超级用户（如果不存在）
    docker-compose exec django_service python manage.py shell << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Super user created: admin/admin123')
else:
    print('Super user already exists')
EOF
    
    echo -e "${GREEN}✅ 数据库初始化完成${NC}"
}

# 显示访问信息
show_access_info() {
    echo -e "${BLUE}"
    echo "========================================"
    echo "🎉 AnsFlow 安装完成!"
    echo "========================================"
    echo -e "${NC}"
    
    echo -e "${GREEN}📋 服务访问地址:${NC}"
    echo "  🎨 前端界面:      http://localhost:3000"
    echo "  🔧 Django 管理:   http://localhost:8000/admin"
    echo "  ⚡ FastAPI 文档:  http://localhost:8001/docs"
    echo "  🐰 RabbitMQ 管理: http://localhost:15672"
    echo "  📊 Grafana 监控:  http://localhost:3001"
    echo ""
    echo -e "${GREEN}🔑 默认登录凭据:${NC}"
    echo "  Admin 用户:      admin / admin123"
    echo "  RabbitMQ:        ansflow / ansflow_rabbitmq_123"
    echo "  Grafana:         admin / admin123"
    echo ""
    echo -e "${YELLOW}📚 更多信息:${NC}"
    echo "  项目文档:        README.md"
    echo "  项目结构:        PROJECT_STRUCTURE.md"
    echo "  技术架构:        项目说明/技术架构分析报告.md"
    echo ""
    echo -e "${GREEN}💡 常用命令:${NC}"
    echo "  查看服务状态:    make status"
    echo "  查看日志:        make dev-logs"
    echo "  重启服务:        make dev-restart"
    echo "  停止服务:        make dev-down"
    echo "  运行测试:        make test"
}

# 主函数
main() {
    echo -e "${YELLOW}开始安装 AnsFlow CI/CD 平台...${NC}"
    
    # 检查系统环境
    check_docker
    
    # 设置环境
    setup_env
    create_directories
    setup_permissions
    
    # 启动服务
    start_services
    wait_for_services
    
    # 初始化应用
    init_database
    
    # 显示完成信息
    show_access_info
    
    echo -e "${GREEN}🎉 安装完成！享受使用 AnsFlow！${NC}"
}

# 错误处理
trap 'echo -e "${RED}❌ 安装过程中出现错误，请检查日志${NC}"; exit 1' ERR

# 执行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
