#!/usr/bin/env python3
"""
测试修复后的命令执行
"""

import subprocess

def test_subprocess_fix():
    """测试subprocess调用修复"""
    
    print("🧪 测试subprocess调用修复...")
    
    # 模拟我们修复后的代码
    current_dir = "/tmp"
    command = "ls -la"
    
    debug_commands = [
        f"echo 'Executing in workspace: /tmp'",
        f"echo \"Current directory: $(pwd)\"",
        command
    ]
    full_command = " && ".join(debug_commands)
    full_command = f"cd '{current_dir}' && {full_command}"
    
    print(f"📋 完整命令: {full_command}")
    
    try:
        process = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"✅ 命令执行成功!")
        print(f"   返回码: {process.returncode}")
        print(f"   输出: {process.stdout[:200]}...")
        
        return process.returncode == 0
        
    except Exception as e:
        print(f"❌ 命令执行失败: {e}")
        return False

if __name__ == "__main__":
    success = test_subprocess_fix()
    print(f"\n{'🎉 测试通过' if success else '❌ 测试失败'}")
