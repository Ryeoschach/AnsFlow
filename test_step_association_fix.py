#!/usr/bin/env python3
"""
快速测试并行组步骤关联修复
"""

import requests
import json
from datetime import datetime

# 配置
BACKEND_URL = "http://localhost:8000"
API_BASE = f"{BACKEND_URL}/api/v1/pipelines"
HEADERS = {"Content-Type": "application/json"}

def test_step_association_fix():
    """测试步骤关联修复"""
    
    print("🧪 测试步骤关联修复")
    print("=" * 50)
    
    try:
        # 1. 获取流水线
        pipelines_response = requests.get(f"{API_BASE}/pipelines/", headers=HEADERS)
        pipelines = pipelines_response.json()
        
        if not pipelines:
            print("❌ 没有找到流水线")
            return False
        
        pipeline = pipelines[0]
        pipeline_id = pipeline["id"]
        print(f"📋 使用流水线: {pipeline['name']} (ID: {pipeline_id})")
        
        # 2. 获取当前步骤
        detail_response = requests.get(f"{API_BASE}/pipelines/{pipeline_id}/", headers=HEADERS)
        pipeline_detail = detail_response.json()
        steps = pipeline_detail.get("steps", [])
        
        print(f"📝 当前步骤: {len(steps)} 个")
        for step in steps:
            group_info = f" → 并行组: {step.get('parallel_group')}" if step.get('parallel_group') else ""
            print(f"  - {step['name']} (ID: {step['id']}){group_info}")
        
        if len(steps) < 2:
            print("❌ 需要至少2个步骤进行测试")
            return False
        
        # 3. 创建测试并行组
        test_group_id = f"test_fix_{int(datetime.now().timestamp())}"
        test_steps = [steps[0]["id"], steps[1]["id"]]
        
        group_data = {
            "id": test_group_id,
            "name": "步骤关联测试组",
            "description": "测试步骤关联修复",
            "pipeline": pipeline_id,
            "sync_policy": "wait_all",
            "timeout_seconds": 3600,
            "steps": test_steps
        }
        
        print(f"🆕 创建测试并行组，包含步骤: {test_steps}")
        create_response = requests.post(f"{API_BASE}/parallel-groups/", json=group_data, headers=HEADERS)
        
        if create_response.status_code != 201:
            print(f"❌ 创建并行组失败: {create_response.status_code}")
            print(f"错误信息: {create_response.text}")
            return False
        
        print("✅ 并行组创建成功")
        
        # 4. 模拟前端保存流程 - 更新流水线包含步骤关联
        print("💾 模拟前端保存流程...")
        
        # 更新步骤的parallel_group字段
        updated_steps = []
        for step in steps:
            updated_step = {
                "id": step["id"],
                "name": step["name"],
                "step_type": step["step_type"],
                "description": step.get("description", ""),
                "parameters": step.get("parameters", {}),
                "order": step["order"],
                "is_active": True,
                "parallel_group": test_group_id if step["id"] in test_steps else None
            }
            updated_steps.append(updated_step)
        
        # 保存流水线
        update_data = {
            "name": pipeline_detail["name"],
            "description": pipeline_detail.get("description", ""),
            "project": pipeline_detail["project"],
            "is_active": pipeline_detail.get("is_active", True),
            "execution_mode": pipeline_detail.get("execution_mode", "sequential"),
            "execution_tool": pipeline_detail.get("execution_tool"),
            "tool_job_name": pipeline_detail.get("tool_job_name", ""),
            "tool_job_config": pipeline_detail.get("tool_job_config", {}),
            "steps": updated_steps
        }
        
        print(f"📤 准备保存的步骤关联:")
        for step in updated_steps:
            if step.get("parallel_group"):
                print(f"  ✅ 步骤 {step['name']} → 并行组 {step['parallel_group']}")
        
        save_response = requests.put(f"{API_BASE}/pipelines/{pipeline_id}/", json=update_data, headers=HEADERS)
        
        if save_response.status_code != 200:
            print(f"❌ 保存流水线失败: {save_response.status_code}")
            print(f"错误信息: {save_response.text}")
            return False
        
        print("✅ 流水线保存成功")
        
        # 5. 验证保存结果
        print("🔍 验证保存结果...")
        
        verify_response = requests.get(f"{API_BASE}/pipelines/{pipeline_id}/", headers=HEADERS)
        verify_detail = verify_response.json()
        verify_steps = verify_detail.get("steps", [])
        
        success_count = 0
        for step in verify_steps:
            if step["id"] in test_steps:
                if step.get("parallel_group") == test_group_id:
                    print(f"  ✅ 步骤 {step['name']} 关联正确: {step['parallel_group']}")
                    success_count += 1
                else:
                    print(f"  ❌ 步骤 {step['name']} 关联失败: {step.get('parallel_group')}")
            else:
                if not step.get("parallel_group"):
                    print(f"  ✅ 步骤 {step['name']} 正确无关联")
                else:
                    print(f"  ⚠️ 步骤 {step['name']} 意外关联: {step.get('parallel_group')}")
        
        # 6. 清理测试数据
        print("🧹 清理测试数据...")
        delete_response = requests.delete(f"{API_BASE}/parallel-groups/{test_group_id}/", headers=HEADERS)
        
        if delete_response.status_code == 204:
            print("✅ 测试数据清理完成")
        else:
            print(f"⚠️ 清理失败: {delete_response.status_code}")
        
        # 7. 总结结果
        print("\n📊 测试结果:")
        if success_count == len(test_steps):
            print(f"✅ 所有 {success_count} 个步骤关联正确")
            print("🎉 步骤关联修复成功！")
            return True
        else:
            print(f"❌ 只有 {success_count}/{len(test_steps)} 个步骤关联正确")
            print("💡 需要进一步检查后端代码")
            return False
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    
    print("🔧 AnsFlow 步骤关联修复验证工具")
    print("=" * 60)
    
    success = test_step_association_fix()
    
    if success:
        print("\n✅ 修复验证成功")
        print("💡 现在可以在前端测试并行组管理功能")
    else:
        print("\n❌ 修复验证失败")
        print("💡 请检查后端序列化器代码修复")

if __name__ == "__main__":
    main()
