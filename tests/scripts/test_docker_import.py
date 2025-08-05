#!/usr/bin/env python
"""
Docker 本地资源导入功能测试脚本
"""
import os
import sys
import json
import requests
from datetime import datetime

# API配置
API_BASE_URL = 'http://localhost:8000/api/v1'
DOCKER_API_BASE = f'{API_BASE_URL}/docker'

def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def test_local_docker_apis():
    """测试本地Docker API"""
    print_header("测试本地Docker资源API")
    
    # 测试获取本地镜像
    print("\n📋 测试获取本地镜像")
    try:
        response = requests.get(f'{DOCKER_API_BASE}/local/images/')
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 成功获取本地镜像: {data.get('total', 0)} 个")
            if data.get('images'):
                for img in data['images'][:3]:  # 显示前3个
                    print(f"    📦 {img['name']}:{img['tag']} ({img['size']} bytes)")
        else:
            print(f"  ❌ 获取本地镜像失败: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
    
    # 测试获取本地容器
    print("\n📋 测试获取本地容器")
    try:
        response = requests.get(f'{DOCKER_API_BASE}/local/containers/')
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 成功获取本地容器: {data.get('total', 0)} 个")
            if data.get('containers'):
                for container in data['containers'][:3]:  # 显示前3个
                    print(f"    🚢 {container['name']} ({container['status']}) - {container['image']}")
        else:
            print(f"  ❌ 获取本地容器失败: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")

def test_import_functions():
    """测试导入功能"""
    print_header("测试Docker资源导入功能")
    
    # 测试导入镜像
    print("\n📋 测试导入本地镜像")
    try:
        response = requests.post(f'{DOCKER_API_BASE}/local/import/images/')
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"  ✅ 导入成功: {data.get('imported', 0)} 个镜像")
                print(f"    📊 跳过: {data.get('skipped', 0)} 个已存在的镜像")
                if data.get('errors'):
                    print(f"    ⚠️ 错误: {len(data['errors'])} 个")
            else:
                print(f"  ❌ 导入失败: {data.get('error', '未知错误')}")
        else:
            print(f"  ❌ 导入请求失败: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
    
    # 测试导入容器
    print("\n📋 测试导入本地容器")
    try:
        response = requests.post(f'{DOCKER_API_BASE}/local/import/containers/')
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"  ✅ 导入成功: {data.get('imported', 0)} 个容器")
                print(f"    📊 跳过: {data.get('skipped', 0)} 个已存在的容器")
                if data.get('errors'):
                    print(f"    ⚠️ 错误: {len(data['errors'])} 个")
            else:
                print(f"  ❌ 导入失败: {data.get('error', '未知错误')}")
        else:
            print(f"  ❌ 导入请求失败: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")

def test_sync_function():
    """测试同步功能"""
    print_header("测试Docker资源同步功能")
    
    print("\n📋 测试同步本地资源状态")
    try:
        response = requests.post(f'{DOCKER_API_BASE}/local/sync/')
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"  ✅ 同步成功")
                print(f"    📊 更新容器: {data.get('updated_containers', 0)} 个")
                print(f"    📊 更新镜像: {data.get('updated_images', 0)} 个")
                if data.get('container_errors'):
                    print(f"    ⚠️ 容器错误: {len(data['container_errors'])} 个")
                if data.get('image_errors'):
                    print(f"    ⚠️ 镜像错误: {len(data['image_errors'])} 个")
            else:
                print(f"  ❌ 同步失败: {data.get('error', '未知错误')}")
        else:
            print(f"  ❌ 同步请求失败: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")

def check_managed_resources():
    """检查管理的资源"""
    print_header("检查管理的Docker资源")
    
    # 检查托管镜像
    print("\n📋 检查托管镜像")
    try:
        response = requests.get(f'{DOCKER_API_BASE}/images/')
        if response.status_code == 200:
            data = response.json()
            images = data.get('results', [])
            print(f"  ✅ 托管镜像数量: {len(images)}")
            for img in images[:5]:  # 显示前5个
                print(f"    📦 {img['name']} (状态: {img.get('build_status', 'unknown')})")
        else:
            print(f"  ❌ 获取托管镜像失败: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
    
    # 检查托管容器
    print("\n📋 检查托管容器")
    try:
        response = requests.get(f'{DOCKER_API_BASE}/containers/')
        if response.status_code == 200:
            data = response.json()
            containers = data.get('results', [])
            print(f"  ✅ 托管容器数量: {len(containers)}")
            for container in containers[:5]:  # 显示前5个
                print(f"    🚢 {container['name']} (状态: {container.get('status', 'unknown')})")
        else:
            print(f"  ❌ 获取托管容器失败: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")

def main():
    """主函数"""
    print_header("Docker本地资源导入功能测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API地址: {API_BASE_URL}")
    
    # 检查服务是否可用
    try:
        response = requests.get(f'{API_BASE_URL}/docker/system/info/')
        if response.status_code == 200:
            print("✅ Docker API 服务可用")
        else:
            print("❌ Docker API 服务不可用")
            return
    except Exception as e:
        print(f"❌ 无法连接到API服务: {e}")
        return
    
    # 运行测试
    test_local_docker_apis()
    test_import_functions()
    test_sync_function()
    check_managed_resources()
    
    print_header("测试完成")
    print("✅ 所有功能测试完成，请查看上面的结果")
    print("💡 建议在浏览器中访问 http://127.0.0.1:5173/docker 查看UI效果")

if __name__ == "__main__":
    main()
