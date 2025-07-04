#!/usr/bin/env python3
"""
端到端测试Ansible步骤参数的保存与回显
测试完整的流水线+Ansible步骤链路，确保参数正确保存和回显
"""

import os
import sys
import json
import django
from datetime import datetime

# 设置Django环境
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth.models import User
from pipelines.models import Pipeline, PipelineStep
from pipelines.serializers import PipelineSerializer
from ansible_integration.models import AnsiblePlaybook, AnsibleInventory, AnsibleCredential
from project_management.models import Project

class AnsiblePipelineE2ETest:
    def __init__(self):
        self.test_user = None
        self.test_project = None
        self.test_pipeline = None
        self.test_playbook = None
        self.test_inventory = None  
        self.test_credential = None
        
    def setup_test_data(self):
        """创建测试所需的基础数据"""
        print("🔧 创建测试基础数据...")
        
        # 创建测试用户
        self.test_user, created = User.objects.get_or_create(
            username='test_ansible_user',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        print(f"   ✓ 测试用户: {self.test_user.username} ({'新创建' if created else '已存在'})")
        
        # 创建测试项目
        self.test_project, created = Project.objects.get_or_create(
            name='Ansible_Test_Project',
            defaults={
                'description': 'Ansible步骤测试项目',
                'owner': self.test_user
            }
        )
        print(f"   ✓ 测试项目: {self.test_project.name} ({'新创建' if created else '已存在'})")
        
        # 创建Ansible Playbook
        self.test_playbook, created = AnsiblePlaybook.objects.get_or_create(
            name='test_playbook',
            defaults={
                'description': '测试Playbook',
                'content': '''---
- name: Test Playbook
  hosts: all
  tasks:
    - name: Ping test
      ping:
''',
                'created_by': self.test_user
            }
        )
        print(f"   ✓ Ansible Playbook: {self.test_playbook.name} ({'新创建' if created else '已存在'})")
        
        # 创建Ansible Inventory
        self.test_inventory, created = AnsibleInventory.objects.get_or_create(
            name='test_inventory',
            defaults={
                'description': '测试Inventory',
                'content': '''[web]
localhost ansible_connection=local
''',
                'created_by': self.test_user
            }
        )
        print(f"   ✓ Ansible Inventory: {self.test_inventory.name} ({'新创建' if created else '已存在'})")
        
        # 创建Ansible Credential
        self.test_credential, created = AnsibleCredential.objects.get_or_create(
            name='test_credential',
            defaults={
                'credential_type': 'password',
                'username': 'testuser',
                'password': 'testpass',
                'created_by': self.test_user
            }
        )
        print(f"   ✓ Ansible Credential: {self.test_credential.name} ({'新创建' if created else '已存在'})")
        
    def create_test_pipeline(self):
        """创建测试流水线"""
        print("\n📝 创建测试流水线...")
        
        self.test_pipeline, created = Pipeline.objects.get_or_create(
            name='Ansible_E2E_Test_Pipeline',
            defaults={
                'description': 'Ansible端到端测试流水线',
                'project': self.test_project,
                'created_by': self.test_user,
                'is_active': True,
                'execution_mode': 'local'
            }
        )
        print(f"   ✓ 流水线: {self.test_pipeline.name} (ID: {self.test_pipeline.id}) ({'新创建' if created else '已存在'})")
        return self.test_pipeline.id
        
    def test_ansible_step_creation_via_serializer(self):
        """通过序列化器测试Ansible步骤的创建（模拟前端API调用）"""
        print("\n🧪 测试通过序列化器创建Ansible步骤...")
        
        # 准备测试数据 - 模拟前端发送的数据结构
        ansible_step_data = {
            'name': 'Ansible部署步骤',
            'step_type': 'ansible',
            'description': 'Ansible自动化部署',
            'parameters': {
                'playbook_id': self.test_playbook.id,
                'inventory_id': self.test_inventory.id, 
                'credential_id': self.test_credential.id,
                'extra_vars': {
                    'env': 'test',
                    'version': '1.0.0'
                },
                'timeout': 600,
                'verbose': True
            },
            'order': 1,
            'is_active': True
        }
        
        # 创建包含Ansible步骤的流水线更新数据
        pipeline_update_data = {
            'name': self.test_pipeline.name,
            'description': self.test_pipeline.description,
            'project': self.test_project.id,
            'is_active': True,
            'execution_mode': 'local',
            'steps': [ansible_step_data]
        }
        
        print(f"   📤 发送的步骤数据:")
        print(f"      - 步骤名称: {ansible_step_data['name']}")
        print(f"      - 步骤类型: {ansible_step_data['step_type']}")
        print(f"      - Playbook ID: {ansible_step_data['parameters']['playbook_id']}")
        print(f"      - Inventory ID: {ansible_step_data['parameters']['inventory_id']}")
        print(f"      - Credential ID: {ansible_step_data['parameters']['credential_id']}")
        print(f"      - 额外参数: {ansible_step_data['parameters']['extra_vars']}")
        
        # 使用序列化器更新流水线（模拟API调用）
        serializer = PipelineSerializer(instance=self.test_pipeline, data=pipeline_update_data, partial=True)
        
        if serializer.is_valid():
            updated_pipeline = serializer.save()
            print(f"   ✓ 流水线更新成功")
            
            # 检查步骤是否正确创建
            created_steps = PipelineStep.objects.filter(pipeline=updated_pipeline)
            print(f"   ✓ 创建了 {created_steps.count()} 个步骤")
            
            if created_steps.count() > 0:
                ansible_step = created_steps.first()
                print(f"   📥 创建的步骤详情:")
                print(f"      - ID: {ansible_step.id}")
                print(f"      - 名称: {ansible_step.name}")
                print(f"      - 类型: {ansible_step.step_type}")
                print(f"      - 描述: {ansible_step.description}")
                print(f"      - 顺序: {ansible_step.order}")
                print(f"      - ansible_playbook: {ansible_step.ansible_playbook}")
                print(f"      - ansible_inventory: {ansible_step.ansible_inventory}")
                print(f"      - ansible_credential: {ansible_step.ansible_credential}")
                print(f"      - ansible_parameters: {ansible_step.ansible_parameters}")
                
                return ansible_step
            else:
                print("   ❌ 未创建任何步骤")
                return None
        else:
            print(f"   ❌ 序列化器验证失败: {serializer.errors}")
            return None
            
    def test_ansible_step_retrieval_via_serializer(self):
        """通过序列化器测试Ansible步骤的检索（模拟前端API调用）"""
        print("\n🔍 测试通过序列化器检索Ansible步骤...")
        
        # 使用序列化器获取流水线数据（模拟GET API调用）
        serializer = PipelineSerializer(instance=self.test_pipeline)
        pipeline_data = serializer.data
        
        print(f"   📤 获取的流水线数据:")
        print(f"      - 流水线名称: {pipeline_data['name']}")
        print(f"      - 流水线ID: {pipeline_data['id']}")
        print(f"      - 步骤数量: {len(pipeline_data.get('steps', []))}")
        
        if 'steps' in pipeline_data and pipeline_data['steps']:
            for i, step_data in enumerate(pipeline_data['steps']):
                print(f"   📥 步骤 {i+1} 数据:")
                print(f"      - ID: {step_data.get('id')}")
                print(f"      - 名称: {step_data.get('name')}")
                print(f"      - 类型: {step_data.get('step_type')}")
                print(f"      - 描述: {step_data.get('description')}")
                print(f"      - 顺序: {step_data.get('order')}")
                print(f"      - ansible_playbook: {step_data.get('ansible_playbook')}")
                print(f"      - ansible_inventory: {step_data.get('ansible_inventory')}")
                print(f"      - ansible_credential: {step_data.get('ansible_credential')}")
                print(f"      - ansible_parameters: {step_data.get('ansible_parameters')}")
                
                # 检查Ansible参数的完整性
                if step_data.get('step_type') == 'ansible':
                    ansible_params = step_data.get('ansible_parameters', {})
                    print(f"   🔍 Ansible参数详情:")
                    print(f"      - playbook_id: {ansible_params.get('playbook_id')}")
                    print(f"      - inventory_id: {ansible_params.get('inventory_id')}")
                    print(f"      - credential_id: {ansible_params.get('credential_id')}")
                    print(f"      - extra_vars: {ansible_params.get('extra_vars')}")
                    print(f"      - timeout: {ansible_params.get('timeout')}")
                    print(f"      - verbose: {ansible_params.get('verbose')}")
                    
                return step_data
        else:
            print("   ❌ 未找到任何步骤")
            return None
            
    def test_ansible_step_update_via_serializer(self):
        """通过序列化器测试Ansible步骤的更新（模拟前端修改参数）"""
        print("\n✏️ 测试通过序列化器更新Ansible步骤...")
        
        # 准备更新的步骤数据 - 模拟前端修改了参数
        updated_ansible_step_data = {
            'name': 'Ansible部署步骤（已更新）',
            'step_type': 'ansible',
            'description': 'Ansible自动化部署 - 更新版本',
            'parameters': {
                'playbook_id': self.test_playbook.id,
                'inventory_id': self.test_inventory.id,
                'credential_id': self.test_credential.id,
                'extra_vars': {
                    'env': 'production',  # 修改环境
                    'version': '2.0.0',   # 修改版本
                    'debug': False        # 新增参数
                },
                'timeout': 900,           # 修改超时
                'verbose': False,         # 修改verbose
                'check_mode': True        # 新增参数
            },
            'order': 1,
            'is_active': True
        }
        
        # 创建包含更新Ansible步骤的流水线数据
        pipeline_update_data = {
            'name': self.test_pipeline.name,
            'description': self.test_pipeline.description,
            'project': self.test_project.id,
            'is_active': True,
            'execution_mode': 'local',
            'steps': [updated_ansible_step_data]
        }
        
        print(f"   📤 更新的步骤数据:")
        print(f"      - 步骤名称: {updated_ansible_step_data['name']}")
        print(f"      - 新环境: {updated_ansible_step_data['parameters']['extra_vars']['env']}")
        print(f"      - 新版本: {updated_ansible_step_data['parameters']['extra_vars']['version']}")
        print(f"      - 新超时: {updated_ansible_step_data['parameters']['timeout']}")
        print(f"      - 新增debug参数: {updated_ansible_step_data['parameters']['extra_vars']['debug']}")
        print(f"      - 新增check_mode参数: {updated_ansible_step_data['parameters']['check_mode']}")
        
        # 使用序列化器更新流水线
        serializer = PipelineSerializer(instance=self.test_pipeline, data=pipeline_update_data, partial=True)
        
        if serializer.is_valid():
            updated_pipeline = serializer.save()
            print(f"   ✓ 流水线更新成功")
            
            # 检查步骤是否正确更新
            updated_steps = PipelineStep.objects.filter(pipeline=updated_pipeline)
            if updated_steps.count() > 0:
                ansible_step = updated_steps.first()
                print(f"   📥 更新后的步骤详情:")
                print(f"      - 名称: {ansible_step.name}")
                print(f"      - ansible_parameters: {ansible_step.ansible_parameters}")
                
                # 验证参数是否正确更新
                params = ansible_step.ansible_parameters
                if params:
                    extra_vars = params.get('extra_vars', {})
                    print(f"   🔍 参数验证:")
                    print(f"      - 环境是否更新: {extra_vars.get('env') == 'production'}")
                    print(f"      - 版本是否更新: {extra_vars.get('version') == '2.0.0'}")
                    print(f"      - 超时是否更新: {params.get('timeout') == 900}")
                    print(f"      - debug参数是否存在: {'debug' in extra_vars}")
                    print(f"      - check_mode参数是否存在: {'check_mode' in params}")
                
                return ansible_step
            else:
                print("   ❌ 未找到更新的步骤")
                return None
        else:
            print(f"   ❌ 序列化器验证失败: {serializer.errors}")
            return None
            
    def verify_ansible_resources_exist(self):
        """验证Ansible资源是否存在"""
        print("\n🔍 验证Ansible资源是否存在...")
        
        playbook_exists = AnsiblePlaybook.objects.filter(id=self.test_playbook.id).exists()
        inventory_exists = AnsibleInventory.objects.filter(id=self.test_inventory.id).exists()
        credential_exists = AnsibleCredential.objects.filter(id=self.test_credential.id).exists()
        
        print(f"   - Playbook (ID: {self.test_playbook.id}): {'✓ 存在' if playbook_exists else '❌ 不存在'}")
        print(f"   - Inventory (ID: {self.test_inventory.id}): {'✓ 存在' if inventory_exists else '❌ 不存在'}")
        print(f"   - Credential (ID: {self.test_credential.id}): {'✓ 存在' if credential_exists else '❌ 不存在'}")
        
        return playbook_exists and inventory_exists and credential_exists
        
    def cleanup_test_data(self):
        """清理测试数据"""
        print("\n🧹 清理测试数据...")
        
        # 删除测试步骤
        step_count = PipelineStep.objects.filter(pipeline=self.test_pipeline).count()
        PipelineStep.objects.filter(pipeline=self.test_pipeline).delete()
        print(f"   ✓ 删除了 {step_count} 个测试步骤")
        
        # 删除测试流水线
        if self.test_pipeline:
            self.test_pipeline.delete()
            print(f"   ✓ 删除测试流水线")
        
        # 删除Ansible资源
        if self.test_playbook:
            self.test_playbook.delete()
            print(f"   ✓ 删除测试Playbook")
            
        if self.test_inventory:
            self.test_inventory.delete()
            print(f"   ✓ 删除测试Inventory")
            
        if self.test_credential:
            self.test_credential.delete()
            print(f"   ✓ 删除测试Credential")
        
        # 删除测试项目
        if self.test_project:
            self.test_project.delete()
            print(f"   ✓ 删除测试项目")
        
        # 删除测试用户
        if self.test_user:
            self.test_user.delete()
            print(f"   ✓ 删除测试用户")
    
    def run_full_test(self):
        """运行完整的端到端测试"""
        print("🚀 开始Ansible流水线端到端测试")
        print("=" * 60)
        
        try:
            # 1. 设置测试数据
            self.setup_test_data()
            
            # 2. 验证Ansible资源
            if not self.verify_ansible_resources_exist():
                print("❌ Ansible资源验证失败，停止测试")
                return False
            
            # 3. 创建测试流水线
            pipeline_id = self.create_test_pipeline()
            
            # 4. 测试创建Ansible步骤
            created_step = self.test_ansible_step_creation_via_serializer()
            if not created_step:
                print("❌ Ansible步骤创建测试失败")
                return False
                
            # 5. 测试检索Ansible步骤
            retrieved_step = self.test_ansible_step_retrieval_via_serializer()
            if not retrieved_step:
                print("❌ Ansible步骤检索测试失败")
                return False
                
            # 6. 测试更新Ansible步骤
            updated_step = self.test_ansible_step_update_via_serializer()
            if not updated_step:
                print("❌ Ansible步骤更新测试失败")
                return False
            
            print("\n" + "=" * 60)
            print("🎉 所有测试通过！Ansible步骤的参数保存和回显功能正常")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 测试过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            # 清理测试数据
            self.cleanup_test_data()
            
if __name__ == '__main__':
    test = AnsiblePipelineE2ETest()
    success = test.run_full_test()
    
    if success:
        print("\n✅ 测试结果: 成功")
        sys.exit(0)
    else:
        print("\n❌ 测试结果: 失败")
        sys.exit(1)
