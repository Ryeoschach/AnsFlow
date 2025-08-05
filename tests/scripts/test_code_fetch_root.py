#!/usr/bin/env python3
"""
测试修改后的代码拉取逻辑
"""

import os
import tempfile
import subprocess

def test_code_fetch_in_root():
    """测试代码直接拉取到根目录的逻辑"""
    
    print("🧪 测试代码拉取到根目录...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 工作空间: {temp_dir}")
        
        # 模拟修改后的代码拉取逻辑
        def simulate_code_fetch(workspace_dir, command):
            """模拟代码拉取命令"""
            
            print(f"📋 执行命令: {command}")
            
            # 构造完整命令，直接在工作空间根目录执行
            full_command = f"cd '{workspace_dir}' && {command}"
            
            try:
                process = subprocess.run(
                    full_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                success = process.returncode == 0
                print(f"返回码: {process.returncode}")
                if process.stdout:
                    print(f"输出: {process.stdout[:200]}...")
                if process.stderr:
                    print(f"错误: {process.stderr[:200]}...")
                
                return success
                
            except Exception as e:
                print(f"执行失败: {e}")
                return False
        
        # 创建一个简单的git仓库来测试
        # 首先在临时目录创建一个仓库
        repo_dir = os.path.join(temp_dir, "test_repo")
        os.makedirs(repo_dir, exist_ok=True)
        
        # 初始化仓库并添加文件
        setup_commands = [
            f"cd '{repo_dir}' && git init",
            f"cd '{repo_dir}' && echo '# Test Repo' > README.md",
            f"cd '{repo_dir}' && git add README.md",
            f"cd '{repo_dir}' && git config user.email 'test@example.com'",
            f"cd '{repo_dir}' && git config user.name 'Test User'",
            f"cd '{repo_dir}' && git commit -m 'Initial commit'",
            f"cd '{repo_dir}' && mkdir test",
            f"cd '{repo_dir}' && echo 'test content' > test/test.txt",
            f"cd '{repo_dir}' && git add test/test.txt",
            f"cd '{repo_dir}' && git commit -m 'Add test directory'"
        ]
        
        print("🔧 设置测试仓库...")
        for cmd in setup_commands:
            subprocess.run(cmd, shell=True, capture_output=True)
        
        # 创建工作空间目录
        workspace_dir = os.path.join(temp_dir, "workspace")
        os.makedirs(workspace_dir, exist_ok=True)
        
        # 测试场景1: 直接clone到工作空间根目录
        print(f"\n1️⃣ 测试直接clone到根目录:")
        clone_command = f"git clone '{repo_dir}' ."
        success1 = simulate_code_fetch(workspace_dir, clone_command)
        
        # 检查结果
        if success1:
            print("📂 检查目录结构:")
            for root, dirs, files in os.walk(workspace_dir):
                level = root.replace(workspace_dir, '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files[:5]:  # 只显示前5个文件
                    print(f"{subindent}{file}")
            
            # 检查test目录是否存在
            test_dir = os.path.join(workspace_dir, 'test')
            test_exists = os.path.exists(test_dir)
            print(f"\n📋 test目录存在: {'✅' if test_exists else '❌'}")
            
            if test_exists:
                print("🎯 现在其他步骤可以直接使用 'cd test' 命令!")
            
            return test_exists
        else:
            print("❌ 代码拉取失败")
            return False

def test_step_commands():
    """测试步骤命令的简化"""
    
    print(f"\n🧪 测试步骤命令简化...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试目录结构
        test_dir = os.path.join(temp_dir, 'test')
        os.makedirs(test_dir, exist_ok=True)
        
        with open(os.path.join(test_dir, 'test.txt'), 'w') as f:
            f.write("test content")
        
        print(f"📂 工作空间: {temp_dir}")
        
        # 测试简化后的命令
        commands = [
            "cd test",
            "cd test && ls -la",
            "cd test && pwd"
        ]
        
        for i, cmd in enumerate(commands, 1):
            print(f"\n{i}️⃣ 测试命令: {cmd}")
            
            full_command = f"cd '{temp_dir}' && {cmd}"
            
            try:
                process = subprocess.run(
                    full_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                success = process.returncode == 0
                print(f"   返回码: {process.returncode}")
                if process.stdout:
                    print(f"   输出: {process.stdout.strip()}")
                
                if not success and process.stderr:
                    print(f"   错误: {process.stderr.strip()}")
                
            except Exception as e:
                print(f"   执行失败: {e}")

if __name__ == "__main__":
    print("🚀 测试代码拉取逻辑修改...")
    
    # 测试代码拉取
    fetch_success = test_code_fetch_in_root()
    
    # 测试步骤命令
    test_step_commands()
    
    print(f"\n📊 总结:")
    print(f"代码拉取到根目录: {'✅' if fetch_success else '❌'}")
    print(f"💡 修改效果:")
    print(f"  - 代码直接拉取到工作空间根目录")
    print(f"  - 其他步骤可以使用 'cd test' 而不是 'cd code/test'")
    print(f"  - 目录结构更简洁，命令更直观")
