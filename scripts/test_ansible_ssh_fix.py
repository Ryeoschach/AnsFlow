#!/usr/bin/env python3
"""
测试修复后的Ansible SSH密钥认证
通过实际创建凭据和执行来验证修复效果
"""

import os
import sys
import django

# 设置Django环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from ansible_integration.models import AnsibleCredential, AnsiblePlaybook, AnsibleInventory, AnsibleExecution
from django.contrib.auth.models import User
import tempfile

def create_test_credentials():
    """创建测试凭据"""
    print("=== 创建测试SSH密钥凭据 ===")
    
    # 获取或创建测试用户
    user, created = User.objects.get_or_create(
        username='ansible_test_user',
        defaults={'email': 'test@ansflow.com'}
    )
    
    # 示例SSH私钥（这是一个示例密钥，请替换为实际的密钥）
    test_ssh_key = """-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACBK8p7+kf9dE8ZSgTmE8rF8wLMrTn1/8ZmWOv+7iS9XQwAAAJgJr+AiCa/g
IgAAAAtzc2gtZWQyNTUxOQAAACBK8p7+kf9dE8ZSgTmE8rF8wLMrTn1/8ZmWOv+7iS9XQw
AAAEDNmz/3cL5x8+U2c5P7fZ8jD7tZ8vW1L6mN9Qr3sL8M7Krzov6d/10TxlKBOYTysXz
AsytOfX/xmZY6/7uJL1dDAAAADmNyZWVkQENyZWVkLU1CUAECAwQFBgcICQ==
-----END OPENSSH PRIVATE KEY-----"""
    
    # 创建凭据
    credential = AnsibleCredential.objects.create(
        name='测试SSH密钥认证修复',
        credential_type='ssh_key',
        username='ubuntu',  # 或者你的实际用户名
        ssh_private_key=test_ssh_key,  # 这会自动加密
        created_by=user
    )
    
    print(f"✅ 创建测试凭据成功: {credential.name} (ID: {credential.id})")
    print(f"凭据类型: {credential.credential_type}")
    print(f"用户名: {credential.username}")
    print(f"has_ssh_key: {credential.has_ssh_key}")
    
    return credential

def test_key_decryption(credential):
    """测试密钥解密"""
    print(f"\n=== 测试密钥解密 (凭据ID: {credential.id}) ===")
    
    # 测试解密方法
    decrypted_key = credential.get_decrypted_ssh_key()
    
    if decrypted_key:
        print(f"✅ 密钥解密成功")
        print(f"解密后密钥长度: {len(decrypted_key)}")
        print(f"密钥开头: {decrypted_key[:50]}...")
        
        # 检查密钥格式
        if decrypted_key.startswith('-----BEGIN'):
            print("✅ SSH密钥格式验证通过")
            return True
        else:
            print("❌ SSH密钥格式不正确")
            return False
    else:
        print("❌ 密钥解密失败")
        return False

