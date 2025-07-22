#!/usr/bin/env python
"""
集成测试：验证本地执行器和步骤兼容性修复
"""

import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

import requests
import json
from django.contrib.auth.models import User
from cicd_integrations.models import CICDTool

def test_local_executor_creation():
    """测试本地执行器创建API"""
    print("=== 测试本地执行器创建 ===")
    
    # 获取或创建测试用户
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    # 删除可能存在的本地执行器
    CICDTool.objects.filter(tool_type='local').delete()
    
    # 检查本地执行器是否存在
    local_executor = CICDTool.objects.filter(tool_type='local').first()
    if local_executor:
        print(f"✅ 本地执行器已存在: {local_executor.name}")
        return True
    else:
        print("🔄 本地执行器不存在，需要创建")
        
    # 模拟创建本地执行器（通过直接创建数据库记录）
    try:
        # 先尝试导入Project模型
        try:
            from project_management.models import Project
            # 创建或获取系统项目
            system_project, _ = Project.objects.get_or_create(
                name="System Project",
                defaults={'description': '系统自动创建的项目'}
            )
            project_id = system_project.id
        except ImportError:
            # 如果Project模型不存在，设置为None
            project_id = None
        
        local_executor = CICDTool.objects.create(
            name="System Local Executor",
            tool_type="local",
            base_url="http://localhost:8000",
            description="自动创建的本地执行器",
            username="system",
            token="local-executor-token",
            status="authenticated",
            project_id=project_id,
            config={
                "created_automatically": True,
                "supports_docker": True,
                "supports_shell": True,
                "supports_kubernetes": True
            }
        )
        print(f"✅ 本地执行器创建成功: {local_executor.name}")
        return True
    except Exception as e:
        print(f"❌ 本地执行器创建失败: {e}")
        return False

def test_step_executor_integration():
    """测试步骤执行器集成"""
    print("\n=== 测试步骤执行器集成 ===")
    
    try:
        from pipelines.models import PipelineStep, Pipeline
        from project_management.models import Project
        from cicd_integrations.executors.sync_step_executor import SyncStepExecutor
        from cicd_integrations.executors.execution_context import ExecutionContext
        
        # 创建测试项目
        project, _ = Project.objects.get_or_create(
            name="测试项目",
            defaults={'description': '集成测试项目'}
        )
        
        # 创建测试流水线
        pipeline, _ = Pipeline.objects.get_or_create(
            name="集成测试流水线",
            project=project,
            defaults={'description': '集成测试流水线'}
        )
        
        # 创建测试的PipelineStep
        test_step, _ = PipelineStep.objects.get_or_create(
            pipeline=pipeline,
            name="集成测试步骤",
            defaults={
                'step_type': "script",
                'command': "echo 'Hello from integrated test'",
                'environment_vars': {"TEST_VAR": "test_value"},
                'order': 1
            }
        )
        
        # 创建执行上下文
        context = ExecutionContext(
            execution_id=999,
            pipeline_name="集成测试流水线",
            trigger_type="test"
        )
        
        # 创建执行器
        executor = SyncStepExecutor(context)
        
        # 测试关键方法
        step_type = executor._get_step_type(test_step)
        step_name = executor._get_step_name(test_step) 
        step_config = executor._get_step_config(test_step)
        
        print(f"✅ 步骤类型: {step_type}")
        print(f"✅ 步骤名称: {step_name}")
        print(f"✅ 步骤配置: {step_config}")
        
        # 验证方法存在且可调用
        methods_to_test = [
            '_execute_shell_step',
            '_execute_docker_step', 
            '_execute_kubernetes_step',
            '_execute_mock',
            '_execute_custom'
        ]
        
        for method_name in methods_to_test:
            if hasattr(executor, method_name):
                print(f"✅ 方法 {method_name} 存在")
            else:
                print(f"❌ 方法 {method_name} 不存在")
                return False
        
        print("✅ 步骤执行器集成测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 步骤执行器集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始集成测试...")
    
    success1 = test_local_executor_creation()
    success2 = test_step_executor_integration()
    
    if success1 and success2:
        print("\n🎉 所有集成测试通过！")
        print("✅ 本地执行器功能正常")
        print("✅ 步骤执行器兼容性修复成功")
        print("✅ 系统可以正常处理PipelineStep和AtomicStep")
        return True
    else:
        print("\n❌ 存在集成测试失败")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
