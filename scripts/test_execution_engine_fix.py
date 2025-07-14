#!/usr/bin/env python3
"""
测试修复后的执行引擎并行组处理
"""

import sys
import os
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')

import django
django.setup()

from pipelines.models import Pipeline
from cicd_integrations.services import UnifiedCICDEngine
from cicd_integrations.models import PipelineExecution

def test_execution_engine_parallel_groups():
    """测试修复后的执行引擎是否能正确处理并行组"""
    print("🔍 测试修复后的执行引擎并行组处理")
    print("=" * 60)
    
    pipeline_id = 2
    
    # 获取Pipeline对象
    pipeline = Pipeline.objects.get(id=pipeline_id)
    
    print("📋 1. 检查Pipeline步骤数据:")
    steps = pipeline.steps.all().order_by('order')
    print(f"  总步骤数: {len(steps)}")
    
    parallel_groups = set()
    for step in steps:
        pg = step.parallel_group or ''
        if pg:
            parallel_groups.add(pg)
        print(f"    步骤: {step.name}, order: {step.order}, parallel_group: '{pg}'")
    
    print(f"  并行组数: {len(parallel_groups)}")
    
    # 测试执行引擎
    print("\n📋 2. 测试执行引擎的流水线定义构建:")
    try:
        engine = UnifiedCICDEngine()
        
        # 创建一个模拟的执行记录
        class MockExecution:
            def __init__(self, pipeline):
                self.pipeline = pipeline
                self.parameters = {}
                self.cicd_tool = None
        
        mock_execution = MockExecution(pipeline)
        
        # 调用流水线定义构建方法
        pipeline_definition = engine._build_pipeline_definition_from_atomic_steps(mock_execution)
        
        print(f"  流水线定义包含 {len(pipeline_definition['steps'])} 个步骤")
        
        # 检查并行组信息
        definition_parallel_groups = set()
        for step in pipeline_definition['steps']:
            pg = step.get('parallel_group', '')
            if pg:
                definition_parallel_groups.add(pg)
            print(f"    定义步骤: {step['name']}, parallel_group: '{pg}'")
        
        print(f"  定义中的并行组数: {len(definition_parallel_groups)}")
        
        # 验证
        if len(definition_parallel_groups) == len(parallel_groups) and definition_parallel_groups == parallel_groups:
            print("  ✅ 执行引擎正确保留了并行组信息!")
            return True
        else:
            print("  ❌ 执行引擎未正确保留并行组信息")
            print(f"    原始并行组: {parallel_groups}")
            print(f"    定义并行组: {definition_parallel_groups}")
            return False
            
    except Exception as e:
        print(f"  ❌ 执行引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    success = test_execution_engine_parallel_groups()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 执行引擎修复成功!")
        print("🎯 现在实际执行也能正确处理并行组了")
        print("\n💡 修复内容:")
        print("  - 执行引擎现在使用 PipelineStep 而不是 AtomicStep")
        print("  - 并行组信息能正确传递到实际执行中")
        print("  - 预览和实际执行使用相同的数据模型")
    else:
        print("❌ 执行引擎仍有问题需要解决")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
