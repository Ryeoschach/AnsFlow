#!/usr/bin/env python3
"""
简单测试工作空间不被删除的修复
"""

import os
import sys
import tempfile
import shutil

# 添加Django服务到Python路径
sys.path.insert(0, "/Users/creed/Workspace/OpenSource/ansflow/backend/django_service")

def test_workspace_preservation():
    """测试工作空间保留功能"""
    print("=" * 60)
    print("测试工作空间保留功能")
    print("=" * 60)
    
    # 直接导入workspace_manager
    try:
        from cicd_integrations.executors.workspace_manager import PipelineWorkspaceManager
        print("✅ 成功导入PipelineWorkspaceManager")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return
    
    manager = PipelineWorkspaceManager()
    pipeline_name = "test-pipeline"
    execution_id = 101
    
    # 第一次创建
    print("\n1. 第一次创建工作空间...")
    workspace_path1 = manager.create_workspace(pipeline_name, execution_id)
    print(f"工作空间路径: {workspace_path1}")
    
    # 创建测试文件
    test_file = os.path.join(workspace_path1, "git_clone_test.txt")
    test_content = "模拟git clone的代码文件"
    
    print(f"\n2. 创建测试文件（模拟git clone）: {test_file}")
    with open(test_file, 'w') as f:
        f.write(test_content)
    print(f"写入内容: {test_content}")
    
    # 验证文件存在
    if os.path.exists(test_file):
        print("✅ 模拟git clone文件创建成功")
    else:
        print("❌ 模拟git clone文件创建失败")
        return
    
    # 第二次创建（模拟下一个步骤，如docker build）
    print(f"\n3. 第二次创建工作空间（模拟下一个步骤）...")
    workspace_path2 = manager.create_workspace(pipeline_name, execution_id)
    print(f"第二次工作空间路径: {workspace_path2}")
    
    # 检查文件是否还存在
    print(f"\n4. 检查git clone的文件是否还存在...")
    if os.path.exists(test_file):
        print("✅ 文件仍然存在！修复成功！")
        with open(test_file, 'r') as f:
            content = f.read()
        print(f"文件内容: {content}")
        
        # 列出工作空间所有文件
        print(f"\n工作空间文件列表:")
        for item in os.listdir(workspace_path1):
            item_path = os.path.join(workspace_path1, item)
            if os.path.isfile(item_path):
                print(f"  📄 {item}")
            else:
                print(f"  📁 {item}/")
                
        # 模拟下一个步骤也能看到文件
        print(f"\n5. 模拟docker build步骤访问文件...")
        dockerfile_content = f"""FROM python:3.9
COPY {os.path.basename(test_file)} /app/
WORKDIR /app
"""
        dockerfile_path = os.path.join(workspace_path1, "Dockerfile")
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        print(f"创建Dockerfile: {dockerfile_path}")
        print("✅ 后续步骤能正常访问之前步骤的文件")
        
    else:
        print("❌ 文件被删除了，修复失败")
    
    # 清理测试工作空间
    print(f"\n6. 清理测试工作空间...")
    if os.path.exists(workspace_path1):
        shutil.rmtree(workspace_path1)
        print(f"已清理: {workspace_path1}")

if __name__ == "__main__":
    test_workspace_preservation()
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
