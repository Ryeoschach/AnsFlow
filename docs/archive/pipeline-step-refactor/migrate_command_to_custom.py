#!/usr/bin/env python
"""
迁移脚本：将数据库中的command类型步骤改为custom类型
由于前端已经有了custom类型，command类型是历史遗留，应该统一为custom
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import PipelineStep


def migrate_command_to_custom():
    """将所有command类型的步骤迁移为custom类型"""
    
    print("=== 开始迁移command类型步骤为custom类型 ===")
    
    # 查找所有command类型的步骤
    command_steps = PipelineStep.objects.filter(step_type='command')
    count = command_steps.count()
    
    print(f"找到 {count} 个command类型的步骤")
    
    if count == 0:
        print("没有需要迁移的步骤")
        return
    
    # 显示即将迁移的步骤
    print("\n即将迁移的步骤:")
    for step in command_steps:
        print(f"  - ID: {step.id}, Name: {step.name}, Pipeline: {step.pipeline.name if step.pipeline else 'None'}")
    
    # 确认迁移
    response = input(f"\n确认将这 {count} 个步骤的类型从 'command' 改为 'custom'? (y/N): ")
    if response.lower() != 'y':
        print("迁移已取消")
        return
    
    # 执行迁移
    updated_count = command_steps.update(step_type='custom')
    print(f"\n成功迁移 {updated_count} 个步骤")
    
    # 验证迁移结果
    remaining_command_steps = PipelineStep.objects.filter(step_type='command').count()
    new_custom_steps = PipelineStep.objects.filter(step_type='custom').count()
    
    print(f"迁移后统计:")
    print(f"  - 剩余command类型步骤: {remaining_command_steps}")
    print(f"  - 当前custom类型步骤: {new_custom_steps}")
    
    print("\n=== 迁移完成 ===")


def verify_step_types():
    """验证当前数据库中的步骤类型分布"""
    
    print("\n=== 当前步骤类型分布 ===")
    
    from django.db.models import Count
    
    type_counts = (PipelineStep.objects
                   .values('step_type')
                   .annotate(count=Count('id'))
                   .order_by('-count'))
    
    for item in type_counts:
        print(f"  {item['step_type']}: {item['count']} 个")


if __name__ == '__main__':
    try:
        verify_step_types()
        migrate_command_to_custom()
        verify_step_types()
    except Exception as e:
        print(f"迁移过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
