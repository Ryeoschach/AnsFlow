#!/usr/bin/env python3
"""
验证并行组步骤关联修复效果
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')

django.setup()

from pipelines.models import Pipeline, PipelineStep, ParallelGroup
from pipelines.serializers import ParallelGroupSerializer

def test_parallel_group_steps_association():
    """测试并行组步骤关联功能"""
    
    print("🧪 测试并行组步骤关联修复效果")
    print("=" * 50)
    
    try:
        # 1. 获取测试数据
        print("1️⃣ 获取测试数据...")
        
        # 获取流水线
        pipeline = Pipeline.objects.first()
        if not pipeline:
            print("❌ 没有找到流水线")
            return False
        
        print(f"✅ 使用流水线: {pipeline.name} (ID: {pipeline.id})")
        
        # 获取步骤
        steps = pipeline.steps.all()
        if len(steps) < 2:
            print("❌ 步骤数量不足，需要至少2个步骤")
            return False
        
        print(f"✅ 流水线包含 {len(steps)} 个步骤")
        for step in steps:
            group_info = f" → 并行组: {step.parallel_group}" if step.parallel_group else " → 无并行组"
            print(f"  - {step.name} (ID: {step.id}){group_info}")
        
        # 2. 创建测试并行组
        print("2️⃣ 创建测试并行组...")
        
        test_steps = [steps[0].id, steps[1].id]  # 选择前两个步骤
        
        group_data = {
            'id': 'test_steps_association',
            'name': '步骤关联测试组',
            'description': '测试步骤关联修复的并行组',
            'pipeline': pipeline.id,
            'sync_policy': 'wait_all',
            'timeout_seconds': 3600,
            'steps': test_steps
        }
        
        print(f"📝 创建并行组，包含步骤: {test_steps}")
        
        serializer = ParallelGroupSerializer(data=group_data)
        if serializer.is_valid():
            parallel_group = serializer.save()
            print(f"✅ 并行组创建成功: {parallel_group.id}")
        else:
            print(f"❌ 并行组创建失败: {serializer.errors}")
            return False
        
        # 3. 验证步骤关联
        print("3️⃣ 验证步骤关联...")
        
        # 重新获取步骤数据
        updated_steps = pipeline.steps.all()
        associated_steps = updated_steps.filter(parallel_group=parallel_group.id)
        
        print(f"📊 验证结果:")
        print(f"  期望关联步骤数: {len(test_steps)}")
        print(f"  实际关联步骤数: {associated_steps.count()}")
        
        if associated_steps.count() == len(test_steps):
            print("✅ 步骤关联成功!")
            for step in associated_steps:
                print(f"  ✅ 步骤 '{step.name}' (ID: {step.id}) 已关联到并行组")
        else:
            print("❌ 步骤关联失败!")
            return False
        
        # 4. 测试序列化器的读取功能
        print("4️⃣ 测试序列化器读取功能...")
        
        read_serializer = ParallelGroupSerializer(parallel_group)
        serialized_data = read_serializer.data
        
        print(f"📤 序列化结果:")
        print(f"  并行组ID: {serialized_data['id']}")
        print(f"  并行组名称: {serialized_data['name']}")
        print(f"  包含步骤: {serialized_data['steps']}")
        
        if set(serialized_data['steps']) == set(test_steps):
            print("✅ 序列化器读取正确!")
        else:
            print("❌ 序列化器读取错误!")
            return False
        
        # 5. 测试更新功能
        print("5️⃣ 测试更新功能...")
        
        # 只保留第一个步骤
        update_data = {
            'steps': [test_steps[0]]
        }
        
        update_serializer = ParallelGroupSerializer(parallel_group, data=update_data, partial=True)
        if update_serializer.is_valid():
            updated_group = update_serializer.save()
            print(f"✅ 并行组更新成功")
        else:
            print(f"❌ 并行组更新失败: {update_serializer.errors}")
            return False
        
        # 验证更新结果
        final_steps = pipeline.steps.filter(parallel_group=parallel_group.id)
        if final_steps.count() == 1 and final_steps.first().id == test_steps[0]:
            print("✅ 更新功能正常!")
        else:
            print("❌ 更新功能异常!")
            return False
        
        # 6. 清理测试数据
        print("6️⃣ 清理测试数据...")
        
        # 清除步骤关联
        PipelineStep.objects.filter(parallel_group=parallel_group.id).update(parallel_group='')
        
        # 删除并行组
        parallel_group.delete()
        print("✅ 测试数据清理完成")
        
        print("\n🎉 所有测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_current_state():
    """检查当前的数据状态"""
    
    print("\n🔍 检查当前数据状态")
    print("=" * 30)
    
    # 获取所有流水线
    pipelines = Pipeline.objects.all()
    print(f"📋 系统中共有 {pipelines.count()} 个流水线")
    
    for pipeline in pipelines:
        print(f"\n流水线: {pipeline.name} (ID: {pipeline.id})")
        
        # 获取步骤
        steps = pipeline.steps.all()
        print(f"步骤数量: {steps.count()}")
        
        for step in steps:
            group_info = f" → 并行组: {step.parallel_group}" if step.parallel_group else " → 无并行组"
            print(f"  {step.name} (ID: {step.id}){group_info}")
        
        # 获取并行组
        groups = pipeline.parallel_groups.all()
        print(f"并行组数量: {groups.count()}")
        
        for group in groups:
            associated_steps = steps.filter(parallel_group=group.id)
            print(f"  - {group.name} (ID: {group.id})")
            print(f"    属于该组的步骤: {associated_steps.count()} 个")
            for step in associated_steps:
                print(f"      * {step.name} (ID: {step.id})")

def main():
    """主函数"""
    
    print("🔧 并行组步骤关联修复验证")
    print("=" * 50)
    
    # 检查当前状态
    check_current_state()
    
    # 运行测试
    success = test_parallel_group_steps_association()
    
    if success:
        print("\n✅ 修复验证成功!")
        print("📝 修复总结:")
        print("  1. ParallelGroupSerializer现在正确处理steps字段")
        print("  2. 创建并行组时会自动关联步骤")
        print("  3. 更新并行组时会同步更新步骤关联")
        print("  4. 序列化时会正确返回关联的步骤ID")
        
        print("\n💡 下一步:")
        print("  1. 重启Django服务器以应用修复")
        print("  2. 在前端测试并行组管理功能")
        print("  3. 验证步骤关联是否正确保存和显示")
    else:
        print("\n❌ 修复验证失败!")
        print("请检查代码修复是否正确")

if __name__ == "__main__":
    main()
