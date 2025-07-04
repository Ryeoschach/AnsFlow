"""
创建Ansible集成测试数据
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ansible_integration.models import AnsibleInventory, AnsiblePlaybook, AnsibleCredential, AnsibleExecution


class Command(BaseCommand):
    help = '创建Ansible集成测试数据'

    def handle(self, *args, **options):
        self.stdout.write('开始创建Ansible测试数据...')
        
        # 获取或创建超级用户
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@ansflow.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(f'创建了管理员用户: {admin_user.username}')
        
        # 创建测试清单
        inventory1, created = AnsibleInventory.objects.get_or_create(
            name='开发环境',
            defaults={
                'description': '开发环境主机清单',
                'format_type': 'ini',
                'content': """[web]
192.168.1.10 ansible_user=ubuntu
192.168.1.11 ansible_user=ubuntu

[db]
192.168.1.20 ansible_user=ubuntu

[dev:children]
web
db

[dev:vars]
env=development
""",
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了清单: {inventory1.name}')

        inventory2, created = AnsibleInventory.objects.get_or_create(
            name='生产环境',
            defaults={
                'description': '生产环境主机清单',
                'format_type': 'yaml',
                'content': """all:
  children:
    web:
      hosts:
        prod-web-01:
          ansible_host: 10.0.1.10
          ansible_user: ubuntu
        prod-web-02:
          ansible_host: 10.0.1.11
          ansible_user: ubuntu
    db:
      hosts:
        prod-db-01:
          ansible_host: 10.0.1.20
          ansible_user: ubuntu
  vars:
    env: production
""",
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了清单: {inventory2.name}')

        # 创建测试凭据
        credential1, created = AnsibleCredential.objects.get_or_create(
            name='Ubuntu SSH密钥',
            defaults={
                'credential_type': 'ssh_key',
                'username': 'ubuntu',
                'ssh_private_key': '-----BEGIN PRIVATE KEY-----\n(这里是测试SSH私钥)\n-----END PRIVATE KEY-----',
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了凭据: {credential1.name}')

        credential2, created = AnsibleCredential.objects.get_or_create(
            name='Root密码认证',
            defaults={
                'credential_type': 'password',
                'username': 'root',
                'password': 'encrypted_password_here',
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了凭据: {credential2.name}')

        # 创建测试Playbook
        playbook1, created = AnsiblePlaybook.objects.get_or_create(
            name='系统信息收集',
            defaults={
                'description': '收集系统基本信息',
                'version': '1.0',
                'category': 'system',
                'is_template': False,
                'content': """---
- name: 收集系统信息
  hosts: all
  gather_facts: yes
  tasks:
    - name: 显示系统信息
      debug:
        msg: |
          主机名: {{ inventory_hostname }}
          操作系统: {{ ansible_distribution }} {{ ansible_distribution_version }}
          内核版本: {{ ansible_kernel }}
          内存: {{ ansible_memtotal_mb }}MB
          CPU核心数: {{ ansible_processor_vcpus }}
          
    - name: 检查磁盘使用情况
      command: df -h
      register: disk_usage
      
    - name: 显示磁盘使用情况
      debug:
        var: disk_usage.stdout_lines
""",
                'parameters': {},
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了Playbook: {playbook1.name}')

        playbook2, created = AnsiblePlaybook.objects.get_or_create(
            name='Nginx安装配置',
            defaults={
                'description': 'Nginx Web服务器安装和配置',
                'version': '1.0',
                'category': 'web',
                'is_template': True,
                'content': """---
- name: 安装和配置Nginx
  hosts: web
  become: yes
  vars:
    nginx_port: "{{ port | default('80') }}"
    server_name: "{{ domain | default('localhost') }}"
    
  tasks:
    - name: 安装Nginx
      package:
        name: nginx
        state: present
        
    - name: 创建网站目录
      file:
        path: /var/www/{{ server_name }}
        state: directory
        owner: www-data
        group: www-data
        mode: '0755'
        
    - name: 创建Nginx配置文件
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/sites-available/{{ server_name }}
        backup: yes
      notify: restart nginx
      
    - name: 启用网站
      file:
        src: /etc/nginx/sites-available/{{ server_name }}
        dest: /etc/nginx/sites-enabled/{{ server_name }}
        state: link
      notify: restart nginx
      
    - name: 启动并启用Nginx服务
      service:
        name: nginx
        state: started
        enabled: yes
        
  handlers:
    - name: restart nginx
      service:
        name: nginx
        state: restarted
""",
                'parameters': {
                    'port': {'type': 'string', 'default': '80', 'description': '监听端口'},
                    'domain': {'type': 'string', 'default': 'localhost', 'description': '域名'}
                },
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了Playbook模板: {playbook2.name}')

        playbook3, created = AnsiblePlaybook.objects.get_or_create(
            name='Docker环境部署',
            defaults={
                'description': 'Docker和Docker Compose安装配置',
                'version': '1.0',
                'category': 'container',
                'is_template': False,
                'content': """---
