#!/usr/bin/env python3
"""
测试执行详情页面步骤显示修复
"""

import os
import sys
import django
import asyncio
import requests
import json

# 设置路径
sys.path.insert(0, '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

try:
    django.setup()
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

from cicd_integrations.models import PipelineExecution, StepExecution, AtomicStep
from pipelines.models import Pipeline

def test_execution_details_api():
    """测试执行详情API返回的数据"""
    print("=== 测试执行详情API和步骤显示修复 ===")
    
    try:
        # 获取最新的执行记录
        latest_execution = PipelineExecution.objects.select_related('pipeline').order_by('-id').first()
        
        if not latest_execution:
            print("❌ 没有找到执行记录")
            return
        
        execution_id = latest_execution.id
        print(f"📋 测试执行记录: {execution_id}")
        print(f"   流水线: {latest_execution.pipeline.name}")
        print(f"   状态: {latest_execution.status}")
        print(f"   模式: {latest_execution.pipeline.execution_mode}")
        
        # 检查数据库中的 StepExecution 记录
        step_executions = StepExecution.objects.filter(pipeline_execution=latest_execution)
        print(f"   数据库中的步骤执行记录数量: {step_executions.count()}")
        
        if step_executions.exists():
            print("   步骤执行记录:")
            for step_exec in step_executions:
                print(f"     - {step_exec.atomic_step.name} (状态: {step_exec.status})")
        else:
            print("   ⚠️  数据库中没有步骤执行记录")
            
            # 检查原子步骤
            atomic_steps = AtomicStep.objects.filter(pipeline=latest_execution.pipeline).order_by('order')
            print(f"   原子步骤数量: {atomic_steps.count()}")
            for step in atomic_steps:
                print(f"     - {step.name} ({step.step_type})")
        
        # 测试API返回
        api_url = f"http://127.0.0.1:8000/api/v1/executions/{execution_id}/"
        
        print(f"\n🌐 测试API: {api_url}")
        
        try:
            response = requests.get(api_url, timeout=10)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                step_executions_data = data.get('step_executions', [])
                print(f"   API返回的步骤执行记录数量: {len(step_executions_data)}")
                
                if step_executions_data:
                    print("   API返回的步骤:")
                    for step_data in step_executions_data:
                        step_name = step_data.get('atomic_step_name', '未知')
                        step_status = step_data.get('status', '未知')
                        print(f"     - {step_name} (状态: {step_status})")
                else:
                    print("   ❌ API没有返回步骤执行记录")
                    print("   检查序列化器是否正确配置...")
                
            else:
                print(f"   ❌ API请求失败: {response.status_code}")
                print(f"   响应: {response.text[:200]}")
                
        except requests.RequestException as e:
            print(f"   ❌ API请求异常: {e}")
        
        # 生成修复建议
        print(f"\n🔧 修复状态检查:")
        
        # 1. 检查prefetch_related是否生效
        print("1. 检查视图是否预取了step_executions...")
        
        # 2. 检查是否为远程执行创建了StepExecution记录
        if latest_execution.pipeline.execution_mode == 'remote':
            if step_executions.exists():
                print("   ✅ 远程执行已创建步骤记录")
            else:
                print("   ❌ 远程执行缺少步骤记录")
        
        print(f"\n📝 前端页面测试:")
        print(f"请访问: http://127.0.0.1:3000/executions/{execution_id}")
        print(f"检查页面是否显示执行步骤")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_create_missing_step_executions():
    """为缺少步骤执行记录的远程执行补充数据"""
    print("\n=== 为现有远程执行补充步骤执行记录 ===")
    
    try:
        # 查找远程执行但没有步骤记录的执行
        remote_executions = PipelineExecution.objects.filter(
            pipeline__execution_mode='remote'
        ).select_related('pipeline')
        
        for execution in remote_executions:
            step_count = StepExecution.objects.filter(pipeline_execution=execution).count()
            atomic_count = AtomicStep.objects.filter(pipeline=execution.pipeline).count()
            
            if step_count == 0 and atomic_count > 0:
                print(f"🔧 为执行 {execution.id} 补充步骤记录...")
                
                atomic_steps = AtomicStep.objects.filter(
                    pipeline=execution.pipeline
                ).order_by('order')
                
                for index, atomic_step in enumerate(atomic_steps):
                    step_execution = StepExecution.objects.create(
                        pipeline_execution=execution,
                        atomic_step=atomic_step,
                        status='pending',  # 远程执行的状态可能需要从外部同步
                        order=index + 1
                    )
                    print(f"   ✅ 创建步骤记录: {atomic_step.name}")
                
        print("✅ 步骤记录补充完成")
        
    except Exception as e:
        print(f"❌ 补充步骤记录失败: {e}")

if __name__ == "__main__":
    test_execution_details_api()
    test_create_missing_step_executions()
    print("\n" + "="*50)
    print("🎯 下一步: 重新运行远程执行测试，验证步骤记录是否正常创建")
