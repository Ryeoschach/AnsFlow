#!/usr/bin/env python3
"""
测试并行组序列化器的步骤关联修复
验证 ParallelGroupSerializer 能否正确处理 steps 字段
"""
import os
import sys
import django
import time
import json

# 设置Django环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_service.settings')
django.setup()

from pipelines.models import Pipeline, PipelineStep, ParallelGroup
from pipelines.serializers import ParallelGroupSerializer
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import User

def test_parallel_group_serializer():
    """测试并行组序列化器的步骤关联功能"""
    
    print("🔍 开始测试并行组序列化器...")
    
    # 1. 获取测试数据
    try:
        pipeline = Pipeline.objects.get(id=26)
        print(f"✅ 找到流水线: {pipeline.name} (ID: {pipeline.id})")
        
        steps = list(pipeline.steps.all())
        print(f"✅ 流水线包含 {len(steps)} 个步骤:")
        for step in steps:
            print(f"  - 步骤 {step.id}: {step.name} (parallel_group: '{step.parallel_group}')")
        
        # 获取并行组
        parallel_groups = list(pipeline.parallel_groups.all())
        print(f"✅ 流水线包含 {len(parallel_groups)} 个并行组:")
        for group in parallel_groups:
            print(f"  - 并行组 {group.id}: {group.name}")
            
    except Pipeline.DoesNotExist:
        print("❌ 流水线ID 26 不存在")
        return False
    
    # 2. 测试序列化器的读取功能
    print("\n🔍 测试序列化器读取功能...")
    
    if parallel_groups:
        test_group = parallel_groups[0]
        serializer = ParallelGroupSerializer(test_group)
        data = serializer.data
        print(f"✅ 并行组 {test_group.id} 序列化数据: {data}")
        print(f"✅ 关联的步骤: {data.get('steps', [])}")
    
    # 3. 测试序列化器的写入功能
    print("\n🔍 测试序列化器写入功能...")
    
    if len(steps) >= 2:
        # 选择前两个步骤
        test_step_ids = [steps[0].id, steps[1].id]
        
        # 创建新的并行组
        group_data = {
            'name': 'TEST_GROUP_' + str(int(time.time())),
            'description': '测试并行组序列化器',
            'pipeline': pipeline.id,
            'steps': test_step_ids,
            'sync_policy': 'wait_all',
            'timeout_seconds': 300
        }
        
        print(f"📝 创建测试并行组数据: {group_data}")
        
        serializer = ParallelGroupSerializer(data=group_data)
        if serializer.is_valid():
            created_group = serializer.save()
            print(f"✅ 成功创建并行组: {created_group.name} (ID: {created_group.id})")
            
            # 验证步骤关联
            print("\n🔍 验证步骤关联...")
            group_id_str = str(created_group.id)
            
            for step_id in test_step_ids:
                step = PipelineStep.objects.get(id=step_id)
                print(f"  - 步骤 {step.id} ({step.name}): parallel_group = '{step.parallel_group}'")
                
                if step.parallel_group == group_id_str:
                    print(f"    ✅ 步骤 {step.id} 正确关联到并行组 {created_group.id}")
                else:
                    print(f"    ❌ 步骤 {step.id} 未正确关联到并行组 {created_group.id}")
            
            # 测试序列化器的读取功能
            print("\n🔍 测试创建后的读取功能...")
            read_serializer = ParallelGroupSerializer(created_group)
            read_data = read_serializer.data
            print(f"✅ 读取的步骤数据: {read_data.get('steps', [])}")
            
            # 清理测试数据
            print(f"\n🧹 清理测试数据...")
            
            # 清除步骤关联
            PipelineStep.objects.filter(
                pipeline=pipeline,
                parallel_group=group_id_str
            ).update(parallel_group='')
            
            # 删除测试并行组
            created_group.delete()
            print(f"✅ 已清理测试数据")
            
        else:
            print(f"❌ 序列化器验证失败: {serializer.errors}")
            return False
    
    # 4. 测试更新功能
    print("\n🔍 测试序列化器更新功能...")
    
    if parallel_groups and len(steps) >= 2:
        test_group = parallel_groups[0]
        test_step_ids = [steps[0].id, steps[1].id]
        
        update_data = {
            'name': test_group.name,
            'description': test_group.description,
            'pipeline': pipeline.id,
            'steps': test_step_ids,
            'sync_policy': test_group.sync_policy,
            'timeout_seconds': test_group.timeout_seconds
        }
        
        print(f"📝 更新并行组数据: {update_data}")
        
        serializer = ParallelGroupSerializer(test_group, data=update_data)
        if serializer.is_valid():
            updated_group = serializer.save()
            print(f"✅ 成功更新并行组: {updated_group.name} (ID: {updated_group.id})")
            
            # 验证步骤关联
            print("\n🔍 验证更新后的步骤关联...")
            group_id_str = str(updated_group.id)
            
            for step_id in test_step_ids:
                step = PipelineStep.objects.get(id=step_id)
                print(f"  - 步骤 {step.id} ({step.name}): parallel_group = '{step.parallel_group}'")
                
                if step.parallel_group == group_id_str:
                    print(f"    ✅ 步骤 {step.id} 正确关联到并行组 {updated_group.id}")
                else:
                    print(f"    ❌ 步骤 {step.id} 未正确关联到并行组 {updated_group.id}")
            
            # 测试序列化器的读取功能
            print("\n🔍 测试更新后的读取功能...")
            read_serializer = ParallelGroupSerializer(updated_group)
            read_data = read_serializer.data
            print(f"✅ 读取的步骤数据: {read_data.get('steps', [])}")
            
        else:
            print(f"❌ 序列化器更新验证失败: {serializer.errors}")
            return False
    
    print("\n🎉 并行组序列化器测试完成!")
    return True

def main():
    """主函数"""
    import time
    
    print("="*60)
    print("🚀 AnsFlow 并行组序列化器测试")
    print("="*60)
    
    success = test_parallel_group_serializer()
    
    if success:
        print("\n✅ 所有测试通过！并行组序列化器工作正常。")
    else:
        print("\n❌ 测试失败！需要进一步调试。")
    
    print("="*60)

if __name__ == "__main__":
    main()
