#!/usr/bin/env python3
"""
测试流水线执行模式更新是否正常工作
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

def test_execution_mode_update():
    """测试执行模式更新"""
    
    # 获取认证令牌
    token = get_auth_token()
    if not token:
        return False
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 获取流水线列表
    print("1. 获取流水线列表...")
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 获取流水线列表失败: {response.status_code}")
        return False
    
    pipelines_data = response.json()
    pipeline_list = pipelines_data.get('results', pipelines_data)
    
    if not pipeline_list:
        print("❌ 没有可用的流水线进行测试")
        return False
    
    # 选择第一个流水线
    pipeline = pipeline_list[0]
    pipeline_id = pipeline['id']
    current_mode = pipeline.get('execution_mode', 'local')
    
    print(f"2. 选择流水线进行测试: ID={pipeline_id}, 名称='{pipeline['name']}'")
    print(f"   当前执行模式: {current_mode}")
    
    # 获取流水线详情
    print("3. 获取流水线详情...")
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 获取流水线详情失败: {response.status_code}")
        return False
    
    full_pipeline = response.json()
    current_steps = full_pipeline.get('steps', [])
    
    # 测试从 local -> remote -> hybrid -> local 的循环更新
    test_modes = ['remote', 'hybrid', 'local']
    
    for new_mode in test_modes:
        print(f"\n4. 测试更新执行模式: {current_mode} -> {new_mode}")
        
        # 构造包含执行模式的更新数据（模拟 PipelineEditor 保存）
        update_data = {
            'name': full_pipeline['name'],
            'description': full_pipeline.get('description', ''),
            'project': full_pipeline.get('project'),
            'is_active': full_pipeline.get('is_active', True),
            'execution_mode': new_mode,
            'execution_tool': full_pipeline.get('execution_tool'),
            'tool_job_name': full_pipeline.get('tool_job_name'),
            'tool_job_config': full_pipeline.get('tool_job_config'),
            'steps': [
                {
                    'name': step.get('name'),
                    'step_type': step.get('step_type'),
                    'description': step.get('description', ''),
                    'parameters': step.get('parameters', {}),
                    'order': step.get('order'),
                    'is_active': step.get('is_active', True)
                }
                for step in current_steps
            ]
        }
        
        print(f"   发送更新请求: execution_mode={new_mode}")
        
        # 发送 PUT 请求
        response = requests.put(
            f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/",
            json=update_data,
            headers=headers
        )
        
        print(f"   响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            updated_pipeline = response.json()
            saved_mode = updated_pipeline.get('execution_mode')
            
            if saved_mode == new_mode:
                print(f"   ✅ 执行模式更新成功: {saved_mode}")
                current_mode = saved_mode
                full_pipeline = updated_pipeline  # 更新引用
            else:
                print(f"   ❌ 执行模式更新失败: 期望={new_mode}, 实际={saved_mode}")
                return False
        else:
            print(f"   ❌ 流水线更新失败: {response.status_code}")
            print(f"   错误响应: {response.text}")
            return False
    
    print(f"\n✅ 所有执行模式更新测试通过！")
    return True

if __name__ == "__main__":
    print("AnsFlow 流水线执行模式更新测试")
    print("="*60)
    
    result = test_execution_mode_update()
    
    if result:
        print("\n🎉 执行模式更新功能正常工作！")
        sys.exit(0)
    else:
        print("\n❌ 执行模式更新测试失败")
        sys.exit(1)
