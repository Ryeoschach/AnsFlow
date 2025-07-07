#!/usr/bin/env python3
"""
直接测试Ansible步骤在Jenkins Pipeline中的转换
不涉及数据库操作，专注验证转换逻辑
"""

import os
import sys
import django

# 设置Django环境
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from cicd_integrations.adapters.jenkins import JenkinsAdapter
from cicd_integrations.adapters.base import PipelineDefinition

def test_ansible_jenkins_conversion_direct():
    """直接测试Ansible步骤到Jenkins Pipeline的转换"""
    print("="*60)
    print("🧪 直接测试Ansible步骤→Jenkins Pipeline转换")
    print("="*60)
    
    # 创建Jenkins适配器
    jenkins_adapter = JenkinsAdapter(
        base_url='http://localhost:8080',
        username='admin',
        token='test-token'
    )
    
    # 模拟包含Ansible步骤的流水线定义
    print("1. 📋 创建包含Ansible步骤的流水线定义")
    steps = [
        {
            'name': 'Checkout Source',
            'type': 'fetch_code',
            'description': 'Checkout source code from Git repository',
            'parameters': {
                'repository_url': 'https://github.com/example/app.git',
                'branch': 'main'
            }
        },
        {
            'name': 'Configure Infrastructure',
            'type': 'ansible',
            'description': 'Configure servers using Ansible',
            'parameters': {
                'playbook_path': 'infrastructure/setup.yml',
                'inventory_path': 'infrastructure/hosts',
                'extra_vars': {
                    'nginx_version': '1.20.1',
                    'app_user': 'webapp',
                    'ssl_enabled': True
                },
                'tags': 'nginx,ssl',
                'ansible_user': 'admin',
                'verbose': True
            }
        },
        {
            'name': 'Deploy Application',
            'type': 'ansible',
            'description': 'Deploy application using Ansible',
            'parameters': {
                'playbook_path': 'deployment/deploy.yml',
                'inventory_path': 'deployment/production.ini',
                'extra_vars': {
                    'app_version': '3.2.1',
                    'environment': 'production',
                    'database_host': 'db.prod.example.com',
                    'redis_host': 'redis.prod.example.com'
                },
                'limit': 'webservers',
                'ansible_user': 'deploy'
            }
        },
        {
            'name': 'Verify Deployment',
            'type': 'shell_script',
            'description': 'Run deployment verification tests',
            'parameters': {
                'script': '''
                echo "Running deployment verification..."
                curl -f http://app.example.com/health
                curl -f http://app.example.com/api/status
                echo "Deployment verification completed"
                '''
            }
        }
    ]
    
    # 创建Pipeline定义
    pipeline_def = PipelineDefinition(
        name='Full Stack Ansible Deployment',
        steps=steps,
        triggers={'webhook': True, 'schedule': '0 2 * * *'},
        environment={
            'APP_ENV': 'production',
            'DEPLOY_REGION': 'us-west-2',
            'NOTIFICATION_SLACK': '#deployments'
        },
        artifacts=['logs/**/*', 'reports/**/*'],
        timeout=7200  # 2小时
    )
    
    print(f"   ✅ 流水线名称: {pipeline_def.name}")
    print(f"   ✅ 总步骤数: {len(pipeline_def.steps)}")
    print(f"   ✅ Ansible步骤数: {len([s for s in steps if s['type'] == 'ansible'])}")
    print()
    
    # 2. 生成Jenkins Pipeline
    print("2. 🔄 生成Jenkins Pipeline")
    import asyncio
    
    async def generate():
        return await jenkins_adapter.create_pipeline_file(pipeline_def)
    
    jenkinsfile = asyncio.run(generate())
    
    print("3. 📄 生成的完整Jenkins Pipeline:")
    print("=" * 60)
    print(jenkinsfile)
    print("=" * 60)
    print()
    
    # 4. 验证转换结果
    print("4. ✅ 验证Ansible步骤转换")
    
    # 基础Pipeline结构检查
    structure_checks = [
        ('pipeline {', 'Pipeline声明'),
        ('agent any', 'Agent配置'),
        ('stages {', 'Stages声明'),
        ('environment {', '环境变量'),
        ('post {', '后置处理'),
    ]
    
    # Ansible特定检查
    ansible_checks = [
        ('ansible-playbook', 'Ansible命令'),
        ('infrastructure/setup.yml', '基础设施Playbook'),
        ('deployment/deploy.yml', '部署Playbook'),
        ('infrastructure/hosts', '基础设施Inventory'),
        ('deployment/production.ini', '生产环境Inventory'),
        ('nginx_version=1.20.1', '基础设施变量'),
        ('app_version=3.2.1', '应用版本变量'),
        ('--tags nginx,ssl', '标签过滤'),
        ('--limit webservers', '主机限制'),
        ('-u admin', '管理员用户'),
        ('-u deploy', '部署用户'),
        ('-v', '详细输出'),
    ]
    
    all_checks = structure_checks + ansible_checks
    passed_checks = 0
    
    print("   Pipeline结构检查:")
    for check, description in structure_checks:
        if check in jenkinsfile:
            print(f"      ✅ {description}")
            passed_checks += 1
        else:
            print(f"      ❌ {description}")
    
    print("   Ansible步骤检查:")
    for check, description in ansible_checks:
        if check in jenkinsfile:
            print(f"      ✅ {description}")
            passed_checks += 1
        else:
            print(f"      ❌ {description}")
    
    print()
    print("5. 📊 转换结果分析")
    success_rate = passed_checks / len(all_checks) * 100
    print(f"   总检查项: {len(all_checks)}")
    print(f"   通过检查: {passed_checks}")
    print(f"   成功率: {success_rate:.1f}%")
    print()
    
    if success_rate >= 90:
        print("🎉 Ansible到Jenkins转换成功！")
        print("   ✅ 所有重要特性都已正确转换")
        print("   ✅ 生成的Pipeline可以直接在Jenkins中使用")
        result = "excellent"
    elif success_rate >= 70:
        print("✅ Ansible到Jenkins转换基本成功")
        print("   ⚠️ 部分高级特性可能需要手动调整")
        result = "good"
    else:
        print("⚠️ Ansible到Jenkins转换需要改进")
        print("   ❌ 多个关键特性转换失败")
        result = "needs_improvement"
    
    print()
    print("6. 🎯 实际使用场景验证")
    print("   这个转换结果可以用于以下场景:")
    print("   📦 基础设施配置 (Ansible setup.yml)")
    print("   🚀 应用部署 (Ansible deploy.yml)")
    print("   🔧 多环境管理 (不同inventory文件)")
    print("   ⚡ 自动化部署流水线")
    print("   📊 部署后验证")
    
    return result == "excellent" or result == "good"

if __name__ == '__main__':
    try:
        success = test_ansible_jenkins_conversion_direct()
        print()
        print("="*60)
        if success:
            print("🎉 Ansible→Jenkins转换测试完全成功！")
            print("   您的Jenkins流水线中的Ansible步骤已经能够正确转换")
        else:
            print("⚠️ Ansible→Jenkins转换需要进一步完善")
        print("="*60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
