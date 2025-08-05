#!/usr/bin/env python3
"""
GitLab凭据测试脚本
帮助找到本地GitLab实例的正确认证凭据

使用方法:
python scripts/test_gitlab_credentials.py
"""

import requests
import sys
import getpass
from urllib.parse import urljoin
import json

class GitLabCredentialTester:
    def __init__(self, gitlab_url="http://127.0.0.1:8929"):
        self.gitlab_url = gitlab_url.rstrip('/')
        self.session = requests.Session()
        
    def test_web_access(self):
        """测试Web访问"""
        print(f"🔍 测试GitLab Web访问: {self.gitlab_url}")
        try:
            response = self.session.get(self.gitlab_url, timeout=10)
            if response.status_code == 200:
                print("✅ GitLab Web界面可访问")
                return True
            else:
                print(f"❌ GitLab Web访问失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ GitLab Web访问异常: {e}")
            return False
    
    def test_api_access(self):
        """测试API访问"""
        print(f"🔍 测试GitLab API访问...")
        try:
            api_url = f"{self.gitlab_url}/api/v4/version"
            response = self.session.get(api_url, timeout=10)
            if response.status_code == 200:
                version_info = response.json()
                print(f"✅ GitLab API可访问 - 版本: {version_info.get('version', 'Unknown')}")
                return True
            else:
                print(f"❌ GitLab API访问失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ GitLab API访问异常: {e}")
            return False
    
    def test_credentials(self, username, password):
        """测试用户凭据"""
        print(f"🔍 测试凭据: {username}/{'*' * len(password)}")
        
        # 方法1: API认证测试
        try:
            auth_url = f"{self.gitlab_url}/api/v4/user"
            response = self.session.get(auth_url, auth=(username, password), timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ API认证成功!")
                print(f"   用户名: {user_data.get('username', username)}")
                print(f"   姓名: {user_data.get('name', 'N/A')}")
                print(f"   邮箱: {user_data.get('email', 'N/A')}")
                print(f"   管理员: {'是' if user_data.get('is_admin', False) else '否'}")
                return True, user_data
            elif response.status_code == 401:
                print("❌ 认证失败: 用户名或密码错误")
                return False, None
            else:
                print(f"❌ 认证失败: HTTP {response.status_code}")
                print(f"   响应: {response.text[:200]}")
                return False, None
                
        except Exception as e:
            print(f"❌ 认证测试异常: {e}")
            return False, None
    
    def test_git_access(self, username, password):
        """测试Git访问"""
        print(f"🔍 测试Git协议访问...")
        
        import subprocess
        import tempfile
        import os
        from urllib.parse import quote
        
        # 构造认证URL
        auth_url = f"http://{quote(username)}:{quote(password)}@127.0.0.1:8929"
        test_repo_url = f"{auth_url}/test.git"
        
        try:
            # 使用git ls-remote测试
            result = subprocess.run(
                ['git', 'ls-remote', '--exit-code', test_repo_url],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                print("✅ Git认证成功")
                return True
            elif result.returncode == 2:
                print("✅ Git认证成功（测试仓库不存在，这是正常的）")
                return True
            elif result.returncode == 128:
                if 'authentication failed' in result.stderr.lower():
                    print("❌ Git认证失败")
                elif 'repository not found' in result.stderr.lower():
                    print("✅ Git认证成功（测试仓库不存在，这是正常的）")
                    return True
                else:
                    print(f"❌ Git操作失败: {result.stderr}")
            else:
                print(f"❌ Git测试失败: 返回码 {result.returncode}")
                if result.stderr:
                    print(f"   错误: {result.stderr}")
            
            return False
            
        except subprocess.TimeoutExpired:
            print("❌ Git操作超时")
            return False
        except Exception as e:
            print(f"❌ Git测试异常: {e}")
            return False
    
    def interactive_test(self):
        """交互式测试"""
        print("🚀 GitLab凭据交互式测试")
        print("=" * 50)
        
        # 1. 基础连接测试
        if not self.test_web_access():
            print("❌ GitLab Web访问失败，请检查GitLab是否正在运行")
            return False
        
        if not self.test_api_access():
            print("❌ GitLab API访问失败")
            return False
        
        print("\n🔐 请输入GitLab凭据:")
        
        # 2. 交互式凭据输入
        while True:
            username = input("用户名 (输入q退出): ").strip()
            if username.lower() == 'q':
                break
                
            password = getpass.getpass("密码: ")
            
            print(f"\n🧪 测试凭据: {username}")
            print("-" * 30)
            
            # API测试
            api_success, user_data = self.test_credentials(username, password)
            
            # Git测试
            git_success = False
            if api_success:
                git_success = self.test_git_access(username, password)
            
            if api_success and git_success:
                print(f"\n🎉 找到有效凭据!")
                print(f"   用户名: {username}")
                print(f"   密码: {password}")
                print(f"   管理员权限: {'是' if user_data.get('is_admin', False) else '否'}")
                print("\n📋 在AnsFlow中配置:")
                print(f"   平台: GitLab")
                print(f"   认证类型: 用户名密码")
                print(f"   服务器地址: {self.gitlab_url}")
                print(f"   用户名: {username}")
                print(f"   密码: {password}")
                return True
            else:
                print("❌ 凭据测试失败，请尝试其他凭据\n")
        
        return False
    
    def batch_test_common_credentials(self):
        """批量测试常见凭据"""
        print("🔍 批量测试常见凭据...")
        
        common_creds = [
            ("root", "Fengzi1983"),
            ("administrator", "administrator"),
        ]
        
        for username, password in common_creds:
            print(f"\n🧪 测试: {username}/{password}")
            success, user_data = self.test_credentials(username, password)
            if success:
                print(f"🎉 找到有效凭据: {username}/{password}")
                git_success = self.test_git_access(username, password)
                if git_success:
                    print("✅ Git访问也正常!")
                    return username, password
                else:
                    print("⚠️ API可用但Git访问失败")
        
        return None, None

def main():
    gitlab_url = input("GitLab地址 (默认: http://127.0.0.1:8929): ").strip()
    if not gitlab_url:
        gitlab_url = "http://127.0.0.1:8929"
    
    tester = GitLabCredentialTester(gitlab_url)
    
    print("\n选择测试模式:")
    print("1. 交互式测试 (手动输入凭据)")
    print("2. 批量测试常见凭据")
    print("3. 两种都试试")
    
    choice = input("请选择 (1/2/3): ").strip()
    
    if choice == "1":
        tester.interactive_test()
    elif choice == "2":
        username, password = tester.batch_test_common_credentials()
        if username:
            print(f"\n🎉 成功找到凭据: {username}/{password}")
        else:
            print("\n❌ 未找到有效凭据")
    elif choice == "3":
        print("\n=== 批量测试 ===")
        username, password = tester.batch_test_common_credentials()
        if not username:
            print("\n=== 交互式测试 ===")
            tester.interactive_test()
    else:
        print("无效选择")
        return 1
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⏹️ 测试已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 程序异常: {str(e)}")
        sys.exit(1)
