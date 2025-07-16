#!/usr/bin/env python
"""
调试PipelineStep并行组配置
"""
import os
import django
from django.conf import settings

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from cicd_integrations.models import AtomicStep
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_pipeline_parallel_groups():
    """调试流水线的并行组配置"""
    
    # 查找所有流水线，按创建时间排序
    pipelines = Pipeline.objects.all().order_by('-created_at')[:5]
    
    print("=== 最近的流水线 ===")
    for pipeline in pipelines:
        print(f"流水线: {pipeline.name} (ID: {pipeline.id})")
        
        # 检查PipelineStep
        pipeline_steps = pipeline.steps.all().order_by('order')
        print(f"  PipelineStep数量: {pipeline_steps.count()}")
        
        for step in pipeline_steps:
            parallel_info = f" -> 并行组: '{step.parallel_group}'" if step.parallel_group else " -> 无并行组"
            print(f"    步骤 {step.order}: {step.name}{parallel_info}")
        
        # 检查AtomicStep
        atomic_steps = pipeline.atomic_steps.all().order_by('order')
        print(f"  AtomicStep数量: {atomic_steps.count()}")
        
        for step in atomic_steps:
            parallel_info = f" -> 并行组: '{step.parallel_group}'" if step.parallel_group else " -> 无并行组"
            print(f"    步骤 {step.order}: {step.name}{parallel_info}")
        
        # 模拟并行组检测
        parallel_groups = set()
        
        # 检查PipelineStep的并行组
        for step in pipeline_steps:
            if step.parallel_group:
                parallel_groups.add(step.parallel_group)
                print(f"  🔍 PipelineStep检测到并行组: '{step.parallel_group}'")
        
        # 检查AtomicStep的并行组
        for step in atomic_steps:
            if step.parallel_group:
                parallel_groups.add(step.parallel_group)
                print(f"  🔍 AtomicStep检测到并行组: '{step.parallel_group}'")
        
        print(f"  📊 总并行组数: {len(parallel_groups)}")
        if parallel_groups:
            print(f"  📋 并行组列表: {parallel_groups}")
        
        print("-" * 50)

if __name__ == '__main__':
    debug_pipeline_parallel_groups()
