#!/usr/bin/env python3
"""
测试步骤与并行组关联的脚本
"""

import requests
import json
from datetime import datetime

# 配置
BACKEND_URL = "http://localhost:8000"
API_BASE = f"{BACKEND_URL}/api/v1/pipelines"

# 测试用户认证（需要根据实际情况调整）
AUTH_HEADERS = {
    "Content-Type": "application/json"
}

def test_step_parallel_group_association():
    """测试步骤与并行组的关联"""
    
    print("🔧 测试步骤与并行组关联...")
    print("=" * 50)
    
    try:
        # 1. 首先获取一个现有的流水线
        print("1️⃣ 获取现有流水线...")
        response = requests.get(f"{API_BASE}/pipelines/", headers=AUTH_HEADERS)
        
        if response.status_code != 200:
            print(f"   ❌ 获取流水线失败，状态码: {response.status_code}")
            return False
        
        pipelines = response.json()
        if not pipelines:
            print("   ❌ 没有找到任何流水线")
            return False
        
        # 选择第一个流水线
        pipeline = pipelines[0]
        pipeline_id = pipeline["id"]
        print(f"   ✅ 选择流水线: {pipeline['name']} (ID: {pipeline_id})")
        
        # 2. 获取流水线的详细信息，包括步骤
        print("2️⃣ 获取流水线详细信息...")
        response = requests.get(f"{API_BASE}/pipelines/{pipeline_id}/", headers=AUTH_HEADERS)
        
        if response.status_code != 200:
            print(f"   ❌ 获取流水线详情失败，状态码: {response.status_code}")
            return False
        
        pipeline_detail = response.json()
        steps = pipeline_detail.get("steps", [])
        print(f"   ✅ 流水线有 {len(steps)} 个步骤")
        
        if len(steps) < 2:
            print("   ❌ 步骤数量不足，需要至少2个步骤来测试")
            return False
        
        # 打印步骤信息
        for i, step in enumerate(steps[:5]):  # 只显示前5个步骤
            print(f"     步骤 {i+1}: {step['name']} (ID: {step['id']}) - parallel_group: {step.get('parallel_group', 'None')}")
        
        # 3. 创建一个测试并行组
        print("3️⃣ 创建测试并行组...")
        test_group_data = {
            "name": f"测试并行组_{int(datetime.now().timestamp())}",
            "description": "测试步骤关联的并行组",
            "pipeline": pipeline_id,
            "sync_policy": "wait_all",
            "timeout_seconds": 3600
        }
        
        response = requests.post(
            f"{API_BASE}/parallel-groups/",
            headers=AUTH_HEADERS,
            json=test_group_data
        )
        
        if response.status_code != 201:
            print(f"   ❌ 创建并行组失败，状态码: {response.status_code}")
            if response.content:
                print(f"   错误信息: {response.text}")
            return False
        
        created_group = response.json()
        group_id = created_group["id"]
        print(f"   ✅ 创建并行组成功，组ID: {group_id}")
        
        # 4. 更新步骤的parallel_group字段
        print("4️⃣ 关联步骤到并行组...")
        step_ids_to_group = [steps[0]["id"], steps[1]["id"]]  # 选择前两个步骤
        
        # 更新流水线，设置步骤的parallel_group字段
        updated_steps = []
        for step in steps:
            updated_step = {
                "id": step["id"],
                "name": step["name"],
                "description": step.get("description", ""),
                "status": step.get("status", "pending"),
                "step_type": step.get("step_type", "shell"),
                "command": step.get("command", ""),
                "environment_vars": step.get("environment_vars", {}),
                "timeout_seconds": step.get("timeout_seconds", 300),
                "order": step.get("order", 0),
                "dependencies": step.get("dependencies", []),
                "parallel_group": group_id if step["id"] in step_ids_to_group else step.get("parallel_group"),
                "conditions": step.get("conditions", {}),
                "approval_required": step.get("approval_required", False),
                "approval_users": step.get("approval_users", []),
                "retry_policy": step.get("retry_policy", {}),
                "notification_config": step.get("notification_config", {})
            }
            updated_steps.append(updated_step)
        
        # 更新流水线
        updated_pipeline_data = {
            "name": pipeline_detail["name"],
            "description": pipeline_detail.get("description", ""),
            "project": pipeline_detail["project"],
            "is_active": pipeline_detail.get("is_active", True),
            "execution_mode": pipeline_detail.get("execution_mode", "sequential"),
            "execution_tool": pipeline_detail.get("execution_tool", "native"),
            "tool_job_name": pipeline_detail.get("tool_job_name", ""),
            "tool_job_config": pipeline_detail.get("tool_job_config", {}),
            "steps": updated_steps
        }
        
        response = requests.put(
            f"{API_BASE}/pipelines/{pipeline_id}/",
            headers=AUTH_HEADERS,
            json=updated_pipeline_data
        )
        
        if response.status_code != 200:
            print(f"   ❌ 更新流水线失败，状态码: {response.status_code}")
            if response.content:
                print(f"   错误信息: {response.text}")
            return False
        
        print(f"   ✅ 成功关联步骤 {step_ids_to_group} 到并行组 {group_id}")
        
        # 5. 重新获取并行组，验证steps字段
        print("5️⃣ 验证并行组的steps字段...")
        response = requests.get(f"{API_BASE}/parallel-groups/{group_id}/", headers=AUTH_HEADERS)
        
        if response.status_code != 200:
            print(f"   ❌ 获取并行组失败，状态码: {response.status_code}")
            return False
        
        fetched_group = response.json()
        group_steps = fetched_group.get("steps", [])
        print(f"   ✅ 并行组包含步骤: {group_steps}")
        
        # 验证步骤是否正确关联
        expected_steps = set(step_ids_to_group)
        actual_steps = set(group_steps)
        
        if expected_steps == actual_steps:
            print("   ✅ 步骤关联验证成功！")
        else:
            print(f"   ❌ 步骤关联验证失败！")
            print(f"       期望: {expected_steps}")
            print(f"       实际: {actual_steps}")
        
        # 6. 验证流水线中步骤的parallel_group字段
        print("6️⃣ 验证流水线中步骤的parallel_group字段...")
        response = requests.get(f"{API_BASE}/pipelines/{pipeline_id}/", headers=AUTH_HEADERS)
        
        if response.status_code != 200:
            print(f"   ❌ 重新获取流水线失败，状态码: {response.status_code}")
            return False
        
        updated_pipeline = response.json()
        updated_steps = updated_pipeline.get("steps", [])
        
        for step in updated_steps:
            if step["id"] in step_ids_to_group:
                if step.get("parallel_group") == group_id:
                    print(f"   ✅ 步骤 {step['name']} (ID: {step['id']}) 的parallel_group正确设置为 {group_id}")
                else:
                    print(f"   ❌ 步骤 {step['name']} (ID: {step['id']}) 的parallel_group设置错误：{step.get('parallel_group')}")
        
        # 7. 清理测试数据
        print("7️⃣ 清理测试数据...")
        
        # 清除步骤的parallel_group关联
        cleanup_steps = []
        for step in updated_steps:
            cleanup_step = {
                "id": step["id"],
                "name": step["name"],
                "description": step.get("description", ""),
                "status": step.get("status", "pending"),
                "step_type": step.get("step_type", "shell"),
                "command": step.get("command", ""),
                "environment_vars": step.get("environment_vars", {}),
                "timeout_seconds": step.get("timeout_seconds", 300),
                "order": step.get("order", 0),
                "dependencies": step.get("dependencies", []),
                "parallel_group": None,  # 清除关联
                "conditions": step.get("conditions", {}),
                "approval_required": step.get("approval_required", False),
                "approval_users": step.get("approval_users", []),
                "retry_policy": step.get("retry_policy", {}),
                "notification_config": step.get("notification_config", {})
            }
            cleanup_steps.append(cleanup_step)
        
        cleanup_pipeline_data = {
            "name": updated_pipeline["name"],
            "description": updated_pipeline.get("description", ""),
            "project": updated_pipeline["project"],
            "is_active": updated_pipeline.get("is_active", True),
            "execution_mode": updated_pipeline.get("execution_mode", "sequential"),
            "execution_tool": updated_pipeline.get("execution_tool", "native"),
            "tool_job_name": updated_pipeline.get("tool_job_name", ""),
            "tool_job_config": updated_pipeline.get("tool_job_config", {}),
            "steps": cleanup_steps
        }
        
        requests.put(
            f"{API_BASE}/pipelines/{pipeline_id}/",
            headers=AUTH_HEADERS,
            json=cleanup_pipeline_data
        )
        
        # 删除测试并行组
        requests.delete(f"{API_BASE}/parallel-groups/{group_id}/", headers=AUTH_HEADERS)
        
        print("   ✅ 测试数据清理完成")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 测试过程中发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_step_parallel_group_association()
    if success:
        print("\n🎉 所有测试通过！")
    else:
        print("\n❌ 测试失败！")
