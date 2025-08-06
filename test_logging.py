#!/usr/bin/env python3
"""
AnsFlow日志系统测试脚本
用于验证Django和FastAPI日志配置是否正常工作
"""

import os
import sys
import time
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
django_service_path = project_root / 'backend' / 'django_service'
sys.path.insert(0, str(django_service_path))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

def test_django_logging():
    """测试Django日志配置"""
    print("=" * 50)
    print("测试Django日志配置")
    print("=" * 50)
    
    try:
        import django
        django.setup()
        
        # 获取Django日志器
        logger = logging.getLogger('ansflow')
        
        # 测试不同级别的日志
        logger.debug("这是一条调试日志")
        logger.info("这是一条信息日志")
        logger.warning("这是一条警告日志")
        logger.error("这是一条错误日志")
        
        # 测试结构化日志
        logger.info(
            "用户登录",
            extra={
                'user_id': 12345,
                'user_name': 'test_user',
                'ip': '192.168.1.100',
                'action': 'login',
                'labels': ['auth', 'user', 'success']
            }
        )
        
        # 测试敏感数据过滤
        logger.info(
            "处理用户密码",
            extra={
                'user_id': 12345,
                'password': 'secret123456',
                'token': 'abcdef123456',
                'action': 'password_change'
            }
        )
        
        print("✅ Django日志测试完成")
        
    except Exception as e:
        print(f"❌ Django日志测试失败: {e}")


def test_common_logging():
    """测试通用日志配置"""
    print("=" * 50) 
    print("测试通用日志配置")
    print("=" * 50)
    
    try:
        from common.logging_config import AnsFlowLoggingConfig
        
        # 设置日志配置
        config = AnsFlowLoggingConfig()
        logger = config.setup_logging(
            service_name='test_service',
            log_level='DEBUG',
            log_file=project_root / 'logs' / 'test.log'
        )
        
        # 测试日志输出
        logger.debug("通用日志配置 - 调试信息")
        logger.info("通用日志配置 - 信息")
        logger.warning("通用日志配置 - 警告")
        logger.error("通用日志配置 - 错误")
        
        print("✅ 通用日志配置测试完成")
        
    except Exception as e:
        print(f"❌ 通用日志配置测试失败: {e}")


def test_log_files():
    """检查日志文件是否创建"""
    print("=" * 50)
    print("检查日志文件")
    print("=" * 50)
    
    log_dir = project_root / 'logs'
    django_log_dir = django_service_path / 'logs'
    
    print(f"项目日志目录: {log_dir}")
    print(f"Django日志目录: {django_log_dir}")
    
    if log_dir.exists():
        log_files = list(log_dir.glob('*.log'))
        print(f"找到日志文件: {[f.name for f in log_files]}")
    else:
        print("❌ 项目日志目录不存在")
    
    if django_log_dir.exists():
        django_log_files = list(django_log_dir.glob('*.log'))
        print(f"找到Django日志文件: {[f.name for f in django_log_files]}")
    else:
        print("❌ Django日志目录不存在")


def main():
    """主函数"""
    print("🚀 AnsFlow日志系统测试开始")
    
    # 创建日志目录
    (project_root / 'logs').mkdir(exist_ok=True)
    (django_service_path / 'logs').mkdir(exist_ok=True)
    
    # 运行测试
    test_common_logging()
    test_django_logging()
    test_log_files()
    
    print("\n🎉 所有测试完成")


if __name__ == "__main__":
    main()
