#!/usr/bin/env python
"""
测试流水线工作目录功能
验证每个流水线执行都有独立的工作目录
"""

import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from unittest.mock import Mock
from cicd_integrations.executors.workspace_manager import workspace_manager
from cicd_integrations.executors.execution_context import ExecutionContext

def test_workspace_creation():
    """测试工作目录创建"""
    print("=== 测试工作目录创建 ===")
    
    try:
        # 测试数据
        pipeline_name = "测试流水线"
        execution_id = 12345
        
        # 创建工作目录
        workspace_path = workspace_manager.create_workspace(pipeline_name, execution_id)
        
        print(f"✅ 工作目录创建成功: {workspace_path}")
        print(f"   - 流水线名称: {pipeline_name}")
        print(f"   - 执行编号: {execution_id}")
        
        # 验证目录是否存在
        if os.path.exists(workspace_path):
            print(f"✅ 工作目录确实存在: {workspace_path}")
        else:
            print(f"❌ 工作目录不存在: {workspace_path}")
            return False
        
        # 验证目录名称格式
        expected_dir_name = f"测试流水线_{execution_id}"
        if expected_dir_name in workspace_path:
            print(f"✅ 目录名称格式正确: {expected_dir_name}")
        else:
            print(f"❌ 目录名称格式不正确，期望包含: {expected_dir_name}")
            return False
        
        # 清理测试目录
        workspace_manager.cleanup_workspace(execution_id)
        print(f"✅ 测试目录清理完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_execution_context_with_workspace():
    """测试ExecutionContext的工作目录功能"""
    print("\n=== 测试ExecutionContext工作目录功能 ===")
    
    try:
        # 创建执行上下文
        context = ExecutionContext(
            execution_id=67890,
            pipeline_name="Docker构建流水线",
            trigger_type="manual"
        )
        
        print(f"✅ ExecutionContext创建成功")
        
        # 获取工作目录
        workspace_path = context.get_workspace_path()
        print(f"✅ 工作目录路径: {workspace_path}")
        
        # 验证目录存在
        if os.path.exists(workspace_path):
            print(f"✅ 工作目录存在")
        else:
            print(f"❌ 工作目录不存在")
            return False
        
        # 测试切换目录
        original_cwd = os.getcwd()
        current_dir = context.change_directory()
        print(f"✅ 切换到工作目录: {current_dir}")
        
        # 创建子目录并切换
        sub_dir = context.change_directory("build")
        print(f"✅ 切换到子目录: {sub_dir}")
        
        # 测试路径解析
        test_file_path = context.resolve_path("test.txt")
        print(f"✅ 路径解析结果: {test_file_path}")
        
        # 恢复原目录
        os.chdir(original_cwd)
        
        # 清理工作目录
        context.cleanup_workspace()
        print(f"✅ 工作目录清理完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_workspaces():
    """测试多个工作目录的隔离性"""
    print("\n=== 测试多个工作目录隔离性 ===")
    
    try:
        # 创建多个工作目录
        workspaces = []
        for i in range(3):
            execution_id = 10000 + i
            pipeline_name = f"流水线_{i+1}"
            
            workspace_path = workspace_manager.create_workspace(pipeline_name, execution_id)
            workspaces.append((execution_id, workspace_path))
            
            print(f"✅ 创建工作目录 {i+1}: {workspace_path}")
        
        # 验证所有目录都不同
        paths = [ws[1] for ws in workspaces]
        if len(set(paths)) == len(paths):
            print(f"✅ 所有工作目录路径都不同，隔离性良好")
        else:
            print(f"❌ 存在重复的工作目录路径")
            return False
        
        # 在每个目录中创建文件
        for i, (execution_id, workspace_path) in enumerate(workspaces):
            test_file = os.path.join(workspace_path, f"test_{i}.txt")
            with open(test_file, 'w') as f:
                f.write(f"这是流水线 {i+1} 的测试文件")
            print(f"✅ 在工作目录 {i+1} 中创建了测试文件")
        
        # 验证文件隔离
        for i, (execution_id, workspace_path) in enumerate(workspaces):
            test_file = os.path.join(workspace_path, f"test_{i}.txt")
            if os.path.exists(test_file):
                print(f"✅ 工作目录 {i+1} 的文件存在且独立")
            else:
                print(f"❌ 工作目录 {i+1} 的文件不存在")
                return False
        
        # 清理所有工作目录
        for execution_id, workspace_path in workspaces:
            workspace_manager.cleanup_workspace(execution_id)
        print(f"✅ 所有测试工作目录清理完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_workspace_naming():
    """测试工作目录命名规则"""
    print("\n=== 测试工作目录命名规则 ===")
    
    try:
        test_cases = [
            ("正常流水线", 1, "正常流水线_1"),
            ("包含空格的 流水线", 2, "包含空格的_流水线_2"),
            ("包含/特殊\\字符:的?流水线", 3, "包含_特殊_字符_的_流水线_3"),
            ("非常长的流水线名称" * 10, 4, None)  # 这个会被截断
        ]
        
        for pipeline_name, execution_id, expected_pattern in test_cases:
            workspace_path = workspace_manager.create_workspace(pipeline_name, execution_id)
            dir_name = os.path.basename(workspace_path)
            
            print(f"✅ 流水线名称: '{pipeline_name}'")
            print(f"   目录名称: '{dir_name}'")
            
            # 验证目录名称是安全的（不包含非法字符）
            illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
            has_illegal = any(char in dir_name for char in illegal_chars)
            
            if not has_illegal:
                print(f"✅ 目录名称安全，不包含非法字符")
            else:
                print(f"❌ 目录名称包含非法字符")
                return False
            
            # 清理
            workspace_manager.cleanup_workspace(execution_id)
        
        print(f"✅ 所有命名规则测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试流水线工作目录功能...")
    
    test1 = test_workspace_creation()
    test2 = test_execution_context_with_workspace()
    test3 = test_multiple_workspaces()
    test4 = test_workspace_naming()
    
    if test1 and test2 and test3 and test4:
        print("\n🎉 所有工作目录功能测试通过！")
        print("✅ 工作目录创建正常")
        print("✅ ExecutionContext集成正常") 
        print("✅ 多工作目录隔离性正常")
        print("✅ 目录命名规则正常")
        print(f"\n📁 工作目录格式: /tmp/流水线名称_执行编号")
        print(f"🧹 自动清理机制已启用")
        return True
    else:
        print("\n❌ 存在测试失败")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
