#!/usr/bin/env python3
"""
测试系统监控API的所有端点
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def get_token():
    """获取认证token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{API_BASE}/auth/token/", json=login_data)
    if response.status_code == 200:
        data = response.json()
        return data.get('access')
    return None

def test_system_monitoring_endpoints():
    """测试所有系统监控端点"""
    token = get_token()
    if not token:
        print("无法获取认证token")
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # 测试的端点列表
    test_endpoints = [
        "/settings/system-monitoring/",           # 基础列表端点 (前端调用)
        "/settings/system-monitoring/status/",   # 系统状态 (已工作)
        "/settings/system-monitoring/metrics/",  # 系统指标
        "/settings/system-monitoring/health/",   # 健康检查 (前端调用)
        "/settings/system-monitoring/info/",     # 系统信息
    ]
    
    print("=" * 60)
    print("测试系统监控API端点")
    print("=" * 60)
    
    for endpoint in test_endpoints:
        try:
            url = f"{API_BASE}{endpoint}"
            response = requests.get(url, headers=headers)
            
            print(f"\n端点: {endpoint}")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应: ✅ 成功")
                if isinstance(data, dict):
                    print(f"数据字段: {list(data.keys())}")
                elif isinstance(data, list):
                    print(f"返回列表长度: {len(data)}")
            else:
                print(f"响应: ❌ 错误")
                print(f"错误信息: {response.text[:200]}...")
                
        except Exception as e:
            print(f"端点: {endpoint}")
            print(f"异常: {e}")

if __name__ == "__main__":
    test_system_monitoring_endpoints()
