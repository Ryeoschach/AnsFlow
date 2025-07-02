#!/usr/bin/env python3
"""
AnsFlow Git凭据连接问题诊断工具
专门用于诊断Git凭据管理中的连接失败问题

使用方法:
python scripts/diagnose_git_credentials.py

功能:
1. 测试后端Git凭据测试API
2. 模拟前端测试连接调用
3. 直接测试Git连接
4. 提供详细的错误诊断和解决方案
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

class GitCredentialDiagnoser:
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
    
    def get_git_credentials(self):
        """获取Git凭据列表"""
        print_step("获取Git凭据列表...")
        
        try:
            response = self.session.get(f"{API_BASE}/cicd/git-credentials/")
            
            if response.status_code == 200:
                data = response.json()
                
                # 处理分页数据结构
                if isinstance(data, dict) and 'results' in data:
                    credentials = data['results']
                    print_success(f"获取到 {len(credentials)} 个Git凭据")
                elif isinstance(data, list):
                    credentials = data
                    print_success(f"获取到 {len(credentials)} 个Git凭据")
                else:
                    print_error(f"意外的数据格式: {type(data)}")
                    return []
                
                return credentials
            else:
                print_error(f"获取凭据列表失败: {response.status_code}")
                print(f"响应: {response.text}")
                return []
                
        except Exception as e:
            print_error(f"请求失败: {e}")
            return []
    
    def test_credential_via_api(self, credential_id):
        """通过API测试凭据"""
        print_step(f"通过API测试凭据 ID: {credential_id}")
        
        try:
            response = self.session.post(f"{API_BASE}/cicd/git-credentials/{credential_id}/test_connection/")
            
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print_success("API测试成功")
                else:
                    print_error(f"API测试失败: {result.get('message', 'Unknown error')}")
                return result
            else:
                print_error(f"API调用失败: {response.status_code}")
                return {"success": False, "message": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print_error(f"API测试异常: {e}")
            return {"success": False, "message": str(e)}
    
    def test_git_connection_direct(self, platform, server_url, credential_type, username, password):
        """直接测试Git连接"""
        print_step(f"直接测试Git连接...")
        print(f"平台: {platform}")
        print(f"服务器: {server_url}")
        print(f"认证类型: {credential_type}")
        print(f"用户名: {username}")
        
        if credential_type == "username_password":
            return self._test_username_password_direct(server_url, username, password)
        else:
            print_warning(f"暂不支持直接测试认证类型: {credential_type}")
            return False
    
    def _test_username_password_direct(self, server_url, username, password):
        """直接测试用户名密码认证"""
        print_step("执行用户名密码认证测试...")
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix='git_test_')
        
        try:
            # 构造认证URL
            parsed_url = urlparse(server_url)
            
            if server_url.startswith('https://'):
                auth_url = f"https://{quote(username)}:{quote(password)}@{server_url[8:]}"
            elif server_url.startswith('http://'):
                auth_url = f"http://{quote(username)}:{quote(password)}@{server_url[7:]}"
            else:
                print_error("无效的服务器URL格式")
                return False
            
            # 测试仓库URL - 使用一个通用的测试路径
            # 本地GitLab使用实际存在的仓库
            if '127.0.0.1:8929' in server_url:
                test_repo_url = f"{auth_url}/root/demo.git"
            else:
                test_repo_url = f"{auth_url}/test.git"
            
            print(f"测试URL: {server_url}/{'root/demo.git' if '127.0.0.1:8929' in server_url else 'test.git'}")
            
            # 设置环境变量
            env = os.environ.copy()
            env['GIT_TERMINAL_PROMPT'] = '0'
            env['GIT_ASKPASS'] = 'echo'
            
            # 使用git ls-remote测试
            cmd = ['git', 'ls-remote', '--exit-code', test_repo_url]
            
            print_step("执行: git ls-remote --exit-code [URL]")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                cwd=temp_dir
            )
            
            print(f"返回码: {result.returncode}")
            print(f"标准输出: {result.stdout}")
            print(f"错误输出: {result.stderr}")
            
            # 分析结果
            if result.returncode == 0:
                print_success("Git认证成功")
                return True
            elif result.returncode == 2:
                # 仓库不存在，但认证成功
                print_success("Git认证成功（测试仓库不存在是正常的）")
                return True
            elif result.returncode == 128:
                if 'authentication failed' in result.stderr.lower():
                    print_error("Git认证失败：用户名或密码错误")
                    self._provide_auth_suggestions(server_url)
                elif 'repository not found' in result.stderr.lower():
                    print_success("Git认证成功（测试仓库不存在是正常的）")
                    return True
                else:
                    print_error(f"Git操作失败: {result.stderr}")
                    self._analyze_git_error(result.stderr)
            else:
                print_error(f"Git测试失败，返回码: {result.returncode}")
                print_error(f"错误信息: {result.stderr}")
                self._analyze_git_error(result.stderr)
            
            return False
            
        except subprocess.TimeoutExpired:
            print_error("Git操作超时")
            return False
        except FileNotFoundError:
            print_error("系统中未找到git命令，请确保已安装Git")
            return False
        except Exception as e:
            print_error(f"Git测试异常: {e}")
            return False
        finally:
            # 清理临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def _provide_auth_suggestions(self, server_url):
        """提供认证建议"""
        print_warning("认证失败可能的原因和解决方案:")
        
        if 'github.com' in server_url:
            print("🔹 GitHub 建议:")
            print("   - GitHub已禁用密码认证，请使用Personal Access Token")
            print("   - 创建Token: Settings > Developer settings > Personal access tokens")
            print("   - 在AnsFlow中选择'访问令牌'认证类型")
        elif 'gitlab' in server_url.lower():
            print("🔹 GitLab 建议:")
            print("   - 检查是否启用了2FA（二因子认证）")
            print("   - 如果启用了2FA，请使用Personal Access Token")
            print("   - 创建Token: User Settings > Access Tokens")
            print("   - 在AnsFlow中选择'访问令牌'认证类型")
        else:
            print("🔹 通用建议:")
            print("   - 检查用户名和密码是否正确")
            print("   - 检查是否有仓库访问权限")
            print("   - 考虑使用Personal Access Token替代密码")
    
    def _analyze_git_error(self, error_output):
        """分析Git错误输出"""
        error_lower = error_output.lower()
        
        if 'ssl' in error_lower:
            print_warning("SSL/TLS相关问题:")
            print("   - 可能是SSL证书问题")
            print("   - 对于本地GitLab，考虑配置受信任证书")
        elif 'timeout' in error_lower:
            print_warning("网络超时问题:")
            print("   - 检查网络连接")
            print("   - 检查服务器地址是否正确")
        elif 'connection refused' in error_lower:
            print_warning("连接被拒绝:")
            print("   - 检查服务器是否正在运行")
            print("   - 检查端口是否正确")
        elif 'host' in error_lower and 'resolve' in error_lower:
            print_warning("DNS解析问题:")
            print("   - 检查服务器地址是否正确")
            print("   - 检查DNS配置")
    
    def diagnose_credential(self, credential):
        """诊断单个凭据"""
        print_header(f"诊断凭据: {credential['name']}")
        
        print(f"ID: {credential['id']}")
        print(f"名称: {credential['name']}")
        print(f"平台: {credential['platform']}")
        print(f"认证类型: {credential['credential_type']}")
        print(f"服务器地址: {credential['server_url']}")
        print(f"用户名: {credential['username']}")
        print(f"是否启用: {credential['is_active']}")
        
        if credential.get('last_test_at'):
            print(f"上次测试时间: {credential['last_test_at']}")
            print(f"上次测试结果: {'成功' if credential.get('last_test_result') else '失败'}")
        
        # 1. 通过API测试
        print_header("1. API测试")
        api_result = self.test_credential_via_api(credential['id'])
        
        # 2. 直接测试Git连接
        print_header("2. 直接Git连接测试")
        if credential['credential_type'] == 'username_password':
            # 注意：这里我们无法获取到实际的密码，因为它是加密存储的
            print_warning("无法直接测试：密码已加密存储")
            print("建议检查后端GitCredentialTester的实现")
        else:
            print_warning(f"暂不支持直接测试认证类型: {credential['credential_type']}")
        
        return api_result
    
    def run_diagnosis(self):
        """运行完整诊断"""
        print_header("AnsFlow Git凭据连接问题诊断")
        
        # 1. 获取认证令牌
        if not self.get_auth_token():
            return False
        
        # 2. 获取Git凭据列表
        credentials = self.get_git_credentials()
        if not credentials:
            print_warning("没有找到Git凭据，请先创建凭据")
            return False
        
        # 3. 逐个诊断凭据
        failed_credentials = []
        
        for credential in credentials:
            result = self.diagnose_credential(credential)
            if not result.get('success'):
                failed_credentials.append(credential)
        
        # 4. 总结报告
        print_header("诊断总结")
        
        total = len(credentials)
        failed = len(failed_credentials)
        success = total - failed
        
        print(f"总凭据数: {total}")
        print_success(f"测试成功: {success}")
        print_error(f"测试失败: {failed}")
        
        if failed_credentials:
            print_header("失败凭据详情")
            for cred in failed_credentials:
                print(f"- {cred['name']} ({cred['platform']}) - {cred['server_url']}")
        
        # 5. 提供建议
        self._provide_general_suggestions()
        
        return failed == 0
    
    def _provide_general_suggestions(self):
        """提供通用建议"""
        print_header("问题解决建议")
        
        print("🔹 常见问题和解决方案:")
        print()
        print("1. GitHub连接失败:")
        print("   - GitHub已禁用密码认证，必须使用Personal Access Token")
        print("   - 创建Token: https://github.com/settings/personal-access-tokens/tokens")
        print("   - 在AnsFlow中使用'访问令牌'认证类型")
        print()
        print("2. GitLab连接失败:")
        print("   - 检查GitLab是否启用了2FA")
        print("   - 如果启用2FA，需要使用Personal Access Token")
        print("   - 本地GitLab可能需要配置SSL证书")
        print()
        print("3. 后端实现问题:")
        print("   - 检查GitCredentialViewSet._test_username_password_connection方法")
        print("   - 确认git命令在服务器上可用")
        print("   - 检查Django服务器的网络配置")
        print()
        print("4. 数据库问题:")
        print("   - 确认凭据密码正确加密/解密")
        print("   - 检查GitCredential.decrypt_password()方法")
        print()
        print("5. 网络问题:")
        print("   - 确认服务器可以访问外部Git服务")
        print("   - 检查防火墙和代理设置")

def main():
    print("🚀 AnsFlow Git凭据连接问题诊断工具")
    print("=" * 60)
    
    diagnoser = GitCredentialDiagnoser()
    success = diagnoser.run_diagnosis()
    
    if success:
        print_success("所有Git凭据连接正常")
        return 0
    else:
        print_error("发现Git凭据连接问题，请参考上述建议进行修复")
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
