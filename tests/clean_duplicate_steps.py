#!/usr/bin/env python3
"""
清理Integration Test Pipeline中的重复步骤
"""

import os
import sys
import django
from django.conf import settings

# 设置 Django 环境
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from pipelines.models import Pipeline
from cicd_integrations.models import AtomicStep
from django.db import models

def clean_duplicate_steps():
    """清理Integration Test Pipeline中的重复步骤"""
    print("🧹 清理Integration Test Pipeline重复步骤")
    print("=" * 50)
    
    try:
        # 查找流水线
        pipeline = Pipeline.objects.filter(name="Integration Test Pipeline").first()
        if not pipeline:
            print("❌ 未找到Integration Test Pipeline")
            return False
        
        print(f"✅ 找到流水线: {pipeline.name} (ID: {pipeline.id})")
        
        # 显示当前步骤
        current_steps = pipeline.atomic_steps.all().order_by('order')
        print(f"📋 当前步骤 ({current_steps.count()}个):")
        for step in current_steps:
            print(f"   {step.order}. {step.name} ({step.step_type}) [ID: {step.id}]")
        
        # 检查重复步骤
        step_type_counts = {}
        for step in current_steps:
            key = f"{step.step_type}_{step.name}"
            if key in step_type_counts:
                step_type_counts[key].append(step)
            else:
                step_type_counts[key] = [step]
        
        # 找出重复的步骤
        duplicates_found = False
        for key, steps in step_type_counts.items():
            if len(steps) > 1:
                duplicates_found = True
                print(f"\n⚠️  发现重复步骤: {key}")
                for i, step in enumerate(steps):
                    marker = "👈 保留" if i == 0 else "❌ 删除"
                    print(f"   Order {step.order}: {step.name} [ID: {step.id}] {marker}")
        
        if not duplicates_found:
            print("\n✅ 没有发现重复步骤")
            return True
        
        # 询问是否删除重复项
        print(f"\n🤔 是否删除重复步骤? (y/n): ", end="")
        try:
            user_input = input().strip().lower()
            if user_input not in ['y', 'yes']:
                print("👋 取消清理操作")
                return True
        except KeyboardInterrupt:
            print(f"\n👋 取消清理操作")
            return True
        
        # 删除重复步骤（保留第一个）
        deleted_count = 0
        for key, steps in step_type_counts.items():
            if len(steps) > 1:
                # 保留第一个（order最小的），删除其余的
                steps_to_delete = steps[1:]  # 跳过第一个
                for step in steps_to_delete:
                    print(f"🗑️  删除重复步骤: {step.name} [ID: {step.id}, Order: {step.order}]")
                    step.delete()
                    deleted_count += 1
        
        print(f"\n✅ 成功删除 {deleted_count} 个重复步骤")
        
        # 重新排序steps的order
        remaining_steps = pipeline.atomic_steps.all().order_by('order')
        print(f"\n🔄 重新排序剩余步骤...")
        for i, step in enumerate(remaining_steps, 1):
            if step.order != i:
                step.order = i
                step.save()
                print(f"   调整 {step.name} 的order: {step.order} → {i}")
        
        # 显示最终结果
        final_steps = pipeline.atomic_steps.all().order_by('order')
        print(f"\n📊 清理后的步骤列表 ({final_steps.count()}个):")
        for step in final_steps:
            icon = {
                'fetch_code': '📥',
                'build': '🔨',
                'ansible': '🤖',
                'test': '🧪',
                'security_scan': '🛡️',
                'docker_build': '🐳'
            }.get(step.step_type, '📋')
            print(f"   {step.order}. {icon} {step.name} ({step.step_type})")
        
        return True
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🧹 Integration Test Pipeline 重复步骤清理工具")
    print("=" * 60)
    print("目标: 清理流水线中的重复步骤，确保数据一致性")
    print("=" * 60)
    
    success = clean_duplicate_steps()
    
    if success:
        print(f"\n🎉 清理完成！")
        print(f"💡 建议:")
        print(f"1. 重新测试预览API，确认步骤数量一致")
        print(f"2. 验证流水线执行功能")
        print(f"3. 检查前端预览页面显示")
    else:
        print(f"\n❌ 清理失败，请检查日志")

if __name__ == "__main__":
    main()
