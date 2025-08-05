#!/usr/bin/env python3
"""
测试 Docker 注册表认证信息保存和传递
"""

import os
import sys
import django

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from django.contrib.auth.models import User
from docker_integration.models import DockerRegistry
from docker_integration.serializers import DockerRegistrySerializer
from rest_framework.test import APIRequestFactory
from django.test import RequestFactory

def test_registry_password_handling():
    """测试注册表密码处理"""
    
    print("=== 测试 Docker 注册表密码处理 ===")
    
    # 创建测试用户
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    # 创建模拟请求
    factory = APIRequestFactory()
    request = factory.post('/api/registries/')
    request.user = user
    
    # 测试数据
    test_data = {
        'name': 'Test Harbor Registry',
        'url': 'https://reg.cyfee.com:10443',
        'registry_type': 'harbor',
        'username': 'admin',
        'password': 'admin123',
        'description': 'Test Harbor registry with password'
    }
    
    print(f"创建注册表，数据: {test_data}")
    
    # 测试创建
    serializer = DockerRegistrySerializer(data=test_data, context={'request': request})
    if serializer.is_valid():
        registry = serializer.save()
        print(f"✅ 注册表创建成功: {registry.name}")
        print(f"   ID: {registry.id}")
        print(f"   用户名: {registry.username}")
        print(f"   认证配置: {registry.auth_config}")
        
        # 验证密码是否正确保存
        if registry.auth_config and 'password' in registry.auth_config:
            if registry.auth_config['password'] == 'admin123':
                print("✅ 密码正确保存到 auth_config 中")
            else:
                print(f"❌ 密码保存错误: {registry.auth_config['password']}")
        else:
            print("❌ 密码未保存到 auth_config 中")
        
        # 测试更新
        print("\n--- 测试更新注册表 ---")
        update_data = {
            'username': 'admin_updated',
            'password': 'new_password123'
        }
        
        update_serializer = DockerRegistrySerializer(
            registry, 
            data=update_data, 
            partial=True,
            context={'request': request}
        )
        
        if update_serializer.is_valid():
            updated_registry = update_serializer.save()
            print(f"✅ 注册表更新成功")
            print(f"   用户名: {updated_registry.username}")
            print(f"   认证配置: {updated_registry.auth_config}")
            
            # 验证更新后的密码
            if updated_registry.auth_config and 'password' in updated_registry.auth_config:
                if updated_registry.auth_config['password'] == 'new_password123':
                    print("✅ 密码更新正确")
                else:
                    print(f"❌ 密码更新错误: {updated_registry.auth_config['password']}")
            else:
                print("❌ 更新后密码丢失")
        else:
            print(f"❌ 更新失败: {update_serializer.errors}")
        
        # 测试序列化输出（模拟 API 响应）
        print("\n--- 测试 API 响应 ---")
        response_serializer = DockerRegistrySerializer(updated_registry)
        response_data = response_serializer.data
        print(f"API 响应数据: {response_data}")
        
        # 验证密码不会在响应中泄露
        if 'password' not in response_data:
            print("✅ 密码不会在 API 响应中泄露")
        else:
            print("❌ 密码在 API 响应中泄露")
        
        # 清理
        registry.delete()
        print(f"\n✅ 测试完成，注册表已删除")
        
    else:
        print(f"❌ 创建失败: {serializer.errors}")

def test_existing_harbor_registry():
    """测试现有的 Harbor 注册表"""
    print("\n=== 检查现有 Harbor 注册表 ===")
    
    try:
        harbor_registry = DockerRegistry.objects.get(id=5)
        print(f"找到 Harbor 注册表: {harbor_registry.name}")
        print(f"URL: {harbor_registry.url}")
        print(f"用户名: {harbor_registry.username}")
        print(f"认证配置: {harbor_registry.auth_config}")
        
        # 检查认证信息是否完整
        if harbor_registry.auth_config and 'password' in harbor_registry.auth_config:
            print("✅ Harbor 注册表包含密码信息")
        else:
            print("❌ Harbor 注册表缺少密码信息")
            
    except DockerRegistry.DoesNotExist:
        print("❌ 未找到 ID 为 5 的 Harbor 注册表")

if __name__ == '__main__':
    test_registry_password_handling()
    test_existing_harbor_registry()
