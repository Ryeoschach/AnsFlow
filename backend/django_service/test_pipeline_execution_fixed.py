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

from pipelines.models import Pipeline
from cicd_integrations.models import PipelineExecution, AtomicStep
from cicd_integrations.executors.sync_pipeline_executor import SyncPipelineExecutor
from django.contrib.auth import get_user_model
from project_management.models import Project
import time

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
    
    # 创建或获取测试项目
    project, created = Project.objects.get_or_create(
        name='WebSocket测试项目',
        defaults={
            'description': '用于WebSocket实时监控测试的项目',
            'owner': user,
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ 创建新项目: {project.name}")
    else:
        print(f"✅ 使用现有项目: {project.name}")
    
    # 创建流水线
    pipeline, created = Pipeline.objects.get_or_create(
        name='WebSocket测试流水线',
        project=project,
        defaults={
            'description': '用于测试WebSocket实时监控的示例流水线',
            'created_by': user,
            'status': 'pending'
        }
    )
    
    if created:
        print(f"✅ 创建新流水线: {pipeline.name}")
        
        # 删除旧的原子步骤（如果有的话）
        pipeline.atomic_steps.all().delete()
        
        # 创建原子步骤
        steps = [
            {'name': '环境检查', 'step_type': 'custom', 'order': 1, 
             'config': {'command': 'echo "检查环境..." && sleep 3'}},
            {'name': '代码拉取', 'step_type': 'fetch_code', 'order': 2,
             'config': {'command': 'echo "拉取代码..." && sleep 4'}},
            {'name': '依赖安装', 'step_type': 'build', 'order': 3,
             'config': {'command': 'echo "安装依赖..." && sleep 5'}},
            {'name': '单元测试', 'step_type': 'test', 'order': 4,
             'config': {'command': 'echo "运行测试..." && sleep 3'}},
            {'name': '构建应用', 'step_type': 'build', 'order': 5,
             'config': {'command': 'echo "构建应用..." && sleep 4'}},
            {'name': '部署验证', 'step_type': 'deploy', 'order': 6,
             'config': {'command': 'echo "验证部署..." && sleep 2'}},
        ]
        
        for step_data in steps:
            AtomicStep.objects.create(
                pipeline=pipeline,
                created_by=user,
                **step_data
            )
        
        print(f"✅ 创建了 {len(steps)} 个原子步骤")
    else:
        print(f"✅ 使用现有流水线: {pipeline.name}")
        # 确保原子步骤存在
        if pipeline.atomic_steps.count() == 0:
            print("🔧 流水线没有原子步骤，正在创建...")
            steps = [
                {'name': '环境检查', 'step_type': 'custom', 'order': 1,
                 'config': {'command': 'echo "检查环境..." && sleep 3'}},
                {'name': '代码拉取', 'step_type': 'fetch_code', 'order': 2,
                 'config': {'command': 'echo "拉取代码..." && sleep 4'}},
                {'name': '依赖安装', 'step_type': 'build', 'order': 3,
                 'config': {'command': 'echo "安装依赖..." && sleep 5'}},
                {'name': '单元测试', 'step_type': 'test', 'order': 4,
                 'config': {'command': 'echo "运行测试..." && sleep 3'}},
                {'name': '构建应用', 'step_type': 'build', 'order': 5,
                 'config': {'command': 'echo "构建应用..." && sleep 4'}},
                {'name': '部署验证', 'step_type': 'deploy', 'order': 6,
                 'config': {'command': 'echo "验证部署..." && sleep 2'}},
            ]
            
            for step_data in steps:
                AtomicStep.objects.create(
                    pipeline=pipeline,
                    created_by=user,
                    **step_data
                )
            
            print(f"✅ 创建了 {len(steps)} 个原子步骤")
    
    return pipeline

def execute_pipeline(pipeline):
    """执行流水线"""
    print(f"🚀 开始执行流水线: {pipeline.name}")
    
    # 获取测试用户
    user = User.objects.get(username='admin')
    
    # 创建执行记录
    execution = PipelineExecution.objects.create(
        pipeline=pipeline,
        triggered_by=user,
        status='pending',
        external_id=f'local-{pipeline.id}-{int(time.time())}',  # 生成一个唯一ID
        trigger_type='manual'
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
    executor = SyncPipelineExecutor()
    result = executor.execute_pipeline(execution.id)
    
    # 刷新执行对象以获取最新状态
    execution.refresh_from_db()
    
    print(f"✅ 流水线执行完成！状态: {execution.status}")
    print(f"📝 执行结果: {result.get('status', 'unknown')}")
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
        print(f"🌐 前端查看: http://localhost:3000/executions/{execution.id}")
    else:
        print("❌ 用户取消执行")

if __name__ == '__main__':
    main()
