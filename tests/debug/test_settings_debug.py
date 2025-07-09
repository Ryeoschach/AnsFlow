#!/usr/bin/env python3
"""
Settings API 调试脚本
用于测试审计日志和系统监控等 API 接口
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
        print(f"登录响应内容: {response.text}")
        
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

def test_audit_logs(token=None):
    """测试审计日志 API"""
    print("\n" + "=" * 50)
    print("测试审计日志 API")
    print("=" * 50)
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        # 测试获取审计日志列表
        response = requests.get(f"{API_BASE}/settings/audit-logs/", headers=headers)
        print(f"审计日志 API 状态码: {response.status_code}")
        print(f"审计日志 API 响应: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"审计日志数量: {len(data.get('results', []))}")
        
    except Exception as e:
        print(f"审计日志 API 请求异常: {e}")

def test_system_monitoring(token=None):
    """测试系统监控 API"""
    print("\n" + "=" * 50)
    print("测试系统监控 API")
    print("=" * 50)
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        # 测试获取系统状态
        response = requests.get(f"{API_BASE}/settings/system-monitoring/status/", headers=headers)
        print(f"系统监控 API 状态码: {response.status_code}")
        print(f"系统监控 API 响应: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"系统监控数据: CPU {data.get('cpu_usage')}%, 内存 {data.get('memory_usage')}%, 健康状态 {data.get('system_health')}")
        
    except Exception as e:
        print(f"系统监控 API 请求异常: {e}")

def test_settings_endpoints(token=None):
    """测试其他 Settings 相关端点"""
    print("\n" + "=" * 50)
    print("测试其他 Settings 端点")
    print("=" * 50)
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    endpoints = [
        "/settings/api-keys/",
        "/settings/notification-configs/",
        "/settings/backup-records/",
        "/settings/teams/",
        "/settings/global-configs/"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE}{endpoint}", headers=headers)
            print(f"{endpoint} - 状态码: {response.status_code}")
            if response.status_code != 200:
                print(f"  错误响应: {response.text[:200]}...")
        except Exception as e:
            print(f"{endpoint} - 请求异常: {e}")

def test_database_data():
    """测试数据库中的审计日志数据"""
    print("\n" + "=" * 50)
    print("检查数据库中的审计日志数据")
    print("=" * 50)
    
    try:
        # 这里我们需要直接连接数据库检查
        # 暂时跳过，后面通过 Django shell 检查
        print("需要通过 Django shell 检查数据库数据")
    except Exception as e:
        print(f"数据库检查异常: {e}")

def test_docker_system_apis(token=None):
    """测试 Docker 系统级 API"""
    print("\n" + "=" * 50)
    print("测试 Docker 系统级 API")
    print("=" * 50)
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    # 测试 Docker 系统统计
    try:
        response = requests.get(f"{API_BASE}/docker/system/stats/", headers=headers)
        print(f"Docker 系统统计 API 状态码: {response.status_code}")
        print(f"Docker 系统统计 API 响应: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Docker 统计数据: 镜像 {data.get('total_images')}, 容器 {data.get('total_containers')}, 运行中 {data.get('running_containers')}")
        
    except Exception as e:
        print(f"Docker 系统统计 API 请求异常: {e}")
    
    # 测试 Docker 系统信息
    try:
        response = requests.get(f"{API_BASE}/docker/system/info/", headers=headers)
        print(f"Docker 系统信息 API 状态码: {response.status_code}")
        print(f"Docker 系统信息 API 响应: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Docker 版本: {data.get('docker_version')}, 容器数: {data.get('containers')}")
        
    except Exception as e:
        print(f"Docker 系统信息 API 请求异常: {e}")

def main():
    """主函数"""
    print(f"开始 Settings API 调试 - {datetime.now()}")
    
    # 1. 测试认证
    token = test_auth()
    
    # 2. 测试审计日志 API
    test_audit_logs(token)
    
    # 3. 测试系统监控 API
    test_system_monitoring(token)
    
    # 4. 测试其他端点
    test_settings_endpoints(token)
    
    # 5. 检查数据库数据
    test_database_data()
    
    # 6. 测试 Docker 系统级 API
    test_docker_system_apis(token)
    
    print("\n" + "=" * 50)
    print("调试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()
