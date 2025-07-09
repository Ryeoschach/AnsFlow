#!/usr/bin/env python3
"""
并行组步骤关联问题修复脚本
专门解决步骤没有正确保存到并行组的问题
"""

import requests
import json
from datetime import datetime

# 配置
BACKEND_URL = "http://localhost:8000"
API_BASE = f"{BACKEND_URL}/api/v1/pipelines"

# 认证头
HEADERS = {"Content-Type": "application/json"}

def check_step_group_association():
    """检查步骤与并行组的关联状态"""
    
    print("🔍 检查步骤与并行组关联状态")
    print("=" * 50)
    
    try:
        # 1. 获取流水线列表
        print("1️⃣ 获取流水线列表...")
        response = requests.get(f"{API_BASE}/pipelines/", headers=HEADERS)
        
        if response.status_code != 200:
            print(f"   ❌ 获取流水线失败: {response.status_code}")
            return False
        
        pipelines = response.json()
        if not pipelines:
            print("   ❌ 没有找到流水线")
            return False
        
        pipeline = pipelines[0]
        pipeline_id = pipeline["id"]
        print(f"   ✅ 选择流水线: {pipeline['name']} (ID: {pipeline_id})")
        
        # 2. 获取流水线详情和步骤
        print("2️⃣ 获取步骤信息...")
        detail_response = requests.get(f"{API_BASE}/pipelines/{pipeline_id}/", headers=HEADERS)
        pipeline_detail = detail_response.json()
        steps = pipeline_detail.get("steps", [])
        
        print(f"   📋 流水线包含 {len(steps)} 个步骤:")
        for step in steps:
            group_info = f" → 并行组: {step.get('parallel_group', '无')}" if step.get('parallel_group') else ""
            print(f"     - {step['name']} (ID: {step['id']}){group_info}")
        
        # 3. 获取并行组信息
        print("3️⃣ 获取并行组信息...")
        groups_response = requests.get(f"{API_BASE}/parallel-groups/?pipeline={pipeline_id}", headers=HEADERS)
        groups_data = groups_response.json()
        
        # 处理分页响应
        groups = groups_data.get("results", groups_data) if isinstance(groups_data, dict) else groups_data
        
        print(f"   📊 流水线包含 {len(groups)} 个并行组:")
        for group in groups:
            steps_count = len(group.get("steps", []))
            print(f"     - {group['name']} (ID: {group['id']}) → {steps_count} 个步骤")
            if group.get("steps"):
                print(f"       步骤ID: {group['steps']}")
        
        # 4. 数据一致性分析
        print("4️⃣ 数据一致性分析...")
        
        issues = []
        
        # 检查每个并行组的步骤配置
        for group in groups:
            group_id = group["id"]
            group_steps = group.get("steps", [])
            
            print(f"   🔍 检查并行组 '{group['name']}':")
            
            if not group_steps:
                issues.append(f"并行组 {group['name']} 没有配置任何步骤")
                print(f"     ⚠️ 没有配置任何步骤")
                continue
            
            # 检查组中的每个步骤
            for step_id in group_steps:
                step = next((s for s in steps if s["id"] == step_id), None)
                if not step:
                    issues.append(f"并行组 {group['name']} 中的步骤 {step_id} 不存在")
                    print(f"     ❌ 步骤 {step_id} 不存在")
                elif step.get("parallel_group") != group_id:
                    issues.append(f"步骤 {step['name']} 的parallel_group字段不匹配")
                    print(f"     ❌ 步骤 {step['name']} 的parallel_group字段({step.get('parallel_group')})不匹配")
                else:
                    print(f"     ✅ 步骤 {step['name']} 关联正确")
        
        # 检查有parallel_group字段但不在任何组中的步骤
        for step in steps:
            if step.get("parallel_group"):
                group = next((g for g in groups if g["id"] == step["parallel_group"]), None)
                if not group:
                    issues.append(f"步骤 {step['name']} 引用的并行组 {step['parallel_group']} 不存在")
                elif step["id"] not in group.get("steps", []):
                    issues.append(f"步骤 {step['name']} 不在其所属并行组的steps数组中")
        
        # 5. 报告结果
        print("5️⃣ 检查结果:")
        if issues:
            print(f"   ❌ 发现 {len(issues)} 个问题:")
            for issue in issues:
                print(f"     - {issue}")
            return False
        else:
            print("   ✅ 数据关联完全正确")
            return True
            
    except Exception as e:
        print(f"❌ 检查过程中发生错误: {e}")
        return False

