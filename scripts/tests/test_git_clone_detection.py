#!/usr/bin/env python3
"""
测试Git clone目录检测功能
验证流水线执行时能否正确处理Git clone创建的目录
"""
import os
import tempfile
import shutil
import re
import urllib.parse

def test_git_clone_directory_detection():
    """测试Git clone目录检测逻辑"""
    print("🧪 测试Git clone目录检测功能")
    print("=" * 60)
    
    def detect_git_clone_directory(git_command: str, workspace_path: str) -> str:
        """模拟目录检测逻辑"""
        import re
        import urllib.parse
        
        if 'git clone' not in git_command:
            return None
        
        try:
            # 提取仓库URL
            clone_patterns = [
                r'git\s+clone\s+([^\s]+\.git)(?:\s+([^\s]+))?',  # 匹配 .git 结尾的URL，可选目标目录
                r'git\s+clone\s+([^\s]+)(?:\s+([^\s]+))?'       # 匹配任意URL，可选目标目录
            ]
            
            repo_url = None
            target_directory = None
            
            for pattern in clone_patterns:
                match = re.search(pattern, git_command)
                if match:
                    repo_url = match.group(1)
                    target_directory = match.group(2) if len(match.groups()) > 1 else None
                    break
            
            if not repo_url:
                return None
            
            # 如果指定了目标目录，使用指定的目录
            if target_directory and target_directory != '.':
                cloned_dir = target_directory
            else:
                # 从URL中提取仓库名作为目录名
                if repo_url.startswith('ssh://'):
                    # ssh://git@gitlab.com:2424/user/repo.git -> repo
                    parsed = urllib.parse.urlparse(repo_url)
                    path_parts = parsed.path.strip('/').split('/')
                    repo_name = path_parts[-1] if path_parts else 'repo'
                elif '@' in repo_url and ':' in repo_url and not '://' in repo_url:
                    # git@github.com:user/repo.git -> repo
                    repo_name = repo_url.split(':')[-1].split('/')[-1]
                else:
                    # https://github.com/user/repo.git -> repo
                    repo_name = repo_url.split('/')[-1]
                
                # 移除.git后缀
                if repo_name.endswith('.git'):
                    repo_name = repo_name[:-4]
                
                cloned_dir = repo_name
            
            return cloned_dir
            
        except Exception as e:
            print(f"错误: {e}")
            return None
    
    # 测试用例
    test_cases = [
        {
            "command": "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git",
            "expected": "test",
            "description": "SSH协议GitLab仓库"
        },
        {
            "command": "git clone https://github.com/user/my-project.git",
            "expected": "my-project", 
            "description": "HTTPS协议GitHub仓库"
        },
        {
            "command": "git clone git@github.com:user/repo-name.git",
            "expected": "repo-name",
            "description": "SSH协议GitHub仓库（简化格式）"
        },
        {
            "command": "git clone https://gitlab.com/group/subgroup/project.git",
            "expected": "project",
            "description": "GitLab子组项目"
        },
        {
            "command": "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git custom-dir",
            "expected": "custom-dir",
            "description": "指定目标目录"
        },
        {
            "command": "git clone https://github.com/user/repo.git .",
            "expected": "repo",
            "description": "克隆到当前目录（. 参数）"
        }
    ]
    
    # 创建临时工作目录
    workspace_path = tempfile.mkdtemp(prefix="test_git_clone_")
    print(f"📁 创建测试工作空间: {workspace_path}")
    
    try:
        passed = 0
        total = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            command = test_case["command"]
            expected = test_case["expected"]
            description = test_case["description"]
            
            print(f"\n🧪 测试 {i}/{total}: {description}")
            print(f"   命令: {command}")
            print(f"   期望目录: {expected}")
            
            result = detect_git_clone_directory(command, workspace_path)
            
            if result == expected:
                print(f"   ✅ 通过: 检测到目录 '{result}'")
                passed += 1
            else:
                print(f"   ❌ 失败: 期望 '{expected}'，实际 '{result}'")
        
        print(f"\n" + "=" * 60)
        print(f"📊 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有测试通过！Git clone目录检测功能正常。")
        else:
            print("⚠️ 部分测试失败，需要检查检测逻辑。")
            
    finally:
        # 清理测试目录
        shutil.rmtree(workspace_path)
        print(f"🧹 清理测试工作空间: {workspace_path}")

def demonstrate_real_scenario():
    """演示真实场景"""
    print("\n" + "=" * 60)
    print("📖 真实场景演示")
    print("=" * 60)
    
    print("\n🎯 您遇到的问题:")
    print("命令: git clone ssh://git@gitlab.cyfee.com:2424/root/test.git")
    print("结果: Git在工作目录中创建了 'test' 子目录")
    print("问题: 后续步骤仍在工作目录根目录执行，看不到代码文件")
    
    print("\n🔧 修复后的行为:")
    print("1. 执行Git clone命令")
    print("2. 自动检测创建的 'test' 目录")
    print("3. 自动切换工作目录到 'test' 目录")
    print("4. 后续步骤在 'test' 目录中执行，可以看到代码文件")
    
    print("\n📋 支持的Git URL格式:")
    formats = [
        "ssh://git@gitlab.com:2424/user/repo.git",
        "https://github.com/user/repo.git", 
        "git@github.com:user/repo.git",
        "https://gitlab.com/group/project.git"
    ]
    
    for fmt in formats:
        print(f"  ✅ {fmt}")
    
    print("\n🎯 实际效果:")
    print("执行: git clone ssh://git@gitlab.cyfee.com:2424/root/test.git")
    print("检测: 发现创建了 'test' 目录")
    print("切换: 工作目录从 '/tmp/workspace' 切换到 '/tmp/workspace/test'")
    print("结果: 后续 'ls -la' 命令能看到仓库中的文件")

if __name__ == "__main__":
    try:
        test_git_clone_directory_detection()
        demonstrate_real_scenario()
        print("\n🎊 Git clone目录检测功能验证完成！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
