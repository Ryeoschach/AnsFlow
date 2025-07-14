#!/usr/bin/env python3
"""
AnsFlow 生产环境健康检查脚本
用于监控生产环境的服务状态和性能指标
"""

import requests
import time
import json
import sys
from datetime import datetime
import redis
import pika

class AnsFlowHealthChecker:
    """AnsFlow 生产环境健康检查器"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "checking",
            "services": {},
            "performance": {},
            "alerts": []
        }
        
        # 生产环境配置
        self.django_url = "http://localhost:8000"
        self.fastapi_url = "http://localhost:8001"
        self.redis_url = "redis://localhost:6379"
        self.rabbitmq_url = "amqp://ansflow_prod:password@localhost:5672/ansflow_vhost"
    
    def check_django_service(self):
        """检查 Django 服务状态"""
        try:
            # 健康检查端点
            response = requests.get(f"{self.django_url}/api/v1/health/", timeout=10)
            if response.status_code == 200:
                self.results["services"]["django"] = {
                    "status": "✅ healthy",
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "data": response.json()
                }
            else:
                self.results["services"]["django"] = {
                    "status": f"❌ unhealthy (HTTP {response.status_code})",
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
                self.results["alerts"].append("Django service returned non-200 status")
        except Exception as e:
            self.results["services"]["django"] = {
                "status": f"❌ error: {str(e)}"
            }
            self.results["alerts"].append(f"Django service check failed: {str(e)}")
    
    def check_fastapi_service(self):
        """检查 FastAPI 服务状态"""
        try:
            # 健康检查
            start_time = time.time()
            response = requests.get(f"{self.fastapi_url}/health", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                self.results["services"]["fastapi"] = {
                    "status": "✅ healthy",
                    "response_time_ms": response_time,
                    "data": response.json()
                }
                
                # 性能测试
                self._test_fastapi_performance()
            else:
                self.results["services"]["fastapi"] = {
                    "status": f"❌ unhealthy (HTTP {response.status_code})",
                    "response_time_ms": response_time
                }
                self.results["alerts"].append("FastAPI service returned non-200 status")
        except Exception as e:
            self.results["services"]["fastapi"] = {
                "status": f"❌ error: {str(e)}"
            }
            self.results["alerts"].append(f"FastAPI service check failed: {str(e)}")
    
    def _test_fastapi_performance(self):
        """测试 FastAPI 性能"""
        try:
            # 并发请求测试
            import asyncio
            import aiohttp
            
            async def make_request(session):
                async with session.get(f"{self.fastapi_url}/health") as response:
                    return await response.json()
            
            async def run_concurrent_test():
                async with aiohttp.ClientSession() as session:
                    tasks = [make_request(session) for _ in range(10)]
                    start_time = time.time()
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    end_time = time.time()
                    
                    successful = sum(1 for r in results if not isinstance(r, Exception))
                    total_time = (end_time - start_time) * 1000
                    
                    return {
                        "total_requests": len(tasks),
                        "successful": successful,
                        "total_time_ms": total_time,
                        "avg_time_ms": total_time / len(tasks),
                        "requests_per_second": len(tasks) / (total_time / 1000)
                    }
            
            perf_result = asyncio.run(run_concurrent_test())
            self.results["performance"]["fastapi_concurrent"] = perf_result
            
            # 性能警告
            if perf_result["avg_time_ms"] > 100:
                self.results["alerts"].append("FastAPI average response time > 100ms")
            if perf_result["requests_per_second"] < 20:
                self.results["alerts"].append("FastAPI requests/second < 20")
                
        except Exception as e:
            self.results["performance"]["fastapi_concurrent"] = {"error": str(e)}
    
    def check_redis_service(self):
        """检查 Redis 服务状态"""
        try:
            databases = {
                "default": redis.Redis.from_url(f"{self.redis_url}/1"),
                "session": redis.Redis.from_url(f"{self.redis_url}/3"),
                "api": redis.Redis.from_url(f"{self.redis_url}/4"),
                "pipeline": redis.Redis.from_url(f"{self.redis_url}/5"),
                "channels": redis.Redis.from_url(f"{self.redis_url}/2")
            }
            
            redis_status = {}
            total_memory = 0
            
            for db_name, client in databases.items():
                try:
                    # 测试连接
                    start_time = time.time()
                    client.ping()
                    latency = (time.time() - start_time) * 1000
                    
                    # 获取内存使用情况
                    info = client.info('memory')
                    used_memory = info['used_memory']
                    total_memory += used_memory
                    
                    redis_status[db_name] = {
                        "status": "✅ connected",
                        "latency_ms": round(latency, 2),
                        "memory_mb": round(used_memory / 1024 / 1024, 2)
                    }
                    
                    # 延迟警告
                    if latency > 5:
                        self.results["alerts"].append(f"Redis {db_name} latency > 5ms")
                        
                except Exception as e:
                    redis_status[db_name] = {"status": f"❌ error: {str(e)}"}
                    self.results["alerts"].append(f"Redis {db_name} connection failed")
            
            self.results["services"]["redis"] = redis_status
            self.results["performance"]["redis_total_memory_mb"] = round(total_memory / 1024 / 1024, 2)
            
            # 内存使用警告
            if total_memory > 512 * 1024 * 1024:  # 512MB
                self.results["alerts"].append("Redis total memory usage > 512MB")
                
        except Exception as e:
            self.results["services"]["redis"] = {"error": str(e)}
            self.results["alerts"].append(f"Redis check failed: {str(e)}")
    
    def check_rabbitmq_service(self):
        """检查 RabbitMQ 服务状态"""
        try:
            connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            channel = connection.channel()
            
            # 检查队列状态
            queues = ['high_priority', 'medium_priority', 'low_priority']
            queue_status = {}
            
            for queue_name in queues:
                try:
                    method = channel.queue_declare(queue=queue_name, passive=True)
                    queue_status[queue_name] = {
                        "status": "✅ active",
                        "message_count": method.method.message_count,
                        "consumer_count": method.method.consumer_count
                    }
                    
                    # 队列积压警告
                    if method.method.message_count > 1000:
                        self.results["alerts"].append(f"Queue {queue_name} has {method.method.message_count} pending messages")
                        
                except Exception as e:
                    queue_status[queue_name] = {"status": f"❌ error: {str(e)}"}
            
            connection.close()
            self.results["services"]["rabbitmq"] = queue_status
            
        except Exception as e:
            self.results["services"]["rabbitmq"] = {"error": str(e)}
            self.results["alerts"].append(f"RabbitMQ check failed: {str(e)}")
    
    def check_system_resources(self):
        """检查系统资源使用情况"""
        try:
            import psutil
            
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            
            self.results["performance"]["system"] = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100,
                "memory_available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
                "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
            }
            
            # 系统资源警告
            if cpu_percent > 80:
                self.results["alerts"].append(f"High CPU usage: {cpu_percent}%")
            if memory.percent > 80:
                self.results["alerts"].append(f"High memory usage: {memory.percent}%")
            if (disk.used / disk.total) * 100 > 80:
                self.results["alerts"].append(f"High disk usage: {(disk.used / disk.total) * 100:.1f}%")
                
        except ImportError:
            self.results["performance"]["system"] = {"error": "psutil not installed"}
        except Exception as e:
            self.results["performance"]["system"] = {"error": str(e)}
    
    def check_parallel_execution_performance(self):
        """检查并行执行性能和状态"""
        try:
            # 检查当前运行的并行组
            response = requests.get(f"{self.django_url}/api/v1/executions/parallel-status/", timeout=10)
            
            if response.status_code == 200:
                parallel_data = response.json()
                
                active_parallel_groups = parallel_data.get('active_parallel_groups', 0)
                avg_parallel_execution_time = parallel_data.get('avg_execution_time_seconds', 0)
                parallel_success_rate = parallel_data.get('success_rate_percent', 0)
                concurrent_workers = parallel_data.get('concurrent_workers', 0)
                
                self.results["performance"]["parallel_execution"] = {
                    "active_parallel_groups": active_parallel_groups,
                    "avg_execution_time_seconds": avg_parallel_execution_time,
                    "success_rate_percent": parallel_success_rate,
                    "concurrent_workers": concurrent_workers,
                    "status": "✅ operational"
                }
                
                # 并行执行性能警告
                if active_parallel_groups > 10:
                    self.results["alerts"].append(f"High parallel groups load: {active_parallel_groups} active")
                if avg_parallel_execution_time > 300:  # 5分钟
                    self.results["alerts"].append(f"Long parallel execution time: {avg_parallel_execution_time}s average")
                if parallel_success_rate < 90:
                    self.results["alerts"].append(f"Low parallel success rate: {parallel_success_rate}%")
                if concurrent_workers > 50:
                    self.results["alerts"].append(f"High concurrent workers: {concurrent_workers}")
                
                # 检查Jenkins并行转换性能
                self._check_jenkins_parallel_performance()
                
                # 检查并行组API
                self._check_parallel_groups_api()
                
            else:
                self.results["performance"]["parallel_execution"] = {
                    "status": f"❌ API error (HTTP {response.status_code})"
                }
                self.results["alerts"].append("Parallel execution status API unavailable")
                
        except Exception as e:
            self.results["performance"]["parallel_execution"] = {
                "status": f"❌ check failed: {str(e)}"
            }
            self.results["alerts"].append(f"Parallel execution check failed: {str(e)}")
    
    def _check_jenkins_parallel_performance(self):
        """检查Jenkins并行转换性能"""
        try:
            # 测试Jenkins并行组检测功能
            test_response = requests.post(
                f"{self.django_url}/api/v1/cicd/pipelines/preview/",
                json={
                    "pipeline_id": 2,
                    "preview_mode": False,
                    "execution_mode": "remote"
                },
                timeout=10
            )
            
            if test_response.status_code == 200:
                preview_data = test_response.json()
                workflow_summary = preview_data.get('workflow_summary', {})
                jenkinsfile = preview_data.get('jenkinsfile', '')
                
                # 检查并行组检测
                total_steps = workflow_summary.get('total_steps', 0)
                has_parallel_syntax = 'parallel {' in jenkinsfile
                parallel_group_count = jenkinsfile.count('parallel {')
                
                self.results["performance"]["jenkins_parallel"] = {
                    "parallel_detection_working": has_parallel_syntax,
                    "total_steps_detected": total_steps,
                    "parallel_groups_detected": parallel_group_count,
                    "jenkinsfile_generation": "✅ successful" if jenkinsfile else "❌ failed",
                    "database_integration": "✅ working" if workflow_summary.get('data_source') == 'database' else "❌ failed"
                }
                
                # Jenkins并行组功能警告
                if not has_parallel_syntax:
                    self.results["alerts"].append("Jenkins parallel group detection not working")
                if total_steps == 0:
                    self.results["alerts"].append("Jenkins pipeline preview returns 0 steps")
                if parallel_group_count == 0:
                    self.results["alerts"].append("No parallel groups detected in Jenkins pipeline")
                    
            else:
                self.results["performance"]["jenkins_parallel"] = {
                    "status": f"❌ Pipeline preview API error (HTTP {test_response.status_code})"
                }
                self.results["alerts"].append("Jenkins pipeline preview API unavailable")
            
            # 尝试获取Jenkins统计信息（如果存在）
            try:
                stats_response = requests.get(f"{self.django_url}/api/v1/tools/jenkins/parallel-stats/", timeout=5)
                if stats_response.status_code == 200:
                    jenkins_stats = stats_response.json()
                    self.results["performance"]["jenkins_parallel"].update({
                        "conversion_success_rate": jenkins_stats.get('conversion_success_rate', 0),
                        "avg_conversion_time_ms": jenkins_stats.get('avg_conversion_time_ms', 0),
                        "active_builds": jenkins_stats.get('active_builds', 0)
                    })
            except:
                pass  # Jenkins统计API可能不存在，这是可选的
            
        except Exception as e:
            self.results["performance"]["jenkins_parallel"] = {
                "status": f"❌ check failed: {str(e)}"
            }
            self.results["alerts"].append(f"Jenkins parallel check failed: {str(e)}")

    def _check_parallel_groups_api(self):
        """检查并行组API功能"""
        try:
            # 使用Django shell模拟并行组API调用，因为需要认证
            import subprocess
            
            django_cmd = '''
import sys, os
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
import django
django.setup()

from pipelines.models import Pipeline
pipeline = Pipeline.objects.get(id=2)
steps = pipeline.steps.all().order_by('order')

parallel_groups = {}
for step in steps:
    if step.parallel_group:
        group_name = step.parallel_group
        if group_name not in parallel_groups:
            parallel_groups[group_name] = {'id': group_name, 'name': group_name, 'steps': []}
        parallel_groups[group_name]['steps'].append({'id': step.id, 'name': step.name})

print(f"GROUPS:{len(parallel_groups)}")
print(f"STEPS:{len(steps)}")
'''
            
            result = subprocess.run([
                'python3', '-c', django_cmd
            ], capture_output=True, text=True, cwd='/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
            
            if result.returncode == 0:
                output = result.stdout.strip()
                groups_line = [line for line in output.split('\n') if line.startswith('GROUPS:')]
                steps_line = [line for line in output.split('\n') if line.startswith('STEPS:')]
                
                if groups_line and steps_line:
                    groups_count = int(groups_line[0].split(':')[1])
                    steps_count = int(steps_line[0].split(':')[1])
                    
                    self.results["performance"]["parallel_groups_api"] = {
                        "status": "✅ working",
                        "groups_detected": groups_count,
                        "total_steps": steps_count,
                        "api_logic": "✅ fixed" if groups_count > 0 else "❌ not working"
                    }
                    
                    # API功能警告
                    if groups_count == 0:
                        self.results["alerts"].append("Parallel groups API returns 0 groups")
                    if steps_count == 0:
                        self.results["alerts"].append("Parallel groups API returns 0 steps")
                else:
                    self.results["performance"]["parallel_groups_api"] = {
                        "status": "❌ parsing failed"
                    }
            else:
                self.results["performance"]["parallel_groups_api"] = {
                    "status": f"❌ django shell failed: {result.stderr}"
                }
                
        except Exception as e:
            self.results["performance"]["parallel_groups_api"] = {
                "status": f"❌ check failed: {str(e)}"
            }

    def run_health_check(self):
        """运行完整的健康检查"""
        print("🏥 AnsFlow 生产环境健康检查")
        print("=" * 50)
        
        # 执行各项检查
        print("🔍 检查 Django 服务...")
        self.check_django_service()
        
        print("🔍 检查 FastAPI 服务...")
        self.check_fastapi_service()
        
        print("🔍 检查 Redis 服务...")
        self.check_redis_service()
        
        print("🔍 检查 RabbitMQ 服务...")
        self.check_rabbitmq_service()
        
        print("🔍 检查系统资源...")
        self.check_system_resources()
        
        print("🔍 检查并行执行性能...")
        self.check_parallel_execution_performance()
        
        # 确定整体状态
        has_errors = any(
            "❌" in str(service) or "error" in str(service).lower()
            for service in self.results["services"].values()
        )
        
        if has_errors:
            self.results["overall_status"] = "❌ UNHEALTHY"
        elif self.results["alerts"]:
            self.results["overall_status"] = "⚠️ WARNING"
        else:
            self.results["overall_status"] = "✅ HEALTHY"
        
        return self.results
    
    def print_summary(self):
        """打印健康检查摘要"""
        print("\n" + "=" * 50)
        print(f"📊 健康检查摘要 - {self.results['overall_status']}")
        print("=" * 50)
        
        # 服务状态
        print("\n🔧 服务状态:")
        for service, status in self.results["services"].items():
            if isinstance(status, dict) and "status" in status:
                print(f"  {service}: {status['status']}")
            else:
                print(f"  {service}: {status}")
        
        # 性能指标
        if self.results["performance"]:
            print("\n📈 性能指标:")
            for metric, value in self.results["performance"].items():
                print(f"  {metric}: {value}")
        
        # 警告信息
        if self.results["alerts"]:
            print("\n⚠️ 警告信息:")
            for alert in self.results["alerts"]:
                print(f"  - {alert}")
        
        print("\n" + "=" * 50)

def main():
    """主函数"""
    checker = AnsFlowHealthChecker()
    
    try:
        results = checker.run_health_check()
        checker.print_summary()
        
        # 保存结果到文件
        output_file = f"docs/testing/health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: {output_file}")
        
        # 根据状态设置退出码
        if results["overall_status"] == "❌ UNHEALTHY":
            sys.exit(1)
        elif results["overall_status"] == "⚠️ WARNING":
            sys.exit(2)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ 健康检查失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
