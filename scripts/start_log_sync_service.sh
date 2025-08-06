#!/bin/bash
# AnsFlow 日志同步服务启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_SYNC_SERVICE="$PROJECT_ROOT/common/log_sync_service.py"

echo "🚀 启动 AnsFlow 日志同步服务..."
echo "项目根目录: $PROJECT_ROOT"
echo "同步服务: $LOG_SYNC_SERVICE"

# 检查日志同步服务文件是否存在
if [ ! -f "$LOG_SYNC_SERVICE" ]; then
    echo "❌ 错误: 日志同步服务文件不存在: $LOG_SYNC_SERVICE"
    exit 1
fi

# 设置环境变量
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export DJANGO_SETTINGS_MODULE="ansflow.settings"

# 进入Django服务目录（确保可以正确加载Django设置）
cd "$PROJECT_ROOT/backend/django_service"

echo "📊 初始化统一日志数据库表..."
# 执行SQL初始化脚本
mysql -u root -p ansflow < "$PROJECT_ROOT/common/init_unified_logs_tables.sql" || {
    echo "⚠️  SQL初始化脚本执行失败，继续启动服务..."
}

echo "🔄 启动日志同步服务..."
echo "使用 uv 环境运行Python脚本..."

# 使用 uv 运行日志同步服务
exec uv run python "$LOG_SYNC_SERVICE"
