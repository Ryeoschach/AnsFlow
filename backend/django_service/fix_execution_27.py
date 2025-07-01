#!/usr/bin/env python3
"""
手动修复第27号执行记录的步骤状态
"""

import os
import sys
import django

# 设置 Django
sys.path.insert(0, '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

try:
    django.setup()
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

from cicd_integrations.models import PipelineExecution, StepExecution

def fix_execution_27_step_status():
    """修复第27号执行记录的步骤状态"""
    print("=== 修复第27号执行记录的步骤状态 ===")
    
    try:
        # 获取第27号执行记录
        execution = PipelineExecution.objects.get(id=27)
        print(f"执行记录 {execution.id}:")
        print(f"  状态: {execution.status}")
        print(f"  开始时间: {execution.started_at}")
        print(f"  完成时间: {execution.completed_at}")
        
        # 获取对应的步骤执行记录
        step_executions = StepExecution.objects.filter(pipeline_execution=execution).order_by('order')
        print(f"\n找到 {step_executions.count()} 个步骤执行记录:")
        
        for step_exec in step_executions:
            print(f"  步骤 {step_exec.order}: {step_exec.atomic_step.name} - 状态: {step_exec.status}")
        
        # 如果主执行记录状态是 failed，更新所有步骤状态为 failed
        if execution.status == 'failed':
            print(f"\n主执行记录状态为 {execution.status}，更新所有步骤状态...")
            
            updated_count = 0
            for step_exec in step_executions:
                if step_exec.status == 'pending':
                    step_exec.status = 'failed'
                    step_exec.completed_at = execution.completed_at or execution.started_at
                    step_exec.save()
                    updated_count += 1
                    print(f"  ✅ 更新步骤 {step_exec.order}: {step_exec.atomic_step.name} -> failed")
            
            print(f"\n✅ 总共更新了 {updated_count} 个步骤的状态")
            
        elif execution.status == 'success':
            print(f"\n主执行记录状态为 {execution.status}，更新所有步骤状态...")
            
            updated_count = 0
            for step_exec in step_executions:
                if step_exec.status == 'pending':
                    step_exec.status = 'success'
                    step_exec.completed_at = execution.completed_at or execution.started_at
                    step_exec.save()
                    updated_count += 1
                    print(f"  ✅ 更新步骤 {step_exec.order}: {step_exec.atomic_step.name} -> success")
            
            print(f"\n✅ 总共更新了 {updated_count} 个步骤的状态")
        
        else:
            print(f"\n主执行记录状态为 {execution.status}，无需更新步骤状态")
        
        # 再次检查更新后的状态
        print(f"\n=== 更新后的状态 ===")
        step_executions = StepExecution.objects.filter(pipeline_execution=execution).order_by('order')
        for step_exec in step_executions:
            print(f"  步骤 {step_exec.order}: {step_exec.atomic_step.name} - 状态: {step_exec.status}")
        
        print(f"\n🎉 修复完成！")
        
    except PipelineExecution.DoesNotExist:
        print("❌ 未找到第27号执行记录")
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_execution_27_step_status()