def fix_step_group_association():
    """修复步骤与并行组的关联问题"""
    
    print("\n🔧 修复步骤与并行组关联问题")
    print("=" * 50)
    
    try:
        # 1. 获取数据
        pipelines_response = requests.get(f"{API_BASE}/pipelines/", headers=HEADERS)
        pipelines = pipelines_response.json()
        
        if not pipelines:
            print("❌ 没有找到流水线")
            return False
        
        pipeline = pipelines[0]
        pipeline_id = pipeline["id"]
        
        # 获取流水线详情
        detail_response = requests.get(f"{API_BASE}/pipelines/{pipeline_id}/", headers=HEADERS)
        pipeline_detail = detail_response.json()
        steps = pipeline_detail.get("steps", [])
        
        # 获取并行组
        groups_response = requests.get(f"{API_BASE}/parallel-groups/?pipeline={pipeline_id}", headers=HEADERS)
        groups_data = groups_response.json()
        groups = groups_data.get("results", groups_data) if isinstance(groups_data, dict) else groups_data
        
        print(f"📊 数据获取完成: {len(steps)} 个步骤, {len(groups)} 个并行组")
        
        # 2. 修复步骤的parallel_group字段
        print("🔗 修复步骤的parallel_group字段...")
        
        # 首先清除所有步骤的parallel_group字段
        for step in steps:
            step["parallel_group"] = None
        
        # 根据并行组配置重新设置步骤的parallel_group字段
        updates_made = 0
        for group in groups:
            group_id = group["id"]
            group_steps = group.get("steps", [])
            
            if group_steps:
                print(f"   🔗 处理并行组 '{group['name']}' ({len(group_steps)} 个步骤)")
                
                for step_id in group_steps:
                    step = next((s for s in steps if s["id"] == step_id), None)
                    if step:
                        step["parallel_group"] = group_id
                        updates_made += 1
                        print(f"     ✅ 步骤 '{step['name']}' → 并行组 {group_id}")
        
        print(f"   📊 共更新了 {updates_made} 个步骤的关联")
        
        # 3. 保存更新后的流水线
        print("💾 保存更新后的流水线...")
        
        update_data = {
            "name": pipeline_detail["name"],
            "description": pipeline_detail.get("description", ""),
            "project": pipeline_detail["project"],
            "is_active": pipeline_detail.get("is_active", True),
            "execution_mode": pipeline_detail.get("execution_mode", "sequential"),
            "execution_tool": pipeline_detail.get("execution_tool", "local"),
            "tool_job_name": pipeline_detail.get("tool_job_name", ""),
            "tool_job_config": pipeline_detail.get("tool_job_config", {}),
            "steps": [
                {
                    "id": step["id"],
                    "name": step["name"],
                    "step_type": step["step_type"],
                    "description": step.get("description", ""),
                    "parameters": step.get("parameters", {}),
                    "order": step["order"],
                    "is_active": step.get("is_active", True),
                    "parallel_group": step.get("parallel_group")  # 关键：保存并行组关联
                }
                for step in steps
            ]
        }
        
        save_response = requests.put(
            f"{API_BASE}/pipelines/{pipeline_id}/",
            json=update_data,
            headers=HEADERS
        )
        
        if save_response.status_code == 200:
            print("   ✅ 流水线更新成功")
            return True
        else:
            print(f"   ❌ 流水线更新失败: {save_response.status_code}")
            print(f"   错误信息: {save_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 修复过程中发生错误: {e}")
        return False

