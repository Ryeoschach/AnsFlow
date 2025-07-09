#!/usr/bin/env python3
"""
Docker 系统 API 验证脚本
专门测试 Docker 系统级 API 端点
"""

import requests
import json
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def get_auth_token():
    """获取认证令牌"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/token/", json=login_data)
        if response.status_code == 200:
            data = response.json()
            return data.get('access')
        else:
            print(f"登录失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"登录异常: {e}")
        return None

def test_docker_system_stats(token):
    """测试 Docker 系统统计 API"""
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(f"{API_BASE}/docker/system/stats/", headers=headers)
        print(f"[Docker Stats] 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 总镜像数: {data.get('total_images')}")
            print(f"  ✅ 总容器数: {data.get('total_containers')}")  
            print(f"  ✅ 运行容器数: {data.get('running_containers')}")
            print(f"  ✅ 仓库数: {data.get('total_registries')}")
            print(f"  ✅ Compose项目数: {data.get('total_compose_projects')}")
            
            disk_usage = data.get('disk_usage', {})
            print(f"  ✅ 磁盘使用: 镜像 {disk_usage.get('images', 0)//1024//1024}MB, 容器 {disk_usage.get('containers', 0)//1024//1024}MB")
        else:
            print(f"  ❌ 错误: {response.text}")
            
    except Exception as e:
        print(f"  ❌ 请求异常: {e}")

def test_docker_system_info(token):
    """测试 Docker 系统信息 API"""
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(f"{API_BASE}/docker/system/info/", headers=headers)
        print(f"[Docker Info] 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Docker版本: {data.get('docker_version')}")
            print(f"  ✅ API版本: {data.get('api_version')}")
            print(f"  ✅ 操作系统: {data.get('operating_system')}")
            print(f"  ✅ 架构: {data.get('architecture')}")
            print(f"  ✅ 总内存: {data.get('total_memory', 0)//1024//1024//1024}GB")
            print(f"  ✅ 容器数: {data.get('containers')}")
            print(f"  ✅ 运行中: {data.get('running_containers')}")
            print(f"  ✅ 镜像数: {data.get('images')}")
        else:
            print(f"  ❌ 错误: {response.text}")
            
    except Exception as e:
        print(f"  ❌ 请求异常: {e}")

def test_docker_system_cleanup(token):
    """测试 Docker 系统清理 API"""
    headers = {'Authorization': f'Bearer {token}'}
    
    # 测试参数：只清理悬空镜像
    cleanup_options = {
        "containers": False,
        "images": True,
        "volumes": False,
        "networks": False
    }
    
    try:
        response = requests.post(f"{API_BASE}/docker/system/cleanup/", 
                               json=cleanup_options, headers=headers)
        print(f"[Docker Cleanup] 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 清理成功: {data.get('success')}")
            print(f"  ✅ 清理项目数: {len(data.get('cleaned_up', []))}")
            print(f"  ✅ 错误数: {len(data.get('errors', []))}")
            
            if data.get('cleaned_up'):
                print(f"  📋 清理详情: {data.get('cleaned_up')[:3]}...")
        else:
            print(f"  ❌ 错误: {response.text}")
            
    except Exception as e:
        print(f"  ❌ 请求异常: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🐳 Docker 系统 API 验证测试")
    print("=" * 60)
    print(f"开始时间: {datetime.now()}")
    print()
    
    # 获取认证令牌
    print("🔐 获取认证令牌...")
    token = get_auth_token()
    
    if not token:
        print("❌ 无法获取认证令牌，退出测试")
        return
    
    print("✅ 认证成功")
    print()
    
    # 测试各个端点
    print("📊 测试 Docker 系统统计...")
    test_docker_system_stats(token)
    print()
    
    print("ℹ️  测试 Docker 系统信息...")
    test_docker_system_info(token)
    print()
    
    print("🧹 测试 Docker 系统清理...")
    test_docker_system_cleanup(token)
    print()
    
    print("=" * 60)
    print("✅ 所有 Docker 系统 API 测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
