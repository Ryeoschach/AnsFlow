#!/usr/bin/env python
"""
检查PipelineStep表的实际数据
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from cicd_integrations.models import AtomicStep


def check_pipeline_steps():
    """检查PipelineStep表的实际数据"""
    print("🔍 检查PipelineStep表数据...")
    
    # 检查所有PipelineStep
    all_pipeline_steps = PipelineStep.objects.all()
    print(f"📊 总共有 {all_pipeline_steps.count()} 个PipelineStep")
    
    for step in all_pipeline_steps:
        print(f"  - ID:{step.id}, Pipeline:{step.pipeline.name} (ID:{step.pipeline.id}), Name:{step.name}, Order:{step.order}")
    
    print("\n🔍 按流水线分组的PipelineStep:")
    for pipeline in Pipeline.objects.all():
        steps = PipelineStep.objects.filter(pipeline=pipeline)
        print(f"📋 {pipeline.name} (ID:{pipeline.id}): {steps.count()} 个PipelineStep")
        for step in steps:
            print(f"    - {step.name} (order: {step.order})")


if __name__ == '__main__':
    check_pipeline_steps()
