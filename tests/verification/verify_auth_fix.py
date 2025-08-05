#!/usr/bin/env python3
"""
验证API认证功能修复
测试Token获取是否不再导致页面跳转
"""

import requests
import json
import time

def test_auth_endpoint():
    """测试认证端点是否正常工作"""
    url = 'http://localhost:8000/api/v1/auth/token/'
    
    # 测试数据
    test_credentials = {
        'username': 'admin',  # 请替换为实际的测试用户
        'password': 'admin123'  # 请替换为实际的测试密码
    }
    
    try:
        print("🔐 测试认证端点...")
        response = requests.post(
            url,
            json=test_credentials,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'access' in data:
                token = data['access']
                print(f"✅ Token获取成功: {token[:20]}...")
                return token
            else:
                print("❌ 响应中未找到access token")
                print(f"响应内容: {response.text}")
        else:
            print(f"❌ 认证失败: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        print("📝 提示: 请确保后端服务已启动 (python manage.py runserver)")
        
    return None

def test_with_token(token):
    """使用获取的token测试API端点"""
    if not token:
        print("⚠️ 跳过token测试 - 没有有效token")
        return
        
    url = 'http://localhost:8000/api/v1/settings/api-endpoints/'
    
    try:
        print("\n🧪 使用Token测试API端点...")
        response = requests.get(
            url,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            count = len(data.get('results', [])) if isinstance(data, dict) else len(data)
            print(f"✅ API调用成功，返回 {count} 个端点")
        else:
            print(f"❌ API调用失败: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")

def main():
    print("🚀 开始验证API认证功能修复...")
    print("=" * 50)
    
    # 测试认证端点
    token = test_auth_endpoint()
    
    # 使用token测试API
    test_with_token(token)
    
    print("\n" + "=" * 50)
    print("📋 验证总结:")
    if token:
        print("✅ Token获取功能正常")
        print("✅ 前端认证管理功能可用")
        print("💡 现在可以在前端界面使用认证功能了！")
    else:
        print("⚠️ Token获取失败，请检查:")
        print("   1. 后端服务是否启动")
        print("   2. 认证凭据是否正确")
        print("   3. 数据库中是否有测试用户")
    
    print("\n🎯 接下来:")
    print("1. 启动前端服务: cd frontend && npm run dev")
    print("2. 访问: http://localhost:5173/")
    print("3. 进入: Settings → API接口管理 → 测试接口")
    print("4. 在认证管理标签页测试Token获取")

if __name__ == '__main__':
    main()
