#!/usr/bin/env python
"""
测试并行组检测功能
"""
import os
import django
from django.conf import settings

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import Pipeline
from cicd_integrations.services import UnifiedCICDEngine
from cicd_integrations.models import PipelineExecution
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_parallel_group_detection():
    """测试并行组检测功能"""
    
    # 获取流水线
    pipeline = Pipeline.objects.filter(name='前端并行组测试流水线').first()
    if not pipeline:
        print('❌ 未找到流水线')
        return
    
    print(f'✅ 找到流水线: {pipeline.name}')
    
    # 检查流水线步骤
    pipeline_steps = list(pipeline.steps.all().order_by('order'))
    atomic_steps = list(pipeline.atomic_steps.all().order_by('order'))
    
    print(f'📊 流水线步骤数据:')
    print(f'  - PipelineStep数量: {len(pipeline_steps)}')
    print(f'  - AtomicStep数量: {len(atomic_steps)}')
    
    # 显示AtomicStep详情
    if atomic_steps:
        print(f'\n🔍 AtomicStep详情:')
        parallel_groups = set()
        for step in atomic_steps:
            parallel_info = f" (并行组: {step.parallel_group})" if step.parallel_group else " (无并行组)"
            print(f'  步骤 {step.order}: {step.name}{parallel_info}')
            if step.parallel_group:
                parallel_groups.add(step.parallel_group)
        
        print(f'\n📈 检测到的并行组: {parallel_groups}')
        print(f'📊 并行组数量: {len(parallel_groups)}')
    
    # 创建一个测试执行记录
    execution = PipelineExecution.objects.create(
        pipeline=pipeline,
        status='pending',
        parameters={}
    )
    
    print(f'\n🚀 创建执行记录: {execution.id}')
    
    # 创建UnifiedCICDEngine实例并测试
    engine = UnifiedCICDEngine()
    
    print('\n=== 测试并行组检测 ===')
    try:
        # 模拟执行前的检测过程
        pipeline_steps = list(execution.pipeline.steps.all().order_by('order'))
        atomic_steps = list(execution.pipeline.atomic_steps.all().order_by('order'))
        
        print(f'本地执行: 获取到 {len(pipeline_steps)} 个PipelineStep, {len(atomic_steps)} 个AtomicStep')
        
        # 检查并行组 - 同时检查PipelineStep和AtomicStep
        parallel_groups = set()
        
        # 检查PipelineStep的并行组
        for step in pipeline_steps:
            if step.parallel_group:
                parallel_groups.add(step.parallel_group)
                print(f'PipelineStep \'{step.name}\': parallel_group = \'{step.parallel_group}\'')
        
        # 检查AtomicStep的并行组
        for step in atomic_steps:
            if step.parallel_group:
                parallel_groups.add(step.parallel_group)
                print(f'AtomicStep \'{step.name}\': parallel_group = \'{step.parallel_group}\'')
        
        print(f'本地执行: 检测到 {len(parallel_groups)} 个并行组')
        
        if parallel_groups:
            print(f'✅ 成功检测到并行组: {parallel_groups}')
            print('✅ 将使用并行执行引擎')
        else:
            print('⚠️ 未检测到并行组')
            print('⚠️ 将使用同步执行引擎')
            
    except Exception as e:
        print(f'❌ 测试过程中出错: {e}')
        import traceback
        traceback.print_exc()
    
    # 清理测试数据
    execution.delete()
    print(f'\n🧹 清理测试数据完成')

if __name__ == '__main__':
    test_parallel_group_detection()
