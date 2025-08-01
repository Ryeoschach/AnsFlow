# AnsFlow Ansible 功能使用文档

## 概述

AnsFlow 的 Ansible 功能提供了完整的 Ansible 自动化工具集成，支持 Inventory 管理、Playbook 执行、主机管理和流水线集成等功能。

## 功能特性

### 1. 核心功能
- **Inventory 管理**: 支持 INI 和 YAML 格式的主机清单
- **Playbook 管理**: 可视化创建和管理 Ansible Playbook
- **认证管理**: 加密存储 SSH 密钥和密码
- **主机管理**: 动态主机发现和连通性检查
- **执行监控**: 实时查看 Ansible 执行状态和日志
- **流水线集成**: 无缝集成到 CI/CD 流水线中

### 2. 安全特性
- JWT 身份认证
- 敏感数据加密存储
- 权限控制和审计日志
- SSH 密钥安全管理

## 使用方法

### 1. Web 界面使用

#### 访问入口
```
http://127.0.0.1:5173/ansible
```

#### 界面布局
- **Inventory 标签**: 管理主机清单
- **Playbook 标签**: 管理自动化脚本
- **凭据 标签**: 管理认证信息
- **主机 标签**: 管理单个主机
- **执行历史 标签**: 查看执行记录

### 2. API 接口使用

#### 认证方式
```javascript
// 设置 JWT Token
localStorage.setItem('token', 'your-jwt-token');

// 或使用认证脚本
const token = await apiService.login(username, password);
```

#### 主要 API 端点

##### Inventory 管理
```http
GET    /api/ansible/inventories/     # 获取清单列表
POST   /api/ansible/inventories/     # 创建清单
GET    /api/ansible/inventories/{id}/ # 获取清单详情
PUT    /api/ansible/inventories/{id}/ # 更新清单
DELETE /api/ansible/inventories/{id}/ # 删除清单
```

##### Playbook 管理
```http
GET    /api/ansible/playbooks/       # 获取 Playbook 列表
POST   /api/ansible/playbooks/       # 创建 Playbook
POST   /api/ansible/playbooks/{id}/execute/ # 执行 Playbook
```

##### 主机管理
```http
GET    /api/ansible/hosts/           # 获取主机列表
POST   /api/ansible/hosts/           # 创建主机
POST   /api/ansible/hosts/{id}/check_connectivity/ # 检查连通性
POST   /api/ansible/hosts/{id}/gather_facts/ # 收集 Facts
```

### 3. 流水线集成

#### 步骤类型配置
```yaml
step_type: "ansible"
ansible_playbook: playbook_id
ansible_inventory: inventory_id
ansible_credential: credential_id
ansible_parameters:
  extra_vars:
    app_version: "${BUILD_NUMBER}"
  tags: "deploy"
  verbose: true
```

#### 参数说明
- `ansible_playbook`: Playbook ID
- `ansible_inventory`: Inventory ID  
- `ansible_credential`: 认证凭据 ID
- `ansible_parameters`: Ansible 执行参数
  - `extra_vars`: 额外变量
  - `tags`: 执行标签
  - `skip_tags`: 跳过标签
  - `limit`: 限制主机
  - `verbose`: 详细输出
  - `check_mode`: 检查模式

## 最佳实践

### 1. Inventory 组织
```ini
# 按环境分组
[production]
web1.prod.com
web2.prod.com

[staging]
web1.stage.com
web2.stage.com

# 按功能分组
[webservers]
web1.prod.com
web1.stage.com

[databases]
db1.prod.com
db1.stage.com

# 组变量
[webservers:vars]
nginx_port=80
app_env=production
```

### 2. Playbook 设计
```yaml
---
- name: Deploy Web Application
  hosts: webservers
  become: yes
  vars:
    app_version: "{{ app_version | default('latest') }}"
    
  tasks:
    - name: Update package cache
      apt:
        update_cache: yes
      tags: system
      
    - name: Install dependencies
      apt:
        name: "{{ item }}"
        state: present
      loop:
        - nginx
        - python3
        - git
      tags: dependencies
      
    - name: Deploy application
      git:
        repo: "{{ app_repo }}"
        dest: /opt/app
        version: "{{ app_version }}"
      tags: deploy
      notify: restart nginx
      
  handlers:
    - name: restart nginx
      service:
        name: nginx
        state: restarted
```

### 3. 安全配置
```python
# 使用加密的凭据
credential = AnsibleCredential(
    name='Production SSH Key',
    credential_type='ssh',
    username='deploy',
    ssh_private_key_input=ssh_key,  # 自动加密
    is_encrypted=True
)

# 设置主机变量
host = AnsibleHost(
    hostname='web1.prod.com',
    variables={
        'ansible_python_interpreter': '/usr/bin/python3',
        'ansible_ssh_common_args': '-o StrictHostKeyChecking=no'
    }
)
```

### 4. 监控和日志
```python
# 监控执行状态
execution = AnsibleExecution.objects.get(id=execution_id)
print(f"状态: {execution.status}")
print(f"开始时间: {execution.started_at}")
print(f"结束时间: {execution.finished_at}")

# 查看详细日志
print("标准输出:")
print(execution.stdout)
print("错误输出:")
print(execution.stderr)
```

## 故障排除

### 1. 常见错误

#### 认证失败
```
401 Unauthorized - JWT token missing or invalid
```
**解决方案**: 确保请求头包含有效的 JWT token

#### 连通性问题
```
SSH connection failed
```
**解决方案**: 
- 检查网络连通性
- 验证 SSH 凭据
- 确认端口开放

#### Playbook 语法错误
```
Syntax Error: could not find expected ':'
```
**解决方案**: 
- 验证 YAML 语法
- 检查缩进和格式
- 使用 ansible-playbook --syntax-check

### 2. 调试技巧

#### 启用详细输出
```python
execution_params = {
    'verbose': True,
    'extra_vars': {'debug': True}
}
```

#### 使用检查模式
```python
execution_params = {
    'check_mode': True  # 不实际执行，只检查
}
```

#### 限制执行范围
```python
execution_params = {
    'limit': 'web1.prod.com',  # 只在指定主机执行
    'tags': 'deploy'           # 只执行指定标签
}
```

## 扩展开发

### 1. 自定义步骤类型
```python
# 在 pipeline 模块中注册新的步骤类型
STEP_TYPE_HANDLERS = {
    'ansible': AnsibleStepHandler,
    'ansible_galaxy': AnsibleGalaxyStepHandler,  # 自定义
}
```

### 2. 插件集成
```python
# 自定义 Ansible 模块
class CustomAnsibleModule:
    def run(self, inventory, playbook, **kwargs):
        # 自定义执行逻辑
        pass
```

### 3. 回调插件
```python
# 自定义回调插件收集执行信息
class AnsFlowCallbackPlugin(CallbackPlugin):
    def v2_runner_on_ok(self, result):
        # 处理任务成功事件
        pass
```

## 性能优化

### 1. 并行执行
```yaml
# 在 Playbook 中启用并行
- hosts: webservers
  strategy: free  # 或 linear
  serial: 5       # 批量执行
```

### 2. 缓存优化
```python
# 启用 Facts 缓存
ANSIBLE_FACT_CACHING = True
ANSIBLE_FACT_CACHING_TIMEOUT = 86400
```

### 3. 连接优化
```yaml
# 复用 SSH 连接
[ssh_connection]
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
pipelining = True
```

这个文档涵盖了 AnsFlow 中 Ansible 功能的完整架构和使用方法，从基础概念到高级特性都有详细说明。
