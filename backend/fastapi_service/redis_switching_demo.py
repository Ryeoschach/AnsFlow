#!/usr/bin/env python3
"""
演示如何动态切换Redis实时通道开关
"""
import os
import subprocess
import time

def show_current_status():
    """显示当前Redis状态"""
    redis_enabled = os.getenv('LOGGING_ENABLE_REDIS', 'true').lower() == 'true'
    
    print(f"🔍 当前Redis实时通道状态:")
    print(f"   LOGGING_ENABLE_REDIS = {os.getenv('LOGGING_ENABLE_REDIS', 'true')}")
    print(f"   状态: {'🟢 启用' if redis_enabled else '🔴 禁用'}")
    
    return redis_enabled

def simulate_redis_disabled_test():
    """模拟禁用Redis的测试"""
    print("\n🧪 模拟禁用Redis实时通道的测试:")
    print("=" * 50)
    
    # 创建临时配置
    test_config = """
# 禁用Redis的配置示例
class StandaloneFastAPILogging:
    def __init__(self):
        self.config = {
            'enable_redis': False,  # ❌ 禁用Redis
            'redis_host': 'localhost',
            'redis_port': 6379,
            'redis_db': 5,
        }
    
    def setup_logging(self):
        # 只启用文件和控制台处理器
        handlers = [
            'RotatingFileHandler',  # -> 文件
            'StreamHandler'         # -> 控制台
        ]
        # ❌ 不包含FastAPIRedisHandler
        return self._create_logger(handlers)
"""
    
    print("📋 禁用Redis时的代码逻辑:")
    print(test_config)
    
    print("\n📊 影响分析:")
    print("   ✅ 优点: 降低系统依赖，减少资源占用")
    print("   ❌ 缺点: 失去实时性，数据结构化程度降低")
    print("   ⚠️ 风险: 文件I/O瓶颈，解析错误风险")

def show_switching_method():
    """显示切换方法"""
    print("\n\n🔧 Redis实时通道切换方法:")
    print("=" * 50)
    
    print("📝 方法1: 环境变量切换")
    print("   # 启用Redis")
    print("   export LOGGING_ENABLE_REDIS=true")
    print("   # 禁用Redis") 
    print("   export LOGGING_ENABLE_REDIS=false")
    
    print("\n📝 方法2: 配置文件修改")
    print("   # .env文件")
    print("   LOGGING_ENABLE_REDIS=false")
    
    print("\n📝 方法3: 运行时动态切换")
    print("""
   # FastAPI服务中
   if os.getenv('LOGGING_ENABLE_REDIS', 'true').lower() == 'true':
       logging_system.enable_redis_handler()
   else:
       logging_system.disable_redis_handler()
""")

def demonstrate_impact_on_queries():
    """演示对查询功能的影响"""
    print("\n\n📊 对查询功能的实际影响演示:")
    print("=" * 50)
    
    # 模拟查询性能对比
    scenarios = [
        {
            "name": "实时日志获取",
            "redis_enabled": "< 10ms (Redis Stream直接读取)",
            "redis_disabled": "1-5s (文件轮询 + 解析)"
        },
        {
            "name": "历史日志搜索",
            "redis_enabled": "< 500ms (MySQL索引 + Redis缓存)",
            "redis_disabled": "> 1s (纯MySQL查询)"
        },
        {
            "name": "结构化字段查询",
            "redis_enabled": "支持 execution_id, trace_id 等字段精确查询",
            "redis_disabled": "依赖文本解析，可能丢失结构化信息"
        },
        {
            "name": "异常堆栈追踪",
            "redis_enabled": "完整保留异常信息和上下文",
            "redis_disabled": "可能被文件大小限制截断"
        }
    ]
    
    print(f"{'查询场景':20s} | {'Redis启用':30s} | {'Redis禁用':30s}")
    print("-" * 85)
    
    for scenario in scenarios:
        print(f"{scenario['name']:20s} | {scenario['redis_enabled']:30s} | {scenario['redis_disabled']:30s}")

def show_monitoring_recommendations():
    """显示监控建议"""
    print("\n\n📈 监控和告警建议:")
    print("=" * 50)
    
    print("🟢 Redis启用时的监控指标:")
    print("   • Redis连接状态")
    print("   • Stream长度和增长速率") 
    print("   • Redis内存使用率")
    print("   • WebSocket连接数")
    print("   • 日志同步延迟")
    
    print("\n🔴 Redis禁用时的监控指标:")
    print("   • 文件I/O性能")
    print("   • 文件大小和增长")
    print("   • 解析错误率")
    print("   • MySQL写入性能")
    print("   • 实时推送延迟")
    
    print("\n⚠️ 切换时的注意事项:")
    print("   • 重启服务前备份当前配置")
    print("   • 监控服务启动日志确认切换成功")
    print("   • 验证日志功能正常工作")
    print("   • 必要时可以快速回滚配置")

if __name__ == "__main__":
    show_current_status()
    simulate_redis_disabled_test()
    show_switching_method()
    demonstrate_impact_on_queries()
    show_monitoring_recommendations()
    
    print("\n\n🎯 最终建议:")
    print("=" * 50)
    print("🏭 生产环境: 强烈建议启用Redis")
    print("   - 保证数据完整性和实时性")
    print("   - 支持复杂的日志分析和故障排查")
    
    print("\n🧪 开发/测试环境: 可根据需求选择")
    print("   - 简单场景可禁用Redis降低复杂度")
    print("   - 测试完整功能时建议启用Redis")
    
    print("\n🔄 灵活切换: 支持运行时动态调整")
    print("   - 通过环境变量快速切换")
    print("   - 服务重启后生效")
    print("   - 数据自动适配存储方式")
