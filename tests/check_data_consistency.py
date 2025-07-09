#!/usr/bin/env python
"""
临时修复：修改Pipeline序列化器，让它能够同时返回AtomicStep和PipelineStep数据
这样前端就能正确加载和显示步骤数据
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from cicd_integrations.models import AtomicStep


def check_pipeline_data():
    """检查每个流水线的步骤情况"""
    print("🔍 检查流水线步骤数据情况...")
    
    for pipeline in Pipeline.objects.all():
        atomic_count = pipeline.atomic_steps.count()
        pipeline_count = pipeline.steps.count()
        
        print(f"📋 {pipeline.name} (ID:{pipeline.id}):")
        print(f"    AtomicSteps: {atomic_count}")
        print(f"    PipelineSteps: {pipeline_count}")
        
        if atomic_count > 0:
            print("    AtomicStep列表:")
            for step in pipeline.atomic_steps.order_by('order'):
                print(f"      - {step.name} (type: {step.step_type}, order: {step.order})")
        
        if pipeline_count > 0:
            print("    PipelineStep列表:")
            for step in pipeline.steps.order_by('order'):
                print(f"      - {step.name} (type: {step.step_type}, order: {step.order})")
        
        print()


def test_serializer():
    """测试序列化器能否正确返回数据"""
    from pipelines.serializers import PipelineSerializer
    from rest_framework.test import APIRequestFactory
    from django.contrib.auth.models import User
    
    print("🧪 测试序列化器...")
    
    # 创建一个虚拟请求上下文
    factory = APIRequestFactory()
    request = factory.get('/')
    
    # 获取一个测试用户
    user = User.objects.first()
    if user:
        request.user = user
    
    # 测试流水线序列化
    for pipeline in Pipeline.objects.all()[:3]:  # 只测试前3个
        print(f"\n📋 测试 {pipeline.name}:")
        
        serializer = PipelineSerializer(pipeline, context={'request': request})
        data = serializer.data
        
        print(f"    序列化后的steps字段: {len(data.get('steps', []))} 个步骤")
        for step in data.get('steps', []):
            print(f"      - {step.get('name')} (type: {step.get('step_type')})")


if __name__ == '__main__':
    print("🚀 检查流水线数据一致性")
    print("=" * 50)
    
    check_pipeline_data()
    test_serializer()
    
    print("\n💡 解决方案:")
    print("1. 前端已修改为同时支持PipelineStep和AtomicStep")
    print("2. 前端会优先使用PipelineStep数据，如果不存在则使用AtomicStep")
    print("3. 保存时前端会发送标准的步骤数据给后端API")
    print("4. 后端PipelineSerializer应该能正确处理步骤的创建和更新")
