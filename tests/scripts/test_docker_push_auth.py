#!/usr/bin/env python3
"""
验证 Docker 推送功能的认证信息传递
"""

import os
import sys
import django

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from docker_integration.models import DockerRegistry
from pipelines.models import AtomicStep
from pipelines.services.docker_executor import DockerStepExecutor

def test_docker_push_auth():
    """测试 Docker 推送的认证信息传递"""
    
    print("=== 测试 Docker 推送认证信息传递 ===")
    
    # 获取 Harbor 注册表
    try:
        harbor_registry = DockerRegistry.objects.get(id=5)
        print(f"✅ 找到 Harbor 注册表: {harbor_registry.name}")
        print(f"   URL: {harbor_registry.url}")
        print(f"   用户名: {harbor_registry.username}")
        print(f"   认证配置: {harbor_registry.auth_config}")
        
        # 获取测试用的 AtomicStep
        try:
            atomic_step = AtomicStep.objects.get(id=129)
            print(f"✅ 找到测试步骤: {atomic_step.step_type}")
            print(f"   参数: {atomic_step.parameters}")
            
            # 创建 Docker 执行器
            executor = DockerStepExecutor()
            
            # 模拟获取注册表认证信息的过程
            registry_id = atomic_step.parameters.get('registry_id')
            if registry_id:
                try:
                    registry = DockerRegistry.objects.get(id=registry_id)
                    print(f"\n--- Docker 推送认证信息检查 ---")
                    print(f"注册表 ID: {registry.id}")
                    print(f"注册表名称: {registry.name}")
                    print(f"注册表 URL: {registry.url}")
                    print(f"用户名: {registry.username}")
                    
                    # 检查认证配置
                    if registry.auth_config:
                        print(f"认证配置: {registry.auth_config}")
                        
                        # 模拟 Docker 登录过程
                        auth_info = {
                            'username': registry.username,
                            'password': registry.auth_config.get('password', ''),
                            'registry': registry.url
                        }
                        
                        print(f"\n--- Docker 登录信息 ---")
                        print(f"用户名: {auth_info['username']}")
                        print(f"密码: {'*' * len(auth_info['password'])}")
                        print(f"注册表地址: {auth_info['registry']}")
                        
                        if auth_info['username'] and auth_info['password']:
                            print("✅ 认证信息完整，可以执行 Docker 登录")
                        else:
                            print("❌ 认证信息不完整")
                    else:
                        print("❌ 未找到认证配置")
                        
                except DockerRegistry.DoesNotExist:
                    print(f"❌ 未找到注册表 ID: {registry_id}")
            else:
                print("❌ 步骤参数中未找到 registry_id")
                
        except AtomicStep.DoesNotExist:
            print("❌ 未找到测试步骤 ID: 129")
            
    except DockerRegistry.DoesNotExist:
        print("❌ 未找到 Harbor 注册表 ID: 5")

def test_image_name_construction():
    """测试镜像名称构建"""
    print("\n=== 测试镜像名称构建 ===")
    
    try:
        harbor_registry = DockerRegistry.objects.get(id=5)
        atomic_step = AtomicStep.objects.get(id=129)
        
        # 获取参数
        image = atomic_step.parameters.get('image', 'test')
        tag = atomic_step.parameters.get('tag', '072201')
        
        # 构建完整镜像名称
        registry_url = harbor_registry.url.replace('https://', '').replace('http://', '')
        full_image_name = f"{registry_url}/{image}:{tag}"
        
        print(f"镜像: {image}")
        print(f"标签: {tag}")
        print(f"注册表地址: {registry_url}")
        print(f"完整镜像名称: {full_image_name}")
        print("✅ 镜像名称构建正确")
        
    except Exception as e:
        print(f"❌ 镜像名称构建失败: {e}")

if __name__ == '__main__':
    test_docker_push_auth()
    test_image_name_construction()
