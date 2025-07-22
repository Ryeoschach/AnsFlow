#!/usr/bin/env python3
"""
测试command字段优先级修复
验证用户配置 {"command": "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git", "git_credential_id": 1}
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pipeline_orchestrator.settings')
django.setup()

from pipelines.models import PipelineStep
from cicd_integrations.executors.sync_step_executor import SyncStepExecutor
from cicd_integrations.executors.execution_context import ExecutionContext

def test_command_field_priority():
    """测试command字段优先级"""
    print("🧪 测试command字段优先级修复")
    print("=" * 50)
    
    # 创建模拟的PipelineStep对象
    class MockPipelineStep:
        def __init__(self):
            self.id = 999
            self.name = "测试代码拉取步骤"
            self.step_type = "fetch_code"
            self.command = ""  # PipelineStep的command字段为空
            self.environment_vars = {}
            # 用户的实际配置存储在ansible_parameters中
            self.ansible_parameters = {
                "command": "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git",
                "git_credential_id": 1
            }
    
    # 创建执行上下文
    context = ExecutionContext(
        workspace_id="test_workspace",
        execution_id="test_execution_123"
    )
    
    # 创建执行器
    executor = SyncStepExecutor(context)
    
    # 创建步骤对象
    step = MockPipelineStep()
    
    print(f"📋 步骤信息:")
    print(f"   名称: {step.name}")
    print(f"   类型: {step.step_type}")
    print(f"   ansible_parameters: {step.ansible_parameters}")
    
    # 测试配置获取
    print(f"\n🔍 配置获取测试:")
    config = executor._get_step_config(step)
    print(f"   获取到的配置: {config}")
    
    # 验证关键字段
    command = config.get('command')
    git_credential_id = config.get('git_credential_id')
    
    print(f"\n✅ 关键字段验证:")
    print(f"   command: '{command}'")
    print(f"   git_credential_id: {git_credential_id}")
    
    # 判断修复是否成功
    if command and 'git clone ssh://git@gitlab.cyfee.com:2424/root/test.git' in command:
        print(f"\n🎉 修复成功! command字段已正确获取")
        print(f"   ✓ command字段存在且包含用户指定的Git命令")
        print(f"   ✓ git_credential_id已正确获取: {git_credential_id}")
        
        # 模拟执行逻辑判断
        print(f"\n📊 执行逻辑判断:")
        if command:
            print(f"   ✓ 将使用自定义命令执行代码拉取")
            print(f"   ✓ 不会报'请在步骤配置中指定repository_url'错误")
        else:
            print(f"   ❌ command字段为空，仍会要求repository_url")
            
        return True
    else:
        print(f"\n❌ 修复失败! command字段未正确获取")
        print(f"   expected: git clone ssh://git@gitlab.cyfee.com:2424/root/test.git")
        print(f"   actual: {command}")
        return False

def test_fetch_code_logic():
    """测试代码拉取逻辑"""
    print(f"\n🔬 测试代码拉取执行逻辑")
    print("=" * 50)
    
    # 创建模拟的步骤对象（有command）
    class MockStepWithCommand:
        def __init__(self):
            self.id = 998
            self.name = "带command的步骤"
            self.step_type = "fetch_code"
            self.command = ""
            self.environment_vars = {}
            self.ansible_parameters = {
                "command": "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git",
                "git_credential_id": 1
            }
    
    # 创建模拟的步骤对象（只有repository_url）
    class MockStepWithRepo:
        def __init__(self):
            self.id = 997
            self.name = "带repository_url的步骤"
            self.step_type = "fetch_code"
            self.command = ""
            self.environment_vars = {}
            self.ansible_parameters = {
                "repository_url": "https://github.com/example/repo.git",
                "branch": "main"
            }
    
    # 创建模拟的步骤对象（配置缺失）
    class MockStepMissingConfig:
        def __init__(self):
            self.id = 996
            self.name = "配置缺失的步骤"
            self.step_type = "fetch_code"
            self.command = ""
            self.environment_vars = {}
            self.ansible_parameters = {}
    
    context = ExecutionContext(
        workspace_id="test_workspace",
        execution_id="test_execution_456"
    )
    executor = SyncStepExecutor(context)
    
    # 测试各种配置情况
    test_cases = [
        ("有command字段", MockStepWithCommand()),
        ("有repository_url字段", MockStepWithRepo()),
        ("配置缺失", MockStepMissingConfig())
    ]
    
    for case_name, step in test_cases:
        print(f"\n📋 测试案例: {case_name}")
        config = executor._get_step_config(step)
        
        # 模拟_execute_fetch_code的逻辑判断
        custom_command = config.get('command')
        repository_url = config.get('repository_url')
        
        print(f"   配置: {config}")
        print(f"   command: '{custom_command}'")
        print(f"   repository_url: '{repository_url}'")
        
        if custom_command:
            print(f"   ✅ 结果: 将使用自定义命令执行")
        elif repository_url:
            print(f"   ✅ 结果: 将使用标准git clone执行")
        else:
            print(f"   ❌ 结果: 会报错'代码拉取配置缺失'")

if __name__ == "__main__":
    print("🚀 开始测试command字段优先级修复")
    
    # 测试配置获取
    success = test_command_field_priority()
    
    # 测试执行逻辑
    test_fetch_code_logic()
    
    print(f"\n📋 总结:")
    if success:
        print(f"   ✅ 修复成功，用户配置现在应该能正常工作")
        print(f"   ✅ 参数: {{ \"command\": \"git clone ssh://git@gitlab.cyfee.com:2424/root/test.git\", \"git_credential_id\": 1 }}")
        print(f"   ✅ 不会再报'请在步骤配置中指定repository_url'错误")
    else:
        print(f"   ❌ 修复失败，需要进一步调试")
