#!/usr/bin/env python3
"""
直接测试 _run_command 方法的目录连续性
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

def test_run_command_directory_continuity():
    """直接测试_run_command方法的目录连续性"""
    
    print("🧪 测试 _run_command 方法的目录连续性...")
    
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
        
        print(f"\n初始工作目录: {context.get_current_directory()}")
        
        # 测试1: 创建目录
        print("\n--- 测试1: 创建目录结构 ---")
        result1 = executor._run_command("mkdir -p code/test", {})
        print(f"结果: {'✅' if result1['success'] else '❌'}")
        print(f"工作目录: {context.get_current_directory()}")
        if result1.get('output'):
            print(f"输出: {result1['output'].strip()}")
        if result1.get('error_message'):
            print(f"错误: {result1['error_message']}")
        
        # 测试2: 切换目录
        print("\n--- 测试2: 切换到子目录 ---")
        result2 = executor._run_command("cd code/test && pwd", {})
        print(f"结果: {'✅' if result2['success'] else '❌'}")
        print(f"工作目录: {context.get_current_directory()}")
        if result2.get('output'):
            print(f"输出: {result2['output'].strip()}")
        if result2.get('error_message'):
            print(f"错误: {result2['error_message']}")
        
        # 测试3: 在当前目录执行命令（应该在code/test中）
        print("\n--- 测试3: 在当前目录执行命令 ---")
        result3 = executor._run_command("pwd && echo 'test content' > test.txt", {})
        print(f"结果: {'✅' if result3['success'] else '❌'}")
        print(f"工作目录: {context.get_current_directory()}")
        if result3.get('output'):
            print(f"输出: {result3['output'].strip()}")
        if result3.get('error_message'):
            print(f"错误: {result3['error_message']}")
        
        # 测试4: 验证文件是否创建成功
        print("\n--- 测试4: 验证文件 ---")
        result4 = executor._run_command("ls -la && cat test.txt", {})
        print(f"结果: {'✅' if result4['success'] else '❌'}")
        print(f"工作目录: {context.get_current_directory()}")
        if result4.get('output'):
            print(f"输出: {result4['output'].strip()}")
        if result4.get('error_message'):
            print(f"错误: {result4['error_message']}")
        
        # 测试5: 切换到上级目录
        print("\n--- 测试5: 切换到上级目录 ---")
        result5 = executor._run_command("cd .. && pwd", {})
        print(f"结果: {'✅' if result5['success'] else '❌'}")
        print(f"工作目录: {context.get_current_directory()}")
        if result5.get('output'):
            print(f"输出: {result5['output'].strip()}")
        if result5.get('error_message'):
            print(f"错误: {result5['error_message']}")
        
        # 验证目录结构
        print(f"\n📂 最终目录结构:")
        for root, dirs, files in os.walk(temp_dir):
            level = root.replace(temp_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")

if __name__ == "__main__":
    test_run_command_directory_continuity()
