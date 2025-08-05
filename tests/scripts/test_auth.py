#!/usr/bin/env python
"""
AnsFlow Django API 认证测试脚本
测试JWT认证和API访问
"""

import requests
import json
import os
import sys

# 添加Django项目路径
django_path = "/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service"
if django_path not in sys.path:
    sys.path.append(django_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from django.contrib.auth.models import User

# API基础URL
BASE_URL = "http://localhost:8000"

def get_or_create_test_user():
    """获取或创建测试用户"""
    try:
        user = User.objects.get(username='testuser')
        print(f"✅ 测试用户已存在: {user.username}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        print(f"✅ 创建测试用户: {user.username}")
    return user

def test_jwt_authentication():
    """测试JWT认证"""
    print("🔍 测试JWT认证...")
    
    # 确保测试用户存在
    user = get_or_create_test_user()
    
    # 尝试获取JWT令牌
    auth_data = {
        'username': 'testuser',
        'password': 'testpass123'
    }
    
    # 首先检查是否有JWT端点
    token_url = f"{BASE_URL}/api/v1/auth/token/"
    response = requests.post(token_url, data=auth_data)
    
    if response.status_code == 404:
        print("⚠️  JWT令牌端点未配置，需要添加JWT URL")
        return None
    elif response.status_code == 200:
        token_data = response.json()
        print(f"✅ 获取JWT令牌成功")
        return token_data.get('access')
    else:
        print(f"❌ JWT认证失败: {response.status_code} - {response.text}")
        return None

def test_session_authentication():
    """测试Session认证"""
    print("🔍 测试Session认证...")
    
    session = requests.Session()
    
    # 获取CSRF令牌
    csrf_url = f"{BASE_URL}/admin/"
    response = session.get(csrf_url)
    
    if 'csrftoken' in session.cookies:
        csrf_token = session.cookies['csrftoken']
        print(f"✅ 获取CSRF令牌成功")
        
        # 尝试登录
        login_data = {
            'username': 'admin',
            'password': 'admin',
            'csrfmiddlewaretoken': csrf_token
        }
        
        login_url = f"{BASE_URL}/admin/login/"
        response = session.post(login_url, data=login_data)
        
        if response.status_code == 200 and 'sessionid' in session.cookies:
            print("✅ Session认证成功")
            return session
        else:
            print("❌ Session认证失败")
            return None
    else:
        print("❌ 无法获取CSRF令牌")
        return None

def test_api_with_authentication(session=None, jwt_token=None):
    """使用认证测试API"""
    print("🔍 测试认证后的API访问...")
    
    headers = {}
    if jwt_token:
        headers['Authorization'] = f'Bearer {jwt_token}'
        print("使用JWT认证")
    elif session:
        print("使用Session认证")
    
    # 测试项目API
    projects_url = f"{BASE_URL}/api/v1/projects/projects/"
    if session:
        response = session.get(projects_url)
    else:
        response = requests.get(projects_url, headers=headers)
    
    print(f"项目API状态码: {response.status_code}")
    if response.status_code == 200:
        projects = response.json()
        print(f"✅ 获取到 {len(projects.get('results', projects))} 个项目")
    else:
        print(f"❌ 项目API失败: {response.text[:200]}")
    
    # 测试管道API
    pipelines_url = f"{BASE_URL}/api/v1/pipelines/pipelines/"
    if session:
        response = session.get(pipelines_url)
    else:
        response = requests.get(pipelines_url, headers=headers)
    
    print(f"管道API状态码: {response.status_code}")
    if response.status_code == 200:
        pipelines = response.json()
        print(f"✅ 获取到 {len(pipelines.get('results', pipelines))} 个管道")
    else:
        print(f"❌ 管道API失败: {response.text[:200]}")

def main():
    """运行认证测试"""
    print("🔐 开始AnsFlow Django API认证测试")
    print("=" * 60)
    
    # 测试JWT认证
    jwt_token = test_jwt_authentication()
    print()
    
    # 测试Session认证
    session = test_session_authentication()
    print()
    
    # 测试认证后的API访问
    if jwt_token or session:
        test_api_with_authentication(session=session, jwt_token=jwt_token)
    else:
        print("⚠️  无法进行认证，跳过认证API测试")
    
    print()
    print("✅ 认证测试完成!")

if __name__ == "__main__":
    main()
