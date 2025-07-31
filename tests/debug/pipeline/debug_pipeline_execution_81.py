#!/usr/bin/env python3
"""
查看流水线执行81的详细信息
"""

import os
import sys
import django

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from cicd_integrations.models import StepExecution, PipelineExecution, AtomicStep

def check_pipeline_execution_81():
    """检查流水线执行81的详情"""
    print("=== 检查流水线执行81的详情 ===")
    
    # 查找流水线执行记录
    try:
        exec_run = PipelineExecution.objects.get(id=81)
        print(f"✅ 找到流水线执行: {exec_run}")
        print(f"   流水线ID: {exec_run.pipeline.id}")
        print(f"   流水线名称: {exec_run.pipeline.name}")
        print(f"   执行状态: {exec_run.status}")
        print(f"   开始时间: {exec_run.started_at}")
        print(f"   结束时间: {exec_run.completed_at}")
        
        # 查找相关的步骤执行记录
        steps = StepExecution.objects.filter(pipeline_execution=exec_run)
        print(f"\n📦 步骤执行记录 ({steps.count()}个):")
        
        for step in steps:
            print(f"\n步骤执行ID: {step.id}")
            print(f"  状态: {step.status}")
            print(f"  开始时间: {step.started_at}")
            print(f"  结束时间: {step.completed_at}")
            
            if step.atomic_step:
                print(f"  原子步骤ID: {step.atomic_step.id}")
                print(f"  步骤类型: {step.atomic_step.step_type}")
                print(f"  步骤名称: {step.atomic_step.name}")
                print(f"  参数: {step.atomic_step.parameters}")
                
                # 检查具体的参数
                if step.atomic_step.step_type == 'docker_push':
                    params = step.atomic_step.parameters or {}
                    print(f"\n🔍 Docker Push 步骤参数分析:")
                    print(f"   image: {params.get('image', 'NOT FOUND')}")
                    print(f"   tag: {params.get('tag', 'NOT FOUND')}")
                    print(f"   registry_id: {params.get('registry_id', 'NOT FOUND')}")
                    print(f"   project_id: {params.get('project_id', 'NOT FOUND')}")
                    
                    if 'project_id' in params:
                        print(f"   ✅ project_id 字段存在: {params['project_id']}")
                    else:
                        print(f"   ❌ project_id 字段缺失!")
                        
                    # 检查错误信息
                    if step.error_message:
                        print(f"\n❌ 错误信息: {step.error_message}")
                        
            elif step.pipeline_step:
                print(f"  流水线步骤ID: {step.pipeline_step.id}")
                print(f"  步骤类型: {step.pipeline_step.step_type}")
                print(f"  步骤名称: {step.pipeline_step.name}")
                print(f"  参数: {step.pipeline_step.ansible_parameters}")
            else:
                print(f"  ⚠️ 无关联的步骤对象")
                
    except PipelineExecution.DoesNotExist:
        print("❌ 未找到流水线执行记录 ID: 81")
    except Exception as e:
        print(f"❌ 查询失败: {e}")

def check_step_207():
    """检查步骤207的详情"""
    print("\n=== 检查步骤207的详情 ===")
    
    try:
        step = AtomicStep.objects.get(id=207)
        print(f"✅ 找到原子步骤: {step}")
        print(f"   名称: {step.name}")
        print(f"   类型: {step.step_type}")
        print(f"   参数: {step.parameters}")
        
        if step.step_type == 'docker_push':
            params = step.parameters or {}
            print(f"\n🔍 Docker Push 步骤参数分析:")
            for key, value in params.items():
                print(f"   {key}: {value}")
                
            # 检查是否有project_id
            if 'project_id' in params:
                print(f"   ✅ project_id 字段存在: {params['project_id']}")
            else:
                print(f"   ❌ project_id 字段缺失!")
                
    except AtomicStep.DoesNotExist:
        print("❌ 未找到原子步骤 ID: 207")
    except Exception as e:
        print(f"❌ 查询失败: {e}")

if __name__ == '__main__':
    check_pipeline_execution_81()
    check_step_207()
