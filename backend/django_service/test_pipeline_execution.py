#!/usr/bin/env python3
"""
测试流水线执行脚本
创建并执行一个测试流水线，用于演示WebSocket实时监控功能
"""

import os
import sys
import django
from django.conf import settings

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from cicd_integrations.models import PipelineExecution
from cicd_integrations.executors.sync_pipeline_executor import SyncPipelineExecutor
from django.contrib.auth import get_user_model
import time
import asyncio
from asgiref.sync import sync_to_async

User = get_user_model()

def create_test_pipeline():
    """创建一个测试流水线"""
    print("🔧 创建测试流水线...")
    
    # 获取测试用户
    try:
        user = User.objects.get(username='admin')
    except User.DoesNotExist:
        print("❌ 用户 'admin' 不存在，请先运行 create_test_user.py")
        return None
    
    # 创建流水线
    pipeline, created = Pipeline.objects.get_or_create(
        name='WebSocket测试流水线',
        defaults={
            'description': '用于测试WebSocket实时监控的示例流水线',
            'created_by': user,
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ 创建新流水线: {pipeline.name}")
        
        # 创建流水线步骤
        steps = [
            {'name': '环境检查', 'command': 'echo "检查环境..." && sleep 3', 'order': 1},
            {'name': '代码拉取', 'command': 'echo "拉取代码..." && sleep 4', 'order': 2},
            {'name': '依赖安装', 'command': 'echo "安装依赖..." && sleep 5', 'order': 3},
            {'name': '单元测试', 'command': 'echo "运行测试..." && sleep 3', 'order': 4},
            {'name': '构建应用', 'command': 'echo "构建应用..." && sleep 4', 'order': 5},
            {'name': '部署验证', 'command': 'echo "验证部署..." && sleep 2', 'order': 6},
        ]
        
        for step_data in steps:
            PipelineStep.objects.create(
                pipeline=pipeline,
                **step_data
            )
        
        print(f"✅ 创建了 {len(steps)} 个流水线步骤")
    else:
        print(f"✅ 使用现有流水线: {pipeline.name}")
    
    return pipeline

def execute_pipeline(pipeline):
    """执行流水线"""
    print(f"🚀 开始执行流水线: {pipeline.name}")
    
    # 获取测试用户
    user = User.objects.get(username='admin')
    
    # 创建执行记录
    execution = Execution.objects.create(
        pipeline=pipeline,
        triggered_by=user,
        status='pending'
    )
    
    print(f"📋 创建执行记录: ID={execution.id}")
    print(f"🌐 前端监控页面: http://localhost:3000/executions/{execution.id}")
    print("=" * 60)
    
    # 等待一下让用户有时间打开前端页面
    print("⏳ 等待10秒，请在前端打开监控页面...")
    for i in range(10, 0, -1):
        print(f"⏱️  {i}秒后开始执行...")
        time.sleep(1)
    
    print("🎬 开始执行流水线！")
    
    # 执行流水线
    executor = SyncPipelineExecutor(execution)
    executor.execute()
    
    print(f"✅ 流水线执行完成！状态: {execution.status}")
    return execution

def main():
    """主函数"""
    print("🎯 AnsFlow WebSocket实时监控演示")
    print("=" * 60)
    
    # 创建测试流水线
    pipeline = create_test_pipeline()
    if not pipeline:
        return
    
    print("\n📖 使用说明:")
    print("1. 确保前端服务运行在 http://localhost:3000")
    print("2. 使用 admin/admin123 登录")
    print("3. 当流水线开始执行时，在前端打开监控页面查看实时状态")
    print("4. 您将看到实时的执行状态、步骤进度和日志输出")
    
    # 询问是否开始执行
    response = input("\n是否开始执行流水线？(y/N): ").strip().lower()
    if response in ['y', 'yes']:
        execution = execute_pipeline(pipeline)
        print(f"\n🎉 演示完成！")
        print(f"📊 执行ID: {execution.id}")
        print(f"📈 最终状态: {execution.status}")
    else:
        print("❌ 用户取消执行")

if __name__ == '__main__':
    main()
