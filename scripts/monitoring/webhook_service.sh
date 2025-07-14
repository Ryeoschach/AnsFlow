#!/bin/bash
# AnsFlow Webhook 服务启动脚本
# 作为后台服务运行，支持自动重启

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANSFLOW_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WEBHOOK_SCRIPT="$ANSFLOW_ROOT/scripts/monitoring/alert_webhook.py"
PID_FILE="/tmp/ansflow_webhook.pid"
LOG_FILE="/tmp/ansflow_webhook.log"

start_service() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "✅ Webhook 服务已经在运行 (PID: $(cat "$PID_FILE"))"
        return 0
    fi
    
    echo "🚀 启动 AnsFlow Webhook 服务..."
    
    # 切换到 FastAPI 项目目录使用 uv 环境
    cd "$ANSFLOW_ROOT/backend/fastapi_service"
    
    # 使用 uv 和 nohup 后台运行
    nohup uv run python "$WEBHOOK_SCRIPT" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    sleep 3
    
    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "✅ Webhook 服务启动成功 (PID: $(cat "$PID_FILE"))"
        echo "📄 日志文件: $LOG_FILE"
        echo "🌐 服务地址: http://localhost:5001"
    else
        echo "❌ Webhook 服务启动失败"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_service() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "🛑 停止 Webhook 服务 (PID: $PID)..."
            kill "$PID"
            sleep 2
            
            if kill -0 "$PID" 2>/dev/null; then
                echo "⚡ 强制停止 Webhook 服务..."
                kill -9 "$PID"
            fi
        fi
        rm -f "$PID_FILE"
        echo "✅ Webhook 服务已停止"
    else
        echo "ℹ️  Webhook 服务未运行"
    fi
}

status_service() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        PID=$(cat "$PID_FILE")
        echo "✅ Webhook 服务正在运行 (PID: $PID)"
        
        # 检查服务健康状态
        if curl -s -f http://localhost:5001/health > /dev/null 2>&1; then
            echo "🟢 服务健康检查通过"
        else
            echo "🔴 服务健康检查失败"
        fi
        
        # 显示最近的日志
        if [ -f "$LOG_FILE" ]; then
            echo "📄 最近日志:"
            tail -5 "$LOG_FILE"
        fi
    else
        echo "🔴 Webhook 服务未运行"
        if [ -f "$PID_FILE" ]; then
            rm -f "$PID_FILE"
        fi
    fi
}

restart_service() {
    echo "🔄 重启 Webhook 服务..."
    stop_service
    sleep 1
    start_service
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "📄 Webhook 服务日志:"
        tail -f "$LOG_FILE"
    else
        echo "❌ 日志文件不存在: $LOG_FILE"
    fi
}

case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "使用方法: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动 Webhook 服务"
        echo "  stop    - 停止 Webhook 服务"
        echo "  restart - 重启 Webhook 服务"
        echo "  status  - 查看服务状态"
        echo "  logs    - 查看服务日志"
        exit 1
        ;;
esac
