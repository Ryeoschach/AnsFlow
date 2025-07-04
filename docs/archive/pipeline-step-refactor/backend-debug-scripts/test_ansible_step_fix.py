#!/usr/bin/env python3
"""
测试Ansible步骤保存修复
"""
import os
import django
import sys
import json

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from cicd_integrations.models import AtomicStep
from ansible_integration.models import AnsiblePlaybook, AnsibleInventory, AnsibleCredential
from project_management.models import Project
from django.contrib.auth.models import User

def test_ansible_step_save():
    """测试Ansible步骤的保存功能"""
    print("🧪 测试Ansible步骤保存修复...")
    
    try:
        # 获取或创建测试用户
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={'email': 'test@example.com', 'password': 'test123'}
        )
        
        # 创建测试项目
        project, created = Project.objects.get_or_create(
            name='Test Project',
            defaults={
                'description': 'Test project for ansible step',
                'owner': user
            }
        )
        print(f"✅ 测试项目: {project.name} (ID: {project.id})")
        
        # 创建测试Playbook
        playbook, created = AnsiblePlaybook.objects.get_or_create(
            name='test-playbook',
            defaults={
                'content': 'test content',
                'description': 'Test playbook for ansible step',
                'created_by': user
            }
        )
        print(f"✅ 测试Playbook: {playbook.name} (ID: {playbook.id})")
        
        # 创建测试Inventory
        inventory, created = AnsibleInventory.objects.get_or_create(
            name='test-inventory',
            defaults={
                'content': '[test]\nlocalhost',
                'created_by': user
            }
        )
        print(f"✅ 测试Inventory: {inventory.name} (ID: {inventory.id})")
        
        # 创建测试Credential
        credential, created = AnsibleCredential.objects.get_or_create(
            name='test-credential',
            defaults={
                'credential_type': 'ssh_key',
                'username': 'test',
                'ssh_private_key': 'test-key',
                'created_by': user
            }
        )
        print(f"✅ 测试Credential: {credential.name} (ID: {credential.id})")
        
        # 创建测试流水线
        pipeline, created = Pipeline.objects.get_or_create(
            name='Test Ansible Pipeline',
            defaults={
                'description': 'Test pipeline for ansible step saving',
                'project': project,
                'created_by': user
            }
        )
        print(f"✅ 测试流水线: {pipeline.name} (ID: {pipeline.id})")
        
        # 创建Ansible步骤
        ansible_step = AtomicStep.objects.create(
            name='Test Ansible Step',
            step_type='ansible',
            description='Test ansible step with all fields',
            pipeline=pipeline,
            order=1,
            parameters={
                'extra_vars': {'test_var': 'test_value'},
                'check_mode': False
            },
            ansible_playbook=playbook,
            ansible_inventory=inventory,
            ansible_credential=credential,
            created_by=user
        )
        
        print(f"✅ 创建Ansible步骤: {ansible_step.name} (ID: {ansible_step.id})")
        print(f"   - Playbook: {ansible_step.ansible_playbook.name if ansible_step.ansible_playbook else 'None'}")
        print(f"   - Inventory: {ansible_step.ansible_inventory.name if ansible_step.ansible_inventory else 'None'}")
        print(f"   - Credential: {ansible_step.ansible_credential.name if ansible_step.ansible_credential else 'None'}")
        print(f"   - Parameters: {json.dumps(ansible_step.parameters, indent=2)}")
        
        # 测试更新步骤
        ansible_step.parameters.update({'timeout': 300})
        ansible_step.save()
        
        print(f"✅ 更新步骤参数: {json.dumps(ansible_step.parameters, indent=2)}")
        
        # 验证关联关系
        assert ansible_step.ansible_playbook == playbook
        assert ansible_step.ansible_inventory == inventory
        assert ansible_step.ansible_credential == credential
        
        print("✅ 所有关联关系验证通过！")
        
        # 测试通过流水线访问步骤
        pipeline_steps = pipeline.atomic_steps.filter(step_type='ansible')
        print(f"✅ 流水线中的Ansible步骤数量: {pipeline_steps.count()}")
        
        for step in pipeline_steps:
            print(f"   - {step.name}: Playbook={step.ansible_playbook.name if step.ansible_playbook else 'None'}")
        
        print("\n🎉 Ansible步骤保存功能测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_ansible_step_save()
    sys.exit(0 if success else 1)
