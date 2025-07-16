#!/usr/bin/env python
"""
修复本地执行器测试流水线1的PipelineStep命令配置和并行组配置
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from cicd_integrations.models import AtomicStep

def fix_pipeline_steps():
    """修复PipelineStep的命令配置和并行组"""
    
    # 找到流水线
    pipeline = Pipeline.objects.filter(name='本地执行器测试流水线1').first()
    if not pipeline:
        print('❌ 未找到流水线')
        return
    
    print(f'✅ 找到流水线: {pipeline.name} (ID: {pipeline.id})')
    
    # 获取AtomicStep和PipelineStep
    atomic_steps = list(pipeline.atomic_steps.all().order_by('order'))
    pipeline_steps = list(pipeline.steps.all().order_by('order'))
    
    print(f'📊 AtomicStep数量: {len(atomic_steps)}')
    print(f'📊 PipelineStep数量: {len(pipeline_steps)}')
    
    # 检查数量是否匹配
    if len(atomic_steps) != len(pipeline_steps):
        print('⚠️ AtomicStep和PipelineStep数量不匹配')
        return
    
    # 修复PipelineStep的command字段，从对应的AtomicStep复制命令
    print('\\n=== 修复PipelineStep命令配置 ===')
    updated_count = 0
    
    for i, (atomic_step, pipeline_step) in enumerate(zip(atomic_steps, pipeline_steps)):
        # 从AtomicStep的parameters中获取命令
        command = atomic_step.parameters.get('command', '')
        
        if command and not pipeline_step.command:
            print(f'修复步骤 {pipeline_step.order}: {pipeline_step.name}')
            print(f'  旧命令: "{pipeline_step.command}"')
            print(f'  新命令: "{command}"')
            
            pipeline_step.command = command
            pipeline_step.save()
            updated_count += 1
        elif command and pipeline_step.command != command:
            print(f'更新步骤 {pipeline_step.order}: {pipeline_step.name}')
            print(f'  旧命令: "{pipeline_step.command}"')
            print(f'  新命令: "{command}"')
            
            pipeline_step.command = command
            pipeline_step.save()
            updated_count += 1
    
    print(f'✅ 更新了 {updated_count} 个PipelineStep的命令配置')
    
    # 添加并行组配置来测试并行功能
    print('\\n=== 添加并行组配置 ===')
    
    # 设计并行组：步骤2和4在同一个并行组
    parallel_config = {
        2: 'test_parallel_group',  # 步骤2
        4: 'test_parallel_group',  # 步骤4
    }
    
    parallel_updated = 0
    for pipeline_step in pipeline_steps:
        if pipeline_step.order in parallel_config:
            new_group = parallel_config[pipeline_step.order]
            if pipeline_step.parallel_group != new_group:
                print(f'设置步骤 {pipeline_step.order} ({pipeline_step.name}) 的并行组: {new_group}')
                pipeline_step.parallel_group = new_group
                pipeline_step.save()
                parallel_updated += 1
    
    print(f'✅ 更新了 {parallel_updated} 个PipelineStep的并行组配置')
    
    # 验证修复结果
    print('\\n=== 验证修复结果 ===')
    pipeline_steps = list(pipeline.steps.all().order_by('order'))
    
    empty_commands = [step for step in pipeline_steps if not step.command]
    if empty_commands:
        print(f'⚠️ 仍有 {len(empty_commands)} 个步骤缺少命令配置')
    else:
        print('✅ 所有PipelineStep都有命令配置')
    
    parallel_groups = set()
    for step in pipeline_steps:
        if step.parallel_group:
            parallel_groups.add(step.parallel_group)
    
    print(f'📊 检测到 {len(parallel_groups)} 个并行组: {parallel_groups}')
    
    # 显示最终配置
    print('\\n=== 最终配置 ===')
    for step in pipeline_steps:
        parallel_info = f" (并行组: {step.parallel_group})" if step.parallel_group else ""
        print(f'步骤 {step.order}: {step.name}{parallel_info}')
        print(f'  命令: {step.command}')

if __name__ == '__main__':
    fix_pipeline_steps()
