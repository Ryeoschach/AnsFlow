#!/bin/bash
"""
AnsFlow 监控系统启动脚本
启动所有服务并验证监控系统工作状态
"""

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_success "系统依赖检查通过"
}

# 启动基础服务
start_infrastructure() {
    log_info "启动基础设施服务 (Redis, RabbitMQ, MySQL)..."
    
    docker-compose up -d redis rabbitmq mysql
    
    log_info "等待数据库服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(ansflow_redis|ansflow_rabbitmq|ansflow_mysql)" | grep -q "Up"; then
        log_success "基础设施服务启动成功"
    else
        log_error "基础设施服务启动失败"
        exit 1
    fi
}

# 启动监控服务
start_monitoring() {
    log_info "启动监控服务 (Prometheus, Grafana)..."
    
    docker-compose up -d prometheus grafana
    
    log_info "等待监控服务启动..."
    sleep 15
    
    # 检查服务状态
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(ansflow_prometheus|ansflow_grafana)" | grep -q "Up"; then
        log_success "监控服务启动成功"
    else
        log_error "监控服务启动失败"
        exit 1
    fi
}

# 启动应用服务
start_applications() {
    log_info "启动应用服务 (Django, FastAPI)..."
    
    # 安装 FastAPI 依赖
    log_info "安装 FastAPI 服务依赖..."
    cd backend/fastapi_service
    uv sync
    cd ../..
    
    # 启动 Django 服务
    log_info "启动 Django 服务..."
    cd backend/django_service
    uv run python manage.py migrate --noinput || true
    uv run python manage.py runserver 0.0.0.0:8000 &
    DJANGO_PID=$!
    cd ../..
    
    # 启动 FastAPI 服务
    log_info "启动 FastAPI 服务..."
    cd backend/fastapi_service
    uv run uvicorn ansflow_api.main:app --host 0.0.0.0 --port 8001 --reload &
    FASTAPI_PID=$!
    cd ../..
    
    log_info "等待应用服务启动..."
    sleep 10
    
    log_success "应用服务启动成功"
    log_info "Django PID: $DJANGO_PID"
    log_info "FastAPI PID: $FASTAPI_PID"
}

# 检查服务健康状态
check_health() {
    log_info "检查服务健康状态..."
    
    # 检查 Prometheus
    if curl -s http://localhost:9090/-/healthy > /dev/null; then
        log_success "Prometheus 健康检查通过"
    else
        log_warning "Prometheus 健康检查失败"
    fi
    
    # 检查 Grafana
    if curl -s http://localhost:3001/api/health > /dev/null; then
        log_success "Grafana 健康检查通过"
    else
        log_warning "Grafana 健康检查失败"
    fi
    
    # 检查 Django
    if curl -s http://localhost:8000/health/ > /dev/null; then
        log_success "Django 健康检查通过"
    else
        log_warning "Django 健康检查失败"
    fi
    
    # 检查 Django Metrics
    if curl -s http://localhost:8000/metrics | grep -q "django_"; then
        log_success "Django Prometheus 指标可用"
    else
        log_warning "Django Prometheus 指标不可用"
    fi
    
    # 检查 FastAPI
    if curl -s http://localhost:8001/health/ > /dev/null; then
        log_success "FastAPI 健康检查通过"
    else
        log_warning "FastAPI 健康检查失败"
    fi
    
    # 检查 FastAPI Metrics
    if curl -s http://localhost:8001/metrics | grep -q "ansflow_"; then
        log_success "FastAPI Prometheus 指标可用"
    else
        log_warning "FastAPI Prometheus 指标不可用"
    fi
}

# 显示访问信息
show_access_info() {
    echo ""
    echo "🎉 AnsFlow 监控系统启动完成！"
    echo "=================================="
    echo ""
    echo "📊 监控面板:"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana:    http://localhost:3001 (admin/admin123)"
    echo ""
    echo "🚀 应用服务:"
    echo "  Django API:  http://localhost:8000"
    echo "  FastAPI:     http://localhost:8001"
    echo "  API 文档:    http://localhost:8001/docs"
    echo ""
    echo "📈 监控指标:"
    echo "  FastAPI 指标: http://localhost:8001/metrics"
    echo "  健康检查:     http://localhost:8001/health/"
    echo ""
    echo "🛠️  管理工具:"
    echo "  RabbitMQ 管理: http://localhost:15672 (ansflow/ansflow_rabbitmq_123)"
    echo ""
    echo "💡 提示:"
    echo "  - 使用 Ctrl+C 停止所有服务"
    echo "  - 运行 'python scripts/optimization/test_performance_monitoring.py' 进行监控测试"
    echo "  - 查看 Grafana 仪表板了解系统性能"
    echo ""
}

# 清理函数
cleanup() {
    log_info "正在停止服务..."
    
    # 停止 Python 进程
    if [[ -n "$DJANGO_PID" ]]; then
        kill $DJANGO_PID 2>/dev/null || true
    fi
    if [[ -n "$FASTAPI_PID" ]]; then
        kill $FASTAPI_PID 2>/dev/null || true
    fi
    
    # 停止 Docker 服务
    docker-compose down
    
    log_success "所有服务已停止"
}

# 主函数
main() {
    echo "🚀 启动 AnsFlow 监控系统"
    echo "=========================="
    
    # 设置 trap 来处理中断信号
    trap cleanup EXIT INT TERM
    
    # 执行启动步骤
    check_dependencies
    start_infrastructure
    start_monitoring
    start_applications
    
    # 等待所有服务完全启动
    log_info "等待所有服务完全启动..."
    sleep 20
    
    # 检查健康状态
    check_health
    
    # 显示访问信息
    show_access_info
    
    # 保持脚本运行
    log_info "监控系统正在运行，按 Ctrl+C 停止所有服务"
    while true; do
        sleep 30
        # 定期检查服务状态
        if ! pgrep -f "uvicorn.*8001" > /dev/null; then
            log_warning "FastAPI 服务似乎已停止"
        fi
        if ! pgrep -f "runserver.*8000" > /dev/null; then
            log_warning "Django 服务似乎已停止"
        fi
    done
}

# 运行主函数
main "$@"
