#!/usr/bin/env python3
"""
简化版执行引擎并行组测试
"""
import os
import sys
import django
import traceback

# 配置Django环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from cicd_integrations.models import PipelineExecution
from cicd_integrations.services import UnifiedCICDEngine


def main():
    """主测试函数"""
    print("🔍 执行引擎并行组修复验证")
    print("=" * 50)
    
    # 查找测试流水线
    pipeline = Pipeline.objects.filter(name__icontains="jenkins并行测试").first()
    if not pipeline:
        print("❌ 未找到测试流水线")
        return
    
    # 检查原始数据
    print("📋 原始流水线步骤:")
    steps = list(pipeline.steps.all().order_by('order'))
    parallel_groups = set()
    
    for step in steps:
        pg = step.parallel_group or ''
        if pg:
            parallel_groups.add(pg)
        print(f"  {step.name}: parallel_group='{pg}'")
    
    print(f"  → 原始并行组数: {len(parallel_groups)}")
    
    # 测试执行引擎
    print("\n📋 执行引擎处理结果:")
    try:
        execution = PipelineExecution.objects.create(
            pipeline=pipeline,
            status='pending',
            parameters={}
        )
        
        engine = UnifiedCICDEngine()
        pipeline_definition = engine._build_pipeline_definition_from_atomic_steps(execution)
        
        # 检查结果
        definition_parallel_groups = set()
        for step in pipeline_definition.steps:
            pg = step.get('parallel_group', '')
            if pg:
                definition_parallel_groups.add(pg)
            print(f"  {step['name']}: parallel_group='{pg}'")
        
        print(f"  → 处理后并行组数: {len(definition_parallel_groups)}")
        
        # 验证
        if parallel_groups == definition_parallel_groups:
            print("\n✅ 成功! 执行引擎正确保留了并行组信息")
            print(f"   并行组: {list(parallel_groups)}")
        else:
            print("\n❌ 失败! 并行组信息丢失")
            print(f"   期望: {parallel_groups}")
            print(f"   实际: {definition_parallel_groups}")
        
        # 清理
        execution.delete()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
