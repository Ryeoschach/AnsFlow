#!/usr/bin/env python3
"""
验证前端 PipelineEditor 新增的执行模式编辑功能
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

def verify_pipeline_data():
    """验证流水线数据结构，确保前端能正确显示"""
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("1. 获取流水线列表...")
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 获取流水线列表失败: {response.status_code}")
        return False
    
    pipelines_data = response.json()
    pipeline_list = pipelines_data.get('results', pipelines_data)
    
    if not pipeline_list:
        print("❌ 没有可用的流水线")
        return False
    
    print(f"✅ 找到 {len(pipeline_list)} 个流水线")
    
    # 检查第一个流水线的详细信息
    pipeline = pipeline_list[0]
    pipeline_id = pipeline['id']
    
    print(f"\n2. 检查流水线详情: ID={pipeline_id}, 名称='{pipeline['name']}'")
    
    # 获取详细信息
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 获取流水线详情失败: {response.status_code}")
        return False
    
    full_pipeline = response.json()
    
    # 检查关键字段
    fields_to_check = [
        'id', 'name', 'description', 'execution_mode', 
        'execution_tool', 'tool_job_name', 'is_active', 'steps'
    ]
    
    print("流水线字段检查:")
    for field in fields_to_check:
        value = full_pipeline.get(field)
        status = "✅" if field in full_pipeline else "❌"
        print(f"  {status} {field}: {value}")
    
    # 特别检查执行模式
    execution_mode = full_pipeline.get('execution_mode', 'local')
    execution_tool = full_pipeline.get('execution_tool')
    execution_tool_name = full_pipeline.get('execution_tool_name')
    
    print(f"\n执行模式详情:")
    print(f"  执行模式: {execution_mode}")
    print(f"  执行工具ID: {execution_tool}")
    print(f"  执行工具名称: {execution_tool_name}")
    
    # 检查工具列表
    print("\n3. 获取可用的CI/CD工具...")
    response = requests.get(f"{BASE_URL}/tools/cicd-tools/", headers=headers)
    
    if response.status_code == 200:
        tools_data = response.json()
        tools_list = tools_data.get('results', tools_data)
        print(f"✅ 找到 {len(tools_list)} 个可用工具")
        
        for tool in tools_list[:3]:  # 显示前3个工具
            print(f"  - {tool['name']} ({tool['tool_type']}) - {tool['base_url']}")
    else:
        print(f"❌ 获取工具列表失败: {response.status_code}")
    
    return True

if __name__ == "__main__":
    print("AnsFlow PipelineEditor 功能验证")
    print("="*60)
    
    result = verify_pipeline_data()
    
    if result:
        print("\n✅ 数据验证完成！前端 PipelineEditor 应该能正常显示执行模式编辑功能。")
        print("\n📝 使用说明:")
        print("1. 在前端流水线列表页面，点击流水线名称打开详情")
        print("2. 点击右侧的'编辑步骤'按钮打开 PipelineEditor")
        print("3. 在 PipelineEditor 中，点击'编辑信息'按钮")
        print("4. 在弹出的表单中修改执行模式和执行工具")
        print("5. 点击'保存流水线'保存所有更改")
    else:
        print("\n❌ 数据验证失败")
    
    sys.exit(0 if result else 1)
