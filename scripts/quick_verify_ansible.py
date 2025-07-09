#!/usr/bin/env python3
"""
Ansible 深度集成功能快速验证脚本

用途：快速验证新增的 Ansible 功能是否正常工作
使用方法：
    cd /Users/creed/Workspace/OpenSource/ansflow/backend/django_service
    uv run python ../../scripts/quick_verify_ansible.py
"""

import requests
import json
import sys

def quick_verify():
    """快速验证 Ansible 功能"""
    print("🔍 Ansible 深度集成功能快速验证")
    print("=" * 50)
    
    base_url = 'http://localhost:8000/api/v1'
    
    # 1. 验证 API 端点是否可访问
    endpoints = [
        '/ansible/hosts/',
        '/ansible/host-groups/',
        '/ansible/inventories/',
        '/ansible/playbooks/',
        '/ansible/stats/overview/'
    ]
    
    print("📡 检查 API 端点可访问性...")
    for endpoint in endpoints:
        try:
            response = requests.get(f'{base_url}{endpoint}', timeout=5)
            if response.status_code in [200, 401]:  # 401 表示需要认证，但端点存在
                print(f"✅ {endpoint}")
            else:
                print(f"❌ {endpoint} - {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - 连接失败: {str(e)}")
    
    # 2. 验证数据库表是否存在
    print("\n🗄️  检查数据库表...")
    try:
        from django.db import connection
        cursor = connection.cursor()
        
        tables = [
            'ansible_host',
            'ansible_host_group',
            'ansible_host_group_membership',
            'ansible_inventory_version',
            'ansible_playbook_version'
        ]
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ {table} - {count} 条记录")
            
    except Exception as e:
        print(f"❌ 数据库检查失败: {str(e)}")
    
    # 3. 验证 Celery 任务是否注册
    print("\n⚙️  检查 Celery 任务...")
    try:
        from celery import current_app
        
        tasks = [
            'ansible_integration.tasks.check_host_connectivity',
            'ansible_integration.tasks.gather_host_facts',
            'ansible_integration.tasks.validate_inventory_content',
            'ansible_integration.tasks.validate_playbook_syntax'
        ]
        
        registered_tasks = current_app.tasks.keys()
        
        for task in tasks:
            if task in registered_tasks:
                print(f"✅ {task}")
            else:
                print(f"❌ {task} - 未注册")
                
    except Exception as e:
        print(f"❌ Celery 任务检查失败: {str(e)}")
    
    # 4. 验证模型是否正确导入
    print("\n📦 检查模型导入...")
    try:
        from ansible_integration.models import (
            AnsibleHost, AnsibleHostGroup, AnsibleHostGroupMembership,
            AnsibleInventoryVersion, AnsiblePlaybookVersion
        )
        
        models = [
            ('AnsibleHost', AnsibleHost),
            ('AnsibleHostGroup', AnsibleHostGroup),
            ('AnsibleHostGroupMembership', AnsibleHostGroupMembership),
            ('AnsibleInventoryVersion', AnsibleInventoryVersion),
            ('AnsiblePlaybookVersion', AnsiblePlaybookVersion)
        ]
        
        for name, model in models:
            count = model.objects.count()
            print(f"✅ {name} - {count} 个实例")
            
    except Exception as e:
        print(f"❌ 模型导入失败: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ 快速验证完成！")
    print("\n💡 如需完整测试，请运行：")
    print("   uv run python ../../scripts/test_ansible_deep_integration.py")

if __name__ == '__main__':
    # 设置 Django 环境
    import os
    import sys
    import django
    
    # 添加项目路径
    sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
    
    # 设置 Django 设置模块
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    
    # 初始化 Django
    django.setup()
    
    quick_verify()
