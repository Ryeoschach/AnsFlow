#!/usr/bin/env python3
"""
测试修复后的PipelineSerializer的steps字段处理
"""

import os
import sys
import django

# 添加项目路径
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from pipelines.serializers import PipelineSerializer
from django.contrib.auth.models import User
from rest_framework.request import Request
from unittest.mock import Mock

def test_fixed_serializer():
    """测试修复后的序列化器"""
    
    print("=== 测试修复后的PipelineSerializer ===")
    
    # 1. 获取测试流水线
    pipeline = Pipeline.objects.first()
    if not pipeline:
        print("❌ 没有找到测试流水线")
        return
        
    print(f"✅ 找到测试流水线: {pipeline.name} (ID: {pipeline.id})")
    print(f"   当前PipelineStep数量: {pipeline.steps.count()}")
    
    # 2. 模拟前端发送的完整请求数据
    request_data = {
        'name': pipeline.name,
        'description': pipeline.description,
        'project': pipeline.project_id,
        'is_active': True,
        'execution_mode': 'local',
        'steps': [
            {
                'name': 'Fetch Code',
                'step_type': 'fetch_code',
                'description': 'Pull code from repository',
                'parameters': {
                    'repository_url': 'https://github.com/test/repo.git',
                    'branch': 'main'
                },
                'order': 1,
                'is_active': True
            },
            {
                'name': 'Build Project',
                'step_type': 'build',
                'description': 'Build the project',
                'parameters': {
                    'build_command': 'npm run build',
                    'output_dir': 'dist'
                },
                'order': 2,
                'is_active': True
            },
            {
                'name': 'Deploy with Ansible',
                'step_type': 'ansible',
                'description': 'Deploy using Ansible',
                'parameters': {
                    'playbook_id': 1,
                    'inventory_id': 1,
                    'credential_id': 1,
                    'extra_vars': {'env': 'production'}
                },
                'order': 3,
                'is_active': True
            }
        ]
    }
    
    # 3. 模拟request对象
    mock_request = Mock()
    mock_request.user = User.objects.first()
    
    # 4. 测试序列化器的完整流程
    try:
        # 创建序列化器实例
        serializer = PipelineSerializer(
            instance=pipeline,
            data=request_data,
            context={'request': mock_request},
            partial=True
        )
        
        print(f"\n🔍 测试序列化器验证...")
        is_valid = serializer.is_valid()
        print(f"   is_valid: {is_valid}")
        
        if not is_valid:
            print(f"   验证错误: {serializer.errors}")
            return
            
        print(f"   validated_data keys: {list(serializer.validated_data.keys())}")
        
        if 'steps' in serializer.validated_data:
            steps_data = serializer.validated_data['steps']
            print(f"   steps数据条数: {len(steps_data)}")
            for i, step in enumerate(steps_data, 1):
                print(f"     步骤{i}: {step.get('name')} ({step.get('step_type')})")
        else:
            print("   ❌ validated_data中没有steps字段")
            return
        
        # 5. 执行update
        print(f"\n🔧 执行序列化器update...")
        updated_pipeline = serializer.save()
        
        print(f"✅ update执行成功")
        print(f"   更新后PipelineStep数量: {updated_pipeline.steps.count()}")
        
        # 6. 显示创建的步骤
        steps = updated_pipeline.steps.all().order_by('order')
        for i, step in enumerate(steps, 1):
            print(f"   步骤{i}: {step.name} ({step.step_type}) - Order: {step.order}")
            print(f"         参数: {step.ansible_parameters}")
            
        # 7. 测试序列化输出
        print(f"\n📤 测试序列化输出...")
        output_serializer = PipelineSerializer(updated_pipeline, context={'request': mock_request})
        output_data = output_serializer.data
        
        if 'steps' in output_data:
            print(f"   输出包含{len(output_data['steps'])}个步骤")
            for i, step in enumerate(output_data['steps'], 1):
                print(f"   步骤{i}: {step.get('name')} ({step.get('step_type')})")
        else:
            print("   ❌ 输出中没有steps字段")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_empty_steps():
    """测试空步骤的情况"""
    
    print("\n=== 测试空步骤情况 ===")
    
    pipeline = Pipeline.objects.first()
    if not pipeline:
        return
        
    # 清空步骤
    pipeline.steps.all().delete()
    
    request_data = {
        'name': pipeline.name,
        'steps': []  # 空步骤
    }
    
    mock_request = Mock()
    mock_request.user = User.objects.first()
    
    try:
        serializer = PipelineSerializer(
            instance=pipeline,
            data=request_data,
            context={'request': mock_request},
            partial=True
        )
        
        if serializer.is_valid():
            updated_pipeline = serializer.save()
            print(f"✅ 空步骤处理成功，步骤数量: {updated_pipeline.steps.count()}")
        else:
            print(f"❌ 空步骤验证失败: {serializer.errors}")
            
    except Exception as e:
        print(f"❌ 空步骤测试失败: {e}")

if __name__ == '__main__':
    test_fixed_serializer()
    test_empty_steps()
