#!/usr/bin/env python3
"""
创建测试流水线，验证前端数据刷新是否正确
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

def test_frontend_data_sync():
    """测试前端数据同步问题"""
    
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
        print("❌ 没有可用的流水线")
        return False
    
    # 选择测试流水线
    test_pipeline = None
    for pipeline in pipeline_list:
        if pipeline['name'] == 'Integration Test Pipeline':
            test_pipeline = pipeline
            break
    
    if not test_pipeline:
        print("❌ 没有找到测试流水线 'Integration Test Pipeline'")
        return False
    
    pipeline_id = test_pipeline['id']
    print(f"2. 使用测试流水线: ID={pipeline_id}, 名称='{test_pipeline['name']}'")
    
    # 检查列表中的执行模式
    list_execution_mode = test_pipeline.get('execution_mode', '未设置')
    print(f"   列表中显示的执行模式: {list_execution_mode}")
    
    # 获取详细信息
    print("3. 获取流水线详情...")
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 获取流水线详情失败: {response.status_code}")
        return False
    
    detail_pipeline = response.json()
    detail_execution_mode = detail_pipeline.get('execution_mode', '未设置')
    detail_tool_name = detail_pipeline.get('execution_tool_name', '无')
    
    print(f"   详情中显示的执行模式: {detail_execution_mode}")
    print(f"   详情中显示的执行工具: {detail_tool_name}")
    
    # 检查数据一致性
    if list_execution_mode == detail_execution_mode:
        print("✅ 列表和详情数据一致")
    else:
        print(f"❌ 数据不一致: 列表={list_execution_mode}, 详情={detail_execution_mode}")
    
    # 模拟执行模式更新（类似前端操作）
    print("\n4. 模拟执行模式更新...")
    
    current_mode = detail_execution_mode
    new_mode = 'hybrid' if current_mode != 'hybrid' else 'local'
    
    update_data = {
        'name': detail_pipeline['name'],
        'description': detail_pipeline.get('description', ''),
        'project': detail_pipeline.get('project'),
        'is_active': detail_pipeline.get('is_active', True),
        'execution_mode': new_mode,
        'execution_tool': detail_pipeline.get('execution_tool'),
        'tool_job_name': detail_pipeline.get('tool_job_name'),
        'tool_job_config': detail_pipeline.get('tool_job_config'),
        'steps': detail_pipeline.get('steps', [])
    }
    
    print(f"   更新执行模式: {current_mode} -> {new_mode}")
    
    # 发送更新请求
    response = requests.put(
        f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/",
        json=update_data,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ 更新失败: {response.status_code}")
        print(f"错误响应: {response.text}")
        return False
    
    updated_pipeline = response.json()
    updated_mode = updated_pipeline.get('execution_mode')
    
    print(f"   ✅ 更新成功，新执行模式: {updated_mode}")
    
    # 再次检查列表数据是否同步
    print("\n5. 验证列表数据同步...")
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/", headers=headers)
    
    if response.status_code == 200:
        updated_list = response.json()
        updated_pipeline_list = updated_list.get('results', updated_list)
        
        for pipeline in updated_pipeline_list:
            if pipeline['id'] == pipeline_id:
                list_updated_mode = pipeline.get('execution_mode', '未设置')
                print(f"   列表中的最新执行模式: {list_updated_mode}")
                
                if list_updated_mode == updated_mode:
                    print("✅ 列表数据已正确同步")
                else:
                    print(f"❌ 列表数据未同步: 期望={updated_mode}, 实际={list_updated_mode}")
                break
        else:
            print("❌ 在列表中未找到对应流水线")
    else:
        print(f"❌ 重新获取列表失败: {response.status_code}")
    
    return True

if __name__ == "__main__":
    print("AnsFlow 前端数据同步测试")
    print("="*60)
    
    result = test_frontend_data_sync()
    
    if result:
        print("\n🎉 数据同步测试完成！")
        print("\n📝 前端调试提示:")
        print("1. 确保前端页面已重新加载或刷新")
        print("2. 检查浏览器网络面板，确认API调用返回最新数据")
        print("3. 检查前端状态管理，确保selectedPipeline被正确更新")
        print("4. 如仍有问题，请清理浏览器缓存")
    else:
        print("\n❌ 数据同步测试失败")
    
    sys.exit(0 if result else 1)
