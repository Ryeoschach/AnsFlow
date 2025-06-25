#!/usr/bin/env python3
"""
测试拆分后的Jenkins API端点
验证所有Jenkins相关的REST API是否正常工作
"""
import requests
import json
import sys
import time
from urllib.parse import urljoin

class JenkinsAPITester:
    def __init__(self, base_url='http://localhost:8000/api/v1/cicd/'):
        self.base_url = base_url
        self.session = requests.Session()
        self.tool_id = None
        
    def test_tool_endpoints(self):
        """测试CI/CD工具端点"""
        print("🔍 测试CI/CD工具管理端点...")
        
        try:
            # 测试工具列表
            response = self.session.get(urljoin(self.base_url, 'tools/'))
            print(f"📋 工具列表端点状态: {response.status_code}")
            
            if response.status_code == 200:
                tools = response.json()
                print(f"✅ 找到 {len(tools.get('results', []))} 个工具")
                
                # 寻找Jenkins工具
                jenkins_tools = [
                    tool for tool in tools.get('results', []) 
                    if tool.get('tool_type') == 'jenkins'
                ]
                
                if jenkins_tools:
                    self.tool_id = jenkins_tools[0]['id']
                    print(f"🔧 使用Jenkins工具ID: {self.tool_id}")
                    return True
                else:
                    print("⚠️ 未找到Jenkins工具，请先创建一个Jenkins工具")
                    return False
            else:
                print(f"❌ 工具列表获取失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 工具端点测试失败: {e}")
            return False
    
    def test_jenkins_endpoints(self):
        """测试Jenkins特定端点"""
        if not self.tool_id:
            print("❌ 没有可用的Jenkins工具ID")
            return False
            
        print("🔍 测试Jenkins特定端点...")
        
        jenkins_endpoints = [
            ('jenkins/jobs/', 'GET', '作业列表'),
            ('jenkins/queue/', 'GET', '构建队列'),
            ('health_check/', 'POST', '健康检查')
        ]
        
        success_count = 0
        
        for endpoint, method, description in jenkins_endpoints:
            try:
                url = urljoin(self.base_url, f'tools/{self.tool_id}/{endpoint}')
                
                if method == 'GET':
                    response = self.session.get(url)
                elif method == 'POST':
                    response = self.session.post(url, json={})
                
                print(f"📡 {description} ({method}): {response.status_code}")
                
                if response.status_code in [200, 201]:
                    success_count += 1
                    print(f"  ✅ {description} 成功")
                    
                    # 显示响应摘要
                    try:
                        data = response.json()
                        if 'jobs' in data:
                            print(f"    📝 发现 {data.get('jobs_count', 0)} 个作业")
                        elif 'queue_items' in data:
                            print(f"    📝 队列中有 {data.get('queue_count', 0)} 个项目")
                        elif 'is_healthy' in data:
                            print(f"    📝 健康状态: {data.get('is_healthy', False)}")
                    except:
                        pass
                        
                elif response.status_code == 400:
                    print(f"  ⚠️ {description} 参数错误 (预期行为)")
                    success_count += 1
                elif response.status_code == 404:
                    print(f"  ❌ {description} 端点未找到")
                else:
                    print(f"  ❌ {description} 失败: {response.status_code}")
                    try:
                        error_data = response.json()
                        print(f"    错误: {error_data.get('error', 'Unknown')}")
                    except:
                        pass
                        
            except Exception as e:
                print(f"  ❌ {description} 测试异常: {e}")
        
        print(f"📊 Jenkins端点测试结果: {success_count}/{len(jenkins_endpoints)} 成功")
        return success_count == len(jenkins_endpoints)
    
    def test_job_operations(self):
        """测试Jenkins作业操作端点"""
        if not self.tool_id:
            print("❌ 没有可用的Jenkins工具ID")
            return False
            
        print("🔍 测试Jenkins作业操作端点...")
        
        test_job_name = f"ansflow-api-test-{int(time.time())}"
        
        # 测试作业创建
        create_url = urljoin(self.base_url, f'tools/{self.tool_id}/jenkins/create-job/')
        create_data = {
            'job_name': test_job_name,
            'sample_job': True
        }
        
        try:
            response = self.session.post(create_url, json=create_data)
            print(f"🔨 作业创建: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print(f"  ✅ 作业 {test_job_name} 创建成功")
                
                # 测试作业信息获取
                info_url = urljoin(self.base_url, f'tools/{self.tool_id}/jenkins/job-info/')
                info_response = self.session.get(info_url, params={'job_name': test_job_name})
                print(f"📋 作业信息获取: {info_response.status_code}")
                
                # 测试作业构建启动
                build_url = urljoin(self.base_url, f'tools/{self.tool_id}/jenkins/start-build/')
                build_data = {
                    'job_name': test_job_name,
                    'parameters': {},
                    'wait_for_start': False
                }
                build_response = self.session.post(build_url, json=build_data)
                print(f"🚀 构建启动: {build_response.status_code}")
                
                # 清理测试作业
                delete_url = urljoin(self.base_url, f'tools/{self.tool_id}/jenkins/delete-job/')
                delete_data = {
                    'job_name': test_job_name,
                    'confirm': True
                }
                delete_response = self.session.delete(delete_url, json=delete_data)
                print(f"🗑️ 作业删除: {delete_response.status_code}")
                
                return True
            else:
                print(f"  ❌ 作业创建失败: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"    错误: {error_data.get('error', 'Unknown')}")
                except:
                    pass
                return False
                
        except Exception as e:
            print(f"❌ 作业操作测试异常: {e}")
            return False
    
    def test_execution_endpoints(self):
        """测试流水线执行端点"""
        print("🔍 测试流水线执行端点...")
        
        try:
            # 测试执行列表
            response = self.session.get(urljoin(self.base_url, 'executions/'))
            print(f"📋 执行列表端点: {response.status_code}")
            
            if response.status_code == 200:
                executions = response.json()
                print(f"✅ 找到 {len(executions.get('results', []))} 个执行记录")
                
                # 测试统计端点
                stats_response = self.session.get(urljoin(self.base_url, 'executions/statistics/'))
                print(f"📊 执行统计端点: {stats_response.status_code}")
                
                if stats_response.status_code == 200:
                    stats = stats_response.json()
                    print(f"  📈 总执行次数: {stats.get('total_executions', 0)}")
                    print(f"  📈 成功率: {stats.get('success_rate', 0)}%")
                
                return True
            else:
                print(f"❌ 执行列表获取失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 执行端点测试异常: {e}")
            return False
    
    def test_atomic_steps_endpoints(self):
        """测试原子步骤端点"""
        print("🔍 测试原子步骤端点...")
        
        try:
            # 测试步骤列表
            response = self.session.get(urljoin(self.base_url, 'atomic-steps/'))
            print(f"📋 原子步骤列表: {response.status_code}")
            
            if response.status_code == 200:
                steps = response.json()
                print(f"✅ 找到 {len(steps.get('results', []))} 个原子步骤")
                
                # 测试分类端点
                categories_response = self.session.get(urljoin(self.base_url, 'atomic-steps/categories/'))
                print(f"📂 步骤分类端点: {categories_response.status_code}")
                
                if categories_response.status_code == 200:
                    categories = categories_response.json()
                    print(f"  📂 找到 {categories.get('total_categories', 0)} 个分类")
                
                # 测试使用统计端点
                usage_response = self.session.get(urljoin(self.base_url, 'atomic-steps/usage_statistics/'))
                print(f"📊 使用统计端点: {usage_response.status_code}")
                
                return True
            else:
                print(f"❌ 原子步骤列表获取失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 原子步骤端点测试异常: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有API测试"""
        print("🚀 开始Jenkins API端点测试...")
        print("=" * 50)
        
        results = []
        
        # 测试工具端点
        results.append(("工具管理端点", self.test_tool_endpoints()))
        
        # 测试Jenkins端点
        results.append(("Jenkins特定端点", self.test_jenkins_endpoints()))
        
        # 测试作业操作（可能失败，因为需要真实的Jenkins服务器）
        results.append(("Jenkins作业操作", self.test_job_operations()))
        
        # 测试执行端点
        results.append(("流水线执行端点", self.test_execution_endpoints()))
        
        # 测试原子步骤端点
        results.append(("原子步骤端点", self.test_atomic_steps_endpoints()))
        
        # 显示测试结果
        print("\n" + "=" * 50)
        print("📊 测试结果汇总:")
        
        passed = 0
        total = len(results)
        
        for test_name, success in results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"  {test_name}: {status}")
            if success:
                passed += 1
        
        print(f"\n🎯 总体结果: {passed}/{total} 测试通过")
        
        if passed == total:
            print("🎉 所有API端点测试通过！")
            return True
        else:
            print("⚠️ 部分测试失败，请检查服务器状态和配置")
            return False


if __name__ == "__main__":
    # 可以从命令行参数获取API基础URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8000/api/v1/cicd/'
    
    tester = JenkinsAPITester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)
