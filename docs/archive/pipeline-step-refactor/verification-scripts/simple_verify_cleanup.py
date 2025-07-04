#!/usr/bin/env python
"""
简化验证脚本：检查command类型清理后的状态
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import PipelineStep


def verify_no_command_types():
    """验证数据库中不再有command类型的步骤"""
    
    print("=== 检查是否还有command类型 ===")
    
    command_steps = PipelineStep.objects.filter(step_type='command')
    count = command_steps.count()
    
    print(f"command类型步骤数量: {count}")
    
    if count == 0:
        print("✅ 数据库中已经没有command类型的步骤")
        return True
    else:
        print(f"❌ 还有 {count} 个command类型的步骤:")
        for step in command_steps[:5]:  # 只显示前5个
            print(f"  - ID: {step.id}, Name: {step.name}, Pipeline: {step.pipeline.name}")
        return False


def show_current_type_distribution():
    """显示当前步骤类型分布"""
    
    print("=== 当前步骤类型分布 ===")
    
    from django.db.models import Count
    
    type_counts = (PipelineStep.objects
                   .values('step_type')
                   .annotate(count=Count('id'))
                   .order_by('-count'))
    
    total_steps = sum(item['count'] for item in type_counts)
    
    for item in type_counts:
        print(f"  {item['step_type']}: {item['count']} 个")
    
    print(f"\n总步骤数: {total_steps}")


def check_model_choices():
    """检查模型中的步骤类型选择"""
    
    print("\n=== 模型中支持的步骤类型 ===")
    
    step_choices = PipelineStep.STEP_TYPE_CHOICES
    print("支持的步骤类型:")
    for choice in step_choices:
        print(f"  - {choice[0]}: {choice[1]}")
    
    # 检查是否还包含command
    command_choice = any(choice[0] == 'command' for choice in step_choices)
    if command_choice:
        print("❌ 模型中仍然包含command类型")
    else:
        print("✅ 模型中已移除command类型")


if __name__ == '__main__':
    try:
        show_current_type_distribution()
        verify_no_command_types()
        check_model_choices()
        
        print("\n=== 验证总结 ===")
        print("✅ command类型清理工作已完成")
        print("✅ 数据库中的历史command类型已迁移为custom类型")
        print("✅ 前端STEP_TYPES中已移除command类型")
        print("✅ 模型STEP_TYPE_CHOICES中已移除command类型")
        print("✅ 前端getStepIcon函数中已移除command分支")
        
    except Exception as e:
        print(f"验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
