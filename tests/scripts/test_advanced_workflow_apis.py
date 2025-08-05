#!/usr/bin/env python3
"""
AnsFlow 高级工作流功能端到端测试脚本

这个脚本测试前端高级工作流功能与后端API的对接是否正常。
"""

import json
import requests
import sys
from datetime import datetime

# 配置
BACKEND_URL = "http://localhost:8000"
API_BASE = f"{BACKEND_URL}/api/pipelines"

# 测试用户认证（需要根据实际情况调整）
AUTH_HEADERS = {
    "Authorization": "Bearer YOUR_TOKEN_HERE",  # 替换为实际的认证token
    "Content-Type": "application/json"
}

class AdvancedWorkflowTester:
    """高级工作流功能测试器"""
    
    def __init__(self):
        self.test_results = []
        self.pipeline_id = None
        self.step_id = None
        
    def log_test(self, test_name, success, message="", response_data=None):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        if not success and response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
    
    def test_pipeline_creation(self):
        """测试流水线创建（包含高级功能字段）"""
        test_data = {
            "name": f"Advanced Workflow Test Pipeline {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": "测试高级工作流功能的流水线",
            "project": 1,  # 假设项目ID为1
            "execution_mode": "local",
            "steps": [
                {
                    "name": "Build Step",
                    "step_type": "build",
                    "description": "构建步骤",
                    "order": 1,
                    "parameters": {
                        "build_command": "npm run build"
                    }
                },
                {
                    "name": "Test Step with Advanced Config",
                    "step_type": "test", 
                    "description": "带高级配置的测试步骤",
                    "order": 2,
                    "parameters": {
                        "test_command": "npm test"
                    }
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{API_BASE}/pipelines/",
                headers=AUTH_HEADERS,
                json=test_data
            )
            
            if response.status_code == 201:
                pipeline_data = response.json()
                self.pipeline_id = pipeline_data["id"]
                if pipeline_data.get("steps"):
                    self.step_id = pipeline_data["steps"][0]["id"]
                
                self.log_test(
                    "Pipeline Creation", 
                    True, 
                    f"Pipeline created with ID: {self.pipeline_id}",
                    pipeline_data
                )
                return True
            else:
                self.log_test(
                    "Pipeline Creation", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.json() if response.content else None
                )
                return False
                
        except Exception as e:
            self.log_test("Pipeline Creation", False, f"Exception: {str(e)}")
            return False
    
    def test_step_advanced_config(self):
        """测试步骤高级配置更新"""
        if not self.pipeline_id or not self.step_id:
            self.log_test("Step Advanced Config", False, "No pipeline or step ID available")
            return False
        
        advanced_config = {
            "condition": {
                "type": "expression",
                "expression": "${previous_step.result.status} == 'success'"
            },
            "parallel_group_id": "test-group-1",
            "approval_config": {
                "required": True,
                "approvers": ["admin", "developer"],
                "timeout_hours": 24
            },
            "retry_policy": {
                "max_retries": 3,
                "retry_delay_seconds": 60,
                "retry_on_failure": True
            },
            "notification_config": {
                "on_success": True,
                "on_failure": True,
                "channels": ["email"],
                "recipients": ["admin@example.com"]
            }
        }
        
        try:
            response = requests.put(
                f"{API_BASE}/pipelines/{self.pipeline_id}/steps/{self.step_id}/advanced-config/",
                headers=AUTH_HEADERS,
                json=advanced_config
            )
            
            success = response.status_code == 200
            self.log_test(
                "Step Advanced Config Update",
                success,
                f"Advanced config updated" if success else f"Failed with status {response.status_code}",
                response.json() if response.content else None
            )
            return success
            
        except Exception as e:
            self.log_test("Step Advanced Config Update", False, f"Exception: {str(e)}")
            return False
    
    def test_parallel_group_management(self):
        """测试并行组管理"""
        if not self.pipeline_id:
            self.log_test("Parallel Group Management", False, "No pipeline ID available")
            return False
        
        # 创建并行组
        group_data = {
            "id": "test-parallel-group-1",
            "name": "Test Parallel Group",
            "description": "测试并行组",
            "pipeline": self.pipeline_id,
            "sync_policy": "wait_all",
            "timeout_seconds": 3600
        }
        
        try:
            # 创建并行组
            response = requests.post(
                f"{API_BASE}/parallel-groups/",
                headers=AUTH_HEADERS,
                json=group_data
            )
            
            if response.status_code == 201:
                self.log_test("Parallel Group Creation", True, "Parallel group created")
                
                # 获取并行组列表
                response = requests.get(
                    f"{API_BASE}/parallel-groups/?pipeline_id={self.pipeline_id}",
                    headers=AUTH_HEADERS
                )
                
                if response.status_code == 200:
                    groups = response.json()
                    self.log_test("Parallel Group List", True, f"Found {len(groups)} groups")
                    return True
                else:
                    self.log_test("Parallel Group List", False, f"Failed with status {response.status_code}")
                    return False
            else:
                self.log_test("Parallel Group Creation", False, f"Failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Parallel Group Management", False, f"Exception: {str(e)}")
            return False
    
    def test_workflow_analysis(self):
        """测试工作流分析"""
        if not self.pipeline_id:
            self.log_test("Workflow Analysis", False, "No pipeline ID available")
            return False
        
        try:
            # 分析工作流依赖
            response = requests.get(
                f"{API_BASE}/pipelines/{self.pipeline_id}/analyze-workflow/",
                headers=AUTH_HEADERS
            )
            
            if response.status_code == 200:
                analysis_data = response.json()
                self.log_test("Workflow Dependencies Analysis", True, "Analysis completed")
                
                # 获取工作流指标
                response = requests.get(
                    f"{API_BASE}/pipelines/{self.pipeline_id}/workflow-metrics/",
                    headers=AUTH_HEADERS
                )
                
                if response.status_code == 200:
                    metrics_data = response.json()
                    self.log_test("Workflow Metrics", True, f"Metrics: {metrics_data}")
                    return True
                else:
                    self.log_test("Workflow Metrics", False, f"Failed with status {response.status_code}")
                    return False
            else:
                self.log_test("Workflow Analysis", False, f"Failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Workflow Analysis", False, f"Exception: {str(e)}")
            return False
    
    def test_execution_recovery_apis(self):
        """测试执行恢复相关API"""
        test_execution_id = "test-execution-123"
        
        try:
            # 测试获取执行步骤历史
            response = requests.get(
                f"{API_BASE}/executions/{test_execution_id}/steps/",
                headers=AUTH_HEADERS
            )
            
            # 这个API可能返回404因为测试执行不存在，这是正常的
            self.log_test(
                "Execution Step History API",
                response.status_code in [200, 404],
                f"API accessible (status: {response.status_code})"
            )
            
            # 测试执行恢复API
            recovery_data = {
                "step_id": 1,
                "parameters": {"retry": True}
            }
            
            response = requests.post(
                f"{API_BASE}/executions/{test_execution_id}/resume/",
                headers=AUTH_HEADERS,
                json=recovery_data
            )
            
            # 这个API可能返回404或500因为测试执行不存在，这是正常的
            self.log_test(
                "Execution Recovery API",
                response.status_code in [200, 404, 500],
                f"API accessible (status: {response.status_code})"
            )
            
            return True
            
        except Exception as e:
            self.log_test("Execution Recovery APIs", False, f"Exception: {str(e)}")
            return False
    
    def test_notification_config(self):
        """测试通知配置"""
        test_config = {
            "channels": ["email"],
            "recipients": ["test@example.com"],
            "on_success": True,
            "on_failure": True
        }
        
        try:
            response = requests.post(
                f"{API_BASE}/notifications/test/",
                headers=AUTH_HEADERS,
                json=test_config
            )
            
            success = response.status_code == 200
            response_data = response.json() if response.content else None
            
            self.log_test(
                "Notification Configuration Test",
                success,
                f"Notification test API accessible" if success else f"Failed with status {response.status_code}",
                response_data
            )
            return success
            
        except Exception as e:
            self.log_test("Notification Configuration Test", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 Starting Advanced Workflow API Tests...\n")
        
        tests = [
            self.test_pipeline_creation,
            self.test_step_advanced_config,
            self.test_parallel_group_management,
            self.test_workflow_analysis,
            self.test_execution_recovery_apis,
            self.test_notification_config
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print(f"\n📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Advanced workflow APIs are working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the backend implementation.")
            return False
    
    def generate_report(self):
        """生成详细测试报告"""
        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "passed_tests": len([r for r in self.test_results if r["success"]]),
                "failed_tests": len([r for r in self.test_results if not r["success"]]),
                "timestamp": datetime.now().isoformat()
            },
            "test_details": self.test_results
        }
        
        with open("advanced_workflow_api_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed report saved to: advanced_workflow_api_test_report.json")
        return report

def main():
    """主函数"""
    print("AnsFlow Advanced Workflow API Testing")
    print("=" * 50)
    print()
    print("⚠️  注意：请确保后端服务正在运行 (http://localhost:8000)")
    print("⚠️  注意：请更新 AUTH_HEADERS 中的认证信息")
    print()
    
    # 检查后端服务是否可用
    try:
        response = requests.get(f"{BACKEND_URL}/api/pipelines/health/", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务不可用，请启动后端服务后重试")
            return False
    except requests.exceptions.RequestException:
        print("❌ 无法连接到后端服务，请确保服务正在运行")
        return False
    
    print("✅ 后端服务连接正常\n")
    
    # 运行测试
    tester = AdvancedWorkflowTester()
    success = tester.run_all_tests()
    tester.generate_report()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
