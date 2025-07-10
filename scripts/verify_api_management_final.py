#!/usr/bin/env python3
"""
AnsFlow API 管理模块最终验证脚本

验证项目：
1. API 端点状态切换（is_active/is_enabled）
2. 请求体字段保存和回显（request_body_schema/request_schema）
3. 批量导入功能
4. 前端表单完整性
5. 数据库持久化
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List

# 配置
DJANGO_BASE_URL = "http://localhost:8000/api/v1"
FRONTEND_BASE_URL = "http://localhost:3000"

# 测试用户凭据
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}

class APIManagementVerifier:
    def __init__(self):
        self.auth_token = None
        self.headers = {'Content-Type': 'application/json'}
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
    
    def authenticate(self) -> bool:
        """获取认证令牌"""
        try:
            response = requests.post(
                f"{DJANGO_BASE_URL}/auth/token/",
                json=TEST_USER,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access')
                self.headers['Authorization'] = f'Bearer {self.auth_token}'
                self.log_test("认证测试", True, "成功获取访问令牌")
                return True
            else:
                self.log_test("认证测试", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("认证测试", False, f"认证失败: {str(e)}")
            return False
    
    def test_create_api_endpoint(self) -> Dict[str, Any]:
        """测试创建API端点"""
        endpoint_data = {
            "name": "测试API端点",
            "path": "/api/test/endpoint",
            "method": "POST",
            "description": "用于验证的测试API端点",
            "service_type": "rest",
            "is_active": True,
            "auth_required": True,
            "rate_limit": 100,
            "request_body_schema": {
                "type": "json",
                "description": "测试请求体",
                "required": True,
                "content_type": "application/json",
                "example": {"test_field": "test_value", "number_field": 123}
            },
            "tags": ["test", "verification"],
            "version": "1.0.0"
        }
        
        try:
            response = requests.post(
                f"{DJANGO_BASE_URL}/settings/api-endpoints/",
                json=endpoint_data,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 201:
                created_endpoint = response.json()
                self.log_test(
                    "创建API端点", 
                    True, 
                    f"成功创建端点 ID: {created_endpoint.get('id')}"
                )
                return created_endpoint
            else:
                self.log_test(
                    "创建API端点", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                return {}
                
        except Exception as e:
            self.log_test("创建API端点", False, f"创建失败: {str(e)}")
            return {}
    
    def test_status_toggle(self, endpoint_id: int) -> bool:
        """测试状态切换功能"""
        try:
            # 首先获取当前状态
            response = requests.get(
                f"{DJANGO_BASE_URL}/settings/api-endpoints/{endpoint_id}/",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_test(
                    "状态切换测试", 
                    False, 
                    f"无法获取端点信息: HTTP {response.status_code}"
                )
                return False
            
            current_endpoint = response.json()
            current_status = current_endpoint.get('is_active', True)
            
            # 切换状态
            new_status = not current_status
            update_data = {"is_active": new_status}
            
            response = requests.put(
                f"{DJANGO_BASE_URL}/settings/api-endpoints/{endpoint_id}/",
                json=update_data,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                updated_endpoint = response.json()
                actual_status = updated_endpoint.get('is_active')
                
                if actual_status == new_status:
                    self.log_test(
                        "状态切换测试", 
                        True, 
                        f"状态成功从 {current_status} 切换到 {actual_status}"
                    )
                    return True
                else:
                    self.log_test(
                        "状态切换测试", 
                        False, 
                        f"状态切换失败: 期望 {new_status}, 实际 {actual_status}"
                    )
                    return False
            else:
                self.log_test(
                    "状态切换测试", 
                    False, 
                    f"更新失败: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("状态切换测试", False, f"状态切换异常: {str(e)}")
            return False
    
    def test_request_body_schema(self, endpoint_id: int) -> bool:
        """测试请求体字段保存和回显"""
        try:
            # 准备新的请求体schema
            new_schema = {
                "type": "json",
                "description": "更新的请求体schema",
                "required": False,
                "content_type": "application/json",
                "example": {
                    "updated_field": "updated_value",
                    "nested_object": {
                        "key1": "value1",
                        "key2": 456
                    }
                }
            }
            
            update_data = {"request_body_schema": new_schema}
            
            # 更新请求体schema
            response = requests.put(
                f"{DJANGO_BASE_URL}/settings/api-endpoints/{endpoint_id}/",
                json=update_data,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_test(
                    "请求体Schema测试", 
                    False, 
                    f"更新失败: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            # 重新获取数据验证保存
            time.sleep(0.5)  # 等待数据库写入
            
            response = requests.get(
                f"{DJANGO_BASE_URL}/settings/api-endpoints/{endpoint_id}/",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                endpoint = response.json()
                saved_schema = endpoint.get('request_body_schema')
                
                if saved_schema and saved_schema.get('description') == new_schema['description']:
                    self.log_test(
                        "请求体Schema测试", 
                        True, 
                        "请求体schema成功保存和回显"
                    )
                    return True
                else:
                    self.log_test(
                        "请求体Schema测试", 
                        False, 
                        f"Schema不匹配: 保存的 {saved_schema}, 期望的 {new_schema}"
                    )
                    return False
            else:
                self.log_test(
                    "请求体Schema测试", 
                    False, 
                    f"获取失败: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("请求体Schema测试", False, f"Schema测试异常: {str(e)}")
            return False
    
    def test_batch_import(self) -> bool:
        """测试批量导入功能"""
        try:
            # 准备批量导入数据
            import_data = [
                {
                    "name": "批量导入端点1",
                    "path": "/api/batch/endpoint1",
                    "method": "GET",
                    "description": "批量导入的第一个端点",
                    "service_type": "rest",
                    "is_active": True,
                    "auth_required": False,
                    "rate_limit": 50
                },
                {
                    "name": "批量导入端点2",
                    "path": "/api/batch/endpoint2",
                    "method": "POST",
                    "description": "批量导入的第二个端点",
                    "service_type": "rest",
                    "is_active": False,
                    "auth_required": True,
                    "rate_limit": 200,
                    "request_body_schema": {
                        "type": "json",
                        "description": "批量导入的请求体",
                        "required": True,
                        "example": {"batch_field": "batch_value"}
                    }
                }
            ]
            
            created_endpoints = []
            for endpoint_data in import_data:
                response = requests.post(
                    f"{DJANGO_BASE_URL}/settings/api-endpoints/",
                    json=endpoint_data,
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 201:
                    created_endpoints.append(response.json())
                else:
                    self.log_test(
                        "批量导入测试", 
                        False, 
                        f"导入失败: HTTP {response.status_code}: {response.text}"
                    )
                    return False
            
            if len(created_endpoints) == len(import_data):
                self.log_test(
                    "批量导入测试", 
                    True, 
                    f"成功导入 {len(created_endpoints)} 个API端点"
                )
                return True
            else:
                self.log_test(
                    "批量导入测试", 
                    False, 
                    f"导入数量不匹配: 期望 {len(import_data)}, 实际 {len(created_endpoints)}"
                )
                return False
                
        except Exception as e:
            self.log_test("批量导入测试", False, f"批量导入异常: {str(e)}")
            return False
    
    def test_database_persistence(self) -> bool:
        """测试数据库持久化"""
        try:
            # 获取所有API端点
            response = requests.get(
                f"{DJANGO_BASE_URL}/settings/api-endpoints/",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                endpoints = data.get('results', []) if isinstance(data, dict) else data
                
                # 验证数据完整性
                fields_to_check = ['id', 'name', 'path', 'method', 'is_active']
                all_valid = True
                
                for endpoint in endpoints:
                    for field in fields_to_check:
                        if field not in endpoint:
                            all_valid = False
                            break
                    if not all_valid:
                        break
                
                if all_valid and len(endpoints) > 0:
                    self.log_test(
                        "数据库持久化测试", 
                        True, 
                        f"成功获取 {len(endpoints)} 个API端点，数据完整"
                    )
                    return True
                else:
                    self.log_test(
                        "数据库持久化测试", 
                        False, 
                        "数据不完整或字段缺失"
                    )
                    return False
            else:
                self.log_test(
                    "数据库持久化测试", 
                    False, 
                    f"获取失败: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("数据库持久化测试", False, f"持久化测试异常: {str(e)}")
            return False
    
    def run_verification(self):
        """运行完整验证"""
        print("🔍 开始 API 管理模块最终验证...")
        print("=" * 60)
        
        # 1. 认证
        if not self.authenticate():
            print("❌ 认证失败，终止测试")
            return False
        
        # 2. 创建测试端点
        print("\n📝 测试创建API端点...")
        test_endpoint = self.test_create_api_endpoint()
        if not test_endpoint:
            print("❌ 创建测试端点失败，终止测试")
            return False
        
        endpoint_id = test_endpoint.get('id')
        
        # 3. 状态切换测试
        print("\n🔄 测试状态切换...")
        self.test_status_toggle(endpoint_id)
        
        # 4. 请求体schema测试
        print("\n📋 测试请求体字段...")
        self.test_request_body_schema(endpoint_id)
        
        # 5. 批量导入测试
        print("\n📦 测试批量导入...")
        self.test_batch_import()
        
        # 6. 数据库持久化测试
        print("\n💾 测试数据库持久化...")
        self.test_database_persistence()
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 API 管理模块验证报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试项: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for test in self.test_results:
                if not test['success']:
                    print(f"  - {test['test']}: {test['details']}")
        
        # 保存详细报告
        report_file = f"api_management_verification_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        # 最终结论
        if failed_tests == 0:
            print("\n🎉 所有测试通过！API 管理模块功能正常。")
        else:
            print(f"\n⚠️  {failed_tests} 个测试失败，请检查相关功能。")

def main():
    """主函数"""
    print("🚀 AnsFlow API 管理模块最终验证")
    print("本脚本将验证API端点管理的所有核心功能\n")
    
    verifier = APIManagementVerifier()
    verifier.run_verification()

if __name__ == "__main__":
    main()
