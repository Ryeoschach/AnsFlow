"""
Git认证凭据管理API视图
"""
import subprocess
import tempfile
import os
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from ..models import GitCredential
from ..serializers import GitCredentialSerializer, GitCredentialListSerializer


class GitCredentialViewSet(viewsets.ModelViewSet):
    """Git认证凭据ViewSet"""
    queryset = GitCredential.objects.all()
    serializer_class = GitCredentialSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """只返回当前用户的凭据"""
        return GitCredential.objects.filter(created_by=self.request.user)
    
    def get_serializer_class(self):
        """根据action选择不同的序列化器"""
        if self.action == 'list':
            return GitCredentialListSerializer
        return GitCredentialSerializer
    
    def perform_create(self, serializer):
        """创建时设置创建者"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """测试Git连接"""
        credential = self.get_object()
        
        try:
            # 使用GitCredentialTester进行测试
            from ..git_credential_tester import GitCredentialTester
            
            tester = GitCredentialTester()
            success = False
            message = "连接失败"
            
            if credential.credential_type == 'username_password':
                password = credential.decrypt_password()
                if not password:
                    message = "密码解密失败"
                else:
                    success, message = tester.test_credential(
                        platform=credential.platform,
                        server_url=credential.server_url,
                        credential_type='username_password',
                        username=credential.username,
                        password=password
                    )
                    
            elif credential.credential_type == 'access_token':
                token = credential.decrypt_password()
                if not token:
                    message = "访问令牌解密失败"
                else:
                    success, message = tester.test_credential(
                        platform=credential.platform,
                        server_url=credential.server_url,
                        credential_type='access_token',
                        username=credential.username,
                        password=token
                    )
                    
            elif credential.credential_type == 'ssh_key':
                private_key = credential.decrypt_ssh_key()
                if not private_key:
                    message = "SSH私钥解密失败"
                else:
                    success, message = tester.test_credential(
                        platform=credential.platform,
                        server_url=credential.server_url,
                        credential_type='ssh_key',
                        ssh_private_key=private_key,
                        email=credential.username
                    )
            else:
                message = f"不支持的认证类型: {credential.credential_type}"
            
            # 更新测试结果
            credential.last_test_at = timezone.now()
            credential.last_test_result = success
            credential.save()
            
            return Response({
                'success': success,
                'message': message,
                'tested_at': credential.last_test_at,
                'platform': credential.platform,
                'credential_type': credential.credential_type
            })
            
        except Exception as e:
            # 更新测试结果
            credential.last_test_at = timezone.now()
            credential.last_test_result = False
            credential.save()
            
            error_message = f'测试失败: {str(e)}'
            print(f"Git credential test error: {error_message}")
            
            return Response({
                'success': False,
                'message': error_message,
                'tested_at': credential.last_test_at,
                'platform': credential.platform,
                'credential_type': credential.credential_type
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _test_git_connection(self, credential):
        """实际的Git连接测试"""
        try:
            # 使用GitCredentialTester进行更准确的测试
            from ..git_credential_tester import GitCredentialTester
            
            tester = GitCredentialTester()
            
            if credential.credential_type == 'username_password':
                password = credential.decrypt_password()
                if not password:
                    return False
                
                success, message = tester.test_credential(
                    platform=credential.platform,
                    server_url=credential.server_url,
                    credential_type='username_password',
                    username=credential.username,
                    password=password
                )
                
                # 记录详细日志
                if success:
                    print(f"Git connection test successful: {message}")
                else:
                    print(f"Git connection test failed: {message}")
                
                return success
                
            elif credential.credential_type == 'access_token':
                token = credential.decrypt_password()
                if not token:
                    return False
                
                success, message = tester.test_credential(
                    platform=credential.platform,
                    server_url=credential.server_url,
                    credential_type='access_token',
                    username=credential.username,
                    password=token
                )
                
                # 记录详细日志
                if success:
                    print(f"Access token test successful: {message}")
                else:
                    print(f"Access token test failed: {message}")
                
                return success
                
            elif credential.credential_type == 'ssh_key':
                private_key = credential.decrypt_ssh_key()
                if not private_key:
                    return False
                
                success, message = tester.test_credential(
                    platform=credential.platform,
                    server_url=credential.server_url,
                    credential_type='ssh_key',
                    ssh_private_key=private_key,
                    email=credential.username  # 使用username字段作为email
                )
                
                # 记录详细日志
                if success:
                    print(f"SSH key test successful: {message}")
                else:
                    print(f"SSH key test failed: {message}")
                
                return success
            else:
                return False
        except Exception as e:
            print(f"Git connection test failed: {e}")
            return False
    
    def _test_username_password_connection(self, credential):
        """测试用户名密码认证"""
        try:
            password = credential.decrypt_password()
            if not password:
                return False
            
            # 构造带认证的URL
            server_url = credential.server_url.rstrip('/')
            if server_url.startswith('https://'):
                auth_url = f"https://{credential.username}:{password}@{server_url[8:]}"
            elif server_url.startswith('http://'):
                auth_url = f"http://{credential.username}:{password}@{server_url[7:]}"
            else:
                return False
            
            # 使用git ls-remote测试连接
            cmd = ['git', 'ls-remote', '--exit-code', auth_url]
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Username/password test failed: {e}")
            return False
    
    def _test_access_token_connection(self, credential):
        """测试访问令牌认证"""
        try:
            token = credential.decrypt_password()
            if not token:
                return False
            
            # 对于不同平台使用不同的token认证方式
            server_url = credential.server_url.rstrip('/')
            
            if credential.platform == 'github':
                # GitHub使用token作为用户名，密码为空
                if server_url.startswith('https://'):
                    auth_url = f"https://{token}@{server_url[8:]}"
                else:
                    auth_url = f"https://{token}@github.com"
            elif credential.platform == 'gitlab':
                # GitLab使用oauth2作为用户名，token作为密码
                if server_url.startswith('https://'):
                    auth_url = f"https://oauth2:{token}@{server_url[8:]}"
                else:
                    return False
            else:
                # 通用方式：使用token作为用户名
                if server_url.startswith('https://'):
                    auth_url = f"https://{token}@{server_url[8:]}"
                else:
                    return False
            
            cmd = ['git', 'ls-remote', '--exit-code', auth_url]
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Access token test failed: {e}")
            return False
    
    def _test_ssh_key_connection(self, credential):
        """测试SSH密钥认证"""
        try:
            private_key = credential.decrypt_ssh_key()
            if not private_key:
                return False
            
            # 创建临时SSH密钥文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as key_file:
                key_file.write(private_key)
                key_file_path = key_file.name
            
            try:
                # 设置密钥文件权限
                os.chmod(key_file_path, 0o600)
                
                # 构造SSH URL
                server_url = credential.server_url.rstrip('/')
                if server_url.startswith('https://'):
                    # 将HTTPS URL转换为SSH URL
                    domain = server_url[8:]
                    if credential.platform == 'github':
                        ssh_url = f"git@github.com"
                    elif credential.platform == 'gitlab':
                        ssh_url = f"git@{domain}"
                    else:
                        ssh_url = f"git@{domain}"
                elif server_url.startswith('ssh://'):
                    ssh_url = server_url[6:]
                else:
                    ssh_url = server_url
                
                # 使用ssh-keyscan测试连接
                cmd = ['ssh', '-i', key_file_path, '-o', 'StrictHostKeyChecking=no', 
                       '-o', 'ConnectTimeout=10', ssh_url.split('@')[1], 'exit']
                result = subprocess.run(cmd, capture_output=True, timeout=15)
                
                # SSH连接测试，returncode为255通常表示SSH连接成功但命令执行失败（正常）
                return result.returncode in [0, 255]
                
            finally:
                # 清理临时文件
                if os.path.exists(key_file_path):
                    os.unlink(key_file_path)
                    
        except Exception as e:
            print(f"SSH key test failed: {e}")
            return False
