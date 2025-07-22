#!/usr/bin/env python3
"""
获取JWT令牌并测试Docker注册表API
"""

import requests
import json

def get_jwt_token(username="admin", password="admin123"):
    """获取JWT令牌"""
    url = "http://localhost:8000/api/v1/auth/token/"
    data = {
        "username": username,
        "password": password
    }
    
    print(f"🔐 正在使用用户 '{username}' 获取JWT令牌...")
    
    try:
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access')
            refresh_token = token_data.get('refresh')
            
            print("✅ JWT令牌获取成功!")
            print(f"Access Token: {access_token[:50]}...")
            print(f"Refresh Token: {refresh_token[:50]}...")
            
            return access_token
        else:
            print(f"❌ 获取令牌失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def test_api_with_token(token):
    """使用JWT令牌测试API"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n📋 测试Docker注册表API...")
    
    # 测试GET请求
    print("\n1. 测试GET /api/v1/docker/registries")
    try:
        response = requests.get(
            "http://localhost:8000/api/v1/docker/registries",
            headers=headers,
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功! 找到 {len(data.get('results', []))} 个注册表")
            for i, registry in enumerate(data.get('results', [])[:3]):
                print(f"  - {i+1}. {registry.get('name', 'Unknown')} ({registry.get('registry_type', 'Unknown')})")
        else:
            print(f"❌ 失败: {response.text}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 测试POST请求
    print("\n2. 测试POST /api/v1/docker/registries")
    test_data = {
        "name": "测试注册表JWT",
        "url": "https://test-jwt.example.com",
        "registry_type": "dockerhub",
        "description": "JWT令牌测试注册表"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/docker/registries",
            headers=headers,
            json=test_data,
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            registry_id = data.get('id')
            print(f"✅ 成功创建注册表! ID: {registry_id}")
            
            # 删除测试数据
            print(f"\n3. 清理测试数据 (DELETE /api/v1/docker/registries/{registry_id}/)")
            delete_response = requests.delete(
                f"http://localhost:8000/api/v1/docker/registries/{registry_id}/",
                headers=headers,
                timeout=10
            )
            
            if delete_response.status_code in [200, 204]:
                print("✅ 测试数据清理成功")
            else:
                print(f"⚠️ 清理失败: {delete_response.status_code}")
        else:
            print(f"❌ 创建失败: {response.text}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def main():
    print("🚀 AnsFlow Docker注册表API JWT认证测试")
    print("=" * 50)
    
    # 获取JWT令牌
    token = get_jwt_token()
    
    if token:
        # 测试API
        test_api_with_token(token)
        
        print("\n" + "=" * 50)
        print("🎉 测试完成!")
        print("\n💡 如何在您的应用中使用:")
        print("1. POST /api/v1/auth/token/ 获取JWT令牌")
        print("2. 在请求头中添加: Authorization: Bearer <token>")
        print("3. 然后就可以正常访问所有API了")
    else:
        print("\n❌ 无法获取JWT令牌，请检查:")
        print("1. Django服务是否运行在 localhost:8000")
        print("2. admin用户是否存在且密码正确")
        print("3. JWT配置是否正确")

if __name__ == "__main__":
    main()
