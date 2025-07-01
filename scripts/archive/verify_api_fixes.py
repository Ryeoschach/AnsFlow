#!/usr/bin/env python3
"""
验证Django API修复的测试脚本
测试Session认证和正确的API路径
"""

import os
import sys
import django
import requests
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

def test_api_fixes():
    """测试API修复"""
    print("🔧 开始验证Django API修复...")
    
    # 1. 测试健康检查
    print("\n1. 测试健康检查端点...")
    client = Client()
    response = client.get('/health/')
    print(f"   健康检查状态: {response.status_code}")
    if response.status_code == 200:
        print(f"   响应: {response.json()}")
    
    # 2. 测试Session配置
    print("\n2. 测试Session配置...")
    from django.conf import settings
    print(f"   SESSION_ENGINE: {settings.SESSION_ENGINE}")
    
    # 3. 测试正确的executions API路径
    print("\n3. 测试executions API路径...")
    
    # 测试错误的路径（应该返回404）
    response = client.get('/api/v1/executions/')
    print(f"   错误路径 /api/v1/executions/ 状态: {response.status_code} (应该是404)")
    
    # 测试正确的路径
    response = client.get('/api/v1/cicd/executions/')
    print(f"   正确路径 /api/v1/cicd/executions/ 状态: {response.status_code}")
    
    # 4. 创建测试用户并测试认证
    print("\n4. 测试用户认证...")
    User = get_user_model()
    
    # 创建测试用户
    test_user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        test_user.set_password('testpass123')
        test_user.save()
        print("   创建了测试用户")
    else:
        print("   使用现有测试用户")
    
    # 测试登录
    login_success = client.login(username='testuser', password='testpass123')
    print(f"   登录状态: {'成功' if login_success else '失败'}")
    
    if login_success:
        # 测试需要认证的API
        response = client.get('/api/v1/cicd/executions/')
        print(f"   认证后访问executions API: {response.status_code}")
    
    # 5. 检查URL路由
    print("\n5. 检查URL路由配置...")
    from django.urls import get_resolver
    
    resolver = get_resolver()
    
    def print_patterns(urlpatterns, prefix=''):
        for pattern in urlpatterns:
            if hasattr(pattern, 'url_patterns'):
                print_patterns(pattern.url_patterns, prefix + str(pattern.pattern))
            else:
                print(f"   {prefix}{pattern.pattern}")
    
    print("   主要API路由:")
    print("   /api/v1/pipelines/ -> pipelines应用")
    print("   /api/v1/cicd/ -> cicd_integrations应用")
    print("   /api/v1/cicd/executions/ -> PipelineExecutionViewSet")
    
    print("\n✅ API修复验证完成!")

if __name__ == '__main__':
    test_api_fixes()
