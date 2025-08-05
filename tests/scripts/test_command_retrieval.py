#!/usr/bin/env python3
"""
测试步骤命令获取可能的问题
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

def test_command_retrieval_issues():
    """测试命令获取问题"""
    
    print("🧪 测试命令获取可能的问题...")
    
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
        
        # 模拟一个mock步骤对象来测试命令获取
        class MockStep:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        # 测试1: 空命令
        print("\n--- 测试1: 空命令 ---")
        mock_step = MockStep(command="", id=1, name="empty_command")
        try:
            cmd = executor._get_step_command(mock_step)
            print(f"获取到的命令: '{cmd}'")
            if cmd == "":
                print("命令为空字符串")
                # 测试空命令的执行
                result = executor._run_command(cmd, {})
                print(f"执行结果: {'✅' if result['success'] else '❌'}")
                print(f"错误: {result.get('error_message', 'N/A')}")
        except Exception as e:
            print(f"获取命令时异常: {e}")
        
        # 测试2: None命令
        print("\n--- 测试2: None命令 ---")
        mock_step = MockStep(command=None, id=2, name="none_command")
        try:
            cmd = executor._get_step_command(mock_step)
            print(f"获取到的命令: '{cmd}'")
            result = executor._run_command(cmd, {})
            print(f"执行结果: {'✅' if result['success'] else '❌'}")
            print(f"错误: {result.get('error_message', 'N/A')}")
        except Exception as e:
            print(f"获取命令时异常: {e}")
        
        # 测试3: 测试 _execute_custom 方法的具体行为
        print("\n--- 测试3: _execute_custom 方法测试 ---")
        mock_step = MockStep(id=3, name="custom_test")
        try:
            result = executor._execute_custom(mock_step, {})
            print(f"执行结果: {'✅' if result['success'] else '❌'}")
            print(f"错误: {result.get('error_message', 'N/A')}")
            if result.get('output'):
                print(f"输出前100字符: {result['output'][:100]}...")
        except Exception as e:
            print(f"_execute_custom 异常: {e}")
        
        # 测试4: 测试实际存在的步骤类型
        print("\n--- 测试4: 测试步骤配置获取 ---")
        mock_step_with_config = MockStep(
            id=4, 
            name="test_with_config",
            config={"script": "echo 'hello from config'"}
        )
        try:
            config = executor._get_step_config(mock_step_with_config)
            print(f"获取到的配置: {config}")
            
            result = executor._execute_custom(mock_step_with_config, {})
            print(f"执行结果: {'✅' if result['success'] else '❌'}")
            if result.get('error_message'):
                print(f"错误: {result['error_message']}")
        except Exception as e:
            print(f"配置测试异常: {e}")

if __name__ == "__main__":
    test_command_retrieval_issues()
