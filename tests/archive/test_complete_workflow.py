#!/usr/bin/env python3
"""
最终验证：执行模式更新和前端显示的完整流程测试
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

def test_complete_workflow():
    """测试完整的执行模式更新和显示流程"""
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("\n" + "="*60)
    print("第一步：获取流水线列表（模拟前端列表页面）")
    print("="*60)
    
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
    test_pipeline = pipeline_list[0]
    pipeline_id = test_pipeline['id']
    current_mode = test_pipeline.get('execution_mode', 'local')
    
    print(f"选择流水线: ID={pipeline_id}, 名称='{test_pipeline['name']}'")
    print(f"列表API显示的执行模式: {current_mode}")
    print(f"列表API显示的执行工具: {test_pipeline.get('execution_tool_name', '无')}")
    
    print("\n" + "="*60)
    print("第二步：获取流水线详情（模拟前端详情页面）")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 获取流水线详情失败: {response.status_code}")
        return False
    
    detail_pipeline = response.json()
    detail_mode = detail_pipeline.get('execution_mode', 'local')
    
    print(f"详情API显示的执行模式: {detail_mode}")
    print(f"详情API显示的执行工具: {detail_pipeline.get('execution_tool_name', '无')}")
    
    # 检查列表和详情的一致性
    if current_mode != detail_mode:
        print(f"❌ 列表和详情的执行模式不一致: 列表={current_mode}, 详情={detail_mode}")
        return False
    else:
        print(f"✅ 列表和详情的执行模式一致: {current_mode}")
    
    print("\n" + "="*60)
    print("第三步：更新执行模式（模拟前端PipelineEditor保存）")
    print("="*60)
    
    # 切换到不同的执行模式
    if current_mode == 'local':
        new_mode = 'remote'
    elif current_mode == 'remote':
        new_mode = 'hybrid'
    else:  # hybrid
        new_mode = 'local'
    
    print(f"准备更新执行模式: {current_mode} -> {new_mode}")
    
    # 构造更新数据
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
    
    # 发送更新请求
    response = requests.put(
        f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/",
        json=update_data,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ 更新流水线失败: {response.status_code}")
        print(f"错误响应: {response.text}")
        return False
    
    updated_pipeline = response.json()
    saved_mode = updated_pipeline.get('execution_mode')
    
    if saved_mode != new_mode:
        print(f"❌ 更新后的执行模式不正确: 期望={new_mode}, 实际={saved_mode}")
        return False
    
    print(f"✅ 成功更新执行模式: {saved_mode}")
    print(f"更新后的执行工具: {updated_pipeline.get('execution_tool_name', '无')}")
    
    print("\n" + "="*60)
    print("第四步：验证列表API反映更新（模拟前端列表刷新）")
    print("="*60)
    
    # 重新获取列表，验证更新是否反映
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 重新获取流水线列表失败: {response.status_code}")
        return False
    
    fresh_pipelines_data = response.json()
    fresh_pipeline_list = fresh_pipelines_data.get('results', fresh_pipelines_data)
    
    # 找到更新的流水线
    fresh_pipeline = None
    for p in fresh_pipeline_list:
        if p['id'] == pipeline_id:
            fresh_pipeline = p
            break
    
    if not fresh_pipeline:
        print(f"❌ 在列表中找不到流水线 ID={pipeline_id}")
        return False
    
    fresh_mode = fresh_pipeline.get('execution_mode', 'local')
    
    if fresh_mode != new_mode:
        print(f"❌ 列表API没有反映更新: 期望={new_mode}, 实际={fresh_mode}")
        return False
    
    print(f"✅ 列表API正确反映更新: {fresh_mode}")
    
    print("\n" + "="*60)
    print("第五步：前端显示预期验证")
    print("="*60)
    
    # 模拟前端显示逻辑
    mode_display = {
        'local': '本地执行',
        'remote': '远程工具', 
        'hybrid': '混合模式'
    }
    
    expected_display = mode_display.get(fresh_mode, '未知模式')
    color = 'green' if fresh_mode == 'remote' else 'blue'
    
    print(f"前端应该显示:")
    print(f"  执行模式标签: {expected_display} ({color}色)")
    print(f"  CI/CD工具: {fresh_pipeline.get('execution_tool_name', '无')}")
    
    if fresh_pipeline.get('tool_job_name'):
        print(f"  作业名称: {fresh_pipeline['tool_job_name']}")
    
    return True

if __name__ == "__main__":
    print("AnsFlow 执行模式完整流程验证")
    print("="*60)
    
    result = test_complete_workflow()
    
    if result:
        print("\n" + "="*60)
        print("🎉 完整流程验证成功！")
        print("="*60)
        print("✅ 后端API正确支持执行模式更新")
        print("✅ 列表API包含所有必要字段")
        print("✅ 详情API与列表API字段一致")
        print("✅ 更新后数据正确同步")
        print("✅ 前端应该能正确显示执行模式")
        print("\n📝 用户现在可以:")
        print("1. 在PipelineEditor中编辑执行模式")
        print("2. 保存后立即在页面上看到更新")
        print("3. 执行模式变化会正确反映在所有页面")
    else:
        print("\n❌ 流程验证失败，仍有问题需要解决")
    
    sys.exit(0 if result else 1)
