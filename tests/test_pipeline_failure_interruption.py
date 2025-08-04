#!/usr/bin/env python3
"""
测试流水线失败中断功能
验证当前面的步骤失败时，后面的步骤会被取消并显示相应提示
"""

import os
import sys
import django

# 设置Django环境
sys.path.insert(0, '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

try:
    django.setup()
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

from pipelines.models import Pipeline
from cicd_integrations.models import PipelineExecution, StepExecution, AtomicStep
from project_management.models import Project
from pipelines.services.parallel_execution import ParallelExecutionService
from django.contrib.auth.models import User
from django.utils import timezone


def create_test_pipeline():
    """创建测试流水线"""
    print("=== 创建测试流水线 ===")
    
    # 获取或创建用户
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    # 获取或创建项目
    project, created = Project.objects.get_or_create(
        name='测试项目',
        defaults={
            'description': '用于测试的项目',
            'owner': user
        }
    )
    
    # 创建测试流水线
    pipeline = Pipeline.objects.create(
        name='失败中断测试流水线',
        description='测试步骤失败时的中断功能',
        created_by=user,
        project=project,
        execution_mode='local'
    )
    
    # 创建多个原子步骤
    steps = []
    step_configs = [
        {'name': '步骤1-准备环境', 'step_type': 'shell', 'order': 1, 'should_fail': False},
        {'name': '步骤2-构建代码', 'step_type': 'shell', 'order': 2, 'should_fail': True},  # 这个步骤会失败
        {'name': '步骤3-运行测试', 'step_type': 'shell', 'order': 3, 'should_fail': False},
        {'name': '步骤4-部署应用', 'step_type': 'shell', 'order': 4, 'should_fail': False},
        {'name': '步骤5-清理资源', 'step_type': 'shell', 'order': 5, 'should_fail': False},
    ]
    
    for config in step_configs:
        step = AtomicStep.objects.create(
            pipeline=pipeline,
            name=config['name'],
            step_type=config['step_type'],
            order=config['order'],
            created_by=user,
            parameters={
                'command': f"echo '执行{config['name']}'",
                'should_fail': config['should_fail']  # 用于测试
            }
        )
        steps.append(step)
        print(f"创建步骤: {step.name} (order: {step.order})")
    
    return pipeline, steps


def simulate_sequential_execution_with_failure(pipeline, steps):
    """模拟串行执行并测试失败中断"""
    print(f"\n=== 模拟串行执行（步骤失败中断测试）===")
    
    # 创建流水线执行记录
    user = User.objects.get(username='test_user')
    pipeline_execution = PipelineExecution.objects.create(
        pipeline=pipeline,
        triggered_by=user,
        trigger_type='manual',
        status='running'
    )
    
    # 使用并行执行服务的串行执行方法
    service = ParallelExecutionService()
    
    # 构造stage数据结构
    stage = {
        'stage_number': 1,
        'parallel': False,
        'items': steps
    }
    
    print(f"开始执行流水线，共 {len(steps)} 个步骤...")
    
    # 模拟步骤执行，在第2个步骤时失败
    try:
        # 手动模拟执行过程
        for index, step in enumerate(steps):
            print(f"\n执行步骤 {index + 1}: {step.name}")
            
            # 创建步骤执行记录
            step_execution = StepExecution.objects.create(
                pipeline_execution=pipeline_execution,
                atomic_step=step,
                status='running',
                order=step.order,
                started_at=timezone.now()
            )
            
            # 模拟步骤执行结果
            should_fail = step.parameters.get('should_fail', False)
            
            if should_fail:
                # 步骤失败
                step_execution.status = 'failed'
                step_execution.error_message = f"步骤 {step.name} 执行失败（模拟失败）"
                step_execution.completed_at = timezone.now()
                step_execution.save()
                
                print(f"  ❌ 步骤 {step.name} 失败: {step_execution.error_message}")
                
                # 使用我们的失败中断功能
                remaining_steps = steps[index + 1:]
                if remaining_steps:
                    print(f"  🚫 取消后续 {len(remaining_steps)} 个步骤...")
                    service._cancel_remaining_steps(remaining_steps, pipeline_execution, step.name)
                    
                break
            else:
                # 步骤成功
                step_execution.status = 'success'
                step_execution.completed_at = timezone.now()
                step_execution.save()
                
                print(f"  ✅ 步骤 {step.name} 成功完成")
        
        # 更新流水线执行状态
        pipeline_execution.status = 'failed'
        pipeline_execution.completed_at = timezone.now()
        pipeline_execution.save()
        
    except Exception as e:
        print(f"执行过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
    
    return pipeline_execution


def check_execution_results(pipeline_execution):
    """检查执行结果"""
    print(f"\n=== 检查执行结果 ===")
    
    # 获取所有步骤执行记录
    step_executions = StepExecution.objects.filter(
        pipeline_execution=pipeline_execution
    ).order_by('order')
    
    print(f"流水线执行状态: {pipeline_execution.status}")
    print(f"总步骤数: {step_executions.count()}")
    
    print(f"\n步骤执行详情:")
    for step_exec in step_executions:
        status_emoji = {
            'success': '✅',
            'failed': '❌', 
            'cancelled': '🚫',
            'running': '🔄',
            'pending': '⏳'
        }.get(step_exec.status, '❓')
        
        print(f"  {status_emoji} 步骤 {step_exec.order}: {step_exec.atomic_step.name}")
        print(f"     状态: {step_exec.status}")
        if step_exec.error_message:
            print(f"     消息: {step_exec.error_message}")
        if step_exec.started_at:
            print(f"     开始时间: {step_exec.started_at.strftime('%H:%M:%S')}")
        if step_exec.completed_at:
            print(f"     完成时间: {step_exec.completed_at.strftime('%H:%M:%S')}")
        print()
    
    # 验证预期结果
    print("=== 验证结果 ===")
    success_count = step_executions.filter(status='success').count()
    failed_count = step_executions.filter(status='failed').count()
    cancelled_count = step_executions.filter(status='cancelled').count()
    
    print(f"成功步骤: {success_count}")
    print(f"失败步骤: {failed_count}")
    print(f"取消步骤: {cancelled_count}")
    
    # 验证是否符合预期
    expected_success = 1  # 第1步成功
    expected_failed = 1   # 第2步失败
    expected_cancelled = 3  # 第3,4,5步被取消
    
    if (success_count == expected_success and 
        failed_count == expected_failed and 
        cancelled_count == expected_cancelled):
        print("✅ 失败中断功能验证成功！")
        
        # 检查取消步骤的消息
        cancelled_steps = step_executions.filter(status='cancelled')
        for cancelled_step in cancelled_steps:
            if "前面有失败的步骤（步骤2-构建代码），后面步骤取消执行" in cancelled_step.error_message:
                print(f"✅ 取消消息正确: {cancelled_step.atomic_step.name}")
            else:
                print(f"❌ 取消消息错误: {cancelled_step.error_message}")
    else:
        print("❌ 失败中断功能验证失败！")
        print(f"预期: 成功={expected_success}, 失败={expected_failed}, 取消={expected_cancelled}")
        print(f"实际: 成功={success_count}, 失败={failed_count}, 取消={cancelled_count}")


def cleanup_test_data():
    """清理测试数据"""
    print(f"\n=== 清理测试数据 ===")
    
    # 删除测试流水线（会级联删除相关数据）
    pipelines = Pipeline.objects.filter(name__contains='失败中断测试')
    count = pipelines.count()
    pipelines.delete()
    
    print(f"清理了 {count} 个测试流水线")


def main():
    """主函数"""
    print("🚀 流水线失败中断功能测试")
    print("=" * 50)
    
    try:
        # 清理之前的测试数据
        cleanup_test_data()
        
        # 创建测试流水线
        pipeline, steps = create_test_pipeline()
        
        # 模拟执行
        pipeline_execution = simulate_sequential_execution_with_failure(pipeline, steps)
        
        # 检查结果
        check_execution_results(pipeline_execution)
        
        print("\n🎉 测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试数据
        cleanup_test_data()


if __name__ == "__main__":
    main()
