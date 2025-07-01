#!/usr/bin/env python3
"""
手动运行监控任务进行调试
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
from cicd_integrations.tasks import _update_step_executions_status
from django.utils import timezone
import asyncio

async def debug_step_update():
    """调试步骤状态更新"""
    print("=" * 60)
    print("🔍 手动调试步骤状态更新")
    print("=" * 60)
    
    # 获取第32号执行记录
    execution = PipelineExecution.objects.get(id=32)
    print(f"\n📋 执行记录 {execution.id}:")
    print(f"   状态: {execution.status}")
    print(f"   外部ID: {execution.external_id}")
    
    # 获取步骤执行记录
    steps = StepExecution.objects.filter(pipeline_execution=execution).order_by('order')
    print(f"\n📝 步骤执行记录 ({steps.count()} 个):")
    for step in steps:
        print(f"   - {step.atomic_step.name}: {step.status}")
    
    # 手动调用更新函数
    print(f"\n🔧 手动调用 _update_step_executions_status...")
    try:
        await _update_step_executions_status(execution, execution.status)
        print("   ✅ 调用成功")
    except Exception as e:
        print(f"   ❌ 调用失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 重新检查步骤状态
    steps = StepExecution.objects.filter(pipeline_execution=execution).order_by('order')
    print(f"\n📊 更新后的步骤状态:")
    for step in steps:
        print(f"   - {step.atomic_step.name}: {step.status}")
        print(f"     开始: {step.started_at}")
        print(f"     完成: {step.completed_at}")

if __name__ == "__main__":
    asyncio.run(debug_step_update())
