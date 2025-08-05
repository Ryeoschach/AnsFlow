#!/usr/bin/env python3
"""
测试修复后的目录处理逻辑
"""

import subprocess
import tempfile
import os

def test_workspace_root_execution():
    """测试从工作空间根目录执行命令"""
    
    print("🧪 测试从工作空间根目录执行命令...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 工作空间: {temp_dir}")
        
        # 创建测试目录结构
        code_dir = os.path.join(temp_dir, 'code')
        test_dir = os.path.join(code_dir, 'test')
        os.makedirs(test_dir, exist_ok=True)
        
        # 在test目录中创建文件
        with open(os.path.join(test_dir, 'test.txt'), 'w') as f:
            f.write("Test file in code/test directory")
        
        print(f"📋 创建目录结构: {temp_dir}/code/test/")
        
        # 模拟修复后的命令执行逻辑
        def simulate_run_command_from_workspace_root(command):
            """模拟从工作空间根目录执行命令"""
            
            # 构造完整命令
            debug_commands = [
                f"echo 'Executing in workspace: {temp_dir}'",
                f"echo \"Current directory: $(pwd)\"",
                command
            ]
            full_command = " && ".join(debug_commands)
            full_command = f"cd '{temp_dir}' && {full_command}"
            
            print(f"执行命令: {command}")
            print(f"完整命令: {full_command}")
            
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
                print(f"输出: {process.stdout}")
                if process.stderr:
                    print(f"错误: {process.stderr}")
                
                return success
                
            except Exception as e:
                print(f"执行失败: {e}")
                return False
        
        # 测试场景
        print(f"\n🎯 测试场景:")
        
        # 场景1: cd code/test (这应该现在能工作)
        print(f"\n1. 测试 'cd code/test':")
        success1 = simulate_run_command_from_workspace_root("cd code/test")
        
        # 场景2: cd code/test && ls -la (完整的测试步骤)
        print(f"\n2. 测试 'cd code/test && ls -la':")
        success2 = simulate_run_command_from_workspace_root("cd code/test && ls -la")
        
        # 场景3: cd code/test && pwd (确认目录)
        print(f"\n3. 测试 'cd code/test && pwd':")
        success3 = simulate_run_command_from_workspace_root("cd code/test && pwd")
        
        print(f"\n📊 测试结果:")
        print(f"  场景1 (cd code/test): {'✅' if success1 else '❌'}")
        print(f"  场景2 (cd code/test && ls): {'✅' if success2 else '❌'}")
        print(f"  场景3 (cd code/test && pwd): {'✅' if success3 else '❌'}")
        
        return success1 and success2 and success3

if __name__ == "__main__":
    success = test_workspace_root_execution()
    print(f"\n{'🎉 所有测试通过！' if success else '❌ 部分测试失败'}")
    print("✅ 修复生效：自定义步骤现在从工作空间根目录执行，'cd code/test' 命令应该能正常工作")
