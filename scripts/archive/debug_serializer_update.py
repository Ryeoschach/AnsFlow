#!/usr/bin/env python3
"""
调试脚本：测试PipelineSerializer.update方法处理steps数据
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

def test_serializer_update():
    """测试序列化器update方法"""
    
    print("=== 调试PipelineSerializer.update方法 ===")
    
    # 1. 获取测试流水线
    try:
        pipeline = Pipeline.objects.first()
        if not pipeline:
            print("❌ 没有找到测试流水线")
            return
            
        print(f"✅ 找到测试流水线: {pipeline.name} (ID: {pipeline.id})")
        print(f"   当前PipelineStep数量: {pipeline.steps.count()}")
        
    except Exception as e:
        print(f"❌ 获取流水线失败: {e}")
        return
    
    # 2. 模拟前端发送的steps数据
    mock_steps_data = [
        {
            'name': 'Test Step 1',
            'step_type': 'fetch_code',
            'description': 'Fetch source code',
            'parameters': {
                'repository_url': 'https://github.com/test/repo.git',
                'branch': 'main'
            },
            'order': 1,
            'is_active': True
        },
        {
            'name': 'Test Step 2', 
            'step_type': 'ansible',
            'description': 'Run Ansible playbook',
            'parameters': {
                'playbook_id': 1,
                'inventory_id': 1,
                'credential_id': 1,
                'extra_vars': {'env': 'production'}
            },
            'order': 2,
            'is_active': True
        }
    ]
    
    # 3. 模拟request对象
    mock_request = Mock()
    mock_request.user = User.objects.first() or User.objects.create_user('testuser')
    
    # 4. 测试序列化器
    try:
        # 创建序列化器实例
        serializer = PipelineSerializer(instance=pipeline, context={'request': mock_request})
        
        # 模拟validated_data（注意：steps不会在validated_data中）
        validated_data = {
            'name': pipeline.name,
            'description': pipeline.description,
            'steps': mock_steps_data  # 这个实际上不会被传递到update方法
        }
        
        print(f"\n🔍 测试数据:")
        print(f"   validated_data keys: {list(validated_data.keys())}")
        print(f"   steps数据条数: {len(mock_steps_data)}")
        
        # 手动测试update方法
        print(f"\n🔧 调用serializer.update()...")
        updated_pipeline = serializer.update(pipeline, validated_data)
        
        print(f"✅ update方法执行完成")
        print(f"   更新后PipelineStep数量: {updated_pipeline.steps.count()}")
        
        # 显示创建的步骤
        steps = updated_pipeline.steps.all()
        for i, step in enumerate(steps, 1):
            print(f"   步骤{i}: {step.name} ({step.step_type}) - Order: {step.order}")
            
    except Exception as e:
        print(f"❌ 序列化器update失败: {e}")
        import traceback
        traceback.print_exc()

def test_steps_field_behavior():
    """测试steps字段的行为"""
    
    print("\n=== 测试steps字段行为 ===")
    
    # 获取流水线
    pipeline = Pipeline.objects.first()
    if not pipeline:
        print("❌ 没有测试流水线")
        return
        
    # 创建序列化器
    mock_request = Mock()
    mock_request.user = User.objects.first()
    serializer = PipelineSerializer(context={'request': mock_request})
    
    # 检查Meta字段
    print(f"Meta fields: {serializer.Meta.fields}")
    print(f"Read-only fields: {serializer.Meta.read_only_fields}")
    
    # 检查declared_fields
    print(f"Declared fields: {list(serializer.declared_fields.keys())}")
    print(f"Steps field type: {type(serializer.declared_fields.get('steps', 'Not found'))}")
    
    # 测试to_internal_value
    test_data = {
        'name': 'Test Pipeline',
        'description': 'Test Description',
        'steps': [
            {'name': 'Step 1', 'step_type': 'command', 'order': 1}
        ]
    }
    
    try:
        validated = serializer.to_internal_value(test_data)
        print(f"to_internal_value result keys: {list(validated.keys())}")
    except Exception as e:
        print(f"to_internal_value error: {e}")

if __name__ == '__main__':
    test_serializer_update()
    test_steps_field_behavior()
