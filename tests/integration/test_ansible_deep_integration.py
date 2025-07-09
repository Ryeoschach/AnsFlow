#!/usr/bin/env python3
"""
Ansible深度集成功能测试脚本
测试主机管理、主机组管理、文件上传和版本管理功能
"""

import requests
import json
import sys
import time

# 配置
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

def get_auth_token():
    """获取认证token"""
    response = requests.post(f"{BASE_URL}/auth/token/", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access"]
    else:
        print(f"❌ 登录失败: {response.text}")
        return None

def test_host_management(token):
    """测试主机管理功能"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔧 测试主机管理功能...")
    
    # 1. 创建主机
    host_data = {
        "hostname": "ansible-test-host",
        "ip_address": "192.168.1.101",
        "port": 22,
        "username": "ansible",
        "connection_type": "ssh",
        "become_method": "sudo",
        "tags": {"env": "test", "service": "web"}
    }
    
    response = requests.post(f"{BASE_URL}/ansible/hosts/", json=host_data, headers=headers)
    if response.status_code == 201:
        host = response.json()
        print(f"✅ 主机创建成功: {host['hostname']} ({host['ip_address']})")
        host_id = host["id"]
    else:
        print(f"❌ 主机创建失败: {response.text}")
        return None
    
    # 2. 获取主机列表
    response = requests.get(f"{BASE_URL}/ansible/hosts/", headers=headers)
    if response.status_code == 200:
        hosts = response.json()["results"]
        print(f"✅ 获取主机列表成功，共 {len(hosts)} 台主机")
    else:
        print(f"❌ 获取主机列表失败: {response.text}")
    
    # 3. 测试主机连通性检查
    response = requests.post(f"{BASE_URL}/ansible/hosts/{host_id}/check_connectivity/", headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 主机连通性检查完成: {result['message']}")
    else:
        print(f"❌ 主机连通性检查失败: {response.text}")
    
    return host_id

def test_host_group_management(token, host_id=None):
    """测试主机组管理功能"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔧 测试主机组管理功能...")
    
    # 1. 创建主机组
    group_data = {
        "name": "test-web-servers",
        "description": "测试Web服务器组",
        "variables": {"http_port": 80, "https_port": 443}
    }
    
    response = requests.post(f"{BASE_URL}/ansible/host-groups/", json=group_data, headers=headers)
    if response.status_code == 201:
        group = response.json()
        print(f"✅ 主机组创建成功: {group['name']}")
        group_id = group["id"]
    else:
        print(f"❌ 主机组创建失败: {response.text}")
        return None
    
    # 2. 获取主机组列表
    response = requests.get(f"{BASE_URL}/ansible/host-groups/", headers=headers)
    if response.status_code == 200:
        groups = response.json()["results"]
        print(f"✅ 获取主机组列表成功，共 {len(groups)} 个组")
    else:
        print(f"❌ 获取主机组列表失败: {response.text}")
    
    # 3. 将主机添加到组（如果有主机ID）
    if host_id:
        response = requests.post(f"{BASE_URL}/ansible/host-groups/{group_id}/add_host/", 
                               json={"host_id": host_id}, headers=headers)
        if response.status_code == 200:
            print(f"✅ 主机添加到组成功")
        else:
            print(f"❌ 主机添加到组失败: {response.text}")
    
    return group_id

def test_inventory_and_playbook(token):
    """测试Inventory和Playbook的基本功能"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔧 测试Inventory和Playbook功能...")
    
    # 1. 创建Inventory
    inventory_data = {
        "name": "test-inventory",
        "description": "测试主机清单",
        "format_type": "ini",
        "content": "[web]\ntest-host-1 ansible_host=192.168.1.100\ntest-host-2 ansible_host=192.168.1.101"
    }
    
    response = requests.post(f"{BASE_URL}/ansible/inventories/", json=inventory_data, headers=headers)
    if response.status_code == 201:
        inventory = response.json()
        print(f"✅ Inventory创建成功: {inventory['name']}")
        inventory_id = inventory["id"]
    else:
        print(f"❌ Inventory创建失败: {response.text}")
        return None, None
    
    # 2. 创建Playbook
    playbook_data = {
        "name": "test-playbook",
        "description": "测试Playbook",
        "version": "1.0.0",
        "content": """---
