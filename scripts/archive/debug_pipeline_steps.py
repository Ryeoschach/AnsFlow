#!/usr/bin/env python3
"""
调试流水线步骤保存和加载问题
"""
import os
import django
import sys
import json

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from cicd_integrations.models import AtomicStep
from django.contrib.auth.models import User

def debug_pipeline_steps():
    """调试流水线步骤问题"""
    print("🔍 调试流水线步骤保存和加载问题...")
    
    try:
        # 查找Integration Test Pipeline
        integration_pipeline = Pipeline.objects.filter(name__icontains='Integration Test').first()
        if integration_pipeline:
            print(f"✅ 找到Integration Test Pipeline: {integration_pipeline.name} (ID: {integration_pipeline.id})")
            
            # 检查关联的步骤
            atomic_steps = integration_pipeline.atomic_steps.all()
            pipeline_steps = integration_pipeline.steps.all()
            
            print(f"📊 AtomicStep数量: {atomic_steps.count()}")
            print(f"📊 PipelineStep数量: {pipeline_steps.count()}")
            
            if atomic_steps.exists():
                print("\n🔍 AtomicStep列表:")
                for step in atomic_steps:
                    print(f"  - {step.name} ({step.step_type}) - Order: {step.order}")
                    print(f"    Parameters: {step.parameters}")
                    if hasattr(step, 'ansible_playbook') and step.ansible_playbook:
                        print(f"    Ansible Playbook: {step.ansible_playbook.name}")
            
            if pipeline_steps.exists():
                print("\n🔍 PipelineStep列表:")
                for step in pipeline_steps:
                    print(f"  - {step.name} ({step.step_type}) - Order: {step.order}")
                    print(f"    Parameters: {step.ansible_parameters}")
        else:
            print("❌ 未找到Integration Test Pipeline")
            
        # 列出所有流水线及其步骤数量
        print("\n📋 所有流水线步骤统计:")
        for pipeline in Pipeline.objects.all():
            atomic_count = pipeline.atomic_steps.count()
            pipeline_step_count = pipeline.steps.count()
            print(f"  - {pipeline.name}: AtomicSteps={atomic_count}, PipelineSteps={pipeline_step_count}")
            
        # 检查数据库中是否有孤立的步骤
        orphaned_atomic = AtomicStep.objects.filter(pipeline__isnull=True)
        orphaned_pipeline = PipelineStep.objects.filter(pipeline__isnull=True)
        
        print(f"\n🔍 孤立步骤统计:")
        print(f"  - 孤立的AtomicStep: {orphaned_atomic.count()}")
        print(f"  - 孤立的PipelineStep: {orphaned_pipeline.count()}")
        
        if orphaned_atomic.exists():
            print("  孤立的AtomicStep:")
            for step in orphaned_atomic[:5]:  # 只显示前5个
                print(f"    - {step.name} ({step.step_type})")
                
        if orphaned_pipeline.exists():
            print("  孤立的PipelineStep:")
            for step in orphaned_pipeline[:5]:  # 只显示前5个
                print(f"    - {step.name} ({step.step_type})")
        
        return True
        
    except Exception as e:
        print(f"❌ 调试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = debug_pipeline_steps()
    sys.exit(0 if success else 1)
