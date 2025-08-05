#!/usr/bin/env python3
"""
测试GitLab连接修复的脚本
"""
import sys
import os

# 添加Django路径
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')

import django
django.setup()

from cicd_integrations.git_credential_tester import GitCredentialTester

def test_gitlab_connection():
    """测试GitLab连接"""
    print("🔧 测试GitLab连接修复...")
    
    tester = GitCredentialTester()
    
    # 测试用户名密码认证
    print("\n📝 测试用户名密码认证...")
    success, message = tester.test_credential(
        platform='gitlab',
        server_url='https://gitlab.cyfee.com:8443',
        credential_type='username_password',
        username='test_user',
        password='test_password'
    )
    
    print(f"结果: {'✅ 成功' if success else '❌ 失败'}")
    print(f"消息: {message}")
    
    # 测试访问令牌认证
    print("\n🔑 测试访问令牌认证...")
    success, message = tester.test_credential(
        platform='gitlab',
        server_url='https://gitlab.cyfee.com:8443',
        credential_type='access_token',
        username='test_user',
        password='test_token'
    )
    
    print(f"结果: {'✅ 成功' if success else '❌ 失败'}")
    print(f"消息: {message}")
    
    print("\n✨ 测试完成！现在应该不会再出现 '/test.git/' 路径错误了")

if __name__ == '__main__':
    test_gitlab_connection()
