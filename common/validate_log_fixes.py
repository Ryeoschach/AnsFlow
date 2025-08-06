#!/usr/bin/env python3
"""
AnsFlow 日志修复验证脚本
验证FastAPI日志Redis集成和历史日志同步是否正常工作
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import logging
import json

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'backend' / 'django_service'))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
import django
django.setup()

from common.unified_log_connector import UnifiedLogConnector, LogEntry, get_config_from_db


class LogFixValidation:
    """日志修复验证类"""
    
    def __init__(self):
        self.config = get_config_from_db()
        self.connector = None
        
    async def initialize(self):
        """初始化连接器"""
        self.connector = UnifiedLogConnector(self.config)
        await self.connector.initialize()
        print("✅ 统一日志连接器初始化完成")
        
    async def test_fastapi_redis_integration(self):
        """测试FastAPI Redis集成"""
        print("\n🔍 测试FastAPI Redis集成...")
        
        try:
            # 模拟FastAPI日志写入
            test_log = LogEntry(
                id=f"fastapi-test-{int(datetime.now().timestamp() * 1000)}",
                timestamp=datetime.now().replace(tzinfo=datetime.now().astimezone().tzinfo),
                level='INFO',
                service='fastapi',
                component='test',
                module='validation',
                message='FastAPI Redis集成测试日志',
                execution_id=9999
            )
            
            # 写入Redis Stream
            message_id = await self.connector.write_realtime_log(test_log)
            print(f"✅ FastAPI测试日志写入Redis Stream成功: {message_id}")
            
            # 验证能否从Stream中读取
            messages = await self.connector.redis_client.xrevrange(
                'ansflow:logs:stream', 
                count=10
            )
            
            fastapi_logs = [
                msg for msg in messages 
                if msg[1].get('service') == 'fastapi'
            ]
            
            print(f"✅ Redis Stream中FastAPI日志数量: {len(fastapi_logs)}")
            
            return len(fastapi_logs) > 0
            
        except Exception as e:
            print(f"❌ FastAPI Redis集成测试失败: {e}")
            return False
            
    async def test_historical_sync(self):
        """测试历史日志同步"""
        print("\n🔍 测试历史日志同步...")
        
        try:
            # 查询历史日志总数
            historical_logs = await self.connector.query_historical_logs(limit=1000)
            total_count = len(historical_logs)
            print(f"📊 历史日志总数: {total_count}")
            
            # 按服务分组统计
            service_stats = {}
            for log in historical_logs:
                service = log.service
                service_stats[service] = service_stats.get(service, 0) + 1
                
            print("📈 按服务分组统计:")
            for service, count in service_stats.items():
                print(f"   {service}: {count} 条日志")
                
            # 检查是否有FastAPI历史日志
            fastapi_historical = await self.connector.query_historical_logs(
                service='fastapi', 
                limit=100
            )
            
            print(f"✅ FastAPI历史日志数量: {len(fastapi_historical)}")
            
            return total_count > 24  # 应该超过原来的24条测试数据
            
        except Exception as e:
            print(f"❌ 历史日志同步测试失败: {e}")
            return False
            
    async def test_realtime_stream(self):
        """测试实时日志流"""
        print("\n🔍 测试实时日志流...")
        
        try:
            # 获取最近的实时日志
            messages = await self.connector.redis_client.xrevrange(
                'ansflow:logs:stream',
                count=20
            )
            
            print(f"📡 Redis Stream中日志总数: {len(messages)}")
            
            # 按服务分组
            service_counts = {}
            for msg_id, fields in messages:
                service = fields.get('service', 'unknown')
                service_counts[service] = service_counts.get(service, 0) + 1
                
            print("📊 实时日志按服务分组:")
            for service, count in service_counts.items():
                print(f"   {service}: {count} 条")
                
            # 检查是否包含所有预期服务
            expected_services = ['django_service', 'fastapi', 'system']
            has_all_services = all(service in service_counts for service in expected_services)
            
            if has_all_services:
                print("✅ 实时日志流包含所有预期服务")
            else:
                missing = [s for s in expected_services if s not in service_counts]
                print(f"⚠️  缺少服务的日志: {missing}")
                
            return len(messages) > 0
            
        except Exception as e:
            print(f"❌ 实时日志流测试失败: {e}")
            return False
            
    async def test_data_consistency(self):
        """测试数据一致性"""
        print("\n🔍 测试数据一致性...")
        
        try:
            # 创建一个测试日志并同步到所有存储
            test_log = LogEntry(
                id=f"consistency-test-{int(datetime.now().timestamp() * 1000)}",
                timestamp=datetime.now().replace(tzinfo=datetime.now().astimezone().tzinfo),
                level='INFO',
                service='test-validation',
                component='consistency',
                module='validation',
                message='数据一致性测试日志'
            )
            
            # 同步到所有存储系统
            await self.connector.sync_log_entry(test_log)
            print("✅ 日志已同步到所有存储系统")
            
            # 等待一秒确保数据写入
            await asyncio.sleep(1)
            
            # 验证一致性
            consistency = await self.connector.verify_data_consistency(test_log.id)
            print(f"📋 一致性检查结果: {consistency}")
            
            return consistency['redis_stream'] and consistency['mysql_historical']
            
        except Exception as e:
            print(f"❌ 数据一致性测试失败: {e}")
            return False
            
    async def generate_summary_report(self):
        """生成修复总结报告"""
        print("\n📋 生成修复总结报告...")
        
        try:
            # Redis Stream统计
            stream_messages = await self.connector.redis_client.xlen('ansflow:logs:stream')
            
            # 历史日志统计
            historical_logs = await self.connector.query_historical_logs(limit=5000)
            historical_count = len(historical_logs)
            
            # 按服务和时间统计
            service_stats = {}
            recent_24h_count = 0
            now = datetime.now()
            
            for log in historical_logs:
                service = log.service
                service_stats[service] = service_stats.get(service, 0) + 1
                
                # 计算24小时内的日志
                time_diff = now - log.timestamp
                if time_diff.total_seconds() < 24 * 3600:
                    recent_24h_count += 1
                    
            report = {
                'timestamp': datetime.now().isoformat(),
                'redis_stream': {
                    'total_messages': stream_messages,
                    'status': '正常' if stream_messages > 0 else '异常'
                },
                'historical_logs': {
                    'total_count': historical_count,
                    'recent_24h': recent_24h_count,
                    'service_distribution': service_stats,
                    'status': '正常' if historical_count > 50 else '数据较少'
                },
                'data_consistency': {
                    'redis_mysql_sync': '已建立' if historical_count > 24 else '待完善',
                    'fastapi_integration': 'FastAPI' in service_stats,
                    'django_integration': 'django_service' in service_stats
                }
            }
            
            print("\n" + "="*60)
            print("📊 ANSFLOW 统一日志修复总结报告")
            print("="*60)
            print(f"生成时间: {report['timestamp']}")
            print(f"\n🔄 Redis Stream状态: {report['redis_stream']['status']}")
            print(f"   消息总数: {report['redis_stream']['total_messages']}")
            print(f"\n💾 历史日志状态: {report['historical_logs']['status']}")
            print(f"   总记录数: {report['historical_logs']['total_count']}")
            print(f"   24小时内: {report['historical_logs']['recent_24h']}")
            print(f"\n📈 服务分布:")
            for service, count in service_stats.items():
                print(f"   {service}: {count} 条")
            print(f"\n🔗 数据一致性:")
            print(f"   Redis-MySQL同步: {report['data_consistency']['redis_mysql_sync']}")
            print(f"   FastAPI集成: {'✅' if report['data_consistency']['fastapi_integration'] else '❌'}")
            print(f"   Django集成: {'✅' if report['data_consistency']['django_integration'] else '❌'}")
            print("="*60)
            
            return report
            
        except Exception as e:
            print(f"❌ 生成报告失败: {e}")
            return None
            
    async def run_validation(self):
        """运行所有验证测试"""
        print("🚀 开始AnsFlow日志修复验证...\n")
        
        await self.initialize()
        
        results = {
            'fastapi_redis': await self.test_fastapi_redis_integration(),
            'historical_sync': await self.test_historical_sync(),
            'realtime_stream': await self.test_realtime_stream(),
            'data_consistency': await self.test_data_consistency()
        }
        
        # 生成总结报告
        report = await self.generate_summary_report()
        
        # 总结验证结果
        print(f"\n🏁 验证完成！")
        print("测试结果:")
        for test_name, passed in results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"   {test_name}: {status}")
            
        overall_success = all(results.values())
        if overall_success:
            print("\n🎉 所有测试通过！日志修复成功。")
        else:
            failed_tests = [name for name, passed in results.items() if not passed]
            print(f"\n⚠️  以下测试失败: {', '.join(failed_tests)}")
            
        return overall_success, report
        
    async def close(self):
        """关闭连接"""
        if self.connector:
            await self.connector.close()


async def main():
    """主函数"""
    validator = LogFixValidation()
    try:
        success, report = await validator.run_validation()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ 验证过程异常: {e}")
        return 1
    finally:
        await validator.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
