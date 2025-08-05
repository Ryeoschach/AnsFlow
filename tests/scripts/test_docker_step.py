#!/usr/bin/env python3
"""
测试 Docker 步骤执行的脚本
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

def test_docker_step_execution():
    """测试 Docker 步骤执行"""
    print("🐳 测试 Docker 步骤执行")
    print("=" * 50)
    
    try:
        # 获取你的流水线步骤
        pipeline = Pipeline.objects.get(name='本地docker测试')
        step = pipeline.steps.first()
        
        print(f"📋 步骤信息:")
        print(f"  名称: {step.name}")
        print(f"  类型: {step.step_type}")
        print(f"  Docker 镜像: {step.docker_image}")
        print(f"  Docker 标签: {step.docker_tag}")
        
        # 获取测试用户
        try:
            user = User.objects.get(username='admin')
        except User.DoesNotExist:
            user = User.objects.create_user('test_user', 'test@example.com', 'password')
        
        # 创建真实的 PipelineExecution
        pipeline_execution = PipelineExecution.objects.create(
            pipeline=pipeline,
            triggered_by=user,
            status='running',
            trigger_type='manual'
        )
        
        print(f"📝 创建流水线执行记录: ID={pipeline_execution.id}")
        
        # 创建执行上下文
        context = ExecutionContext(
            execution_id=pipeline_execution.id,
            pipeline_name=pipeline.name,
            trigger_type='manual',
            triggered_by='test_user',
            parameters={},
            environment={}
        )
        
        # 创建步骤执行器
        executor = SyncStepExecutor(context)
        
        print(f"\n🚀 开始执行 Docker 步骤...")
        
        # 执行步骤
        result = executor.execute_step(step, {})
        
        print(f"\n📊 执行结果:")
        print(f"  状态: {result.get('status')}")
        print(f"  执行时间: {result.get('execution_time')} 秒")
        print(f"  输出: {result.get('output', '').strip()}")
        if result.get('error_message'):
            print(f"  错误: {result.get('error_message')}")
        
        if result.get('metadata'):
            print(f"  元数据: {result.get('metadata')}")
        
        # 清理测试数据
        pipeline_execution.delete()
        
        print("\n" + "=" * 50)
        if result.get('status') == 'success':
            print("✅ Docker 步骤执行成功！")
            print("\n🎯 现在你可以再次运行流水线，应该会看到正确的 Docker Pull 命令被执行了！")
        else:
            print("❌ Docker 步骤执行失败！")
        
        return result.get('status') == 'success'
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_docker_step_execution()
    sys.exit(0 if success else 1)
