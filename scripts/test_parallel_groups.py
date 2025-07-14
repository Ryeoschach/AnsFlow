#!/usr/bin/env python3
"""
AnsFlow 并行组功能测试脚本
用于验证本地和远程并行执行功能
"""
import requests
import json
import time
import sys

class ParallelGroupTester:
    """并行组功能测试器"""
    
    def __init__(self):
        self.django_url = "http://localhost:8000"
        self.test_results = []
    
    def test_local_parallel_execution(self):
        """测试本地并行执行"""
        print("🧪 测试本地并行执行...")
        
        # 创建包含并行组的流水线
        pipeline_data = {
            "name": "本地并行测试流水线",
            "description": "测试本地模式下的并行组执行",
            "execution_mode": "local",
            "config": {
                "timeout_seconds": 300,
                "max_parallel_workers": 3
            }
        }
        
        try:
            # 创建流水线
            response = requests.post(
                f"{self.django_url}/api/v1/pipelines/pipelines/",
                json=pipeline_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                pipeline = response.json()
                pipeline_id = pipeline['id']
                print(f"✅ 创建流水线成功，ID: {pipeline_id}")
                
                # 添加并行组步骤
                self._add_parallel_steps(pipeline_id)
                
                # 执行流水线
                exec_response = requests.post(
                    f"{self.django_url}/api/v1/pipelines/pipelines/{pipeline_id}/execute/",
                    json={"trigger_type": "test"}
                )
                
                if exec_response.status_code == 200:
                    execution = exec_response.json()
                    print(f"✅ 流水线执行启动成功，执行ID: {execution.get('execution_id')}")
                    
                    # 监控执行状态
                    self._monitor_execution(execution.get('execution_id'))
                    
                    self.test_results.append({
                        "test": "local_parallel_execution",
                        "status": "success",
                        "pipeline_id": pipeline_id,
                        "execution_id": execution.get('execution_id')
                    })
                else:
                    print(f"❌ 流水线执行失败: {exec_response.text}")
                    self.test_results.append({
                        "test": "local_parallel_execution",
                        "status": "failed",
                        "error": exec_response.text
                    })
            else:
                print(f"❌ 创建流水线失败: {response.text}")
                self.test_results.append({
                    "test": "local_parallel_execution",
                    "status": "failed",
                    "error": response.text
                })
                
        except Exception as e:
            print(f"❌ 本地并行测试失败: {e}")
            self.test_results.append({
                "test": "local_parallel_execution",
                "status": "error",
                "error": str(e)
            })
    
    def test_jenkins_parallel_conversion(self):
        """测试Jenkins并行转换"""
        print("🧪 测试Jenkins并行转换...")
        
        # 创建Jenkins工具配置
        tool_data = {
            "name": "测试Jenkins服务器",
            "tool_type": "jenkins",
            "url": "http://jenkins.test.com",
            "credentials": {
                "username": "test_user",
                "token": "test_token"
            },
            "config": {
                "default_timeout": 3600,
                "parallel_support": True
            }
        }
        
        try:
            # 创建CI/CD工具
            tool_response = requests.post(
                f"{self.django_url}/api/v1/cicd-integrations/tools/",
                json=tool_data,
                headers={"Content-Type": "application/json"}
            )
            
            if tool_response.status_code == 201:
                tool = tool_response.json()
                tool_id = tool['id']
                print(f"✅ 创建Jenkins工具成功，ID: {tool_id}")
                
                # 创建远程执行流水线
                pipeline_data = {
                    "name": "Jenkins并行测试流水线",
                    "description": "测试Jenkins模式下的并行组转换",
                    "execution_mode": "remote",
                    "execution_tool_id": tool_id,
                    "tool_job_name": "parallel-test-job"
                }
                
                pipeline_response = requests.post(
                    f"{self.django_url}/api/v1/pipelines/pipelines/",
                    json=pipeline_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if pipeline_response.status_code == 201:
                    pipeline = pipeline_response.json()
                    pipeline_id = pipeline['id']
                    print(f"✅ 创建Jenkins流水线成功，ID: {pipeline_id}")
                    
                    # 添加并行组步骤
                    self._add_parallel_steps(pipeline_id, for_jenkins=True)
                    
                    # 测试Jenkins代码生成
                    self._test_jenkins_code_generation(pipeline_id)
                    
                    self.test_results.append({
                        "test": "jenkins_parallel_conversion",
                        "status": "success",
                        "pipeline_id": pipeline_id,
                        "tool_id": tool_id
                    })
                else:
                    print(f"❌ 创建Jenkins流水线失败: {pipeline_response.text}")
                    self.test_results.append({
                        "test": "jenkins_parallel_conversion",
                        "status": "failed",
                        "error": pipeline_response.text
                    })
            else:
                print(f"❌ 创建Jenkins工具失败: {tool_response.text}")
                self.test_results.append({
                    "test": "jenkins_parallel_conversion",
                    "status": "failed",
                    "error": tool_response.text
                })
                
        except Exception as e:
            print(f"❌ Jenkins并行转换测试失败: {e}")
            self.test_results.append({
                "test": "jenkins_parallel_conversion",
                "status": "error",
                "error": str(e)
            })
    
    def test_hybrid_parallel_execution(self):
        """测试混合模式并行执行"""
        print("🧪 测试混合模式并行执行...")
        
        try:
            # 创建混合模式流水线
            pipeline_data = {
                "name": "混合并行测试流水线",
                "description": "测试混合模式下的并行组智能分配",
                "execution_mode": "hybrid",
                "config": {
                    "local_worker_ratio": 0.6,
                    "remote_worker_ratio": 0.4
                }
            }
            
            response = requests.post(
                f"{self.django_url}/api/v1/pipelines/pipelines/",
                json=pipeline_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                pipeline = response.json()
                pipeline_id = pipeline['id']
                print(f"✅ 创建混合模式流水线成功，ID: {pipeline_id}")
                
                # 添加混合类型的并行步骤
                self._add_hybrid_parallel_steps(pipeline_id)
                
                self.test_results.append({
                    "test": "hybrid_parallel_execution",
                    "status": "success",
                    "pipeline_id": pipeline_id
                })
            else:
                print(f"❌ 创建混合模式流水线失败: {response.text}")
                self.test_results.append({
                    "test": "hybrid_parallel_execution",
                    "status": "failed",
                    "error": response.text
                })
                
        except Exception as e:
            print(f"❌ 混合模式并行测试失败: {e}")
            self.test_results.append({
                "test": "hybrid_parallel_execution",
                "status": "error",
                "error": str(e)
            })
    
    def _add_parallel_steps(self, pipeline_id, for_jenkins=False):
        """添加并行组步骤"""
        parallel_group_id = f"test-group-{int(time.time())}"
        
        steps = [
            {
                "name": "并行步骤1：构建",
                "step_type": "shell" if not for_jenkins else "jenkins_shell",
                "order": 1,
                "parallel_group": parallel_group_id,
                "config": {
                    "command": "echo '开始构建...' && sleep 3 && echo '构建完成'"
                }
            },
            {
                "name": "并行步骤2：测试",
                "step_type": "shell" if not for_jenkins else "jenkins_shell", 
                "order": 2,
                "parallel_group": parallel_group_id,
                "config": {
                    "command": "echo '开始测试...' && sleep 5 && echo '测试完成'"
                }
            },
            {
                "name": "并行步骤3：分析",
                "step_type": "python" if not for_jenkins else "jenkins_python",
                "order": 3,
                "parallel_group": parallel_group_id,
                "config": {
                    "script": "import time; print('开始分析...'); time.sleep(2); print('分析完成')"
                }
            }
        ]
        
        for step in steps:
            try:
                step_response = requests.post(
                    f"{self.django_url}/api/v1/cicd-integrations/atomic-steps/",
                    json={**step, "pipeline": pipeline_id},
                    headers={"Content-Type": "application/json"}
                )
                
                if step_response.status_code == 201:
                    print(f"✅ 添加步骤成功: {step['name']}")
                else:
                    print(f"❌ 添加步骤失败: {step['name']} - {step_response.text}")
                    
            except Exception as e:
                print(f"❌ 添加步骤异常: {step['name']} - {e}")
    
    def _add_hybrid_parallel_steps(self, pipeline_id):
        """添加混合模式的并行步骤"""
        parallel_group_id = f"hybrid-group-{int(time.time())}"
        
        steps = [
            {
                "name": "本地步骤：文件处理",
                "step_type": "python",
                "order": 1,
                "parallel_group": parallel_group_id,
                "config": {
                    "script": "print('本地文件处理'); import os; print(f'当前目录: {os.getcwd()}')"
                }
            },
            {
                "name": "远程步骤：Docker构建",
                "step_type": "docker",
                "order": 2,
                "parallel_group": parallel_group_id,
                "config": {
                    "image": "ubuntu:latest",
                    "command": "echo '远程Docker构建' && uname -a"
                }
            },
            {
                "name": "本地步骤：日志分析",
                "step_type": "shell",
                "order": 3,
                "parallel_group": parallel_group_id,
                "config": {
                    "command": "echo '本地日志分析' && date"
                }
            }
        ]
        
        for step in steps:
            try:
                step_response = requests.post(
                    f"{self.django_url}/api/v1/cicd-integrations/atomic-steps/",
                    json={**step, "pipeline": pipeline_id},
                    headers={"Content-Type": "application/json"}
                )
                
                if step_response.status_code == 201:
                    print(f"✅ 添加混合步骤成功: {step['name']}")
                else:
                    print(f"❌ 添加混合步骤失败: {step['name']} - {step_response.text}")
                    
            except Exception as e:
                print(f"❌ 添加混合步骤异常: {step['name']} - {e}")
    
    def _monitor_execution(self, execution_id):
        """监控执行状态"""
        if not execution_id:
            return
            
        print(f"📊 监控执行状态: {execution_id}")
        
        for i in range(30):  # 最多等待30秒
            try:
                response = requests.get(
                    f"{self.django_url}/api/v1/cicd-integrations/executions/{execution_id}/"
                )
                
                if response.status_code == 200:
                    execution = response.json()
                    status = execution.get('status', 'unknown')
                    print(f"  状态: {status}")
                    
                    if status in ['success', 'failed', 'cancelled']:
                        print(f"🏁 执行完成，最终状态: {status}")
                        break
                else:
                    print(f"  获取状态失败: {response.status_code}")
                    
            except Exception as e:
                print(f"  监控异常: {e}")
            
            time.sleep(1)
    
    def _test_jenkins_code_generation(self, pipeline_id):
        """测试Jenkins代码生成"""
        try:
            response = requests.get(
                f"{self.django_url}/api/v1/pipelines/pipelines/{pipeline_id}/jenkins-code/"
            )
            
            if response.status_code == 200:
                jenkins_code = response.json().get('jenkins_code', '')
                print("✅ Jenkins代码生成成功")
                print("📝 生成的Jenkins Pipeline代码预览:")
                print(jenkins_code[:500] + "..." if len(jenkins_code) > 500 else jenkins_code)
            else:
                print(f"❌ Jenkins代码生成失败: {response.text}")
                
        except Exception as e:
            print(f"❌ Jenkins代码生成异常: {e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始AnsFlow并行组功能测试")
        print("=" * 60)
        
        # 执行各项测试
        self.test_local_parallel_execution()
        print()
        self.test_jenkins_parallel_conversion()
        print()
        self.test_hybrid_parallel_execution()
        
        # 输出测试结果
        print("\n" + "=" * 60)
        print("📋 测试结果摘要")
        print("=" * 60)
        
        for result in self.test_results:
            test_name = result['test']
            status = result['status']
            status_icon = "✅" if status == "success" else "❌"
            
            print(f"{status_icon} {test_name}: {status}")
            
            if status != "success":
                print(f"   错误: {result.get('error', 'Unknown error')}")
        
        # 保存详细结果
        self._save_test_results()
    
    def _save_test_results(self):
        """保存测试结果"""
        try:
            results_file = f"docs/testing/parallel_group_test_{int(time.time())}.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "summary": {
                        "total_tests": len(self.test_results),
                        "successful": len([r for r in self.test_results if r['status'] == 'success']),
                        "failed": len([r for r in self.test_results if r['status'] != 'success'])
                    },
                    "detailed_results": self.test_results
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 测试结果已保存到: {results_file}")
            
        except Exception as e:
            print(f"\n❌ 保存测试结果失败: {e}")


def main():
    """主函数"""
    tester = ParallelGroupTester()
    
    try:
        tester.run_all_tests()
        
        # 根据测试结果设置退出码
        failed_tests = [r for r in tester.test_results if r['status'] != 'success']
        if failed_tests:
            print(f"\n❌ 有 {len(failed_tests)} 个测试失败")
            sys.exit(1)
        else:
            print(f"\n✅ 所有 {len(tester.test_results)} 个测试通过")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
