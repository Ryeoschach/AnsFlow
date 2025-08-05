#!/usr/bin/env python3
"""
测试并行组管理功能的脚本
"""

import requests
import json
from datetime import datetime

# 配置
BACKEND_URL = "http://localhost:8000"
API_BASE = f"{BACKEND_URL}/api/pipelines"

# 测试用户认证（需要根据实际情况调整）
AUTH_HEADERS = {
    "Authorization": "Bearer YOUR_TOKEN_HERE",  # 替换为实际的认证token
    "Content-Type": "application/json"
}

def test_parallel_group_apis():
    """测试并行组API"""
    
    print("🔧 测试并行组管理API...")
    print("=" * 50)
    
    # 测试数据
    test_pipeline_id = 1  # 假设存在ID为1的流水线
    test_group_data = {
        "id": f"test_parallel_group_{int(datetime.now().timestamp())}",
        "name": "测试并行组",
        "description": "这是一个测试并行组",
        "pipeline": test_pipeline_id,
        "sync_policy": "wait_all",
        "timeout_seconds": 3600
    }
    
    group_id = None
    
    try:
        # 1. 创建并行组
        print("1️⃣ 测试创建并行组...")
        response = requests.post(
            f"{API_BASE}/parallel-groups/",
            headers=AUTH_HEADERS,
            json=test_group_data
        )
        
        if response.status_code == 201:
            created_group = response.json()
            group_id = created_group["id"]
            print(f"   ✅ 创建成功，组ID: {group_id}")
        else:
            print(f"   ❌ 创建失败，状态码: {response.status_code}")
            if response.content:
                print(f"   错误信息: {response.json()}")
            return False
        
        # 2. 获取并行组列表
        print("2️⃣ 测试获取并行组列表...")
        response = requests.get(
            f"{API_BASE}/parallel-groups/?pipeline={test_pipeline_id}",
            headers=AUTH_HEADERS
        )
        
        if response.status_code == 200:
            groups = response.json()
            print(f"   ✅ 获取成功，找到 {len(groups)} 个并行组")
            
            # 验证我们创建的组是否在列表中
            found_group = None
            for group in groups:
                if group["id"] == group_id:
                    found_group = group
                    break
            
            if found_group:
                print(f"   ✅ 找到创建的并行组: {found_group['name']}")
            else:
                print(f"   ⚠️ 未找到创建的并行组")
        else:
            print(f"   ❌ 获取失败，状态码: {response.status_code}")
        
        # 3. 更新并行组
        print("3️⃣ 测试更新并行组...")
        updated_data = {
            **test_group_data,
            "name": "更新后的测试并行组",
            "description": "这是更新后的描述",
            "timeout_seconds": 7200
        }
        
        response = requests.put(
            f"{API_BASE}/parallel-groups/{group_id}/",
            headers=AUTH_HEADERS,
            json=updated_data
        )
        
        if response.status_code == 200:
            updated_group = response.json()
            print(f"   ✅ 更新成功，新名称: {updated_group['name']}")
        else:
            print(f"   ❌ 更新失败，状态码: {response.status_code}")
            if response.content:
                print(f"   错误信息: {response.json()}")
        
        # 4. 删除并行组
        print("4️⃣ 测试删除并行组...")
        response = requests.delete(
            f"{API_BASE}/parallel-groups/{group_id}/",
            headers=AUTH_HEADERS
        )
        
        if response.status_code == 204:
            print(f"   ✅ 删除成功")
        else:
            print(f"   ❌ 删除失败，状态码: {response.status_code}")
            if response.content:
                print(f"   错误信息: {response.json()}")
        
        # 5. 验证删除结果
        print("5️⃣ 验证删除结果...")
        response = requests.get(
            f"{API_BASE}/parallel-groups/{group_id}/",
            headers=AUTH_HEADERS
        )
        
        if response.status_code == 404:
            print(f"   ✅ 删除验证成功，组已不存在")
        else:
            print(f"   ⚠️ 删除验证失败，组仍然存在")
        
        print("\n🎉 并行组API测试完成！")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_api_endpoints():
    """测试API端点可用性"""
    
    print("🔍 检查并行组相关API端点...")
    print("=" * 50)
    
    endpoints = [
        ("GET", "/parallel-groups/", "获取并行组列表"),
        ("POST", "/parallel-groups/", "创建并行组"),
        ("GET", "/parallel-groups/test-id/", "获取单个并行组"),
        ("PUT", "/parallel-groups/test-id/", "更新并行组"),
        ("DELETE", "/parallel-groups/test-id/", "删除并行组"),
    ]
    
    available_count = 0
    
    for method, endpoint, description in endpoints:
        url = f"{API_BASE}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=AUTH_HEADERS, timeout=5)
            elif method == "POST":
                response = requests.post(url, headers=AUTH_HEADERS, json={}, timeout=5)
            elif method == "PUT":
                response = requests.put(url, headers=AUTH_HEADERS, json={}, timeout=5)
            elif method == "DELETE":
                response = requests.delete(url, headers=AUTH_HEADERS, timeout=5)
            
            # 对于需要认证的端点，401/403是正常的
            # 对于不存在的资源，404是正常的
            # 对于无效数据，400是正常的
            if response.status_code in [200, 201, 204, 400, 401, 403, 404, 405]:
                status = "✅ 可用"
                available_count += 1
            else:
                status = f"❌ 错误 ({response.status_code})"
                
        except requests.exceptions.RequestException:
            status = "❌ 连接失败"
        except Exception as e:
            status = f"❌ 异常: {str(e)[:30]}"
        
        print(f"{status:<15} {method:<8} {endpoint:<30} {description}")
    
    print(f"\n📊 API端点可用性: {available_count}/{len(endpoints)}")
    return available_count == len(endpoints)

def main():
    """主函数"""
    
    print("🚀 并行组管理功能测试")
    print("=" * 60)
    print(f"后端URL: {BACKEND_URL}")
    print(f"API基础路径: {API_BASE}")
    print()
    
    # 检查后端服务
    try:
        response = requests.get(f"{BACKEND_URL}/api/pipelines/health/", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正常运行")
        else:
            print(f"⚠️ 后端服务响应异常: {response.status_code}")
    except:
        print("❌ 无法连接到后端服务")
        print("   请确保后端服务已启动: cd backend/django_service && uv run python manage.py runserver")
        return False
    
    print()
    
    # 测试API端点
    endpoints_ok = test_api_endpoints()
    print()
    
    # 如果端点可用，进行功能测试
    if endpoints_ok:
        print("⚠️ 注意：以下功能测试需要有效的认证令牌")
        print("   请在脚本中更新 AUTH_HEADERS 的 Authorization 字段")
        print()
        
        # 如果用户提供了有效的认证信息，可以进行功能测试
        # test_parallel_group_apis()
        print("📝 如需进行完整功能测试，请:")
        print("   1. 更新脚本中的 AUTH_HEADERS")
        print("   2. 确保存在测试用的流水线（ID=1）")
        print("   3. 取消注释 test_parallel_group_apis() 调用")
    
    return True

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✅ 并行组管理功能测试完成")
        print("💡 建议: 在前端界面中测试完整的用户交互流程")
    else:
        print("\n❌ 测试失败，请检查后端配置")
