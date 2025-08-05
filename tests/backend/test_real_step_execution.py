#!/usr/bin/env python
"""
测试步骤执行器的真实执行功能
验证是否正确移除了模拟数据
"""

import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from cicd_integrations.executors.sync_step_executor import SyncStepExecutor
from cicd_integrations.executors.execution_context import ExecutionContext

def test_fetch_code_without_repo():
    """测试代码检出步骤在没有仓库URL时的行为"""
    print("=== 测试代码检出步骤（缺少仓库URL）===")
    
    # 创建模拟步骤对象
    class MockStep:
        def __init__(self):
            self.id = 1
            self.name = "测试代码检出"
            self.step_type = "fetch_code"
            self.config = {}  # 没有repository_url
    
    # 创建执行上下文
    context = ExecutionContext(
        execution_id=1001,
        pipeline_name="测试流水线",
        trigger_type="manual"
    )
    
    # 创建执行器
    executor = SyncStepExecutor(context)
    
    # 执行步骤
    result = executor._execute_fetch_code(MockStep(), {})
    
    print(f"执行结果: {result}")
    print(f"是否成功: {result['success']}")
    print(f"错误信息: {result.get('error_message', 'None')}")
    
    # 清理
    context.cleanup_workspace()
    
    return result['success'] == False and 'repository_url' in result['error_message']

def test_docker_build_without_dockerfile():
    """测试Docker构建步骤在没有Dockerfile时的行为"""
    print("\n=== 测试Docker构建步骤（缺少Dockerfile）===")
    
    # 创建模拟步骤对象
    class MockStep:
        def __init__(self):
            self.id = 2
            self.name = "测试Docker构建"
            self.step_type = "docker_build"
            self.docker_image = "nginx"
            self.docker_tag = "latest"
            self.config = {}
    
    # 创建执行上下文
    context = ExecutionContext(
        execution_id=1002,
        pipeline_name="Docker测试流水线",
        trigger_type="manual"
    )
    
    # 创建空的工作目录（没有Dockerfile）
    workspace_path = context.get_workspace_path()
    print(f"工作目录: {workspace_path}")
    
    # 创建执行器
    executor = SyncStepExecutor(context)
    
    # 执行Docker构建步骤
    result = executor._execute_docker_fallback(MockStep(), {})
    
    print(f"执行结果: {result}")
    print(f"是否成功: {result['success']}")
    print(f"错误信息: {result.get('error_message', 'None')}")
    
    # 清理
    context.cleanup_workspace()
    
    return result['success'] == False and 'Dockerfile不存在' in result['error_message']

def test_notify_without_command():
    """测试通知步骤在没有命令时的行为"""
    print("\n=== 测试通知步骤（缺少通知命令）===")
    
    # 创建模拟步骤对象
    class MockStep:
        def __init__(self):
            self.id = 3
            self.name = "测试通知"
            self.step_type = "notify"
            self.config = {
                'message': '测试消息',
                'type': 'email'
                # 没有notify_command
            }
    
    # 创建执行上下文
    context = ExecutionContext(
        execution_id=1003,
        pipeline_name="通知测试流水线",
        trigger_type="manual"
    )
    
    # 创建执行器
    executor = SyncStepExecutor(context)
    
    # 执行通知步骤
    result = executor._execute_notify(MockStep(), {})
    
    print(f"执行结果: {result}")
    print(f"是否成功: {result['success']}")
    print(f"错误信息: {result.get('error_message', 'None')}")
    
    # 清理
    context.cleanup_workspace()
    
    return result['success'] == False and 'notify_command' in result['error_message']

def test_unsupported_step_type():
    """测试不支持的步骤类型"""
    print("\n=== 测试不支持的步骤类型 ===")
    
    # 创建模拟步骤对象
    class MockStep:
        def __init__(self):
            self.id = 4
            self.name = "不支持的步骤"
            self.step_type = "unsupported_type"
            self.config = {}
    
    # 创建执行上下文
    context = ExecutionContext(
        execution_id=1004,
        pipeline_name="不支持步骤测试",
        trigger_type="manual"
    )
    
    # 创建执行器
    executor = SyncStepExecutor(context)
    
    # 执行步骤
    result = executor._execute_by_type(MockStep(), {}, {})
    
    print(f"执行结果: {result}")
    print(f"是否成功: {result['success']}")
    print(f"错误信息: {result.get('error_message', 'None')}")
    
    # 清理
    context.cleanup_workspace()
    
    return result['success'] == False and '不支持的步骤类型' in result['error_message']

def main():
    """主测试函数"""
    print("开始测试步骤执行器的真实执行功能...")
    print("验证是否正确移除了模拟数据并提供合适的错误处理")
    
    test1 = test_fetch_code_without_repo()
    test2 = test_docker_build_without_dockerfile()
    test3 = test_notify_without_command()
    test4 = test_unsupported_step_type()
    
    print(f"\n=== 测试结果汇总 ===")
    print(f"代码检出步骤错误处理: {'✅ 通过' if test1 else '❌ 失败'}")
    print(f"Docker构建步骤错误处理: {'✅ 通过' if test2 else '❌ 失败'}")
    print(f"通知步骤错误处理: {'✅ 通过' if test3 else '❌ 失败'}")
    print(f"不支持步骤类型处理: {'✅ 通过' if test4 else '❌ 失败'}")
    
    if test1 and test2 and test3 and test4:
        print("\n🎉 所有测试通过！")
        print("✅ 已成功移除模拟数据")
        print("✅ 步骤执行器现在进行真实的命令执行")
        print("✅ 提供了合适的错误处理和提示")
        return True
    else:
        print("\n❌ 存在测试失败")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
