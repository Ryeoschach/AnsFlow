#!/usr/bin/env python3
"""
清理并行组数据中的无效记录
"""
import os
import sys
import django
from django.conf import settings

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from pipelines.models import Pipeline, PipelineStep, ParallelGroup

def clean_parallel_group_data():
    """清理无效的并行组数据"""
    
    print("🧹 开始清理并行组数据...")
    
    # 查找所有并行组
    all_groups = ParallelGroup.objects.all()
    print(f"📊 数据库中共有 {all_groups.count()} 个并行组")
    
    # 查找无效的并行组（ID为空或None）
    invalid_groups = ParallelGroup.objects.filter(id__in=['', None])
    print(f"🔍 发现 {invalid_groups.count()} 个无效的并行组")
    
    for group in invalid_groups:
        print(f"  - 无效并行组: ID='{group.id}', Name='{group.name}'")
    
    # 删除无效的并行组
    if invalid_groups.exists():
        count = invalid_groups.count()
        invalid_groups.delete()
        print(f"✅ 已删除 {count} 个无效的并行组")
    else:
        print("✅ 没有发现无效的并行组")
    
    # 清理步骤中的无效并行组关联
    print("\n🔍 检查步骤中的无效并行组关联...")
    
    # 查找所有步骤
    all_steps = PipelineStep.objects.all()
    print(f"📊 数据库中共有 {all_steps.count()} 个步骤")
    
    # 查找有并行组关联的步骤
    steps_with_group = all_steps.exclude(parallel_group='')
    print(f"📊 有并行组关联的步骤: {steps_with_group.count()} 个")
    
    # 验证每个步骤的并行组关联是否有效
    invalid_associations = []
    for step in steps_with_group:
        try:
            # 尝试查找对应的并行组
            group = ParallelGroup.objects.get(id=step.parallel_group)
            print(f"  ✅ 步骤 {step.id} ({step.name}) -> 并行组 {group.id} ({group.name})")
        except ParallelGroup.DoesNotExist:
            print(f"  ❌ 步骤 {step.id} ({step.name}) -> 无效并行组 '{step.parallel_group}'")
            invalid_associations.append(step)
    
    # 清理无效关联
    if invalid_associations:
        print(f"\n🧹 清理 {len(invalid_associations)} 个无效的步骤并行组关联...")
        for step in invalid_associations:
            step.parallel_group = ''
            step.save()
            print(f"  ✅ 已清理步骤 {step.id} ({step.name}) 的无效并行组关联")
    else:
        print("\n✅ 没有发现无效的步骤并行组关联")
    
    print("\n🎯 数据清理完成！")

if __name__ == "__main__":
    clean_parallel_group_data()
