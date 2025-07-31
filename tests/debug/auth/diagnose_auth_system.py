#!/usr/bin/env python3
"""
Django认证系统诊断工具
帮助理解不同认证方式的区别
"""

import requests
import json

def test_session_vs_jwt_auth():
    """测试Session认证 vs JWT认证的区别"""
    
    print("🔍 Django认证系统诊断")
    print("=" * 60)
    
    # 测试1: 直接访问API（无认证）
    print("\n=== 测试1: 直接访问API（无认证头） ===")
    try:
        response = requests.get("http://localhost:8000/api/v1/docker/registries/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:100]}...")
        
        if response.status_code == 401:
            print("✅ 正确：REST API要求JWT认证，返回401是正常的")
        else:
            print("⚠️ 意外：API应该返回401")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试2: 尝试获取JWT令牌
    print("\n=== 测试2: 获取JWT令牌 ===")
    try:
        login_data = {"username": "admin", "password": "admin123"}
        response = requests.post("http://localhost:8000/api/v1/auth/token/", json=login_data)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access')
            print("✅ JWT令牌获取成功")
            print(f"Access Token: {access_token[:30]}...")
            
            # 测试3: 使用JWT令牌访问API
            print("\n=== 测试3: 使用JWT令牌访问API ===")
            headers = {"Authorization": f"Bearer {access_token}"}
            
            auth_response = requests.get("http://localhost:8000/api/v1/docker/registries/", headers=headers)
            print(f"状态码: {auth_response.status_code}")
            
            if auth_response.status_code == 200:
                data = auth_response.json()
                print("✅ 使用JWT令牌访问成功！")
                print(f"返回数据: 找到 {len(data.get('results', []))} 个注册表")
            else:
                print(f"❌ 使用JWT令牌访问失败: {auth_response.text}")
                
        else:
            print(f"❌ JWT令牌获取失败: {response.text}")
            print("可能原因:")
            print("1. admin用户不存在")
            print("2. 密码不正确") 
            print("3. JWT配置有问题")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试4: 检查Django管理后台认证状态
    print("\n=== 测试4: Django管理后台认证检查 ===")
    try:
        # 尝试访问admin页面（这里只是检查是否可达）
        admin_response = requests.get("http://localhost:8000/admin/", allow_redirects=False)
        print(f"Admin页面状态码: {admin_response.status_code}")
        
        if admin_response.status_code in [200, 302]:
            print("✅ Django管理后台可访问")
        else:
            print("❌ Django管理后台不可访问")
            
    except Exception as e:
        print(f"❌ 管理后台检查失败: {e}")
    
    # 说明部分
    print("\n" + "=" * 60)
    print("📚 认证系统说明")
    print("=" * 60)
    print()
    print("🔐 Django有两套独立的认证系统:")
    print()
    print("1. 【管理后台认证】")
    print("   - 使用: Session + Cookie")
    print("   - 适用: Django Admin管理界面")
    print("   - 登录方式: /admin/ 页面表单登录")
    print()
    print("2. 【REST API认证】")
    print("   - 使用: JWT Token")
    print("   - 适用: API端点 (/api/v1/...)")
    print("   - 登录方式: POST /api/v1/auth/token/")
    print()
    print("💡 解决方案:")
    print()
    print("如果您要访问API，需要:")
    print("1. 获取JWT令牌: POST /api/v1/auth/token/")
    print("2. 在请求头添加: Authorization: Bearer <token>")
    print()
    print("如果您在浏览器中访问API，会看到401错误是正常的！")

if __name__ == "__main__":
    test_session_vs_jwt_auth()