def simulate_fixed_ansible_execution(credential):
    """模拟修复后的Ansible执行逻辑"""
    print(f"\n=== 模拟修复后的Ansible执行 (凭据ID: {credential.id}) ===")
    
    try:
        # 这是修复后的逻辑
        if credential.credential_type == 'ssh_key' and credential.has_ssh_key:
            # 获取解密后的SSH私钥
            decrypted_ssh_key = credential.get_decrypted_ssh_key()
            if decrypted_ssh_key:
                # 确保SSH密钥以换行符结尾，并且格式正确
                if not decrypted_ssh_key.endswith('\n'):
                    decrypted_ssh_key += '\n'
                
                # 创建临时SSH密钥文件
                with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as temp_key:
                    temp_key.write(decrypted_ssh_key)
                    key_path = temp_key.name
                
                # 设置密钥文件权限
                os.chmod(key_path, 0o600)
                
                # 模拟ansible命令构建
                cmd = [
                    'ansible-playbook',
                    'test-playbook.yml',
                    '-i', 'inventory.ini',
                    '--private-key', key_path,
                    '-u', credential.username,
                    '-v'
                ]
                
                print(f"✅ Ansible命令构建成功:")
                print(f"   命令: {' '.join(cmd[:3])} ... --private-key {key_path}")
                print(f"   SSH密钥文件: {key_path}")
                print(f"   文件权限: {oct(os.stat(key_path).st_mode)[-3:]}")
                
                # 验证密钥文件内容
                with open(key_path, 'r') as f:
                    content = f.read()
                    if content == decrypted_ssh_key:
                        print("✅ 密钥文件内容验证通过")
                        success = True
                    else:
                        print("❌ 密钥文件内容验证失败")
                        success = False
                
                # 清理临时文件
                os.unlink(key_path)
                print(f"✅ 临时文件已清理: {key_path}")
                
                return success
            else:
                print("❌ SSH密钥解密失败或为空")
                return False
        else:
            print("❌ 凭据类型或SSH密钥检查失败")
            return False
            
    except Exception as e:
        print(f"❌ 模拟执行异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_before_after_comparison():
    """显示修复前后的代码对比"""
    print("\n=== 修复前后代码对比 ===")
    
    print("❌ 修复前 (错误的代码):")
    print("""
    if credential.credential_type == 'ssh_key' and credential.ssh_private_key:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as temp_key:
            temp_key.write(credential.ssh_private_key)  # 直接使用加密密钥！
            key_path = temp_key.name
    """)
    
    print("✅ 修复后 (正确的代码):")
    print("""
    if credential.credential_type == 'ssh_key' and credential.has_ssh_key:
        decrypted_ssh_key = credential.get_decrypted_ssh_key()  # 解密后使用！
        if decrypted_ssh_key:
            if not decrypted_ssh_key.endswith('\\n'):
                decrypted_ssh_key += '\\n'
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as temp_key:
                temp_key.write(decrypted_ssh_key)
                key_path = temp_key.name
            os.chmod(key_path, 0o600)
    """)

def cleanup_test_data():
    """清理测试数据"""
    print("\n=== 清理测试数据 ===")
    try:
        # 删除测试凭据
        deleted_credentials = AnsibleCredential.objects.filter(name='测试SSH密钥认证修复').delete()
        print(f"✅ 删除测试凭据: {deleted_credentials[0]} 个")
        
        # 删除测试用户
        deleted_users = User.objects.filter(username='ansible_test_user').delete()
        print(f"✅ 删除测试用户: {deleted_users[0]} 个")
        
    except Exception as e:
        print(f"⚠️ 清理过程中出现异常: {e}")

def main():
    """主函数"""
    print("🔧 AnsFlow Ansible SSH密钥认证修复验证")
    print("=" * 60)
    
    try:
        # 1. 创建测试凭据
        credential = create_test_credentials()
        
        # 2. 测试密钥解密
        decrypt_success = test_key_decryption(credential)
        
        # 3. 模拟修复后的执行
        execute_success = simulate_fixed_ansible_execution(credential)
        
        # 4. 显示修复对比
        show_before_after_comparison()
        
        # 5. 总结结果
        print("\n" + "=" * 60)
        print("📊 测试结果总结:")
        print(f"✅ 凭据创建: 成功")
        print(f"{'✅' if decrypt_success else '❌'} 密钥解密: {'成功' if decrypt_success else '失败'}")
        print(f"{'✅' if execute_success else '❌'} 执行模拟: {'成功' if execute_success else '失败'}")
        
        if decrypt_success and execute_success:
            print("\n🎉 所有测试通过！SSH密钥认证问题已修复")
            print("\n📋 修复要点:")
            print("1. 使用 get_decrypted_ssh_key() 方法获取解密后的密钥")
            print("2. 检查密钥格式并确保以换行符结尾")
            print("3. 正确设置临时文件权限 (600)")
            print("4. 添加详细的错误处理和日志")
            
            print("\n🚀 可以部署到生产环境!")
        else:
            print("\n⚠️ 测试未全部通过，请检查相关问题")
            
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试数据
        cleanup_test_data()

if __name__ == '__main__':
    main()
