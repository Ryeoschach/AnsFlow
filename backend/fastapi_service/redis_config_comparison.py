#!/usr/bin/env python3
"""
演示Redis实时通道开启/关闭的配置和影响
"""
import os
from pathlib import Path

def show_redis_enabled_config():
    """显示启用Redis时的配置"""
    print("🟢 启用Redis实时通道的配置:")
    print("=" * 50)
    
    print("\n📋 环境变量配置:")
    config = {
        "LOGGING_ENABLE_REDIS": "true",
        "LOGGING_REDIS_HOST": "localhost", 
        "LOGGING_REDIS_PORT": "6379",
        "LOGGING_REDIS_DB": "5",
        "LOGGING_LEVEL": "INFO"
    }
    
    for key, value in config.items():
        print(f"   {key}={value}")
    
    print(f"\n🏗️ Django日志处理器配置:")
    print("""
    LOGGING = {
        'handlers': {
            'redis_handler': {
                'class': 'common.logging_config.AnsFlowRedisHandler',
                'stream_name': 'ansflow:logs:stream',
                'redis_db': 5,
            },
            'file_handler': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/logs/services/django/django_service.log',
            }
        },
        'loggers': {
            'ansflow.django_service': {
                'handlers': ['redis_handler', 'file_handler', 'console'],
                'level': 'INFO',
            }
        }
    }""")
    
    print(f"\n🚀 FastAPI日志处理器配置:")
    print("""
    # FastAPI独立日志系统
    logging_config = {
        'enable_redis': True,
        'redis_host': 'localhost',
        'redis_port': 6379,
        'redis_db': 5,
        'handlers': [
            'FastAPIRedisHandler',    # -> Redis Stream
            'RotatingFileHandler',    # -> 文件
            'StreamHandler'           # -> 控制台
        ]
    }""")

def show_redis_disabled_config():
    """显示禁用Redis时的配置"""
    print("\n\n🔴 禁用Redis实时通道的配置:")
    print("=" * 50)
    
    print("\n📋 环境变量配置:")
    config = {
        "LOGGING_ENABLE_REDIS": "false",  # 关键差异
        "LOGGING_REDIS_HOST": "localhost", 
        "LOGGING_REDIS_PORT": "6379",
        "LOGGING_REDIS_DB": "5",
        "LOGGING_LEVEL": "INFO"
    }
    
    for key, value in config.items():
        status = " ❌ 已禁用" if key == "LOGGING_ENABLE_REDIS" else ""
        print(f"   {key}={value}{status}")
    
    print(f"\n🏗️ Django日志处理器配置:")
    print("""
    LOGGING = {
        'handlers': {
            'file_handler': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/logs/services/django/django_service.log',
            }
            # ❌ 没有redis_handler
        },
        'loggers': {
            'ansflow.django_service': {
                'handlers': ['file_handler', 'console'],  # ❌ 移除redis_handler
                'level': 'INFO',
            }
        }
    }""")
    
    print(f"\n🚀 FastAPI日志处理器配置:")
    print("""
    # FastAPI独立日志系统
    logging_config = {
        'enable_redis': False,  # ❌ 关键差异
        'redis_host': 'localhost',
        'redis_port': 6379, 
        'redis_db': 5,
        'handlers': [
            # ❌ 没有FastAPIRedisHandler
            'RotatingFileHandler',    # -> 文件
            'StreamHandler'           # -> 控制台
        ]
    }""")

def show_data_flow_comparison():
    """显示数据流对比"""
    print("\n\n📊 数据流对比:")
    print("=" * 50)
    
    print("\n🟢 启用Redis时的数据路径:")
    print("""
    应用日志 -> JSON格式化 -> [Redis Stream] -> WebSocket实时推送
                           -> [本地文件] -> 文件备份
                           -> [MySQL数据库] <- Redis同步服务
    
    实时查询: Redis Stream (毫秒级)
    历史查询: MySQL数据库 + 索引优化
    文件备份: 灾难恢复和审计
    """)
    
    print("\n🔴 禁用Redis时的数据路径:")
    print("""
    应用日志 -> JSON格式化 -> [本地文件] -> 文件监控 -> WebSocket推送
                                    -> 文件解析 -> [MySQL数据库]
    
    实时查询: 文件监控 (秒级延迟)
    历史查询: MySQL数据库 (可能数据不完整)
    文件依赖: 单点故障风险
    """)

