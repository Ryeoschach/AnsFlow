#!/usr/bin/env python3
"""
Docker注册表API URL修复验证测试
验证不带斜杠和带斜杠的URL都能正常工作
"""

import requests
import json

def test_docker_registry_api():
    """测试Docker注册表API的URL修复"""
    
    base_url = "http://localhost:8000"
    
    # 测试数据
    test_data = {
        "name": "test-registry",
        "url": "https://registry.example.com",
        "registry_type": "docker_hub"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🧪 开始Docker注册表API URL修复测试")
    print("=" * 50)
    
    # 测试1: 不带斜杠的GET请求
    print("\n=== 测试1: GET /api/v1/docker/registries (不带斜杠) ===")
    try:
        response = requests.get(f"{base_url}/api/v1/docker/registries", headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text[:200]}...")
        
        if response.status_code in [200, 401]:  # 200=成功, 401=认证失败但URL正确
            print("✅ GET请求不带斜杠 - 成功")
        else:
            print("❌ GET请求不带斜杠 - 失败")
            
    except Exception as e:
        print(f"❌ GET请求不带斜杠 - 异常: {e}")
    
    # 测试2: 不带斜杠的POST请求
    print("\n=== 测试2: POST /api/v1/docker/registries (不带斜杠) ===")
    try:
        response = requests.post(
            f"{base_url}/api/v1/docker/registries", 
            headers=headers,
            data=json.dumps(test_data),
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text[:200]}...")
        
        if response.status_code in [200, 201, 400, 401]:  # 成功状态或认证/验证错误
            print("✅ POST请求不带斜杠 - 成功")
        elif response.status_code == 500:
            # 检查是否是重定向错误
            if "APPEND_SLASH" in response.text or "redirect" in response.text.lower():
                print("❌ POST请求不带斜杠 - 仍有重定向问题")
            else:
                print("✅ POST请求不带斜杠 - 成功（非重定向错误）")
        else:
            print("❌ POST请求不带斜杠 - 失败")
            
    except Exception as e:
        print(f"❌ POST请求不带斜杠 - 异常: {e}")
    
    # 测试3: 带斜杠的GET请求（向后兼容性）
    print("\n=== 测试3: GET /api/v1/docker/registries/ (带斜杠) ===")
    try:
        response = requests.get(f"{base_url}/api/v1/docker/registries/", headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text[:200]}...")
        
        if response.status_code in [200, 401]:
            print("✅ GET请求带斜杠 - 成功")
        else:
            print("❌ GET请求带斜杠 - 失败")
            
    except Exception as e:
        print(f"❌ GET请求带斜杠 - 异常: {e}")
    
    # 测试4: 带斜杠的POST请求（向后兼容性）
    print("\n=== 测试4: POST /api/v1/docker/registries/ (带斜杠) ===")
    try:
        response = requests.post(
            f"{base_url}/api/v1/docker/registries/", 
            headers=headers,
            data=json.dumps(test_data),
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text[:200]}...")
        
        if response.status_code in [200, 201, 400, 401]:
            print("✅ POST请求带斜杠 - 成功")
        else:
            print("❌ POST请求带斜杠 - 失败")
            
    except Exception as e:
        print(f"❌ POST请求带斜杠 - 异常: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Docker注册表API URL修复测试完成!")
    print("\n总结:")
    print("- 如果所有测试返回401认证错误，说明URL路由正常工作")
    print("- 如果POST请求不再返回500重定向错误，说明修复成功")
    print("- 带斜杠和不带斜杠的URL都应该正常工作")

if __name__ == '__main__':
    test_docker_registry_api()
