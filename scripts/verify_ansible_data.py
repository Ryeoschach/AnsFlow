#!/usr/bin/env python3
"""
Ansible 深度集成数据库验证脚本

使用 Django shell 验证数据库中的新模型和数据
"""

from django.db import connection
from ansible_integration.models import (
    AnsibleHost, AnsibleHostGroup, AnsibleHostGroupMembership,
    AnsibleInventoryVersion, AnsiblePlaybookVersion,
    AnsibleInventory, AnsiblePlaybook
)

def verify_models():
    """验证模型和数据"""
    print("🔍 Ansible 深度集成数据验证")
    print("=" * 50)
    
    # 验证模型实例计数
    models_data = [
        ("主机 (AnsibleHost)", AnsibleHost),
        ("主机组 (AnsibleHostGroup)", AnsibleHostGroup),
        ("主机组成员关系 (AnsibleHostGroupMembership)", AnsibleHostGroupMembership),
        ("Inventory (AnsibleInventory)", AnsibleInventory),
        ("Inventory版本 (AnsibleInventoryVersion)", AnsibleInventoryVersion),
        ("Playbook (AnsiblePlaybook)", AnsiblePlaybook),
        ("Playbook版本 (AnsiblePlaybookVersion)", AnsiblePlaybookVersion),
    ]
    
    print("📊 数据统计:")
    for name, model in models_data:
        try:
            count = model.objects.count()
            print(f"  {name}: {count} 个")
        except Exception as e:
            print(f"  {name}: ❌ 错误 - {str(e)}")
    
    # 验证数据库表结构
    print("\n🗄️  数据库表验证:")
    cursor = connection.cursor()
    
    tables = [
        'ansible_host',
        'ansible_host_group',
        'ansible_host_group_membership',
        'ansible_inventory_version',
        'ansible_playbook_version'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✅ {table}: {count} 条记录")
        except Exception as e:
            print(f"  ❌ {table}: 错误 - {str(e)}")
    
    # 验证最新数据
    print("\n📝 最新数据:")
    try:
        # 最新主机
        latest_host = AnsibleHost.objects.order_by('-created_at').first()
        if latest_host:
            print(f"  最新主机: {latest_host.hostname} ({latest_host.ip_address})")
        else:
            print("  暂无主机数据")
        
        # 最新主机组
        latest_group = AnsibleHostGroup.objects.order_by('-created_at').first()
        if latest_group:
            print(f"  最新主机组: {latest_group.name}")
        else:
            print("  暂无主机组数据")
        
        # 最新 Inventory
        latest_inventory = AnsibleInventory.objects.order_by('-created_at').first()
        if latest_inventory:
            print(f"  最新 Inventory: {latest_inventory.name}")
            # 检查是否有版本
            version_count = AnsibleInventoryVersion.objects.filter(inventory=latest_inventory).count()
            print(f"    └─ 版本数: {version_count}")
        else:
            print("  暂无 Inventory 数据")
        
        # 最新 Playbook
        latest_playbook = AnsiblePlaybook.objects.order_by('-created_at').first()
        if latest_playbook:
            print(f"  最新 Playbook: {latest_playbook.name}")
            # 检查是否有版本
            version_count = AnsiblePlaybookVersion.objects.filter(playbook=latest_playbook).count()
            print(f"    └─ 版本数: {version_count}")
        else:
            print("  暂无 Playbook 数据")
            
    except Exception as e:
        print(f"  ❌ 数据查询错误: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ 数据验证完成！")

if __name__ == '__main__':
    verify_models()
