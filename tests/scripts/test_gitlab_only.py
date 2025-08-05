#!/usr/bin/env python3
"""
AnsFlow GitLab专项测试工具
只测试GitLab凭据，排除其他平台干扰

使用方法:
python scripts/test_gitlab_only.py

功能:
1. 获取并过滤只测试GitLab凭据
2. 通过API测试GitLab连接
3. 提供GitLab特定的诊断和建议
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
    print(f"{Colors.BOLD}🔗 {message}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")

class GitLabTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
    def get_auth_token(self):
        """获取认证令牌"""
        print_step("获取AnsFlow认证令牌...")
        
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
    
    def get_gitlab_credentials(self):
        """获取GitLab凭据列表"""
        print_step("获取GitLab凭据列表...")
        
        try:
            response = self.session.get(f"{API_BASE}/cicd/git-credentials/")
            
            if response.status_code == 200:
                data = response.json()
                
                # 处理分页数据结构
                if isinstance(data, dict) and 'results' in data:
                    all_credentials = data['results']
                elif isinstance(data, list):
                    all_credentials = data
                else:
                    print_error(f"意外的数据格式: {type(data)}")
                    return []
                
                # 只保留GitLab凭据
                gitlab_credentials = [
                    cred for cred in all_credentials 
                    if cred.get('platform', '').lower() == 'gitlab' or 
                    'gitlab' in cred.get('server_url', '').lower()
                ]
                
                print_success(f"获取到 {len(gitlab_credentials)} 个GitLab凭据")
                return gitlab_credentials
            else:
                print_error(f"获取凭据列表失败: {response.status_code}")
                print(f"响应: {response.text}")
                return []
                
        except Exception as e:
            print_error(f"请求失败: {e}")
            return []
    
    def test_credential_via_api(self, credential_id, credential_name):
        """通过API测试凭据"""
        print_step(f"通过API测试GitLab凭据: {credential_name}")
        
        try:
            response = self.session.post(f"{API_BASE}/cicd/git-credentials/{credential_id}/test_connection/")
            
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print_success("✅ GitLab API测试成功")
                    return True
                else:
                    error_msg = result.get('message', 'Unknown error')
                    print_error(f"❌ GitLab API测试失败: {error_msg}")
                    self._analyze_gitlab_error(error_msg)
                    return False
            else:
                print_error(f"❌ API调用失败: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"错误详情: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"❌ API测试异常: {e}")
            return False
    
    def _analyze_gitlab_error(self, error_message):
        """分析GitLab错误信息"""
        error_lower = error_message.lower()
        
        print_warning("GitLab错误分析:")
        
        if 'authentication failed' in error_lower or 'unauthorized' in error_lower:
            print("🔹 认证失败原因可能包括:")
            print("   - 用户名或密码错误")
            print("   - 启用了2FA，需要使用Personal Access Token")
            print("   - GitLab禁用了密码认证")
            print("   - 账号被锁定或禁用")
            
        elif 'ssl' in error_lower or 'certificate' in error_lower:
            print("🔹 SSL证书问题:")
            print("   - 本地GitLab使用自签名证书")
            print("   - 需要配置Git忽略SSL验证或添加受信任证书")
            
        elif 'connection refused' in error_lower:
            print("🔹 连接被拒绝:")
            print("   - GitLab服务未启动")
            print("   - 端口8929不可访问")
            print("   - 防火墙阻止连接")
            
        elif 'timeout' in error_lower:
            print("🔹 连接超时:")
            print("   - GitLab服务响应慢")
            print("   - 网络连接问题")
            
        elif 'repository not found' in error_lower:
            print("🔹 仓库不存在:")
            print("   - 测试仓库路径不存在（这可能是正常的）")
            print("   - 如果认证成功，这个错误是可以接受的")
            
        elif 'encryption' in error_lower or 'decrypt' in error_lower:
            print("🔹 加密解密问题:")
            print("   - GIT_CREDENTIAL_ENCRYPTION_KEY未设置")
            print("   - 凭据加密/解密失败")
            print("   - 需要重新设置凭据")
            
        else:
            print(f"🔹 未知错误: {error_message}")
    
    def test_gitlab_connectivity(self):
        """测试GitLab连通性"""
        print_header("GitLab连通性测试")
        
        gitlab_url = "http://127.0.0.1:8929"
        
        print_step(f"测试GitLab Web访问: {gitlab_url}")
        try:
            response = requests.get(gitlab_url, timeout=10)
            if response.status_code == 200:
                print_success("GitLab Web界面可访问")
            else:
                print_warning(f"GitLab Web返回状态码: {response.status_code}")
        except Exception as e:
            print_error(f"GitLab Web访问失败: {e}")
        
        print_step(f"测试GitLab API访问: {gitlab_url}/api/v4/version")
        try:
            response = requests.get(f"{gitlab_url}/api/v4/version", timeout=10)
            if response.status_code == 200:
                version_info = response.json()
                print_success(f"GitLab API可访问，版本: {version_info.get('version', 'Unknown')}")
            else:
                print_warning(f"GitLab API返回状态码: {response.status_code}")
        except Exception as e:
            print_error(f"GitLab API访问失败: {e}")
    
    def provide_gitlab_solutions(self):
        """提供GitLab特定的解决方案"""
        print_header("GitLab问题解决方案")
        
        print("🔧 GitLab凭据问题解决步骤:")
        print()
        print("1. 检查加密密钥配置:")
        print("   ❯ 确认 backend/django_service/settings.py 中设置了 GIT_CREDENTIAL_ENCRYPTION_KEY")
        print("   ❯ 如果未设置，运行: python scripts/fix_git_credential_encryption.py")
        print()
        print("2. 检查GitLab认证设置:")
        print("   ❯ 访问 http://127.0.0.1:8929/admin")
        print("   ❯ 用root账号登录")
        print("   ❯ 检查是否启用了2FA")
        print("   ❯ 如果启用2FA，创建Personal Access Token")
        print()
        print("3. 重新创建GitLab凭据:")
        print("   ❯ 在AnsFlow前端删除现有GitLab凭据")
        print("   ❯ 重新添加凭据，确保用户名密码正确")
        print("   ❯ 如果有2FA，使用Access Token")
        print()
        print("4. 测试GitLab连接:")
        print("   ❯ 在GitLab中创建测试仓库")
        print("   ❯ 使用git命令手动测试认证")
        print("   ❯ 确认网络连通性")
        print()
        print("5. 检查Django日志:")
        print("   ❯ 查看Django服务器控制台输出")
        print("   ❯ 检查是否有详细错误信息")
    
    def run_gitlab_test(self):
        """运行GitLab专项测试"""
        print_header("AnsFlow GitLab凭据专项测试")
        
        # 1. 获取认证令牌
        if not self.get_auth_token():
            return False
        
        # 2. 测试GitLab连通性
        self.test_gitlab_connectivity()
        
        # 3. 获取GitLab凭据列表
        gitlab_credentials = self.get_gitlab_credentials()
        if not gitlab_credentials:
            print_warning("没有找到GitLab凭据")
            print("请在AnsFlow前端创建GitLab凭据后再次测试")
            self.provide_gitlab_solutions()
            return False
        
        # 4. 测试每个GitLab凭据
        all_success = True
        
        for credential in gitlab_credentials:
            print_header(f"测试GitLab凭据: {credential['name']}")
            
            print(f"📋 凭据详情:")
            print(f"   ID: {credential['id']}")
            print(f"   名称: {credential['name']}")
            print(f"   服务器: {credential['server_url']}")
            print(f"   用户名: {credential['username']}")
            print(f"   认证类型: {credential['credential_type']}")
            print(f"   是否启用: {credential['is_active']}")
            
            # API测试
            success = self.test_credential_via_api(credential['id'], credential['name'])
            if not success:
                all_success = False
            
            print()
        
        # 5. 总结和建议
        print_header("测试总结")
        
        total_gitlab = len(gitlab_credentials)
        if all_success:
            print_success(f"所有 {total_gitlab} 个GitLab凭据测试成功 🎉")
        else:
            print_error(f"发现GitLab凭据连接问题")
            self.provide_gitlab_solutions()
        
        return all_success

def main():
    print("🔗 AnsFlow GitLab凭据专项测试工具")
    print("=" * 60)
    
    tester = GitLabTester()
    success = tester.run_gitlab_test()
    
    if success:
        print_success("\n🎉 所有GitLab凭据连接正常")
        return 0
    else:
        print_error("\n❌ 发现GitLab凭据连接问题，请参考上述建议进行修复")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⏹️ 测试已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 程序异常: {str(e)}")
        sys.exit(1)
