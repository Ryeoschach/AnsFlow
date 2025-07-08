#!/usr/bin/env python3
"""
测试并行组更新和删除操作
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

def test_parallel_group_operations():
    """测试并行组的更新和删除操作"""
    
    print("🧪 开始测试并行组更新和删除操作...")
    
    # 1. 查找测试流水线
    try:
        pipeline = Pipeline.objects.get(id=26)
        print(f"✅ 找到测试流水线: {pipeline.name} (ID: {pipeline.id})")
    except Pipeline.DoesNotExist:
        print("❌ 未找到流水线ID 26")
        return
    
    # 2. 获取步骤
    steps = pipeline.steps.all()
    print(f"📋 流水线包含 {steps.count()} 个步骤")
    
    # 3. 获取现有并行组
    groups = pipeline.parallel_groups.all()
    print(f"🔗 流水线包含 {groups.count()} 个并行组")
    
    if groups.count() == 0:
        print("❌ 没有并行组可以测试")
        return
    
    # 4. 测试更新第一个并行组
    test_group = groups.first()
    print(f"\n🔄 测试更新并行组: {test_group.id} - {test_group.name}")
    
    # 选择前两个步骤进行关联
    if steps.count() >= 2:
        test_steps = list(steps[:2])
        step_ids = [step.id for step in test_steps]
        
        update_data = {
            'id': test_group.id,
            'name': test_group.name + " (已更新)",
            'description': test_group.description + " - 已通过测试更新",
            'pipeline': pipeline.id,
            'sync_policy': test_group.sync_policy,
            'timeout_seconds': test_group.timeout_seconds,
            'steps': step_ids
        }
        
        print(f"更新数据: {update_data}")
        
        try:
            serializer = ParallelGroupSerializer(test_group, data=update_data)
            if serializer.is_valid():
                updated_group = serializer.save()
                print(f"✅ 成功更新并行组: {updated_group.name}")
                
                # 验证步骤关联
                print("🔍 验证步骤关联...")
                for step_id in step_ids:
                    step = PipelineStep.objects.get(id=step_id)
                    print(f"  - 步骤 {step.id} ({step.name}): parallel_group = '{step.parallel_group}'")
                    
                    if step.parallel_group == str(updated_group.id):
                        print(f"    ✅ 步骤 {step.id} 已正确关联")
                    else:
                        print(f"    ❌ 步骤 {step.id} 关联失败")
                
                # 测试序列化
                serializer_check = ParallelGroupSerializer(updated_group)
                updated_data = serializer_check.data
                print(f"📊 更新后的数据: {updated_data}")
                
            else:
                print(f"❌ 更新验证失败: {serializer.errors}")
                
        except Exception as e:
            print(f"❌ 更新操作异常: {e}")
    
    # 5. 测试删除最后一个并行组
    if groups.count() > 1:
        delete_group = groups.last()
        print(f"\n🗑️  测试删除并行组: {delete_group.id} - {delete_group.name}")
        
        try:
            # 检查是否有关联的步骤
            group_id_str = str(delete_group.id)
            associated_steps = pipeline.steps.filter(parallel_group=group_id_str)
            print(f"关联的步骤数: {associated_steps.count()}")
            
            # 删除前先清理步骤关联
            if associated_steps.exists():
                associated_steps.update(parallel_group='')
                print("✅ 已清理步骤关联")
            
            # 删除并行组
            delete_group.delete()
            print(f"✅ 成功删除并行组: {delete_group.name}")
            
        except Exception as e:
            print(f"❌ 删除操作异常: {e}")
    
    # 6. 检查最终状态
    print(f"\n📊 最终状态检查...")
    final_groups = pipeline.parallel_groups.all()
    print(f"剩余并行组数: {final_groups.count()}")
    
    for group in final_groups:
        group_id_str = str(group.id)
        associated_steps = pipeline.steps.filter(parallel_group=group_id_str)
        print(f"  - {group.id}: {associated_steps.count()} 个步骤")
    
    print("\n🎯 测试完成！")

if __name__ == "__main__":
    test_parallel_group_operations()
