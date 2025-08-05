#!/usr/bin/env python3
"""
AnsFlow 性能分析和监控测试脚本
测试 Prometheus 监控集成和性能指标收集
"""

import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime
from typing import List, Dict, Any

class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.fastapi_base_url = "http://localhost:8001"
        self.django_base_url = "http://localhost:8000"
        self.prometheus_url = "http://localhost:9090"
        self.grafana_url = "http://localhost:3001"
        
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
    
    async def test_fastapi_metrics_endpoint(self):
        """测试 FastAPI Prometheus 指标端点"""
        print("🔍 测试 FastAPI Prometheus 指标端点...")
        
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(f"{self.fastapi_base_url}/metrics") as response:
                    duration = time.time() - start_time
                    content = await response.text()
                    
                    metrics_found = []
                    if "ansflow_http_requests_total" in content:
                        metrics_found.append("HTTP请求计数器")
                    if "ansflow_http_request_duration_seconds" in content:
                        metrics_found.append("HTTP请求延迟")
                    if "ansflow_websocket_connections_total" in content:
                        metrics_found.append("WebSocket连接")
                    if "ansflow_system_cpu_usage_percent" in content:
                        metrics_found.append("系统CPU使用率")
                    
                    result = {
                        "status": "success" if response.status == 200 else "failed",
                        "response_time": duration,
                        "metrics_count": len([line for line in content.split('\n') if line.startswith('ansflow_')]),
                        "metrics_found": metrics_found,
                        "content_length": len(content)
                    }
                    
                    print(f"✅ FastAPI 指标端点响应: {response.status}")
                    print(f"📊 发现 {len(metrics_found)} 个 AnsFlow 指标")
                    print(f"⏱️  响应时间: {duration:.3f}s")
                    
                    self.test_results["tests"]["fastapi_metrics"] = result
                    return result
                    
        except Exception as e:
            print(f"❌ FastAPI 指标测试失败: {e}")
            result = {"status": "error", "error": str(e)}
            self.test_results["tests"]["fastapi_metrics"] = result
            return result
    
    async def test_health_endpoints(self):
        """测试健康检查端点"""
        print("\n🏥 测试健康检查端点...")
        
        endpoints = [
            f"{self.fastapi_base_url}/health/",
            f"{self.fastapi_base_url}/health/ready",
            f"{self.fastapi_base_url}/health/live"
        ]
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    async with session.get(endpoint) as response:
                        duration = time.time() - start_time
                        data = await response.json()
                        
                        endpoint_name = endpoint.split('/')[-1] or "root"
                        results[endpoint_name] = {
                            "status": response.status,
                            "response_time": duration,
                            "healthy": data.get("status") in ["healthy", "ready", "alive"],
                            "data": data
                        }
                        
                        status_emoji = "✅" if response.status == 200 else "❌"
                        print(f"{status_emoji} {endpoint_name}: {response.status} ({duration:.3f}s)")
                        
                except Exception as e:
                    print(f"❌ {endpoint} 测试失败: {e}")
                    results[endpoint.split('/')[-1] or "root"] = {
                        "status": "error", 
                        "error": str(e)
                    }
        
        self.test_results["tests"]["health_endpoints"] = results
        return results
    
    async def load_test_fastapi(self, duration: int = 30, concurrent: int = 10):
        """对 FastAPI 进行负载测试"""
        print(f"\n🚀 FastAPI 负载测试 ({concurrent} 并发，{duration}s)...")
        
        endpoints = [
            "/",
            "/health/",
            "/health/ready",
            "/health/live"
        ]
        
        results = {
            "duration": duration,
            "concurrent_users": concurrent,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "avg_response_time": 0,
            "min_response_time": 0,
            "max_response_time": 0,
            "p95_response_time": 0,
            "requests_per_second": 0
        }
        
        async def make_request(session, endpoint):
            try:
                start_time = time.time()
                async with session.get(f"{self.fastapi_base_url}{endpoint}") as response:
                    duration = time.time() - start_time
                    results["response_times"].append(duration)
                    results["total_requests"] += 1
                    
                    if response.status == 200:
                        results["successful_requests"] += 1
                    else:
                        results["failed_requests"] += 1
                        
            except Exception as e:
                results["total_requests"] += 1
                results["failed_requests"] += 1
        
        # 运行负载测试
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            tasks = []
            
            while time.time() - start_time < duration:
                for _ in range(concurrent):
                    endpoint = endpoints[results["total_requests"] % len(endpoints)]
                    task = asyncio.create_task(make_request(session, endpoint))
                    tasks.append(task)
                
                # 等待一小段时间避免过载
                await asyncio.sleep(0.1)
            
            # 等待所有任务完成
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # 计算统计数据
        if results["response_times"]:
            results["avg_response_time"] = statistics.mean(results["response_times"])
            results["min_response_time"] = min(results["response_times"])
            results["max_response_time"] = max(results["response_times"])
            results["p95_response_time"] = statistics.quantiles(results["response_times"], n=20)[18]  # 95th percentile
        
        results["requests_per_second"] = results["total_requests"] / duration
        
        print(f"📊 负载测试结果:")
        print(f"   总请求数: {results['total_requests']}")
        print(f"   成功请求: {results['successful_requests']}")
        print(f"   失败请求: {results['failed_requests']}")
        print(f"   成功率: {results['successful_requests']/results['total_requests']*100:.1f}%")
        print(f"   请求/秒: {results['requests_per_second']:.2f}")
        print(f"   平均响应时间: {results['avg_response_time']*1000:.2f}ms")
        print(f"   95%分位数: {results['p95_response_time']*1000:.2f}ms")
        
        self.test_results["tests"]["load_test"] = results
        return results
    
    async def test_websocket_monitoring(self):
        """测试 WebSocket 监控"""
        print("\n🔌 测试 WebSocket 监控...")
        
        try:
            import websockets
            
            results = {
                "connections_tested": 0,
                "successful_connections": 0,
                "failed_connections": 0,
                "connection_times": []
            }
            
            # 测试多个 WebSocket 连接
            for i in range(5):
                try:
                    start_time = time.time()
                    uri = f"ws://localhost:8001/ws/monitor"
                    async with websockets.connect(uri) as websocket:
                        connection_time = time.time() - start_time
                        results["connection_times"].append(connection_time)
                        results["successful_connections"] += 1
                        
                        # 发送测试消息
                        await websocket.send(json.dumps({"type": "ping"}))
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        
                        print(f"✅ WebSocket 连接 {i+1}: 成功 ({connection_time:.3f}s)")
                        
                except Exception as e:
                    print(f"❌ WebSocket 连接 {i+1}: 失败 - {e}")
                    results["failed_connections"] += 1
                
                results["connections_tested"] += 1
                await asyncio.sleep(0.5)  # 避免过快连接
            
            if results["connection_times"]:
                results["avg_connection_time"] = statistics.mean(results["connection_times"])
            
            self.test_results["tests"]["websocket_monitoring"] = results
            return results
            
        except ImportError:
            print("⚠️  websockets 库未安装，跳过 WebSocket 测试")
            result = {"status": "skipped", "reason": "websockets library not available"}
            self.test_results["tests"]["websocket_monitoring"] = result
            return result
    
    async def test_prometheus_query(self):
        """测试 Prometheus 查询"""
        print("\n📈 测试 Prometheus 查询...")
        
        queries = [
            "up",
            "ansflow_http_requests_total",
            "ansflow_websocket_connections_total",
            "ansflow_system_cpu_usage_percent"
        ]
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for query in queries:
                try:
                    url = f"{self.prometheus_url}/api/v1/query"
                    params = {"query": query}
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            metric_count = len(data.get("data", {}).get("result", []))
                            results[query] = {
                                "status": "success",
                                "metric_count": metric_count
                            }
                            print(f"✅ {query}: {metric_count} 个指标")
                        else:
                            results[query] = {
                                "status": "failed",
                                "response_code": response.status
                            }
                            print(f"❌ {query}: HTTP {response.status}")
                            
                except Exception as e:
                    results[query] = {"status": "error", "error": str(e)}
                    print(f"❌ {query}: {e}")
        
        self.test_results["tests"]["prometheus_queries"] = results
        return results
    
    async def test_grafana_api(self):
        """测试 Grafana API"""
        print("\n📊 测试 Grafana API...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # 测试 Grafana 健康状态
                async with session.get(f"{self.grafana_url}/api/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        result = {
                            "status": "success",
                            "grafana_status": data,
                            "response_code": response.status
                        }
                        print(f"✅ Grafana 健康检查: {data.get('database', 'unknown')}")
                    else:
                        result = {
                            "status": "failed",
                            "response_code": response.status
                        }
                        print(f"❌ Grafana 健康检查失败: HTTP {response.status}")
                    
                    self.test_results["tests"]["grafana_api"] = result
                    return result
                    
        except Exception as e:
            print(f"❌ Grafana API 测试失败: {e}")
            result = {"status": "error", "error": str(e)}
            self.test_results["tests"]["grafana_api"] = result
            return result
    
    async def test_django_metrics_endpoint(self):
        """测试 Django Prometheus 指标端点"""
        print("🔍 测试 Django Prometheus 指标端点...")
        
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(f"{self.django_base_url}/metrics") as response:
                    duration = time.time() - start_time
                    content = await response.text()
                    
                    metrics_found = []
                    if "django_http_requests_total" in content:
                        metrics_found.append("Django HTTP请求计数器")
                    if "django_http_request_duration_seconds" in content:
                        metrics_found.append("Django HTTP请求延迟")
                    if "django_db_" in content:
                        metrics_found.append("Django数据库指标")
                    if "ansflow_pipelines_total" in content:
                        metrics_found.append("AnsFlow Pipeline指标")
                    if "ansflow_user_activity_total" in content:
                        metrics_found.append("用户活动指标")
                    
                    result = {
                        "status": "success" if response.status == 200 else "failed",
                        "status_code": response.status,
                        "response_time_ms": round(duration * 1000, 2),
                        "metrics_found": metrics_found,
                        "content_length": len(content)
                    }
                    
                    self.test_results["tests"]["django_metrics"] = result
                    
                    if response.status == 200:
                        print(f"  ✅ Django /metrics 端点正常 ({duration*1000:.2f}ms)")
                        print(f"  📊 发现指标: {', '.join(metrics_found)}")
                    else:
                        print(f"  ❌ Django /metrics 端点异常: {response.status}")
                        
        except Exception as e:
            result = {
                "status": "error",
                "error": str(e)
            }
            self.test_results["tests"]["django_metrics"] = result
            print(f"  ❌ Django /metrics 测试失败: {e}")
    
    async def test_django_health_endpoint(self):
        """测试 Django 健康检查端点"""
        print("🔍 测试 Django 健康检查端点...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # 测试基础健康检查
                start_time = time.time()
                async with session.get(f"{self.django_base_url}/health/") as response:
                    duration = time.time() - start_time
                    content = await response.json()
                    
                    basic_health_result = {
                        "status": content.get("status"),
                        "response_time_ms": round(duration * 1000, 2),
                        "service_info": {
                            "service": content.get("service"),
                            "version": content.get("version")
                        }
                    }
                
                # 测试详细健康检查
                start_time = time.time()
                async with session.get(f"{self.django_base_url}/monitoring/health/detailed/") as response:
                    duration = time.time() - start_time
                    content = await response.json()
                    
                    detailed_health_result = {
                        "status": content.get("status"),
                        "response_time_ms": round(duration * 1000, 2),
                        "system_checks": content.get("system", {}),
                        "application_checks": content.get("application", {}),
                        "database_checks": content.get("database", {}),
                        "cache_checks": content.get("cache", {})
                    }
                
                result = {
                    "basic_health": basic_health_result,
                    "detailed_health": detailed_health_result
                }
                
                self.test_results["tests"]["django_health"] = result
                
                print(f"  ✅ Django 基础健康检查正常 ({basic_health_result['response_time_ms']}ms)")
                print(f"  ✅ Django 详细健康检查正常 ({detailed_health_result['response_time_ms']}ms)")
                
        except Exception as e:
            result = {
                "status": "error",
                "error": str(e)
            }
            self.test_results["tests"]["django_health"] = result
            print(f"  ❌ Django 健康检查测试失败: {e}")
    
    async def test_django_api_performance(self):
        """测试 Django API 性能"""
        print("🔍 测试 Django API 性能...")
        
        endpoints = [
            "/api/health/",
            "/api/v1/auth/",
            "/api/v1/pipelines/",
            "/api/v1/projects/"
        ]
        
        performance_results = {}
        
        try:
            async with aiohttp.ClientSession() as session:
                for endpoint in endpoints:
                    try:
                        times = []
                        status_codes = []
                        
                        # 执行5次请求测试
                        for _ in range(5):
                            start_time = time.time()
                            async with session.get(f"{self.django_base_url}{endpoint}") as response:
                                duration = time.time() - start_time
                                times.append(duration * 1000)  # 转换为毫秒
                                status_codes.append(response.status)
                        
                        # 计算统计数据
                        avg_time = statistics.mean(times)
                        min_time = min(times)
                        max_time = max(times)
                        
                        performance_results[endpoint] = {
                            "avg_response_time_ms": round(avg_time, 2),
                            "min_response_time_ms": round(min_time, 2),
                            "max_response_time_ms": round(max_time, 2),
                            "status_codes": status_codes,
                            "requests_count": len(times)
                        }
                        
                        print(f"  📊 {endpoint}: 平均 {avg_time:.2f}ms, 范围 {min_time:.2f}-{max_time:.2f}ms")
                        
                    except Exception as e:
                        performance_results[endpoint] = {
                            "error": str(e)
                        }
                        print(f"  ❌ {endpoint} 测试失败: {e}")
                
                self.test_results["tests"]["django_api_performance"] = performance_results
                
        except Exception as e:
            self.test_results["tests"]["django_api_performance"] = {
                "error": str(e)
            }
            print(f"  ❌ Django API 性能测试失败: {e}")

    def save_results(self, filename: str = None):
        """保存测试结果到文件"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_analysis_{timestamp}.json"
        
        filepath = f"/Users/creed/Workspace/OpenSource/ansflow/docs/testing/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 测试结果已保存到: {filepath}")
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("🎯 AnsFlow 性能分析和监控测试总结")
        print("="*60)
        
        total_tests = len(self.test_results["tests"])
        passed_tests = 0
        
        for test_name, result in self.test_results["tests"].items():
            if isinstance(result, dict):
                if result.get("status") in ["success", "passed"] or result.get("successful_requests", 0) > 0:
                    passed_tests += 1
                    status = "✅ PASS"
                elif result.get("status") == "skipped":
                    status = "⏭️  SKIP"
                else:
                    status = "❌ FAIL"
            else:
                status = "❓ UNKNOWN"
            
            print(f"{status} {test_name}")
        
        print("-"*60)
        print(f"总计: {passed_tests}/{total_tests} 测试通过")
        
        if passed_tests == total_tests:
            print("🎉 所有监控测试通过！系统就绪！")
        else:
            print("⚠️  部分测试失败，请检查系统配置")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始 AnsFlow 性能分析和监控测试...")
        print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*60)
        
        # 运行各项测试
        await self.test_fastapi_metrics_endpoint()
        await self.test_health_endpoints()
        await self.load_test_fastapi(duration=15, concurrent=5)  # 较短的负载测试
        await self.test_websocket_monitoring()
        await self.test_prometheus_query()
        await self.test_grafana_api()
        await self.test_django_metrics_endpoint()
        await self.test_django_health_endpoint()
        await self.test_django_api_performance()
        
        # 保存结果和打印总结
        self.save_results("performance_monitoring_test_report.json")
        self.print_summary()

async def main():
    """主函数"""
    analyzer = PerformanceAnalyzer()
    
    try:
        await analyzer.run_all_tests()
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试执行出错: {e}")

if __name__ == "__main__":
    asyncio.run(main())
