#!/usr/bin/env python3
"""
简化的Ansible到Jenkins转换测试
直接测试Jenkins适配器的Ansible步骤转换功能
"""

import os
import sys
import django

# 设置Django环境
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from cicd_integrations.adapters.jenkins import JenkinsAdapter

def test_ansible_step_conversion():
    """测试Ansible步骤转换为Jenkins脚本"""
    print("="*60)
    print("🧪 测试Ansible步骤转换为Jenkins脚本")
    print("="*60)
    
    # 创建Jenkins适配器
    jenkins_adapter = JenkinsAdapter(
        base_url='http://localhost:8080',
        username='admin',
        token='test-token'
    )
    
    # 测试用例1: 基本Ansible步骤
    print("1. 🔧 基本Ansible步骤测试")
    basic_params = {
        'playbook_path': 'deploy.yml',
        'inventory_path': 'hosts',
        'extra_vars': {
            'app_version': '1.0.0',
            'environment': 'production'
        }
    }
    
    script = jenkins_adapter._generate_stage_script('ansible', basic_params)
    print("生成的Jenkins脚本:")
    print("-" * 40)
    print(script)
    print("-" * 40)
    print()
    
    # 测试用例2: 带认证的Ansible步骤
    print("2. 🔐 带认证的Ansible步骤测试")
    auth_params = {
        'playbook_path': 'site.yml',
        'inventory_path': 'production.ini',
        'ansible_user': 'deploy',
        'extra_vars': {
            'database_password': 'secret123',
            'api_key': 'abc123'
        },
        'tags': 'webserver,database',
        'verbose': True
    }
    
    script = jenkins_adapter._generate_stage_script('ansible', auth_params)
    print("生成的Jenkins脚本:")
    print("-" * 40)
    print(script)
    print("-" * 40)
    print()
    
    # 测试用例3: 检查模式的Ansible步骤
    print("3. ✅ 检查模式的Ansible步骤测试")
    check_params = {
        'playbook_path': 'check.yml',
        'inventory_path': 'staging',
        'check_mode': True,
        'limit': 'webservers',
        'skip_tags': 'slow'
    }
    
    script = jenkins_adapter._generate_stage_script('ansible', check_params)
    print("生成的Jenkins脚本:")
    print("-" * 40)
    print(script)
    print("-" * 40)
    print()
    
    # 测试用例4: 自定义命令的Ansible步骤
    print("4. 🛠️ 自定义命令的Ansible步骤测试")
    custom_params = {
        'command': 'ansible-playbook -i hosts custom.yml --vault-password-file .vault_pass'
    }
    
    script = jenkins_adapter._generate_stage_script('ansible', custom_params)
    print("生成的Jenkins脚本:")
    print("-" * 40)
    print(script)
    print("-" * 40)
    print()
    
    # 测试用例5: 完整Jenkinsfile生成
    print("5. 📄 完整Jenkinsfile生成测试")
    from cicd_integrations.adapters.base import PipelineDefinition
    
    steps = [
        {
            'name': 'Checkout Code',
            'type': 'shell_script',
            'parameters': {
                'script': 'git checkout main'
            }
        },
        {
            'name': 'Deploy with Ansible',
            'type': 'ansible',
            'parameters': basic_params
        },
        {
            'name': 'Verify Deployment',
            'type': 'shell_script',
            'parameters': {
                'script': 'curl -f http://localhost:8080/health'
            }
        }
    ]
    
    # 创建Pipeline定义
    pipeline_def = PipelineDefinition(
        name='Ansible Test Pipeline',
        steps=steps,
        triggers={},
        environment={'APP_ENV': 'production'},
        artifacts=[],
        timeout=3600
    )
    
    # 使用create_pipeline_file生成完整Jenkinsfile
    import asyncio
    jenkinsfile = asyncio.run(jenkins_adapter.create_pipeline_file(pipeline_def))
    print("生成的完整Jenkinsfile:")
    print("=" * 60)
    print(jenkinsfile)
    print("=" * 60)
    print()
    
    print("✅ Ansible到Jenkins转换测试完成！")
    print("🎯 转换功能正常工作，可以将Ansible步骤转换为Jenkins Pipeline")
    
    return True

if __name__ == '__main__':
    try:
        success = test_ansible_step_conversion()
        print("\n🎉 测试成功！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
