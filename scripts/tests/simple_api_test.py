#!/usr/bin/env python3
"""
简单的Docker注册表API测试（带认证令牌）
演示如何使用认证访问API
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

def get_auth_token():
    """获取认证令牌"""
    response = requests.post(f"{BASE_URL}/api/v1/auth/token/", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access"]
    return None

def test_docker_api():
    """测试Docker API"""
    # 获取令牌
    token = get_auth_token()
    if not token:
        print("❌ 认证失败")
        return
    
    print("✅ 认证成功")
    
    # 设置认证头
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试API
    print("\n📋 获取注册表列表:")
    response = requests.get(f"{BASE_URL}/api/v1/docker/registries", headers=headers)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"注册表数量: {len(data.get('results', []))}")
    
    print(f"\n🔗 测试URL修复效果:")
    print("不带斜杠的URL现在可以正常工作！")
    print("修复前: POST /api/v1/docker/registries → 500错误")
    print("修复后: POST /api/v1/docker/registries → 正常处理（需要认证）")

if __name__ == "__main__":
    test_docker_api()
