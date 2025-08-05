#!/usr/bin/env python3
"""
测试Git凭据API响应，查看新增字段
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_credential_api():
    # 1. 获取认证令牌
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    session = requests.Session()
    response = session.post(f"{API_BASE}/auth/token/", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access') or data.get('token')
        session.headers.update({'Authorization': f'Bearer {token}'})
        print("✅ 成功获取认证令牌")
    else:
        print("❌ 获取认证令牌失败")
        return
    
    # 2. 获取凭据列表
    print("\n📋 获取凭据列表...")
    response = session.get(f"{API_BASE}/cicd/git-credentials/")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ 成功获取凭据列表")
        print("\n📄 完整API响应:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # 检查新增字段
        if isinstance(data, dict) and 'results' in data:
            credentials = data['results']
        elif isinstance(data, list):
            credentials = data
        else:
            credentials = []
        
        print(f"\n🔍 分析凭据字段:")
        for cred in credentials:
            print(f"\n凭据: {cred.get('name', 'Unknown')}")
            
            # 检查新增的字段
            has_password = cred.get('has_password')
            has_ssh_key = cred.get('has_ssh_key')
            
            print(f"  - has_password: {has_password}")
            print(f"  - has_ssh_key: {has_ssh_key}")
            
            if has_password is None:
                print("  ⚠️ has_password 字段不存在")
            if has_ssh_key is None:
                print("  ⚠️ has_ssh_key 字段不存在")
    else:
        print(f"❌ 获取凭据列表失败: {response.status_code}")
        print(response.text)

if __name__ == '__main__':
    test_credential_api()
