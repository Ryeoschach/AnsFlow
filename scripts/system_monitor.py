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
