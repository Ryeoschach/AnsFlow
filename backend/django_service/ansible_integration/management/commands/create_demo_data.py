"""
创建更丰富的Ansible演示数据
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from ansible_integration.models import AnsibleInventory, AnsiblePlaybook, AnsibleCredential


class Command(BaseCommand):
    help = '创建更丰富的Ansible演示数据'

    def handle(self, *args, **options):
        self.stdout.write('开始创建Ansible演示数据...')
        
        # 获取管理员用户
        admin_user = User.objects.get(username='admin')
        
        # 创建更多主机清单
        inventory_k8s, created = AnsibleInventory.objects.get_or_create(
            name='Kubernetes集群',
            defaults={
                'description': 'Kubernetes集群节点清单',
                'format_type': 'yaml',
                'content': """all:
  children:
    k8s_master:
      hosts:
        k8s-master-01:
          ansible_host: 10.0.2.10
          ansible_user: ubuntu
          node_role: master
        k8s-master-02:
          ansible_host: 10.0.2.11
          ansible_user: ubuntu
          node_role: master
        k8s-master-03:
          ansible_host: 10.0.2.12
          ansible_user: ubuntu
          node_role: master
    k8s_worker:
      hosts:
        k8s-worker-01:
          ansible_host: 10.0.2.20
          ansible_user: ubuntu
          node_role: worker
        k8s-worker-02:
          ansible_host: 10.0.2.21
          ansible_user: ubuntu
          node_role: worker
        k8s-worker-03:
          ansible_host: 10.0.2.22
          ansible_user: ubuntu
          node_role: worker
        k8s-worker-04:
          ansible_host: 10.0.2.23
          ansible_user: ubuntu
          node_role: worker
  vars:
    kubernetes_version: "1.28.0"
    container_runtime: containerd
    pod_network_cidr: "10.244.0.0/16"
    service_cidr: "10.96.0.0/12"
""",
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了清单: {inventory_k8s.name}')

        inventory_monitoring, created = AnsibleInventory.objects.get_or_create(
            name='监控系统',
            defaults={
                'description': '监控系统主机清单',
                'format_type': 'ini',
                'content': """[prometheus]
prometheus-01 ansible_host=10.0.3.10 ansible_user=ubuntu
prometheus-02 ansible_host=10.0.3.11 ansible_user=ubuntu

[grafana]
grafana-01 ansible_host=10.0.3.20 ansible_user=ubuntu

[alertmanager]
alertmanager-01 ansible_host=10.0.3.30 ansible_user=ubuntu

[node_exporter]
web-01 ansible_host=10.0.1.10 ansible_user=ubuntu
web-02 ansible_host=10.0.1.11 ansible_user=ubuntu
db-01 ansible_host=10.0.1.20 ansible_user=ubuntu

[monitoring:children]
prometheus
grafana
alertmanager

[monitoring:vars]
prometheus_version=2.45.0
grafana_version=10.0.0
alertmanager_version=0.25.0
node_exporter_version=1.6.0
""",
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了清单: {inventory_monitoring.name}')

        inventory_ci_cd, created = AnsibleInventory.objects.get_or_create(
            name='CI/CD环境',
            defaults={
                'description': '持续集成和部署环境',
                'format_type': 'yaml',
                'content': """all:
  children:
    jenkins:
      hosts:
        jenkins-master:
          ansible_host: 10.0.4.10
          ansible_user: ubuntu
          jenkins_role: master
        jenkins-agent-01:
          ansible_host: 10.0.4.20
          ansible_user: ubuntu
          jenkins_role: agent
        jenkins-agent-02:
          ansible_host: 10.0.4.21
          ansible_user: ubuntu
          jenkins_role: agent
    gitlab:
      hosts:
        gitlab-server:
          ansible_host: 10.0.4.30
          ansible_user: ubuntu
    harbor:
      hosts:
        harbor-registry:
          ansible_host: 10.0.4.40
          ansible_user: ubuntu
  vars:
    jenkins_version: "2.414.1"
    gitlab_version: "16.1.0"
    harbor_version: "2.8.0"
""",
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了清单: {inventory_ci_cd.name}')

        # 创建更多Playbook
        playbook_k8s_install, created = AnsiblePlaybook.objects.get_or_create(
            name='Kubernetes集群安装',
            defaults={
                'description': '自动化安装Kubernetes集群',
                'version': '1.2.0',
                'category': 'kubernetes',
                'is_template': True,
                'content': """---
