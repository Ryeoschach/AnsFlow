# Ansible自动化部署集成计划

## 📋 集成概述

为AnsFlow平台开发完整的Ansible自动化部署集成功能，使平台支持Ansible playbook的管理、执行和监控，提供企业级自动化部署能力。

## 🎯 功能目标

### 核心功能
- **Playbook管理**: 上传、版本控制、模板化Ansible playbooks
- **Inventory管理**: 主机组管理、动态inventory、凭据配置
- **执行监控**: 实时执行监控、日志流式输出、状态同步
- **模板系统**: 预定义部署模板、参数化配置
- **权限控制**: 基于RBAC的Ansible资源访问控制

### 企业级特性
- **批量部署**: 多环境、多主机组的批量部署
- **回滚机制**: 部署失败自动回滚、历史版本恢复
- **审批流程**: 生产环境部署审批、多级审核
- **审计日志**: 完整的部署操作审计和追踪
- **告警通知**: 部署状态告警、Slack/邮件集成

## 🏗️ 技术架构

### 后端实现 (Django)

#### 1. 数据模型设计

```python
# models.py
class AnsibleInventory(models.Model):
    """Ansible主机清单"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    content = models.TextField()  # INI格式或YAML格式
    format_type = models.CharField(max_length=10, choices=[('ini', 'INI'), ('yaml', 'YAML')])
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class AnsiblePlaybook(models.Model):
    """Ansible Playbook"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    content = models.TextField()  # YAML格式playbook内容
    version = models.CharField(max_length=50, default='1.0')
    is_template = models.BooleanField(default=False)
    category = models.CharField(max_length=50, blank=True)  # 分类：web, database, monitoring等
    parameters = models.JSONField(default=dict)  # 可配置参数定义
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class AnsibleCredential(models.Model):
    """Ansible连接凭据"""
    name = models.CharField(max_length=100)
    credential_type = models.CharField(max_length=20, choices=[
        ('ssh_key', 'SSH密钥'),
        ('password', '用户名密码'),
        ('vault', 'Ansible Vault')
    ])
    username = models.CharField(max_length=100, blank=True)
    password = models.TextField(blank=True)  # 加密存储
    ssh_private_key = models.TextField(blank=True)  # 加密存储
    vault_password = models.TextField(blank=True)  # 加密存储
    sudo_password = models.TextField(blank=True)  # 加密存储
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class AnsibleExecution(models.Model):
    """Ansible执行记录"""
    playbook = models.ForeignKey(AnsiblePlaybook, on_delete=models.CASCADE)
    inventory = models.ForeignKey(AnsibleInventory, on_delete=models.CASCADE)
    credential = models.ForeignKey(AnsibleCredential, on_delete=models.CASCADE)
    parameters = models.JSONField(default=dict)  # 执行参数
    status = models.CharField(max_length=20, choices=[
        ('pending', '等待中'),
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('cancelled', '已取消')
    ])
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    return_code = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### 2. Ansible执行引擎

```python
# ansible_runner.py
import ansible_runner
import tempfile
import os
from django.conf import settings

