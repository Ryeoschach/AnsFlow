#!/usr/bin/env python3
"""
批量修复所有待处理的步骤执行状态
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
from django.utils import timezone

def fix_all_pending_steps():
    """修复所有待处理的步骤执行状态"""
    print("=" * 60)
    print("🔧 批量修复步骤执行状态")
    print("=" * 60)
    
    # 查找所有已完成但仍有 pending 步骤的执行记录
    completed_executions = PipelineExecution.objects.filter(
        status__in=['success', 'failed', 'cancelled', 'timeout']
    ).prefetch_related('step_executions')
    
    fixed_count = 0
    execution_count = 0
    
    for execution in completed_executions:
        pending_steps = execution.step_executions.filter(status='pending')
        
        if pending_steps.exists():
            execution_count += 1
            print(f"\n📋 处理执行记录 {execution.id} (状态: {execution.status})")
            print(f"   发现 {pending_steps.count()} 个 pending 步骤")
            
            # 根据执行记录状态确定步骤的最终状态
            if execution.status == 'success':
                final_status = 'success'
            elif execution.status == 'timeout':
                final_status = 'timeout'
            else:
                final_status = 'failed'  # failed, cancelled
            
            for step in pending_steps:
                print(f"   - 修复步骤: {step.atomic_step.name} (pending → {final_status})")
                
                step.status = final_status
                step.completed_at = timezone.now()
                if not step.started_at:
                    step.started_at = step.completed_at
                step.save()
                
                fixed_count += 1
    
    print(f"\n" + "=" * 60)
    print(f"✅ 修复完成!")
    print(f"📊 统计信息:")
    print(f"   - 处理的执行记录: {execution_count} 个")
    print(f"   - 修复的步骤: {fixed_count} 个")
    
    if fixed_count == 0:
        print("🎉 所有步骤状态都是正确的，无需修复！")
    
    print("=" * 60)

if __name__ == "__main__":
    fix_all_pending_steps()
