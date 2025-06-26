#!/usr/bin/env python
"""
AnsFlow API 修复验证脚本
测试Session认证和API路径修复是否成功
"""

import requests
import json
import sys
import os

# Django设置
django_path = "/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service"
if django_path not in sys.path:
    sys.path.append(django_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

# API基础URL
BASE_URL = "http://localhost:8000"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print(f"{'='*60}")

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def test_session_authentication():
    """测试Session认证修复"""
    print_header("Session认证测试")
    
    session = requests.Session()
    
    # 1. 获取Django admin页面（获取CSRF token）
    try:
        response = session.get(f"{BASE_URL}/admin/")
        if response.status_code == 200:
            print_success("成功访问Django admin页面")
            
            # 检查CSRF token
            if 'csrftoken' in session.cookies:
                csrf_token = session.cookies['csrftoken']
                print_success(f"获取CSRF token: {csrf_token[:10]}...")
                
                # 2. 尝试登录
                login_data = {
                    'username': 'admin',
                    'password': 'admin123',
                    'csrfmiddlewaretoken': csrf_token,
                    'next': '/admin/'
                }
                
                login_response = session.post(f"{BASE_URL}/admin/login/", data=login_data)
                
                if login_response.status_code == 200:
                    if 'sessionid' in session.cookies:
                        print_success("Session认证成功 - 获得sessionid")
                        return session
                    else:
                        print_error("登录失败 - 未获得sessionid")
                else:
                    print_error(f"登录请求失败: {login_response.status_code}")
            else:
                print_error("未能获取CSRF token")
        else:
            print_error(f"无法访问admin页面: {response.status_code}")
    except Exception as e:
        print_error(f"Session认证测试异常: {e}")
    
    return None

def test_jwt_authentication():
    """测试JWT认证"""
    print_header("JWT认证测试")
    
    auth_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/token/", json=auth_data)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access')
            
            if access_token:
                print_success("JWT认证成功")
                print_info(f"Token: {access_token[:20]}...")
                return access_token
            else:
                print_error("JWT响应中没有access token")
        else:
            print_error(f"JWT认证失败: {response.status_code} - {response.text}")
    except Exception as e:
        print_error(f"JWT认证异常: {e}")
    
    return None

def test_api_paths(jwt_token=None):
    """测试API路径修复"""
    print_header("API路径测试")
    
    headers = {}
    if jwt_token:
        headers['Authorization'] = f'Bearer {jwt_token}'
    
    # 测试路径列表
    test_paths = [
        "/api/v1/cicd/executions/",  # 原始正确路径
        "/api/v1/executions/",       # 兼容性路径
    ]
    
    for path in test_paths:
        try:
            response = requests.get(f"{BASE_URL}{path}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"路径 {path} 正常 - 返回 {len(data.get('results', []))} 条记录")
            elif response.status_code == 401:
                print_info(f"路径 {path} 需要认证 (401) - 路径可访问")
            elif response.status_code == 404:
                print_error(f"路径 {path} 404错误 - 路径不存在")
            else:
                print_info(f"路径 {path} 状态码: {response.status_code}")
                
        except Exception as e:
            print_error(f"测试路径 {path} 异常: {e}")

def test_specific_execution(execution_id=7, jwt_token=None):
    """测试特定执行记录访问"""
    print_header(f"执行记录 {execution_id} 访问测试")
    
    headers = {}
    if jwt_token:
        headers['Authorization'] = f'Bearer {jwt_token}'
    
    # 测试具体执行记录的两种路径
    test_paths = [
        f"/api/v1/cicd/executions/{execution_id}/",  # 原始路径
        f"/api/v1/executions/{execution_id}/",       # 兼容路径
    ]
    
    for path in test_paths:
        try:
            response = requests.get(f"{BASE_URL}{path}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"路径 {path} 正常 - 执行ID: {data.get('id')}")
            elif response.status_code == 404:
                print_error(f"路径 {path} 404错误 - 记录不存在或路径错误")
            elif response.status_code == 401:
                print_info(f"路径 {path} 需要认证 - 路径可访问")
            else:
                print_info(f"路径 {path} 状态码: {response.status_code}")
                
        except Exception as e:
            print_error(f"测试路径 {path} 异常: {e}")

def test_health_check():
    """测试健康检查"""
    print_header("健康检查测试")
    
    try:
        response = requests.get(f"{BASE_URL}/health/")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"服务健康: {data.get('status')}")
            print_info(f"服务版本: {data.get('version')}")
        else:
            print_error(f"健康检查失败: {response.status_code}")
            
    except Exception as e:
        print_error(f"健康检查异常: {e}")

def main():
    """运行所有测试"""
    print_header("AnsFlow API 修复验证")
    
    # 1. 健康检查
    test_health_check()
    
    # 2. Session认证测试
    session = test_session_authentication()
    
    # 3. JWT认证测试
    jwt_token = test_jwt_authentication()
    
    # 4. API路径测试
    test_api_paths(jwt_token)
    
    # 5. 特定执行记录测试
    test_specific_execution(7, jwt_token)
    
    print_header("测试完成")
    
    if jwt_token or session:
        print_success("认证修复验证成功")
    else:
        print_error("认证仍有问题，需要进一步调试")

if __name__ == "__main__":
    main()
