#!/usr/bin/env python3
"""
测试工作目录延续性功能
"""
import os
import sys
import django

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

django.setup()

from pipelines.models import Pipeline, PipelineStep
from cicd_integrations.models import PipelineExecution
from cicd_integrations.executors.sync_step_executor import SyncStepExecutor
from cicd_integrations.executors.execution_context import ExecutionContext
from django.contrib.auth.models import User

def test_directory_continuity():
    """测试工作目录延续性"""
    print("🚀 测试工作目录延续性功能")
    print("=" * 50)
    
    try:
        # 获取或创建测试用户
        try:
            user = User.objects.get(username='admin')
        except User.DoesNotExist:
            user = User.objects.create_user('test_user', 'test@example.com', 'password')
        
        # 创建或获取测试流水线
        pipeline, created = Pipeline.objects.get_or_create(
            name='工作目录延续测试',
            defaults={
                'description': '测试工作目录在步骤间的延续性'
            }
        )
        
        if created or not pipeline.steps.exists():
            print("📝 创建测试步骤...")
            
            # 清理旧步骤
            pipeline.steps.all().delete()
            
            # 步骤1: 创建子目录
            step1 = PipelineStep.objects.create(
                pipeline=pipeline,
                name='创建并进入子目录',
                step_type='custom',
                description='创建code/test目录并切换到该目录',
                order=1,
                command='mkdir -p code/test && cd code/test',
                environment_vars={}
            )
            
            # 步骤2: 验证当前目录
            step2 = PipelineStep.objects.create(
                pipeline=pipeline,
                name='验证当前目录',
                step_type='custom',
                description='显示当前工作目录',
                order=2,
                command='pwd',
                environment_vars={}
            )
            
            # 步骤3: 在当前目录执行操作
            step3 = PipelineStep.objects.create(
                pipeline=pipeline,
                name='在当前目录创建文件',
                step_type='custom',
                description='在当前目录创建测试文件',
                order=3,
                command='echo "测试文件内容" > test.txt && ls -la',
                environment_vars={}
            )
            
            # 步骤4: 返回上级目录
            step4 = PipelineStep.objects.create(
                pipeline=pipeline,
                name='返回上级目录',
                step_type='custom',
                description='返回上级目录并查看内容',
                order=4,
                command='cd .. && pwd && ls -la',
                environment_vars={}
            )
            
            # 步骤5: 验证文件是否存在
            step5 = PipelineStep.objects.create(
                pipeline=pipeline,
                name='验证文件存在',
                step_type='custom',
                description='验证之前创建的文件是否存在',
                order=5,
                command='cd test && cat test.txt',
                environment_vars={}
            )
            
            print(f"✅ 创建了 {pipeline.steps.count()} 个测试步骤")
        
        # 创建执行记录
        execution = PipelineExecution.objects.create(
            pipeline=pipeline,
            triggered_by=user,
            status='running',
            trigger_type='manual'
        )
        
        print(f"📝 创建流水线执行记录: ID={execution.id}")
        
        # 创建执行上下文
        context = ExecutionContext(
            execution_id=execution.id,
            pipeline_name=pipeline.name,
            trigger_type='manual',
            triggered_by='test_user',
            parameters={},
            environment={}
        )
        
        print(f"🏠 初始工作目录: {context.get_workspace_path()}")
        print(f"📂 当前工作目录: {context.get_current_directory()}")
        
        # 创建步骤执行器
        executor = SyncStepExecutor(context)
        
        print(f"\n🚀 开始执行步骤序列...")
        
        # 依次执行所有步骤
        steps = pipeline.steps.order_by('order')
        all_success = True
        
        for i, step in enumerate(steps, 1):
            print(f"\n--- 步骤 {i}: {step.name} ---")
            print(f"命令: {step.command}")
            print(f"执行前工作目录: {context.get_current_directory()}")
            
            # 执行步骤
            result = executor.execute_step(step, {})
            
            print(f"执行状态: {result.get('status')}")
            print(f"执行时间: {result.get('execution_time', 0):.2f} 秒")
            print(f"执行后工作目录: {result.get('working_directory', context.get_current_directory())}")
            
            output = result.get('output', '').strip()
            if output:
                print(f"输出:\n{output}")
            
            if result.get('error_message'):
                print(f"❌ 错误: {result.get('error_message')}")
                all_success = False
            else:
                print("✅ 步骤执行成功")
            
            print(f"当前上下文工作目录: {context.get_current_directory()}")
        
        # 验证结果
        print(f"\n{'='*50}")
        if all_success:
            print("✅ 工作目录延续性测试成功！")
            print("\n🎯 关键验证点:")
            print("1. 步骤1创建并进入code/test目录")
            print("2. 步骤2在code/test目录中执行pwd")
            print("3. 步骤3在code/test目录中创建文件")
            print("4. 步骤4返回上级目录到code")
            print("5. 步骤5再次进入test目录并读取文件")
            print("\n✨ 工作目录状态在步骤间正确延续！")
        else:
            print("❌ 工作目录延续性测试失败！")
        
        return all_success
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_directory_change():
    """简单的目录切换测试"""
    print("\n🔧 简单目录切换测试")
    print("-" * 30)
    
    # 创建执行上下文
    context = ExecutionContext(
        execution_id=999,
        pipeline_name='简单测试',
        trigger_type='manual'
    )
    
    executor = SyncStepExecutor(context)
    
    # 测试创建目录并切换
    print("测试1: 创建并切换到子目录")
    result = executor._run_command(
        "mkdir -p test_dir && cd test_dir",
        dict(os.environ)
    )
    print(f"结果: {result.get('success')}")
    print(f"当前目录: {context.get_current_directory()}")
    
    # 测试在新目录中执行命令
    print("\n测试2: 在子目录中执行pwd")
    result = executor._run_command("pwd", dict(os.environ))
    print(f"输出: {result.get('output', '').strip()}")
    print(f"当前目录: {context.get_current_directory()}")
    
    # 测试返回上级目录
    print("\n测试3: 返回上级目录")
    result = executor._run_command("cd ..", dict(os.environ))
    print(f"结果: {result.get('success')}")
    print(f"当前目录: {context.get_current_directory()}")

if __name__ == "__main__":
    print("🧪 工作目录延续性功能测试")
    print("=" * 60)
    
    # 先运行简单测试
    test_simple_directory_change()
    
    print("\n" + "=" * 60)
    
    # 再运行完整测试
    success = test_directory_continuity()
    
    sys.exit(0 if success else 1)
