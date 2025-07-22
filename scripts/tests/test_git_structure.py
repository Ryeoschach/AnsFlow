#!/usr/bin/env python3
"""
验证Git克隆后的目录结构
"""

import os
import tempfile
import subprocess

def test_git_structure():
    """测试Git克隆后的目录结构"""
    
    print("🧪 测试Git克隆目录结构...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 临时目录: {temp_dir}")
        
        # 模拟拉取代码步骤
        code_dir = os.path.join(temp_dir, 'code')
        os.makedirs(code_dir, exist_ok=True)
        
        print(f"📋 创建code目录: {code_dir}")
        
        # 模拟git clone的效果
        # 通常git clone会在当前目录创建一个新的仓库目录
        # 例如: git clone repo.git 会创建 repo/ 目录
        
        # 假设仓库名是test，那么克隆后会有:
        # /tmp/workspace/code/test/
        test_repo_dir = os.path.join(code_dir, 'test')
        os.makedirs(test_repo_dir, exist_ok=True)
        
        # 在仓库中创建一些测试文件
        with open(os.path.join(test_repo_dir, 'README.md'), 'w') as f:
            f.write("# Test Repository")
        
        print(f"📋 模拟仓库目录: {test_repo_dir}")
        
        # 检查目录结构
        print(f"\n📂 目录结构:")
        for root, dirs, files in os.walk(temp_dir):
            level = root.replace(temp_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
        
        print(f"\n🎯 测试场景:")
        print(f"1. 工作空间: {temp_dir}")
        print(f"2. 拉取代码后在: {code_dir}")
        print(f"3. 仓库内容在: {test_repo_dir}")
        
        print(f"\n📋 不同的cd命令测试:")
        
        # 场景1: 从code目录执行cd test
        print(f"从 {code_dir} 执行 'cd test':")
        target1 = os.path.join(code_dir, 'test')
        print(f"  目标: {target1}")
        print(f"  存在: {'✅' if os.path.exists(target1) else '❌'}")
        
        # 场景2: 从code目录执行cd code/test  
        print(f"从 {code_dir} 执行 'cd code/test':")
        target2 = os.path.join(code_dir, 'code', 'test')
        print(f"  目标: {target2}")
        print(f"  存在: {'✅' if os.path.exists(target2) else '❌'}")
        
        # 场景3: 从工作空间根目录执行cd code/test
        print(f"从 {temp_dir} 执行 'cd code/test':")
        target3 = os.path.join(temp_dir, 'code', 'test')  
        print(f"  目标: {target3}")
        print(f"  存在: {'✅' if os.path.exists(target3) else '❌'}")
        
        return os.path.exists(target1), os.path.exists(target3)

if __name__ == "__main__":
    test1, test3 = test_git_structure()
    
    print(f"\n🎯 结论:")
    if test1:
        print("✅ 在code目录中使用 'cd test' 是正确的")
    if test3:
        print("✅ 在根目录中使用 'cd code/test' 是正确的")
    
    print(f"\n💡 建议:")
    print("测试步骤应该使用 'cd test' 而不是 'cd code/test'")
    print("因为拉取代码步骤已经将工作目录设置为 code/ 目录")
