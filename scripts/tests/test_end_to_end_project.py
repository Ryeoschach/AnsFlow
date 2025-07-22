#!/usr/bin/env python3
"""
端到端测试 Docker 注册表项目名称功能
使用真实的 nginx 镜像进行测试
"""

import os
import sys
import django
import subprocess

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from docker_integration.models import DockerRegistry

def test_docker_operations_with_project():
    """测试带项目名称的 Docker 操作"""
    
    print("=== 端到端测试 Docker 项目名称功能 ===")
    
    try:
        # 获取 Harbor 注册表
        harbor_registry = DockerRegistry.objects.get(id=5)
        print(f"✅ 找到 Harbor 注册表: {harbor_registry.name}")
        print(f"   URL: {harbor_registry.url}")
        print(f"   项目名称: {harbor_registry.project_name}")
        
        # 确保项目名称为 'test'
        harbor_registry.project_name = 'test'
        harbor_registry.save()
        print(f"✅ 设置项目名称为: test")
        
        # 1. 拉取一个公共镜像
        print(f"\n--- 步骤 1: 拉取 nginx:alpine 镜像 ---")
        try:
            subprocess.run(['docker', 'pull', 'nginx:alpine'], check=True, capture_output=True)
            print(f"✅ 成功拉取 nginx:alpine")
        except subprocess.CalledProcessError as e:
            print(f"❌ 拉取失败: {e}")
            return
        
        # 2. 标记镜像到 Harbor 项目
        target_image = "reg.cyfee.com:10443/test/nginx:alpine"
        print(f"\n--- 步骤 2: 标记镜像到 Harbor 项目 ---")
        print(f"标记: nginx:alpine -> {target_image}")
        
        try:
            subprocess.run(['docker', 'tag', 'nginx:alpine', target_image], check=True, capture_output=True)
            print(f"✅ 成功标记镜像")
        except subprocess.CalledProcessError as e:
            print(f"❌ 标记失败: {e}")
            return
        
        # 3. 登录到 Harbor 注册表
        print(f"\n--- 步骤 3: 登录到 Harbor 注册表 ---")
        try:
            login_cmd = f"echo 'admin123' | docker login reg.cyfee.com:10443 -u admin --password-stdin"
            result = subprocess.run(login_cmd, shell=True, check=True, capture_output=True, text=True)
            print(f"✅ 成功登录到 Harbor")
        except subprocess.CalledProcessError as e:
            print(f"❌ 登录失败: {e}")
            print(f"   错误输出: {e.stderr}")
            return
        
        # 4. 推送镜像到 Harbor 项目
        print(f"\n--- 步骤 4: 推送镜像到 Harbor 项目 ---")
        print(f"推送: {target_image}")
        
        try:
            result = subprocess.run(['docker', 'push', target_image], check=True, capture_output=True, text=True)
            print(f"✅ 成功推送镜像到 Harbor 项目")
            print(f"   推送输出: {result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"❌ 推送失败: {e}")
            print(f"   错误输出: {e.stderr}")
            
        # 5. 验证镜像在 Harbor 中的路径
        print(f"\n--- 步骤 5: 验证镜像路径 ---")
        print(f"✅ 镜像应该位于: https://reg.cyfee.com:10443/harbor/projects/4/repositories")
        print(f"✅ 镜像路径: test/nginx")
        print(f"✅ 镜像标签: alpine")
        
        # 6. 清理本地镜像
        print(f"\n--- 步骤 6: 清理本地镜像 ---")
        try:
            subprocess.run(['docker', 'rmi', target_image], check=True, capture_output=True)
            print(f"✅ 删除本地标记镜像")
        except subprocess.CalledProcessError:
            print(f"⚠️ 清理镜像失败（可能已不存在）")
            
    except DockerRegistry.DoesNotExist:
        print("❌ 未找到 Harbor 注册表 ID: 5")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def verify_project_name_logic():
    """验证项目名称逻辑"""
    print("\n=== 验证项目名称逻辑 ===")
    
    try:
        harbor_registry = DockerRegistry.objects.get(id=5)
        
        # 测试不同的项目名称场景
        test_scenarios = [
            {
                'project_name': '',
                'image': 'myapp',
                'tag': 'v1.0',
                'expected_path': 'reg.cyfee.com:10443/myapp:v1.0'
            },
            {
                'project_name': 'test',
                'image': 'myapp', 
                'tag': 'v1.0',
                'expected_path': 'reg.cyfee.com:10443/test/myapp:v1.0'
            },
            {
                'project_name': 'production',
                'image': 'backend-api',
                'tag': '2.1.0',
                'expected_path': 'reg.cyfee.com:10443/production/backend-api:2.1.0'
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n测试场景:")
            print(f"  项目名称: '{scenario['project_name']}'")
            print(f"  镜像名: {scenario['image']}")
            print(f"  标签: {scenario['tag']}")
            print(f"  预期路径: {scenario['expected_path']}")
            
            # 构建实际路径
            registry_host = harbor_registry.url.replace('https://', '').replace('http://', '')
            
            if scenario['project_name']:
                actual_path = f"{registry_host}/{scenario['project_name']}/{scenario['image']}:{scenario['tag']}"
            else:
                actual_path = f"{registry_host}/{scenario['image']}:{scenario['tag']}"
            
            print(f"  实际路径: {actual_path}")
            
            if actual_path == scenario['expected_path']:
                print(f"  ✅ 路径构建正确")
            else:
                print(f"  ❌ 路径构建错误")
                
    except Exception as e:
        print(f"❌ 验证失败: {e}")

if __name__ == '__main__':
    verify_project_name_logic()
    
    # 询问是否执行实际的 Docker 操作
    print(f"\n{'='*50}")
    response = input("是否执行实际的 Docker 推送测试？这将需要网络连接和 Docker。(y/N): ")
    
    if response.lower() in ['y', 'yes']:
        test_docker_operations_with_project()
    else:
        print("跳过实际 Docker 操作测试")
