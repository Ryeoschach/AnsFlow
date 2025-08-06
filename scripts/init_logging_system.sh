#!/bin/bash
# AnsFlow 日志系统初始化和启动脚本
# 基于方案一的统一日志架构

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"

echo -e "${BLUE}=== AnsFlow 日志系统初始化 ===${NC}"
echo "项目根目录: $PROJECT_ROOT"
echo "日志目录: $LOG_DIR"

# 1. 创建日志目录结构
echo -e "\n${YELLOW}1. 创建统一日志目录结构...${NC}"
mkdir -p "$LOG_DIR/services/"{django,fastapi,system}
mkdir -p "$LOG_DIR/aggregated"
mkdir -p "$LOG_DIR/archived"

echo "✅ 日志目录结构创建完成"
tree "$LOG_DIR" || ls -la "$LOG_DIR"

# 2. 设置日志目录权限
echo -e "\n${YELLOW}2. 设置日志目录权限...${NC}"
chmod -R 755 "$LOG_DIR"
echo "✅ 日志目录权限设置完成"

# 3. 加载环境变量
echo -e "\n${YELLOW}3. 加载日志配置...${NC}"
if [ -f "$PROJECT_ROOT/.env.logging" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env.logging" | xargs)
    echo "✅ 已加载开发环境日志配置"
elif [ -f "$PROJECT_ROOT/.env.logging.example" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env.logging.example" | xargs)
    echo "⚠️  使用示例配置文件"
else
    echo -e "${RED}❌ 未找到日志配置文件${NC}"
    exit 1
fi

# 4. 检查 Python 环境
echo -e "\n${YELLOW}4. 检查 Python 环境...${NC}"
check_python_service() {
    local service_dir="$1"
    local service_name="$2"
    
    if [ -d "$service_dir" ]; then
        echo "检查 $service_name 服务..."
        cd "$service_dir"
        
        if [ -f "pyproject.toml" ] && [ -d ".venv" ]; then
            echo "  ✅ $service_name uv 环境正常"
            
            # 检查 structlog 依赖
            if uv run python -c "import structlog" 2>/dev/null; then
                echo "  ✅ structlog 已安装"
            else
                echo "  ⚠️  正在安装 structlog..."
                uv add structlog
            fi
            
            return 0
        else
            echo -e "  ${RED}❌ $service_name 环境未配置${NC}"
            return 1
        fi
    else
        echo -e "  ${RED}❌ $service_name 服务目录不存在${NC}"
        return 1
    fi
}

cd "$PROJECT_ROOT"
check_python_service "backend/django_service" "Django"
django_status=$?

check_python_service "backend/fastapi_service" "FastAPI"
fastapi_status=$?

# 5. 初始化日志配置
echo -e "\n${YELLOW}5. 初始化日志配置文件...${NC}"
cd "$PROJECT_ROOT"

# Django 服务日志配置
if [ $django_status -eq 0 ]; then
    echo "配置 Django 服务日志..."
    cd backend/django_service
    
    # 创建日志配置初始化脚本
    cat > init_logging.py << 'EOF'
import os
import sys
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow')

from common.django_logging_config import setup_django_logging, get_logger
import logging.config

# 设置日志配置
config = setup_django_logging()
logging.config.dictConfig(config)

# 测试日志
logger = get_logger('ansflow.django', 'init')
logger.info("Django 日志系统初始化完成")
logger.info("日志目录: %s", os.getenv('LOG_DIR', '/Users/creed/Workspace/OpenSource/ansflow/logs'))

print("✅ Django 日志系统初始化成功")
EOF
    
    uv run python init_logging.py
    rm init_logging.py
    
    cd "$PROJECT_ROOT"
fi

# FastAPI 服务日志配置
if [ $fastapi_status -eq 0 ]; then
    echo "配置 FastAPI 服务日志..."
    cd backend/fastapi_service
    
    # 创建日志配置初始化脚本
    cat > init_logging.py << 'EOF'
import os
import sys
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow')

from fastapi_logging_config import setup_fastapi_logging, get_logger

# 设置日志配置
logger = setup_fastapi_logging()
logger.info("FastAPI 日志系统初始化完成")
logger.info("日志目录: %s", os.getenv('LOG_DIR', '/Users/creed/Workspace/OpenSource/ansflow/logs'))

print("✅ FastAPI 日志系统初始化成功")
EOF
    
    uv run python init_logging.py
    rm init_logging.py
    
    cd "$PROJECT_ROOT"
fi

# 6. 创建系统监控日志
echo -e "\n${YELLOW}6. 创建系统监控日志配置...${NC}"
cat > logs/services/system/system_monitor.py << 'EOF'
#!/usr/bin/env python3
import json
import time
import psutil
import os
from datetime import datetime
from pathlib import Path

def get_system_stats():
    """获取系统统计信息"""
    return {
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "level": "INFO",
        "service": "system",
        "component": "monitor",
        "message": "System monitoring stats",
        "stats": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        }
    }

def main():
    log_file = Path(__file__).parent / "system_main.log"
    
    while True:
        stats = get_system_stats()
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(stats, ensure_ascii=False) + '\n')
        
        time.sleep(60)  # 每分钟记录一次

