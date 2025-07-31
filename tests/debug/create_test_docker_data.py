#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker注册表数据创建脚本
用于在数据库中创建测试用的Docker注册表数据
"""

import os
import sys
import django

# 添加Django项目路径
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')

# 配置Django
django.setup()

from docker_management.models import DockerRegistry, DockerRegistryProject
from django.contrib.auth.models import User

def create_test_registries():
    """创建测试用的Docker注册表"""
    
    print("🐳 开始创建测试Docker注册表数据...")
    
    # 获取或创建一个用户
    try:
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            print(f"✅ 创建测试用户: {user.username}")
        else:
            print(f"ℹ️ 使用现有用户: {user.username}")
    except Exception as e:
        print(f"❌ 用户创建失败: {e}")
        return
    
    # 创建测试注册表数据
    test_registries = [
        {
            'name': 'Docker Hub',
            'url': 'https://registry-1.docker.io',
            'registry_type': 'dockerhub',
            'username': '',
            'description': '官方Docker Hub注册表',
            'is_default': True,
            'created_by': user,
            'auth_config': {}
        },
        {
            'name': '私有注册表',
            'url': 'https://registry.example.com',
            'registry_type': 'private',
            'username': 'admin',
            'description': '私有Docker注册表',
            'is_default': False,
            'created_by': user,
            'auth_config': {
                'username': 'admin',
                'password': 'password123'
            }
        },
        {
            'name': 'Harbor注册表',
            'url': 'https://harbor.company.com',
            'registry_type': 'harbor',
            'username': 'harbor_user',
            'description': '企业级Harbor注册表',
            'is_default': False,
            'created_by': user,
            'auth_config': {
                'username': 'harbor_user',
                'password': 'harbor_pass'
            }
        },
        {
            'name': 'AWS ECR',
            'url': 'https://123456789012.dkr.ecr.us-west-2.amazonaws.com',
            'registry_type': 'ecr',
            'username': 'AWS',
            'description': 'Amazon Elastic Container Registry',
            'is_default': False,
            'created_by': user,
            'auth_config': {
                'aws_access_key_id': 'AKIAIOSFODNN7EXAMPLE',
                'aws_secret_access_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
                'aws_region': 'us-west-2'
            }
        }
    ]
    
    created_registries = []
    
    for registry_data in test_registries:
        try:
            # 检查是否已存在
            existing = DockerRegistry.objects.filter(name=registry_data['name']).first()
            if existing:
                print(f"ℹ️ 注册表已存在: {registry_data['name']}")
                created_registries.append(existing)
                continue
            
            # 创建新注册表
            registry = DockerRegistry.objects.create(**registry_data)
            created_registries.append(registry)
            print(f"✅ 创建注册表: {registry.name} ({registry.registry_type})")
            
        except Exception as e:
            print(f"❌ 创建注册表失败 {registry_data['name']}: {e}")
    
    return created_registries

def create_test_projects(registries):
    """为注册表创建测试项目"""
    
    print("\n📦 开始创建测试Docker项目...")
    
    if not registries:
        print("❌ 没有可用的注册表，无法创建项目")
        return
    
    # 获取用户
    user = User.objects.first()
    
    test_projects = [
        {
            'name': 'my-web-app',
            'description': '前端Web应用项目',
            'visibility': 'public',
            'tags': ['web', 'frontend', 'react']
        },
        {
            'name': 'api-server',
            'description': '后端API服务项目',
            'visibility': 'private',
            'tags': ['api', 'backend', 'django']
        },
        {
            'name': 'database',
            'description': '数据库服务项目',
            'visibility': 'private',
            'tags': ['database', 'postgresql']
        },
        {
            'name': 'nginx-proxy',
            'description': 'Nginx反向代理项目',
            'visibility': 'public',
            'tags': ['proxy', 'nginx']
        }
    ]
    
    created_projects = []
    
    for registry in registries[:2]:  # 只在前两个注册表中创建项目
        for project_data in test_projects:
            try:
                # 检查是否已存在
                existing = DockerRegistryProject.objects.filter(
                    name=project_data['name'],
                    registry=registry
                ).first()
                
                if existing:
                    print(f"ℹ️ 项目已存在: {registry.name}/{project_data['name']}")
                    created_projects.append(existing)
                    continue
                
                # 创建新项目
                project = DockerRegistryProject.objects.create(
                    name=project_data['name'],
                    registry=registry,
                    description=project_data['description'],
                    visibility=project_data['visibility'],
                    tags=project_data['tags'],
                    is_default=False,
                    config={
                        'auto_build': True,
                        'webhook_enabled': False
                    },
                    image_count=0,
                    created_by=user
                )
                created_projects.append(project)
                print(f"✅ 创建项目: {registry.name}/{project.name}")
                
            except Exception as e:
                print(f"❌ 创建项目失败 {registry.name}/{project_data['name']}: {e}")
    
    return created_projects

def show_summary():
    """显示创建结果汇总"""
    
    print("\n📊 数据创建汇总:")
    print("=" * 50)
    
    # 统计注册表
    total_registries = DockerRegistry.objects.count()
    print(f"📋 注册表总数: {total_registries}")
    
    for registry in DockerRegistry.objects.all():
        project_count = DockerRegistryProject.objects.filter(registry=registry).count()
        status_icon = "🟢" if registry.is_default else "🔵"
        print(f"  {status_icon} {registry.name} ({registry.registry_type}) - {project_count} 项目")
    
    # 统计项目
    total_projects = DockerRegistryProject.objects.count()
    print(f"\n📦 项目总数: {total_projects}")
    
    for project in DockerRegistryProject.objects.all():
        visibility_icon = "🔓" if project.visibility == 'public' else "🔒"
        print(f"  {visibility_icon} {project.registry.name}/{project.name} ({project.visibility})")
    
    print("\n✅ 测试数据创建完成！")
    print("💡 现在可以在前端页面中看到注册表和项目数据了")

def main():
    """主函数"""
    
    print("🚀 AnsFlow Docker注册表测试数据创建工具")
    print("=" * 60)
    
    try:
        # 创建注册表
        registries = create_test_registries()
        
        # 创建项目
        projects = create_test_projects(registries)
        
        # 显示汇总
        show_summary()
        
        return True
        
    except Exception as e:
        print(f"❌ 创建过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 测试数据创建成功！可以刷新前端页面查看效果。")
        sys.exit(0)
    else:
        print("\n💥 测试数据创建失败！请检查错误信息。")
        sys.exit(1)
