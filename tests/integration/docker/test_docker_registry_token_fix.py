#!/usr/bin/env python3
"""
测试Docker Registry API Token修复
验证前端代码中的Token键名一致性问题已经修复
"""

import requests
import json
import sys
import os

# 添加Django项目路径
sys.path.insert(0, '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def test_token_consistency():
    """测试Token键名一致性修复"""
    print("🔍 测试Docker Registry API Token修复")
    print("=" * 60)
    
    # 1. 获取或创建测试用户的JWT token
    try:
        user = User.objects.get(username='admin')
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        print(f"✅ 获取JWT Token成功: {access_token[:20]}...")
    except User.DoesNotExist:
        print("❌ 未找到admin用户，请先创建")
        return False
    
    # 2. 测试API调用
    base_url = 'http://127.0.0.1:8000/api/v1'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    print(f"\n🧪 测试API调用")
    print(f"🔗 请求URL: {base_url}/docker/registries/")
    print(f"🗝️  Authorization Header: Bearer {access_token[:20]}...")
    
    try:
        # 测试 Docker Registry API
        response = requests.get(f'{base_url}/docker/registries/', headers=headers, timeout=10)
        print(f"📡 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Docker Registry API调用成功！Token键名修复生效")
            data = response.json()
            print(f"📊 响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        elif response.status_code == 401:
            print("❌ 仍然返回401错误，Token可能未正确传递")
            print(f"📝 响应内容: {response.text}")
            return False
        else:
            print(f"⚠️  非预期状态码: {response.status_code}")
            print(f"📝 响应内容: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ API请求失败: {e}")
        return False

def verify_frontend_code():
    """验证前端代码中的Token键名统一性"""
    print(f"\n🔍 验证前端代码Token键名统一性")
    print("=" * 40)
    
    # 检查dockerRegistryService.ts文件
    docker_service_file = '/Users/creed/Workspace/OpenSource/ansflow/frontend/src/services/dockerRegistryService.ts'
    api_service_file = '/Users/creed/Workspace/OpenSource/ansflow/frontend/src/services/api.ts'
    
    try:
        # 检查dockerRegistryService.ts
        with open(docker_service_file, 'r', encoding='utf-8') as f:
            docker_content = f.read()
        
        # 检查api.ts
        with open(api_service_file, 'r', encoding='utf-8') as f:
            api_content = f.read()
        
        # 统计token键名使用情况
        docker_authtoken_count = docker_content.count("localStorage.getItem('authToken')")
        docker_token_count = docker_content.count("localStorage.getItem('token')")
        
        api_authtoken_count = api_content.count("localStorage.getItem('authToken')")
        api_token_count = api_content.count("localStorage.getItem('token')")
        
        print(f"📁 dockerRegistryService.ts:")
        print(f"   - authToken使用次数: {docker_authtoken_count}")
        print(f"   - token使用次数: {docker_token_count}")
        
        print(f"📁 api.ts:")
        print(f"   - authToken使用次数: {api_authtoken_count}")
        print(f"   - token使用次数: {api_token_count}")
        
        # 检查是否已修复
        if docker_authtoken_count > 0 and docker_token_count == 0:
            print("✅ dockerRegistryService.ts已修复，统一使用authToken")
            return True
        elif docker_token_count > 0:
            print("❌ dockerRegistryService.ts仍在使用错误的token键名")
            return False
        else:
            print("⚠️  未检测到token使用")
            return False
            
    except FileNotFoundError as e:
        print(f"❌ 文件未找到: {e}")
        return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🛠️  Docker Registry API Token修复验证")
    print("=" * 60)
    
    # 验证前端代码修复
    frontend_fixed = verify_frontend_code()
    
    # 测试API调用
    api_works = test_token_consistency()
    
    print(f"\n📋 测试结果总结")
    print("=" * 30)
    print(f"前端代码修复: {'✅ 通过' if frontend_fixed else '❌ 失败'}")
    print(f"API调用测试: {'✅ 通过' if api_works else '❌ 失败'}")
    
    if frontend_fixed and api_works:
        print("🎉 所有测试通过！Token键名不一致问题已修复")
        return True
    else:
        print("⚠️  仍有问题需要解决")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
