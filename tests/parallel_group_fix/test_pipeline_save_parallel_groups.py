#!/usr/bin/env python3
"""
测试保存流水线后并行组关联是否保持
"""
import os
import sys
import django
from django.conf import settings

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from pipelines.models import Pipeline, PipelineStep, ParallelGroup
from pipelines.serializers import ParallelGroupSerializer, PipelineSerializer

def test_pipeline_save_with_parallel_groups():
    """测试保存流水线后并行组关联是否保持"""
    
    print("🧪 测试保存流水线后并行组关联保持...")
    
    # 1. 获取测试流水线
    try:
        pipeline = Pipeline.objects.get(id=26)
        print(f"✅ 找到测试流水线: {pipeline.name} (ID: {pipeline.id})")
    except Pipeline.DoesNotExist:
        print("❌ 未找到流水线ID 26")
        return
    
    # 2. 检查当前步骤和并行组状态
    steps = pipeline.steps.all()
    groups = pipeline.parallel_groups.all()
    
    print(f"\n📊 当前状态:")
    print(f"  - 步骤数: {steps.count()}")
    print(f"  - 并行组数: {groups.count()}")
    
    # 显示步骤的并行组关联
    print(f"\n📋 步骤的并行组关联:")
    for step in steps:
        print(f"  - 步骤 {step.id} ({step.name}): parallel_group = '{step.parallel_group}'")
    
    # 3. 确保有一些并行组关联（如果没有，先创建一些）
    test_group = None
    for group in groups:
        group_id_str = str(group.id)
        associated_steps = steps.filter(parallel_group=group_id_str)
        if associated_steps.exists():
            test_group = group
            break
    
    if not test_group and groups.exists():
        # 为第一个并行组分配一些步骤
        test_group = groups.first()
        test_steps = list(steps[:2])  # 选择前两个步骤
        
        # 更新步骤的并行组关联
        for step in test_steps:
            step.parallel_group = str(test_group.id)
            step.save()
        
        print(f"\n🔗 已为测试创建并行组关联:")
        print(f"  - 并行组: {test_group.id} ({test_group.name})")
        print(f"  - 关联步骤: {[s.id for s in test_steps]}")
    
    # 4. 记录保存前的状态
    print(f"\n📸 保存前的状态快照:")
    steps_before = {}
    for step in pipeline.steps.all():
        steps_before[step.name] = step.parallel_group
        print(f"  - {step.name}: '{step.parallel_group}'")
    
    # 5. 模拟前端保存流水线
    print(f"\n💾 模拟保存流水线...")
    
    # 构造类似前端的请求数据
    steps_data = []
    for i, step in enumerate(pipeline.steps.all().order_by('order')):
        step_data = {
            'name': step.name,
            'step_type': step.step_type,
            'description': step.description,
            'parameters': step.ansible_parameters or {},
            'order': i + 1,
            'is_active': True,
            'parallel_group': step.parallel_group  # 关键：包含并行组信息
        }
        steps_data.append(step_data)
        print(f"  📋 步骤数据: {step.name} -> parallel_group: '{step.parallel_group}'")
    
    update_data = {
        'name': pipeline.name,
        'description': pipeline.description,
        'project': pipeline.project.id,
        'is_active': pipeline.is_active,
        'execution_mode': pipeline.execution_mode,
        'steps': steps_data
    }
    
    # 使用 serializer 保存
    try:
        serializer = PipelineSerializer(pipeline, data=update_data)
        if serializer.is_valid():
            updated_pipeline = serializer.save()
            print(f"✅ 流水线保存成功")
        else:
            print(f"❌ 流水线保存验证失败: {serializer.errors}")
            return
    except Exception as e:
        print(f"❌ 流水线保存异常: {e}")
        return
    
    # 6. 检查保存后的状态
    print(f"\n🔍 检查保存后的状态:")
    
    updated_steps = updated_pipeline.steps.all()
    steps_after = {}
    
    print(f"保存后的步骤:")
    for step in updated_steps:
        steps_after[step.name] = step.parallel_group
        print(f"  - {step.name}: '{step.parallel_group}'")
    
    # 7. 对比保存前后
    print(f"\n📊 保存前后对比:")
    success_count = 0
    total_count = 0
    
    for step_name in steps_before:
        before_group = steps_before[step_name]
        after_group = steps_after.get(step_name, '')
        total_count += 1
        
        if before_group == after_group:
            print(f"  ✅ {step_name}: '{before_group}' -> '{after_group}' (保持一致)")
            success_count += 1
        else:
            print(f"  ❌ {step_name}: '{before_group}' -> '{after_group}' (发生变化)")
    
    # 8. 结果总结
    print(f"\n🎯 测试结果:")
    if success_count == total_count:
        print(f"✅ 完全成功! {success_count}/{total_count} 个步骤的并行组关联保持不变")
    else:
        print(f"❌ 部分失败! {success_count}/{total_count} 个步骤的并行组关联保持不变")
        print(f"   {total_count - success_count} 个步骤的并行组关联丢失")
    
    # 9. 验证并行组视图
    print(f"\n🔗 验证并行组视图:")
    for group in pipeline.parallel_groups.all():
        serializer = ParallelGroupSerializer(group)
        group_data = serializer.data
        print(f"  - 并行组 {group.id}: {len(group_data['steps'])} 个步骤 {group_data['steps']}")

if __name__ == "__main__":
    test_pipeline_save_with_parallel_groups()
