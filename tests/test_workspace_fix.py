#!/usr/bin/env python3
"""
测试工作空间不被删除的修复
"""

import os
import sys
import tempfile
import shutil

# 添加Django服务到Python路径
sys.path.append("/Users/creed/Workspace/OpenSource/ansflow/backend/django_service")

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_service.settings')

import django
django.setup()

from cicd_integrations.executors.workspace_manager import PipelineWorkspaceManager
from cicd_integrations.executors.execution_context import ExecutionContext

def test_workspace_preservation():
    """测试工作空间保留功能"""
    print("=" * 60)
    print("测试工作空间保留功能")
    print("=" * 60)
    
    pipeline_name = "test-pipeline"
    execution_id = 99
    
    # 第一次创建工作空间
    print("\n1. 第一次创建ExecutionContext...")
    context1 = ExecutionContext(
        pipeline_name=pipeline_name,
        execution_id=execution_id,
        environment_variables={}
    )
    
    workspace_path = context1.workspace_path
    print(f"工作空间路径: {workspace_path}")
    
    # 在工作空间中创建测试文件
    test_file = os.path.join(workspace_path, "test_code.txt")
    test_content = "This is test content from first execution"
    
    print(f"\n2. 在工作空间中创建测试文件: {test_file}")
    with open(test_file, 'w') as f:
        f.write(test_content)
    print(f"写入内容: {test_content}")
    
    # 验证文件存在
    if os.path.exists(test_file):
        print("✅ 测试文件创建成功")
        with open(test_file, 'r') as f:
            content = f.read()
        print(f"文件内容: {content}")
    else:
        print("❌ 测试文件创建失败")
        return
    
    # 第二次创建ExecutionContext（模拟下一个阶段）
    print(f"\n3. 第二次创建ExecutionContext（模拟下一个阶段）...")
    context2 = ExecutionContext(
        pipeline_name=pipeline_name,
        execution_id=execution_id,
        environment_variables={}
    )
    
    print(f"第二次工作空间路径: {context2.workspace_path}")
    
    # 检查测试文件是否还存在
    print(f"\n4. 检查测试文件是否还存在...")
    if os.path.exists(test_file):
        print("✅ 测试文件仍然存在！修复成功！")
        with open(test_file, 'r') as f:
            content = f.read()
        print(f"文件内容: {content}")
        
        # 列出工作空间所有文件
        print(f"\n工作空间文件列表:")
        for item in os.listdir(workspace_path):
            item_path = os.path.join(workspace_path, item)
            if os.path.isfile(item_path):
                print(f"  📄 {item}")
            else:
                print(f"  📁 {item}/")
    else:
        print("❌ 测试文件被删除了，修复失败")
    
    # 清理测试工作空间
    print(f"\n5. 清理测试工作空间...")
    if os.path.exists(workspace_path):
        shutil.rmtree(workspace_path)
        print(f"已清理: {workspace_path}")

def test_workspace_manager_directly():
    """直接测试WorkspaceManager"""
    print("\n" + "=" * 60)
    print("直接测试WorkspaceManager")
    print("=" * 60)
    
    manager = PipelineWorkspaceManager()
    pipeline_name = "test-pipeline"
    execution_id = 100
    
    # 第一次创建
    print("\n1. 第一次创建工作空间...")
    workspace_path1 = manager.create_workspace(pipeline_name, execution_id)
    print(f"工作空间路径: {workspace_path1}")
    
    # 创建测试文件
    test_file = os.path.join(workspace_path1, "manager_test.txt")
    test_content = "WorkspaceManager test content"
    
    print(f"\n2. 创建测试文件: {test_file}")
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    # 第二次创建（应该重用）
    print(f"\n3. 第二次创建工作空间...")
    workspace_path2 = manager.create_workspace(pipeline_name, execution_id)
    print(f"第二次工作空间路径: {workspace_path2}")
    
    # 检查文件是否存在
    if os.path.exists(test_file):
        print("✅ WorkspaceManager测试成功！文件被保留")
        with open(test_file, 'r') as f:
            content = f.read()
        print(f"文件内容: {content}")
    else:
        print("❌ WorkspaceManager测试失败！文件被删除")
    
    # 清理
    if os.path.exists(workspace_path1):
        shutil.rmtree(workspace_path1)
        print(f"已清理: {workspace_path1}")

if __name__ == "__main__":
    test_workspace_preservation()
    test_workspace_manager_directly()
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
