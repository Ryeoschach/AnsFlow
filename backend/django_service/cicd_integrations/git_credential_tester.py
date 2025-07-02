"""
Git凭据连接测试工具
支持测试各种Git平台的认证方式
"""
import os
import subprocess
import tempfile
import shutil
import requests
from urllib.parse import urlparse
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class GitCredentialTester:
    """Git凭据测试类"""
    
    def __init__(self):
        self.temp_dir = None
    
    def test_credential(self, platform: str, server_url: str, credential_type: str, 
                       username: str = None, password: str = None, 
                       ssh_private_key: str = None, email: str = None) -> Tuple[bool, str]:
        """
        测试Git凭据连接
        
        Args:
            platform: Git平台类型 (github, gitlab, gitee, etc.)
            server_url: Git服务器URL
            credential_type: 认证类型 (username_password, access_token, ssh_key, oauth)
            username: 用户名
            password: 密码或Token
            ssh_private_key: SSH私钥
            email: 邮箱地址
            
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息或成功信息)
        """
        try:
            if credential_type == 'username_password':
                return self._test_username_password(server_url, username, password)
            elif credential_type == 'access_token':
                return self._test_access_token(platform, server_url, username, password)
            elif credential_type == 'ssh_key':
                return self._test_ssh_key(server_url, ssh_private_key, email)
            elif credential_type == 'oauth':
                return self._test_oauth(platform, server_url, password)
            else:
                return False, f"不支持的认证类型: {credential_type}"
                
        except Exception as e:
            logger.error(f"测试Git凭据时发生错误: {str(e)}")
            return False, f"测试失败: {str(e)}"
    
    def _test_username_password(self, server_url: str, username: str, password: str) -> Tuple[bool, str]:
        """测试用户名密码认证"""
        if not all([server_url, username, password]):
            return False, "用户名、密码或服务器URL不能为空"
        
        # 构造认证URL
        parsed_url = urlparse(server_url)
        if parsed_url.netloc:
            # 使用HTTPS进行简单的认证测试
            auth_url = f"https://{username}:{password}@{parsed_url.netloc}"
            test_repo_url = f"{auth_url}/test.git"  # 虚拟的测试仓库
            
            return self._test_git_ls_remote(test_repo_url, username, password)
        else:
            return False, "无效的服务器URL"
    
    def _test_access_token(self, platform: str, server_url: str, username: str, token: str) -> Tuple[bool, str]:
        """测试访问令牌认证"""
        if not all([server_url, token]):
            return False, "访问令牌或服务器URL不能为空"
        
        # 根据平台进行API测试
        if platform.lower() == 'github':
            return self._test_github_token(token)
        elif platform.lower() == 'gitlab':
            return self._test_gitlab_token(server_url, token)
        elif platform.lower() == 'gitee':
            return self._test_gitee_token(token)
        else:
            # 通用测试方法：尝试使用token访问API
            return self._test_generic_token(server_url, username, token)
    
    def _test_ssh_key(self, server_url: str, private_key: str, email: str = None) -> Tuple[bool, str]:
        """测试SSH密钥认证"""
        if not all([server_url, private_key]):
            return False, "SSH私钥或服务器URL不能为空"
        
        try:
            # 创建临时目录
            self.temp_dir = tempfile.mkdtemp()
            
            # 写入SSH私钥到临时文件
            ssh_key_path = os.path.join(self.temp_dir, 'id_rsa')
            with open(ssh_key_path, 'w') as f:
                f.write(private_key)
            os.chmod(ssh_key_path, 0o600)
            
            # 提取主机名
            parsed_url = urlparse(server_url)
            if parsed_url.netloc:
                hostname = parsed_url.netloc
            else:
                # 处理git@github.com:user/repo.git格式
                if '@' in server_url and ':' in server_url:
                    hostname = server_url.split('@')[1].split(':')[0]
                else:
                    return False, "无法解析服务器主机名"
            
            # 测试SSH连接
            ssh_command = [
                'ssh',
                '-i', ssh_key_path,
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=10',
                '-T',
                f'git@{hostname}'
            ]
            
            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            # SSH连接成功的标志（即使返回非0状态码）
            if result.returncode == 1 and ('successfully authenticated' in result.stderr.lower() or 
                                          'welcome' in result.stderr.lower() or
                                          'hi ' in result.stderr.lower()):
                return True, "SSH密钥认证成功"
            elif result.returncode == 255:
                return False, f"SSH连接失败: {result.stderr}"
            else:
                # 对于某些Git服务，即使认证成功也会返回错误码
                return True, "SSH密钥可能有效，但无法完全验证"
                
        except subprocess.TimeoutExpired:
            return False, "SSH连接超时"
        except Exception as e:
            return False, f"SSH测试失败: {str(e)}"
        finally:
            # 清理临时文件
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
    
    def _test_oauth(self, platform: str, server_url: str, oauth_token: str) -> Tuple[bool, str]:
        """测试OAuth令牌认证"""
        # OAuth测试通常与access_token类似
        return self._test_access_token(platform, server_url, None, oauth_token)
    
    def _test_github_token(self, token: str) -> Tuple[bool, str]:
        """测试GitHub访问令牌"""
        try:
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(
                'https://api.github.com/user',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return True, f"GitHub认证成功，用户: {user_data.get('login', 'Unknown')}"
            elif response.status_code == 401:
                return False, "GitHub Token无效或已过期"
            else:
                return False, f"GitHub API请求失败: {response.status_code}"
                
        except requests.RequestException as e:
            return False, f"GitHub API请求失败: {str(e)}"
    
    def _test_gitlab_token(self, server_url: str, token: str) -> Tuple[bool, str]:
        """测试GitLab访问令牌"""
        try:
            # 构造GitLab API URL
            parsed_url = urlparse(server_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            api_url = f"{base_url}/api/v4/user"
            
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                return True, f"GitLab认证成功，用户: {user_data.get('username', 'Unknown')}"
            elif response.status_code == 401:
                return False, "GitLab Token无效或已过期"
            else:
                return False, f"GitLab API请求失败: {response.status_code}"
                
        except requests.RequestException as e:
            return False, f"GitLab API请求失败: {str(e)}"
    
    def _test_gitee_token(self, token: str) -> Tuple[bool, str]:
        """测试Gitee访问令牌"""
        try:
            response = requests.get(
                f'https://gitee.com/api/v5/user?access_token={token}',
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return True, f"Gitee认证成功，用户: {user_data.get('login', 'Unknown')}"
            elif response.status_code == 401:
                return False, "Gitee Token无效或已过期"
            else:
                return False, f"Gitee API请求失败: {response.status_code}"
                
        except requests.RequestException as e:
            return False, f"Gitee API请求失败: {str(e)}"
    
    def _test_generic_token(self, server_url: str, username: str, token: str) -> Tuple[bool, str]:
        """通用令牌测试方法"""
        try:
            # 尝试使用token作为密码进行Git操作测试
            parsed_url = urlparse(server_url)
            if parsed_url.netloc:
                # 构造带认证的URL
                test_url = f"https://{username or 'token'}:{token}@{parsed_url.netloc}"
                return self._test_git_ls_remote(f"{test_url}/test.git", username, token)
            else:
                return False, "无效的服务器URL"
                
        except Exception as e:
            return False, f"通用令牌测试失败: {str(e)}"
    
    def _test_git_ls_remote(self, repo_url: str, username: str = None, password: str = None) -> Tuple[bool, str]:
        """使用git ls-remote测试仓库访问"""
        try:
            # 设置环境变量以避免交互式密码输入
            env = os.environ.copy()
            if username and password:
                env['GIT_USERNAME'] = username
                env['GIT_PASSWORD'] = password
            
            # 使用git ls-remote测试（这是一个只读操作）
            cmd = ['git', 'ls-remote', '--exit-code', repo_url]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                env=env
            )
            
            # 如果命令执行成功（返回码为0）或者只是找不到仓库（返回码为2）
            if result.returncode == 0:
                return True, "Git认证成功，可以访问仓库"
            elif result.returncode == 2:
                return True, "Git认证成功，但测试仓库不存在（这是正常的）"
            elif result.returncode == 128:
                if 'authentication failed' in result.stderr.lower():
                    return False, "Git认证失败：用户名或密码错误"
                elif 'repository not found' in result.stderr.lower():
                    return True, "Git认证成功，但测试仓库不存在（这是正常的）"
                else:
                    return False, f"Git操作失败: {result.stderr}"
            else:
                return False, f"Git测试失败: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Git操作超时"
        except FileNotFoundError:
            return False, "系统中未找到git命令，请确保已安装Git"
        except Exception as e:
            return False, f"Git测试失败: {str(e)}"


def main():
    """测试脚本主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Git凭据连接测试工具')
    parser.add_argument('--platform', required=True, choices=['github', 'gitlab', 'gitee', 'bitbucket', 'other'],
                       help='Git平台类型')
    parser.add_argument('--server-url', required=True, help='Git服务器URL')
    parser.add_argument('--credential-type', required=True, 
                       choices=['username_password', 'access_token', 'ssh_key', 'oauth'],
                       help='认证类型')
    parser.add_argument('--username', help='用户名')
    parser.add_argument('--password', help='密码或Token')
    parser.add_argument('--ssh-key-file', help='SSH私钥文件路径')
    parser.add_argument('--email', help='邮箱地址')
    
    args = parser.parse_args()
    
    # 读取SSH私钥
    ssh_private_key = None
    if args.ssh_key_file:
        try:
            with open(args.ssh_key_file, 'r') as f:
                ssh_private_key = f.read()
        except Exception as e:
            print(f"读取SSH私钥文件失败: {e}")
            return
    
    # 创建测试器
    tester = GitCredentialTester()
    
    # 执行测试
    success, message = tester.test_credential(
        platform=args.platform,
        server_url=args.server_url,
        credential_type=args.credential_type,
        username=args.username,
        password=args.password,
        ssh_private_key=ssh_private_key,
        email=args.email
    )
    
    if success:
        print(f"✅ 测试成功: {message}")
    else:
        print(f"❌ 测试失败: {message}")


if __name__ == '__main__':
    main()
