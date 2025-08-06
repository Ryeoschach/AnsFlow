#!/usr/bin/env python3
"""
AnsFlow 统一日志系统集成测试脚本
测试Django、FastAPI、Celery服务的日志是否都能写入Redis实时日志系统
"""

import os
import sys
import time
import json
import requests
import redis
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'backend' / 'django_service'))

# Django配置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

try:
    import django
    django.setup()
    from settings_management.models import GlobalConfig
    HAS_DJANGO = True
except Exception as e:
    print(f"⚠️  Django导入失败: {e}")
    HAS_DJANGO = False


class UnifiedLoggingTester:
    """统一日志系统测试器"""
    
    def __init__(self):
        self.redis_client = None
        self.test_results = {}
        
    def connect_redis(self) -> bool:
        """连接Redis"""
        try:
            # 从数据库获取Redis配置
            if HAS_DJANGO:
                try:
                    redis_host = GlobalConfig.objects.get(key='REDIS_HOST').value
                    redis_port = int(GlobalConfig.objects.get(key='REDIS_PORT').value)
                    redis_db = int(GlobalConfig.objects.get(key='REDIS_DB').value)
                except:
                    redis_host = 'localhost'
                    redis_port = 6379
                    redis_db = 5
            else:
                redis_host = 'localhost'
                redis_port = 6379
                redis_db = 5
                
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True
            )
            
            # 测试连接
            self.redis_client.ping()
            print(f"✅ Redis连接成功 - {redis_host}:{redis_port}/{redis_db}")
            return True
            
        except Exception as e:
            print(f"❌ Redis连接失败: {e}")
            return False
    
    def clear_test_logs(self):
        """清理测试日志"""
        try:
            # 删除测试相关的日志条目
            stream_name = 'ansflow:logs'
            
            # 获取最近的日志条目
            entries = self.redis_client.xrange(stream_name, count=100)
            
            deleted_count = 0
            for entry_id, fields in entries:
                if 'message' in fields:
                    message = fields['message']
                    # 如果是测试消息，删除它
                    if 'TEST_LOG_INTEGRATION' in message:
                        try:
                            self.redis_client.xdel(stream_name, entry_id)
                            deleted_count += 1
                        except:
                            pass
            
            if deleted_count > 0:
                print(f"🧹 清理了 {deleted_count} 条测试日志")
                
        except Exception as e:
            print(f"⚠️  清理测试日志失败: {e}")
    
    def test_django_logging(self) -> bool:
        """测试Django服务日志"""
        try:
            print("\n🧪 测试Django服务日志...")
            
            # 发送测试请求到Django服务
            test_url = "http://localhost:8000/api/test-logging/"
            test_data = {
                "message": "TEST_LOG_INTEGRATION_DJANGO",
                "level": "info"
            }
            
            response = requests.post(test_url, json=test_data, timeout=5)
            
            if response.status_code == 200:
                print("✅ Django日志测试请求发送成功")
                self.test_results['django'] = True
                return True
            else:
                print(f"❌ Django日志测试请求失败: {response.status_code}")
                self.test_results['django'] = False
                return False
                
        except Exception as e:
            print(f"❌ Django日志测试失败: {e}")
            self.test_results['django'] = False
            return False
    
    def test_fastapi_logging(self) -> bool:
        """测试FastAPI服务日志"""
        try:
            print("\n🧪 测试FastAPI服务日志...")
            
            # 发送测试请求到FastAPI服务
            test_url = "http://localhost:8001/test-logging/"
            test_data = {
                "message": "TEST_LOG_INTEGRATION_FASTAPI",
                "level": "info"
            }
            
            response = requests.post(test_url, json=test_data, timeout=5)
            
            if response.status_code == 200:
                print("✅ FastAPI日志测试请求发送成功")
                self.test_results['fastapi'] = True
                return True
            else:
                print(f"❌ FastAPI日志测试请求失败: {response.status_code}")
                self.test_results['fastapi'] = False
                return False
                
        except Exception as e:
            print(f"❌ FastAPI日志测试失败: {e}")
            self.test_results['fastapi'] = False
            return False
    
    def test_celery_logging(self) -> bool:
        """测试Celery服务日志"""
        try:
            print("\n🧪 测试Celery服务日志...")
            
            # 发送测试任务到Celery
            test_url = "http://localhost:8000/api/test-celery-logging/"
            test_data = {
                "message": "TEST_LOG_INTEGRATION_CELERY",
                "task_name": "test_logging_task"
            }
            
            response = requests.post(test_url, json=test_data, timeout=10)
            
            if response.status_code == 200:
                print("✅ Celery日志测试任务发送成功")
                self.test_results['celery'] = True
                return True
            else:
                print(f"❌ Celery日志测试任务失败: {response.status_code}")
                self.test_results['celery'] = False
                return False
                
        except Exception as e:
            print(f"❌ Celery日志测试失败: {e}")
            self.test_results['celery'] = False
            return False
    
    def verify_logs_in_redis(self) -> dict:
        """验证Redis中的日志"""
        try:
            print("\n🔍 验证Redis中的日志...")
            
            stream_name = 'ansflow:logs'
            
            # 等待日志写入
            time.sleep(3)
            
            # 获取最近的日志条目
            entries = self.redis_client.xrevrange(stream_name, count=50)
            
            found_services = set()
            test_logs = []
            
            for entry_id, fields in entries:
                try:
                    if 'message' in fields:
                        message_data = json.loads(fields['message'])
                        
                        # 检查是否是测试日志
                        if 'TEST_LOG_INTEGRATION' in str(message_data):
                            test_logs.append(message_data)
                            
                            # 获取服务名
                            service = message_data.get('service', 'unknown')
                            if service:
                                found_services.add(service)
                                
                except json.JSONDecodeError:
                    # 尝试直接检查消息
                    message = fields.get('message', '')
                    if 'TEST_LOG_INTEGRATION' in message:
                        # 从消息中提取服务信息
                        if 'DJANGO' in message:
                            found_services.add('django_service')
                        elif 'FASTAPI' in message:
                            found_services.add('fastapi_service')
                        elif 'CELERY' in message:
                            found_services.add('celery')
            
            print(f"📊 在Redis中找到的服务日志: {list(found_services)}")
            print(f"📝 测试日志条目数量: {len(test_logs)}")
            
            return {
                'found_services': list(found_services),
                'test_log_count': len(test_logs),
                'test_logs': test_logs[:5]  # 只返回前5条用于显示
            }
            
        except Exception as e:
            print(f"❌ 验证Redis日志失败: {e}")
            return {
                'found_services': [],
                'test_log_count': 0,
                'test_logs': []
            }
    
    def generate_report(self, redis_results: dict):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📋 AnsFlow 统一日志系统集成测试报告")
        print("="*60)
        
        # 服务测试结果
        print("\n🔧 服务测试结果:")
        for service, result in self.test_results.items():
            status = "✅ 成功" if result else "❌ 失败"
            print(f"   {service.upper():<10} - {status}")
        
        # Redis验证结果
        print(f"\n📊 Redis日志验证结果:")
        print(f"   找到的服务日志: {redis_results['found_services']}")
        print(f"   测试日志数量: {redis_results['test_log_count']}")
        
        # 期望vs实际
        expected_services = {'django_service', 'fastapi_service', 'celery'}
        found_services = set(redis_results['found_services'])
        
        missing_services = expected_services - found_services
        if missing_services:
            print(f"\n⚠️  缺失的服务日志: {list(missing_services)}")
            print("   可能的原因:")
            for service in missing_services:
                if service == 'fastapi_service':
                    print("   - FastAPI服务未正确集成统一日志系统")
                elif service == 'celery':
                    print("   - Celery服务未正确配置日志处理器")
                elif service == 'django_service':
                    print("   - Django服务日志配置异常")
        else:
            print("\n🎉 所有服务日志都已正确集成到Redis实时日志系统!")
        
        # 总体状态
        all_tests_passed = all(self.test_results.values())
        all_services_found = len(missing_services) == 0
        
        overall_status = "✅ 通过" if (all_tests_passed and all_services_found) else "❌ 失败"
        print(f"\n🎯 总体集成状态: {overall_status}")
        
        if redis_results['test_logs']:
            print(f"\n📝 示例日志条目:")
            for i, log in enumerate(redis_results['test_logs'][:3], 1):
                print(f"   {i}. {log}")
        
        print("="*60)


def main():
    """主函数"""
    print("🚀 启动AnsFlow统一日志系统集成测试")
    
    tester = UnifiedLoggingTester()
    
    # 连接Redis
    if not tester.connect_redis():
        return
    
    # 清理旧的测试日志
    tester.clear_test_logs()
    
    # 测试各个服务
    print("\n📋 开始测试各服务日志集成...")
    
    tester.test_django_logging()
    tester.test_fastapi_logging()
    tester.test_celery_logging()
    
    # 验证Redis中的日志
    redis_results = tester.verify_logs_in_redis()
    
    # 生成报告
    tester.generate_report(redis_results)


if __name__ == "__main__":
    main()
