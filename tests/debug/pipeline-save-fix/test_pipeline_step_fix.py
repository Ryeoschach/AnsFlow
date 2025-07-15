#!/usr/bin/env python3
"""
验证流水线步骤保存修复
"""

import os
import sys
import django
import json

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from pipelines.serializers import PipelineSerializer
from django.contrib.auth.models import User
from django.test import RequestFactory

def test_pipeline_step_preservation():
    """测试流水线步骤保存修复"""
    
    print("🔍 测试流水线步骤保存修复")
    print("=" * 50)
    
    # 获取测试流水线
    pipeline = Pipeline.objects.first()
    if not pipeline:
        print("❌ 没有找到测试流水线")
        return
    
    # 确保有步骤
    if not pipeline.steps.exists():
        # 创建测试步骤
        PipelineStep.objects.create(
            pipeline=pipeline,
            name='测试步骤',
            step_type='custom',
            order=1,
            command='echo "test"'
        )
    
    original_steps_count = pipeline.steps.count()
    print(f"📋 流水线: {pipeline.name}")
    print(f"📝 原始步骤数量: {original_steps_count}")
    
    # 创建请求工厂
    factory = RequestFactory()
    user = User.objects.first()
    
    # 测试1: 模拟"编辑流水线"请求 - 不包含steps字段
    print(f"\n🧪 测试1: 编辑流水线（不包含steps）")
    
    request = factory.put(f'/pipelines/{pipeline.id}/')
    request.user = user
    
    # 模拟"编辑流水线"的请求数据
    request.data = {
        'name': pipeline.name + ' (编辑)',
        'description': 'Updated description',
        'execution_mode': 'local'
    }
    
    context = {'request': request}
    
    serializer = PipelineSerializer(
        pipeline, 
        data=request.data, 
        context=context,
        partial=True
    )
    
    if serializer.is_valid():
        updated_pipeline = serializer.save()
        after_steps_count = updated_pipeline.steps.count()
        
        print(f"✅ 验证通过")
        print(f"📊 更新后步骤数量: {after_steps_count}")
        
        if after_steps_count == original_steps_count:
            print("✅ 成功: 编辑流水线没有删除步骤")
        else:
            print("❌ 失败: 编辑流水线删除了步骤")
            return False
    else:
        print(f"❌ 序列化器验证失败: {serializer.errors}")
        return False
    
    # 测试2: 模拟"拖拽式配置"请求 - 包含steps字段
    print(f"\n🧪 测试2: 拖拽式配置（包含steps）")
    
    request2 = factory.put(f'/pipelines/{pipeline.id}/')
    request2.user = user
    
    # 模拟"拖拽式配置"的请求数据，包含steps字段
    request2.data = {
        'name': pipeline.name + ' (拖拽)',
        'description': 'Updated via drag config',
        'execution_mode': 'local',
        'steps': [
            {
                'name': '新步骤1',
                'step_type': 'custom',
                'description': '新建步骤1',
                'parameters': {},
                'order': 1
            },
            {
                'name': '新步骤2',
                'step_type': 'custom', 
                'description': '新建步骤2',
                'parameters': {},
                'order': 2
            }
        ]
    }
    
    context2 = {'request': request2}
    
    serializer2 = PipelineSerializer(
        pipeline, 
        data=request2.data, 
        context=context2,
        partial=True
    )
    
    if serializer2.is_valid():
        updated_pipeline2 = serializer2.save()
        final_steps_count = updated_pipeline2.steps.count()
        
        print(f"✅ 验证通过")
        print(f"📊 最终步骤数量: {final_steps_count}")
        
        if final_steps_count == 2:
            print("✅ 成功: 拖拽式配置正确更新了步骤")
        else:
            print("❌ 失败: 拖拽式配置没有正确更新步骤")
            return False
    else:
        print(f"❌ 序列化器验证失败: {serializer2.errors}")
        return False
    
    print(f"\n🎉 所有测试通过！修复成功！")
    return True

if __name__ == '__main__':
    success = test_pipeline_step_preservation()
    if not success:
        sys.exit(1)
