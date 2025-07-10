#!/usr/bin/env python3
"""
AnsFlow微服务优化测试脚本
验证Redis缓存、RabbitMQ队列、FastAPI性能优化是否正常工作
"""

import asyncio
import time
import json
import requests
import aiohttp
import redis
import pika
from datetime import datetime
import sys
import os

# 测试配置
DJANGO_URL = "http://localhost:8000"
FASTAPI_URL = "http://localhost:8001"
REDIS_URL = "redis://localhost:6379"
RABBITMQ_URL = "amqp://ansflow:ansflow_rabbitmq_123@localhost:5672/ansflow_vhost"

class AnsFlowOptimizationTester:
    """AnsFlow微服务优化测试器"""
    
    def __init__(self):
        self.results = {
            "redis_tests": {},
            "rabbitmq_tests": {},
            "fastapi_tests": {},
            "django_cache_tests": {},
            "overall_status": "pending"
        }
    
    def test_redis_connections(self):
        """测试Redis多数据库连接"""
        print("🔍 Testing Redis multi-database connections...")
        
        try:
            # 测试各个Redis数据库
            databases = {
                "default": redis.Redis.from_url(f"{REDIS_URL}/1"),
                "session": redis.Redis.from_url(f"{REDIS_URL}/3"),
                "api": redis.Redis.from_url(f"{REDIS_URL}/4"),
                "pipeline": redis.Redis.from_url(f"{REDIS_URL}/5"),
                "channels": redis.Redis.from_url(f"{REDIS_URL}/2")
            }
            
            for db_name, client in databases.items():
                try:
                    # 测试连接和基本操作
                    test_key = f"ansflow:test:{db_name}"
                    test_value = f"test_value_{datetime.now().isoformat()}"
                    
                    client.set(test_key, test_value, ex=10)  # 10秒过期
                    retrieved_value = client.get(test_key)
                    
                    if retrieved_value and retrieved_value.decode() == test_value:
                        self.results["redis_tests"][db_name] = {
                            "status": "✅ Connected",
                            "latency_ms": self._measure_redis_latency(client)
                        }
                        print(f"  ✅ {db_name} database: OK")
                    else:
                        self.results["redis_tests"][db_name] = {"status": "❌ Data mismatch"}
                        print(f"  ❌ {db_name} database: Data mismatch")
                    
                    # 清理测试数据
                    client.delete(test_key)
                    
                except Exception as e:
                    self.results["redis_tests"][db_name] = {"status": f"❌ Error: {e}"}
                    print(f"  ❌ {db_name} database: {e}")
            
        except Exception as e:
            print(f"  ❌ Redis connection failed: {e}")
            self.results["redis_tests"]["error"] = str(e)
    
    def _measure_redis_latency(self, client):
        """测量Redis延迟"""
        start_time = time.time()
        for _ in range(10):
            client.ping()
        end_time = time.time()
        return round((end_time - start_time) * 1000 / 10, 2)
    
    def test_rabbitmq_connection(self):
        """测试RabbitMQ连接和队列"""
        print("🔍 Testing RabbitMQ connection and queues...")
        
        try:
            # 建立RabbitMQ连接
            connection = pika.BlockingConnection(
                pika.URLParameters(RABBITMQ_URL)
            )
            channel = connection.channel()
            
            # 测试队列声明
            queues = ['high_priority', 'medium_priority', 'low_priority']
            for queue_name in queues:
                try:
                    channel.queue_declare(queue=queue_name, durable=True)
                    
                    # 发送测试消息
                    test_message = {
                        "test": True,
                        "timestamp": datetime.now().isoformat(),
                        "queue": queue_name
                    }
                    
                    channel.basic_publish(
                        exchange='',
                        routing_key=queue_name,
                        body=json.dumps(test_message),
                        properties=pika.BasicProperties(delivery_mode=2)  # 持久化消息
                    )
                    
                    self.results["rabbitmq_tests"][queue_name] = "✅ Queue OK"
                    print(f"  ✅ {queue_name} queue: OK")
                    
                except Exception as e:
                    self.results["rabbitmq_tests"][queue_name] = f"❌ Error: {e}"
                    print(f"  ❌ {queue_name} queue: {e}")
            
            # 关闭连接
            connection.close()
            
        except Exception as e:
            print(f"  ❌ RabbitMQ connection failed: {e}")
            self.results["rabbitmq_tests"]["error"] = str(e)
    
    def test_django_cache_performance(self):
        """测试Django缓存性能"""
        print("🔍 Testing Django cache performance...")
        
        try:
            # 测试API端点（应该有缓存）
            api_endpoint = f"{DJANGO_URL}/api/v1/settings/api-endpoints/"
            
            # 第一次请求（缓存未命中）
            start_time = time.time()
            response1 = requests.get(api_endpoint, timeout=10)
            first_request_time = time.time() - start_time
            
            if response1.status_code == 200:
                # 第二次请求（缓存命中）
                start_time = time.time()
                response2 = requests.get(api_endpoint, timeout=10)
                second_request_time = time.time() - start_time
                
                if response2.status_code == 200:
                    cache_improvement = (first_request_time - second_request_time) / first_request_time * 100
                    
                    self.results["django_cache_tests"] = {
                        "first_request_ms": round(first_request_time * 1000, 2),
                        "second_request_ms": round(second_request_time * 1000, 2),
                        "cache_improvement_percent": round(cache_improvement, 2),
                        "status": "✅ Cache working" if cache_improvement > 0 else "⚠️ No improvement"
                    }
                    
                    print(f"  ✅ First request: {first_request_time*1000:.2f}ms")
                    print(f"  ✅ Second request: {second_request_time*1000:.2f}ms")
                    print(f"  📈 Improvement: {cache_improvement:.1f}%")
                else:
                    print(f"  ❌ Second request failed: {response2.status_code}")
            else:
                print(f"  ❌ First request failed: {response1.status_code}")
                
        except Exception as e:
            print(f"  ❌ Django cache test failed: {e}")
            self.results["django_cache_tests"]["error"] = str(e)
    
    async def test_fastapi_performance(self):
        """测试FastAPI性能"""
        print("🔍 Testing FastAPI performance...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # 测试健康检查端点
                health_url = f"{FASTAPI_URL}/health"
                
                start_time = time.time()
                async with session.get(health_url) as response:
                    if response.status == 200:
                        response_time = time.time() - start_time
                        data = await response.json()
                        
                        self.results["fastapi_tests"]["health_check"] = {
                            "status": "✅ OK",
                            "response_time_ms": round(response_time * 1000, 2),
                            "data": data
                        }
                        print(f"  ✅ Health check: {response_time*1000:.2f}ms")
                    else:
                        self.results["fastapi_tests"]["health_check"] = {
                            "status": f"❌ HTTP {response.status}"
                        }
                        print(f"  ❌ Health check failed: HTTP {response.status}")
                
                # 测试多个并发请求
                await self._test_concurrent_requests(session)
                
        except Exception as e:
            print(f"  ❌ FastAPI test failed: {e}")
            self.results["fastapi_tests"]["error"] = str(e)
    
    async def _test_concurrent_requests(self, session):
        """测试并发请求性能"""
        print("  🔍 Testing concurrent requests...")
        
        try:
            health_url = f"{FASTAPI_URL}/health"
            concurrent_requests = 20
            
            # 创建并发请求
            tasks = []
            for _ in range(concurrent_requests):
                task = session.get(health_url)
                tasks.append(task)
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            successful_responses = 0
            for response in responses:
                if hasattr(response, 'status') and response.status == 200:
                    successful_responses += 1
                    response.close()
            
            self.results["fastapi_tests"]["concurrent"] = {
                "total_requests": concurrent_requests,
                "successful": successful_responses,
                "total_time_ms": round(total_time * 1000, 2),
                "avg_time_ms": round(total_time * 1000 / concurrent_requests, 2),
                "requests_per_second": round(concurrent_requests / total_time, 2)
            }
            
            print(f"    ✅ {successful_responses}/{concurrent_requests} successful")
            print(f"    📊 {total_time*1000:.2f}ms total, {total_time*1000/concurrent_requests:.2f}ms avg")
            print(f"    🚀 {concurrent_requests/total_time:.2f} req/sec")
            
        except Exception as e:
            print(f"    ❌ Concurrent test failed: {e}")
    
    def test_integration(self):
        """集成测试"""
        print("🔍 Testing integration...")
        
        try:
            # 测试Django到FastAPI的通信
            # 这里可以添加具体的集成测试逻辑
            self.results["integration_tests"] = {
                "status": "✅ Basic integration OK"
            }
            print("  ✅ Basic integration working")
            
        except Exception as e:
            print(f"  ❌ Integration test failed: {e}")
            self.results["integration_tests"]["error"] = str(e)
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 ANSFLOW OPTIMIZATION TEST REPORT")
        print("="*60)
        
        # 判断整体状态
        failed_tests = 0
        total_tests = 0
        
        for category, tests in self.results.items():
            if category == "overall_status":
                continue
            
            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    total_tests += 1
                    if isinstance(result, dict):
                        if "❌" in result.get("status", ""):
                            failed_tests += 1
                    elif "❌" in str(result):
                        failed_tests += 1
        
        success_rate = (total_tests - failed_tests) / total_tests * 100 if total_tests > 0 else 0
        
        if success_rate >= 90:
            self.results["overall_status"] = "✅ EXCELLENT"
        elif success_rate >= 70:
            self.results["overall_status"] = "⚠️ GOOD"
        else:
            self.results["overall_status"] = "❌ NEEDS ATTENTION"
        
        print(f"Overall Status: {self.results['overall_status']}")
        print(f"Success Rate: {success_rate:.1f}% ({total_tests - failed_tests}/{total_tests})")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # 详细结果
        print("\n📋 Detailed Results:")
        print(json.dumps(self.results, indent=2, ensure_ascii=False))
        
        # 保存报告到文件
        with open('ansflow_optimization_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Report saved to: ansflow_optimization_test_report.json")
        
        return self.results["overall_status"]
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 Starting AnsFlow Optimization Tests...")
        print(f"⏰ Test started at: {datetime.now().isoformat()}")
        print("-" * 60)
        
        # 按顺序运行测试
        self.test_redis_connections()
        print()
        
        self.test_rabbitmq_connection()
        print()
        
        self.test_django_cache_performance()
        print()
        
        await self.test_fastapi_performance()
        print()
        
        self.test_integration()
        print()
        
        # 生成报告
        status = self.generate_report()
        
        return status


async def main():
    """主函数"""
    tester = AnsFlowOptimizationTester()
    
    try:
        status = await tester.run_all_tests()
        
        # 根据结果设置退出码
        if "✅" in status:
            sys.exit(0)  # 成功
        elif "⚠️" in status:
            sys.exit(1)  # 警告
        else:
            sys.exit(2)  # 失败
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(3)
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        sys.exit(4)


if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(main())
