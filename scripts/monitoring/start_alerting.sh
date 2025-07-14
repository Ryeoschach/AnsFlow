#!/bin/bash

# AnsFlow 告警系统启动脚本
# 启动 AlertManager 和告警处理 Webhook 服务

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

# 检查 Docker 是否运行
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    log_success "Docker is running"
}

# 启动 AlertManager
start_alertmanager() {
    log_info "Starting AlertManager..."
    
    # 检查 AlertManager 配置文件
    if [ ! -f "monitoring/alertmanager/alertmanager.yml" ]; then
        log_error "AlertManager configuration file not found: monitoring/alertmanager/alertmanager.yml"
        exit 1
    fi
    
    # 启动 AlertManager 容器
    docker run -d \
        --name ansflow_alertmanager \
        --restart unless-stopped \
        -p 9093:9093 \
        -v "$(pwd)/monitoring/alertmanager:/etc/alertmanager" \
        prom/alertmanager:latest \
        --config.file=/etc/alertmanager/alertmanager.yml \
        --storage.path=/alertmanager \
        --web.external-url=http://localhost:9093 \
        --cluster.advertise-address=0.0.0.0:9093
    
    log_success "AlertManager started on port 9093"
}

# 启动告警处理 Webhook 服务
start_webhook_service() {
    log_info "Starting Alert Webhook Service..."
    
    # 检查 webhook 脚本
    if [ ! -f "scripts/monitoring/alert_webhook.py" ]; then
        log_error "Alert webhook script not found: scripts/monitoring/alert_webhook.py"
        exit 1
    fi
    
    # 使用 FastAPI 环境运行 webhook 服务
    cd backend/fastapi_service
    
    # 后台启动 webhook 服务
    nohup uv run python ../../scripts/monitoring/alert_webhook.py > ../../logs/alert_webhook.log 2>&1 &
    WEBHOOK_PID=$!
    
    # 保存 PID
    echo $WEBHOOK_PID > ../../.webhook_pid
    
    cd ../..
    
    log_success "Alert Webhook Service started (PID: $WEBHOOK_PID) on port 5001"
}

# 检查服务状态
check_services() {
    log_info "Checking services status..."
    
    # 检查 AlertManager
    if curl -s http://localhost:9093/-/healthy > /dev/null; then
        log_success "AlertManager is healthy"
    else
        log_warning "AlertManager health check failed"
    fi
    
    # 检查 Webhook 服务
    if curl -s http://localhost:5001/health > /dev/null; then
        log_success "Alert Webhook Service is healthy"
    else
        log_warning "Alert Webhook Service health check failed"
    fi
    
    # 检查 Prometheus（确保它能连接到 AlertManager）
    if curl -s http://localhost:9090/-/healthy > /dev/null; then
        log_success "Prometheus is healthy"
    else
        log_warning "Prometheus health check failed"
    fi
}

# 显示服务信息
show_services_info() {
    echo ""
    echo "====================================="
    echo "🚨 AnsFlow 告警系统已启动"
    echo "====================================="
    echo ""
    echo "📊 服务地址:"
    echo "  • AlertManager:     http://localhost:9093"
    echo "  • Webhook Service:  http://localhost:5001"
    echo "  • Prometheus:       http://localhost:9090"
    echo "  • Grafana:          http://localhost:3001"
    echo ""
    echo "📋 有用的端点:"
    echo "  • AlertManager UI:  http://localhost:9093/#/alerts"
    echo "  • Webhook Status:   http://localhost:5001/health"
    echo "  • Alert History:    http://localhost:5001/alerts/history"
    echo "  • Alert Stats:      http://localhost:5001/alerts/stats"
    echo ""
    echo "🔧 管理命令:"
    echo "  • 查看告警状态:     curl http://localhost:5001/alerts/stats"
    echo "  • 查看告警历史:     curl http://localhost:5001/alerts/history"
    echo "  • 重启 AlertManager: docker restart ansflow_alertmanager"
    echo ""
    echo "📝 日志位置:"
    echo "  • Webhook 日志:     $(pwd)/logs/alert_webhook.log"
    echo "  • AlertManager 日志: docker logs ansflow_alertmanager"
    echo ""
}

# 停止服务
stop_services() {
    log_info "Stopping alert services..."
    
    # 停止 AlertManager
    if docker ps -q -f name=ansflow_alertmanager > /dev/null; then
        docker stop ansflow_alertmanager
        docker rm ansflow_alertmanager
        log_success "AlertManager stopped"
    fi
    
    # 停止 Webhook 服务
    if [ -f ".webhook_pid" ]; then
        WEBHOOK_PID=$(cat .webhook_pid)
        if kill -0 $WEBHOOK_PID 2>/dev/null; then
            kill $WEBHOOK_PID
            log_success "Alert Webhook Service stopped (PID: $WEBHOOK_PID)"
        fi
        rm -f .webhook_pid
    fi
}

# 重启服务
restart_services() {
    log_info "Restarting alert services..."
    stop_services
    sleep 2
    start_services
}

# 启动所有服务
start_services() {
    check_docker
    
    # 创建日志目录
    mkdir -p logs
    
    # 停止可能已经运行的服务
    stop_services
    
    # 启动服务
    start_alertmanager
    sleep 3
    start_webhook_service
    sleep 2
    
    # 检查服务状态
    check_services
    
    # 显示服务信息
    show_services_info
}

# 主函数
main() {
    case "$1" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            check_services
            ;;
        info)
            show_services_info
            ;;
        *)
            echo "Usage: $0 {start|stop|restart|status|info}"
            echo ""
            echo "Commands:"
            echo "  start   - 启动告警系统"
            echo "  stop    - 停止告警系统"
            echo "  restart - 重启告警系统"
            echo "  status  - 检查服务状态"
            echo "  info    - 显示服务信息"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
