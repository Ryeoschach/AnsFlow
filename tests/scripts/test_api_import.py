#!/usr/bin/env python
"""
测试后端API导入功能
"""
import os
import sys
import django
import requests
import json

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

def get_auth_token():
    """获取认证token"""
    # 获取或创建测试用户
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'is_active': True
        }
    )
    if created:
        user.set_password('testpass')
        user.save()
        print("创建测试用户")
    
    # 创建JWT token
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    return access_token

def test_import_api():
    """测试导入API"""
    print("🚀 测试后端API导入功能")
    print("=" * 50)
    
    # 获取认证token
    token = get_auth_token()
    print(f"✅ 获取认证token: {token[:20]}...")
    
    # 测试导入镜像API
    url = 'http://127.0.0.1:8000/api/v1/docker/local/import/images/'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print(f"\n📡 调用API: {url}")
    response = requests.post(url, headers=headers)
    
    print(f"📊 响应状态: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ 导入成功!")
        print(f"  📦 导入数量: {data.get('imported', 0)}")
        print(f"  ⏭️ 跳过数量: {data.get('skipped', 0)}")
        print(f"  ❌ 错误数量: {len(data.get('errors', []))}")
        print(f"  💬 消息: {data.get('message', '')}")
        
        if data.get('errors'):
            print("  错误详情:")
            for error in data.get('errors', []):
                print(f"    - {error}")
    else:
        print(f"❌ API调用失败: {response.text}")

if __name__ == "__main__":
    test_import_api()
