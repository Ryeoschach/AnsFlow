#!/usr/bin/env python3
"""
重新加密Git凭据密码的脚本
解决密码解密失败的问题

使用方法:
python scripts/reencrypt_git_credentials.py
"""

import os
import sys
import django

# 设置Django环境
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from cicd_integrations.models import GitCredential
import getpass

def main():
    print("🔧 Git凭据密码重新加密工具")
    print("=" * 50)
    
    # 获取所有Git凭据
    credentials = GitCredential.objects.all()
    print(f"找到 {credentials.count()} 个Git凭据")
    
    for credential in credentials:
        print(f"\n🔍 处理凭据: {credential.name} ({credential.platform})")
        print(f"   认证类型: {credential.credential_type}")
        print(f"   用户名: {credential.username}")
        print(f"   服务器: {credential.server_url}")
        
        # 尝试解密现有密码
        try:
            existing_password = credential.decrypt_password()
            if existing_password:
                print("✅ 密码解密成功，无需重新加密")
                continue
            else:
                print("❌ 密码解密失败 (返回空值)")
        except Exception as e:
            print(f"❌ 密码解密失败: {e}")
        
        # 需要重新输入密码
        print("请重新输入密码进行重新加密...")
        
        if credential.credential_type == 'username_password':
            new_password = getpass.getpass(f"请输入 {credential.username} 的密码: ")
        elif credential.credential_type == 'access_token':
            new_password = getpass.getpass(f"请输入 {credential.username} 的访问令牌: ")
        else:
            print(f"⚠️ 暂不支持重新加密认证类型: {credential.credential_type}")
            continue
        
        if not new_password:
            print("❌ 密码为空，跳过此凭据")
            continue
        
        # 重新加密并保存
        try:
            credential.encrypt_password(new_password)
            credential.save()
            print("✅ 密码重新加密成功")
            
            # 验证解密
            decrypted = credential.decrypt_password()
            if decrypted == new_password:
                print("✅ 解密验证成功")
            else:
                print("❌ 解密验证失败")
                
        except Exception as e:
            print(f"❌ 重新加密失败: {e}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ 操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 程序异常: {str(e)}")
        sys.exit(1)
