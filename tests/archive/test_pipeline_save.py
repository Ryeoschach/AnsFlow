#!/usr/bin/env python3
"""
测试流水线保存后数据库更新是否正确
模拟前端保存操作，验证AtomicStep是否正确更新
"""

import os
import sys
import json
import requests

# Django设置
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from pipelines.models import Pipeline
from cicd_integrations.models import AtomicStep

print("🧪 流水线保存数据库更新测试")
print("=" * 60)

# 配置
BASE_URL = "http://localhost:8000"
PIPELINE_ID = 12  # Integration Test Pipeline
LOGIN_URL = f"{BASE_URL}/api/v1/auth/token/"
PIPELINE_URL = f"{BASE_URL}/api/v1/pipelines/pipelines/{PIPELINE_ID}/"

# 准备测试数据：模拟前端保存的3个步骤
test_steps = [
    {
        "id": "temp_1",
        "name": "代码拉取",
        "step_type": "fetch_code",
        "order": 1,
        "description": "从Git仓库拉取代码",
        "parameters": {
            "repository_url": "https://github.com/example/repo",
            "branch": "main"
        }
    },
    {
        "id": "temp_2", 
        "name": "构建项目",
        "step_type": "build",
        "order": 2,
        "description": "编译和构建项目",
        "parameters": {
            "build_command": "npm install && npm run build"
        }
    },
    {
        "id": "temp_3",
        "name": "Ansible部署",
        "step_type": "ansible",
        "order": 3,
        "description": "使用Ansible进行自动化部署",
        "parameters": {
            "playbook_path": "deploy.yml",
            "inventory_path": "production.ini",
            "extra_vars": {
                "app_version": "3.0.0",
                "environment": "production"
            }
        }
    }
]

def login():
    """登录获取token"""
    try:
        response = requests.post(LOGIN_URL, json={
            "username": "admin",
            "password": "admin123"
        })
        if response.status_code == 200:
            token = response.json()['access']
            print(f"✅ 登录成功，获取token")
            return token
        else:
            print(f"❌ 登录失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

def get_pipeline_before(token):
    """获取保存前的流水线数据"""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(PIPELINE_URL, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"❌ 获取流水线数据失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 获取流水线数据异常: {e}")
        return None

def save_pipeline(token, steps_data):
    """保存流水线（模拟前端保存操作）"""
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # 构建保存数据
        save_data = {
            "steps": steps_data
        }
        
        print(f"📤 发送保存请求...")
        print(f"📝 保存的步骤数量: {len(steps_data)}")
        for i, step in enumerate(steps_data, 1):
            print(f"   {i}. {step['name']} ({step['step_type']})")
        
        response = requests.patch(PIPELINE_URL, headers=headers, json=save_data)
        
        print(f"📡 保存请求状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ 流水线保存成功")
            return response.json()
        else:
            print(f"❌ 流水线保存失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📝 错误信息: {error_data}")
            except:
                print(f"📝 错误响应: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 保存流水线异常: {e}")
        return None

def check_database_after():
    """检查保存后数据库中的数据"""
    try:
        pipeline = Pipeline.objects.get(id=PIPELINE_ID)
        atomic_steps = list(pipeline.atomic_steps.all().order_by('order'))
        
        print(f"\n📊 数据库中的AtomicStep数据:")
        print(f"   数量: {len(atomic_steps)}")
        for step in atomic_steps:
            print(f"   {step.order}. {step.name} ({step.step_type})")
            if step.step_type == 'ansible':
                print(f"      📝 Ansible参数: {step.parameters}")
        
        return atomic_steps
    except Exception as e:
        print(f"❌ 检查数据库失败: {e}")
        return []

def test_preview_api_after(token):
    """测试保存后预览API的结果"""
    try:
        preview_url = f"{BASE_URL}/api/v1/cicd/pipelines/preview/"
        headers = {'Authorization': f'Bearer {token}'}
        
        # 测试实际模式
        payload = {
            "pipeline_id": PIPELINE_ID,
            "cicd_tool_id": 1,
            "preview_mode": False  # 实际模式，读取数据库
        }
        
        response = requests.post(preview_url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            workflow_summary = data.get('workflow_summary', {})
            total_steps = workflow_summary.get('total_steps', 0)
            step_types = workflow_summary.get('step_types', [])
            data_source = workflow_summary.get('data_source', '未知')
            
            print(f"\n📊 预览API结果（实际模式）:")
            print(f"   步骤数量: {total_steps}")
            print(f"   步骤类型: {step_types}")
            print(f"   数据来源: {data_source}")
            print(f"   包含ansible: {'是' if 'ansible' in step_types else '否'}")
            
            return total_steps
        else:
            print(f"❌ 预览API调用失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 预览API测试异常: {e}")
        return None

def main():
    print("🎯 目标: 验证前端保存后数据库是否正确更新")
    print("-" * 60)
    
    # 1. 登录
    token = login()
    if not token:
        return
    
    # 2. 获取保存前的数据
    print(f"\n📋 保存前的流水线数据:")
    before_data = get_pipeline_before(token)
    if before_data:
        before_steps = before_data.get('steps', [])
        print(f"   前端API返回步骤数: {len(before_steps)}")
    
    # 检查保存前数据库状态
    before_atomic_steps = check_database_after()
    print(f"   数据库AtomicStep数: {len(before_atomic_steps)}")
    
    # 3. 模拟前端保存操作
    print(f"\n💾 执行保存操作:")
    save_result = save_pipeline(token, test_steps)
    
    if save_result:
        # 4. 检查保存后数据库状态
        print(f"\n🔍 保存后数据库检查:")
        after_atomic_steps = check_database_after()
        
        # 5. 测试预览API
        api_steps = test_preview_api_after(token)
        
        # 6. 结果对比
        print(f"\n📊 结果对比:")
        print(f"   保存的步骤数: {len(test_steps)}")
        print(f"   数据库AtomicStep数: {len(after_atomic_steps)}")
        print(f"   预览API返回数: {api_steps if api_steps else '获取失败'}")
        
        if len(test_steps) == len(after_atomic_steps) == api_steps:
            print(f"\n🎉 测试成功！数据库已正确更新")
            print(f"✅ 前端保存的3个步骤已正确同步到数据库")
            print(f"✅ 预览API实际模式返回的步骤数量一致")
        else:
            print(f"\n❌ 测试失败！数据不一致")
            if len(after_atomic_steps) != len(test_steps):
                print(f"   数据库未正确更新：期望{len(test_steps)}个，实际{len(after_atomic_steps)}个")
            if api_steps != len(test_steps):
                print(f"   预览API数据不一致：期望{len(test_steps)}个，实际{api_steps}个")
    else:
        print(f"\n❌ 保存操作失败，无法进行后续测试")

if __name__ == "__main__":
    main()
