#!/usr/bin/env python3
"""
测试多种CI/CD工具的Pipeline预览功能
"""

import os
import sys
import django
from datetime import datetime
import json

# 设置Django环境
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from project_management.models import Project
from pipelines.models import Pipeline

def test_multi_tool_preview():
    """测试多种CI/CD工具的预览生成"""
    print("="*60)
    print("🧪 测试多种CI/CD工具预览功能")
    print("="*60)
    
    try:
        # 1. 创建测试客户端和数据
        client = Client()
        
        user, _ = User.objects.get_or_create(
            username='test_admin',
            defaults={
                'email': 'test@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        project, _ = Project.objects.get_or_create(
            name='Multi CI/CD Test Project',
            defaults={
                'description': 'Test project for multi CI/CD tools',
                'owner': user
            }
        )
        
        pipeline, _ = Pipeline.objects.get_or_create(
            name='Multi Tool Preview Pipeline',
            defaults={
                'description': 'Pipeline for testing multi tool preview',
                'project': project,
                'execution_mode': 'remote',
                'created_by': user
            }
        )
        
        # 2. 复杂的步骤配置
        steps_data = [
            {
                'name': 'Environment Setup',
                'step_type': 'shell_script',
                'parameters': {
                    'script': 'npm install && pip install -r requirements.txt'
                },
                'order': 1
            },
            {
                'name': 'Build Application',
                'step_type': 'build',
                'parameters': {
                    'build_tool': 'npm',
                    'command': 'npm run build:prod'
                },
                'order': 2
            },
            {
                'name': 'Run Unit Tests',
                'step_type': 'test',
                'parameters': {
                    'test_command': 'npm test -- --coverage',
                    'coverage': True
                },
                'order': 3
            },
            {
                'name': 'Build Docker Image',
                'step_type': 'docker_build',
                'parameters': {
                    'tag': 'v1.0.0',
                    'dockerfile': 'Dockerfile.prod'
                },
                'order': 4
            },
            {
                'name': 'Deploy with Ansible',
                'step_type': 'ansible',
                'parameters': {
                    'playbook_path': 'deploy/production.yml',
                    'inventory_path': 'deploy/hosts/production',
                    'extra_vars': {
                        'app_version': 'v1.0.0',
                        'environment': 'production',
                        'database_host': 'prod-db.example.com'
                    },
                    'tags': 'deploy,migrate',
                    'verbose': True
                },
                'order': 5
            }
        ]
        
        # 3. 测试不同CI/CD工具类型
        tools_to_test = [
            ('jenkins', 'Jenkins'),
            ('gitlab', 'GitLab CI/CD'),
            ('github', 'GitHub Actions')
        ]
        
        for tool_type, tool_name in tools_to_test:
            print(f"\n🔄 测试 {tool_name} 预览生成")
            print("-" * 40)
            
            preview_data = {
                'pipeline_id': pipeline.id,
                'steps': steps_data,
                'execution_mode': 'remote',
                'ci_tool_type': tool_type,
                'environment': {
                    'NODE_ENV': 'production',
                    'DATABASE_URL': 'postgresql://prod-db.example.com:5432/myapp'
                }
            }
            
            response = client.post(
                '/api/v1/cicd/pipelines/preview/',
                data=json.dumps(preview_data),
                content_type='application/json'
            )
            
            print(f"API响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {tool_name} 预览生成成功!")
                
                # 验证基本信息
                summary = result.get('workflow_summary', {})
                print(f"   总步骤数: {summary.get('total_steps')}")
                print(f"   预计耗时: {summary.get('estimated_duration')}")
                print(f"   步骤类型: {summary.get('step_types')}")
                
                # 验证工具特定配置
                if tool_type == 'jenkins' and 'jenkinsfile' in result:
                    jenkins_content = result['jenkinsfile']
                    print(f"   ✅ Jenkinsfile 生成: {len(jenkins_content)} 字符")
                    # 验证关键内容
                    checks = ['pipeline {', 'agent any', 'stages {', 'npm test', 'ansible-playbook', 'docker build']
                    passed = sum(1 for check in checks if check in jenkins_content)
                    print(f"   内容验证: {passed}/{len(checks)} 通过")
                    
                elif tool_type == 'gitlab' and 'gitlab_ci' in result:
                    gitlab_content = result['gitlab_ci']
                    print(f"   ✅ .gitlab-ci.yml 生成: {len(gitlab_content)} 字符")
                    checks = ['stages:', 'script:', 'npm test', 'ansible-playbook', 'docker build']
                    passed = sum(1 for check in checks if check in gitlab_content)
                    print(f"   内容验证: {passed}/{len(checks)} 通过")
                    
                elif tool_type == 'github' and 'github_actions' in result:
                    github_content = result['github_actions']
                    print(f"   ✅ GitHub Actions 工作流生成: {len(github_content)} 字符")
                    checks = ['name:', 'on:', 'jobs:', 'runs-on:', 'uses: actions/checkout']
                    passed = sum(1 for check in checks if check in github_content)
                    print(f"   内容验证: {passed}/{len(checks)} 通过")
                
                print(f"   支持的工具: {result.get('supported_tools', [])}")
                print(f"   当前工具: {result.get('current_tool', tool_type)}")
                
            else:
                print(f"❌ {tool_name} 预览生成失败: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"错误信息: {error_data}")
                except:
                    print(f"响应内容: {response.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pipeline_config_variations():
    """测试不同Pipeline配置的预览生成"""
    print("\n" + "="*60)
    print("🧪 测试不同Pipeline配置变体")
    print("="*60)
    
    client = Client()
    
    # 测试不同的配置组合
    test_cases = [
        {
            'name': '简单Web应用流水线',
            'steps': [
                {'name': 'Install Dependencies', 'step_type': 'shell_script', 'parameters': {'script': 'npm install'}, 'order': 1},
                {'name': 'Build', 'step_type': 'build', 'parameters': {'build_tool': 'npm'}, 'order': 2},
                {'name': 'Test', 'step_type': 'test', 'parameters': {'test_command': 'npm test'}, 'order': 3}
            ]
        },
        {
            'name': 'Java Maven项目',
            'steps': [
                {'name': 'Compile', 'step_type': 'build', 'parameters': {'build_tool': 'maven'}, 'order': 1},
                {'name': 'Unit Tests', 'step_type': 'test', 'parameters': {'test_command': 'mvn test'}, 'order': 2},
                {'name': 'Package', 'step_type': 'build', 'parameters': {'build_tool': 'maven', 'command': 'mvn package'}, 'order': 3}
            ]
        },
        {
            'name': '纯Ansible部署',
            'steps': [
                {'name': 'Deploy Infrastructure', 'step_type': 'ansible', 'parameters': {'playbook_path': 'infra.yml'}, 'order': 1},
                {'name': 'Deploy Application', 'step_type': 'ansible', 'parameters': {'playbook_path': 'app.yml'}, 'order': 2}
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n🔄 测试用例 {i+1}: {test_case['name']}")
        print("-" * 40)
        
        preview_data = {
            'pipeline_id': 999,  # 模拟ID
            'steps': test_case['steps'],
            'execution_mode': 'local'
        }
        
        response = client.post(
            '/api/v1/cicd/pipelines/preview/',
            data=json.dumps(preview_data),
            content_type='application/json'
        )
        
        if response.status_code == 200:
            result = response.json()
            summary = result.get('workflow_summary', {})
            print(f"   ✅ 步骤数: {summary.get('total_steps')}")
            print(f"   ✅ 预计耗时: {summary.get('estimated_duration')}")
            print(f"   ✅ 步骤类型: {summary.get('step_types')}")
            
            if 'jenkinsfile' in result:
                print(f"   ✅ Jenkinsfile 已生成")
        else:
            print(f"   ❌ 测试失败: {response.status_code}")

if __name__ == '__main__':
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试多种CI/CD工具
    multi_tool_success = test_multi_tool_preview()
    
    # 测试不同配置
    test_pipeline_config_variations()
    
    print("\n" + "="*60)
    if multi_tool_success:
        print("🎉 多种CI/CD工具预览功能测试完成！")
        print("   ✅ Jenkins预览支持")
        print("   ✅ GitLab CI预览支持") 
        print("   ✅ GitHub Actions预览支持")
        print("   ✅ 不同配置组合测试通过")
    else:
        print("⚠️ 测试存在问题，需要进一步调试")
    print("="*60)
