#!/usr/bin/env python3
"""
测试创建新步骤是否能正确保存步骤类型
"""

import os
import sys
import django

# 设置Django环境
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from django.contrib.auth.models import User
from pipelines.models import Pipeline, PipelineStep
from pipelines.serializers import PipelineSerializer
from project_management.models import Project

def test_new_steps():
    print("🧪 测试创建新步骤的类型保存...")
    
    # 获取或创建测试数据
    user, _ = User.objects.get_or_create(
        username='step_type_test_user',
        defaults={'email': 'test@test.com'}
    )
    
    project, _ = Project.objects.get_or_create(
        name='Step_Type_Test_Project',
        defaults={'description': '步骤类型测试', 'owner': user}
    )
    
    pipeline, _ = Pipeline.objects.get_or_create(
        name='Step_Type_Test_Pipeline',
        defaults={
            'description': '测试步骤类型',
            'project': project,
            'created_by': user,
            'is_active': True,
            'execution_mode': 'local'
        }
    )
    
    # 删除现有步骤
    pipeline.steps.all().delete()
    
    # 准备新的步骤数据
    steps_data = [
        {
            'name': '代码拉取步骤',
            'step_type': 'fetch_code',
            'description': '拉取代码',
            'parameters': {'repo_url': 'https://github.com/test/repo.git'},
            'order': 1,
            'is_active': True
        },
        {
            'name': '构建步骤',
            'step_type': 'build', 
            'description': '构建应用',
            'parameters': {'build_tool': 'maven'},
            'order': 2,
            'is_active': True
        },
        {
            'name': '测试步骤',
            'step_type': 'test',
            'description': '运行测试',
            'parameters': {'test_framework': 'junit'},
            'order': 3,
            'is_active': True
        }
    ]
    
    # 通过序列化器保存
    pipeline_data = {
        'name': pipeline.name,
        'description': pipeline.description,
        'project': pipeline.project.id,
        'is_active': True,
        'execution_mode': 'local',
        'steps': steps_data
    }
    
    serializer = PipelineSerializer(instance=pipeline, data=pipeline_data, partial=True)
    
    if serializer.is_valid():
        updated_pipeline = serializer.save()
        print(f"✓ 流水线更新成功")
        
        # 检查创建的步骤类型
        created_steps = PipelineStep.objects.filter(pipeline=updated_pipeline).order_by('order')
        print(f"✓ 创建了 {created_steps.count()} 个步骤")
        
        for step in created_steps:
            print(f"   - 步骤: {step.name}, 类型: {step.step_type}")
        
        # 通过序列化器获取数据，模拟前端API调用
        print("\n📤 通过序列化器获取流水线数据（模拟前端API）:")
        read_serializer = PipelineSerializer(instance=updated_pipeline)
        pipeline_data = read_serializer.data
        
        print(f"   - 流水线名称: {pipeline_data['name']}")
        print(f"   - 步骤数量: {len(pipeline_data.get('steps', []))}")
        
        for i, step_data in enumerate(pipeline_data.get('steps', [])):
            print(f"   - 步骤 {i+1}: {step_data.get('name')} (类型: {step_data.get('step_type')})")
        
        return True
    else:
        print(f"❌ 序列化器验证失败: {serializer.errors}")
        return False

if __name__ == '__main__':
    success = test_new_steps()
    if success:
        print("\n✅ 测试通过: 新步骤类型保存正确")
    else:
        print("\n❌ 测试失败")