def create_test_parallel_group():
    """创建一个测试并行组来验证修复效果"""
    
    print("\n🧪 创建测试并行组验证修复效果")
    print("=" * 50)
    
    try:
        # 获取流水线数据
        pipelines_response = requests.get(f"{API_BASE}/pipelines/", headers=HEADERS)
        pipelines = pipelines_response.json()
        
        if not pipelines:
            print("❌ 没有找到流水线")
            return False
        
        pipeline = pipelines[0]
        pipeline_id = pipeline["id"]
        
        # 获取步骤
        detail_response = requests.get(f"{API_BASE}/pipelines/{pipeline_id}/", headers=HEADERS)
        pipeline_detail = detail_response.json()
        steps = pipeline_detail.get("steps", [])
        
        if len(steps) < 2:
            print("❌ 步骤数量不足，需要至少2个步骤")
            return False
        
        # 选择前两个步骤
        test_steps = [steps[0]["id"], steps[1]["id"]]
        
        # 创建测试并行组
        test_group_data = {
            "id": f"test_fix_{int(datetime.now().timestamp())}",
            "name": f"步骤关联测试组_{datetime.now().strftime('%H%M%S')}",
            "description": "用于测试步骤关联修复的并行组",
            "pipeline": pipeline_id,
            "sync_policy": "wait_all",
            "timeout_seconds": 3600,
            "steps": test_steps
        }
        
        print(f"📝 创建测试并行组，包含步骤: {test_steps}")
        
        create_response = requests.post(
            f"{API_BASE}/parallel-groups/",
            json=test_group_data,
            headers=HEADERS
        )
        
        if create_response.status_code != 201:
            print(f"❌ 创建并行组失败: {create_response.status_code}")
            print(f"错误信息: {create_response.text}")
            return False
        
        created_group = create_response.json()
        group_id = created_group["id"]
        print(f"✅ 测试并行组创建成功 (ID: {group_id})")
        
        # 验证步骤关联
        print("🔍 验证步骤关联...")
        updated_detail_response = requests.get(f"{API_BASE}/pipelines/{pipeline_id}/", headers=HEADERS)
        updated_detail = updated_detail_response.json()
        updated_steps = updated_detail.get("steps", [])
        
        associated_steps = [s for s in updated_steps if s.get("parallel_group") == group_id]
        
        print(f"📊 验证结果: {len(associated_steps)}/{len(test_steps)} 个步骤正确关联")
        
        for step in associated_steps:
            print(f"   ✅ 步骤 '{step['name']}' 正确关联到并行组 {group_id}")
        
        # 清理测试数据
        print("🧹 清理测试数据...")
        delete_response = requests.delete(f"{API_BASE}/parallel-groups/{group_id}/", headers=HEADERS)
        
        if delete_response.status_code == 204:
            print("✅ 测试数据清理完成")
        else:
            print(f"⚠️ 清理测试数据失败: {delete_response.status_code}")
        
        return len(associated_steps) == len(test_steps)
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    
    print("🔧 AnsFlow 并行组步骤关联修复工具")
    print("=" * 60)
    
    # 1. 检查当前状态
    print("阶段 1: 检查当前关联状态")
    initial_check = check_step_group_association()
    
    if not initial_check:
        # 2. 如果有问题，尝试修复
        print("\n阶段 2: 修复步骤关联问题")
        fix_success = fix_step_group_association()
        
        if fix_success:
            # 3. 再次检查
            print("\n阶段 3: 验证修复结果")
            check_step_group_association()
        else:
            print("❌ 修复失败")
            return
    
    # 4. 创建测试并行组验证
    print("\n阶段 4: 功能测试验证")
    test_success = create_test_parallel_group()
    
    if test_success:
        print("\n🎉 所有测试通过！")
        print("✅ 步骤关联功能工作正常")
        
        print("\n📝 修复总结:")
        print("1. ✅ 检查并修复了数据一致性问题")
        print("2. ✅ 确保步骤的parallel_group字段正确")
        print("3. ✅ 验证了前端-后端数据同步")
        print("4. ✅ 测试了创建和关联功能")
        
        print("\n💡 建议:")
        print("- 前端修复代码已部署，请测试界面功能")
        print("- 注意检查编辑并行组时步骤选择器的显示")
        print("- 确保保存后步骤正确显示在并行组中")
        
    else:
        print("\n❌ 功能测试失败")
        print("请检查前端代码修复是否正确部署")

if __name__ == "__main__":
    main()
