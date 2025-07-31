#!/usr/bin/env python3
"""
检查项目ID 4的配置
"""

import os
import sys
import django

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from docker_integration.models import DockerRegistryProject, DockerRegistry

def check_project_config():
    """检查项目配置"""
    print("=== 检查项目配置 ===")
    
    try:
        # 查找项目ID 4
        try:
            proj = DockerRegistryProject.objects.get(id=4)
            print(f"✅ 找到项目 ID: 4")
            print(f"   名称: {proj.name}")
            print(f"   注册表ID: {proj.registry}")
            print(f"   描述: {proj.description}")
            
            # 查找对应的注册表
            try:
                registry = DockerRegistry.objects.get(id=proj.registry)
                print(f"   对应注册表: {registry.name} ({registry.url})")
            except DockerRegistry.DoesNotExist:
                print(f"   ❌ 未找到对应的注册表ID: {proj.registry}")
                
        except DockerRegistryProject.DoesNotExist:
            print("❌ 未找到项目 ID: 4")
            
            # 列出所有可用的项目
            print("\n📋 所有可用的项目:")
            projects = DockerRegistryProject.objects.all()
            for proj in projects:
                print(f"   ID: {proj.id}, 名称: {proj.name}, 注册表ID: {proj.registry}")
                
    except Exception as e:
        print(f"❌ 查询失败: {e}")

if __name__ == '__main__':
    check_project_config()
