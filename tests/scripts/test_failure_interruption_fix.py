#!/usr/bin/env python3
"""
测试失败中断修复的脚本
验证 UnifiedCICDEngine 现在对所有本地执行都使用失败中断功能
"""

import os
import sys
import django
import json
from datetime import datetime

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

django.setup()

from pipelines.models import Pipeline, PipelineStep
from cicd_integrations.models import PipelineExecution, StepExecution
from cicd_integrations.services import UnifiedCICDEngine, execute_pipeline_task
from project_management.models import Project
from django.contrib.auth.models import User
from django.utils import timezone

def create_test_pipeline():
    """创建测试流水线"""
    print("📋 创建测试流水线...")
    
    # 获取或创建测试用户
    try:
        user = User.objects.get(username='admin')
    except User.DoesNotExist:
        user = User.objects.create_user('test_user', 'test@example.com', 'password')
    
    # 创建测试项目
    project = Project.objects.create(
        name=f"测试项目 {datetime.now().strftime('%H%M%S')}",
        description="失败中断测试项目",
        owner=user
    )
    
    # 创建流水线
    pipeline_name = f"失败中断测试流水线 {datetime.now().strftime('%H%M%S')}"
    pipeline = Pipeline.objects.create(
        name=pipeline_name,
        description="测试失败中断功能",
        execution_mode='local',
        project=project,
        created_by=user
    )
    
    # 创建步骤
    step1 = PipelineStep.objects.create(
        pipeline=pipeline,
        name="成功步骤1",
        step_type="shell_command",
        command="echo '步骤1执行成功'",
        order=1
    )
    
    step2 = PipelineStep.objects.create(
        pipeline=pipeline,
        name="成功步骤2",
        step_type="shell_command", 
        command="echo '步骤2执行成功'",
        order=2
    )
    
    step3 = PipelineStep.objects.create(
        pipeline=pipeline,
        name="失败步骤3",
        step_type="shell_command",
        command="echo '步骤3故意失败' && exit 1",
        order=3
    )
    
    step4 = PipelineStep.objects.create(
        pipeline=pipeline,
        name="应被取消的步骤4",
        step_type="shell_command",
        command="echo '步骤4不应该执行'",
        order=4
    )
    
    step5 = PipelineStep.objects.create(
        pipeline=pipeline,
        name="应被取消的步骤5",
        step_type="shell_command",
        command="echo '步骤5不应该执行'",
        order=5
    )
    
    print(f"✅ 创建流水线: {pipeline.name}")
    print(f"   - 步骤数量: 5")
    print(f"   - 执行模式: {pipeline.execution_mode}")
    print(f"   - 流水线ID: {pipeline.id}")
    print(f"   - 项目: {project.name}")
    
    return pipeline, user, project

