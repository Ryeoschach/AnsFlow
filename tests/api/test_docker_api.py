#!/usr/bin/env python3
"""
Docker API 调试脚本
"""

import requests
import json
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_auth():
    """测试用户认证"""
    print("=" * 50)
    print("测试用户认证")
    print("=" * 50)
    
    # 尝试登录
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/token/", json=login_data)
        print(f"登录响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access')
            print(f"获取到 token: {token[:50]}..." if token else "未获取到 token")
            return token
        else:
            print("登录失败")
            return None
    except Exception as e:
        print(f"登录请求异常: {e}")
        return None

def test_docker_endpoints(token=None):
    """测试 Docker 相关端点"""
    print("\n" + "=" * 50)
    print("测试 Docker API 端点")
    print("=" * 50)
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    endpoints = [
        "/docker/system/info/",
        "/docker/system/stats/",
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\n测试端点: {endpoint}")
            response = requests.get(f"{API_BASE}{endpoint}", headers=headers)
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            print(f"响应内容: {response.text[:1000]}...")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"JSON 数据键: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                except json.JSONDecodeError:
                    print("响应不是有效的 JSON")
            
        except Exception as e:
            print(f"{endpoint} - 请求异常: {e}")

def test_docker_cleanup(token=None):
    """测试 Docker 清理端点"""
    print("\n" + "=" * 50)
    print("测试 Docker 清理 API")
    print("=" * 50)
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    cleanup_data = {
        "containers": False,
        "images": False,
        "volumes": False,
        "networks": False
    }
    
    try:
        response = requests.post(f"{API_BASE}/docker/system/cleanup/", json=cleanup_data, headers=headers)
        print(f"清理 API 状态码: {response.status_code}")
        print(f"清理 API 响应: {response.text[:500]}...")
        
    except Exception as e:
        print(f"清理 API 请求异常: {e}")

def main():
    """主函数"""
    print(f"开始 Docker API 调试 - {datetime.now()}")
    
    # 1. 测试认证
    token = test_auth()
    
    # 2. 测试 Docker 端点
    test_docker_endpoints(token)
    
    # 3. 测试清理端点
    test_docker_cleanup(token)
    
    print("\n" + "=" * 50)
    print("调试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()
