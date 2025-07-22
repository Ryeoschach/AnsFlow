#!/usr/bin/env python3
"""
Docker 注册表验证 API 修复验证脚本
验证 /api/v1/docker/registries/4/test_connection/ 端点是否正常工作
"""
import requests
import json
import sys
import os

# 添加Django路径
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


def print_header(title):
    """打印标题"""
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")


def print_success(message):
    """打印成功信息"""
    print(f"✅ {message}")


def print_error(message):
    """打印错误信息"""
    print(f"❌ {message}")


def print_info(message):
    """打印信息"""
    print(f"📋 {message}")


def get_auth_token():
    """获取认证Token"""
    try:
        user = User.objects.first()
        if not user:
            user = User.objects.create_user('testuser', 'test@example.com', 'password123')
            print_info(f"创建测试用户: {user.username}")
        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        print_success(f"获取认证Token成功: {access_token[:20]}...")
        return access_token
    except Exception as e:
        print_error(f"获取认证Token失败: {e}")
        return None


def test_wrong_api_path():
    """测试错误的API路径"""
    print_header("测试错误的API路径")
    
    # 测试错误路径
    wrong_url = "http://127.0.0.1:8000/api/v1/docker/registries/4/test/"
    try:
        response = requests.post(wrong_url, headers={'Content-Type': 'application/json'})
        if response.status_code == 404:
            print_success(f"错误路径正确返回404: {wrong_url}")
        else:
            print_error(f"错误路径返回意外状态码 {response.status_code}: {wrong_url}")
    except Exception as e:
        print_error(f"测试错误路径时发生异常: {e}")


def test_correct_api_path():
    """测试正确的API路径"""
    print_header("测试正确的API路径")
    
    # 获取认证Token
    token = get_auth_token()
    if not token:
        return False
    
    # 测试正确路径
    correct_url = "http://127.0.0.1:8000/api/v1/docker/registries/4/test_connection/"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        print_info(f"调用API: {correct_url}")
        response = requests.post(correct_url, headers=headers)
        
        print_info(f"响应状态码: {response.status_code}")
        print_info(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print_success("Docker注册表连接测试API工作正常")
                return True
            else:
                print_error(f"API返回错误状态: {data}")
                return False
        else:
            print_error(f"API返回错误状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试正确路径时发生异常: {e}")
        return False


def check_registry_status():
    """检查注册表状态"""
    print_header("检查注册表状态")
    
    try:
        from docker_integration.models import DockerRegistry
        
        registry = DockerRegistry.objects.get(id=4)
        print_success(f"找到注册表: {registry.name}")
        print_info(f"   URL: {registry.url}")
        print_info(f"   类型: {registry.registry_type}")
        print_info(f"   状态: {registry.status}")
        print_info(f"   是否默认: {registry.is_default}")
        print_info(f"   最后检查: {registry.last_check}")
        print_info(f"   检查消息: {registry.check_message}")
        
        if registry.auth_config:
            print_info(f"   认证配置: {registry.auth_config}")
        else:
            print_error("   认证配置为空")
            
        return True
        
    except Exception as e:
        print_error(f"检查注册表状态失败: {e}")
        return False


def main():
    """主函数"""
    print_header("Docker 注册表验证 API 修复验证")
    
    # 1. 检查注册表状态
    registry_ok = check_registry_status()
    
    # 2. 测试错误的API路径
    test_wrong_api_path()
    
    # 3. 测试正确的API路径
    api_ok = test_correct_api_path()
    
    # 4. 总结
    print_header("修复验证总结")
    
    if registry_ok:
        print_success("注册表状态检查通过")
    else:
        print_error("注册表状态检查失败")
    
    if api_ok:
        print_success("API路径修复验证通过")
        print_info("前端应该使用: /api/v1/docker/registries/{id}/test_connection/")
    else:
        print_error("API路径修复验证失败")
    
    if registry_ok and api_ok:
        print_success("🎉 所有验证通过！Docker注册表验证API已正常工作")
        return True
    else:
        print_error("❗ 存在问题需要进一步修复")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
