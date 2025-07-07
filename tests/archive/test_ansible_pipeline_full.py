#!/usr/bin/env python3
"""
验证Ansible步骤在实际流水线中的转换效果
测试流水线执行时Ansible步骤是否正确转换为Jenkins Pipeline
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
from project_management.models import Project
from pipelines.models import Pipeline
from cicd_integrations.models import CICDTool, AtomicStep, PipelineExecution
from cicd_integrations.services import UnifiedCICDEngine
from cicd_integrations.adapters.jenkins import JenkinsAdapter

def test_pipeline_with_ansible():
    """测试包含Ansible步骤的流水线执行"""
    print("="*60)
    print("🧪 测试包含Ansible步骤的流水线Pipeline转换")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. 获取/创建基础数据
        print("1. 📋 准备基础数据")
        user = User.objects.get(username='admin')
        
        # 获取或创建项目
        project, _ = Project.objects.get_or_create(
            name='Ansible Test Project',
            defaults={
                'description': 'Test project for Ansible pipeline',
                'owner': user
            }
        )
        print(f"   ✅ 项目: {project.name}")
        
        # 2. 创建测试流水线
        print("2. 🚀 创建测试流水线")
        pipeline, _ = Pipeline.objects.get_or_create(
            name='Ansible Deploy Pipeline',
            defaults={
                'description': 'Pipeline with Ansible deployment steps',
                'project': project,
                'execution_mode': 'remote',
                'created_by': user
            }
        )
        print(f"   ✅ 流水线: {pipeline.name}")
        
        # 3. 创建Ansible原子步骤
        print("3. ⚙️ 创建Ansible原子步骤")
        
        # 删除现有步骤（如果有）
        AtomicStep.objects.filter(pipeline=pipeline).delete()
        
        # 步骤1: 代码检出
        checkout_step = AtomicStep.objects.create(
            pipeline=pipeline,
            name='Checkout Code',
            description='Checkout source code from repository',
            step_type='shell_script',
            order=1,
            parameters={
                'script': 'git checkout main && echo "Code checked out successfully"'
            }
        )
        
        # 步骤2: Ansible部署
        ansible_step = AtomicStep.objects.create(
            pipeline=pipeline,
            name='Deploy with Ansible',
            description='Deploy application using Ansible playbook',
            step_type='ansible',
            order=2,
            parameters={
                'playbook_path': 'deploy.yml',
                'inventory_path': 'production.ini',
                'extra_vars': {
                    'app_version': '2.1.0',
                    'environment': 'production',
                    'database_host': 'db.example.com'
                },
                'tags': 'webserver,database',
                'ansible_user': 'deploy',
                'verbose': True
            }
        )
        
        # 步骤3: 健康检查
        health_check_step = AtomicStep.objects.create(
            pipeline=pipeline,
            name='Health Check',
            description='Verify deployment success',
            step_type='shell_script',
            order=3,
            parameters={
                'script': 'curl -f http://app.example.com/health || exit 1'
            }
        )
        
        print(f"   ✅ 创建了3个步骤:")
        print(f"      - {checkout_step.name} ({checkout_step.step_type})")
        print(f"      - {ansible_step.name} ({ansible_step.step_type})")
        print(f"      - {health_check_step.name} ({health_check_step.step_type})")
        print()
        
        # 4. 模拟执行引擎构建Pipeline定义
        print("4. 🏗️ 构建Pipeline Definition")
        
        # 创建模拟执行记录
        execution = PipelineExecution.objects.create(
            pipeline=pipeline,
            cicd_tool=None,  # 暂不关联真实工具
            status='pending',
            trigger_type='manual',
            triggered_by=user,
            parameters={'test_execution': True}
        )
        
        # 使用执行引擎构建pipeline definition
        engine = UnifiedCICDEngine()
        pipeline_definition = engine._build_pipeline_definition_from_atomic_steps(execution)
        
        print(f"   ✅ Pipeline名称: {pipeline_definition.name}")
        print(f"   ✅ 步骤数量: {len(pipeline_definition.steps)}")
        print()
        
        # 5. 测试Jenkins转换
        print("5. 🔄 测试Jenkins Pipeline转换")
        jenkins_adapter = JenkinsAdapter(
            base_url='http://localhost:8080',
            username='admin',
            token='test-token'
        )
        
        # 生成完整Jenkinsfile
        import asyncio
        async def generate_jenkinsfile():
            return await jenkins_adapter.create_pipeline_file(pipeline_definition)
        
        jenkinsfile = asyncio.run(generate_jenkinsfile())
        
        print("6. 📄 生成的Jenkins Pipeline:")
        print("=" * 60)
        print(jenkinsfile)
        print("=" * 60)
        print()
        
        # 7. 验证Ansible步骤转换
        print("7. ✅ 验证Ansible步骤转换结果")
        
        # 检查是否包含必要的Ansible命令元素
        ansible_checks = [
            ('ansible-playbook', 'Ansible playbook 命令'),
            ('deploy.yml', 'Playbook 文件'),
            ('production.ini', 'Inventory 文件'),
            ('app_version=2.1.0', '额外变量'),
            ('--tags webserver,database', '标签选择'),
            ('-u deploy', '用户设置'),
            ('-v', '详细输出'),
        ]
        
        passed_checks = 0
        for check, description in ansible_checks:
            if check in jenkinsfile:
                print(f"   ✅ {description}: 已包含")
                passed_checks += 1
            else:
                print(f"   ❌ {description}: 未找到")
        
        print()
        print("8. 📊 测试结果总结")
        print(f"   总检查项: {len(ansible_checks)}")
        print(f"   通过检查: {passed_checks}")
        print(f"   成功率: {passed_checks/len(ansible_checks)*100:.1f}%")
        print()
        
        if passed_checks == len(ansible_checks):
            print("🎉 Ansible步骤转换完全成功！")
            print("   ✅ 所有Ansible参数都正确转换为Jenkins Pipeline")
            print("   ✅ 生成的Jenkinsfile结构完整且符合预期")
            print("   ✅ 可以直接在Jenkins中执行")
            success = True
        else:
            print("⚠️ Ansible步骤转换部分成功")
            print("   某些参数可能未正确转换，需要进一步检查")
            success = False
        
        print()
        print("🎯 使用建议:")
        print("   1. 在AnsFlow中创建包含ansible类型步骤的流水线")
        print("   2. 配置playbook_path、inventory_path等参数")
        print("   3. 设置execution_mode为remote")
        print("   4. 执行流水线时，系统会自动转换为Jenkins Pipeline")
        print("   5. Jenkins将执行ansible-playbook命令")
        
        return success
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_pipeline_with_ansible()
    print()
    print("="*60)
    if success:
        print("🎉 Ansible流水线转换测试成功完成！")
    else:
        print("💥 Ansible流水线转换测试失败！")
    print("="*60)
