// AnsFlow Ansible 功能使用示例

// 1. 创建 Inventory
const inventory = await apiService.createAnsibleInventory({
  name: 'Web Servers',
  description: '生产环境 Web 服务器',
  content: `[webservers]
web1.example.com ansible_host=192.168.1.10
web2.example.com ansible_host=192.168.1.11

[databases]
db1.example.com ansible_host=192.168.1.20`,
  format_type: 'ini'
});

// 2. 创建 Playbook
const playbook = await apiService.createAnsiblePlaybook({
  name: 'Deploy Web App',
  description: '部署 Web 应用程序',
  content: `---
- hosts: webservers
  become: yes
  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present
    
    - name: Start nginx
      service:
        name: nginx
        state: started`,
  category: 'web'
});

// 3. 创建认证凭据
const credential = await apiService.createAnsibleCredential({
  name: 'SSH Key for Web Servers',
  credential_type: 'ssh',
  username: 'deploy',
  ssh_private_key_input: '-----BEGIN PRIVATE KEY-----\n...'
});

// 4. 执行 Playbook
const execution = await apiService.executeAnsiblePlaybook(playbook.id, {
  inventory_id: inventory.id,
  credential_id: credential.id,
  extra_vars: {
    app_version: '1.2.3',
    deploy_env: 'production'
  },
  tags: 'deploy',
  check_mode: false
});

// 5. 监控执行状态
const executionStatus = await apiService.getAnsibleExecution(execution.id);
console.log('执行状态:', executionStatus.status);

// 6. 获取执行日志
const logs = await apiService.getAnsibleExecutionLogs(execution.id);
console.log('执行日志:', logs.stdout);

// 7. 主机管理示例 - 支持多种认证方式

// 方法1: 使用连接测试API验证新主机
const connectionTest = await apiService.testConnection({
  ip_address: '192.168.1.10',
  username: 'deploy',
  port: 22,
  connection_type: 'ssh',
  password: 'your-password'  // 或使用 ssh_private_key
});

console.log('连接测试结果:', connectionTest.success);

if (connectionTest.success) {
  // 连接测试成功后创建主机
  const host = await apiService.createAnsibleHost({
    hostname: 'web1.example.com',
    ip_address: '192.168.1.10',
    port: 22,
    username: 'deploy',
    credential: credential.id,  // 关联认证凭据
    connection_type: 'ssh'
  });
  
  // 检查主机连通性（使用凭据认证）
  const connectivity = await apiService.checkHostConnectivity(host.id);
  console.log('连通性检查:', connectivity);
  
  // 收集主机 Facts
  const facts = await apiService.gatherHostFacts(host.id);
  console.log('主机信息:', facts);
}

// 方法2: 使用SSH密钥认证测试
const sshKeyTest = await apiService.testConnection({
  ip_address: '192.168.1.11',
  username: 'ubuntu',
  port: 22,
  connection_type: 'ssh',
  ssh_private_key: `-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...
-----END PRIVATE KEY-----`
});

console.log('SSH密钥测试结果:', sshKeyTest);

// 8. 流水线集成示例
const pipeline = await apiService.createPipeline({
  name: 'Web App Deployment Pipeline',
  description: '自动化 Web 应用部署流水线'
});

const ansibleStep = await apiService.addPipelineStep(pipeline.id, {
  name: 'Deploy with Ansible',
  step_type: 'ansible',
  ansible_playbook: playbook.id,
  ansible_inventory: inventory.id,
  ansible_credential: credential.id,
  ansible_parameters: {
    extra_vars: {
      app_version: '${BUILD_NUMBER}',
      deploy_env: 'production'
    },
    tags: 'deploy',
    verbose: true
  }
});

// 执行流水线中的 Ansible 步骤
const pipelineExecution = await apiService.executePipeline(pipeline.id, {
  parameters: {
    BUILD_NUMBER: '123'
  }
});
