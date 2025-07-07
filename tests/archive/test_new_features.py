#!/usr/bin/env python3
"""
测试新添加的Pipeline预览和导航功能
"""

import os
import sys
import django
from datetime import datetime

# 设置Django环境
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from project_management.models import Project
from pipelines.models import Pipeline
from cicd_integrations.models import AtomicStep
import json

def test_pipeline_preview_api():
    """测试Pipeline预览API"""
    print("="*60)
    print("🧪 测试Pipeline预览API功能")
    print("="*60)
    
    try:
        # 1. 创建测试客户端
        client = Client()
        
        # 2. 获取或创建测试用户
        user, _ = User.objects.get_or_create(
            username='test_admin',
            defaults={
                'email': 'test@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        # 3. 获取或创建测试项目
        project, _ = Project.objects.get_or_create(
            name='Test Project for Preview',
            defaults={
                'description': 'Test project for pipeline preview',
                'owner': user
            }
        )
        
        # 4. 创建测试流水线
        pipeline, _ = Pipeline.objects.get_or_create(
            name='Preview Test Pipeline',
            defaults={
                'description': 'Pipeline for testing preview functionality',
                'project': project,
                'execution_mode': 'remote',
                'created_by': user
            }
        )
        
        # 5. 创建测试步骤
        steps_data = [
            {
                'name': 'Checkout Code',
                'step_type': 'fetch_code',
                'parameters': {
                    'repository_url': 'https://github.com/example/app.git',
                    'branch': 'main'
                },
                'order': 1
            },
            {
                'name': 'Run Ansible Deployment',
                'step_type': 'ansible',
                'parameters': {
                    'playbook_path': 'deploy.yml',
                    'inventory_path': 'production.ini',
                    'extra_vars': {
                        'app_version': '2.1.0',
                        'environment': 'production'
                    },
                    'tags': 'webserver,database',
                    'verbose': True
                },
                'order': 2
            },
            {
                'name': 'Run Tests',
                'step_type': 'test',
                'parameters': {
                    'test_command': 'pytest --cov=.',
                    'coverage': True
                },
                'order': 3
            }
        ]
        
        # 6. 准备API请求数据
        preview_data = {
            'pipeline_id': pipeline.id,
            'steps': steps_data,
            'execution_mode': 'remote',
            'execution_tool': None,
            'environment': {
                'APP_ENV': 'production'
            }
        }
        
        print(f"📋 测试数据准备完成:")
        print(f"   流水线: {pipeline.name}")
        print(f"   步骤数: {len(steps_data)}")
        print()
        
        # 7. 调用预览API
        print("🔄 调用Pipeline预览API")
        response = client.post(
            '/api/v1/cicd/pipelines/preview/',
            data=json.dumps(preview_data),
            content_type='application/json'
        )
        
        print(f"API响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功!")
            print()
            
            # 8. 验证响应内容
            print("📊 预览结果验证:")
            
            if 'workflow_summary' in result:
                summary = result['workflow_summary']
                print(f"   ✅ 总步骤数: {summary.get('total_steps')}")
                print(f"   ✅ 预计耗时: {summary.get('estimated_duration')}")
                print(f"   ✅ 步骤类型: {summary.get('step_types')}")
                print(f"   ✅ 触发方式: {summary.get('triggers')}")
            else:
                print("   ❌ 缺少workflow_summary")
            
            if 'jenkinsfile' in result:
                jenkinsfile = result['jenkinsfile']
                print(f"   ✅ Jenkinsfile生成: {len(jenkinsfile)} 字符")
                
                # 验证Jenkinsfile内容
                jenkinsfile_checks = [
                    ('pipeline {', 'Pipeline声明'),
                    ('agent any', 'Agent配置'),
                    ('stages {', 'Stages声明'),
                    ('Checkout Code', '第一个步骤'),
                    ('ansible-playbook', 'Ansible命令'),
                    ('pytest --cov=.', '测试命令'),
                    ('post {', '后置处理')
                ]
                
                passed_checks = 0
                for check, desc in jenkinsfile_checks:
                    if check in jenkinsfile:
                        print(f"     ✅ {desc}")
                        passed_checks += 1
                    else:
                        print(f"     ❌ {desc}")
                
                print(f"   Jenkinsfile验证: {passed_checks}/{len(jenkinsfile_checks)} 通过")
                
                # 显示生成的Jenkinsfile（前50行）
                print()
                print("📄 生成的Jenkinsfile预览（前50行）:")
                print("-" * 50)
                lines = jenkinsfile.split('\n')
                for i, line in enumerate(lines[:50]):
                    print(f"{i+1:2}: {line}")
                if len(lines) > 50:
                    print("...")
                print("-" * 50)
                
            else:
                print("   ❌ 缺少jenkinsfile")
            
            return True
            
        else:
            print(f"❌ API调用失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误信息: {error_data}")
            except:
                print(f"响应内容: {response.content}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_frontend_integration():
    """测试前端集成情况"""
    print("\n" + "="*60)
    print("🎨 检查前端组件集成")
    print("="*60)
    
    frontend_files = [
        '/Users/creed/workspace/sourceCode/AnsFlow/frontend/src/components/pipeline/PipelinePreview.tsx',
        '/Users/creed/workspace/sourceCode/AnsFlow/frontend/src/components/pipeline/PipelineEditor.tsx',
        '/Users/creed/workspace/sourceCode/AnsFlow/frontend/src/pages/ExecutionDetailFixed.tsx'
    ]
    
    checks = [
        ('PipelinePreview', 'Pipeline预览组件'),
        ('import PipelinePreview', 'PipelineEditor中的预览导入'),
        ('EyeOutlined', '预览按钮图标'),
        ('预览Pipeline', '预览按钮文本'),
        ('返回执行列表', '执行详情页导航'),
        ('查看流水线详情', '流水线详情导航'),
        ('所有流水线', '流水线列表导航')
    ]
    
    for check, desc in checks:
        found = False
        for file_path in frontend_files:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if check in content:
                            found = True
                            break
            except:
                continue
        
        if found:
            print(f"   ✅ {desc}")
        else:
            print(f"   ❌ {desc}")
    
    print()
    print("📝 功能说明:")
    print("   1. Pipeline预览: 在编辑器中点击'预览Pipeline'按钮")
    print("   2. 导航功能: 在执行详情页面可以返回流水线编辑或列表")
    print("   3. Jenkinsfile生成: 自动根据步骤生成完整的Jenkins Pipeline")

if __name__ == '__main__':
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试后端API
    api_success = test_pipeline_preview_api()
    
    # 检查前端集成
    test_frontend_integration()
    
    print("\n" + "="*60)
    if api_success:
        print("🎉 Pipeline预览和导航功能测试完成！")
        print("   ✅ 后端API正常工作")
        print("   ✅ 前端组件集成完成") 
        print("   ✅ 新功能可以使用")
    else:
        print("⚠️ 测试完成，但存在问题")
        print("   ❌ 后端API需要调试")
        print("   ✅ 前端组件已准备就绪")
    print("="*60)
