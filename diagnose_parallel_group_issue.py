#!/usr/bin/env python3
"""
并行组管理问题诊断和修复脚本
"""

import requests
import json
from datetime import datetime
import sys

# 配置
BACKEND_URL = "http://localhost:8000"
API_BASE = f"{BACKEND_URL}/api/v1/pipelines"

# 测试用户认证
AUTH_HEADERS = {
    "Content-Type": "application/json"
}

def diagnose_parallel_group_issue():
    """诊断并行组管理问题"""
    
    print("🔍 AnsFlow 并行组管理问题诊断")
    print("=" * 50)
    
    # 1. 检查后端API可用性
    print("1️⃣ 检查后端API可用性...")
    try:
        response = requests.get(f"{API_BASE}/pipelines/", headers=AUTH_HEADERS, timeout=5)
        if response.status_code == 200:
            print("   ✅ 后端API可用")
        else:
            print(f"   ❌ 后端API返回错误状态码: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"   ❌ 后端API连接失败: {e}")
        return False
    
    # 2. 检查流水线数据
    print("2️⃣ 检查流水线数据...")
    try:
        pipelines = response.json()
        if not pipelines:
            print("   ❌ 没有找到任何流水线")
            return False
        
        print(f"   ✅ 找到 {len(pipelines)} 个流水线")
        
        # 选择第一个流水线进行详细检查
        pipeline = pipelines[0]
        pipeline_id = pipeline["id"]
        print(f"   📋 检查流水线: {pipeline['name']} (ID: {pipeline_id})")
        
        # 获取流水线详情
        detail_response = requests.get(f"{API_BASE}/pipelines/{pipeline_id}/", headers=AUTH_HEADERS)
        if detail_response.status_code != 200:
            print(f"   ❌ 获取流水线详情失败")
            return False
        
        pipeline_detail = detail_response.json()
        steps = pipeline_detail.get("steps", [])
        print(f"   📝 流水线包含 {len(steps)} 个步骤")
        
        # 检查步骤的parallel_group字段
        steps_with_groups = [step for step in steps if step.get("parallel_group")]
        print(f"   🔗 其中 {len(steps_with_groups)} 个步骤已分配到并行组")
        
        for step in steps_with_groups:
            print(f"     - 步骤 '{step['name']}' 属于并行组: {step['parallel_group']}")
        
    except requests.RequestException as e:
        print(f"   ❌ 获取流水线数据失败: {e}")
        return False
    
    # 3. 检查并行组数据
    print("3️⃣ 检查并行组数据...")
    try:
        groups_response = requests.get(f"{API_BASE}/parallel-groups/?pipeline={pipeline_id}", headers=AUTH_HEADERS)
        if groups_response.status_code != 200:
            print(f"   ❌ 获取并行组数据失败，状态码: {groups_response.status_code}")
            return False
        
        groups_data = groups_response.json()
        
        # 处理分页响应
        if isinstance(groups_data, dict) and "results" in groups_data:
            groups = groups_data["results"]
            print(f"   📊 使用分页格式，共 {len(groups)} 个并行组")
        elif isinstance(groups_data, list):
            groups = groups_data
            print(f"   📊 使用数组格式，共 {len(groups)} 个并行组")
        else:
            print(f"   ❌ 并行组数据格式异常: {type(groups_data)}")
            return False
        
        # 检查每个并行组的步骤配置
        for group in groups:
            group_id = group["id"]
            group_name = group["name"]
            group_steps = group.get("steps", [])
            
            print(f"   🔍 并行组 '{group_name}' (ID: {group_id})")
            print(f"     - 配置的步骤数量: {len(group_steps)}")
            
            if group_steps:
                # 验证步骤是否真实存在
                valid_steps = []
                for step_id in group_steps:
                    step = next((s for s in steps if s["id"] == step_id), None)
                    if step:
                        valid_steps.append(step)
                        print(f"     - 步骤 '{step['name']}' (ID: {step_id}) ✅")
                    else:
                        print(f"     - 步骤 ID {step_id} 不存在 ❌")
                
                print(f"     - 有效步骤: {len(valid_steps)}/{len(group_steps)}")
            else:
                print(f"     - ⚠️ 该并行组未配置任何步骤")
        
    except requests.RequestException as e:
        print(f"   ❌ 获取并行组数据失败: {e}")
        return False
    
    # 4. 数据一致性检查
    print("4️⃣ 数据一致性检查...")
    
    # 检查步骤的parallel_group字段与并行组的steps数组是否一致
    inconsistencies = []
    
    for group in groups:
        group_id = group["id"]
        group_steps = group.get("steps", [])
        
        # 检查组中配置的步骤是否都有对应的parallel_group字段
        for step_id in group_steps:
            step = next((s for s in steps if s["id"] == step_id), None)
            if step:
                if step.get("parallel_group") != group_id:
                    inconsistencies.append({
                        "type": "group_step_mismatch",
                        "group_id": group_id,
                        "step_id": step_id,
                        "step_name": step["name"],
                        "expected": group_id,
                        "actual": step.get("parallel_group")
                    })
    
    # 检查有parallel_group字段的步骤是否都在对应的并行组中
    for step in steps:
        step_group = step.get("parallel_group")
        if step_group:
            group = next((g for g in groups if g["id"] == step_group), None)
            if group:
                if step["id"] not in group.get("steps", []):
                    inconsistencies.append({
                        "type": "step_group_mismatch",
                        "step_id": step["id"],
                        "step_name": step["name"],
                        "group_id": step_group,
                        "issue": "step_not_in_group_steps"
                    })
            else:
                inconsistencies.append({
                    "type": "orphaned_step",
                    "step_id": step["id"],
                    "step_name": step["name"],
                    "group_id": step_group,
                    "issue": "group_not_found"
                })
    
    if inconsistencies:
        print(f"   ❌ 发现 {len(inconsistencies)} 个数据一致性问题:")
        for issue in inconsistencies:
            print(f"     - {issue}")
    else:
        print("   ✅ 数据一致性检查通过")
    
    # 5. 生成修复建议
    print("5️⃣ 修复建议:")
    
    if inconsistencies:
        print("   🔧 建议执行以下修复操作:")
        print("   1. 同步步骤的parallel_group字段")
        print("   2. 更新并行组的steps数组")
        print("   3. 清理孤立的并行组引用")
        
        # 提供修复选项
        if input("   是否立即执行自动修复? (y/N): ").lower() == 'y':
            return fix_parallel_group_issues(pipeline_id, steps, groups, inconsistencies)
    else:
        print("   ✅ 数据状态良好，无需修复")
    
    return True

def fix_parallel_group_issues(pipeline_id, steps, groups, inconsistencies):
    """自动修复并行组问题"""
    
    print("🔧 开始自动修复...")
    
    try:
        # 获取流水线详情
        detail_response = requests.get(f"{API_BASE}/pipelines/{pipeline_id}/", headers=AUTH_HEADERS)
        if detail_response.status_code != 200:
            print(f"   ❌ 获取流水线详情失败")
            return False
        
        pipeline_detail = detail_response.json()
        
        # 1. 以并行组的steps数组为准，更新步骤的parallel_group字段
        print("1️⃣ 同步步骤的parallel_group字段...")
        
        # 首先清除所有步骤的parallel_group字段
        for step in steps:
            step["parallel_group"] = None
        
        # 根据并行组的配置设置步骤的parallel_group
        for group in groups:
            group_id = group["id"]
            group_steps = group.get("steps", [])
            
            for step_id in group_steps:
                step = next((s for s in steps if s["id"] == step_id), None)
                if step:
                    step["parallel_group"] = group_id
        
        # 2. 更新流水线数据
        print("2️⃣ 更新流水线数据...")
        
        update_data = {
            "name": pipeline_detail["name"],
            "description": pipeline_detail.get("description", ""),
            "steps": steps
        }
        
        response = requests.put(
            f"{API_BASE}/pipelines/{pipeline_id}/",
            headers=AUTH_HEADERS,
            json=update_data
        )
        
        if response.status_code == 200:
            print("   ✅ 流水线数据更新成功")
        else:
            print(f"   ❌ 流水线数据更新失败，状态码: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
        
        print("🎉 修复完成！")
        return True
        
    except Exception as e:
        print(f"❌ 修复过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    
    print("AnsFlow 并行组管理问题诊断工具")
    print("=" * 50)
    
    success = diagnose_parallel_group_issue()
    
    if success:
        print("\n🎉 诊断完成")
    else:
        print("\n❌ 诊断过程中发生错误")
        sys.exit(1)

if __name__ == "__main__":
    main()
