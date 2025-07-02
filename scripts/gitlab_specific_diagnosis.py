#!/usr/bin/env python3
"""
专门针对GitLab凭据问题的诊断脚本
检查GitLab配置和认证设置

使用方法:
python scripts/gitlab_specific_diagnosis.py
"""

import requests
import subprocess
import json
import sys
import os
from urllib.parse import quote

class GitLabDiagnoser:
    def __init__(self, gitlab_url="http://127.0.0.1:8929"):
        self.gitlab_url = gitlab_url.rstrip('/')
        self.session = requests.Session()
        
    def test_gitlab_web_interface(self):
        """测试GitLab Web界面"""
        print("🔍 检查GitLab Web界面...")
        
        try:
            response = self.session.get(self.gitlab_url, timeout=10)
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(list(response.headers.items())[:5])}")  # 只显示前5个头
            
            if response.status_code == 200:
                print("✅ GitLab Web界面可访问")
                
                # 检查是否显示登录页面
                if 'sign_in' in response.text.lower() or 'login' in response.text.lower():
                    print("📋 检测到登录页面")
                elif 'dashboard' in response.text.lower() or 'projects' in response.text.lower():
                    print("📋 可能已经登录或允许匿名访问")
                    
                return True
            else:
                print(f"❌ GitLab Web访问异常: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ GitLab Web访问失败: {e}")
            return False
    
    def test_gitlab_api_anonymous(self):
        """测试GitLab API匿名访问"""
        print("\n🔍 测试GitLab API匿名访问...")
        
        test_endpoints = [
            ("/api/v4/version", "版本信息"),
            ("/api/v4/projects", "项目列表"),
            ("/api/v4/users", "用户列表"),
            ("/api/v4/application/settings", "应用设置")
        ]
        
        for endpoint, description in test_endpoints:
            try:
                url = f"{self.gitlab_url}{endpoint}"
                response = self.session.get(url, timeout=10)
                print(f"  {description} ({endpoint}): {response.status_code}")
                
                if response.status_code == 200:
                    if endpoint == "/api/v4/version":
                        try:
                            version_data = response.json()
                            print(f"    GitLab版本: {version_data.get('version', 'Unknown')}")
                        except:
                            pass
                elif response.status_code == 401:
                    print(f"    需要认证")
                elif response.status_code == 403:
                    print(f"    权限不足")
                    
            except Exception as e:
                print(f"  {description}: 错误 - {e}")
    
    def check_gitlab_authentication_settings(self):
        """检查GitLab认证设置"""
        print("\n🔍 检查GitLab认证配置...")
        
        # 检查是否启用了基础认证
        try:
            auth_test_url = f"{self.gitlab_url}/api/v4/user"
            
            # 测试Basic Auth头
            response = self.session.get(
                auth_test_url, 
                headers={'Authorization': 'Basic dGVzdDp0ZXN0'}  # test:test
            )
            
            print(f"Basic Auth测试状态码: {response.status_code}")
            
            if response.status_code == 401:
                try:
                    error_data = response.json()
                    print(f"认证错误信息: {error_data}")
                except:
                    print(f"认证错误响应: {response.text[:200]}")
            
        except Exception as e:
            print(f"Basic Auth测试失败: {e}")
    
    def test_common_gitlab_issues(self):
        """测试常见GitLab问题"""
        print("\n🔍 检查常见GitLab配置问题...")
        
        issues_found = []
        
        # 1. 检查是否需要HTTPS
        if self.gitlab_url.startswith('http://'):
            print("⚠️ 使用HTTP协议，某些Git操作可能需要HTTPS")
            issues_found.append("使用HTTP而非HTTPS")
        
        # 2. 检查端口
        if ':8929' in self.gitlab_url:
            print("📋 使用非标准端口8929")
        
        # 3. 测试Git协议访问
        print("🔍 测试Git协议访问...")
        try:
            # 测试匿名Git访问
            result = subprocess.run(
                ['git', 'ls-remote', '--exit-code', f'{self.gitlab_url}/root/test.git'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            print(f"Git ls-remote返回码: {result.returncode}")
            if result.stderr:
                print(f"Git错误输出: {result.stderr}")
                
                if 'authentication failed' in result.stderr.lower():
                    print("✅ Git协议工作，但需要认证（正常）")
                elif 'repository not found' in result.stderr.lower():
                    print("✅ Git协议工作，仓库不存在（正常）")
                elif 'connection refused' in result.stderr.lower():
                    print("❌ Git协议连接被拒绝")
                    issues_found.append("Git协议连接被拒绝")
                    
        except Exception as e:
            print(f"Git协议测试失败: {e}")
            issues_found.append(f"Git协议测试异常: {e}")
        
        return issues_found
    
    def provide_gitlab_solutions(self, issues):
        """提供GitLab解决方案"""
        print("\n🔧 GitLab配置建议:")
        
        print("\n1️⃣ 确认GitLab管理员凭据:")
        print("   - 检查GitLab初始安装时设置的root密码")
        print("   - 可能需要重置root密码")
        print("   - 检查GitLab配置文件中的密码设置")
        
        print("\n2️⃣ 检查GitLab认证配置:")
        print("   - 登录GitLab Web界面 → Admin Area → Settings → Sign-in restrictions")
        print("   - 确认是否启用了密码认证")
        print("   - 检查是否强制启用了2FA")
        
        print("\n3️⃣ 重置root密码（如果需要）:")
        print("   - 进入GitLab容器或服务器")
        print("   - 运行: gitlab-rake 'gitlab:password:reset[root]'")
        print("   - 或编辑GitLab配置重新设置")
        
        print("\n4️⃣ 创建Personal Access Token:")
        print("   - 如果密码认证被禁用，使用Token认证")
        print("   - 登录GitLab → User Settings → Access Tokens")
        print("   - 创建具有api、read_repository权限的Token")
        
        print("\n5️⃣ 检查GitLab日志:")
        print("   - 查看GitLab日志了解认证失败原因")
        print("   - sudo gitlab-ctl tail")
        
        if issues:
            print("\n❗ 发现的问题:")
            for issue in issues:
                print(f"   - {issue}")
    
    def run_diagnosis(self):
        """运行完整诊断"""
        print("🚀 GitLab专项诊断")
        print("=" * 50)
        
        # 1. Web界面测试
        web_ok = self.test_gitlab_web_interface()
        
        # 2. API测试
        self.test_gitlab_api_anonymous()
        
        # 3. 认证设置检查
        self.check_gitlab_authentication_settings()
        
        # 4. 常见问题检查
        issues = self.test_common_gitlab_issues()
        
        # 5. 解决方案
        self.provide_gitlab_solutions(issues)
        
        print("\n📋 建议的下一步:")
        print("1. 确认GitLab管理员用户名和密码")
        print("2. 如果忘记密码，重置root密码")
        print("3. 检查GitLab认证配置")
        print("4. 考虑使用Personal Access Token替代密码")
        print("5. 更新AnsFlow中的Git凭据配置")

def main():
    gitlab_url = input("GitLab地址 (默认: http://127.0.0.1:8929): ").strip()
    if not gitlab_url:
        gitlab_url = "http://127.0.0.1:8929"
    
    diagnoser = GitLabDiagnoser(gitlab_url)
    diagnoser.run_diagnosis()
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⏹️ 诊断已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 程序异常: {str(e)}")
        sys.exit(1)
