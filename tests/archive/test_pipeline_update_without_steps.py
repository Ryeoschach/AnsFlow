#!/usr/bin/env python3
"""
测试流水线更新接口，验证不包含 steps 字段的请求是否能成功处理
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def get_auth_token():
    """获取认证令牌"""
    print("获取认证令牌...")
    
    # 尝试使用默认的测试用户凭据
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
    print(f"响应: {response.text}")
    return None

def test_pipeline_update_without_steps():
    """测试不包含 steps 字段的流水线更新请求"""
    
    # 获取认证令牌
    token = get_auth_token()
    if not token:
        return False
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 首先获取现有的流水线列表
    print("1. 获取流水线列表...")
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 获取流水线列表失败: {response.status_code}")
        print(f"响应内容: {response.text}")
        return False
    
    pipelines = response.json()
    print(f"✅ 成功获取流水线数据: {type(pipelines)}")
    
    # 处理分页响应或直接列表响应
    if isinstance(pipelines, dict):
        if 'results' in pipelines:
            pipeline_list = pipelines['results']
        else:
            print(f"响应结构: {list(pipelines.keys())}")
            return False
    else:
        pipeline_list = pipelines
    
    print(f"流水线数量: {len(pipeline_list)}")
    
    if not pipeline_list:
        print("❌ 没有可用的流水线进行测试")
        return False
    
    # 选择第一个流水线进行测试
    pipeline = pipeline_list[0]
    pipeline_id = pipeline['id']
    print(f"2. 选择流水线进行测试: ID={pipeline_id}, 名称='{pipeline['name']}'")
    
    # 构造不包含 steps 字段的更新数据（模拟前端主页面表单提交）
    update_data = {
        'project': pipeline.get('project'),
        'name': pipeline['name'],
        'description': pipeline.get('description', '') + ' [测试更新]',
        'execution_mode': pipeline.get('execution_mode', 'local'),
        'execution_tool': pipeline.get('execution_tool'),
        'is_active': pipeline.get('is_active', True)
    }
    
    print(f"3. 发送更新请求（不包含 steps 字段）...")
    print(f"更新数据: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
    
    # 发送 PUT 请求
    response = requests.put(
        f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/",
        json=update_data,
        headers=headers
    )
    
    print(f"4. 响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ 流水线更新成功！")
        updated_pipeline = response.json()
        print(f"更新后的流水线名称: {updated_pipeline.get('name')}")
        print(f"更新后的描述: {updated_pipeline.get('description')}")
        return True
    else:
        print(f"❌ 流水线更新失败: {response.status_code}")
        print(f"错误响应: {response.text}")
        return False

def test_pipeline_update_with_steps():
    """测试包含 steps 字段的流水线更新请求（PipelineEditor 场景）"""
    
    print("\n" + "="*60)
    print("测试包含 steps 字段的更新请求")
    print("="*60)
    
    # 获取认证令牌
    token = get_auth_token()
    if not token:
        return False
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 获取流水线列表
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/", headers=headers)
    if response.status_code != 200:
        print(f"❌ 获取流水线列表失败: {response.status_code}")
        return False
    
    pipelines = response.json()
    
    # 处理分页响应或直接列表响应
    if isinstance(pipelines, dict):
        if 'results' in pipelines:
            pipeline_list = pipelines['results']
        else:
            print(f"响应结构: {list(pipelines.keys())}")
            return False
    else:
        pipeline_list = pipelines
    
    if not pipeline_list:
        print("❌ 没有可用的流水线进行测试")
        return False
    
    pipeline = pipeline_list[0]
    pipeline_id = pipeline['id']
    
    # 获取流水线详情（包含 steps）
    print(f"1. 获取流水线详情: ID={pipeline_id}")
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 获取流水线详情失败: {response.status_code}")
        return False
    
    full_pipeline = response.json()
    current_steps = full_pipeline.get('steps', [])
    print(f"当前步骤数量: {len(current_steps)}")
    
    # 构造包含 steps 字段的更新数据
    update_data = {
        'name': full_pipeline['name'],
        'description': full_pipeline.get('description', '') + ' [Editor测试更新]',
        'project': full_pipeline.get('project'),
        'is_active': full_pipeline.get('is_active', True),
        'steps': [
            {
                'name': '测试步骤1',
                'step_type': 'fetch_code',
                'description': '代码拉取步骤',
                'parameters': {'repo_url': 'https://github.com/test/repo.git'},
                'order': 1,
                'is_active': True
            },
            {
                'name': '测试步骤2',
                'step_type': 'build',
                'description': '构建步骤',
                'parameters': {'build_command': 'npm run build'},
                'order': 2,
                'is_active': True
            }
        ]
    }
    
    print(f"2. 发送更新请求（包含 steps 字段）...")
    print(f"步骤数量: {len(update_data['steps'])}")
    
    # 发送 PUT 请求
    response = requests.put(
        f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/",
        json=update_data,
        headers=headers
    )
    
    print(f"3. 响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ 包含 steps 的流水线更新成功！")
        updated_pipeline = response.json()
        updated_steps = updated_pipeline.get('steps', [])
        print(f"更新后的步骤数量: {len(updated_steps)}")
        return True
    else:
        print(f"❌ 包含 steps 的流水线更新失败: {response.status_code}")
        print(f"错误响应: {response.text}")
        return False

if __name__ == "__main__":
    print("AnsFlow 流水线更新接口测试")
    print("="*60)
    print("测试不包含 steps 字段的更新请求（主页面表单场景）")
    print("="*60)
    
    # 测试不包含 steps 的更新
    test1_result = test_pipeline_update_without_steps()
    
    # 测试包含 steps 的更新
    test2_result = test_pipeline_update_with_steps()
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    print(f"不包含 steps 字段的更新: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"包含 steps 字段的更新: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！流水线更新接口修复成功！")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败，需要进一步检查")
        sys.exit(1)
