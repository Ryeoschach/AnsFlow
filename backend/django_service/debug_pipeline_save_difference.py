#!/usr/bin/env python3
"""
调试编辑流水线和拖拽式配置的保存差异
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
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

def test_pipeline_save_scenarios():
    """测试两种保存场景的差异"""
    
    print("🔍 测试编辑流水线和拖拽式配置的保存差异")
    print("=" * 80)
    
    # 获取测试流水线
    pipeline = Pipeline.objects.first()
    if not pipeline:
        print("❌ 没有找到测试流水线")
        return
    
    print(f"📋 测试流水线: {pipeline.name} (ID: {pipeline.id})")
    
    # 记录现有步骤
    original_steps = list(pipeline.steps.all())
    original_atomic_steps = list(pipeline.atomic_steps.all())
    
    print(f"📝 现有步骤数量:")
    print(f"  - PipelineStep: {len(original_steps)}")
    print(f"  - AtomicStep: {len(original_atomic_steps)}")
    
    # 创建请求上下文
    factory = APIRequestFactory()
    user = User.objects.first()
    
    # 场景1: 模拟"编辑流水线"提交 - 不包含steps字段
    print(f"\n🧪 场景1: 编辑流水线提交（不包含steps）")
    
    request = factory.put(f'/pipelines/pipelines/{pipeline.id}/')
    request.user = user
    
    # 编辑流水线表单只发送基本信息，不包含steps
    edit_form_data = {
        'name': pipeline.name + ' (编辑测试)',
        'description': pipeline.description + ' - 编辑流水线测试',
        'execution_mode': 'local',
        'is_active': True
    }
    
    print(f"📤 编辑流水线数据:")
    print(json.dumps(edit_form_data, indent=2, ensure_ascii=False))
    
    # 测试序列化器
    serializer1 = PipelineSerializer(
        pipeline, 
        data=edit_form_data, 
        context={'request': Request(request)},
        partial=True
    )
    
    if serializer1.is_valid():
        print("✅ 编辑流水线序列化器验证通过")
        
        # 保存前记录状态
        steps_before = list(pipeline.steps.all())
        atomic_steps_before = list(pipeline.atomic_steps.all())
        
        print(f"📊 保存前步骤数量: PipelineStep={len(steps_before)}, AtomicStep={len(atomic_steps_before)}")
        
        # 执行保存
        updated_pipeline = serializer1.save()
        
        # 保存后记录状态
        steps_after = list(updated_pipeline.steps.all())
        atomic_steps_after = list(updated_pipeline.atomic_steps.all())
        
        print(f"📊 保存后步骤数量: PipelineStep={len(steps_after)}, AtomicStep={len(atomic_steps_after)}")
        
        if len(steps_after) != len(steps_before) or len(atomic_steps_after) != len(atomic_steps_before):
            print("❌ 编辑流水线保存导致步骤数量变化！")
        else:
            print("✅ 编辑流水线保存没有影响步骤数量")
    else:
        print(f"❌ 编辑流水线序列化器验证失败: {serializer1.errors}")
        
    # 场景2: 模拟"拖拽式配置"提交 - 包含steps字段
    print(f"\n🧪 场景2: 拖拽式配置提交（包含steps）")
    
    # 构造包含steps的数据
    steps_data = []
    for step in pipeline.steps.all():
        steps_data.append({
            'name': step.name,
            'step_type': step.step_type,
            'description': step.description,
            'parameters': step.ansible_parameters or {},
            'order': step.order,
            'is_active': True,
            'parallel_group': step.parallel_group
        })
    
    drag_config_data = {
        'name': pipeline.name + ' (拖拽测试)',
        'description': pipeline.description + ' - 拖拽式配置测试',
        'execution_mode': 'local',
        'is_active': True,
        'steps': steps_data
    }
    
    print(f"📤 拖拽式配置数据:")
    print(f"  - 基本信息: {drag_config_data['name']}")
    print(f"  - 步骤数量: {len(steps_data)}")
    
    # 测试序列化器
    serializer2 = PipelineSerializer(
        pipeline, 
        data=drag_config_data, 
        context={'request': Request(request)},
        partial=True
    )
    
    if serializer2.is_valid():
        print("✅ 拖拽式配置序列化器验证通过")
        
        # 保存前记录状态
        steps_before2 = list(pipeline.steps.all())
        atomic_steps_before2 = list(pipeline.atomic_steps.all())
        
        print(f"📊 保存前步骤数量: PipelineStep={len(steps_before2)}, AtomicStep={len(atomic_steps_before2)}")
        
        # 执行保存
        updated_pipeline2 = serializer2.save()
        
        # 保存后记录状态
        steps_after2 = list(updated_pipeline2.steps.all())
        atomic_steps_after2 = list(updated_pipeline2.atomic_steps.all())
        
        print(f"📊 保存后步骤数量: PipelineStep={len(steps_after2)}, AtomicStep={len(atomic_steps_after2)}")
        
        if len(steps_after2) == len(steps_data) and len(atomic_steps_after2) == len(steps_data):
            print("✅ 拖拽式配置保存正确重建了步骤")
        else:
            print("❌ 拖拽式配置保存步骤数量异常")
    else:
        print(f"❌ 拖拽式配置序列化器验证失败: {serializer2.errors}")
    
    print(f"\n📋 总结:")
    print(f"  - 编辑流水线：只发送基本信息，不包含steps字段")
    print(f"  - 拖拽式配置：发送完整信息，包含steps字段")
    print(f"  - 问题根源：序列化器update方法中steps_data判断逻辑")

if __name__ == '__main__':
    test_pipeline_save_scenarios()
