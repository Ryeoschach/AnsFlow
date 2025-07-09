#!/usr/bin/env python3
"""
创建Pipeline-Ansible集成测试数据
"""
import os
import sys
import django

# 添加项目路径
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

django.setup()

from django.contrib.auth.models import User
from pipelines.models import Pipeline, PipelineStep
from project_management.models import Project
from ansible_integration.models import AnsiblePlaybook, AnsibleInventory, AnsibleCredential


def create_test_pipeline_with_ansible():
    """创建包含Ansible步骤的测试Pipeline"""
    
    # 获取用户和项目
    user = User.objects.get(username='admin')
    
    # 创建或获取项目
    project, created = Project.objects.get_or_create(
        name='AnsFlow测试项目',
        defaults={
            'description': '用于测试Pipeline-Ansible集成的项目',
            'owner': user
        }
    )
    
    # 创建Pipeline
    pipeline = Pipeline.objects.create(
        name='Web应用部署流水线',
        description='包含Ansible自动化部署步骤的CI/CD流水线',
        project=project,
        created_by=user,
        execution_mode='local'
    )
    
    # 获取已存在的Ansible资源
    try:
        nginx_playbook = AnsiblePlaybook.objects.get(name='Nginx安装配置')
        dev_inventory = AnsibleInventory.objects.get(name='开发环境')
        ssh_credential = AnsibleCredential.objects.filter(credential_type='ssh_key').first()
        
        if not ssh_credential:
            ssh_credential = AnsibleCredential.objects.filter(credential_type='password').first()
        
        if not ssh_credential:
            print("错误：没有找到可用的认证凭据")
            return None
            
    except Exception as e:
        print(f"错误：获取Ansible资源失败 - {e}")
        return None
    
    # 创建Pipeline步骤
    
    # 步骤1：代码检出（普通命令步骤）
    step1 = PipelineStep.objects.create(
        pipeline=pipeline,
        name='代码检出',
        description='从Git仓库检出代码',
        step_type='command',
        command='git clone https://github.com/example/webapp.git /tmp/webapp',
        order=1,
        timeout_seconds=300
    )
    
    # 步骤2：构建应用（普通命令步骤）
    step2 = PipelineStep.objects.create(
        pipeline=pipeline,
        name='构建应用',
        description='编译和打包应用',
        step_type='command',
        command='cd /tmp/webapp && npm install && npm run build',
        order=2,
        timeout_seconds=600
    )
    
    # 步骤3：Ansible部署Nginx（Ansible步骤）
    step3 = PipelineStep.objects.create(
        pipeline=pipeline,
        name='部署Nginx服务器',
        description='使用Ansible自动化部署Nginx',
        step_type='ansible',
        ansible_playbook=nginx_playbook,
        ansible_inventory=dev_inventory,
        ansible_credential=ssh_credential,
        ansible_parameters={
            'port': '8080',
            'domain': 'dev.ansflow.com'
        },
        order=3,
        timeout_seconds=900
    )
    
    # 步骤4：健康检查（普通命令步骤）
    step4 = PipelineStep.objects.create(
        pipeline=pipeline,
        name='服务健康检查',
        description='检查部署的服务是否正常运行',
        step_type='command',
        command='curl -f http://dev.ansflow.com:8080/health || exit 1',
        order=4,
        timeout_seconds=60
    )
    
    print(f"✅ 创建成功！")
    print(f"Pipeline ID: {pipeline.id}")
    print(f"Pipeline名称: {pipeline.name}")
    print(f"总步骤数: {pipeline.steps.count()}")
    print(f"Ansible步骤数: {pipeline.steps.filter(step_type='ansible').count()}")
    
    # 显示步骤详情
    print("\n📋 Pipeline步骤:")
    for step in pipeline.steps.all().order_by('order'):
        print(f"  {step.order}. {step.name} ({step.step_type})")
        if step.step_type == 'ansible':
            print(f"     📖 Playbook: {step.ansible_playbook.name}")
            print(f"     📋 Inventory: {step.ansible_inventory.name}")
            print(f"     🔑 Credential: {step.ansible_credential.name}")
    
    return pipeline


if __name__ == '__main__':
    try:
        pipeline = create_test_pipeline_with_ansible()
        if pipeline:
            print(f"\n🎉 Pipeline-Ansible集成测试数据创建完成！")
            print(f"可以使用API测试: /api/v1/pipelines/{pipeline.id}/")
        else:
            print("❌ 创建失败")
    except Exception as e:
        print(f"❌ 创建失败: {e}")
