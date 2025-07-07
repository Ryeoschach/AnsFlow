#!/usr/bin/env python3
"""
简单的HTTP API测试：验证预览模式和实际模式的内容一致性
"""
import json
import requests

print("🧪 流水线预览API测试工具")
print("=" * 60)
print("目标: 验证预览模式和实际模式显示的内容是否一致")
print("=" * 60)

# 配置
BASE_URL = "http://localhost:8000"
PIPELINE_ID = 12  # Integration Test Pipeline的ID
CICD_TOOL_ID = 1  # 假设的CICD工具ID，可能需要调整

API_URL = f"{BASE_URL}/api/v1/cicd/pipelines/preview/"

print(f"🔗 测试API: {API_URL}")

# 准备测试用的前端步骤数据（模拟前端编辑器的内容）
frontend_steps = [
    {
        "id": "step1",
        "name": "代码拉取",
        "step_type": "fetch_code",
        "order": 1,
        "parameters": {
            "repository_url": "https://github.com/example/repo",
            "branch": "main"
        }
    },
    {
        "id": "step2", 
        "name": "Build Step",
        "step_type": "build",
        "order": 2,
        "parameters": {
            "build_command": "npm install && npm run build"
        }
    },
    {
        "id": "step3",
        "name": "Ansible自动化部署",
        "step_type": "ansible",
        "order": 3,
        "parameters": {
            "playbook_path": "deploy.yml",
            "inventory_path": "production.ini",
            "extra_vars": {
                "app_version": "2.1.0",
                "environment": "production",
                "deploy_user": "deploy"
            },
            "vault_password_file": "/etc/ansible/vault_pass",
            "check_mode": False,
            "become": True
        }
    }
]

def test_preview_mode(mode, steps_data=None):
    """测试指定模式的预览API"""
    print(f"\n🎯 测试模式: {mode}")
    print("-" * 30)
    
    payload = {
        "pipeline_id": PIPELINE_ID,
        "cicd_tool_id": CICD_TOOL_ID,
        "preview_mode": mode == "preview"  # 转换为布尔值
    }
    
    if mode == "preview" and steps_data:
        payload["steps"] = steps_data
    
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        print(f"📡 HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API调用成功")
            
            # 检查workflow_summary
            workflow_summary = data.get('workflow_summary', {})
            print(f"� 数据来源: {workflow_summary.get('data_source', '未知')}")
            print(f"📝 预览模式: {workflow_summary.get('preview_mode', '未知')}")
            
            total_steps = workflow_summary.get('total_steps', 0)
            step_types = workflow_summary.get('step_types', [])
            print(f"📋 步骤数量: {total_steps}")
            print(f"📋 步骤类型: {step_types}")
            
            # 检查是否包含ansible步骤
            if 'ansible' in step_types:
                print("✅ 包含ansible步骤类型")
            else:
                print("❌ 未找到ansible步骤类型")
                
            # 显示其他信息
            if 'estimated_duration' in workflow_summary:
                print(f"⏱️  预估时长: {workflow_summary['estimated_duration']}")
            
            return data
        else:
            print(f"❌ API调用失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📝 错误信息: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"📝 错误内容: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        return None

# 首先尝试获取所有CICD工具以找到正确的ID
print("\n🔍 获取CICD工具列表")
print("-" * 30)
try:
    tools_response = requests.get(f"{BASE_URL}/api/v1/cicd/tools/", timeout=10)
    if tools_response.status_code == 200:
        tools = tools_response.json()
        print(f"✅ 找到 {len(tools)} 个CICD工具:")
        for tool in tools:
            print(f"   - {tool['name']} (ID: {tool['id']}, 类型: {tool['tool_type']})")
        if tools:
            CICD_TOOL_ID = tools[0]['id']  # 使用第一个工具
            print(f"🎯 使用CICD工具ID: {CICD_TOOL_ID}")
    else:
        print(f"❌ 获取CICD工具失败: {tools_response.status_code}")
except Exception as e:
    print(f"❌ 获取CICD工具时出错: {e}")

# 测试实际模式（使用数据库数据）
print("\n" + "="*50)
print("🏃 测试实际模式（数据库数据）")
actual_result = test_preview_mode("actual")

# 测试预览模式（使用前端步骤数据）
print("\n" + "="*50)
print("🏃 测试预览模式（前端编辑器数据）")
preview_result = test_preview_mode("preview", frontend_steps)

# 比较结果
print("\n" + "="*50)
print("🔍 结果比较")
print("="*50)

if actual_result and preview_result:
    actual_summary = actual_result.get('workflow_summary', {})
    preview_summary = preview_result.get('workflow_summary', {})
    
    actual_steps = actual_summary.get('total_steps', 0)
    preview_steps = preview_summary.get('total_steps', 0)
    
    actual_types = actual_summary.get('step_types', [])
    preview_types = preview_summary.get('step_types', [])
    
    actual_ansible = 'ansible' in actual_types
    preview_ansible = 'ansible' in preview_types
    
    print(f"📊 实际模式: {actual_steps} 个步骤，{'包含' if actual_ansible else '不包含'}ansible步骤")
    print(f"📊 预览模式: {preview_steps} 个步骤，{'包含' if preview_ansible else '不包含'}ansible步骤")
    print(f"📊 实际模式数据来源: {actual_summary.get('data_source', '未知')}")
    print(f"📊 预览模式数据来源: {preview_summary.get('data_source', '未知')}")
    
    if actual_ansible and preview_ansible:
        print("🎉 成功！两种模式都包含ansible步骤")
        print("✅ 预览与实际内容一致性问题已解决")
    elif actual_ansible:
        print("⚠️  实际模式有ansible步骤，但预览模式没有")
        print("💡 这可能是正常的，如果前端编辑器没有ansible步骤")
    elif preview_ansible:
        print("⚠️  预览模式有ansible步骤，但实际模式没有")
        print("❌ 这是之前的问题：数据库缺少ansible步骤")
    else:
        print("❌ 两种模式都没有ansible步骤")
        
    # 检查具体步骤类型对比
    if actual_types:
        print(f"\n🔍 实际模式的步骤类型: {actual_types}")
    if preview_types:
        print(f"� 预览模式的步骤类型: {preview_types}")
                
else:
    print("❌ 无法比较结果，API调用失败")

print("\n💡 接下来的步骤:")
print("1. 如果实际模式现在包含ansible步骤，问题已解决")
print("2. 在前端预览页面测试两种模式切换")
print("3. 验证执行流水线功能是否正常")
print("4. 确保所有流水线的步骤都正确保存到数据库")
