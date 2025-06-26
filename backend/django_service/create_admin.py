#!/usr/bin/env python3
"""
创建管理员用户脚本
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from django.contrib.auth.models import User

def create_admin_user():
    """创建管理员用户"""
    username = "admin"
    email = "admin@ansflow.local"
    password = "admin123"
    
    try:
        # 检查用户是否已存在
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()
            print(f"✅ 更新用户密码成功: {username}")
        else:
            # 创建新用户
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            print(f"✅ 创建管理员用户成功: {username}")
        
        print(f"📧 邮箱: {email}")
        print(f"🔑 密码: {password}")
        print(f"🌐 前端地址: http://localhost:3002")
        print(f"🔗 管理后台: http://localhost:8000/admin/")
        
    except Exception as e:
        print(f"❌ 创建用户失败: {e}")

if __name__ == "__main__":
    create_admin_user()
