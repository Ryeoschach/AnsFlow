#!/usr/bin/env python3
"""
测试并行组与步骤关联的修复情况
"""
import os
import sys
import django
from django.conf import settings

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from pipelines.models import Pipeline, PipelineStep, ParallelGroup
from pipelines.serializers import ParallelGroupSerializer

def test_parallel_group_associations():
    """测试并行组与步骤关联功能"""
    
    print("🔍 开始测试并行组与步骤关联修复...")
    
    # 1. 查找测试流水线
    try:
        pipeline = Pipeline.objects.get(id=26)
        print(f"✅ 找到测试流水线: {pipeline.name} (ID: {pipeline.id})")
    except Pipeline.DoesNotExist:
        print("❌ 未找到流水线ID 26，使用第一个可用的流水线...")
        pipeline = Pipeline.objects.first()
        if not pipeline:
            print("❌ 数据库中没有流水线数据")
            return
        print(f"✅ 使用流水线: {pipeline.name} (ID: {pipeline.id})")
    
    # 2. 查看现有步骤
    steps = pipeline.steps.all()
    print(f"\n📋 流水线包含 {steps.count()} 个步骤:")
    for step in steps:
        print(f"  - 步骤 {step.id}: {step.name} (parallel_group: '{step.parallel_group}')")
    
    # 3. 查看现有并行组
    groups = pipeline.parallel_groups.all()
    print(f"\n🔗 流水线包含 {groups.count()} 个并行组:")
    for group in groups:
        print(f"  - 并行组 {group.id}: {group.name}")
        # 使用serializer获取关联的步骤
        serializer = ParallelGroupSerializer(group)
        group_data = serializer.to_representation(group)
        group_steps = group_data.get('steps', [])
        print(f"    关联步骤: {group_steps}")
    
    # 4. 测试创建新的并行组并关联步骤
    if steps.count() >= 2:
        print("\n🧪 测试创建新的并行组并关联步骤...")
        
        # 选择前两个步骤进行测试
        test_steps = list(steps[:2])
        step_ids = [step.id for step in test_steps]
        
        # 生成唯一的并行组ID
        import time
        unique_id = f"test_group_{int(time.time() * 1000)}"
        
        # 创建测试数据
        test_data = {
            'id': unique_id,
            'name': 'Test Parallel Group',
            'description': 'Test group for step association',
            'pipeline': pipeline.id,
            'steps': step_ids
        }
        
        print(f"创建并行组数据: {test_data}")
        
        # 使用serializer创建并行组
        serializer = ParallelGroupSerializer(data=test_data)
        if serializer.is_valid():
            group = serializer.save()
            print(f"✅ 成功创建并行组: {group.name} (ID: {group.id})")
            
            # 验证步骤关联
            print("\n🔍 验证步骤关联...")
            group_id_str = str(group.id)
            
            for step_id in step_ids:
                step = PipelineStep.objects.get(id=step_id)
                print(f"  - 步骤 {step.id} ({step.name}): parallel_group = '{step.parallel_group}'")
                
                if step.parallel_group == group_id_str:
                    print(f"    ✅ 步骤 {step.id} 已正确关联到并行组 {group.id}")
                else:
                    print(f"    ❌ 步骤 {step.id} 未正确关联到并行组 {group.id}")
            
            # 使用serializer验证
            serializer_after = ParallelGroupSerializer(group)
            group_data_after = serializer_after.to_representation(group)
            associated_steps = group_data_after.get('steps', [])
            print(f"\n📊 Serializer返回的关联步骤: {associated_steps}")
            
            if set(associated_steps) == set(step_ids):
                print("✅ Serializer验证通过: 步骤关联正确")
            else:
                print("❌ Serializer验证失败: 步骤关联不正确")
                print(f"  期望: {step_ids}")
                print(f"  实际: {associated_steps}")
        else:
            print(f"❌ 创建并行组失败: {serializer.errors}")
    
    # 5. 测试更新并行组的步骤关联
    if groups.exists() and steps.count() >= 1:
        print("\n🔄 测试更新并行组的步骤关联...")
        
        group = groups.first()
        test_step = steps.first()
        
        update_data = {
            'id': group.id,  # 提供ID字段
            'name': group.name,
            'description': group.description,
            'pipeline': group.pipeline.id,
            'steps': [test_step.id]
        }
        
        print(f"更新并行组数据: {update_data}")
        
        serializer = ParallelGroupSerializer(group, data=update_data)
        if serializer.is_valid():
            updated_group = serializer.save()
            print(f"✅ 成功更新并行组: {updated_group.name}")
            
            # 验证更新后的关联
            test_step.refresh_from_db()
            group_id_str = str(updated_group.id)
            
            print(f"验证步骤 {test_step.id} 的 parallel_group: '{test_step.parallel_group}'")
            
            if test_step.parallel_group == group_id_str:
                print(f"✅ 步骤 {test_step.id} 已正确关联到并行组 {updated_group.id}")
            else:
                print(f"❌ 步骤 {test_step.id} 未正确关联到并行组 {updated_group.id}")
        else:
            print(f"❌ 更新并行组失败: {serializer.errors}")
    
    print("\n🎯 测试完成！")

if __name__ == "__main__":
    test_parallel_group_associations()
