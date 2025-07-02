#!/usr/bin/env python3
"""
Git凭据加密密钥修复脚本
解决凭据解密失败的问题

使用方法:
python scripts/fix_git_credential_encryption.py
"""

import os
import sys
import django
from cryptography.fernet import Fernet

# 设置Django环境
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from cicd_integrations.models import GitCredential
from django.conf import settings

def generate_encryption_key():
    """生成新的加密密钥"""
    key = Fernet.generate_key()
    print(f"生成的加密密钥: {key.decode()}")
    return key

def check_current_credentials():
    """检查当前凭据状态"""
    print("🔍 检查当前Git凭据...")
    
    credentials = GitCredential.objects.all()
    print(f"发现 {credentials.count()} 个Git凭据")
    
    for cred in credentials:
        print(f"\n凭据: {cred.name}")
        print(f"  平台: {cred.platform}")
        print(f"  类型: {cred.credential_type}")
        print(f"  用户名: {cred.username}")
        print(f"  有加密密码: {'是' if cred.password_encrypted else '否'}")
        
        # 尝试解密
        try:
            decrypted = cred.decrypt_password()
            if decrypted:
                print(f"  解密状态: ✅ 成功")
            else:
                print(f"  解密状态: ❌ 失败（返回None）")
        except Exception as e:
            print(f"  解密状态: ❌ 失败（异常: {e}）")

def fix_encryption_key():
    """修复加密密钥"""
    print("\n🔧 修复加密密钥...")
    
    # 检查是否已经设置了密钥
    existing_key = getattr(settings, 'GIT_CREDENTIAL_ENCRYPTION_KEY', None)
    if existing_key:
        print(f"已存在加密密钥: {existing_key[:20]}...")
    else:
        print("未设置加密密钥")
    
    # 生成新密钥
    new_key = generate_encryption_key()
    
    # 更新设置文件
    settings_file = '/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service/ansflow/settings.py'
    
    print(f"\n📝 建议在设置文件中添加以下配置:")
    print(f"文件: {settings_file}")
    print("添加内容:")
    print(f"# Git凭据加密密钥")
    print(f"GIT_CREDENTIAL_ENCRYPTION_KEY = '{new_key.decode()}'")
    
    return new_key

def reset_credentials_with_new_key(key):
    """使用新密钥重新设置凭据"""
    print("\n🔄 重新设置凭据...")
    
    # 临时设置新密钥
    settings.GIT_CREDENTIAL_ENCRYPTION_KEY = key.decode()
    
    # 获取所有凭据
    credentials = GitCredential.objects.all()
    
    for cred in credentials:
        print(f"\n处理凭据: {cred.name}")
        
        # 清空现有的加密密码
        cred.password_encrypted = ""
        
        # 提示用户重新输入密码
        if cred.credential_type == 'username_password':
            print(f"请为 {cred.name} 重新输入密码:")
            print(f"  平台: {cred.platform}")
            print(f"  用户名: {cred.username}")
            
            import getpass
            new_password = getpass.getpass("密码: ")
            if new_password:
                cred.encrypt_password(new_password)
                cred.save()
                print("✅ 密码已重新加密保存")
            else:
                print("❌ 未输入密码，跳过")
                
        elif cred.credential_type == 'access_token':
            print(f"请为 {cred.name} 重新输入访问令牌:")
            print(f"  平台: {cred.platform}")
            print(f"  用户名: {cred.username}")
            
            import getpass
            new_token = getpass.getpass("访问令牌: ")
            if new_token:
                cred.encrypt_password(new_token)
                cred.save()
                print("✅ 访问令牌已重新加密保存")
            else:
                print("❌ 未输入访问令牌，跳过")

def verify_fix():
    """验证修复"""
    print("\n✅ 验证修复结果...")
    
    credentials = GitCredential.objects.all()
    success_count = 0
    
    for cred in credentials:
        try:
            decrypted = cred.decrypt_password()
            if decrypted:
                print(f"✅ {cred.name}: 解密成功")
                success_count += 1
            else:
                print(f"❌ {cred.name}: 解密失败（返回None）")
        except Exception as e:
            print(f"❌ {cred.name}: 解密失败（{e}）")
    
    print(f"\n📊 修复结果: {success_count}/{credentials.count()} 个凭据解密成功")
    return success_count == credentials.count()

def main():
    print("🔧 AnsFlow Git凭据加密密钥修复工具")
    print("=" * 60)
    
    # 1. 检查当前状态
    check_current_credentials()
    
    # 2. 生成新的加密密钥
    new_key = fix_encryption_key()
    
    print("\n⚠️ 重要提示:")
    print("1. 请先将上面的加密密钥添加到Django设置文件中")
    print("2. 重启Django服务器")
    print("3. 然后重新运行此脚本进行凭据重设")
    
    choice = input("\n是否继续重新设置凭据? (y/N): ").strip().lower()
    if choice == 'y':
        # 3. 重新设置凭据
        reset_credentials_with_new_key(new_key)
        
        # 4. 验证修复
        if verify_fix():
            print("\n🎉 修复完成！所有Git凭据都能正常解密")
        else:
            print("\n❌ 修复未完全成功，请检查输入的凭据")
    else:
        print("\n📋 请手动完成以下步骤:")
        print("1. 将加密密钥添加到settings.py")
        print("2. 重启Django服务器")
        print("3. 在AnsFlow界面中重新编辑并保存Git凭据")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ 修复已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 程序异常: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
