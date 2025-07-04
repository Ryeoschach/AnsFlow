#!/usr/bin/env python3
"""
调试PipelineStep创建问题的脚本
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from pipelines.serializers import PipelineSerializer

def test_step_creation():
    print("🔍 调试PipelineStep创建问题...")
    
    # 获取测试流水线
    try:
        pipeline = Pipeline.objects.get(name='Integration Test Pipeline')
        print(f"✅ 找到流水线: {pipeline.name} (ID: {pipeline.id})")
    except Pipeline.DoesNotExist:
        print("❌ 未找到Integration Test Pipeline")
        return
    
    # 测试步骤数据
    step_data = {
        'name': '测试步骤',
        'step_type': 'test',
        'description': '这是一个测试步骤',
        'parameters': {'test_param': 'value'},
        'order': 1,
        'is_active': True
    }
    
    print(f"📦 步骤数据: {step_data}")
    
    # 检查PipelineStep模型的字段
    print("\n📋 PipelineStep模型字段:")
    for field in PipelineStep._meta.fields:
        print(f"  - {field.name}: {field.__class__.__name__}")
        if hasattr(field, 'choices') and field.choices:
            print(f"    可选值: {field.choices}")
    
    # 尝试手动创建步骤
    print("\n🧪 尝试手动创建PipelineStep...")
    try:
        # 调整步骤数据以匹配PipelineStep模型
        pipeline_step_data = {
            'pipeline': pipeline,
            'name': step_data['name'],
            'step_type': 'command',  # PipelineStep可能需要不同的step_type
            'description': step_data['description'],
            'order': step_data['order'],
            'ansible_parameters': step_data['parameters'],  # 使用ansible_parameters而不是parameters
        }
        
        step = PipelineStep.objects.create(**pipeline_step_data)
        print(f"✅ 成功创建步骤: {step.id} - {step.name}")
        print(f"📊 流水线步骤数量: {pipeline.steps.count()}")
        
        # 清理测试数据
        step.delete()
        print("🧹 已删除测试步骤")
        
    except Exception as e:
        print(f"❌ 创建步骤失败: {e}")
        print(f"❌ 错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    
    # 测试序列化器的update方法
    print("\n🧪 测试序列化器update方法...")
    try:
        update_data = {
            'name': pipeline.name,
            'description': 'Test pipeline',
            'steps': [step_data]
        }
        
        serializer = PipelineSerializer(pipeline, data=update_data, partial=True)
        if serializer.is_valid():
            print("✅ 序列化器验证通过")
            # 不实际保存，只测试验证
            print(f"📦 验证后的数据: {serializer.validated_data}")
        else:
            print(f"❌ 序列化器验证失败: {serializer.errors}")
            
    except Exception as e:
        print(f"❌ 序列化器测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_step_creation()