def show_performance_impact():
    """显示性能影响"""
    print("\n\n⚡ 性能影响分析:")
    print("=" * 50)
    
    print("\n🟢 启用Redis的性能特征:")
    performance_redis = {
        "实时日志延迟": "< 10ms",
        "查询响应时间": "< 100ms (Redis) + < 500ms (MySQL)",
        "系统资源占用": "中等 (Redis内存 + MySQL磁盘)",
        "并发处理能力": "高 (Redis支持高并发)",
        "数据一致性": "强 (事务保证)",
        "故障恢复": "快速 (Redis持久化 + MySQL备份)"
    }
    
    for metric, value in performance_redis.items():
        print(f"   • {metric}: {value}")
    
    print("\n🔴 禁用Redis的性能特征:")
    performance_file = {
        "实时日志延迟": "1-5s (文件轮询)",
        "查询响应时间": "> 1s (文件读取 + 解析)",
        "系统资源占用": "低 (仅文件I/O + MySQL)",
        "并发处理能力": "受限 (文件锁竞争)",
        "数据一致性": "弱 (解析可能出错)",
        "故障恢复": "依赖文件完整性"
    }
    
    for metric, value in performance_file.items():
        print(f"   • {metric}: {value}")

def show_query_functionality_impact():
    """显示查询功能的具体影响"""
    print("\n\n🔍 查询功能具体影响:")
    print("=" * 50)
    
    features = [
        ("实时日志流", "✅ 毫秒级推送", "⚠️ 秒级延迟"),
        ("历史日志查询", "✅ 完整数据", "✅ 基本功能"),
        ("结构化搜索", "✅ 字段精确查询", "⚠️ 文本模糊搜索"),
        ("时间范围查询", "✅ 高性能索引", "✅ 基本支持"),
        ("级别过滤", "✅ 即时过滤", "✅ 基本过滤"),
        ("服务过滤", "✅ 精确匹配", "✅ 基本匹配"),
        ("关键词搜索", "✅ 全文索引", "⚠️ 简单匹配"),
        ("执行ID追踪", "✅ 关联查询", "❌ 无法追踪"),
        ("异常信息保留", "✅ 完整堆栈", "⚠️ 可能截断"),
        ("性能分析", "✅ 实时指标", "⚠️ 有限分析"),
        ("日志聚合", "✅ 高性能统计", "⚠️ 慢查询"),
        ("导出功能", "✅ 多格式导出", "✅ 基本导出")
    ]
    
    print(f"{'功能':15s} | {'Redis启用':15s} | {'Redis禁用':15s}")
    print("-" * 50)
    
    for feature, redis_status, file_status in features:
        print(f"{feature:15s} | {redis_status:15s} | {file_status:15s}")

if __name__ == "__main__":
    show_redis_enabled_config()
    show_redis_disabled_config()
    show_data_flow_comparison()
    show_performance_impact()
    show_query_functionality_impact()
    
    print("\n\n💡 总结建议:")
    print("=" * 50)
    print("✅ 生产环境推荐: 启用Redis实时通道")
    print("   - 数据完整性和实时性更佳")
    print("   - 支持高级查询和分析功能")
    print("   - 更好的性能和扩展性")
    
    print("\n⚠️ 开发/测试环境: 可选择禁用Redis")
    print("   - 降低环境复杂度")
    print("   - 减少资源占用")
    print("   - 基本功能仍可用")
    
    print("\n🔧 切换方式:")
    print("   - 修改环境变量: LOGGING_ENABLE_REDIS=true/false")
    print("   - 重启相关服务生效")
    print("   - 数据会自动适配新的存储方式")
