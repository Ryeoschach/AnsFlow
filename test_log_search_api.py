#!/usr/bin/env python3
"""
测试日志搜索API的脚本
"""
import json
import requests
import sys
import os

# 添加Django设置
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

def get_auth_token():
    """获取或创建测试用户的认证token"""
    try:
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            user.set_password('test_password')
            user.save()
            print(f"✅ 创建测试用户: {user.username}")
        
        token, created = Token.objects.get_or_create(user=user)
        print(f"✅ 获取认证token: {token.key}")
        return token.key
        
    except Exception as e:
        print(f"❌ 获取认证token失败: {e}")
        return None

def test_log_search_api():
    """测试日志搜索API"""
    print("🔍 测试日志搜索API...")
    
    # 获取认证token
    token = get_auth_token()
    if not token:
        return False
    
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    # 测试数据
    search_params = {
        'start_time': None,
        'end_time': None,
        'levels': ['INFO', 'ERROR'],
        'services': [],
        'keywords': '',
        'limit': 10,
        'offset': 0
    }
    
    try:
        # 测试搜索API
        print("📤 发送搜索请求...")
        response = requests.post(
            'http://localhost:8000/api/v1/settings/logging/search/',
            headers=headers,
            json=search_params,
            timeout=30
        )
        
        print(f"📥 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 搜索成功!")
            print(f"   找到日志条数: {data.get('total_count', 0)}")
            print(f"   搜索的文件数: {data.get('files_searched', 0)}")
            print(f"   查询时间: {data.get('query_time', 'N/A')}")
            
            # 显示几条日志样本
            logs = data.get('logs', [])
            if logs:
                print(f"\n📝 前3条日志样本:")
                for i, log in enumerate(logs[:3], 1):
                    print(f"   {i}. [{log.get('timestamp', 'N/A')}] [{log.get('level', 'N/A')}] {log.get('message', 'N/A')}")
            else:
                print("   ⚠️  未找到任何日志条目")
            
            return True
        else:
            print(f"❌ 搜索失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 意外错误: {e}")
        return False

def test_log_stats_api():
    """测试日志统计API"""
    print("\n📊 测试日志统计API...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            'http://localhost:8000/api/v1/settings/logging/stats/',
            headers=headers,
            timeout=30
        )
        
        print(f"📥 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 统计获取成功!")
            print(f"   总文件数: {data.get('total_files', 0)}")
            print(f"   总大小: {data.get('total_size_mb', 0):.2f} MB")
            print(f"   服务: {', '.join(data.get('services', []))}")
            print(f"   日志级别: {', '.join(data.get('levels', []))}")
            return True
        else:
            print(f"❌ 统计获取失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 统计API测试失败: {e}")
        return False

def test_log_index_api():
    """测试日志索引API"""
    print("\n📁 测试日志文件索引API...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            'http://localhost:8000/api/v1/settings/logging/index/',
            headers=headers,
            timeout=30
        )
        
        print(f"📥 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 索引获取成功!")
            print(f"   文件数量: {len(data)}")
            
            if data:
                print(f"\n📁 前5个文件:")
                for i, file_info in enumerate(data[:5], 1):
                    print(f"   {i}. {file_info.get('file_path', 'N/A')} ({file_info.get('size_mb', 0):.2f} MB)")
            
            return True
        else:
            print(f"❌ 索引获取失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 索引API测试失败: {e}")
        return False

if __name__ == '__main__':
    print("🚀 开始测试日志管理API...")
    print("=" * 50)
    
    # 运行测试
    search_ok = test_log_search_api()
    stats_ok = test_log_stats_api()
    index_ok = test_log_index_api()
    
    print("\n" + "=" * 50)
    print("📋 测试总结:")
    print(f"   日志搜索API: {'✅ 通过' if search_ok else '❌ 失败'}")
    print(f"   日志统计API: {'✅ 通过' if stats_ok else '❌ 失败'}")
    print(f"   日志索引API: {'✅ 通过' if index_ok else '❌ 失败'}")
    
    if all([search_ok, stats_ok, index_ok]):
        print("\n🎉 所有测试通过! 日志管理API工作正常。")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败，需要检查配置或服务状态。")
        sys.exit(1)
