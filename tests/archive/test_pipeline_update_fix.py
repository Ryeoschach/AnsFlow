#!/usr/bin/env python3
"""
测试流水线更新修复 - 验证 steps 字段可选
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_pipeline_update_without_steps():
    """测试不包含 steps 字段的流水线更新"""
    
    # 1. 获取现有流水线列表
    print("1. 获取流水线列表...")
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/")
    if response.status_code != 200:
        print(f"获取流水线列表失败: {response.status_code}")
        return False
    
    pipelines = response.json()
    if not pipelines:
        print("没有找到任何流水线")
        return False
    
    # 选择第一个流水线进行测试
    pipeline = pipelines[0]
    pipeline_id = pipeline['id']
    print(f"选择流水线进行测试: ID={pipeline_id}, Name='{pipeline['name']}'")
    
    # 2. 测试不包含 steps 字段的更新（模拟前端主页面表单提交）
    print("\n2. 测试不包含 steps 字段的更新...")
    update_data = {
        "name": pipeline['name'],
        "description": "测试更新 - 不包含 steps 字段",
        "project": pipeline['project'],
        "is_active": pipeline['is_active']
    }
    
    print(f"发送更新请求: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
    
    response = requests.put(
        f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/",
        json=update_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"更新响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ 成功：不包含 steps 字段的更新成功")
        updated_pipeline = response.json()
        print(f"更新后的描述: {updated_pipeline.get('description', 'N/A')}")
        return True
    else:
        print(f"❌ 失败：更新失败")
        print(f"错误响应: {response.text}")
        return False

def test_pipeline_update_with_empty_steps():
    """测试包含空 steps 字段的流水线更新"""
    
    # 获取流水线列表
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/")
    if response.status_code != 200:
        return False
    
    pipelines = response.json()
    if not pipelines:
        return False
    
    pipeline = pipelines[0]
    pipeline_id = pipeline['id']
    
    print("\n3. 测试包含空 steps 字段的更新...")
    update_data = {
        "name": pipeline['name'],
        "description": "测试更新 - 包含空 steps 字段",
        "project": pipeline['project'],
        "is_active": pipeline['is_active'],
        "steps": []  # 空的 steps 数组
    }
    
    print(f"发送更新请求: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
    
    response = requests.put(
        f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/",
        json=update_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"更新响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ 成功：包含空 steps 字段的更新成功")
        updated_pipeline = response.json()
        print(f"更新后的描述: {updated_pipeline.get('description', 'N/A')}")
        return True
    else:
        print(f"❌ 失败：更新失败")
        print(f"错误响应: {response.text}")
        return False

def test_pipeline_update_with_steps():
    """测试包含 steps 字段的流水线更新"""
    
    # 获取流水线列表
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/")
    if response.status_code != 200:
        return False
    
    pipelines = response.json()
    if not pipelines:
        return False
    
    pipeline = pipelines[0]
    pipeline_id = pipeline['id']
    
    print("\n4. 测试包含 steps 字段的更新...")
    update_data = {
        "name": pipeline['name'],
        "description": "测试更新 - 包含 steps 字段",
        "project": pipeline['project'],
        "is_active": pipeline['is_active'],
        "steps": [
            {
                "name": "测试步骤",
                "step_type": "build",
                "description": "测试构建步骤",
                "parameters": {"timeout": 300},
                "order": 1,
                "is_active": True
            }
        ]
    }
    
    print(f"发送更新请求: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
    
    response = requests.put(
        f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/",
        json=update_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"更新响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ 成功：包含 steps 字段的更新成功")
        updated_pipeline = response.json()
        print(f"更新后的描述: {updated_pipeline.get('description', 'N/A')}")
        steps = updated_pipeline.get('steps', [])
        print(f"更新后的步骤数量: {len(steps)}")
        return True
    else:
        print(f"❌ 失败：更新失败")
        print(f"错误响应: {response.text}")
        return False

if __name__ == "__main__":
    print("=== 流水线更新修复验证 ===\n")
    
    results = []
    results.append(test_pipeline_update_without_steps())
    results.append(test_pipeline_update_with_empty_steps())
    results.append(test_pipeline_update_with_steps())
    
    print(f"\n=== 测试结果总结 ===")
    print(f"成功: {sum(results)}/{len(results)}")
    print(f"失败: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 所有测试通过！流水线更新修复成功。")
    else:
        print("⚠️  部分测试失败，需要进一步调查。")
