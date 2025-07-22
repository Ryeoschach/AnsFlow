#!/usr/bin/env python3
"""
调试Git clone目录检测功能
验证为什么实际执行时检测功能没有生效
"""
import os
import tempfile
import shutil
import sys

# 添加Django项目路径
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')

def test_git_clone_detection_debug():
    """调试Git clone检测功能"""
    print("🔍 调试Git clone目录检测功能")
    print("=" * 60)
    
    # 模拟实际的命令和环境
    git_command = "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git"
    workspace_path = "/tmp/本地docker测试_41"
    
    print(f"Git命令: {git_command}")
    print(f"工作空间: {workspace_path}")
    
    # 创建模拟环境
    test_workspace = tempfile.mkdtemp(prefix="debug_test_")
    print(f"测试工作空间: {test_workspace}")
    
    try:
        # 模拟Git clone创建的目录
        test_repo_dir = os.path.join(test_workspace, "test")
        os.makedirs(test_repo_dir)
        
        # 创建.git目录
        git_dir = os.path.join(test_repo_dir, ".git")
        os.makedirs(git_dir)
        
        # 创建一些文件
        with open(os.path.join(test_repo_dir, "README.md"), "w") as f:
            f.write("# Test Repo")
        
        print(f"✅ 模拟Git clone创建目录: {test_repo_dir}")
        
        # 测试检测逻辑
        detected_dir = detect_git_clone_directory_name(git_command)
        print(f"🔍 检测到的目录名: {detected_dir}")
        
        # 检查目录是否存在
        if detected_dir:
            expected_path = os.path.join(test_workspace, detected_dir)
            exists = os.path.exists(expected_path)
            print(f"📁 预期路径: {expected_path}")
            print(f"📁 目录存在: {exists}")
            
            if exists:
                is_git_repo = os.path.exists(os.path.join(expected_path, ".git"))
                print(f"🔧 是Git仓库: {is_git_repo}")
                
                if is_git_repo:
                    print("✅ 检测逻辑完全正确！")
                    print(f"应该切换工作目录到: {expected_path}")
                else:
                    print("⚠️ 目录存在但不是Git仓库")
            else:
                print("❌ 预期的目录不存在")
        else:
            print("❌ 无法检测目录名")
        
        # 检查实际文件系统状态
        print(f"\n📋 实际文件系统状态:")
        items = os.listdir(test_workspace)
        for item in items:
            item_path = os.path.join(test_workspace, item)
            if os.path.isdir(item_path):
                print(f"📁 {item}/")
                # 列出子目录内容
                try:
                    sub_items = os.listdir(item_path)[:5]  # 只显示前5个
                    for sub_item in sub_items:
                        print(f"   - {sub_item}")
                    if len(os.listdir(item_path)) > 5:
                        print(f"   ... 还有 {len(os.listdir(item_path)) - 5} 个文件")
                except:
                    pass
            else:
                print(f"📄 {item}")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        shutil.rmtree(test_workspace)
        print(f"🧹 清理测试环境: {test_workspace}")

def detect_git_clone_directory_name(git_command: str) -> str:
    """提取Git clone命令中的目录名"""
    import re
    import urllib.parse
    
    if 'git clone' not in git_command:
        return None
    
    try:
        # 提取仓库URL
        clone_patterns = [
            r'git\s+clone\s+([^\s]+\.git)(?:\s+([^\s]+))?',
            r'git\s+clone\s+([^\s]+)(?:\s+([^\s]+))?'
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
            return target_directory
        
        # 从URL中提取仓库名作为目录名
        if repo_url.startswith('ssh://'):
            parsed = urllib.parse.urlparse(repo_url)
            path_parts = parsed.path.strip('/').split('/')
            repo_name = path_parts[-1] if path_parts else 'repo'
        elif '@' in repo_url and ':' in repo_url and not '://' in repo_url:
            repo_name = repo_url.split(':')[-1].split('/')[-1]
        else:
            repo_name = repo_url.split('/')[-1]
        
        # 移除.git后缀
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        return repo_name
        
    except Exception as e:
        print(f"检测错误: {e}")
        return None

def debug_real_workspace():
    """调试真实的工作空间"""
    print(f"\n🔍 调试真实工作空间")
    print("=" * 60)
    
    real_workspace = "/tmp/本地docker测试_41"
    
    print(f"检查工作空间: {real_workspace}")
    
    try:
        if os.path.exists(real_workspace):
            print(f"✅ 工作空间存在")
            items = os.listdir(real_workspace)
            print(f"📋 内容 ({len(items)} 项):")
            for item in items:
                item_path = os.path.join(real_workspace, item)
                if os.path.isdir(item_path):
                    print(f"📁 {item}/")
                    # 检查是否是Git仓库
                    git_dir = os.path.join(item_path, ".git")
                    if os.path.exists(git_dir):
                        print(f"   ✅ 是Git仓库")
                    else:
                        print(f"   ⚠️ 不是Git仓库")
                    
                    # 列出内容
                    try:
                        sub_items = os.listdir(item_path)[:3]
                        for sub_item in sub_items:
                            print(f"   - {sub_item}")
                    except:
                        pass
                else:
                    print(f"📄 {item}")
            
            if not items:
                print("📂 工作空间为空")
        else:
            print(f"❌ 工作空间不存在")
    
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    try:
        test_git_clone_detection_debug()
        debug_real_workspace()
        print("\n🎯 结论:")
        print("如果检测逻辑正确但实际执行时没有效果，可能的原因:")
        print("1. 日志级别问题，logger.info没有显示")
        print("2. 检测时机问题，Git clone还没有完全创建目录")
        print("3. 工作空间路径或权限问题")
        print("4. 代码没有正确加载最新修改")
    except Exception as e:
        print(f"\n❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