if __name__ == '__main__':
    main()
EOF

chmod +x logs/services/system/system_monitor.py
echo "✅ 系统监控脚本创建完成"

# 7. 设置日志聚合定时任务
echo -e "\n${YELLOW}7. 设置日志聚合任务...${NC}"
if command -v python3 &> /dev/null; then
    # 测试日志聚合脚本
    cd "$PROJECT_ROOT"
    python3 scripts/log_aggregator.py --action aggregate --date $(date +%Y-%m-%d) 2>/dev/null || echo "⚠️  日志聚合脚本需要手动运行"
    echo "✅ 日志聚合任务配置完成"
else
    echo "⚠️  Python3 未找到，跳过聚合任务配置"
fi

# 8. 创建快速查看日志的脚本
echo -e "\n${YELLOW}8. 创建日志查看工具...${NC}"
cat > "$PROJECT_ROOT/view_logs.sh" << 'EOF'
#!/bin/bash
# AnsFlow 日志查看工具

LOG_DIR="logs"
SERVICE="$1"
TYPE="$2"
LINES="${3:-50}"

show_usage() {
    echo "使用方法: $0 [service] [type] [lines]"
    echo ""
    echo "参数说明:"
    echo "  service  服务名称: django, fastapi, system, all"
    echo "  type     日志类型: main, error, access, performance"
    echo "  lines    显示行数 (默认: 50)"
    echo ""
    echo "示例:"
    echo "  $0 django main 100     # 查看 Django 主日志最近 100 行"
    echo "  $0 fastapi error       # 查看 FastAPI 错误日志最近 50 行"
    echo "  $0 all main            # 查看所有服务主日志"
}

if [ "$1" = "-h" ] || [ "$1" = "--help" ] || [ -z "$1" ]; then
    show_usage
    exit 0
fi

if [ "$SERVICE" = "all" ]; then
    echo "=== 所有服务 ${TYPE:-main} 日志 ==="
    for svc in django fastapi system; do
        log_file="$LOG_DIR/services/$svc/${svc}_${TYPE:-main}.log"
        if [ -f "$log_file" ]; then
            echo ""
            echo "--- $svc 服务 ---"
            tail -n "$LINES" "$log_file"
        fi
    done
else
    log_file="$LOG_DIR/services/$SERVICE/${SERVICE}_${TYPE:-main}.log"
    if [ -f "$log_file" ]; then
        echo "=== $SERVICE ${TYPE:-main} 日志 (最近 $LINES 行) ==="
        tail -n "$LINES" "$log_file"
    else
        echo "❌ 日志文件不存在: $log_file"
        exit 1
    fi
fi
EOF

chmod +x "$PROJECT_ROOT/view_logs.sh"
echo "✅ 日志查看工具创建完成"

# 9. 显示初始化结果
echo -e "\n${GREEN}=== 日志系统初始化完成 ===${NC}"
echo ""
echo "📁 日志目录结构:"
echo "   logs/"
echo "   ├── services/"
echo "   │   ├── django/     (Django 服务日志)"
echo "   │   ├── fastapi/    (FastAPI 服务日志)"
echo "   │   └── system/     (系统监控日志)"
echo "   ├── aggregated/     (聚合日志)"
echo "   └── archived/       (归档日志)"
echo ""
echo "🛠  可用工具:"
echo "   ./view_logs.sh      - 快速查看日志"
echo "   python3 scripts/log_aggregator.py - 手动聚合日志"
echo ""
echo "🔧 配置文件:"
echo "   .env.logging        - 开发环境配置"
echo "   .env.logging.production - 生产环境配置"
echo ""
echo "📋 下一步操作:"
echo "   1. 检查配置文件并根据需要调整"
echo "   2. 启动相关服务"
echo "   3. 使用 ./view_logs.sh 查看日志"
echo "   4. 设置定时任务进行日志聚合"

# 10. 验证日志系统
echo -e "\n${YELLOW}10. 验证日志系统...${NC}"
sleep 2

# 检查是否有日志文件生成
log_count=$(find "$LOG_DIR/services" -name "*.log" | wc -l)
if [ "$log_count" -gt 0 ]; then
    echo "✅ 发现 $log_count 个日志文件"
    find "$LOG_DIR/services" -name "*.log" -exec ls -lh {} \;
else
    echo "⚠️  暂未发现日志文件，启动服务后将自动创建"
fi

echo -e "\n${GREEN}🎉 AnsFlow 日志系统初始化完成！${NC}"
