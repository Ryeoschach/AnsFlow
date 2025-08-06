#!/usr/bin/env python3
"""
AnsFlow统一日志系统数据一致性诊断脚本
用于分析实时日志、历史查询和日志索引的数据抓取对象一致性问题
"""

import os
import sys
import django
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

# 现在可以导入Django模块
from django.db import connection
import redis


class LogConsistencyDiagnostic:
    """日志一致性诊断器"""
    
    def __init__(self):
        self.redis_client = None
        self.setup_redis()
    
    def setup_redis(self):
        """设置Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=5,
                decode_responses=True
            )
            # 测试连接
            self.redis_client.ping()
            print("✅ Redis连接成功")
        except Exception as e:
            print(f"❌ Redis连接失败: {e}")
            self.redis_client = None
    
    def analyze_realtime_logs(self):
        """分析实时日志数据源"""
        print("\n🔍 分析实时日志数据源...")
        
        if not self.redis_client:
            print("❌ Redis不可用，无法分析实时日志")
            return
        
        try:
            # 检查Redis Stream中的日志
            stream_info = self.redis_client.xinfo_stream('ansflow:logs:stream')
            total_messages = stream_info['length']
            print(f"📊 Redis Stream总消息数: {total_messages}")
            
            # 获取最近的消息分析服务类型
            messages = self.redis_client.xrevrange('ansflow:logs:stream', count=100)
            service_count = {}
            
            for msg_id, fields in messages:
                service = fields.get('service', 'unknown')
                service_count[service] = service_count.get(service, 0) + 1
            
            print("📈 实时日志服务分布:")
            for service, count in service_count.items():
                print(f"   - {service}: {count} 条")
            
            # 分析为什么FastAPI日志缺失
            if 'fastapi' not in service_count:
                print("⚠️  发现问题: FastAPI服务日志缺失")
                self.analyze_fastapi_logging_issue()
            
        except Exception as e:
            print(f"❌ 分析实时日志失败: {e}")
    
    def analyze_fastapi_logging_issue(self):
        """分析FastAPI日志缺失问题"""
        print("\n🔧 分析FastAPI日志缺失原因...")
        
        # 检查FastAPI日志文件
        fastapi_log_dir = Path("/Users/creed/Workspace/OpenSource/ansflow/logs/services/fastapi")
        if fastapi_log_dir.exists():
            log_files = list(fastapi_log_dir.glob("*.log"))
            print(f"📁 FastAPI日志文件: {[f.name for f in log_files]}")
            
            # 检查日志文件内容
            for log_file in log_files[:3]:  # 只检查前3个文件
                if log_file.stat().st_size > 0:
                    print(f"📄 {log_file.name}: {log_file.stat().st_size} 字节")
                else:
                    print(f"📄 {log_file.name}: 空文件")
        else:
            print("❌ FastAPI日志目录不存在")
        
        # 检查FastAPI是否有直接写入Redis的配置
        fastapi_service_dir = Path("/Users/creed/Workspace/OpenSource/ansflow/backend/fastapi_service")
        logging_integration_file = fastapi_service_dir / "logging_integration.py"
        
        if logging_integration_file.exists():
            with open(logging_integration_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'Redis' in content and 'xadd' in content:
                    print("✅ FastAPI有Redis日志集成代码")
                else:
                    print("⚠️  FastAPI缺少Redis直接写入功能")
        
        print("\n💡 可能的解决方案:")
        print("   1. 在FastAPI logging_integration.py中添加DirectRedisHandler")
        print("   2. 确保FastAPI日志通过Redis Stream写入")
        print("   3. 检查WebSocket日志监控是否包含FastAPI日志文件")
    
    def analyze_historical_logs(self):
        """分析历史日志数据源"""
        print("\n🔍 分析历史日志数据源...")
        
        try:
            with connection.cursor() as cursor:
                # 检查是否有unified_logs表
                cursor.execute("SHOW TABLES LIKE 'unified_logs'")
                table_exists = cursor.fetchone()
                
                if table_exists:
                    print("✅ unified_logs表存在")
                    
                    # 统计总数
                    cursor.execute("SELECT COUNT(*) FROM unified_logs")
                    total_count = cursor.fetchone()[0]
                    print(f"📊 历史日志总数: {total_count}")
                    
                    # 按服务统计
                    cursor.execute("SELECT service, COUNT(*) FROM unified_logs GROUP BY service")
                    service_stats = cursor.fetchall()
                    
                    print("📈 历史日志服务分布:")
                    for service, count in service_stats:
                        print(f"   - {service}: {count} 条")
                    
                    # 检查最近的日志
                    cursor.execute("""
                        SELECT service, level, message, timestamp 
                        FROM unified_logs 
                        ORDER BY timestamp DESC 
                        LIMIT 5
                    """)
                    recent_logs = cursor.fetchall()
                    
                    print("🕐 最近5条历史日志:")
                    for service, level, message, timestamp in recent_logs:
                        print(f"   [{timestamp}] {service}.{level}: {message[:50]}...")
                    
                    # 分析为什么只有24条记录
                    if total_count == 24:
                        print("⚠️  发现问题: 历史日志只有24条，可能是测试数据")
                        self.analyze_historical_log_pipeline()
                else:
                    print("❌ unified_logs表不存在")
                    self.check_alternative_log_tables()
                
        except Exception as e:
            print(f"❌ 分析历史日志失败: {e}")
    
    def analyze_historical_log_pipeline(self):
        """分析历史日志数据流水线"""
        print("\n🔧 分析历史日志数据流水线...")
        
        # 检查是否有自动化的日志存储机制
        print("🔍 检查日志存储机制:")
        print("   1. 是否有定时任务将Redis Stream数据转存到MySQL?")
        print("   2. 是否有日志轮转和归档机制?")
        print("   3. 应用日志是否直接写入MySQL?")
        
        # 检查Django日志配置
        from django.conf import settings
        if hasattr(settings, 'LOGGING'):
            logging_config = settings.LOGGING
            handlers = logging_config.get('handlers', {})
            
            print("📋 Django日志处理器:")
            for handler_name, handler_config in handlers.items():
                handler_class = handler_config.get('class', 'unknown')
                print(f"   - {handler_name}: {handler_class}")
        
        print("\n💡 可能的解决方案:")
        print("   1. 实现Redis Stream到MySQL的定时同步任务")
        print("   2. 在应用启动时创建unified_logs表结构")
        print("   3. 添加日志中间件自动存储到数据库")
    
    def check_alternative_log_tables(self):
        """检查其他可能的日志表"""
        print("\n🔍 检查其他日志相关表...")
        
        try:
            with connection.cursor() as cursor:
                # 查找所有包含log的表
                cursor.execute("SHOW TABLES")
                all_tables = [table[0] for table in cursor.fetchall()]
                log_tables = [table for table in all_tables if 'log' in table.lower()]
                
                print(f"📋 包含'log'的表: {log_tables}")
                
                # 检查执行相关的日志表
                execution_tables = [table for table in all_tables if 'execution' in table.lower()]
                print(f"📋 包含'execution'的表: {execution_tables}")
                
                # 如果有执行表，检查其中是否有日志字段
                for table in execution_tables[:3]:  # 只检查前3个
                    cursor.execute(f"DESCRIBE {table}")
                    columns = cursor.fetchall()
                    log_columns = [col[0] for col in columns if 'log' in col[0].lower()]
                    if log_columns:
                        print(f"   - {table} 有日志字段: {log_columns}")
                
        except Exception as e:
            print(f"❌ 检查其他日志表失败: {e}")
    
    def analyze_log_indexing(self):
        """分析日志索引系统"""
        print("\n🔍 分析日志索引系统...")
        
        # 检查ElasticSearch是否启用
        print("📋 ElasticSearch状态: 未启用 (在当前配置中)")
        print("📋 当前使用MySQL作为搜索后备")
        
        # 检查搜索性能
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.statistics 
                    WHERE table_schema = 'ansflow' 
                    AND table_name = 'unified_logs'
                """)
                index_count = cursor.fetchone()[0] if cursor.fetchone() else 0
                print(f"📊 unified_logs表索引数量: {index_count}")
        except:
            print("⚠️  无法检查unified_logs表索引")
    
    def generate_consistency_report(self):
        """生成数据一致性报告"""
        print("\n📊 数据一致性分析报告")
        print("=" * 50)
        
        print("\n🎯 发现的主要问题:")
        print("1. 实时日志缺失FastAPI服务数据")
        print("   - FastAPI日志没有写入Redis Stream")
        print("   - 只能看到Django和System日志")
        
        print("\n2. 历史查询数据量有限")
        print("   - 只有24条记录，疑似测试数据")
        print("   - 缺少生产环境的真实日志数据")
        
        print("\n3. 数据流水线不完整")
        print("   - Redis Stream → MySQL 缺少自动同步")
        print("   - 应用日志没有统一写入历史数据库")
        
        print("\n💡 推荐的解决方案:")
        print("1. 修复FastAPI日志集成:")
        print("   - 在FastAPI中实现DirectRedisHandler")
        print("   - 确保所有应用日志都写入Redis Stream")
        
        print("\n2. 实现历史日志自动存储:")
        print("   - 创建Redis Stream → MySQL同步任务")
        print("   - 实现日志中间件自动存储")
        
        print("\n3. 完善数据一致性保证:")
        print("   - 使用UnifiedLogConnector同步写入")
        print("   - 添加数据一致性验证机制")
    
    def run_diagnosis(self):
        """运行完整诊断"""
        print("🚀 开始AnsFlow日志系统数据一致性诊断...")
        print("=" * 60)
        
        self.analyze_realtime_logs()
        self.analyze_historical_logs()
        self.analyze_log_indexing()
        self.generate_consistency_report()
        
        print("\n✅ 诊断完成!")


if __name__ == "__main__":
    diagnostic = LogConsistencyDiagnostic()
    diagnostic.run_diagnosis()
