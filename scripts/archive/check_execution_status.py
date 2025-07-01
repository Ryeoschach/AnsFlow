#!/usr/bin/env python
"""
检查流水线执行状态
"""
import os
import sys
import django

# 添加 Django 项目路径
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_service.settings')

# 初始化 Django
django.setup()

from cicd_integrations.models import PipelineExecution

def check_execution_status(execution_id):
    """检查指定执行记录的状态"""
    try:
        execution = PipelineExecution.objects.select_related(
            'pipeline', 'cicd_tool'
        ).get(id=execution_id)
        
        print("=" * 60)
        print(f"📋 执行记录 #{execution_id} 状态报告")
        print("=" * 60)
        print(f"🎯 流水线: {execution.pipeline.name}")
        print(f"🔧 CI/CD工具: {execution.cicd_tool.name if execution.cicd_tool else 'None'}")
        print(f"📊 状态: {execution.status}")
        print(f"🆔 外部ID: {execution.external_id}")
        print(f"🕐 创建时间: {execution.created_at}")
        print(f"🚀 开始时间: {execution.started_at}")
        print(f"✅ 完成时间: {execution.completed_at}")
        print(f"📝 触发类型: {execution.trigger_type}")
        print(f"👤 触发者: {execution.triggered_by.username if execution.triggered_by else 'system'}")
        
        if execution.logs:
            print(f"📄 日志:")
            print("-" * 40)
            print(execution.logs[:500] + "..." if len(execution.logs) > 500 else execution.logs)
        else:
            print("📄 日志: 暂无")
            
        print("=" * 60)
        
        return execution
        
    except PipelineExecution.DoesNotExist:
        print(f"❌ 执行记录 #{execution_id} 不存在")
        return None
    except Exception as e:
        print(f"❌ 检查执行状态时出错: {e}")
        return None

def list_recent_executions(limit=5):
    """列出最近的执行记录"""
    executions = PipelineExecution.objects.select_related(
        'pipeline', 'cicd_tool'
    ).order_by('-created_at')[:limit]
    
    print("=" * 80)
    print(f"📋 最近 {limit} 个执行记录")
    print("=" * 80)
    
    for execution in executions:
        print(f"#{execution.id:3d} | {execution.pipeline.name:20s} | {execution.status:10s} | {execution.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("=" * 80)

if __name__ == "__main__":
    # 检查最近的执行记录
    list_recent_executions()
    
    # 检查最新的执行记录（ID 19）
    check_execution_status(19)
