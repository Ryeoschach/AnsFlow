#!/usr/bin/env python
"""
修复流水线步骤数据一致性问题
将AtomicStep数据迁移到PipelineStep，统一使用PipelineStep作为前端数据源
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from cicd_integrations.models import AtomicStep
from django.db import transaction


def migrate_atomic_steps_to_pipeline_steps():
    """将AtomicStep数据迁移到PipelineStep"""
    print("🔄 开始迁移AtomicStep到PipelineStep...")
    
    # 获取所有有AtomicStep的流水线
    pipelines_to_migrate = []
    
    for pipeline in Pipeline.objects.all():
        atomic_count = pipeline.atomic_steps.count()
        pipeline_count = pipeline.steps.count()
        
        print(f"📋 {pipeline.name}: AtomicSteps={atomic_count}, PipelineSteps={pipeline_count}")
        
        if atomic_count > 0:
            pipelines_to_migrate.append(pipeline)
            if pipeline_count > 0:
                print(f"  ⚠️ 需要重建: {pipeline.name} (存在冲突数据)")
            else:
                print(f"  ➡️ 需要迁移: {pipeline.name}")
    
    print(f"\n📊 共发现 {len(pipelines_to_migrate)} 个流水线需要处理")
    
    if not pipelines_to_migrate:
        print("✅ 没有需要迁移的流水线")
        return
    
    # 执行迁移
    for pipeline in pipelines_to_migrate:
        with transaction.atomic():
            print(f"\n🔄 处理流水线: {pipeline.name}")
            
            # 先删除现有的PipelineStep（如果有）
            if pipeline.steps.exists():
                deleted_count = pipeline.steps.count()
                pipeline.steps.all().delete()
                print(f"  🗑️ 删除现有PipelineStep: {deleted_count} 个")
            
            atomic_steps = pipeline.atomic_steps.order_by('order')
            
            for atomic_step in atomic_steps:
                # 创建对应的PipelineStep
                pipeline_step_data = {
                    'pipeline': pipeline,
                    'name': atomic_step.name,
                    'description': atomic_step.description,
                    'step_type': atomic_step.step_type,
                    'order': atomic_step.order,
                    'ansible_parameters': atomic_step.parameters,  # 将parameters存到ansible_parameters
                }
                
                # 如果有ansible相关字段，复制过来
                if atomic_step.ansible_playbook:
                    pipeline_step_data['ansible_playbook'] = atomic_step.ansible_playbook
                if atomic_step.ansible_inventory:
                    pipeline_step_data['ansible_inventory'] = atomic_step.ansible_inventory
                if atomic_step.ansible_credential:
                    pipeline_step_data['ansible_credential'] = atomic_step.ansible_credential
                
                pipeline_step = PipelineStep.objects.create(**pipeline_step_data)
                print(f"  ✅ 创建PipelineStep: {pipeline_step.name} (order: {pipeline_step.order})")
            
            print(f"  📊 迁移完成: {atomic_steps.count()} 个步骤")


def verify_migration():
    """验证迁移结果"""
    print("\n🔍 验证迁移结果...")
    
    for pipeline in Pipeline.objects.all():
        atomic_count = pipeline.atomic_steps.count()
        pipeline_count = pipeline.steps.count()
        
        print(f"📋 {pipeline.name}: AtomicSteps={atomic_count}, PipelineSteps={pipeline_count}")
        
        if atomic_count > 0 and pipeline_count > 0:
            print(f"  ⚠️ 同时存在两种步骤类型")
        elif pipeline_count > 0:
            print(f"  ✅ 使用PipelineStep")
        elif atomic_count > 0:
            print(f"  ❌ 仍然只有AtomicStep")
        else:
            print(f"  📝 无步骤")


def main():
    print("🚀 修复流水线步骤数据一致性")
    print("=" * 50)
    
    # 显示当前状态
    print("📊 当前状态:")
    verify_migration()
    
    # 执行迁移
    migrate_atomic_steps_to_pipeline_steps()
    
    # 验证结果
    verify_migration()
    
    print("\n✅ 修复完成！")
    print("\n💡 提示:")
    print("- 现在所有流水线都应该有PipelineStep数据")
    print("- 前端将使用PipelineStep进行编辑和显示")
    print("- AtomicStep数据保持不变，可用于历史记录")


if __name__ == '__main__':
    main()
