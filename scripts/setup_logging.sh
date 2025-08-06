#!/bin/bash

# AnsFlow 统一日志系统启动脚本
# 基于方案一的实现

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 日志目录
LOG_DIR="${PROJECT_ROOT}/logs"

echo -e "${BLUE}=== AnsFlow 统一日志系统初始化 ===${NC}"
echo "项目根目录: $PROJECT_ROOT"
echo "日志目录: $LOG_DIR"

# 1. 创建日志目录结构
echo -e "\n${YELLOW}1. 创建统一日志目录结构...${NC}"

mkdir -p "${LOG_DIR}/services/django"
mkdir -p "${LOG_DIR}/services/fastapi"  
mkdir -p "${LOG_DIR}/services/system"
mkdir -p "${LOG_DIR}/aggregated"
mkdir -p "${LOG_DIR}/archived"

echo -e "${GREEN}✓ 日志目录结构创建完成${NC}"

# 2. 复制环境配置文件
echo -e "\n${YELLOW}2. 设置环境配置...${NC}"

ENV_LOGGING_FILE="${PROJECT_ROOT}/.env.logging"
ENV_EXAMPLE_FILE="${PROJECT_ROOT}/.env.logging.example"

if [[ ! -f "$ENV_LOGGING_FILE" && -f "$ENV_EXAMPLE_FILE" ]]; then
    cp "$ENV_EXAMPLE_FILE" "$ENV_LOGGING_FILE"
    echo -e "${GREEN}✓ 已从模板创建 .env.logging 配置文件${NC}"
    echo -e "${YELLOW}  请根据需要修改配置: $ENV_LOGGING_FILE${NC}"
elif [[ -f "$ENV_LOGGING_FILE" ]]; then
    echo -e "${GREEN}✓ .env.logging 配置文件已存在${NC}"
else
    echo -e "${RED}✗ 找不到配置模板文件 .env.logging.example${NC}"
    exit 1
fi

# 3. 设置脚本权限
echo -e "\n${YELLOW}3. 设置脚本执行权限...${NC}"

AGGREGATOR_SCRIPT="${PROJECT_ROOT}/scripts/log_aggregator.py"
if [[ -f "$AGGREGATOR_SCRIPT" ]]; then
    chmod +x "$AGGREGATOR_SCRIPT"
    echo -e "${GREEN}✓ 日志聚合脚本权限设置完成${NC}"
else
    echo -e "${RED}✗ 日志聚合脚本不存在: $AGGREGATOR_SCRIPT${NC}"
fi

# 4. 测试日志配置
echo -e "\n${YELLOW}4. 测试日志系统配置...${NC}"

# 创建测试日志
TEST_LOG_FILE="${LOG_DIR}/services/system/system_main.log"
TEST_MESSAGE="{\"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\", \"level\": \"INFO\", \"service\": \"system\", \"component\": \"init\", \"message\": \"Log system initialized successfully\"}"

echo "$TEST_MESSAGE" >> "$TEST_LOG_FILE"
echo -e "${GREEN}✓ 测试日志已写入: $TEST_LOG_FILE${NC}"

# 5. 检查依赖包
echo -e "\n${YELLOW}5. 检查Python依赖...${NC}"

PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python"
fi

if ! command -v $PYTHON_CMD &> /dev/null; then
    echo -e "${RED}✗ 未找到Python环境${NC}"
    exit 1
fi

echo "使用Python版本: $($PYTHON_CMD --version)"

