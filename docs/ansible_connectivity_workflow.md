# AnsFlow Ansible 主机连通性测试工作流程

## 功能概述

AnsFlow 的主机管理功能提供了完整的主机连通性测试机制，支持单主机检查、批量检查和实时状态监控。

## 工作流程图

```mermaid
graph TD
    A[用户点击连通性检查按钮] --> B[前端调用 checkHostConnectivity API]
    B --> C[Django REST API 接收请求]
    C --> D[获取主机对象信息]
    D --> E[执行 Ansible ping 命令]
    E --> F{命令执行结果}
    
    F -->|成功| G[更新主机状态为 active]
    F -->|失败| H[更新主机状态为 failed]
    F -->|超时| I[更新主机状态为 failed，设置超时消息]
    
    G --> J[保存检查时间和消息]
    H --> J
    I --> J
    
    J --> K[返回检查结果给前端]
    K --> L[前端显示结果通知]
    L --> M[刷新主机列表状态]
    
    N[异步版本：使用 Celery 任务] --> O[check_host_connectivity.delay()]
    O --> P[后台执行连通性检查]
    P --> Q[更新数据库状态]
    Q --> R[可通过任务ID查询结果]
```

## 技术实现详解

### 1. 前端实现 (`/frontend/src/pages/Ansible.tsx`)

#### UI 组件
```tsx
// 连通性检查按钮
<Tooltip title="检查连通性">
  <Button 
    size="small" 
    icon={<ReloadOutlined />}
    onClick={() => handleCheckConnectivity(record.id)}
  />
</Tooltip>
```

#### 事件处理器
```tsx
const handleCheckConnectivity = async (hostId: number) => {
  try {
    const result = await apiService.checkHostConnectivity(hostId);
    if (result.success) {
      message.success(`主机连接成功`);
    } else {
      message.error(`主机连接失败: ${result.message}`);
    }
    fetchHosts(); // 刷新主机状态
  } catch (error) {
    message.error('检查连通性失败');
  }
};
```

#### 状态显示
```tsx
// 主机状态列
{
  title: '状态',
  dataIndex: 'status',
  key: 'status',
  render: (status: string) => (
    <Tag color={getStatusColor(status)}>
      {status === 'active' ? '活跃' : 
       status === 'failed' ? '失败' : 
       status === 'inactive' ? '非活跃' : '未知'}
    </Tag>
  )
}
```

### 2. API 服务层 (`/frontend/src/services/api.ts`)

```typescript
async checkHostConnectivity(id: number): Promise<HostConnectivityResult> {
  const response = await this.api.post(`/ansible/hosts/${id}/check_connectivity/`)
  return response.data
}
```

### 3. 后端 API 实现 (`/backend/django_service/ansible_integration/views.py`)

#### 同步检查版本
```python
@action(detail=True, methods=['post'])
def check_connectivity(self, request, pk=None):
    """检查主机连通性"""
    host = self.get_object()
    
    try:
        # 使用ansible命令检查连通性
        result = subprocess.run([
            'ansible', f'{host.ip_address}',
            '-m', 'ping',
            '-u', host.username,
            '-p', str(host.port),
            '--timeout=10'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            host.status = 'active'
            host.check_message = '连接成功'
        else:
            host.status = 'failed'
            host.check_message = result.stderr or result.stdout
            
        host.last_check = timezone.now()
        host.save()
        
        return Response({
            'success': result.returncode == 0,
            'status': host.status,
            'message': host.check_message,
            'checked_at': host.last_check
        })
        
    except subprocess.TimeoutExpired:
        host.status = 'failed'
        host.check_message = '连接超时'
        host.last_check = timezone.now()
        host.save()
        
        return Response({
            'success': False,
            'status': 'failed',
            'message': '连接超时',
            'checked_at': host.last_check
        })
```

### 4. 异步任务实现 (`/backend/django_service/ansible_integration/tasks.py`)

