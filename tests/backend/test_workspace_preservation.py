#!/usr/bin/env python3
"""
测试工作目录保留功能
验证流水线执行完成后工作目录是否被正确保留
"""
import os
import sys
import django
import tempfile
import shutil
from pathlib import Path

# 设置Django环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansible_backend.settings')
django.setup()

from cicd_integrations.executors.execution_context import ExecutionContext
from cicd_integrations.executors.workspace_manager import workspace_manager
from cicd_integrations.executors.sync_step_executor import SyncStepExecutor

def test_workspace_preservation():
    """测试工作目录保留功能"""
    print("🧪 测试工作目录保留功能")
    print("=" * 50)
    
    # 创建测试用的执行上下文
    execution_id = 9999
    context = ExecutionContext(
        execution_id=execution_id,
        pipeline_name="test_workspace_preservation",
        trigger_type="manual",
        triggered_by="test_user"
    )
    
    print(f"✅ 创建执行上下文 (ID: {execution_id})")
    
    # 获取工作目录路径
    workspace_path = context.get_workspace_path()
    print(f"📁 工作目录路径: {workspace_path}")
    
    # 确认目录存在
    assert os.path.exists(workspace_path), f"工作目录不存在: {workspace_path}"
    print(f"✅ 工作目录已创建并存在")
    
    # 在工作目录中创建一些测试文件
    test_file = os.path.join(workspace_path, "test_file.txt")
    test_dir = os.path.join(workspace_path, "test_dir")
    
    with open(test_file, 'w') as f:
        f.write("这是一个测试文件，用于验证工作目录保留功能\n")
        f.write(f"执行ID: {execution_id}\n")
        f.write("如果你看到这个文件，说明工作目录保留功能正常工作\n")
    
    os.makedirs(test_dir, exist_ok=True)
    sub_file = os.path.join(test_dir, "sub_file.txt")
    with open(sub_file, 'w') as f:
        f.write("子目录中的测试文件\n")
    
    print(f"✅ 在工作目录中创建测试文件: {test_file}")
    print(f"✅ 在工作目录中创建测试子目录: {test_dir}")
    
    # 验证当前保留设置
    print(f"🔧 当前工作目录保留设置: {workspace_manager.preserve_workspaces}")
    
    # 测试默认的清理行为（应该跳过清理）
    print("\n🧪 测试默认清理行为（应该保留工作目录）")
    context.cleanup_workspace()
    
    # 验证文件和目录仍然存在
    assert os.path.exists(workspace_path), "工作目录不应该被删除"
    assert os.path.exists(test_file), "测试文件不应该被删除"
    assert os.path.exists(test_dir), "测试子目录不应该被删除"
    assert os.path.exists(sub_file), "子目录中的文件不应该被删除"
    print("✅ 默认清理模式：工作目录已保留")
    
    # 列出保留的工作目录
    preserved_workspaces = workspace_manager.list_preserved_workspaces()
    print(f"\n📋 当前保留的工作目录:")
    for exec_id, path in preserved_workspaces.items():
        print(f"  - 执行ID {exec_id}: {path}")
    
    # 测试强制清理
    print(f"\n🧪 测试强制清理功能")
    context.force_cleanup_workspace()
    
    # 验证目录已被删除
    assert not os.path.exists(workspace_path), "强制清理后工作目录应该被删除"
    print("✅ 强制清理模式：工作目录已删除")
    
    print("\n" + "=" * 50)
    print("🎉 工作目录保留功能测试完成")
    print("\n📝 功能说明:")
    print("1. 流水线执行完成后，工作目录默认会被保留")
    print("2. 保留的目录包含所有执行过程中的文件和日志")
    print("3. 如需手动清理，可以调用 context.force_cleanup_workspace()")
    print("4. 也可以通过 workspace_manager.set_preserve_workspaces(False) 关闭保留功能")

def test_workspace_manager_settings():
    """测试工作目录管理器设置"""
    print("\n🧪 测试工作目录管理器设置")
    print("=" * 50)
    
    # 测试保留设置切换
    original_setting = workspace_manager.preserve_workspaces
    print(f"📋 原始保留设置: {original_setting}")
    
    # 切换到不保留模式
    workspace_manager.set_preserve_workspaces(False)
    print(f"🔧 设置为不保留模式: {workspace_manager.preserve_workspaces}")
    
    # 创建新的执行上下文进行测试
    execution_id = 8888
    context = ExecutionContext(
        execution_id=execution_id,
        pipeline_name="test_no_preservation",
        trigger_type="manual",
        triggered_by="test_user"
    )
    
    workspace_path = context.get_workspace_path()
    print(f"📁 测试工作目录: {workspace_path}")
    
    # 创建测试文件
    test_file = os.path.join(workspace_path, "temp_file.txt")
    with open(test_file, 'w') as f:
        f.write("临时测试文件")
    
    # 执行清理（应该删除目录）
    context.cleanup_workspace()
    
    # 验证目录被删除
    assert not os.path.exists(workspace_path), "在不保留模式下，工作目录应该被删除"
    print("✅ 不保留模式：工作目录已删除")
    
    # 恢复原始设置
    workspace_manager.set_preserve_workspaces(original_setting)
    print(f"🔄 恢复原始设置: {workspace_manager.preserve_workspaces}")

if __name__ == "__main__":
    try:
        test_workspace_preservation()
        test_workspace_manager_settings()
        print("\n🎊 所有测试通过！工作目录保留功能正常工作。")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