# 检查必需的包
REQUIRED_PACKAGES=("psutil")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! $PYTHON_CMD -c "import $package" 2>/dev/null; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [[ ${#MISSING_PACKAGES[@]} -gt 0 ]]; then
    echo -e "${YELLOW}需要安装的包: ${MISSING_PACKAGES[*]}${NC}"
    echo "请运行: pip install ${MISSING_PACKAGES[*]}"
else
    echo -e "${GREEN}✓ Python依赖检查通过${NC}"
fi

# 6. 创建定时任务配置
echo -e "\n${YELLOW}6. 创建定时任务配置...${NC}"

CRON_CONFIG_FILE="${PROJECT_ROOT}/scripts/crontab.example"
cat > "$CRON_CONFIG_FILE" << 'EOF'
# AnsFlow 日志系统定时任务配置
# 请根据需要修改时间和路径

# 每小时聚合一次日志
0 * * * * /usr/bin/python3 /Users/creed/Workspace/OpenSource/ansflow/scripts/log_aggregator.py --aggregate

# 每天凌晨2点归档旧日志
0 2 * * * /usr/bin/python3 /Users/creed/Workspace/OpenSource/ansflow/scripts/log_aggregator.py --archive

# 每天凌晨3点生成日志报告
0 3 * * * /usr/bin/python3 /Users/creed/Workspace/OpenSource/ansflow/scripts/log_aggregator.py --report

# 每周日凌晨4点执行完整维护
0 4 * * 0 /usr/bin/python3 /Users/creed/Workspace/OpenSource/ansflow/scripts/log_aggregator.py --all
EOF

echo -e "${GREEN}✓ 定时任务配置已创建: $CRON_CONFIG_FILE${NC}"
echo -e "${YELLOW}  要启用定时任务，请运行: crontab $CRON_CONFIG_FILE${NC}"

# 7. 创建监控脚本
echo -e "\n${YELLOW}7. 创建系统监控脚本...${NC}"

MONITOR_SCRIPT="${PROJECT_ROOT}/scripts/system_monitor.py"
cat > "$MONITOR_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""
系统监控启动脚本
"""
import sys
import os
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from monitoring.system_logging_config import get_system_logger
    
    def main():
        logger = get_system_logger()
        
        print("启动系统监控...")
        
        while True:
            try:
                # 收集系统指标
                logger.log_system_metrics()
                
                # 收集Docker指标
                logger.log_docker_metrics()
                
                # 等待60秒
                time.sleep(60)
                
            except KeyboardInterrupt:
                print("监控已停止")
                break
            except Exception as e:
                logger.log_error(f"监控异常: {e}", error_type="monitor")
                time.sleep(10)  # 出错后等待10秒再继续
                
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保安装了必要的依赖包")
    sys.exit(1)
EOF

chmod +x "$MONITOR_SCRIPT"
echo -e "${GREEN}✓ 系统监控脚本已创建: $MONITOR_SCRIPT${NC}"

# 8. 生成使用指南
echo -e "\n${YELLOW}8. 生成使用指南...${NC}"

USAGE_GUIDE="${PROJECT_ROOT}/docs/日志系统使用指南_v2.md"
cat > "$USAGE_GUIDE" << 'EOF'
# AnsFlow 统一日志系统使用指南 v2.0

## 1. 目录结构

```
logs/
├── services/           # 按服务分类的日志文件
│   ├── django/        # Django服务日志
│   ├── fastapi/       # FastAPI服务日志
│   └── system/        # 系统监控日志
├── aggregated/        # 聚合后的日志文件
└── archived/          # 归档的历史日志
```

## 2. 日志文件命名规范

- 主日志: `{service}_main.log`
- 错误日志: `{service}_error.log`
- 访问日志: `{service}_access.log`
- 性能日志: `{service}_performance.log`

## 3. 配置文件说明

### 3.1 环境配置 (.env.logging)
```bash
LOG_DIR=/path/to/logs     # 日志目录
LOG_LEVEL=INFO            # 日志级别
LOG_FORMAT=json           # 日志格式 (json/text)
LOG_RETENTION_DAYS=30     # 保留天数
```

## 4. 使用方法

### 4.1 Django服务
```python
from common.django_logging_config import get_logger, log_performance

# 获取日志器
logger = get_logger('ansflow.views', component='user_management')
logger.info("用户登录", extra={'user_id': 123, 'ip': '192.168.1.1'})

# 性能监控装饰器
@log_performance()
def slow_function():
    # 耗时操作
    pass
```

### 4.2 FastAPI服务
```python
from core.fastapi_logging_config import get_logger, log_performance

# 获取结构化日志器
logger = get_logger('ansflow.api', component='auth')
logger.info("API调用", user_id=123, endpoint="/api/users")

# 异步性能监控
@log_performance()
async def api_handler():
    # API处理逻辑
    pass
```

### 4.3 系统监控
```python
from monitoring.system_logging_config import get_system_logger

# 获取系统监控日志器
system_logger = get_system_logger()

# 记录系统指标
system_logger.log_system_metrics()

# 记录Docker指标
system_logger.log_docker_metrics()
```

## 5. 日志聚合和归档

### 5.1 手动执行
```bash
# 聚合日志
python3 scripts/log_aggregator.py --aggregate

# 归档旧日志
python3 scripts/log_aggregator.py --archive

# 生成报告
python3 scripts/log_aggregator.py --report

# 执行所有操作
python3 scripts/log_aggregator.py --all
```

### 5.2 定时任务
```bash
# 安装定时任务
crontab scripts/crontab.example
```

## 6. 启动系统监控
```bash
# 启动系统监控
python3 scripts/system_monitor.py
```

## 7. 日志查询示例

### 7.1 查看今日错误日志
```bash
python3 scripts/log_aggregator.py --aggregate
cat logs/aggregated/errors_only_$(date +%Y%m%d).log | jq '.'
```

### 7.2 查看性能日志
```bash
cat logs/aggregated/performance_combined_$(date +%Y%m%d).log | jq '.response_time_ms'
```

### 7.3 查看特定服务日志
```bash
tail -f logs/services/django/django_main.log | jq '.'
```

## 8. 故障排查

### 8.1 日志文件不生成
- 检查目录权限
- 检查环境变量配置
- 查看控制台错误信息

### 8.2 日志格式错误
- 验证LOG_FORMAT环境变量
- 检查JSON格式化器配置

### 8.3 性能问题
- 调整LOG_LEVEL到WARNING减少日志量
- 启用日志压缩和归档
- 检查磁盘空间

## 9. 最佳实践

1. **结构化日志**: 使用JSON格式便于查询分析
2. **组件标识**: 为每个日志器指定component
3. **敏感数据**: 避免记录密码、令牌等敏感信息
4. **性能监控**: 对关键功能使用性能装饰器
5. **定期维护**: 配置自动归档和清理任务
EOF

echo -e "${GREEN}✓ 使用指南已生成: $USAGE_GUIDE${NC}"

# 9. 最终检查
echo -e "\n${YELLOW}9. 执行最终检查...${NC}"

echo "检查目录结构:"
find "$LOG_DIR" -type d | head -10

echo -e "\n检查配置文件:"
if [[ -f "$ENV_LOGGING_FILE" ]]; then
    echo -e "${GREEN}✓ $ENV_LOGGING_FILE${NC}"
else
    echo -e "${RED}✗ $ENV_LOGGING_FILE${NC}"
fi

echo -e "\n检查脚本文件:"
for script in "$AGGREGATOR_SCRIPT" "$MONITOR_SCRIPT"; do
    if [[ -x "$script" ]]; then
        echo -e "${GREEN}✓ $script${NC}"
    else
        echo -e "${RED}✗ $script${NC}"
    fi
done

# 10. 完成
echo -e "\n${GREEN}=== 日志系统初始化完成 ===${NC}"
echo -e "${BLUE}下一步操作:${NC}"
echo "1. 检查并修改配置文件: $ENV_LOGGING_FILE"
echo "2. 安装Python依赖: pip install psutil docker"
echo "3. 配置定时任务: crontab $CRON_CONFIG_FILE"
echo "4. 启动系统监控: python3 $MONITOR_SCRIPT"
echo "5. 查看使用指南: $USAGE_GUIDE"

echo -e "\n${YELLOW}测试日志系统:${NC}"
echo "python3 $AGGREGATOR_SCRIPT --report"
