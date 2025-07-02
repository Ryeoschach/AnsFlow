#!/usr/bin/env python3
"""
重置GitLab凭据脚本
解决密码修改后的缓存问题

使用方法:
python scripts/reset_gitlab_credential.py
"""

import requests
import json
import sys
import os

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
    print(f"{Colors.BOLD}🔧 {message}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")

class GitLabCredentialResetter:
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
                return []
                
        except Exception as e:
            print_error(f"请求失败: {e}")
            return []
    
    def update_credential(self, credential_id, password):
        """更新凭据密码"""
        print_step(f"更新凭据ID {credential_id} 的密码...")
        
        update_data = {
            "password": password
        }
        
        try:
            response = self.session.patch(f"{API_BASE}/cicd/git-credentials/{credential_id}/", json=update_data)
            
            if response.status_code == 200:
                print_success("凭据密码更新成功")
                return True
            else:
                print_error(f"更新失败: {response.status_code}")
                print(f"响应: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"更新请求失败: {e}")
            return False
    
    def test_credential(self, credential_id, credential_name):
        """测试凭据连接"""
        print_step(f"测试凭据连接: {credential_name}")
        
        try:
            response = self.session.post(f"{API_BASE}/cicd/git-credentials/{credential_id}/test_connection/")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print_success("✅ 凭据测试成功")
                    return True
                else:
                    error_msg = result.get('message', 'Unknown error')
                    print_error(f"❌ 凭据测试失败: {error_msg}")
                    return False
            else:
                print_error(f"❌ 测试API调用失败: {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"❌ 测试异常: {e}")
            return False
    
    def reset_gitlab_credentials(self):
        """重置GitLab凭据"""
        print_header("GitLab凭据重置工具")
        
        # 1. 获取认证令牌
        if not self.get_auth_token():
            return False
        
        # 2. 获取GitLab凭据列表
        gitlab_credentials = self.get_gitlab_credentials()
        if not gitlab_credentials:
            print_warning("没有找到GitLab凭据")
            return False
        
        # 3. 显示当前凭据并询问是否重置
        print_header("当前GitLab凭据")
        for i, credential in enumerate(gitlab_credentials):
            print(f"{i+1}. 名称: {credential['name']}")
            print(f"   ID: {credential['id']}")
            print(f"   用户名: {credential['username']}")
            print(f"   服务器: {credential['server_url']}")
            print()
        
        # 4. 询问要重置的凭据
        try:
            choice = input("请输入要重置的凭据编号 (1-{}，0=全部): ".format(len(gitlab_credentials)))
            choice = int(choice)
            
            if choice == 0:
                selected_credentials = gitlab_credentials
            elif 1 <= choice <= len(gitlab_credentials):
                selected_credentials = [gitlab_credentials[choice-1]]
            else:
                print_error("无效的选择")
                return False
                
        except (ValueError, KeyboardInterrupt):
            print_error("操作已取消")
            return False
        
        # 5. 询问新密码
        try:
            new_password = input("请输入GitLab root账号的正确密码: ").strip()
            if not new_password:
                print_error("密码不能为空")
                return False
        except KeyboardInterrupt:
            print_error("操作已取消")
            return False
        
        # 6. 重置凭据
        all_success = True
        for credential in selected_credentials:
            print_header(f"重置凭据: {credential['name']}")
            
            # 更新密码
            if self.update_credential(credential['id'], new_password):
                # 测试连接
                if self.test_credential(credential['id'], credential['name']):
                    print_success(f"✅ 凭据 {credential['name']} 重置成功")
                else:
                    print_error(f"❌ 凭据 {credential['name']} 测试失败")
                    all_success = False
            else:
                print_error(f"❌ 凭据 {credential['name']} 更新失败")
                all_success = False
        
        return all_success

def main():
    print("🔧 AnsFlow GitLab凭据重置工具")
    print("=" * 60)
    print("此工具可以帮您重置GitLab凭据密码，解决缓存问题")
    print()
    
    resetter = GitLabCredentialResetter()
    success = resetter.reset_gitlab_credentials()
    
    if success:
        print_success("\n🎉 GitLab凭据重置成功")
        print("建议：")
        print("1. 刷新AnsFlow前端页面")
        print("2. 重新测试GitLab连接")
        return 0
    else:
        print_error("\n❌ GitLab凭据重置失败")
        print("建议：")
        print("1. 检查GitLab root账号密码是否正确")
        print("2. 确认GitLab服务正常运行")
        print("3. 在AnsFlow前端手动删除并重新创建凭据")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⏹️ 操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 程序异常: {str(e)}")
        sys.exit(1)
