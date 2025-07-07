#!/usr/bin/env python3
"""
测试流水线预览API的预览模式和实际模式
验证Integration Test Pipeline的ansible步骤是否在两种模式下都正确显示
"""
import os
import sys
import json
import requests
from requests.auth import HTTPBasicAuth

# Django设置
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_service.settings')

import django
django.setup()

from cicd_integrations.models import Pipeline, CICDTool

print("🧪 流水线预览API测试工具")
print("=" * 60)
print("目标: 验证预览模式和实际模式显示的内容是否一致")
print("=" * 60)

# 查找Integration Test Pipeline
try:
    pipeline = Pipeline.objects.get(name="Integration Test Pipeline")
    print(f"✅ 找到流水线: {pipeline.name} (ID: {pipeline.id})")
    
    # 获取关联的CICD工具
    cicd_tool = pipeline.cicd_tool
    print(f"📋 CICD工具: {cicd_tool.name} ({cicd_tool.tool_type})")
    
except Pipeline.DoesNotExist:
    print("❌ 未找到Integration Test Pipeline")
    sys.exit(1)

# 测试API的基础URL
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/pipelines/{pipeline.id}/preview/"

print(f"\n🔗 测试API: {API_URL}")

# 准备测试用的前端步骤数据（模拟前端编辑器的内容）
frontend_steps = [
    {
        "id": "step1",
        "name": "代码拉取",
        "type": "fetch_code",
        "order": 1,
        "parameters": {
            "repository_url": "https://github.com/example/repo",
            "branch": "main"
        }
    },
    {
        "id": "step2", 
        "name": "Build Step",
        "type": "build",
        "order": 2,
        "parameters": {
            "build_command": "npm install && npm run build"
        }
    },
    {
        "id": "step3",
        "name": "Ansible自动化部署",
        "type": "ansible",
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
        "cicd_tool_id": cicd_tool.id,
        "preview_mode": mode
    }
    
    if mode == "preview" and steps_data:
        payload["steps"] = steps_data
    
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        print(f"📡 HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API调用成功")
            print(f"📝 数据来源: {data.get('data_source', '未知')}")
            
            steps = data.get('steps', [])
            print(f"📋 步骤数量: {len(steps)}")
            
            # 检查是否包含ansible步骤
            ansible_steps = [s for s in steps if s.get('type') == 'ansible']
            if ansible_steps:
                print(f"✅ 包含 {len(ansible_steps)} 个ansible步骤:")
                for i, step in enumerate(ansible_steps, 1):
                    print(f"   {i}. {step.get('name', '未命名')} (order: {step.get('order', 'N/A')})")
                    params = step.get('parameters', {})
                    if 'playbook_path' in params:
                        print(f"      📝 Playbook: {params['playbook_path']}")
            else:
                print("❌ 未找到ansible步骤")
            
            return data
        else:
            print(f"❌ API调用失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📝 错误信息: {error_data}")
            except:
                print(f"📝 错误内容: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        return None

# 测试实际模式（使用数据库数据）
print("\n" + "="*50)
actual_result = test_preview_mode("actual")

# 测试预览模式（使用前端步骤数据）
print("\n" + "="*50)
preview_result = test_preview_mode("preview", frontend_steps)

# 比较结果
print("\n" + "="*50)
print("🔍 结果比较")
print("="*50)

if actual_result and preview_result:
    actual_steps = actual_result.get('steps', [])
    preview_steps = preview_result.get('steps', [])
    
    actual_ansible = [s for s in actual_steps if s.get('type') == 'ansible']
    preview_ansible = [s for s in preview_steps if s.get('type') == 'ansible']
    
    print(f"📊 实际模式: {len(actual_ansible)} 个ansible步骤")
    print(f"📊 预览模式: {len(preview_ansible)} 个ansible步骤")
    
    if len(actual_ansible) > 0 and len(preview_ansible) > 0:
        print("🎉 成功！两种模式都包含ansible步骤")
        print("✅ 预览与实际内容一致性问题已解决")
    elif len(actual_ansible) > 0:
        print("⚠️  实际模式有ansible步骤，但预览模式没有")
    elif len(preview_ansible) > 0:
        print("⚠️  预览模式有ansible步骤，但实际模式没有")
    else:
        print("❌ 两种模式都没有ansible步骤")
else:
    print("❌ 无法比较结果，API调用失败")

print("\n💡 建议:")
print("1. 在前端预览页面测试两种模式切换")
print("2. 验证执行流水线功能是否正常")
print("3. 确保所有流水线的步骤都正确保存到数据库")
