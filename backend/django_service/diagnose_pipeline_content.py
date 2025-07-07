#!/usr/bin/env python3
"""
诊断流水线预览内容不一致问题
检查数据库中的实际步骤数据 vs 前端编辑器内容
"""

import requests
import json
import sys
import os
import django
from django.conf import settings

# 设置 Django 环境
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from pipelines.models import Pipeline
from cicd_integrations.models import AtomicStep

def get_auth_token():
    """获取认证令牌"""
    login_data = {"username": "admin", "password": "admin123"}
    try:
        response = requests.post("http://localhost:8000/api/v1/auth/login/", json=login_data)
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token') or data.get('access')
        else:
            print(f"❌ 登录失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

def diagnose_pipeline_by_name(pipeline_name="Integration Test Pipeline"):
    """诊断指定名称的流水线"""
    print(f"🔍 诊断流水线: {pipeline_name}")
    print("=" * 70)
    
    try:
        # 从数据库直接查询
        pipeline = Pipeline.objects.filter(name__icontains=pipeline_name).first()
        if not pipeline:
            print(f"❌ 未找到包含 '{pipeline_name}' 的流水线")
            # 显示所有流水线
            all_pipelines = Pipeline.objects.all()
            print(f"📋 可用的流水线:")
            for p in all_pipelines:
                print(f"   - {p.name} (ID: {p.id})")
            return
        
        print(f"✅ 找到流水线: {pipeline.name} (ID: {pipeline.id})")
        
        # 1. 检查数据库中的原子步骤
        print(f"\n1️⃣ 数据库中的AtomicStep数据:")
        atomic_steps = pipeline.atomic_steps.all().order_by('order')
        
        if not atomic_steps.exists():
            print("   ❌ 数据库中没有AtomicStep数据!")
        else:
            print(f"   ✅ 找到 {atomic_steps.count()} 个AtomicStep:")
            for step in atomic_steps:
                print(f"      {step.order}. {step.name} ({step.step_type})")
                if step.step_type == 'ansible':
                    print(f"         📝 Ansible参数: {step.parameters}")
        
        # 2. 通过API获取流水线详情
        print(f"\n2️⃣ API返回的流水线详情:")
        token = get_auth_token()
        if token:
            headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            response = requests.get(f"http://localhost:8000/api/v1/pipelines/pipelines/{pipeline.id}/", headers=headers)
            
            if response.status_code == 200:
                api_data = response.json()
                steps_data = api_data.get('steps', [])
                atomic_steps_data = api_data.get('atomic_steps', [])
                
                print(f"   📊 API字段:")
                print(f"      steps: {len(steps_data)} 个")
                print(f"      atomic_steps: {len(atomic_steps_data)} 个")
                
                if steps_data:
                    print(f"   📋 steps字段内容:")
                    for i, step in enumerate(steps_data):
                        print(f"      {i+1}. {step.get('name', 'N/A')} ({step.get('step_type', 'N/A')})")
                        if step.get('step_type') == 'ansible':
                            print(f"         📝 Ansible参数: {step.get('parameters', {})}")
                
                if atomic_steps_data:
                    print(f"   📋 atomic_steps字段内容:")
                    for i, step in enumerate(atomic_steps_data):
                        print(f"      {i+1}. {step.get('name', 'N/A')} ({step.get('step_type', 'N/A')})")
                        if step.get('step_type') == 'ansible':
                            print(f"         📝 Ansible参数: {step.get('parameters', {})}")
            else:
                print(f"   ❌ API调用失败: {response.status_code}")
        
        # 3. 测试预览API - 实际模式（数据库内容）
        print(f"\n3️⃣ 预览API - 实际模式测试:")
        if token:
            preview_data = {
                "pipeline_id": pipeline.id,
                "steps": [],  # 空数组，让后端从数据库获取
                "execution_mode": "local",
                "preview_mode": False,  # 实际模式
                "ci_tool_type": "jenkins"
            }
            
            response = requests.post("http://localhost:8000/api/v1/cicd/pipelines/preview/", 
                                   json=preview_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get('workflow_summary', {})
                print(f"   ✅ 预览API成功:")
                print(f"      总步骤数: {summary.get('total_steps', 0)}")
                print(f"      数据来源: {summary.get('data_source', 'unknown')}")
                print(f"      步骤类型: {summary.get('step_types', [])}")
                
                # 检查是否包含ansible
                step_types = summary.get('step_types', [])
                if 'ansible' in step_types:
                    print(f"      ✅ 包含ansible步骤")
                else:
                    print(f"      ❌ 缺少ansible步骤")
            else:
                print(f"   ❌ 预览API失败: {response.status_code} - {response.text}")
        
        # 4. 模拟前端编辑器发送的预览模式
        print(f"\n4️⃣ 预览API - 编辑器模式测试:")
        if token:
            # 模拟前端编辑器中包含ansible步骤的数据
            editor_steps = [
                {
                    "name": "环境检查",
                    "step_type": "custom",
                    "parameters": {"command": "echo '检查环境'"},
                    "order": 1,
                    "description": "检查执行环境"
                },
                {
                    "name": "Ansible部署",
                    "step_type": "ansible",
                    "parameters": {
                        "playbook_path": "deploy.yml",
                        "inventory_path": "production.ini",
                        "extra_vars": {"app_version": "2.1.0", "environment": "production"}
                    },
                    "order": 2,
                    "description": "Ansible自动化部署"
                },
                {
                    "name": "运行测试",
                    "step_type": "test",
                    "parameters": {"test_command": "pytest --cov=."},
                    "order": 3,
                    "description": "执行单元测试"
                }
            ]
            
            preview_data = {
                "pipeline_id": pipeline.id,
                "steps": editor_steps,  # 前端编辑器内容
                "execution_mode": "local",
                "preview_mode": True,  # 编辑器预览模式
                "ci_tool_type": "jenkins"
            }
            
            response = requests.post("http://localhost:8000/api/v1/cicd/pipelines/preview/", 
                                   json=preview_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get('workflow_summary', {})
                print(f"   ✅ 编辑器预览成功:")
                print(f"      总步骤数: {summary.get('total_steps', 0)}")
                print(f"      数据来源: {summary.get('data_source', 'unknown')}")
                print(f"      步骤类型: {summary.get('step_types', [])}")
                
                step_types = summary.get('step_types', [])
                if 'ansible' in step_types:
                    print(f"      ✅ 包含ansible步骤")
                else:
                    print(f"      ❌ 缺少ansible步骤")
            else:
                print(f"   ❌ 编辑器预览失败: {response.status_code} - {response.text}")
        
    except Exception as e:
        print(f"❌ 诊断过程异常: {e}")

def add_missing_ansible_step(pipeline_name="Integration Test Pipeline"):
    """为流水线添加缺失的ansible步骤"""
    print(f"\n🔧 修复流水线: {pipeline_name}")
    print("=" * 50)
    
    try:
        pipeline = Pipeline.objects.filter(name__icontains=pipeline_name).first()
        if not pipeline:
            print(f"❌ 未找到流水线")
            return
        
        # 检查是否已有ansible步骤
        existing_ansible = pipeline.atomic_steps.filter(step_type='ansible').exists()
        if existing_ansible:
            print(f"✅ 流水线已有ansible步骤，无需添加")
            return
        
        # 获取最大order值
        max_order = pipeline.atomic_steps.aggregate(models.Max('order'))['order__max'] or 0
        
        # 创建ansible步骤
        ansible_step = AtomicStep.objects.create(
            pipeline=pipeline,
            name="Ansible自动化部署",
            step_type="ansible",
            description="使用Ansible进行自动化部署",
            parameters={
                "playbook_path": "deploy.yml",
                "inventory_path": "production.ini",
                "extra_vars": {
                    "app_version": "2.1.0",
                    "environment": "production"
                }
            },
            order=max_order + 1,
            is_active=True
        )
        
        print(f"✅ 已添加ansible步骤: {ansible_step.name} (Order: {ansible_step.order})")
        
        # 验证添加结果
        total_steps = pipeline.atomic_steps.count()
        ansible_count = pipeline.atomic_steps.filter(step_type='ansible').count()
        print(f"📊 流水线现有步骤: {total_steps} 个 (ansible: {ansible_count} 个)")
        
    except Exception as e:
        print(f"❌ 修复过程异常: {e}")

def main():
    """主函数"""
    print("🧪 流水线预览内容不一致诊断工具")
    print("=" * 70)
    print("问题: 预览模式显示ansible步骤，实际模式缺少ansible步骤")
    print("目标: 诊断数据库vs前端编辑器内容差异")
    print("=" * 70)
    
    # 诊断流水线
    diagnose_pipeline_by_name("Integration Test Pipeline")
    
    # 询问是否要修复
    print(f"\n🤔 是否要为流水线添加缺失的ansible步骤? (y/n): ", end="")
    try:
        user_input = input().strip().lower()
        if user_input in ['y', 'yes']:
            from django.db import models
            add_missing_ansible_step("Integration Test Pipeline")
            print(f"\n🔄 重新诊断修复后的状态:")
            diagnose_pipeline_by_name("Integration Test Pipeline")
        else:
            print(f"💡 如需修复，请手动在前端保存包含ansible步骤的流水线")
    except KeyboardInterrupt:
        print(f"\n👋 诊断完成")
    
    print(f"\n📝 总结:")
    print(f"1. 预览模式用前端编辑器临时数据（可能包含未保存的ansible步骤）")
    print(f"2. 实际模式用数据库已保存数据（如果缺少ansible步骤则不显示）")
    print(f"3. 解决方案: 在前端编辑器中保存包含ansible步骤的流水线")

if __name__ == "__main__":
    main()
