#!/usr/bin/env python3
"""
测试工作目录删除后的恢复功能
"""

import os
import sys
import tempfile
import shutil

# 添加项目路径到sys.path
project_root = '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service'
sys.path.insert(0, project_root)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from cicd_integrations.executors.sync_step_executor import SyncStepExecutor
from cicd_integrations.executors.execution_context import ExecutionContext

def test_workspace_recovery():
    """测试工作目录删除后的恢复"""
    
    print("🧪 测试工作目录删除后的恢复功能...")
    
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
        
        # 测试1: 正常创建文件
        print("\n--- 测试1: 正常创建文件 ---")
        result1 = executor._run_command("echo 'hello' > test1.txt && ls -la", {})
        print(f"结果: {'✅' if result1['success'] else '❌'}")
        print(f"工作目录: {context.get_current_directory()}")
        if result1.get('output'):
            print(f"输出: {result1['output'].strip()}")
        
        # 模拟工作目录被删除
        print("\n--- 模拟工作目录被删除 ---")
        current_workspace = context.get_workspace_path()
        print(f"删除工作目录: {current_workspace}")
        if os.path.exists(current_workspace):
            shutil.rmtree(current_workspace)
            print("✅ 工作目录已删除")
        
        # 测试2: 工作目录删除后尝试执行命令
        print("\n--- 测试2: 工作目录删除后执行命令 ---")
        result2 = executor._run_command("echo 'hello after deletion' > test2.txt && pwd && ls -la", {})
        print(f"结果: {'✅' if result2['success'] else '❌'}")
        print(f"工作目录: {context.get_current_directory()}")
        if result2.get('output'):
            print(f"输出: {result2['output'].strip()}")
        if result2.get('error_message'):
            print(f"错误: {result2['error_message']}")
        
        # 测试3: 继续执行命令，验证恢复是否成功
        print("\n--- 测试3: 验证工作目录恢复 ---")
        result3 = executor._run_command("echo 'recovery test' > test3.txt && ls -la && cat test3.txt", {})
        print(f"结果: {'✅' if result3['success'] else '❌'}")
        print(f"工作目录: {context.get_current_directory()}")
        if result3.get('output'):
            print(f"输出: {result3['output'].strip()}")
        if result3.get('error_message'):
            print(f"错误: {result3['error_message']}")
        
        # 验证工作目录是否已恢复
        final_workspace = context.get_workspace_path()
        print(f"\n📂 最终工作目录状态:")
        print(f"路径: {final_workspace}")
        print(f"存在: {'✅' if os.path.exists(final_workspace) else '❌'}")
        
        if os.path.exists(final_workspace):
            print("目录内容:")
            for item in os.listdir(final_workspace):
                item_path = os.path.join(final_workspace, item)
                if os.path.isfile(item_path):
                    print(f"  📄 {item}")
                else:
                    print(f"  📁 {item}/")

def test_change_directory_robustness():
    """测试change_directory方法的健壮性"""
    
    print("\n🔧 测试 change_directory 方法的健壮性...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 临时工作目录: {temp_dir}")
        
        # 创建执行上下文
        context = ExecutionContext(
            execution_id=2,
            pipeline_name="test_robustness",
            trigger_type="manual",
            workspace_path=temp_dir,
            environment={}
        )
        
        print(f"\n初始工作目录: {context.get_current_directory()}")
        
        # 测试1: 正常切换目录
        print("\n--- 测试1: 正常切换目录 ---")
        try:
            result_dir = context.change_directory()
            print(f"✅ 切换成功: {result_dir}")
        except Exception as e:
            print(f"❌ 切换失败: {e}")
        
        # 删除工作目录
        print("\n--- 删除工作目录 ---")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print("✅ 工作目录已删除")
        
        # 测试2: 工作目录不存在时切换
        print("\n--- 测试2: 工作目录不存在时切换 ---")
        try:
            result_dir = context.change_directory()
            print(f"✅ 切换成功（恢复后）: {result_dir}")
            print(f"目录存在: {'✅' if os.path.exists(result_dir) else '❌'}")
        except Exception as e:
            print(f"❌ 切换失败: {e}")

if __name__ == "__main__":
    test_workspace_recovery()
    test_change_directory_robustness()