- name: 安装Docker环境
  hosts: all
  become: yes
  
  tasks:
    - name: 更新包管理器缓存
      apt:
        update_cache: yes
      when: ansible_os_family == "Debian"
      
    - name: 安装依赖包
      package:
        name:
          - apt-transport-https
          - ca-certificates
          - curl
          - gnupg
          - lsb-release
        state: present
      when: ansible_os_family == "Debian"
      
    - name: 添加Docker GPG密钥
      apt_key:
        url: https://download.docker.com/linux/ubuntu/gpg
        state: present
      when: ansible_os_family == "Debian"
      
    - name: 添加Docker源
      apt_repository:
        repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
        state: present
      when: ansible_os_family == "Debian"
      
    - name: 安装Docker
      package:
        name:
          - docker-ce
          - docker-ce-cli
          - containerd.io
        state: present
        
    - name: 启动并启用Docker服务
      service:
        name: docker
        state: started
        enabled: yes
        
    - name: 添加用户到docker组
      user:
        name: "{{ ansible_user }}"
        groups: docker
        append: yes
        
    - name: 安装Docker Compose
      pip:
        name: docker-compose
        state: present
""",
                'parameters': {},
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了Playbook: {playbook3.name}')

        # 创建一些执行记录
        execution1, created = AnsibleExecution.objects.get_or_create(
            id=1,
            defaults={
                'playbook': playbook1,
                'inventory': inventory1,
                'credential': credential1,
                'parameters': {},
                'status': 'success',
                'return_code': 0,
                'stdout': """PLAY [收集系统信息] *****************************************************

TASK [Gathering Facts] ************************************************
ok: [192.168.1.10]
ok: [192.168.1.11]

TASK [显示系统信息] ***************************************************
ok: [192.168.1.10] => {
    "msg": "主机名: 192.168.1.10\\n操作系统: Ubuntu 20.04\\n内核版本: 5.4.0\\n内存: 2048MB\\nCPU核心数: 2"
}
ok: [192.168.1.11] => {
    "msg": "主机名: 192.168.1.11\\n操作系统: Ubuntu 20.04\\n内核版本: 5.4.0\\n内存: 2048MB\\nCPU核心数: 2"
}

PLAY RECAP ************************************************************
192.168.1.10               : ok=2    changed=0    unreachable=0    failed=0
192.168.1.11               : ok=2    changed=0    unreachable=0    failed=0
""",
                'stderr': '',
                'started_at': '2025-01-17 10:00:00',
                'completed_at': '2025-01-17 10:01:30',
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了执行记录: {execution1.id}')

        execution2, created = AnsibleExecution.objects.get_or_create(
            id=2,
            defaults={
                'playbook': playbook2,
                'inventory': inventory2,
                'credential': credential1,
                'parameters': {'port': '8080', 'domain': 'example.com'},
                'status': 'failed',
                'return_code': 1,
                'stdout': """PLAY [安装和配置Nginx] *********************************************

TASK [Gathering Facts] ************************************************
ok: [prod-web-01]
fatal: [prod-web-02]: UNREACHABLE! => {"changed": false, "msg": "Failed to connect to the host via ssh", "unreachable": true}

PLAY RECAP ************************************************************
prod-web-01                : ok=1    changed=0    unreachable=0    failed=0
prod-web-02                : ok=0    changed=0    unreachable=1    failed=0
""",
                'stderr': 'SSH连接失败: prod-web-02主机无法访问',
                'started_at': '2025-01-17 14:30:00',
                'completed_at': '2025-01-17 14:31:15',
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了执行记录: {execution2.id}')

        execution3, created = AnsibleExecution.objects.get_or_create(
            id=3,
            defaults={
                'playbook': playbook3,
                'inventory': inventory1,
                'credential': credential1,
                'parameters': {},
                'status': 'running',
                'return_code': None,
                'stdout': """PLAY [安装Docker环境] *********************************************

TASK [Gathering Facts] ************************************************
ok: [192.168.1.10]
ok: [192.168.1.11]

TASK [更新包管理器缓存] ********************************************
changed: [192.168.1.10]
changed: [192.168.1.11]

TASK [安装依赖包] *************************************************
[正在执行中...]
""",
                'stderr': '',
                'started_at': '2025-01-17 16:00:00',
                'completed_at': None,
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了执行记录: {execution3.id}')

        self.stdout.write(
            self.style.SUCCESS('Ansible测试数据创建完成！')
        )
        self.stdout.write('统计信息:')
        self.stdout.write(f'  - 清单数量: {AnsibleInventory.objects.count()}')
        self.stdout.write(f'  - Playbook数量: {AnsiblePlaybook.objects.count()}')
        self.stdout.write(f'  - 凭据数量: {AnsibleCredential.objects.count()}')
        self.stdout.write(f'  - 执行记录数量: {AnsibleExecution.objects.count()}')