def test_failure_interruption_with_unified_engine():
    """测试统一引擎的失败中断功能"""
    print("\n🔧 测试统一引擎的失败中断功能")
    print("=" * 60)
    
    # 创建测试流水线
    pipeline, user, project = create_test_pipeline()
    
    try:
        # 创建流水线执行记录
        pipeline_execution = PipelineExecution.objects.create(
            pipeline=pipeline,
            triggered_by=user,
            status='pending',
            trigger_type='manual',
            trigger_data={'test': 'failure_interruption_fix'},
            parameters={}
        )
        
        print(f"📊 流水线执行记录创建: {pipeline_execution.id}")
        
        # 使用执行任务函数
        print("🚀 开始执行流水线...")
        start_time = timezone.now()
        
        # 执行流水线
        execute_pipeline_task(pipeline_execution.id)
        
        # 等待执行完成（给一些时间让异步任务完成）
        import time
        print("⏳ 等待执行完成...")
        time.sleep(5)
        
        end_time = timezone.now()
        execution_duration = (end_time - start_time).total_seconds()
        
        # 刷新执行记录
        pipeline_execution.refresh_from_db()
        
        print(f"\n📈 执行结果分析:")
        print(f"   - 流水线状态: {pipeline_execution.status}")
        print(f"   - 执行时长: {execution_duration:.2f}秒")
        print(f"   - 触发数据: {json.dumps(pipeline_execution.trigger_data, indent=2, ensure_ascii=False)}")
        
        # 检查步骤执行情况
        step_executions = StepExecution.objects.filter(
            pipeline_execution=pipeline_execution
        ).order_by('order')
        
        print(f"\n📝 步骤执行详情:")
        success_count = 0
        failed_count = 0
        cancelled_count = 0
        
        for step_exec in step_executions:
            status_icon = {
                'success': '✅',
                'failed': '❌', 
                'cancelled': '⏹️',
                'pending': '⏳',
                'running': '🔄'
            }.get(step_exec.status, '❓')
            
            # 获取步骤名称
            step_name = "未知步骤"
            if step_exec.pipeline_step:
                step_name = step_exec.pipeline_step.name
            elif step_exec.atomic_step:
                step_name = step_exec.atomic_step.name
            
            print(f"   {status_icon} 步骤 {step_exec.order}: {step_name}")
            print(f"      状态: {step_exec.status}")
            if step_exec.started_at:
                print(f"      开始时间: {step_exec.started_at.strftime('%H:%M:%S')}")
            if step_exec.completed_at:
                print(f"      完成时间: {step_exec.completed_at.strftime('%H:%M:%S')}")
                duration = (step_exec.completed_at - step_exec.started_at).total_seconds()
                print(f"      执行时长: {duration:.2f}秒")
            if step_exec.error_message:
                print(f"      错误信息: {step_exec.error_message}")
            if step_exec.logs:
                print(f"      日志: {step_exec.logs[:100]}...")
            print()
            
            if step_exec.status == 'success':
                success_count += 1
            elif step_exec.status == 'failed':
                failed_count += 1
            elif step_exec.status == 'cancelled':
                cancelled_count += 1
        
        # 验证失败中断逻辑
        print(f"📊 统计信息:")
        print(f"   - 成功步骤: {success_count}")
        print(f"   - 失败步骤: {failed_count}")  
        print(f"   - 取消步骤: {cancelled_count}")
        print(f"   - 总步骤数: {step_executions.count()}")
        
        # 验证预期结果
        print(f"\n🔍 验证失败中断功能:")
        
        # 预期结果：步骤1、2成功，步骤3失败，步骤4、5不被执行(不创建执行记录)
        expected_success = 2  # 步骤1、2
        expected_failed = 1   # 步骤3
        expected_total_executed = 3  # 只有前3个步骤被执行
        
        success = True
        
        if success_count != expected_success:
            print(f"   ❌ 成功步骤数不符合预期: 期望{expected_success}，实际{success_count}")
            success = False
        else:
            print(f"   ✅ 成功步骤数符合预期: {success_count}")
        
        if failed_count != expected_failed:
            print(f"   ❌ 失败步骤数不符合预期: 期望{expected_failed}，实际{failed_count}")
            success = False
        else:
            print(f"   ✅ 失败步骤数符合预期: {failed_count}")
        
        if step_executions.count() != expected_total_executed:
            print(f"   ❌ 执行步骤总数不符合预期: 期望{expected_total_executed}，实际{step_executions.count()}")
            success = False
        else:
            print(f"   ✅ 执行步骤总数符合预期: {step_executions.count()} (后续步骤被正确阻止)")
        
        if pipeline_execution.status != 'failed':
            print(f"   ❌ 流水线状态不符合预期: 期望'failed'，实际'{pipeline_execution.status}'")
            success = False
        else:
            print(f"   ✅ 流水线状态符合预期: {pipeline_execution.status}")
        
        if success:
            print(f"\n🎉 失败中断功能测试通过！")
            print("   修复生效：UnifiedCICDEngine 现在正确使用失败中断功能")
            print("   ✅ 当步骤失败时，后续步骤被正确阻止执行")
            print("   ✅ 失败中断在步骤级别生效，防止不必要的资源浪费")
        else:
            print(f"\n⚠️  失败中断功能测试未完全通过")
            print("   可能需要进一步调试")
        
        return success
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理测试数据
        print(f"\n🧹 清理测试数据...")
        try:
            # 删除步骤执行记录
            StepExecution.objects.filter(pipeline_execution=pipeline_execution).delete()
            # 删除流水线执行记录
            pipeline_execution.delete()
            # 删除流水线步骤
            pipeline.steps.all().delete()
            # 删除流水线
            pipeline.delete()
            # 删除项目
            project.delete()
            print("✅ 测试数据清理完成")
        except Exception as e:
            print(f"⚠️  清理测试数据时出现错误: {e}")

def main():
    """主函数"""
    print("🔧 失败中断功能修复验证")
    print("=" * 60)
    print("此脚本验证 UnifiedCICDEngine 修复后的失败中断功能")
    print("预期行为：当步骤3失败时，步骤4和5应该被取消")
    print()
    
    try:
        success = test_failure_interruption_with_unified_engine()
        return success
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
