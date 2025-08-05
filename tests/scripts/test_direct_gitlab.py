#!/usr/bin/env python3
"""
直接测试GitLab凭据连接
绕过Django服务器，直接调用GitCredentialTester
"""

import sys
import os
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from cicd_integrations.git_credential_tester import GitCredentialTester
from cicd_integrations.models import GitCredential

def test_gitlab_directly():
    print("🔧 直接测试GitLab凭据连接")
    print("=" * 50)
    
    # 获取GitLab凭据
    try:
        gitlab_creds = GitCredential.objects.filter(platform='gitlab')
        if not gitlab_creds.exists():
            print("❌ 未找到GitLab凭据")
            return False
        
        for cred in gitlab_creds:
            print(f"\n🔍 测试凭据: {cred.name}")
            print(f"   服务器: {cred.server_url}")
            print(f"   用户名: {cred.username}")
            
            # 解密密码
            password = cred.decrypt_password()
            if not password:
                print("❌ 密码解密失败")
                continue
            
            print("✅ 密码解密成功")
            
            # 直接调用GitCredentialTester
            tester = GitCredentialTester()
            success, message = tester.test_credential(
                platform='gitlab',
                server_url=cred.server_url,
                credential_type='username_password',
                username=cred.username,
                password=password
            )
            
            if success:
                print(f"✅ 连接成功: {message}")
            else:
                print(f"❌ 连接失败: {message}")
            
            return success
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

if __name__ == '__main__':
    test_gitlab_directly()
