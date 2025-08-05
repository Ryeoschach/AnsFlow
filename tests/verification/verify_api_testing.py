#!/usr/bin/env python3
"""
AnsFlow API端点测试功能验证脚本

验证以下功能：
1. API端点测试接口
2. 请求参数处理
3. 请求体处理
4. 请求头处理
5. 响应时间计算
6. 错误处理
"""

import requests
import json
import time
import os
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class APITestingVerifier:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
    def authenticate(self):
        """认证并获取token"""
        print("🔐 正在进行身份认证...")
        
        # 尝试使用环境变量中的token
        env_token = os.getenv('ANSFLOW_AUTH_TOKEN')
        if env_token:
            self.auth_token = env_token
            self.session.headers.update({'Authorization': f'Bearer {env_token}'})
            print("✅ 使用环境变量中的认证token")
            return True
        
        # 尝试登录获取token
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login/", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token') or data.get('token')
                if self.auth_token:
                    self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                    print("✅ 登录认证成功")
                    return True
                    
        except Exception as e:
            print(f"❌ 认证失败: {e}")
            
        print("⚠️ 未配置认证，将尝试匿名访问")
        return False
    
    def create_test_endpoint(self) -> Dict[str, Any]:
        """创建用于测试的API端点"""
        print("📝 创建测试API端点...")
        
        endpoint_data = {
            "name": "测试健康检查接口",
            "path": "/api/v1/health/",
            "method": "GET",
            "description": "用于API测试功能验证的健康检查接口",
            "service_type": "django",
            "auth_required": False,
            "is_active": True,
            "tags": ["test", "health"],
            "request_body_schema": None
        }
        
        try:
            response = self.session.post(f"{API_BASE}/settings/api-endpoints/", json=endpoint_data)
            
            if response.status_code == 201:
                endpoint = response.json()
                print(f"✅ 测试端点创建成功: {endpoint['name']} (ID: {endpoint['id']})")
                return endpoint
            else:
                print(f"❌ 创建测试端点失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 创建测试端点异常: {e}")
            return None
    
    def create_post_test_endpoint(self) -> Dict[str, Any]:
        """创建用于POST测试的API端点"""
        print("📝 创建POST测试API端点...")
        
        endpoint_data = {
            "name": "测试POST接口",
            "path": "/api/v1/settings/api-endpoints/",
            "method": "POST",
            "description": "用于POST请求测试的接口",
            "service_type": "django",
            "auth_required": True,
            "is_active": True,
            "tags": ["test", "post"],
            "request_body_schema": {
                "type": "json",
                "description": "创建API端点的请求体",
                "required": True,
                "example": {
                    "name": "示例接口",
                    "path": "/test/",
                    "method": "GET"
                },
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "接口名称"},
                        "path": {"type": "string", "description": "接口路径"},
                        "method": {"type": "string", "description": "HTTP方法"}
                    },
                    "required": ["name", "path", "method"]
                }
            }
        }
        
        try:
            response = self.session.post(f"{API_BASE}/settings/api-endpoints/", json=endpoint_data)
            
            if response.status_code == 201:
                endpoint = response.json()
                print(f"✅ POST测试端点创建成功: {endpoint['name']} (ID: {endpoint['id']})")
                return endpoint
            else:
                print(f"❌ 创建POST测试端点失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 创建POST测试端点异常: {e}")
            return None
    
    def test_get_endpoint(self, endpoint_id: int) -> bool:
        """测试GET端点"""
        print(f"🧪 测试GET端点 (ID: {endpoint_id})...")
        
        test_data = {
            "params": {},
            "headers": {
                "X-Test-Header": "API-Testing"
            }
        }
        
        try:
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/settings/api-endpoints/{endpoint_id}/test_endpoint/", 
                json=test_data
            )
            end_time = time.time()
            
            test_duration = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ GET测试成功:")
                print(f"   状态: {'成功' if result.get('success') else '失败'}")
                print(f"   状态码: {result.get('status_code')}")
                print(f"   响应时间: {result.get('response_time_ms', 0):.2f}ms")
                print(f"   测试耗时: {test_duration:.2f}ms")
                
                if result.get('response_data'):
                    print(f"   响应数据大小: {len(str(result['response_data']))} 字符")
                
                return result.get('success', False)
            else:
                print(f"❌ GET测试失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ GET测试异常: {e}")
            return False
    
    def test_post_endpoint_with_params(self, endpoint_id: int) -> bool:
        """测试带参数的POST端点"""
        print(f"🧪 测试POST端点带参数 (ID: {endpoint_id})...")
        
        test_data = {
            "params": {
                "test_param": "test_value"
            },
            "body": {
                "name": "测试接口 - API Testing",
                "path": "/api/test/",
                "method": "GET",
                "description": "通过API测试功能创建的接口"
            },
            "headers": {
                "Content-Type": "application/json",
                "X-Test-Source": "API-Testing"
            }
        }
        
        try:
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/settings/api-endpoints/{endpoint_id}/test_endpoint/", 
                json=test_data
            )
            end_time = time.time()
            
            test_duration = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ POST测试成功:")
                print(f"   状态: {'成功' if result.get('success') else '失败'}")
                print(f"   状态码: {result.get('status_code')}")
                print(f"   响应时间: {result.get('response_time_ms', 0):.2f}ms")
                print(f"   测试耗时: {test_duration:.2f}ms")
                print(f"   请求URL: {result.get('request_url', 'N/A')}")
                
                if result.get('response_data'):
                    response_data = result['response_data']
                    if isinstance(response_data, dict) and 'id' in response_data:
                        print(f"   创建的接口ID: {response_data['id']}")
                        # 清理创建的测试接口
                        self.cleanup_endpoint(response_data['id'])
                
                return result.get('success', False)
            else:
                print(f"❌ POST测试失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ POST测试异常: {e}")
            return False
    
    def test_invalid_endpoint(self, endpoint_id: int) -> bool:
        """测试无效端点（用于错误处理验证）"""
        print(f"🧪 测试错误处理 (ID: {endpoint_id})...")
        
        # 创建一个指向不存在路径的测试端点
        invalid_endpoint_data = {
            "name": "无效测试端点",
            "path": "/api/v1/nonexistent/endpoint/",
            "method": "GET",
            "description": "用于测试错误处理的无效端点",
            "service_type": "django",
            "auth_required": False,
            "is_active": True,
            "tags": ["test", "error"]
        }
        
        try:
            # 创建无效端点
            response = self.session.post(f"{API_BASE}/settings/api-endpoints/", json=invalid_endpoint_data)
            if response.status_code != 201:
                print(f"❌ 无法创建无效测试端点")
                return False
            
            invalid_endpoint = response.json()
            invalid_endpoint_id = invalid_endpoint['id']
            
            # 测试无效端点
            test_data = {"params": {}, "headers": {}}
            
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/settings/api-endpoints/{invalid_endpoint_id}/test_endpoint/", 
                json=test_data
            )
            end_time = time.time()
            
            test_duration = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 错误处理测试成功:")
                print(f"   状态: {'成功' if result.get('success') else '失败'}")
                print(f"   状态码: {result.get('status_code', 'N/A')}")
                print(f"   错误信息: {result.get('error', 'N/A')}")
                print(f"   测试耗时: {test_duration:.2f}ms")
                
                # 清理无效端点
                self.cleanup_endpoint(invalid_endpoint_id)
                
                # 错误处理测试应该返回失败状态但HTTP状态码为200
                return not result.get('success', True)
            else:
                print(f"❌ 错误处理测试失败: {response.status_code}")
                self.cleanup_endpoint(invalid_endpoint_id)
                return False
                
        except Exception as e:
            print(f"❌ 错误处理测试异常: {e}")
            return False
    
    def cleanup_endpoint(self, endpoint_id: int):
        """清理测试端点"""
        try:
            response = self.session.delete(f"{API_BASE}/settings/api-endpoints/{endpoint_id}/")
            if response.status_code == 204:
                print(f"🧹 清理端点 {endpoint_id} 成功")
            else:
                print(f"⚠️ 清理端点 {endpoint_id} 失败: {response.status_code}")
        except Exception as e:
            print(f"⚠️ 清理端点 {endpoint_id} 异常: {e}")
    
    def verify_frontend_integration(self) -> bool:
        """验证前端集成"""
        print("🌐 验证前端集成...")
        
        try:
            # 检查前端是否可访问
            frontend_response = requests.get("http://localhost:5173", timeout=5)
            if frontend_response.status_code == 200:
                print("✅ 前端服务运行正常")
                return True
            else:
                print(f"⚠️ 前端服务状态异常: {frontend_response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 无法访问前端服务: {e}")
            return False
    
    def run_verification(self):
        """运行完整验证"""
        print("=" * 60)
        print("🚀 开始API端点测试功能验证")
        print("=" * 60)
        
        # 认证
        auth_success = self.authenticate()
        
        # 验证前端
        frontend_ok = self.verify_frontend_integration()
        
        # 创建测试端点
        get_endpoint = self.create_test_endpoint()
        post_endpoint = self.create_post_test_endpoint()
        
        results = []
        
        if get_endpoint:
            # 测试GET端点
            get_success = self.test_get_endpoint(get_endpoint['id'])
            results.append(("GET端点测试", get_success))
            
            # 清理GET测试端点
            self.cleanup_endpoint(get_endpoint['id'])
        
        if post_endpoint:
            # 测试POST端点
            post_success = self.test_post_endpoint_with_params(post_endpoint['id'])
            results.append(("POST端点测试", post_success))
            
            # 测试错误处理
            error_success = self.test_invalid_endpoint(post_endpoint['id'])
            results.append(("错误处理测试", error_success))
            
            # 清理POST测试端点
            self.cleanup_endpoint(post_endpoint['id'])
        
        # 汇总结果
        print("=" * 60)
        print("📊 验证结果汇总")
        print("=" * 60)
        
        success_count = 0
        total_count = len(results)
        
        for test_name, success in results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"{test_name}: {status}")
            if success:
                success_count += 1
        
        print(f"\n前端服务: {'✅ 正常' if frontend_ok else '❌ 异常'}")
        print(f"认证状态: {'✅ 成功' if auth_success else '⚠️ 跳过'}")
        
        overall_success = success_count == total_count
        print(f"\n总体结果: {success_count}/{total_count} 测试通过")
        
        if overall_success:
            print("🎉 所有API测试功能验证通过！")
        else:
            print("⚠️ 部分测试失败，请检查相关功能")
        
        print("\n💡 现在您可以:")
        print("1. 访问 http://localhost:5173/")
        print("2. 进入 Settings → API接口管理")
        print("3. 点击任意API端点的测试按钮")
        print("4. 体验完整的API测试功能")
        
        return overall_success

if __name__ == "__main__":
    verifier = APITestingVerifier()
    verifier.run_verification()
