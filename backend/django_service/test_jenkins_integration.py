#!/usr/bin/env python3
"""
AnsFlow Jenkins 集成完整测试脚本

这个脚本演示了如何：
1. 配置 Jenkins 工具
2. 创建原子步骤
3. 执行流水线
4. 监控执行状态
5. 获取执行日志

使用方法:
    python test_jenkins_integration.py --jenkins-url http://localhost:8080 --username admin --token your_token
"""

import requests
import json
import sys
import time
import argparse
from datetime import datetime


class AnsFlowJenkinsTest:
    """AnsFlow Jenkins 集成测试类"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
    
    def authenticate(self, username="admin", password="admin"):
        """认证并获取 JWT 令牌"""
        print("🔐 正在进行认证...")
        
        auth_data = {
            "username": username,
            "password": password
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/auth/token/", json=auth_data)
        
        if response.status_code == 200:
            tokens = response.json()
            self.token = tokens['access']
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
            print("✅ 认证成功")
            return True
        else:
            print(f"❌ 认证失败: {response.status_code} - {response.text}")
            return False
    
    def get_or_create_project(self):
        """获取或创建项目"""
        print("📁 获取项目...")
        
        response = self.session.get(f"{self.base_url}/api/v1/projects/projects/")
        
        if response.status_code == 200:
            projects = response.json()
            if projects['results']:
                project = projects['results'][0]
                print(f"✅ 使用现有项目: {project['name']}")
                return project['id']
        
        # 创建新项目
        project_data = {
            "name": "Jenkins Integration Test",
            "description": "测试 Jenkins 集成的项目",
            "repository_url": "https://github.com/example/test-repo.git",
            "status": "active"
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/projects/projects/", json=project_data)
        
        if response.status_code == 201:
            project = response.json()
            print(f"✅ 创建新项目: {project['name']}")
            return project['id']
        else:
            print(f"❌ 创建项目失败: {response.status_code} - {response.text}")
            return None
    
    def register_jenkins_tool(self, jenkins_url, username, token, project_id):
        """注册 Jenkins 工具"""
        print("🔧 注册 Jenkins 工具...")
        
        tool_data = {
            "name": "jenkins-integration-test",
            "tool_type": "jenkins",
            "base_url": jenkins_url,
            "username": username,
            "token": token,
            "project": project_id,
            "config": {
                "crumb_issuer": True,
                "timeout": 30
            },
            "metadata": {
                "test_integration": True,
                "created_via": "test_script"
            }
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/cicd/tools/", json=tool_data)
        
        if response.status_code == 201:
            tool = response.json()
            print(f"✅ Jenkins 工具注册成功: {tool['name']} (ID: {tool['id']})")
            return tool
        else:
            print(f"❌ Jenkins 工具注册失败: {response.status_code} - {response.text}")
            return None
    
    def health_check_tool(self, tool_id):
        """执行工具健康检查"""
        print("🏥 执行健康检查...")
        
        response = self.session.post(f"{self.base_url}/api/v1/cicd/tools/{tool_id}/health_check/")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 健康检查完成: {result['message']}")
            print(f"   状态: {result['status']}")
            print(f"   是否健康: {result['is_healthy']}")
            return result['is_healthy']
        else:
            print(f"❌ 健康检查失败: {response.status_code} - {response.text}")
            return False
    
    def create_atomic_steps(self):
        """创建原子步骤"""
        print("📋 创建原子步骤...")
        
        steps = [
            {
                "name": "Git Checkout Test",
                "step_type": "fetch_code",
                "description": "测试用的 Git 检出步骤",
                "parameters": {
                    "repository_url": "https://github.com/example/test-repo.git",
                    "branch": "main",
                    "shallow_clone": True
                },
                "is_public": True
            },
            {
                "name": "Echo Build Test",
                "step_type": "build",
                "description": "测试用的构建步骤",
                "parameters": {
                    "commands": ["echo 'Building application...'", "echo 'Build completed!'"]
                },
                "is_public": True
            },
            {
                "name": "Echo Test",
                "step_type": "test",
                "description": "测试用的测试步骤",
                "parameters": {
                    "commands": ["echo 'Running tests...'", "echo 'All tests passed!'"]
                },
                "is_public": True
            }
        ]
        
        created_steps = []
        for step_data in steps:
            response = self.session.post(f"{self.base_url}/api/v1/cicd/atomic-steps/", json=step_data)
            
            if response.status_code == 201:
                step = response.json()
                print(f"  ✅ 创建步骤: {step['name']}")
                created_steps.append(step)
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"  ⏭️  步骤已存在: {step_data['name']}")
            else:
                print(f"  ❌ 创建步骤失败: {step_data['name']} - {response.status_code}")
        
        return created_steps
    
    def create_test_pipeline(self, project_id):
        """创建测试流水线"""
        print("🚀 创建测试流水线...")
        
        pipeline_data = {
            "name": "Jenkins Integration Test Pipeline",
            "description": "用于测试 Jenkins 集成的流水线",
            "project": project_id,
            "config": {
                "steps": [
                    {
                        "name": "Checkout",
                        "type": "fetch_code",
                        "parameters": {
                            "repository_url": "https://github.com/example/test-repo.git",
                            "branch": "main"
                        }
                    },
                    {
                        "name": "Build",
                        "type": "build",
                        "parameters": {
                            "commands": ["echo 'Building...'", "sleep 5", "echo 'Build done!'"]
                        }
                    },
                    {
                        "name": "Test",
                        "type": "test",
                        "parameters": {
                            "commands": ["echo 'Testing...'", "sleep 3", "echo 'Tests passed!'"]
                        }
                    }
                ],
                "environment": {
                    "BUILD_NUMBER": "${BUILD_NUMBER}",
                    "GIT_BRANCH": "${GIT_BRANCH}"
                },
                "timeout": 600
            }
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/pipelines/pipelines/", json=pipeline_data)
        
        if response.status_code == 201:
            pipeline = response.json()
            print(f"✅ 创建流水线成功: {pipeline['name']} (ID: {pipeline['id']})")
            return pipeline
        else:
            print(f"❌ 创建流水线失败: {response.status_code} - {response.text}")
            return None
    
    def execute_pipeline(self, tool_id, pipeline_id):
        """执行流水线"""
        print("🏃 执行流水线...")
        
        execution_data = {
            "pipeline_id": pipeline_id,
            "cicd_tool_id": tool_id,
            "trigger_type": "manual",
            "parameters": {
                "BUILD_NUMBER": str(int(time.time())),
                "GIT_BRANCH": "main",
                "TEST_PARAM": "integration_test"
            }
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/cicd/tools/{tool_id}/execute_pipeline/", json=execution_data)
        
        if response.status_code == 201:
            execution = response.json()
            print(f"✅ 流水线执行已启动: ID {execution['id']}")
            print(f"   外部 ID: {execution.get('external_id', '待分配')}")
            print(f"   状态: {execution['status']}")
            if execution.get('external_url'):
                print(f"   Jenkins URL: {execution['external_url']}")
            return execution
        else:
            print(f"❌ 流水线执行失败: {response.status_code} - {response.text}")
            return None
    
    def monitor_execution(self, execution_id, max_wait=300):
        """监控流水线执行"""
        print(f"👀 监控流水线执行 (最多等待 {max_wait} 秒)...")
        
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < max_wait:
            response = self.session.get(f"{self.base_url}/api/v1/cicd/executions/{execution_id}/")
            
            if response.status_code == 200:
                execution = response.json()
                current_status = execution['status']
                
                if current_status != last_status:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"  [{timestamp}] 状态: {current_status}")
                    last_status = current_status
                
                # 检查是否完成
                if current_status in ['success', 'failed', 'cancelled', 'timeout']:
                    print(f"✅ 执行完成，最终状态: {current_status}")
                    
                    # 获取执行日志
                    self.get_execution_logs(execution_id)
                    return execution
                
                time.sleep(10)  # 每10秒检查一次
            else:
                print(f"❌ 获取执行状态失败: {response.status_code}")
                break
        
        print("⏰ 监控超时")
        return None
    
    def get_execution_logs(self, execution_id):
        """获取执行日志"""
        print("📄 获取执行日志...")
        
        response = self.session.get(f"{self.base_url}/api/v1/cicd/executions/{execution_id}/logs/")
        
        if response.status_code == 200:
            log_data = response.json()
            logs = log_data.get('logs', '')
            
            if logs:
                print("📋 执行日志:")
                print("-" * 50)
                print(logs)
                print("-" * 50)
            else:
                print("⚠️  暂无日志")
        else:
            print(f"❌ 获取日志失败: {response.status_code}")
    
    def run_full_test(self, jenkins_url, jenkins_username, jenkins_token):
        """运行完整测试"""
        print("🧪 开始 AnsFlow Jenkins 集成完整测试")
        print("=" * 60)
        
        # 1. 认证
        if not self.authenticate():
            return False
        
        # 2. 获取项目
        project_id = self.get_or_create_project()
        if not project_id:
            return False
        
        # 3. 注册 Jenkins 工具
        tool = self.register_jenkins_tool(jenkins_url, jenkins_username, jenkins_token, project_id)
        if not tool:
            return False
        
        # 4. 健康检查
        if not self.health_check_tool(tool['id']):
            print("⚠️  健康检查失败，但继续测试...")
        
        # 5. 创建原子步骤
        self.create_atomic_steps()
        
        # 6. 创建测试流水线
        pipeline = self.create_test_pipeline(project_id)
        if not pipeline:
            return False
        
        # 7. 执行流水线
        execution = self.execute_pipeline(tool['id'], pipeline['id'])
        if not execution:
            return False
        
        # 8. 监控执行
        final_execution = self.monitor_execution(execution['id'])
        
        # 9. 显示结果
        print("\n" + "=" * 60)
        print("🎉 测试完成!")
        
        if final_execution:
            print(f"📊 最终状态: {final_execution['status']}")
            print(f"🔗 管理界面: {self.base_url}/admin/cicd_integrations/")
            print(f"📖 API 文档: {self.base_url}/api/schema/swagger-ui/")
            
            if final_execution.get('external_url'):
                print(f"🔗 Jenkins 链接: {final_execution['external_url']}")
            
            return final_execution['status'] == 'success'
        
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AnsFlow Jenkins 集成测试')
    parser.add_argument('--jenkins-url', required=True, help='Jenkins 服务器 URL')
    parser.add_argument('--username', required=True, help='Jenkins 用户名')
    parser.add_argument('--token', required=True, help='Jenkins API Token')
    parser.add_argument('--ansflow-url', default='http://localhost:8000', help='AnsFlow 服务器 URL')
    parser.add_argument('--auth-username', default='admin', help='AnsFlow 用户名')
    parser.add_argument('--auth-password', default='admin', help='AnsFlow 密码')
    
    args = parser.parse_args()
    
    # 创建测试实例
    test = AnsFlowJenkinsTest(args.ansflow_url)
    
    # 运行测试
    success = test.run_full_test(args.jenkins_url, args.username, args.token)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
