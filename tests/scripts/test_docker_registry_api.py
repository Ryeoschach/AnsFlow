#!/usr/bin/env python3
"""
测试Docker注册表API的URL问题修复
"""

import requests
import json

def test_docker_registry_api():
    """测试Docker注册表API"""
    
    base_url = "http://localhost:8000"
    
    # 测试数据
    test_registry = {
        "name": "Test Registry",
        "registry_type": "docker_hub",
        "url": "https://registry.hub.docker.com",
        "description": "测试注册表"
    }
    
    # 测试用的认证token (需要替换为实际token)
    headers = {
        "Content-Type": "application/json",
        # "Authorization": "Bearer YOUR_TOKEN_HERE"  # 如果需要认证
    }
    
    print("🧪 测试Docker注册表API URL修复")
    print("=" * 50)
    
    # 测试1: 不带尾部斜杠的POST请求 (之前失败的情况)
    print("\n1. 测试POST /api/v1/docker/registries (不带尾部斜杠)")
    url_without_slash = f"{base_url}/api/v1/docker/registries"
    
    try:
        response = requests.post(
            url_without_slash,
            headers=headers,
            json=test_registry,
            timeout=10
        )
        
        print(f"   状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")
        
        if response.status_code == 200 or response.status_code == 201:
            print("   ✅ 成功：不带尾部斜杠的POST请求正常工作")
        elif response.status_code == 401:
            print("   ⚠️  认证错误：需要登录token，但URL路由正常")
        elif response.status_code == 500:
            print("   ❌ 失败：仍然存在内部服务器错误")
            print(f"   响应内容: {response.text[:500]}")
        else:
            print(f"   ❓ 其他状态：{response.status_code}")
            print(f"   响应内容: {response.text[:200]}")
            
    except requests.RequestException as e:
        print(f"   ❌ 请求失败: {e}")
    
    # 测试2: 带尾部斜杠的POST请求 (标准情况)
    print("\n2. 测试POST /api/v1/docker/registries/ (带尾部斜杠)")
    url_with_slash = f"{base_url}/api/v1/docker/registries/"
    
    try:
        response = requests.post(
            url_with_slash,
            headers=headers,
            json=test_registry,
            timeout=10
        )
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            print("   ✅ 成功：带尾部斜杠的POST请求正常工作")
        elif response.status_code == 401:
            print("   ⚠️  认证错误：需要登录token，但URL路由正常")
        elif response.status_code == 500:
            print("   ❌ 失败：存在内部服务器错误")
        else:
            print(f"   ❓ 其他状态：{response.status_code}")
            
    except requests.RequestException as e:
        print(f"   ❌ 请求失败: {e}")
    
    # 测试3: GET请求测试
    print("\n3. 测试GET /api/v1/docker/registries (列表)")
    
    try:
        response = requests.get(
            url_without_slash,
            headers=headers,
            timeout=10
        )
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ 成功：GET请求正常工作")
        elif response.status_code == 401:
            print("   ⚠️  认证错误：需要登录token，但URL路由正常")
        else:
            print(f"   ❓ 其他状态：{response.status_code}")
            
    except requests.RequestException as e:
        print(f"   ❌ 请求失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 结论:")
    print("   如果看到认证错误(401)而不是内部服务器错误(500)，")
    print("   说明URL路由问题已经修复！")
    print("   如果仍然看到500错误，说明需要进一步调试。")

if __name__ == '__main__':
    test_docker_registry_api()
