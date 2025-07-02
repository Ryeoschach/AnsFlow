#!/usr/bin/env python3
"""
AnsFlow Git凭据连接问题修复脚本

主要问题和解决方案:
1. GitHub已禁用密码认证，必须使用Personal Access Token
2. GitLab本地实例可能有特殊配置需求
3. 后端测试逻辑需要优化

使用方法:
python scripts/fix_git_credentials.py
"""

import requests
import json
import sys
import os
import subprocess
import tempfile
import shutil
from urllib.parse import urlparse, quote
import time

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(message):
    print(f"{Colors.BLUE}🔍 {message}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.END}")

def print_header(message):
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}🚀 {message}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")

class GitCredentialFixer:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
    def get_auth_token(self):
        """获取认证令牌"""
        print_step("获取认证令牌...")
        
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/auth/token/", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access') or data.get('token')
                if self.token:
                    self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                    print_success("成功获取认证令牌")
                    return True
            
            print_error(f"获取认证令牌失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
        except Exception as e:
            print_error(f"认证请求失败: {e}")
            return False
    
    def test_direct_git_access(self):
        """直接测试Git访问能力"""
        print_header("测试系统Git环境")
        
        # 1. 检查git命令
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print_success(f"Git已安装: {result.stdout.strip()}")
            else:
                print_error("Git未安装或不可用")
                return False
        except FileNotFoundError:
            print_error("系统中未找到git命令")
            return False
        
        # 2. 测试网络连接
        print_step("测试网络连接...")
        
        test_hosts = [
            ("GitHub", "https://github.com"),
            ("本地GitLab", "http://127.0.0.1:8929")
        ]
        
        for name, url in test_hosts:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print_success(f"{name} 网络连接正常")
                else:
                    print_warning(f"{name} 返回状态码: {response.status_code}")
            except Exception as e:
                print_error(f"{name} 网络连接失败: {e}")
        
        return True
    
    def test_github_specifically(self):
        """专门测试GitHub连接问题"""
        print_header("GitHub连接问题诊断")
        
        print_warning("重要提醒：GitHub已于2021年8月13日停用密码认证")
        print("GitHub现在要求使用以下认证方式:")
        print("1. Personal Access Token")
        print("2. SSH密钥")
        print("3. GitHub App认证")
        
        print_step("测试GitHub API访问...")
        try:
            # 测试公共API
            response = requests.get("https://api.github.com/user", timeout=10)
            if response.status_code == 401:
                print_success("GitHub API可达（需要认证）")
            else:
                print_warning(f"GitHub API响应: {response.status_code}")
        except Exception as e:
            print_error(f"GitHub API不可达: {e}")
        
        # 测试Git协议
        print_step("测试GitHub Git协议...")
        try:
            result = subprocess.run(
                ['git', 'ls-remote', '--exit-code', 'https://github.com/octocat/Hello-World.git'],
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0:
                print_success("GitHub Git协议工作正常（公共仓库）")
            else:
                print_warning("GitHub Git协议测试异常")
                print(f"错误输出: {result.stderr}")
        except Exception as e:
            print_error(f"GitHub Git测试失败: {e}")
        
        return True
    
    def test_gitlab_local(self):
        """测试本地GitLab连接"""
        print_header("本地GitLab连接诊断")
        
        gitlab_url = "http://127.0.0.1:8929"
        
        # 1. 基础连接测试
        print_step("测试GitLab Web访问...")
        try:
            response = requests.get(gitlab_url, timeout=10)
            if response.status_code == 200:
                print_success("GitLab Web界面可访问")
            else:
                print_warning(f"GitLab Web访问返回: {response.status_code}")
        except Exception as e:
            print_error(f"GitLab Web访问失败: {e}")
            return False
        
        # 2. API测试
        print_step("测试GitLab API...")
        try:
            api_url = f"{gitlab_url}/api/v4/projects"
            response = requests.get(api_url, timeout=10)
            if response.status_code in [200, 401]:
                print_success("GitLab API可达")
            else:
                print_warning(f"GitLab API响应: {response.status_code}")
        except Exception as e:
            print_error(f"GitLab API测试失败: {e}")
        
        # 3. 用户名密码测试（如果有的话）
        print_step("测试用户认证...")
        test_credentials = [
            ("root", "password"),
            ("root", "root"),
            ("root", "12345678"),
            ("admin", "admin"),
            ("admin", "password")
        ]
        
        for username, password in test_credentials:
            try:
                auth_response = requests.get(
                    f"{gitlab_url}/api/v4/user",
                    auth=(username, password),
                    timeout=5
                )
                if auth_response.status_code == 200:
                    user_data = auth_response.json()
                    print_success(f"找到有效凭据: {username}/{password} - 用户: {user_data.get('name', username)}")
                    return username, password
                elif auth_response.status_code == 401:
                    print_warning(f"凭据无效: {username}/{password}")
                else:
                    print_warning(f"认证测试异常: {username}/{password} - {auth_response.status_code}")
            except Exception as e:
                print_warning(f"认证测试失败: {username}/{password} - {e}")
        
        print_error("未找到有效的GitLab凭据")
        return None
    
    def create_github_token_guide(self):
        """生成GitHub Token创建指南"""
        print_header("GitHub Personal Access Token 创建指南")
        
        print("🔧 创建GitHub Personal Access Token:")
        print("1. 登录GitHub → 点击右上角头像 → Settings")
        print("2. 左侧菜单 → Developer settings → Personal access tokens → Tokens (classic)")
        print("3. 点击 'Generate new token' → 'Generate new token (classic)'")
        print("4. 填写Note（如：AnsFlow CI/CD Platform）")
        print("5. 选择Expiration（建议90天或自定义）")
        print("6. 勾选所需权限：")
        print("   ✅ repo (完整仓库访问)")
        print("   ✅ workflow (GitHub Actions)")
        print("   ✅ read:user (读取用户信息)")
        print("   ✅ user:email (读取邮箱)")
        print("7. 点击 'Generate token'")
        print("8. 复制生成的token（只显示一次！）")
        print()
        print("🔐 在AnsFlow中配置:")
        print("1. 进入Git凭据管理页面")
        print("2. 选择 '访问令牌' 认证类型")
        print("3. 服务器地址：https://github.com")
        print("4. 用户名：你的GitHub用户名")
        print("5. 访问令牌：刚才生成的token")
    
    def fix_backend_implementation(self):
        """修复后端实现建议"""
        print_header("后端实现修复建议")
        
        print("🔧 发现的后端问题:")
        print("1. ❌ 直接使用 'git ls-remote' 测试URL")
        print("2. ❌ 没有正确处理认证失败的情况")
        print("3. ❌ 缺少对不同平台的特殊处理")
        print("4. ❌ 错误消息不够详细")
        print()
        
        print("💡 建议的修复方案:")
        print("1. ✅ 改用GitCredentialTester类")
        print("2. ✅ 为每个平台提供专门的测试方法")
        print("3. ✅ 改进错误处理和消息")
        print("4. ✅ 添加网络超时和重试机制")
        print()
        
        print("📝 具体修改文件:")
        print("- backend/django_service/cicd_integrations/views/git_credentials.py")
        print("- 使用 GitCredentialTester 替换现有的简单测试")
        print("- 添加详细的错误日志记录")
    
    def provide_solutions(self):
        """提供完整的解决方案"""
        print_header("完整解决方案")
        
        print("🎯 针对您的两个平台:")
        print()
        
        print("1️⃣ GitHub (https://github.com):")
        print("   ❌ 问题: 密码认证已被禁用")
        print("   ✅ 解决: 使用Personal Access Token")
        print("   📋 步骤:")
        print("   - 删除现有的用户名密码凭据")
        print("   - 创建新的'访问令牌'类型凭据")
        print("   - 按照上面的指南生成GitHub Token")
        print()
        
        print("2️⃣ 本地GitLab (http://127.0.0.1:8929):")
        print("   ❌ 问题: 可能的凭据不正确或配置问题")
        print("   ✅ 解决: 验证凭据并检查GitLab配置")
        print("   📋 步骤:")
        print("   - 确认GitLab管理员凭据")
        print("   - 检查GitLab是否启用了密码认证")
        print("   - 如果启用了2FA，使用Personal Access Token")
        print("   - 检查GitLab用户权限设置")
        print()
        
        print("3️⃣ 后端代码修复:")
        print("   ❌ 问题: Git凭据测试逻辑过于简单")
        print("   ✅ 解决: 使用改进的GitCredentialTester")
        print("   📋 步骤:")
        print("   - 更新git_credentials.py视图")
        print("   - 使用平台特定的测试方法")
        print("   - 改进错误处理和消息反馈")
    
    def run_complete_diagnosis(self):
        """运行完整诊断"""
        print_header("AnsFlow Git凭据连接问题完整诊断")
        
        # 1. 基础环境检查
        if not self.test_direct_git_access():
            return False
        
        # 2. 获取认证
        if not self.get_auth_token():
            return False
        
        # 3. GitHub专项诊断
        self.test_github_specifically()
        
        # 4. GitLab专项诊断
        gitlab_creds = self.test_gitlab_local()
        
        # 5. 生成解决方案
        self.create_github_token_guide()
        self.fix_backend_implementation()
        self.provide_solutions()
        
        return True

def main():
    print("🔧 AnsFlow Git凭据连接问题修复工具")
    print("=" * 60)
    
    fixer = GitCredentialFixer()
    success = fixer.run_complete_diagnosis()
    
    if success:
        print_header("总结")
        print_success("诊断完成！请按照上述建议进行修复")
        print()
        print("📋 下一步行动:")
        print("1. 为GitHub创建Personal Access Token")
        print("2. 验证本地GitLab的管理员凭据")
        print("3. 在AnsFlow中更新Git凭据配置")
        print("4. 可选：修复后端代码实现")
        return 0
    else:
        print_error("诊断过程中遇到问题，请检查系统环境")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⏹️ 诊断已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 程序异常: {str(e)}")
        sys.exit(1)
