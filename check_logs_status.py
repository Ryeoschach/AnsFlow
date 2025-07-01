#!/usr/bin/env python3
"""
检查执行记录的日志状态
"""
import os
import sys
import django

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_service.settings')
django.setup()

from cicd_integrations.models import PipelineExecution, StepExecution

def main():
    print("检查最近的执行记录的日志状态...")
    
    # 获取最近10条执行记录
    executions = PipelineExecution.objects.select_related('cicd_tool').order_by('-id')[:10]
    
    for execution in executions:
        print(f"\n=== 执行记录 {execution.id} ===")
        print(f"状态: {execution.status}")
        print(f"工具: {execution.cicd_tool.name if execution.cicd_tool else 'None'}")
        print(f"外部ID: {execution.external_id}")
        print(f"主执行日志长度: {len(execution.logs) if execution.logs else 0}")
        if execution.logs:
            print(f"主执行日志预览: {execution.logs[:100]}...")
        
        # 检查步骤日志
        steps = execution.steps.all().order_by('order')
        print(f"步骤数量: {steps.count()}")
        
        for step in steps:
            print(f"  步骤 {step.order}: {step.status}")
            print(f"    原子步骤: {step.atomic_step.name if step.atomic_step else 'None'}")
            print(f"    日志长度: {len(step.logs) if step.logs else 0}")
            if step.logs:
                print(f"    日志预览: {step.logs[:50]}...")

if __name__ == "__main__":
    main()
