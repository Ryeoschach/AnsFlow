#!/usr/bin/env python3
"""
测试Git凭据API字段
检查新增的has_password和has_ssh_key字段是否正确返回
"""

import requests
import json

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def get_auth_token():
    """获取认证令牌"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{API_BASE}/auth/token/", json=login_data)
    if response.status_code == 200:
        data = response.json()
        return data.get('access') or data.get('token')
    return None

def test_credentials_api():
    """测试凭据API字段"""
    token = get_auth_token()
    if not token:
        print("❌ 认证失败")
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # 测试列表API
    print("🔍 测试凭据列表API...")
    response = requests.get(f"{API_BASE}/cicd/git-credentials/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        if isinstance(data, dict) and 'results' in data:
            credentials = data['results']
        else:
            credentials = data
        
        print(f"✅ 获取到 {len(credentials)} 个凭据")
        
        if credentials:
            print("\n📋 第一个凭据的字段:")
            first_cred = credentials[0]
            for key, value in first_cred.items():
                print(f"   {key}: {value}")
            
            # 检查关键字段
            print("\n🔍 检查关键字段:")
            print(f"   has_credentials: {first_cred.get('has_credentials', 'MISSING')}")
            print(f"   has_password: {first_cred.get('has_password', 'MISSING')}")
            print(f"   has_ssh_key: {first_cred.get('has_ssh_key', 'MISSING')}")
            
            # 测试详情API
            cred_id = first_cred['id']
            print(f"\n🔍 测试凭据详情API (ID: {cred_id})...")
            detail_response = requests.get(f"{API_BASE}/cicd/git-credentials/{cred_id}/", headers=headers)
            
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                print("✅ 详情API响应:")
                print(f"   has_credentials: {detail_data.get('has_credentials', 'MISSING')}")
                print(f"   has_password: {detail_data.get('has_password', 'MISSING')}")
                print(f"   has_ssh_key: {detail_data.get('has_ssh_key', 'MISSING')}")
            else:
                print(f"❌ 详情API失败: {detail_response.status_code}")
                
    else:
        print(f"❌ 列表API失败: {response.status_code}")
        print(f"响应: {response.text}")

if __name__ == '__main__':
    test_credentials_api()
