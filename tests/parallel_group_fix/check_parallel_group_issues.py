#!/usr/bin/env python3
"""
检查并修复并行组数据不完整问题
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

def check_parallel_group_issues():
    """检查并行组数据不完整问题"""
    
    print("🔍 检查并行组数据不完整问题...")
    
    # 1. 查找测试流水线
    try:
        pipeline = Pipeline.objects.get(id=26)
        print(f"✅ 找到测试流水线: {pipeline.name} (ID: {pipeline.id})")
    except Pipeline.DoesNotExist:
        print("❌ 未找到流水线ID 26")
        return
    
    # 2. 查看所有并行组
    groups = pipeline.parallel_groups.all()
    print(f"\n📊 流水线包含 {groups.count()} 个并行组:")
    
    for group in groups:
        print(f"\n🔗 并行组: {group.id} - {group.name}")
        print(f"   描述: {group.description}")
        print(f"   流水线: {group.pipeline_id}")
        print(f"   同步策略: {group.sync_policy}")
        print(f"   超时时间: {group.timeout_seconds}")
        
        # 检查关联的步骤
        group_id_str = str(group.id)
        associated_steps = pipeline.steps.filter(parallel_group=group_id_str)
        print(f"   关联步骤数: {associated_steps.count()}")
        
        for step in associated_steps:
            print(f"     - 步骤 {step.id}: {step.name}")
        
        # 检查是否有数据完整性问题
        issues = []
        
        # 检查必填字段
        if not group.name:
            issues.append("名称为空")
        if not group.id:
            issues.append("ID为空")
        if not group.pipeline_id:
            issues.append("流水线ID为空")
        
        # 检查ID格式
        if group.id and (group.id.strip() == '' or group.id == 'None'):
            issues.append("ID格式无效")
        
        if issues:
            print(f"   ❌ 数据问题: {', '.join(issues)}")
        else:
            print(f"   ✅ 数据完整")
    
    # 3. 检查孤立的步骤关联
    print(f"\n🔍 检查孤立的步骤关联...")
    
    all_steps = pipeline.steps.all()
    valid_group_ids = set(str(g.id) for g in groups if g.id)
    
    for step in all_steps:
        if step.parallel_group and step.parallel_group not in valid_group_ids:
            print(f"❌ 步骤 {step.id} ({step.name}) 关联到无效的并行组: '{step.parallel_group}'")
    
    # 4. 尝试序列化每个并行组
    print(f"\n🧪 测试并行组序列化...")
    
    for group in groups:
        try:
            serializer = ParallelGroupSerializer(group)
            data = serializer.data
            print(f"✅ 并行组 {group.id} 序列化成功")
            print(f"   数据: {data}")
        except Exception as e:
            print(f"❌ 并行组 {group.id} 序列化失败: {e}")
    
    # 5. 识别需要清理的并行组
    print(f"\n🧹 识别需要清理的并行组...")
    
    problematic_groups = []
    for group in groups:
        # 检查是否有问题的并行组
        if not group.id or group.id.strip() == '' or group.id == 'None':
            problematic_groups.append(group)
        elif not group.name.strip():
            problematic_groups.append(group)
    
    if problematic_groups:
        print(f"❌ 发现 {len(problematic_groups)} 个有问题的并行组:")
        for group in problematic_groups:
            print(f"   - ID: '{group.id}', 名称: '{group.name}'")
        
        # 询问是否删除
        response = input("\n是否删除这些有问题的并行组? (y/n): ")
        if response.lower() == 'y':
            for group in problematic_groups:
                # 先清理关联的步骤
                group_id_str = str(group.id)
                pipeline.steps.filter(parallel_group=group_id_str).update(parallel_group='')
                # 删除并行组
                group.delete()
                print(f"✅ 已删除并行组: {group.id}")
    else:
        print("✅ 没有发现需要清理的并行组")
    
    print("\n🎯 检查完成！")

if __name__ == "__main__":
    check_parallel_group_issues()
