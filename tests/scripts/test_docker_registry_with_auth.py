#!/usr/bin/env python3
"""
Docker注册表API认证测试
测试带认证的Docker注册表API功能
"""

import requests
import json

def get_auth_token():
    """获取认证令牌"""
    login_url = "http://localhost:8000/api/v1/auth/token/"
    
    # 尝试使用默认的admin用户
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(login_url, json=login_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('access'), None
        else:
            return None, f"登录失败: {response.status_code} - {response.text}"
    except Exception as e:
        return None, f"登录请求失败: {str(e)}"

def test_docker_registry_with_auth():
    """测试带认证的Docker注册表API"""
    
    print("🔐 开始Docker注册表API认证测试")
    print("=" * 50)
    
    # 获取认证令牌
    print("\n=== 步骤1: 获取认证令牌 ===")
    access_token, error = get_auth_token()
    
    if error:
        print(f"❌ 认证失败: {error}")
        print("\n建议:")
        print("1. 确保Django服务正在运行")
        print("2. 检查是否有默认用户账号")
        print("3. 或者创建超级用户: python manage.py createsuperuser")
        return
    
    print(f"✅ 认证成功，获得令牌: {access_token[:20]}...")
    
    # 设置认证头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    base_url = "http://localhost:8000"
    
    # 测试数据
    test_registry = {
        "name": "测试注册表",
        "url": "https://registry-test.example.com",
        "registry_type": "dockerhub",
        "description": "这是一个测试注册表"
    }
    
    # 测试2: 创建Docker注册表
    print("\n=== 步骤2: 创建Docker注册表 ===")
    try:
        response = requests.post(
            f"{base_url}/api/v1/docker/registries",
            headers=headers,
            data=json.dumps(test_registry),
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code in [200, 201]:
            print("✅ 创建注册表成功")
            registry_data = response.json()
            registry_id = registry_data.get('id')
        elif response.status_code == 400:
            print("⚠️ 创建失败 - 可能是验证错误或重复数据")
            registry_id = None
        else:
            print(f"❌ 创建注册表失败: {response.status_code}")
            registry_id = None
            
    except Exception as e:
        print(f"❌ 创建注册表异常: {e}")
        registry_id = None
    
    # 测试3: 获取注册表列表
    print("\n=== 步骤3: 获取注册表列表 ===")
    try:
        response = requests.get(
            f"{base_url}/api/v1/docker/registries",
            headers=headers,
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            registries = response.json()
            print(f"✅ 获取成功，共有 {len(registries.get('results', []))} 个注册表")
            
            # 显示前几个注册表
            results = registries.get('results', [])
            for i, registry in enumerate(results[:3]):
                print(f"  - 注册表{i+1}: {registry.get('name', 'Unknown')} ({registry.get('url', 'No URL')})")
        else:
            print(f"❌ 获取注册表列表失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 获取注册表列表异常: {e}")
    
    # 测试4: 删除测试注册表（如果创建成功）
    if registry_id:
        print(f"\n=== 步骤4: 删除测试注册表 (ID: {registry_id}) ===")
        try:
            response = requests.delete(
                f"{base_url}/api/v1/docker/registries/{registry_id}/",
                headers=headers,
                timeout=10
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code in [200, 204]:
                print("✅ 删除注册表成功")
            else:
                print(f"❌ 删除注册表失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 删除注册表异常: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Docker注册表API认证测试完成!")
    print("\n测试结果总结:")
    print("- 如果所有步骤都成功，说明API完全正常")
    print("- 如果只是认证失败，说明需要创建用户账号")
    print("- 如果API操作成功，说明URL修复完全有效")

def create_test_user():
    """创建测试用户的辅助脚本"""
    print("\n" + "=" * 50)
    print("📝 创建测试用户指南")
    print("=" * 50)
    print("\n如果认证失败，请在Django目录中运行以下命令创建超级用户:")
    print("cd backend/django_service")
    print("uv run python manage.py createsuperuser")
    print("\n然后使用创建的用户名和密码更新测试脚本中的登录信息")

if __name__ == '__main__':
    test_docker_registry_with_auth()
    create_test_user()
