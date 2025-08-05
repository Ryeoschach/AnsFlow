#!/usr/bin/env python3
"""
简化的目录连续性测试
直接测试SyncStepExecutor的目录连续性功能，不依赖数据库
"""

import os
import sys
import tempfile
from unittest.mock import Mock

# 添加项目路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend', 'django_service'))
sys.path.insert(0, project_root)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from cicd_integrations.executors.sync_step_executor import SyncStepExecutor
from cicd_integrations.executors.execution_context import ExecutionContext

def test_directory_continuity_simple():
    """简化的目录连续性测试"""
    
    print("🧪 开始测试目录连续性功能...")
    
    # 创建临时工作目录
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 创建临时工作目录: {temp_dir}")
        
        # 创建执行上下文
        context = ExecutionContext(
            execution_id=1,
            pipeline_name="test_pipeline",
            trigger_type="manual",
            workspace_path=temp_dir,
            environment={}
        )
        
        # 创建执行器
        executor = SyncStepExecutor(context)
        
        print("\n--- 步骤 1: 创建目录结构 ---")
        
        # 测试1: 创建目录结构
        result1 = executor._run_command("mkdir -p code/test && echo '创建目录结构完成'", {})
        print(f"步骤1执行结果: {'✅' if result1['success'] else '❌'}")
        print(f"当前工作目录: {context.get_current_directory()}")
        if result1.get('output'):
            print(f"输出: {result1['output'].strip()}")
        
        print("\n--- 步骤 2: 切换到子目录并创建文件 ---")
        
        # 测试2: 切换目录并创建文件
        result2 = executor._run_command("cd code/test && echo 'hello world' > test.txt && pwd", {})
        print(f"步骤2执行结果: {'✅' if result2['success'] else '❌'}")
        print(f"当前工作目录: {context.get_current_directory()}")
        if result2.get('output'):
            print(f"输出: {result2['output'].strip()}")
        
        print("\n--- 步骤 3: 在当前目录执行命令（应该在code/test目录中） ---")
        
        # 测试3: 验证目录状态
        result3 = executor._run_command("pwd && ls -la && cat test.txt", {})
        print(f"步骤3执行结果: {'✅' if result3['success'] else '❌'}")
        print(f"当前工作目录: {context.get_current_directory()}")
        if result3.get('output'):
            print(f"输出: {result3['output'].strip()}")
        
        print("\n--- 步骤 4: 切换到上级目录 ---")
        
        # 测试4: 切换到上级目录
        result4 = executor._run_command("cd .. && pwd && ls -la", {})
        print(f"步骤4执行结果: {'✅' if result4['success'] else '❌'}")
        print(f"当前工作目录: {context.get_current_directory()}")
        if result4.get('output'):
            print(f"输出: {result4['output'].strip()}")
        
        print("\n🎯 测试结果分析:")
        
        # 分析结果
        all_success = all([
            result1['success'],
            result2['success'], 
            result3['success'],
            result4['success']
        ])
        
        current_dir = context.get_current_directory()
        
        if all_success:
            print("✅ 所有命令执行成功")
            
            # 检查目录状态变化
            if current_dir and 'code' in current_dir and 'test' not in current_dir:
                print("✅ 目录连续性测试成功：正确保持了目录状态变化")
                print(f"   最终目录位于: {current_dir}")
            elif current_dir and 'code/test' in current_dir:
                print("⚠️  目录状态可能不正确：应该在code目录而不是code/test")
                print(f"   最终目录位于: {current_dir}")
            else:
                print("⚠️  目录状态不确定，需要进一步检查")
                print(f"   最终目录位于: {current_dir}")
        else:
            print("❌ 部分命令执行失败")
        
        print(f"\n📝 目录变化轨迹:")
        print(f"   初始目录: {temp_dir}")
        print(f"   最终目录: {current_dir}")
        
        # 验证测试文件是否存在
        test_file_path = os.path.join(temp_dir, 'code', 'test', 'test.txt')
        if os.path.exists(test_file_path):
            print(f"✅ 测试文件已创建: {test_file_path}")
            with open(test_file_path, 'r') as f:
                content = f.read().strip()
                print(f"   文件内容: {content}")
        else:
            print(f"❌ 测试文件未找到: {test_file_path}")

def test_directory_detection():
    """测试目录变化检测功能"""
    
    print("\n🔍 测试目录变化检测...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建执行上下文
        context = ExecutionContext(
            execution_id=2,
            pipeline_name="test_detection",
            trigger_type="manual",
            workspace_path=temp_dir,
            environment={}
        )
        
        # 创建执行器
        executor = SyncStepExecutor(context)
        
        # 创建子目录
        os.makedirs(os.path.join(temp_dir, 'subdir'), exist_ok=True)
        
        print(f"初始目录: {context.get_current_directory()}")
        
        # 测试相对路径检测
        executor._detect_directory_change("cd subdir", context.get_current_directory())
        print(f"cd subdir 后: {context.get_current_directory()}")
        
        # 测试上级目录检测
        executor._detect_directory_change("cd ..", context.get_current_directory())
        print(f"cd .. 后: {context.get_current_directory()}")
        
        # 测试绝对路径检测
        abs_path = os.path.join(temp_dir, 'subdir')
        executor._detect_directory_change(f"cd {abs_path}", context.get_current_directory())
        print(f"cd {abs_path} 后: {context.get_current_directory()}")

if __name__ == "__main__":
    test_directory_continuity_simple()
    test_directory_detection()