```python
@shared_task
def check_host_connectivity(host_id):
    """异步检查主机连通性"""
    try:
        from .models import AnsibleHost
        host = AnsibleHost.objects.get(id=host_id)
        
        logger.info(f"开始检查主机连通性: {host.hostname} ({host.ip_address})")
        
        # 使用ansible ping模块检查连通性
        result = subprocess.run([
            'ansible', f'{host.ip_address}',
            '-m', 'ping',
            '-u', host.username,
            '-p', str(host.port),
            '--timeout=10'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            host.status = 'active'
            host.check_message = '连接成功'
            success = True
        else:
            host.status = 'failed'
            host.check_message = result.stderr or result.stdout
            success = False
            
        host.last_check = timezone.now()
        host.save()
        
        return {
            'host_id': host_id,
            'hostname': host.hostname,
            'success': success,
            'status': host.status,
            'message': host.check_message
        }
        
    except Exception as e:
        logger.error(f"主机连通性检查失败: {str(e)}")
        return {
            'host_id': host_id,
            'success': False,
            'message': str(e)
        }
```

## 核心特性

### 1. 实时状态更新
- 检查完成后立即更新数据库状态
- 前端自动刷新显示最新状态
- 支持状态颜色标识（绿色=活跃，红色=失败，灰色=未知）

### 2. 超时处理
- 命令执行超时：15秒
- Ansible 内部超时：10秒
- 超时后自动标记为失败状态

### 3. 错误处理
- 捕获 subprocess 执行异常
- 记录详细的错误信息
- 前端友好的错误提示

### 4. 批量操作支持
```python
@action(detail=False, methods=['post'])
def batch_check(self, request):
    """批量检查主机连通性"""
    host_ids = request.data.get('host_ids', [])
    
    results = []
    for host in hosts:
        # 使用异步任务进行批量检查
        task_result = check_host_connectivity.delay(host.id)
        results.append({
            'host_id': host.id,
            'hostname': host.hostname,
            'task_id': task_result.id,
            'message': '连通性检查已启动'
        })
```

## 状态码说明

### 主机状态
- `active`: 主机连接正常，可以执行 Ansible 任务
- `failed`: 主机连接失败，无法建立 SSH 连接
- `inactive`: 主机暂时不可用（手动设置）
- `unknown`: 未进行过连通性检查

### 检查消息示例
- **成功**: "连接成功"
- **失败**: SSH 错误信息或 Ansible 错误输出
- **超时**: "连接超时"
- **异常**: 具体的异常信息

## 最佳实践

### 1. 主机配置建议
```python
# 创建主机时的推荐配置
host = AnsibleHost(
    hostname='web01.example.com',
    ip_address='192.168.1.10',
    port=22,  # 标准SSH端口
    username='deploy',  # 部署用户
    connection_type='ssh',
    variables={
        'ansible_ssh_common_args': '-o StrictHostKeyChecking=no',
        'ansible_python_interpreter': '/usr/bin/python3'
    }
)
```

### 2. 网络配置要求
- SSH 端口必须开放
- 防火墙允许来源IP访问
- SSH 密钥认证已配置
- 目标主机有Python环境

### 3. 监控建议
- 定期执行批量连通性检查
- 监控失败主机的错误信息
- 设置告警机制（连续失败时通知）

## 故障排除

### 常见问题及解决方案

#### 1. SSH 连接被拒绝
```
错误：ssh: connect to host 192.168.1.10 port 22: Connection refused
解决：检查目标主机SSH服务状态，确认端口开放
```

#### 2. 认证失败
```
错误：Permission denied (publickey,password)
解决：检查SSH密钥配置或用户名密码
```

#### 3. Python 解释器找不到
```
错误：/usr/bin/python: not found
解决：在主机变量中设置正确的 ansible_python_interpreter
```

#### 4. 连接超时
```
错误：连接超时
解决：检查网络连通性，调整超时时间配置
```

### 调试技巧

#### 1. 手动测试 Ansible 连接
```bash
# 在服务器上手动执行测试
ansible 192.168.1.10 -m ping -u deploy -p 22
```

#### 2. 查看详细日志
```python
# 在 Django 日志中查看详细信息
logger.info(f"检查主机: {host.hostname}")
logger.error(f"连接失败: {result.stderr}")
```

#### 3. 前端调试
```javascript
// 浏览器控制台查看API响应
console.log('连通性检查结果:', result);
```

这个连通性测试系统提供了完整的主机管理和监控能力，是 AnsFlow 自动化平台的重要组成部分。通过实时状态监控和详细的错误信息，运维人员可以快速识别和解决主机连接问题。
