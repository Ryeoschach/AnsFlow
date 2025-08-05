#!/usr/bin/env python
"""
API路径修复验证脚本
测试兼容性路由是否正常工作
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

def test_api_paths():
    """测试API路径"""
    print("🔧 测试API路径兼容性")
    print("=" * 50)
    
    # 获取JWT token用于认证
    auth_data = {'username': 'admin', 'password': 'admin123'}
    
    try:
        token_response = requests.post(f"{BASE_URL}/api/v1/auth/token/", json=auth_data)
        
        if token_response.status_code == 200:
            token = token_response.json().get('access')
            headers = {'Authorization': f'Bearer {token}'}
            print("✅ 获取JWT token成功")
        else:
            headers = {}
            print("⚠️  JWT认证失败，使用无认证测试")
    except:
        headers = {}
        print("⚠️  无法连接认证服务，使用无认证测试")
    
    # 测试路径列表
    test_cases = [
        {
            'name': '原始CICD路径 - 列表',
            'path': '/api/v1/cicd/executions/',
            'method': 'GET'
        },
        {
            'name': '兼容性路径 - 列表', 
            'path': '/api/v1/executions/',
            'method': 'GET'
        },
        {
            'name': '原始CICD路径 - 详情',
            'path': '/api/v1/cicd/executions/7/',
            'method': 'GET'
        },
        {
            'name': '兼容性路径 - 详情',
            'path': '/api/v1/executions/7/',
            'method': 'GET'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🔍 测试: {test_case['name']}")
        print(f"   路径: {test_case['path']}")
        
        try:
            url = f"{BASE_URL}{test_case['path']}"
            response = requests.get(url, headers=headers, timeout=5)
            
            status_code = response.status_code
            
            if status_code == 200:
                print(f"   ✅ 成功 (200) - API正常工作")
                results.append(True)
            elif status_code == 401:
                print(f"   🔐 需要认证 (401) - 路径存在但需要权限")
                results.append(True)  # 路径存在
            elif status_code == 404:
                print(f"   ❌ 路径不存在 (404)")
                results.append(False)
            elif status_code == 500:
                print(f"   🔥 服务器错误 (500) - 需要修复")
                try:
                    error_text = response.text[:200] + "..." if len(response.text) > 200 else response.text
                    print(f"   错误详情: {error_text}")
                except:
                    print(f"   无法获取错误详情")
                results.append(False)
            else:
                print(f"   ⚠️  其他状态码: {status_code}")
                results.append(False)
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ 连接失败 - Django服务器未运行?")
            results.append(False)
        except requests.exceptions.Timeout:
            print(f"   ⏰ 请求超时")
            results.append(False)
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
            results.append(False)
    
    # 总结结果
    print("\n" + "=" * 50)
    print("📊 测试结果总结")
    print("=" * 50)
    
    success_count = sum(results)
    total_count = len(results)
    
    for i, (test_case, result) in enumerate(zip(test_cases, results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{i+1}. {test_case['name']}: {status}")
    
    print(f"\n总体结果: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("🎉 所有路径测试通过！")
        return True
    else:
        print("⚠️  部分路径存在问题，需要进一步调试")
        return False

def test_health():
    """测试服务健康状态"""
    print("\n🏥 测试Django服务健康状态")
    print("-" * 30)
    
    try:
        response = requests.get(f"{BASE_URL}/health/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 服务正常: {data.get('status')}")
            print(f"   版本: {data.get('version')}")
            return True
        else:
            print(f"❌ 服务异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
    
    return False

if __name__ == "__main__":
    print("🚀 AnsFlow API路径兼容性验证")
    print("=" * 60)
    
    # 检查服务健康状态
    if not test_health():
        print("\n❌ Django服务未正常运行，请先启动服务")
        print("   启动命令: cd backend/django_service && python manage.py runserver 8000")
        sys.exit(1)
    
    # 测试API路径
    success = test_api_paths()
    
    if success:
        print("\n🎉 API路径兼容性修复验证成功！")
        print("✅ 前端现在可以使用两种路径格式访问executions API")
    else:
        print("\n⚠️  仍有问题需要解决，请检查上述错误信息")
    
    print("\n📋 路径说明:")
    print("   - 推荐使用: /api/v1/cicd/executions/ (标准路径)")
    print("   - 兼容支持: /api/v1/executions/ (前端兼容)")
