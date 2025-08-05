#!/usr/bin/env python3
"""
测试增强的命令执行日志记录功能
验证详细的执行信息是否正确记录和显示
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# 添加项目路径到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(project_root, 'backend', 'django_service')
sys.path.insert(0, backend_path)

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from cicd_integrations.executors.execution_context import ExecutionContext
from cicd_integrations.executors.sync_step_executor import SyncStepExecutor

def print_section(title):
    """打印带分隔符的标题"""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def print_execution_result(result, command_description):
    """打印详细的执行结果"""
    print(f"\n🔍 {command_description}")
    print(f"   成功状态: {'✅' if result['success'] else '❌'}")
    print(f"   返回码: {result['return_code']}")
    print(f"   工作目录: {result['working_directory']}")
    
    if 'execution_details' in result:
        details = result['execution_details']
        print("\n📊 执行详情:")
        print(f"   原始命令: {details['original_command']}")
        print(f"   完整命令: {details['full_command']}")
        print(f"   执行目录: {details['execution_directory']}")
        print(f"   最终目录: {details['final_directory']}")
        
        if details['stdout']:
            print(f"\n📤 标准输出:")
            for line in details['stdout'].strip().split('\n'):
                print(f"      {line}")
        
        if details['stderr']:
            print(f"\n⚠️  错误输出:")
            for line in details['stderr'].strip().split('\n'):
                print(f"      {line}")
    
    if 'output' in result and result['output']:
        print(f"\n💬 输出预览: {result['output'][:100]}{'...' if len(result['output']) > 100 else ''}")

def test_enhanced_logging():
    """测试增强的日志记录功能"""
    print_section("测试增强的命令执行日志记录")
    
    # 创建临时测试目录
    temp_dir = tempfile.mkdtemp(prefix="ansflow_logging_test_")
    test_dir = os.path.join(temp_dir, "test_workspace")
    os.makedirs(test_dir)
    
    try:
        # 创建执行上下文和执行器
        context = ExecutionContext(
            execution_id=1,
            pipeline_name="test_logging_pipeline", 
            trigger_type="manual",
            workspace_path=test_dir
        )
        executor = SyncStepExecutor(context)
        
        print(f"📁 测试工作区: {test_dir}")
        
        # 测试 1: 基本命令执行
        print_section("测试 1: 基本命令执行")
        result = executor._run_command("echo 'Hello, AnsFlow!'")
        print_execution_result(result, "执行 echo 命令")
        
        # 测试 2: 目录操作命令
        print_section("测试 2: 目录操作命令")
        result = executor._run_command("pwd")
        print_execution_result(result, "显示当前目录")
        
        # 创建子目录进行测试
        subdir = os.path.join(test_dir, "subdir")
        os.makedirs(subdir)
        
        # 测试 3: 目录切换命令
        print_section("测试 3: 目录切换命令")
        result = executor._run_command(f"cd {subdir}")
        print_execution_result(result, f"切换到子目录: {subdir}")
        
        # 测试 4: 验证目录变化
        print_section("测试 4: 验证目录变化后的执行")
        result = executor._run_command("pwd")
        print_execution_result(result, "切换目录后显示当前目录")
        
        # 测试 5: 文件操作命令
        print_section("测试 5: 文件操作命令")
        result = executor._run_command("echo 'Test content' > test.txt")
        print_execution_result(result, "创建测试文件")
        
        result = executor._run_command("cat test.txt")
        print_execution_result(result, "读取测试文件内容")
        
        # 测试 6: 列出目录内容
        print_section("测试 6: 列出目录内容")
        result = executor._run_command("ls -la")
        print_execution_result(result, "列出目录内容")
        
        # 测试 7: 错误命令
        print_section("测试 7: 错误命令测试")
        result = executor._run_command("nonexistent_command")
        print_execution_result(result, "执行不存在的命令")
        
        # 测试 8: 复杂命令组合
        print_section("测试 8: 复杂命令组合")
        result = executor._run_command("echo 'Line 1' && echo 'Line 2' && pwd")
        print_execution_result(result, "执行命令组合")
        
        print_section("日志记录测试完成")
        print("✅ 所有测试执行完毕")
        print(f"🗂️  测试目录: {temp_dir}")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理临时目录
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"🧹 已清理临时目录: {temp_dir}")

def test_custom_script_logging():
    """测试自定义脚本的日志记录"""
    print_section("测试自定义脚本日志记录")
    
    # 创建临时测试目录
    temp_dir = tempfile.mkdtemp(prefix="ansflow_script_test_")
    test_dir = os.path.join(temp_dir, "script_workspace")
    os.makedirs(test_dir)
    
    try:
        # 创建执行上下文和执行器
        context = ExecutionContext(
            execution_id=2,
            pipeline_name="test_script_pipeline", 
            trigger_type="manual",
            workspace_path=test_dir
        )
        executor = SyncStepExecutor(context)
        
        print(f"📁 脚本测试工作区: {test_dir}")
        
        # 创建测试脚本
        script_content = """#!/bin/bash
echo "脚本开始执行"
echo "当前目录: $(pwd)"
echo "创建测试文件..."
echo "测试内容" > script_test.txt
echo "文件创建完成"
ls -la script_test.txt
echo "脚本执行完成"
"""
        
        script_path = os.path.join(test_dir, "test_script.sh")
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        
        # 测试脚本执行
        print_section("执行测试脚本")
        
        # 模拟 _execute_custom_script 方法的调用
        step_data = {
            'script_content': script_content,
            'script_type': 'bash'
        }
        
        result = executor._execute_custom_script(step_data)
        
        print(f"\n🚀 脚本执行结果:")
        print(f"   成功状态: {'✅' if result.get('success', False) else '❌'}")
        
        if 'output' in result:
            print(f"\n📤 脚本输出:")
            for line in result['output'].split('\n'):
                if line.strip():
                    print(f"      {line}")
        
        if 'error_output' in result:
            print(f"\n⚠️  错误输出:")
            for line in result['error_output'].split('\n'):
                if line.strip():
                    print(f"      {line}")
        
        print_section("脚本日志记录测试完成")
        
    except Exception as e:
        print(f"❌ 脚本测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理临时目录
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"🧹 已清理临时目录: {temp_dir}")

if __name__ == "__main__":
    print(f"🚀 开始测试增强的日志记录功能")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_enhanced_logging()
    test_custom_script_logging()
    
    print(f"\n🎉 所有日志记录测试完成!")
