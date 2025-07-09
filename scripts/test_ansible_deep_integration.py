#!/usr/bin/env python3
"""
Ansible 深度集成功能测试脚本

测试内容：
1. 主机管理功能
2. 主机组管理功能
3. 文件上传功能
4. 版本管理功能
5. 连通性检查功能
"""

import requests
import json
import time
import sys
import os

# API 基础配置
BASE_URL = 'http://localhost:8000'
API_BASE = f'{BASE_URL}/api/v1'

class AnsibleIntegrationTest:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.created_items = {
            'hosts': [],
            'host_groups': [],
            'inventories': [],
            'playbooks': []
        }

    def login(self, username='admin', password='admin123'):
        """登录并获取认证token"""
        try:
            response = self.session.post(f'{API_BASE}/auth/token/', {
                'username': username,
                'password': password
            })
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access')
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                print(f"✅ 登录成功: {username}")
                return True
            else:
                print(f"❌ 登录失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 登录异常: {str(e)}")
            return False

    def test_host_management(self):
        """测试主机管理功能"""
        print("\n🔧 测试主机管理功能...")
        
        # 1. 创建测试主机
        host_data = {
            'hostname': 'test-server-01',
            'ip_address': '192.168.1.100',
            'port': 22,
            'username': 'ubuntu',
            'connection_type': 'ssh',
            'become_method': 'sudo',
            'tags': {'env': 'test', 'type': 'web'}
        }
        
        try:
            response = self.session.post(f'{API_BASE}/ansible/hosts/', json=host_data)
            if response.status_code == 201:
                host = response.json()
                self.created_items['hosts'].append(host['id'])
                print(f"✅ 主机创建成功: {host['hostname']} (ID: {host['id']})")
                
                # 2. 测试主机列表获取
                response = self.session.get(f'{API_BASE}/ansible/hosts/')
                if response.status_code == 200:
                    hosts = response.json()
                    print(f"✅ 主机列表获取成功，共 {len(hosts)} 个主机")
                else:
                    print(f"❌ 主机列表获取失败: {response.status_code}")
                
                # 3. 测试主机详情获取
                response = self.session.get(f'{API_BASE}/ansible/hosts/{host["id"]}/')
                if response.status_code == 200:
                    host_detail = response.json()
                    print(f"✅ 主机详情获取成功: {host_detail['hostname']}")
                else:
                    print(f"❌ 主机详情获取失败: {response.status_code}")
                
                # 4. 测试主机连通性检查
                response = self.session.post(f'{API_BASE}/ansible/hosts/{host["id"]}/check_connectivity/')
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 连通性检查完成: {result.get('message', '未知结果')}")
                else:
                    print(f"❌ 连通性检查失败: {response.status_code}")
                
                return True
            else:
                print(f"❌ 主机创建失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 主机管理测试异常: {str(e)}")
            return False

    def test_host_group_management(self):
        """测试主机组管理功能"""
        print("\n📁 测试主机组管理功能...")
        
        # 1. 创建父主机组
        parent_group_data = {
            'name': 'production',
            'description': '生产环境主机组',
            'variables': {'env': 'production', 'backup': True}
        }
        
        try:
            response = self.session.post(f'{API_BASE}/ansible/host-groups/', json=parent_group_data)
            if response.status_code == 201:
                parent_group = response.json()
                self.created_items['host_groups'].append(parent_group['id'])
                print(f"✅ 父主机组创建成功: {parent_group['name']} (ID: {parent_group['id']})")
                
                # 2. 创建子主机组
                child_group_data = {
                    'name': 'web-servers',
                    'description': 'Web服务器组',
                    'parent': parent_group['id'],
                    'variables': {'role': 'web', 'port': 80}
                }
                
                response = self.session.post(f'{API_BASE}/ansible/host-groups/', json=child_group_data)
                if response.status_code == 201:
                    child_group = response.json()
                    self.created_items['host_groups'].append(child_group['id'])
                    print(f"✅ 子主机组创建成功: {child_group['name']} (ID: {child_group['id']})")
                    
                    # 3. 测试主机组列表获取
                    response = self.session.get(f'{API_BASE}/ansible/host-groups/')
                    if response.status_code == 200:
                        groups = response.json()
                        print(f"✅ 主机组列表获取成功，共 {len(groups)} 个主机组")
                    else:
                        print(f"❌ 主机组列表获取失败: {response.status_code}")
                    
                    # 4. 测试主机添加到组
                    if self.created_items['hosts']:
                        host_id = self.created_items['hosts'][0]
                        response = self.session.post(
                            f'{API_BASE}/ansible/host-groups/{child_group["id"]}/add_host/',
                            json={'host_id': host_id}
                        )
                        if response.status_code == 200:
                            print(f"✅ 主机成功添加到组: host_{host_id} -> {child_group['name']}")
                        else:
                            print(f"❌ 主机添加到组失败: {response.status_code}")
                    
                    return True
                else:
                    print(f"❌ 子主机组创建失败: {response.status_code} - {response.text}")
                    return False
            else:
                print(f"❌ 父主机组创建失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 主机组管理测试异常: {str(e)}")
            return False

    def test_inventory_management(self):
        """测试 Inventory 管理功能"""
        print("\n📋 测试 Inventory 管理功能...")
        
        inventory_data = {
            'name': 'test-inventory',
            'description': '测试用主机清单',
            'format_type': 'ini',
            'content': '''[webservers]
192.168.1.100 ansible_user=ubuntu
192.168.1.101 ansible_user=ubuntu

[databases]
192.168.1.200 ansible_user=postgres

[production:children]
webservers
databases

[production:vars]
env=production
backup=yes'''
        }
        
        try:
            # 1. 创建 Inventory
            response = self.session.post(f'{API_BASE}/ansible/inventories/', json=inventory_data)
            if response.status_code == 201:
                inventory = response.json()
                self.created_items['inventories'].append(inventory['id'])
                print(f"✅ Inventory 创建成功: {inventory['name']} (ID: {inventory['id']})")
                
                # 2. 测试 Inventory 验证
                response = self.session.post(f'{API_BASE}/ansible/inventories/{inventory["id"]}/validate_inventory/')
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Inventory 验证完成: {result.get('message', '未知结果')}")
                else:
                    print(f"❌ Inventory 验证失败: {response.status_code}")
                
                # 3. 测试版本创建
                version_data = {
                    'version': '1.1',
                    'changelog': '添加数据库服务器组'
                }
                response = self.session.post(
                    f'{API_BASE}/ansible/inventories/{inventory["id"]}/create_version/',
                    json=version_data
                )
                if response.status_code == 200:
                    version = response.json()
                    print(f"✅ Inventory 版本创建成功: v{version['version']}")
                else:
                    print(f"❌ Inventory 版本创建失败: {response.status_code}")
                
                # 4. 测试版本列表获取
                response = self.session.get(f'{API_BASE}/ansible/inventories/{inventory["id"]}/versions/')
                if response.status_code == 200:
                    versions = response.json()
                    print(f"✅ Inventory 版本列表获取成功，共 {len(versions)} 个版本")
                else:
                    print(f"❌ Inventory 版本列表获取失败: {response.status_code}")
                
                return True
            else:
                print(f"❌ Inventory 创建失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Inventory 管理测试异常: {str(e)}")
            return False

    def test_playbook_management(self):
        """测试 Playbook 管理功能"""
        print("\n📖 测试 Playbook 管理功能...")
        
        playbook_data = {
            'name': 'nginx-setup',
            'description': 'Nginx 安装和配置 Playbook',
            'version': '1.0',
            'category': 'web',
            'is_template': True,
            'content': '''---
- name: Install and configure Nginx
  hosts: webservers
  become: yes
  
  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present
        update_cache: yes
    
    - name: Start nginx service
      systemd:
        name: nginx
        state: started
        enabled: yes
    
    - name: Configure nginx
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/nginx.conf
      notify:
        - restart nginx
  
  handlers:
    - name: restart nginx
      systemd:
        name: nginx
        state: restarted''',
            'parameters': {
                'nginx_port': 80,
                'server_name': 'example.com'
            }
        }
        
        try:
            # 1. 创建 Playbook
            response = self.session.post(f'{API_BASE}/ansible/playbooks/', json=playbook_data)
            if response.status_code == 201:
                playbook = response.json()
                self.created_items['playbooks'].append(playbook['id'])
                print(f"✅ Playbook 创建成功: {playbook['name']} (ID: {playbook['id']})")
                
                # 2. 测试 Playbook 语法验证
                response = self.session.post(f'{API_BASE}/ansible/playbooks/{playbook["id"]}/validate_playbook/')
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Playbook 语法验证完成: {result.get('message', '未知结果')}")
                else:
                    print(f"❌ Playbook 语法验证失败: {response.status_code}")
                
                # 3. 测试版本创建
                version_data = {
                    'version': '1.1',
                    'changelog': '添加SSL配置支持',
                    'is_release': True
                }
                response = self.session.post(
                    f'{API_BASE}/ansible/playbooks/{playbook["id"]}/create_version/',
                    json=version_data
                )
                if response.status_code == 200:
                    version = response.json()
                    print(f"✅ Playbook 版本创建成功: v{version['version']}")
                else:
                    print(f"❌ Playbook 版本创建失败: {response.status_code}")
                
                return True
            else:
                print(f"❌ Playbook 创建失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Playbook 管理测试异常: {str(e)}")
            return False

    def test_statistics(self):
        """测试统计功能"""
        print("\n📊 测试统计功能...")
        
        try:
            response = self.session.get(f'{API_BASE}/ansible/stats/overview/')
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ 统计数据获取成功:")
                print(f"   - 主机数量: {stats.get('total_hosts', 0)}")
                print(f"   - 主机组数量: {stats.get('total_host_groups', 0)}")
                print(f"   - Inventory数量: {stats.get('total_inventories', 0)}")
                print(f"   - Playbook数量: {stats.get('total_playbooks', 0)}")
                print(f"   - 执行总数: {stats.get('total_executions', 0)}")
                return True
            else:
                print(f"❌ 统计数据获取失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 统计功能测试异常: {str(e)}")
            return False

    def cleanup(self):
        """清理测试数据"""
        print("\n🧹 清理测试数据...")
        
        # 清理主机
        for host_id in self.created_items['hosts']:
            try:
                response = self.session.delete(f'{API_BASE}/ansible/hosts/{host_id}/')
                if response.status_code == 204:
                    print(f"✅ 主机 {host_id} 删除成功")
                else:
                    print(f"❌ 主机 {host_id} 删除失败: {response.status_code}")
            except Exception as e:
                print(f"❌ 主机 {host_id} 删除异常: {str(e)}")
        
        # 清理主机组
        for group_id in self.created_items['host_groups']:
            try:
                response = self.session.delete(f'{API_BASE}/ansible/host-groups/{group_id}/')
                if response.status_code == 204:
                    print(f"✅ 主机组 {group_id} 删除成功")
                else:
                    print(f"❌ 主机组 {group_id} 删除失败: {response.status_code}")
            except Exception as e:
                print(f"❌ 主机组 {group_id} 删除异常: {str(e)}")
        
        # 清理 Inventory
        for inventory_id in self.created_items['inventories']:
            try:
                response = self.session.delete(f'{API_BASE}/ansible/inventories/{inventory_id}/')
                if response.status_code == 204:
                    print(f"✅ Inventory {inventory_id} 删除成功")
                else:
                    print(f"❌ Inventory {inventory_id} 删除失败: {response.status_code}")
            except Exception as e:
                print(f"❌ Inventory {inventory_id} 删除异常: {str(e)}")
        
        # 清理 Playbook
        for playbook_id in self.created_items['playbooks']:
            try:
                response = self.session.delete(f'{API_BASE}/ansible/playbooks/{playbook_id}/')
                if response.status_code == 204:
                    print(f"✅ Playbook {playbook_id} 删除成功")
                else:
                    print(f"❌ Playbook {playbook_id} 删除失败: {response.status_code}")
            except Exception as e:
                print(f"❌ Playbook {playbook_id} 删除异常: {str(e)}")

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始 Ansible 深度集成功能测试...")
        print("=" * 60)
        
        # 登录
        if not self.login():
            print("❌ 登录失败，终止测试")
            return False
        
        success_count = 0
        total_tests = 5
        
        try:
            # 运行各项测试
            if self.test_host_management():
                success_count += 1
            
            if self.test_host_group_management():
                success_count += 1
            
            if self.test_inventory_management():
                success_count += 1
            
            if self.test_playbook_management():
                success_count += 1
            
            if self.test_statistics():
                success_count += 1
            
        finally:
            # 清理测试数据
            self.cleanup()
        
        print("\n" + "=" * 60)
        print(f"📈 测试结果: {success_count}/{total_tests} 通过")
        
        if success_count == total_tests:
            print("🎉 所有测试通过！Ansible 深度集成功能正常！")
            return True
        else:
            print(f"⚠️  有 {total_tests - success_count} 个测试失败，请检查相关功能")
            return False


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print(__doc__)
        return
    
    test = AnsibleIntegrationTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
