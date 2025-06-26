#!/usr/bin/env python3
"""
创建测试用户脚本
非交互式创建管理员用户用于前端登录测试
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from django.contrib.auth.models import User

def create_test_user():
    """创建测试用户"""
    username = 'admin'
    password = 'admin123'
    email = 'admin@example.com'
    
    try:
        # 检查用户是否已存在
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            # 更新密码
            user.set_password(password)
            user.save()
            print(f"✅ 用户 '{username}' 已存在，密码已更新")
        else:
            # 创建新用户
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            print(f"✅ 超级用户 '{username}' 创建成功")
        
        print(f"📝 登录凭据:")
        print(f"   用户名: {username}")
        print(f"   密码: {password}")
        print(f"🌐 前端地址: http://localhost:3000")
        print(f"🔐 Django管理界面: http://localhost:8000/admin/")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建用户失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 创建AnsFlow测试用户")
    print("="*40)
    
    success = create_test_user()
    
    if success:
        print("\n🎉 用户创建完成！您现在可以:")
        print("1. 访问 http://localhost:3000 登录前端")
        print("2. 使用用户名: admin, 密码: admin123")
        print("3. 查看实时监控功能")
    else:
        print("\n⚠️ 用户创建失败，请检查Django配置")
