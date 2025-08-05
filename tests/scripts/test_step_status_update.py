#!/usr/bin/env python3
"""
测试步骤状态更新功能
"""

import os
import sys
import django
import asyncio
import logging

# 设置路径
sys.path.insert(0, '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

try:
    django.setup()
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

from django.utils import timezone
from cicd_integrations.models import PipelineExecution, StepExecution
from cicd_integrations.tasks import _update_step_executions_status

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_step_status_update():
    """测试步骤状态更新"""
    print("=== 测试步骤状态更新功能 ===")
    
    try:
        from asgiref.sync import sync_to_async
        
        # 获取最新的远程执行记录
        executions = await sync_to_async(list)(PipelineExecution.objects.filter(
            pipeline__execution_mode='remote'
        ).order_by('-created_at')[:3])
        
        print(f"找到 {len(executions)} 个远程执行记录")
        
        for execution in executions:
            print(f"\n--- 执行记录 {execution.id} ---")
            print(f"流水线: {execution.pipeline.name}")
            print(f"状态: {execution.status}")
            print(f"外部ID: {execution.external_id}")
            
            # 获取步骤执行记录
            step_executions = await sync_to_async(list)(StepExecution.objects.filter(
                pipeline_execution=execution
            ).order_by('order'))
            
            print(f"步骤数量: {len(step_executions)}")
            
            if step_executions:
                print("当前步骤状态:")
                for step_exec in step_executions:
                    print(f"  - {step_exec.atomic_step.name}: {step_exec.status}")
                
                # 如果所有步骤都是pending，且流水线已完成，则更新步骤状态
                all_pending = all(step.status == 'pending' for step in step_executions)
                execution_completed = execution.status in ['success', 'failed', 'cancelled', 'timeout']
                
                if all_pending and execution_completed:
                    print(f"检测到步骤状态未更新，执行更新...")
                    await _update_step_executions_status(execution, execution.status)
                    
                    # 重新获取步骤状态
                    updated_steps = await sync_to_async(list)(StepExecution.objects.filter(
                        pipeline_execution=execution
                    ).order_by('order'))
                    
                    print("更新后的步骤状态:")
                    for step_exec in updated_steps:
                        print(f"  - {step_exec.atomic_step.name}: {step_exec.status}")
                else:
                    print("步骤状态正常，无需更新")
            else:
                print("没有找到步骤执行记录")
        
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_step_status_update())