class AnsibleExecutor:
    """Ansible执行器"""
    
    def __init__(self, execution_id):
        self.execution = AnsibleExecution.objects.get(id=execution_id)
        self.temp_dir = tempfile.mkdtemp()
    
    def prepare_environment(self):
        """准备执行环境"""
        # 创建临时inventory文件
        inventory_path = os.path.join(self.temp_dir, 'inventory')
        with open(inventory_path, 'w') as f:
            f.write(self.execution.inventory.content)
        
        # 创建临时playbook文件
        playbook_path = os.path.join(self.temp_dir, 'playbook.yml')
        with open(playbook_path, 'w') as f:
            f.write(self.execution.playbook.content)
        
        # 准备认证文件
        if self.execution.credential.ssh_private_key:
            key_path = os.path.join(self.temp_dir, 'ssh_key')
            with open(key_path, 'w') as f:
                f.write(decrypt_password(self.execution.credential.ssh_private_key))
            os.chmod(key_path, 0o600)
        
        return inventory_path, playbook_path
    
    def execute_playbook(self):
        """执行playbook"""
        inventory_path, playbook_path = self.prepare_environment()
        
        # 准备执行参数
        extravars = self.execution.parameters.copy()
        
        # 执行ansible-playbook
        result = ansible_runner.run(
            private_data_dir=self.temp_dir,
            playbook=playbook_path,
            inventory=inventory_path,
            extravars=extravars,
            quiet=False,
            verbosity=2
        )
        
        # 更新执行状态
        self.execution.return_code = result.rc
        self.execution.stdout = result.stdout.read() if result.stdout else ''
        self.execution.stderr = result.stderr.read() if result.stderr else ''
        self.execution.status = 'success' if result.rc == 0 else 'failed'
        self.execution.completed_at = timezone.now()
        self.execution.save()
        
        return result
    
    def cleanup(self):
        """清理临时文件"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
```

#### 3. Celery异步任务

```python
# tasks.py
from celery import shared_task
from .models import AnsibleExecution
from .ansible_runner import AnsibleExecutor

@shared_task
def execute_ansible_playbook(execution_id):
    """异步执行Ansible playbook"""
    try:
        execution = AnsibleExecution.objects.get(id=execution_id)
        execution.status = 'running'
        execution.started_at = timezone.now()
        execution.save()
        
        # 发送WebSocket开始信号
        send_websocket_message(f'ansible_execution_{execution_id}', {
            'type': 'execution_started',
            'execution_id': execution_id,
            'status': 'running'
        })
        
        # 执行playbook
        executor = AnsibleExecutor(execution_id)
        result = executor.execute_playbook()
        
        # 发送WebSocket完成信号
        send_websocket_message(f'ansible_execution_{execution_id}', {
            'type': 'execution_completed',
            'execution_id': execution_id,
            'status': execution.status,
            'return_code': result.rc
        })
        
        executor.cleanup()
        
    except Exception as e:
        execution.status = 'failed'
        execution.stderr = str(e)
        execution.completed_at = timezone.now()
        execution.save()
        
        send_websocket_message(f'ansible_execution_{execution_id}', {
            'type': 'execution_failed',
            'execution_id': execution_id,
            'error': str(e)
        })
```

### 前端实现 (React + TypeScript)

#### 1. 类型定义

```typescript
// types/ansible.ts
export interface AnsibleInventory {
  id: number;
  name: string;
  description: string;
  content: string;
  format_type: 'ini' | 'yaml';
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface AnsiblePlaybook {
  id: number;
  name: string;
  description: string;
  content: string;
  version: string;
  is_template: boolean;
  category: string;
  parameters: Record<string, any>;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface AnsibleCredential {
  id: number;
  name: string;
  credential_type: 'ssh_key' | 'password' | 'vault';
  username: string;
  has_password: boolean;
  has_ssh_key: boolean;
  has_vault_password: boolean;
  created_by: string;
  created_at: string;
}

export interface AnsibleExecution {
  id: number;
  playbook: AnsiblePlaybook;
  inventory: AnsibleInventory;
  credential: AnsibleCredential;
  parameters: Record<string, any>;
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled';
  started_at: string | null;
  completed_at: string | null;
  stdout: string;
  stderr: string;
  return_code: number | null;
  created_by: string;
  created_at: string;
}
```

#### 2. Ansible管理组件

```tsx
// components/ansible/AnsibleDashboard.tsx
import React, { useState, useEffect } from 'react';
import { Tabs, Card, Statistic, Row, Col } from 'antd';
import { PlayCircleOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import PlaybookManager from './PlaybookManager';
import InventoryManager from './InventoryManager';
import CredentialManager from './CredentialManager';
import ExecutionList from './ExecutionList';

const AnsibleDashboard: React.FC = () => {
  const [stats, setStats] = useState({
    total_executions: 0,
    successful_executions: 0,
    failed_executions: 0,
    running_executions: 0
  });

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/ansible/stats/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('获取统计数据失败:', error);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const items = [
    {
      key: 'executions',
      label: '执行历史',
      children: <ExecutionList />
    },
    {
      key: 'playbooks',
      label: 'Playbook管理',
      children: <PlaybookManager />
    },
    {
      key: 'inventories',
      label: '主机清单',
      children: <InventoryManager />
    },
    {
      key: 'credentials',
      label: '认证凭据',
      children: <CredentialManager />
    }
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总执行次数"
              value={stats.total_executions}
              prefix={<PlayCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功执行"
              value={stats.successful_executions}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="失败执行"
              value={stats.failed_executions}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="正在运行"
              value={stats.running_executions}
              prefix={<PlayCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>
      
      <Card>
        <Tabs items={items} />
      </Card>
    </div>
  );
};

export default AnsibleDashboard;
```

## 📋 开发计划

### 第一阶段：基础框架 (Week 1)
- [ ] 后端数据模型设计和迁移
- [ ] 基础API接口开发 (CRUD操作)
- [ ] 前端路由和基础组件架构
- [ ] Ansible runner基础集成

### 第二阶段：核心功能 (Week 2)
- [ ] Playbook上传和管理功能
- [ ] Inventory文件管理
- [ ] 认证凭据安全存储
- [ ] 基础执行引擎开发

### 第三阶段：执行监控 (Week 3)
- [ ] Celery异步执行集成
- [ ] WebSocket实时监控
- [ ] 执行日志流式输出
- [ ] 状态同步和错误处理

### 第四阶段：企业功能 (Week 4)
- [ ] 模板系统和参数化配置
- [ ] 批量部署和回滚机制
- [ ] 审批流程集成
- [ ] 告警通知系统

## 🧪 测试策略

### 单元测试
- 数据模型测试
- API接口测试
- Ansible执行器测试
- 权限控制测试

### 集成测试
- 端到端playbook执行测试
- WebSocket实时监控测试
- 多环境部署测试
- 错误处理和回滚测试

### 性能测试
- 大规模主机并发部署测试
- 长时间运行playbook测试
- 资源使用优化测试

## 📚 文档计划

- **用户指南**: Ansible集成使用教程
- **API文档**: 完整的REST API文档
- **最佳实践**: Playbook编写规范和部署指南
- **故障排除**: 常见问题和解决方案

## 🔒 安全考虑

- **凭据加密**: 所有敏感信息加密存储
- **权限控制**: 基于RBAC的资源访问控制
- **审计日志**: 完整的操作审计和追踪
- **网络安全**: SSH密钥管理和安全连接
- **环境隔离**: 开发/测试/生产环境严格隔离

## 🎯 成功指标

- ✅ 支持标准Ansible playbook执行
- ✅ 实时执行监控和日志查看
- ✅ 企业级权限控制和审计
- ✅ 99%+的执行成功率
- ✅ <5秒的执行响应时间
- ✅ 支持100+主机并发部署

---

> 📝 **更新日期**: 2025年1月17日  
> 🏷️ **版本**: v1.0  
> 👤 **负责人**: AnsFlow开发团队
