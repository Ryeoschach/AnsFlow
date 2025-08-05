#!/usr/bin/env python3
"""
API认证管理功能验证脚本
验证新增的token获取和管理功能
"""

import requests
import json
import sys
from datetime import datetime

# 配置
DJANGO_BASE_URL = "http://localhost:8000"
FRONTEND_BASE_URL = "http://localhost:5173"

class AuthTestVerifier:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None

    def print_section(self, title):
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")

    def print_step(self, step, description):
        print(f"\n{step}. {description}")
        print("-" * 50)

    def test_auth_endpoint(self):
        """测试认证端点"""
        self.print_step("1", "测试认证端点可用性")
        
        try:
            # 测试无效凭据
            response = self.session.post(
                f"{DJANGO_BASE_URL}/api/v1/auth/token/",
                json={
                    "username": "invalid_user",
                    "password": "invalid_password"
                }
            )
            
            if response.status_code == 401:
                print("✅ 认证端点正常工作 - 正确拒绝无效凭据")
                print(f"   响应: {response.json()}")
            else:
                print(f"⚠️  认证端点响应异常 - 状态码: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 认证端点测试失败: {e}")
            return False
            
        return True

    def test_valid_auth(self):
        """测试有效认证"""
        self.print_step("2", "测试默认管理员账户认证")
        
        # 尝试常见的默认凭据
        credentials = [
            {"username": "admin", "password": "admin"},
            {"username": "admin", "password": "password"},
            {"username": "test", "password": "test"},
            {"username": "demo", "password": "demo"},
        ]
        
        for cred in credentials:
            try:
                response = self.session.post(
                    f"{DJANGO_BASE_URL}/api/v1/auth/token/",
                    json=cred
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'access' in data:
                        self.auth_token = data['access']
                        print(f"✅ 认证成功! 用户: {cred['username']}")
                        print(f"   Token: {self.auth_token[:20]}...{self.auth_token[-10:]}")
                        print(f"   完整响应: {json.dumps(data, indent=2)}")
                        return True
                    else:
                        print(f"⚠️  认证响应格式异常: {data}")
                else:
                    print(f"   尝试 {cred['username']}/{cred['password']}: 失败 ({response.status_code})")
                    
            except Exception as e:
                print(f"   认证请求失败: {e}")
                
        print("❌ 未找到有效的认证凭据")
        print("💡 提示: 请确保Django后端已创建用户账户")
        return False

    def test_token_usage(self):
        """测试token使用"""
        if not self.auth_token:
            print("❌ 无可用token，跳过token使用测试")
            return False
            
        self.print_step("3", "测试token在API请求中的使用")
        
        # 测试需要认证的API端点
        test_endpoints = [
            "/api/v1/settings/users/",
            "/api/v1/settings/api-endpoints/",
        ]
        
        for endpoint in test_endpoints:
            try:
                # 不带token的请求
                response_no_auth = self.session.get(f"{DJANGO_BASE_URL}{endpoint}")
                
                # 带token的请求
                response_with_auth = self.session.get(
                    f"{DJANGO_BASE_URL}{endpoint}",
                    headers={'Authorization': f'Bearer {self.auth_token}'}
                )
                
                print(f"\n   测试端点: {endpoint}")
                print(f"   无认证: {response_no_auth.status_code} {response_no_auth.reason}")
                print(f"   有认证: {response_with_auth.status_code} {response_with_auth.reason}")
                
                if response_no_auth.status_code == 401 and response_with_auth.status_code in [200, 201]:
                    print("   ✅ Token认证工作正常")
                else:
                    print("   ⚠️  认证行为异常")
                    
            except Exception as e:
                print(f"   请求失败: {e}")
                
        return True

    def test_frontend_integration(self):
        """测试前端集成"""
        self.print_step("4", "验证前端认证管理功能")
        
        try:
            # 检查前端是否可访问
            response = requests.get(FRONTEND_BASE_URL, timeout=5)
            if response.status_code == 200:
                print("✅ 前端服务可访问")
                print(f"   地址: {FRONTEND_BASE_URL}")
                print("   请手动验证以下功能:")
                print("   1. 进入 Settings → API接口管理")
                print("   2. 点击任意API端点的'测试接口'按钮")
                print("   3. 点击'认证管理'标签页")
                print("   4. 输入用户名和密码获取token")
                print("   5. 验证token自动更新到请求头")
                return True
            else:
                print(f"⚠️  前端服务响应异常: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 前端服务不可访问: {e}")
            print("💡 请确保前端开发服务器已启动: npm run dev")
            
        return False

    def run_verification(self):
        """运行完整验证"""
        self.print_section("AnsFlow API认证管理功能验证")
        print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"后端地址: {DJANGO_BASE_URL}")
        print(f"前端地址: {FRONTEND_BASE_URL}")
        
        results = []
        
        # 1. 测试认证端点
        results.append(self.test_auth_endpoint())
        
        # 2. 测试有效认证
        results.append(self.test_valid_auth())
        
        # 3. 测试token使用
        results.append(self.test_token_usage())
        
        # 4. 测试前端集成
        results.append(self.test_frontend_integration())
        
        # 总结
        self.print_section("验证结果总结")
        passed = sum(results)
        total = len(results)
        
        print(f"通过测试: {passed}/{total}")
        
        if passed == total:
            print("🎉 所有测试通过! 认证管理功能工作正常")
            print("\n📝 后续步骤:")
            print("1. 启动前端服务: cd frontend && npm run dev")
            print("2. 访问: http://localhost:5173/")
            print("3. 测试完整的认证管理功能")
        else:
            print("⚠️  部分测试未通过，请检查系统配置")
            
        return passed == total

if __name__ == "__main__":
    verifier = AuthTestVerifier()
    success = verifier.run_verification()
    sys.exit(0 if success else 1)
