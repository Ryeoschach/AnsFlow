#!/usr/bin/env python3
"""
查看步骤执行日志
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from cicd_integrations.models import StepExecution, PipelineExecution

def view_execution_logs():
    """查看最近的执行日志"""
    
    print("🔍 查看最近的执行日志...")
    
    # 获取最近的流水线执行记录
    recent_execution = PipelineExecution.objects.filter(
        status='success'
    ).order_by('-created_at').first()
    
    if not recent_execution:
        print("❌ 没有找到成功的执行记录")
        return
    
    print(f"✅ 找到执行记录: {recent_execution.id} - {recent_execution.pipeline.name}")
    print(f"执行状态: {recent_execution.status}")
    print(f"执行时间: {recent_execution.created_at}")
    
    # 获取步骤执行记录
    step_executions = StepExecution.objects.filter(
        pipeline_execution=recent_execution
    ).order_by('order')
    
    print(f"\n📋 步骤执行日志 ({step_executions.count()} 个步骤):")
    print("=" * 60)
    
    for step_execution in step_executions:
        step_name = step_execution.step_name
        print(f"\n=== 步骤 {step_execution.order}: {step_name} ===")
        print(f"状态: {step_execution.status}")
        print(f"开始时间: {step_execution.started_at}")
        print(f"完成时间: {step_execution.completed_at}")
        
        if step_execution.logs:
            print(f"日志:\n{step_execution.logs}")
        else:
            print("没有日志内容")
        
        if step_execution.error_message:
            print(f"错误信息: {step_execution.error_message}")
        
        print("-" * 40)

if __name__ == '__main__':
    view_execution_logs()
