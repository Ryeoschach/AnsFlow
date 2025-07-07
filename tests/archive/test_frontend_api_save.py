#!/usr/bin/env python3
"""
测试前端API调用的流水线保存功能
验证前端发送的数据格式和后端处理是否正确
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"

def get_auth_token():
    """获取认证令牌"""
    try:
        response = requests.post(f"{BASE_URL}/auth/token/", json={
            'username': 'admin',
            'password': 'admin123'
        })
        if response.status_code == 200:
            data = response.json()
            token = data.get('access') or data.get('token')
            if token:
                print("✅ 成功获取认证令牌")
                return token
            else:
                print(f"❌ 响应中没有找到令牌: {data}")
                return None
        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"响应: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

def test_frontend_api_save():
    """测试前端API保存功能"""
    print("="*80)
    print("🔍 前端API流水线保存功能测试")
    print("="*80)
    
    # 获取认证令牌
    token = get_auth_token()
    if not token:
        return False
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 1. 获取一个测试流水线
    print("\n1. 获取测试流水线...")
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/", headers=headers)
    if response.status_code != 200:
        print(f"❌ 获取流水线列表失败: {response.status_code}")
        return False
    
    pipelines_data = response.json()
    pipeline_list = pipelines_data.get('results', pipelines_data)
    
    if not pipeline_list:
        print("❌ 没有可用的流水线进行测试")
        return False
    
    # 选择一个流水线
    test_pipeline = pipeline_list[0]
    pipeline_id = test_pipeline['id']
    print(f"✅ 选择测试流水线: {test_pipeline['name']} (ID: {pipeline_id})")
    
    # 2. 获取详细信息（模拟前端编辑器加载）
    print(f"\n2. 获取流水线详情...")
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/", headers=headers)
    if response.status_code != 200:
        print(f"❌ 获取流水线详情失败: {response.status_code}")
        return False
    
    original_pipeline = response.json()
    original_steps = original_pipeline.get('steps', [])
    print(f"✅ 编辑前步骤数量: {len(original_steps)}")
    
    # 3. 模拟前端PipelineEditor的handleSavePipeline
    print(f"\n3. 模拟前端保存流程...")
    
    # 构造前端发送的数据格式（模拟PipelineEditor的handleSavePipeline函数）
    frontend_steps = [
        {
            "name": "前端测试步骤1 - 代码拉取",
            "step_type": "fetch_code",
            "description": "模拟前端编辑器的代码拉取步骤",
            "parameters": {
                "repository": "https://github.com/test/frontend-repo.git",
                "branch": "development",
                "depth": 1,
                "timeout": 300
            },
            "order": 1,
            "is_active": True,
            "git_credential": None
        },
        {
            "name": "前端测试步骤2 - Ansible自动化",
            "step_type": "ansible",
            "description": "模拟前端编辑器的Ansible步骤",
            "parameters": {
                "playbook_id": 1,
                "inventory_id": 1,
                "credential_id": 1,
                "extra_vars": {
                    "environment": "test",
                    "service_name": "frontend-api"
                },
                "tags": "deploy,config",
                "verbose": True,
                "timeout": 900
            },
            "order": 2,
            "is_active": True,
            "git_credential": None
        },
        {
            "name": "前端测试步骤3 - 前端构建",
            "step_type": "build",
            "description": "模拟前端编辑器的构建步骤",
            "parameters": {
                "build_tool": "npm",
                "build_command": "npm ci && npm run build:prod",
                "output_dir": "dist",
                "node_version": "18",
                "timeout": 600
            },
            "order": 3,
            "is_active": True,
            "git_credential": None
        },
        {
            "name": "前端测试步骤4 - 测试执行",
            "step_type": "test",
            "description": "模拟前端编辑器的测试步骤",
            "parameters": {
                "test_command": "npm run test:unit && npm run test:e2e",
                "coverage": True,
                "fail_on_error": True,
                "timeout": 1200
            },
            "order": 4,
            "is_active": True,
            "git_credential": None
        }
    ]
    
    # 构造完整的更新数据（完全模拟前端PipelineEditor的数据格式）
    update_data = {
        "name": original_pipeline.get('name'),
        "description": f"{original_pipeline.get('description', '')} [前端API测试更新 {int(time.time())}]",
        "project": original_pipeline.get('project'),
        "is_active": original_pipeline.get('is_active', True),
        "execution_mode": original_pipeline.get('execution_mode', 'local'),
        "execution_tool": original_pipeline.get('execution_tool'),
        "tool_job_name": original_pipeline.get('tool_job_name'),
        "tool_job_config": original_pipeline.get('tool_job_config'),
        "steps": frontend_steps
    }
    
    print(f"发送更新请求，包含 {len(frontend_steps)} 个前端编辑的步骤...")
    print(f"更新数据结构: {json.dumps(update_data, indent=2, ensure_ascii=False)[:500]}...")
    
    # 4. 发送API更新请求（模拟前端apiService.updatePipeline）
    print(f"\n4. 发送API更新请求...")
    
    response = requests.put(
        f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/",
        json=update_data,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ API更新失败: {response.status_code}")
        print(f"错误响应: {response.text}")
        return False
    
    print("✅ API更新成功！")
    updated_response = response.json()
    
    # 5. 验证API响应数据
    print(f"\n5. 验证API响应数据...")
    
    response_steps = updated_response.get('steps', [])
    print(f"API响应中的步骤数量: {len(response_steps)}")
    
    if len(response_steps) != len(frontend_steps):
        print(f"❌ API响应步骤数量不匹配！发送: {len(frontend_steps)}, 响应: {len(response_steps)}")
        return False
    
    # 验证每个步骤
    for i, (sent_step, response_step) in enumerate(zip(frontend_steps, response_steps)):
        print(f"  步骤 {i+1}: {response_step.get('name')} - {response_step.get('step_type')}")
        
        # 检查基本字段
        if response_step.get('name') != sent_step['name']:
            print(f"    ❌ 步骤名称不匹配: 发送 '{sent_step['name']}', 响应 '{response_step.get('name')}'")
            return False
        
        if response_step.get('step_type') != sent_step['step_type']:
            print(f"    ❌ 步骤类型不匹配: 发送 '{sent_step['step_type']}', 响应 '{response_step.get('step_type')}'")
            return False
        
        # 检查参数（ansible步骤特别重要）
        if sent_step['step_type'] == 'ansible':
            sent_params = sent_step['parameters']
            response_params = response_step.get('ansible_parameters', {})
            
            # 检查关键参数
            for key in ['playbook_id', 'inventory_id', 'credential_id']:
                if key in sent_params and sent_params[key] != response_params.get(key):
                    print(f"    ❌ Ansible参数 {key} 不匹配: 发送 {sent_params[key]}, 响应 {response_params.get(key)}")
                    return False
    
    print("✅ API响应验证通过")
    
    # 6. 重新获取流水线详情验证数据库
    print(f"\n6. 验证数据库持久化...")
    time.sleep(1)  # 等待数据库写入
    
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/", headers=headers)
    if response.status_code != 200:
        print(f"❌ 重新获取流水线详情失败: {response.status_code}")
        return False
    
    persisted_pipeline = response.json()
    persisted_steps = persisted_pipeline.get('steps', [])
    
    print(f"数据库中的步骤数量: {len(persisted_steps)}")
    
    if len(persisted_steps) != len(frontend_steps):
        print(f"❌ 数据库步骤数量不匹配！期望: {len(frontend_steps)}, 实际: {len(persisted_steps)}")
        return False
    
    # 验证数据库中的步骤内容
    for i, (sent_step, db_step) in enumerate(zip(frontend_steps, persisted_steps)):
        if db_step.get('name') != sent_step['name']:
            print(f"    ❌ 数据库步骤 {i+1} 名称不匹配: 期望 '{sent_step['name']}', 实际 '{db_step.get('name')}'")
            return False
    
    print("✅ 数据库持久化验证通过")
    
    # 7. 测试预览API一致性
    print(f"\n7. 测试预览API一致性...")
    
    preview_data = {
        "pipeline_id": pipeline_id,
        "preview_mode": False  # 实际模式，应该读取数据库
    }
    
    response = requests.post(
        f"{BASE_URL}/cicd/pipelines/preview/",
        json=preview_data,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ 预览API调用失败: {response.status_code}")
        return False
    
    preview_result = response.json()
    preview_content = preview_result.get('content', '')
    
    # 检查预览内容是否包含保存的步骤
    steps_found_in_preview = 0
    for step in frontend_steps:
        if step['name'] in preview_content:
            steps_found_in_preview += 1
            print(f"  ✅ 预览中找到: {step['name']}")
        else:
            print(f"  ❌ 预览中未找到: {step['name']}")
    
    if steps_found_in_preview == len(frontend_steps):
        print("✅ 预览API与保存内容一致")
    else:
        print(f"❌ 预览API内容不完整: 找到 {steps_found_in_preview}/{len(frontend_steps)} 个步骤")
        return False
    
    return True

def main():
    print("AnsFlow 前端API流水线保存功能测试")
    print("="*80)
    
    success = test_frontend_api_save()
    
    if success:
        print("\n" + "="*80)
        print("🎉 前端API测试通过！")
        print("✅ 前端发送的数据格式正确")
        print("✅ 后端API处理正常")
        print("✅ 数据库同步正确")
        print("✅ 预览API一致")
        print("="*80)
        print("\n💡 问题可能在于：")
        print("1. 前端编辑器状态管理")
        print("2. 前端用户交互流程")
        print("3. 前端数据更新后的UI刷新")
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("❌ 前端API测试失败！")
        print("需要检查前端-后端API交互")
        print("="*80)
        sys.exit(1)

if __name__ == "__main__":
    main()