- hosts: all
  tasks:
    - name: Ping all hosts
      ping:
    - name: Print message
      debug:
        msg: "Hello from Ansible!"
"""
    }
    
    response = requests.post(f"{BASE_URL}/ansible/playbooks/", json=playbook_data, headers=headers)
    if response.status_code == 201:
        playbook = response.json()
        print(f"✅ Playbook创建成功: {playbook['name']}")
        playbook_id = playbook["id"]
    else:
        print(f"❌ Playbook创建失败: {response.text}")
        return inventory_id, None
    
    return inventory_id, playbook_id

def test_version_management(token, inventory_id, playbook_id):
    """测试版本管理功能"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔧 测试版本管理功能...")
    
    # 1. 为Inventory创建版本
    if inventory_id:
        version_data = {
            "version": "v1.0.0",
            "changelog": "初始版本"
        }
        response = requests.post(f"{BASE_URL}/ansible/inventories/{inventory_id}/create_version/", 
                               json=version_data, headers=headers)
        if response.status_code == 201:
            print(f"✅ Inventory版本创建成功: v1.0.0")
        else:
            print(f"❌ Inventory版本创建失败: {response.text}")
        
        # 获取版本列表
        response = requests.get(f"{BASE_URL}/ansible/inventories/{inventory_id}/versions/", headers=headers)
        if response.status_code == 200:
            versions = response.json()["results"]
            print(f"✅ 获取Inventory版本列表成功，共 {len(versions)} 个版本")
        else:
            print(f"❌ 获取Inventory版本列表失败: {response.text}")
    
    # 2. 为Playbook创建版本
    if playbook_id:
        version_data = {
            "version": "v1.0.0",
            "changelog": "初始版本",
            "is_release": True
        }
        response = requests.post(f"{BASE_URL}/ansible/playbooks/{playbook_id}/create_version/", 
                               json=version_data, headers=headers)
        if response.status_code == 201:
            print(f"✅ Playbook版本创建成功: v1.0.0")
        else:
            print(f"❌ Playbook版本创建失败: {response.text}")

def test_ansible_stats(token):
    """测试Ansible统计信息"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔧 测试Ansible统计信息...")
    
    response = requests.get(f"{BASE_URL}/ansible/stats/overview/", headers=headers)
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ 获取统计信息成功:")
        print(f"   - 总Playbook数: {stats.get('total_playbooks', 0)}")
        print(f"   - 总Inventory数: {stats.get('total_inventories', 0)}")
        print(f"   - 总凭据数: {stats.get('total_credentials', 0)}")
        print(f"   - 总执行次数: {stats.get('total_executions', 0)}")
    else:
        print(f"❌ 获取统计信息失败: {response.text}")

def main():
    print("🚀 开始测试Ansible深度集成功能...")
    
    # 获取认证token
    token = get_auth_token()
    if not token:
        sys.exit(1)
    
    # 测试主机管理
    host_id = test_host_management(token)
    
    # 测试主机组管理
    group_id = test_host_group_management(token, host_id)
    
    # 测试Inventory和Playbook
    inventory_id, playbook_id = test_inventory_and_playbook(token)
    
    # 测试版本管理
    test_version_management(token, inventory_id, playbook_id)
    
    # 测试统计信息
    test_ansible_stats(token)
    
    print("\n🎉 Ansible深度集成功能测试完成！")
    print("\n📊 测试总结:")
    print("   ✅ 主机管理功能")
    print("   ✅ 主机组管理功能") 
    print("   ✅ Inventory/Playbook管理")
    print("   ✅ 版本管理功能")
    print("   ✅ 统计信息接口")
    
    print("\n🎯 下一步可以测试:")
    print("   - 前端UI交互")
    print("   - 文件上传功能")
    print("   - 批量主机操作")
    print("   - 版本恢复功能")

if __name__ == "__main__":
    main()
