#!/usr/bin/env python3
"""
测试流水线列表API是否包含执行模式字段
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def get_auth_token():
    """获取认证令牌"""
    print("获取认证令牌...")
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/token/", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access') or data.get('token')
        if token:
            print("✅ 成功获取认证令牌")
            return token
    
    print(f"❌ 获取认证令牌失败: {response.status_code}")
    return None

def test_list_api_fields():
    """测试列表API字段"""
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("1. 测试流水线列表API字段...")
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 获取流水线列表失败: {response.status_code}")
        return False
    
    pipelines_data = response.json()
    pipeline_list = pipelines_data.get('results', pipelines_data)
    
    if not pipeline_list:
        print("❌ 没有可用的流水线")
        return False
    
    # 检查第一个流水线的字段
    first_pipeline = pipeline_list[0]
    pipeline_id = first_pipeline['id']
    
    print(f"2. 检查流水线 ID={pipeline_id} 的列表字段:")
    
    # 检查执行模式相关字段
    execution_fields = [
        'execution_mode', 'execution_tool', 'execution_tool_name', 
        'execution_tool_type', 'tool_job_name'
    ]
    
    list_has_execution_fields = []
    for field in execution_fields:
        if field in first_pipeline:
            value = first_pipeline[field]
            print(f"   ✅ {field}: {value}")
            list_has_execution_fields.append(field)
        else:
            print(f"   ❌ {field}: 缺失")
    
    print(f"\n3. 列表API包含的执行字段: {list_has_execution_fields}")
    
    # 同时检查详情API
    print(f"\n4. 对比详情API字段...")
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 获取流水线详情失败: {response.status_code}")
        return False
    
    detail_pipeline = response.json()
    
    print(f"详情API的执行模式字段:")
    detail_has_execution_fields = []
    for field in execution_fields:
        if field in detail_pipeline:
            value = detail_pipeline[field]
            print(f"   ✅ {field}: {value}")
            detail_has_execution_fields.append(field)
        else:
            print(f"   ❌ {field}: 缺失")
    
    print(f"\n5. 详情API包含的执行字段: {detail_has_execution_fields}")
    
    # 比较列表和详情的字段一致性
    missing_in_list = set(detail_has_execution_fields) - set(list_has_execution_fields)
    if missing_in_list:
        print(f"\n❌ 列表API缺少的字段: {missing_in_list}")
        return False
    else:
        print(f"\n✅ 列表API和详情API的执行模式字段一致！")
        return True

if __name__ == "__main__":
    print("AnsFlow 流水线列表API字段测试")
    print("="*60)
    
    result = test_list_api_fields()
    
    if result:
        print("\n🎉 列表API字段修复成功！前端应该能正确显示执行模式了！")
    else:
        print("\n❌ 列表API字段仍有问题")
    
    sys.exit(0 if result else 1)
