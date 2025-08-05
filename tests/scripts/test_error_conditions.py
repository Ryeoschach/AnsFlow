#!/usr/bin/env python3
"""
测试可能导致 [Errno 2] No such file or directory 错误的情况
"""

import os
import sys
import tempfile

# 添加项目路径到sys.path
project_root = '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service'
sys.path.insert(0, project_root)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from cicd_integrations.executors.sync_step_executor import SyncStepExecutor
from cicd_integrations.executors.execution_context import ExecutionContext

def test_error_conditions():
    """测试可能导致错误的条件"""
    
    print("🧪 测试可能导致 [Errno 2] 错误的情况...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 临时工作目录: {temp_dir}")
        
        # 创建执行上下文
        context = ExecutionContext(
            execution_id=1,
            pipeline_name="test",
            trigger_type="manual",
            workspace_path=temp_dir,
            environment={}
        )
        
        # 创建执行器
        executor = SyncStepExecutor(context)
        
        print("\n--- 测试1: 执行不存在的命令 ---")
        result1 = executor._run_command("nonexistent_command_12345", {})
        print(f"结果: {'✅' if result1['success'] else '❌'}")
        print(f"错误信息: {result1.get('error_message', 'N/A')}")
        
        print("\n--- 测试2: 执行空命令 ---")
        result2 = executor._run_command("", {})
        print(f"结果: {'✅' if result2['success'] else '❌'}")
        print(f"错误信息: {result2.get('error_message', 'N/A')}")
        
        print("\n--- 测试3: 执行只有空格的命令 ---")
        result3 = executor._run_command("   ", {})
        print(f"结果: {'✅' if result3['success'] else '❌'}")
        print(f"错误信息: {result3.get('error_message', 'N/A')}")
        
        print("\n--- 测试4: 执行None命令 ---")
        try:
            result4 = executor._run_command(None, {})
            print(f"结果: {'✅' if result4['success'] else '❌'}")
            print(f"错误信息: {result4.get('error_message', 'N/A')}")
        except Exception as e:
            print(f"异常: {e}")
        
        print("\n--- 测试5: 正常命令测试 ---")
        result5 = executor._run_command("echo 'hello world'", {})
        print(f"结果: {'✅' if result5['success'] else '❌'}")
        print(f"输出: {result5.get('output', 'N/A').strip()}")

def test_step_execution_commands():
    """测试步骤执行时的实际命令"""
    
    print("\n🔍 测试步骤执行中可能使用的命令...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        context = ExecutionContext(
            execution_id=1,
            pipeline_name="test",
            trigger_type="manual",
            workspace_path=temp_dir,
            environment={}
        )
        
        executor = SyncStepExecutor(context)
        
        # 测试一些常见的Git命令
        git_commands = [
            "git --version",
            "which git",
            "ls -la",
            "pwd",
            "whoami"
        ]
        
        for cmd in git_commands:
            print(f"\n测试命令: {cmd}")
            result = executor._run_command(cmd, {})
            print(f"结果: {'✅' if result['success'] else '❌'}")
            if result.get('output'):
                print(f"输出: {result['output'].strip()}")
            if result.get('error_message'):
                print(f"错误: {result['error_message']}")

if __name__ == "__main__":
    test_error_conditions()
    test_step_execution_commands()
