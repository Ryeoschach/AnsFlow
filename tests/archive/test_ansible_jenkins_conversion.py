#!/usr/bin/env python3
"""
测试Ansible步骤转换为Jenkins Pipeline的功能
验证Ansible步骤能否正确转换为Jenkins stage
"""

import os
import sys
import django
from datetime import datetime

# 设置Django环境
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from django.contrib.auth.models import User
from pipelines.models import Pipeline, PipelineStep
from ansible_integration.models import AnsiblePlaybook, AnsibleInventory, AnsibleCredential
from cicd_integrations.models import CICDTool, AtomicStep, PipelineExecution
from cicd_integrations.services import UnifiedCICDEngine
from cicd_integrations.adapters.jenkins import JenkinsAdapter

def test_ansible_jenkins_conversion():
    """测试Ansible步骤转换为Jenkins Pipeline"""
    print("="*60)
    print("🧪 测试Ansible步骤转换为Jenkins Pipeline")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. 获取测试数据
        print("1. 📋 准备测试数据")
        user = User.objects.get(username='admin')
        
        # 获取或创建测试Ansible资源
        playbook, _ = AnsiblePlaybook.objects.get_or_create(
            name='test-playbook',
            defaults={
                'content': '''
---
- hosts: all
  tasks:
    - name: Hello World
      debug:
        msg: "Hello from Ansible!"
''',
                'created_by': user
            }
        )
        
        inventory, _ = AnsibleInventory.objects.get_or_create(
            name='test-inventory',
            defaults={
                'content': '[test]\nlocalhost ansible_connection=local',
                'created_by': user
            }
        )
        
        credential, _ = AnsibleCredential.objects.get_or_create(
            name='test-credential',
            defaults={
                'credential_type': 'ssh_key',
                'username': 'testuser',
                'ssh_private_key': 'test-key',
                'created_by': user
            }
        )
        
        print(f"   ✅ Playbook: {playbook.name}")
        print(f"   ✅ Inventory: {inventory.name}")
        print(f"   ✅ Credential: {credential.name}")
        print()
        
        # 2. 创建测试流水线
        print("2. 🚀 创建测试流水线")
        pipeline, created = Pipeline.objects.get_or_create(
            name='Ansible Jenkins Test Pipeline',
            defaults={
                'description': 'Test pipeline for Ansible to Jenkins conversion',
                'execution_mode': 'remote',
                'created_by': user
            }
        )
        print(f"   ✅ 流水线: {pipeline.name} ({'新建' if created else '已存在'})")
        
        # 3. 创建Ansible原子步骤
        print("3. ⚙️ 创建Ansible原子步骤")
        atomic_step, created = AtomicStep.objects.get_or_create(
            pipeline=pipeline,
            name='Deploy with Ansible',
            defaults={
                'description': 'Deploy application using Ansible playbook',
                'step_type': 'ansible',
                'order': 1,
                'ansible_playbook': playbook,
                'ansible_inventory': inventory,
                'ansible_credential': credential,
                'ansible_parameters': {
                    'extra_vars': {
                        'app_version': '1.0.0',
                        'environment': 'test'
                    },
                    'tags': 'deploy',
                    'verbose': True
                },
                'parameters': {
                    'custom_var': 'test_value'
                }
            }
        )
        print(f"   ✅ Ansible步骤: {atomic_step.name} ({'新建' if created else '已存在'})")
        print()
        
        # 4. 测试Jenkins适配器
        print("4. 🔧 测试Jenkins适配器转换")
        jenkins_adapter = JenkinsAdapter(
            base_url='http://localhost:8080',
            username='admin',
            token='test-token'
        )
        
        # 5. 模拟执行引擎构建pipeline definition
        print("5. 🏗️ 构建Pipeline Definition")
        
        # 创建模拟执行记录
        execution = PipelineExecution.objects.create(
            pipeline=pipeline,
            cicd_tool=None,  # 暂时不关联真实工具
            status='pending',
            trigger_type='manual',
            triggered_by=user,
            parameters={'test_param': 'test_value'}
        )
        
        # 使用执行引擎构建pipeline definition
        engine = UnifiedCICDEngine()
        pipeline_definition = engine._build_pipeline_definition_from_atomic_steps(execution)
        
        print(f"   ✅ Pipeline名称: {pipeline_definition.name}")
        print(f"   ✅ 步骤数量: {len(pipeline_definition.steps)}")
        
        # 6. 测试步骤转换
        print("6. 🔄 测试Ansible步骤转换")
        for i, step in enumerate(pipeline_definition.steps):
            print(f"   步骤 {i+1}: {step['name']} (类型: {step['type']})")
            print(f"   参数: {step['parameters']}")
            
            if step['type'] == 'ansible':
                # 测试Jenkins脚本生成
                jenkins_script = jenkins_adapter._generate_stage_script(
                    step['type'], 
                    step['parameters']
                )
                print(f"   生成的Jenkins脚本:")
                print("   " + "="*50)
                for line in jenkins_script.split('\n'):
                    print(f"   {line}")
                print("   " + "="*50)
            print()
        
        # 7. 生成完整Jenkinsfile
        print("7. 📄 生成完整Jenkinsfile")
        jenkinsfile_content = jenkins_adapter._convert_atomic_steps_to_jenkinsfile(
            pipeline_definition.steps
        )
        
        print("生成的Jenkinsfile内容:")
        print("="*60)
        print(jenkinsfile_content)
        print("="*60)
        
        # 8. 验证结果
        print("8. ✅ 验证结果")
        success_checks = []
        
        # 检查是否包含ansible-playbook命令
        if 'ansible-playbook' in jenkinsfile_content:
            success_checks.append("✅ 包含ansible-playbook命令")
        else:
            success_checks.append("❌ 缺少ansible-playbook命令")
        
        # 检查是否包含playbook名称
        if playbook.name in jenkinsfile_content:
            success_checks.append("✅ 包含playbook名称")
        else:
            success_checks.append("❌ 缺少playbook名称")
        
        # 检查是否包含extra-vars
        if '--extra-vars' in jenkinsfile_content:
            success_checks.append("✅ 包含extra-vars参数")
        else:
            success_checks.append("❌ 缺少extra-vars参数")
        
        # 检查是否包含tags
        if '--tags' in jenkinsfile_content:
            success_checks.append("✅ 包含tags参数")
        else:
            success_checks.append("❌ 缺少tags参数")
        
        # 检查是否包含verbose选项
        if '-v' in jenkinsfile_content:
            success_checks.append("✅ 包含verbose选项")
        else:
            success_checks.append("❌ 缺少verbose选项")
        
        for check in success_checks:
            print(f"   {check}")
        
        print()
        
        # 统计结果
        success_count = len([c for c in success_checks if c.startswith('✅')])
        total_count = len(success_checks)
        
        print(f"🎯 测试结果: {success_count}/{total_count} 通过")
        
        if success_count == total_count:
            print("🎉 所有测试通过！Ansible步骤成功转换为Jenkins Pipeline")
        else:
            print("⚠️ 部分测试失败，需要进一步检查")
        
        print()
        print("📝 使用建议:")
        print("   1. 在流水线中添加ansible类型步骤")
        print("   2. 配置playbook、inventory和credential")
        print("   3. 设置execution_mode为remote")
        print("   4. 执行流水线，Jenkins将自动转换ansible步骤")
        
        return success_count == total_count
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_ansible_jenkins_conversion()
    print()
    print("="*60)
    if success:
        print("🎉 Ansible到Jenkins转换测试成功完成！")
    else:
        print("💥 Ansible到Jenkins转换测试失败！")
    print("="*60)