- name: 安装Kubernetes集群
  hosts: all
  become: yes
  vars:
    kubernetes_version: "{{ k8s_version | default('1.28.0') }}"
    pod_network_cidr: "{{ pod_cidr | default('10.244.0.0/16') }}"
    
  tasks:
    - name: 更新系统包
      apt:
        update_cache: yes
        upgrade: dist
      when: ansible_os_family == "Debian"
      
    - name: 安装依赖包
      package:
        name:
          - apt-transport-https
          - ca-certificates
          - curl
          - gpg
        state: present
        
    - name: 添加Kubernetes APT密钥
      apt_key:
        url: https://packages.cloud.google.com/apt/doc/apt-key.gpg
        state: present
      when: ansible_os_family == "Debian"
      
    - name: 添加Kubernetes APT仓库
      apt_repository:
        repo: "deb https://apt.kubernetes.io/ kubernetes-xenial main"
        state: present
      when: ansible_os_family == "Debian"
      
    - name: 安装容器运行时 (containerd)
      package:
        name: containerd
        state: present
        
    - name: 配置containerd
      copy:
        dest: /etc/containerd/config.toml
        content: |
          [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
            [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
              SystemdCgroup = true
      notify: restart containerd
      
    - name: 安装Kubernetes組件
      package:
        name:
          - kubelet={{ kubernetes_version }}-00
          - kubeadm={{ kubernetes_version }}-00
          - kubectl={{ kubernetes_version }}-00
        state: present
        
    - name: 保持Kubernetes包版本
      dpkg_selections:
        name: "{{ item }}"
        selection: hold
      loop:
        - kubelet
        - kubeadm
        - kubectl
        
  handlers:
    - name: restart containerd
      service:
        name: containerd
        state: restarted

- name: 初始化Kubernetes Master节点
  hosts: k8s_master[0]
  become: yes
  tasks:
    - name: 初始化集群
      command: >
        kubeadm init
        --pod-network-cidr={{ pod_network_cidr }}
        --apiserver-advertise-address={{ ansible_default_ipv4.address }}
      register: kubeadm_init
      
    - name: 创建.kube目录
      file:
        path: /home/{{ ansible_user }}/.kube
        state: directory
        owner: "{{ ansible_user }}"
        group: "{{ ansible_user }}"
        
    - name: 复制admin.conf
      copy:
        src: /etc/kubernetes/admin.conf
        dest: /home/{{ ansible_user }}/.kube/config
        owner: "{{ ansible_user }}"
        group: "{{ ansible_user }}"
        remote_src: yes
        
    - name: 安装CNI网络插件 (Flannel)
      k8s:
        state: present
        definition:
          apiVersion: v1
          kind: Namespace
          metadata:
            name: kube-flannel
      become_user: "{{ ansible_user }}"
""",
                'parameters': {
                    'k8s_version': {'type': 'string', 'default': '1.28.0', 'description': 'Kubernetes版本'},
                    'pod_cidr': {'type': 'string', 'default': '10.244.0.0/16', 'description': 'Pod网络CIDR'}
                },
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了Playbook: {playbook_k8s_install.name}')

        playbook_monitoring, created = AnsiblePlaybook.objects.get_or_create(
            name='Prometheus监控部署',
            defaults={
                'description': '部署Prometheus + Grafana监控系统',
                'version': '2.0.0',
                'category': 'monitoring',
                'is_template': True,
                'content': """---
- name: 部署Prometheus监控系统
  hosts: prometheus
  become: yes
  vars:
    prometheus_version: "{{ prom_version | default('2.45.0') }}"
    prometheus_port: "{{ port | default('9090') }}"
    
  tasks:
    - name: 创建prometheus用户
      user:
        name: prometheus
        system: yes
        shell: /bin/false
        home: /var/lib/prometheus
        
    - name: 创建prometheus目录
      file:
        path: "{{ item }}"
        state: directory
        owner: prometheus
        group: prometheus
        mode: '0755'
      loop:
        - /etc/prometheus
        - /var/lib/prometheus
        - /var/lib/prometheus/data
        
    - name: 下载Prometheus
      get_url:
        url: "https://github.com/prometheus/prometheus/releases/download/v{{ prometheus_version }}/prometheus-{{ prometheus_version }}.linux-amd64.tar.gz"
        dest: /tmp/prometheus.tar.gz
        
    - name: 解压Prometheus
      unarchive:
        src: /tmp/prometheus.tar.gz
        dest: /tmp
        remote_src: yes
        
    - name: 复制Prometheus二进制文件
      copy:
        src: "/tmp/prometheus-{{ prometheus_version }}.linux-amd64/{{ item }}"
        dest: "/usr/local/bin/{{ item }}"
        owner: prometheus
        group: prometheus
        mode: '0755'
        remote_src: yes
      loop:
        - prometheus
        - promtool
        
    - name: 创建Prometheus配置文件
      template:
        src: prometheus.yml.j2
        dest: /etc/prometheus/prometheus.yml
        owner: prometheus
        group: prometheus
        mode: '0644'
      notify: restart prometheus
      
    - name: 创建Prometheus systemd服务
      template:
        src: prometheus.service.j2
        dest: /etc/systemd/system/prometheus.service
      notify:
        - reload systemd
        - restart prometheus
        
    - name: 启动并启用Prometheus服务
      service:
        name: prometheus
        state: started
        enabled: yes
        
  handlers:
    - name: reload systemd
      systemd:
        daemon_reload: yes
        
    - name: restart prometheus
      service:
        name: prometheus
        state: restarted

- name: 部署Grafana
  hosts: grafana
  become: yes
  vars:
    grafana_version: "{{ graf_version | default('10.0.0') }}"
    
  tasks:
    - name: 添加Grafana APT密钥
      apt_key:
        url: https://packages.grafana.com/gpg.key
        state: present
        
    - name: 添加Grafana APT仓库
      apt_repository:
        repo: "deb https://packages.grafana.com/oss/deb stable main"
        state: present
        
    - name: 安装Grafana
      package:
        name: grafana
        state: present
        
    - name: 启动并启用Grafana服务
      service:
        name: grafana-server
        state: started
        enabled: yes
        
    - name: 等待Grafana启动
      wait_for:
        port: 3000
        delay: 10
""",
                'parameters': {
                    'prom_version': {'type': 'string', 'default': '2.45.0', 'description': 'Prometheus版本'},
                    'graf_version': {'type': 'string', 'default': '10.0.0', 'description': 'Grafana版本'},
                    'port': {'type': 'string', 'default': '9090', 'description': 'Prometheus端口'}
                },
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了Playbook: {playbook_monitoring.name}')

        playbook_backup, created = AnsiblePlaybook.objects.get_or_create(
            name='数据库备份',
            defaults={
                'description': '自动化数据库备份任务',
                'version': '1.5.0',
                'category': 'backup',
                'is_template': True,
                'content': """---
- name: 数据库备份任务
  hosts: db
  become: yes
  vars:
    backup_dir: "{{ backup_path | default('/backup') }}"
    retention_days: "{{ retention | default('7') }}"
    databases: "{{ db_list | default(['mysql', 'postgresql']) }}"
    
  tasks:
    - name: 创建备份目录
      file:
        path: "{{ backup_dir }}"
        state: directory
        owner: root
        group: root
        mode: '0755'
        
    - name: 创建MySQL备份脚本
      template:
        src: mysql_backup.sh.j2
        dest: /usr/local/bin/mysql_backup.sh
        mode: '0755'
      when: "'mysql' in databases"
      
    - name: 创建PostgreSQL备份脚本
      template:
        src: postgres_backup.sh.j2
        dest: /usr/local/bin/postgres_backup.sh
        mode: '0755'
      when: "'postgresql' in databases"
      
    - name: 执行MySQL备份
      command: /usr/local/bin/mysql_backup.sh
      register: mysql_backup_result
      when: "'mysql' in databases"
      
    - name: 执行PostgreSQL备份
      command: /usr/local/bin/postgres_backup.sh
      register: postgres_backup_result
      when: "'postgresql' in databases"
      
    - name: 清理过期备份文件
      find:
        paths: "{{ backup_dir }}"
        age: "{{ retention_days }}d"
        patterns: "*.sql.gz"
      register: old_backups
      
    - name: 删除过期备份
      file:
        path: "{{ item.path }}"
        state: absent
      loop: "{{ old_backups.files }}"
      
    - name: 发送备份状态通知
      mail:
        to: admin@example.com
        subject: "数据库备份状态 - {{ inventory_hostname }}"
        body: |
          主机: {{ inventory_hostname }}
          备份时间: {{ ansible_date_time.iso8601 }}
          MySQL备份: {{ 'SUCCESS' if mysql_backup_result.rc == 0 else 'FAILED' }}
          PostgreSQL备份: {{ 'SUCCESS' if postgres_backup_result.rc == 0 else 'FAILED' }}
          备份目录: {{ backup_dir }}
      when: send_notification | default(false)
""",
                'parameters': {
                    'backup_path': {'type': 'string', 'default': '/backup', 'description': '备份目录路径'},
                    'retention': {'type': 'string', 'default': '7', 'description': '备份保留天数'},
                    'db_list': {'type': 'list', 'default': ['mysql', 'postgresql'], 'description': '需要备份的数据库类型'},
                    'send_notification': {'type': 'boolean', 'default': False, 'description': '是否发送邮件通知'}
                },
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了Playbook: {playbook_backup.name}')

        playbook_security, created = AnsiblePlaybook.objects.get_or_create(
            name='安全加固',
            defaults={
                'description': 'Linux系统安全加固配置',
                'version': '1.0.0',
                'category': 'security',
                'is_template': False,
                'content': """---
- name: Linux系统安全加固
  hosts: all
  become: yes
  
  tasks:
    - name: 更新系统包
      package:
        name: '*'
        state: latest
      when: ansible_os_family == "RedHat"
      
    - name: 更新系统包 (Debian/Ubuntu)
      apt:
        upgrade: dist
        update_cache: yes
      when: ansible_os_family == "Debian"
      
    - name: 安装安全相关包
      package:
        name:
          - fail2ban
          - ufw
          - aide
          - rkhunter
          - chkrootkit
        state: present
        
    - name: 配置SSH安全
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: "{{ item.regexp }}"
        line: "{{ item.line }}"
        backup: yes
      loop:
        - { regexp: '^#?PermitRootLogin', line: 'PermitRootLogin no' }
        - { regexp: '^#?PasswordAuthentication', line: 'PasswordAuthentication no' }
        - { regexp: '^#?X11Forwarding', line: 'X11Forwarding no' }
        - { regexp: '^#?MaxAuthTries', line: 'MaxAuthTries 3' }
        - { regexp: '^#?ClientAliveInterval', line: 'ClientAliveInterval 300' }
        - { regexp: '^#?ClientAliveCountMax', line: 'ClientAliveCountMax 2' }
      notify: restart ssh
      
    - name: 配置防火墙规则
      ufw:
        rule: "{{ item.rule }}"
        port: "{{ item.port }}"
        proto: "{{ item.proto | default('tcp') }}"
      loop:
        - { rule: 'allow', port: '22' }
        - { rule: 'allow', port: '80' }
        - { rule: 'allow', port: '443' }
      
    - name: 启用防火墙
      ufw:
        state: enabled
        policy: deny
        direction: incoming
        
    - name: 配置fail2ban
      copy:
        dest: /etc/fail2ban/jail.local
        content: |
          [DEFAULT]
          bantime = 3600
          findtime = 600
          maxretry = 3
          
          [sshd]
          enabled = true
          port = ssh
          filter = sshd
          logpath = /var/log/auth.log
          maxretry = 3
      notify: restart fail2ban
      
    - name: 设置密码策略
      lineinfile:
        path: /etc/pam.d/common-password
        regexp: '^password.*pam_unix.so'
        line: 'password [success=1 default=ignore] pam_unix.so obscure sha512 minlen=8'
        backup: yes
      when: ansible_os_family == "Debian"
      
    - name: 禁用不必要的服务
      service:
        name: "{{ item }}"
        state: stopped
        enabled: no
      loop:
        - telnet
        - rsh
        - rlogin
      ignore_errors: yes
      
    - name: 设置文件权限
      file:
        path: "{{ item.path }}"
        mode: "{{ item.mode }}"
      loop:
        - { path: '/etc/passwd', mode: '0644' }
        - { path: '/etc/shadow', mode: '0640' }
        - { path: '/etc/group', mode: '0644' }
        - { path: '/etc/gshadow', mode: '0640' }
        
  handlers:
    - name: restart ssh
      service:
        name: ssh
        state: restarted
        
    - name: restart fail2ban
      service:
        name: fail2ban
        state: restarted
""",
                'parameters': {},
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了Playbook: {playbook_security.name}')

        # 创建更多凭据示例
        credential_k8s, created = AnsibleCredential.objects.get_or_create(
            name='Kubernetes管理员密钥',
            defaults={
                'credential_type': 'ssh_key',
                'username': 'ubuntu',
                'ssh_private_key': '''-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAFwAAAAdzc2gtcn
NhAAAAAwEAAQAAAQEA0123456789abcdef... (示例SSH密钥)
-----END OPENSSH PRIVATE KEY-----''',
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了凭据: {credential_k8s.name}')

        credential_prod, created = AnsibleCredential.objects.get_or_create(
            name='生产环境访问密钥',
            defaults={
                'credential_type': 'ssh_key',
                'username': 'deploy',
                'ssh_private_key': '''-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0vx2w7Kz8... (示例RSA密钥)
-----END RSA PRIVATE KEY-----''',
                'created_by': admin_user
            }
        )
        if created:
            self.stdout.write(f'创建了凭据: {credential_prod.name}')

        self.stdout.write(
            self.style.SUCCESS('Ansible演示数据创建完成！')
        )
        self.stdout.write('最新统计信息:')
        self.stdout.write(f'  - 清单数量: {AnsibleInventory.objects.count()}')
        self.stdout.write(f'  - Playbook数量: {AnsiblePlaybook.objects.count()}')
        self.stdout.write(f'  - 凭据数量: {AnsibleCredential.objects.count()}')
