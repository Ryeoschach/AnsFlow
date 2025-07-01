# 🔧 AnsFlow Jenkins 集成指南

## 概述

AnsFlow Jenkins 集成允许您将现有的 Jenkins 基础设施无缝整合到 AnsFlow CI/CD 平台中。通过统一的适配器模式，您可以：

- 在 AnsFlow 中统一管理多个 Jenkins 实例
- 使用原子化步骤构建复杂的跨工具流水线
- 实时监控 Jenkins 作业执行状态
- 获取统一的执行日志和报告

## 🚀 快速开始

### 1. 前置条件

- AnsFlow Django 服务运行在 `http://localhost:8000`
- Jenkins 服务器已配置并可访问
- Jenkins 用户具有以下权限：
  - 创建和配置作业
  - 触发构建
  - 查看构建日志
  - API 访问权限

### 2. 获取 Jenkins API Token

1. 登录 Jenkins
2. 点击用户名 → Configure
3. 滚动到 "API Token" 部分
4. 点击 "Add new Token"
5. 输入名称（如 "AnsFlow Integration"）
6. 复制生成的 token

### 3. 注册 Jenkins 工具

#### 方法一：使用管理命令

```bash
cd /Users/creed/workspace/sourceCode/AnsFlow/backend/django_service

# 测试 Jenkins 连接并注册工具
uv run python manage.py test_jenkins \
    --jenkins-url http://localhost:8080 \
    --username your_jenkins_username \
    --token your_jenkins_api_token \
    --tool-name "my-jenkins"
```

#### 方法二：使用 API

```bash
# 1. 获取认证令牌
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# 2. 注册 Jenkins 工具
curl -X POST http://localhost:8000/api/v1/cicd/tools/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-jenkins",
    "tool_type": "jenkins",
    "base_url": "http://localhost:8080",
    "username": "jenkins_user",
    "token": "jenkins_api_token",
    "project": 1,
    "config": {
      "crumb_issuer": true,
      "timeout": 30
    }
  }'
```

### 4. 创建原子步骤

```bash
# 创建示例原子步骤
uv run python manage.py create_atomic_steps --public
```

### 5. 执行流水线

```bash
# 测试流水线执行
uv run python manage.py test_pipeline_execution --tool-id 1
```

## 📋 原子步骤类型

AnsFlow 支持以下原子步骤类型，每种类型都会转换为相应的 Jenkins 脚本：

### 1. fetch_code - 代码拉取

```json
{
  "name": "Git Checkout",
  "type": "fetch_code",
  "parameters": {
    "repository_url": "https://github.com/example/repo.git",
    "branch": "main",
    "shallow_clone": true,
    "submodules": false
  }
}
```

**生成的 Jenkins 脚本：**
```groovy
stage('Git Checkout') {
    steps {
        checkout scm
        // 或者指定具体的仓库
        // git url: 'https://github.com/example/repo.git', branch: 'main'
    }
}
```

### 2. build - 构建

```json
{
  "name": "Maven Build",
  "type": "build",
  "parameters": {
    "tool": "mvn",
    "command": "clean compile",
    "profiles": ["dev"],
    "skip_tests": false
  }
}
```

**生成的 Jenkins 脚本：**
```groovy
stage('Maven Build') {
    steps {
        sh 'mvn clean compile'
    }
}
```

### 3. test - 测试

```json
{
  "name": "Unit Tests",
  "type": "test",
  "parameters": {
    "command": "mvn test",
    "coverage": true,
    "coverage_threshold": 80,
    "report_format": "xml"
  }
}
```

**生成的 Jenkins 脚本：**
```groovy
stage('Unit Tests') {
    steps {
        sh 'mvn test'
        publishHTML([
            allowMissing: false,
            alwaysLinkToLastBuild: true,
            keepAll: true,
            reportDir: 'coverage',
            reportFiles: 'index.html',
            reportName: 'Coverage Report'
        ])
    }
}
```

### 4. security_scan - 安全扫描

```json
{
  "name": "SonarQube Scan",
  "type": "security_scan",
  "parameters": {
    "tool": "sonarqube",
    "project_key": "my-project",
    "quality_gate": true
  }
}
```

### 5. deploy - 部署

```json
{
  "name": "Deploy to Staging",
  "type": "deploy",
  "parameters": {
    "environment": "staging",
    "strategy": "rolling",
    "health_check_url": "https://staging.example.com/health"
  }
}
```

### 6. notify - 通知

```json
{
  "name": "Slack Notification",
  "type": "notify",
  "parameters": {
    "channel": "#ci-cd",
    "on_success": true,
    "on_failure": true
  }
}
```

## 🔄 流水线定义格式

完整的流水线定义包含以下部分：

```json
{
  "name": "Complete CI/CD Pipeline",
  "steps": [
    {
      "name": "Checkout Code",
      "type": "fetch_code",
      "parameters": {
        "repository_url": "https://github.com/example/app.git",
        "branch": "main"
      }
    },
    {
      "name": "Build Application",
      "type": "build",
      "parameters": {
        "tool": "mvn",
        "command": "clean package -DskipTests"
      }
    },
    {
      "name": "Run Tests",
      "type": "test",
      "parameters": {
        "command": "mvn test",
        "coverage": true
      }
    },
    {
      "name": "Security Scan",
      "type": "security_scan",
      "parameters": {
        "tool": "sonarqube"
      }
    },
    {
      "name": "Deploy",
      "type": "deploy",
      "parameters": {
        "environment": "staging",
        "command": "./deploy.sh staging"
      }
    }
  ],
  "environment": {
    "JAVA_HOME": "/usr/lib/jvm/java-11-openjdk",
    "MAVEN_OPTS": "-Xmx512m",
    "BUILD_NUMBER": "${BUILD_NUMBER}"
  },
  "triggers": {
    "webhook": true,
    "schedule": "0 2 * * *"
  },
  "artifacts": [
    "target/*.jar",
    "reports/**"
  ],
  "timeout": 1800
}
```

## 🛠️ API 接口

### 工具管理

```bash
# 获取工具列表
GET /api/v1/cicd/tools/

# 获取特定工具
GET /api/v1/cicd/tools/{id}/

# 健康检查
POST /api/v1/cicd/tools/{id}/health_check/

# 执行流水线
POST /api/v1/cicd/tools/{id}/execute_pipeline/
```

### 执行管理

```bash
# 获取执行列表
GET /api/v1/cicd/executions/

# 获取执行详情
GET /api/v1/cicd/executions/{id}/

# 获取执行日志
GET /api/v1/cicd/executions/{id}/logs/

# 取消执行
POST /api/v1/cicd/executions/{id}/cancel/
```

### 原子步骤管理

```bash
# 获取步骤列表
GET /api/v1/cicd/atomic-steps/

# 创建步骤
POST /api/v1/cicd/atomic-steps/

# 获取简化步骤列表
GET /api/v1/cicd/atomic-steps/simple/
```

## 🔍 监控和日志

### 1. 实时状态监控

```python
import requests
import time

def monitor_execution(execution_id, token):
    headers = {'Authorization': f'Bearer {token}'}
    
    while True:
        response = requests.get(
            f'http://localhost:8000/api/v1/cicd/executions/{execution_id}/',
            headers=headers
        )
        
        if response.status_code == 200:
            execution = response.json()
            status = execution['status']
            print(f"当前状态: {status}")
            
            if status in ['success', 'failed', 'cancelled']:
                break
        
        time.sleep(10)
```

### 2. 获取详细日志

```bash
# 使用 curl 获取日志
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/cicd/executions/1/logs/
```

### 3. WebSocket 实时推送（FastAPI 服务）

```javascript
// 连接 WebSocket 获取实时更新
const ws = new WebSocket('ws://localhost:8001/ws/pipeline/1');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Pipeline status update:', data);
};
```

## ⚙️ 高级配置

### 1. Jenkins 特定配置

```json
{
  "config": {
    "crumb_issuer": true,        // 启用 CSRF 保护
    "timeout": 30,               // 请求超时时间（秒）
    "folder_path": "myteam",     // Jenkins 文件夹路径
    "node_label": "linux",       // 指定节点标签
    "parameters": {              // 默认参数
      "ENVIRONMENT": "staging"
    }
  }
}
```

### 2. 流水线模板

AnsFlow 支持流水线模板，可以快速创建标准化的流水线：

```python
# 使用管理命令创建模板
python manage.py create_pipeline_template \
    --name "Java Spring Boot" \
    --steps fetch_code,build,test,security_scan,deploy
```

### 3. 条件执行

```json
{
  "name": "Production Deploy",
  "type": "deploy",
  "parameters": {
    "environment": "production"
  },
  "conditions": {
    "branch": "main",
    "previous_steps_success": true,
    "manual_approval": true
  }
}
```

## 🔧 故障排除

### 1. 连接问题

**问题：** Jenkins 连接失败
```
Health check failed: Connection refused
```

**解决方案：**
1. 检查 Jenkins URL 是否正确
2. 确认 Jenkins 服务是否运行
3. 检查网络连接和防火墙设置
4. 验证 API Token 是否有效

### 2. 认证问题

**问题：** 认证失败
```
HTTP 401: Authentication required
```

**解决方案：**
1. 重新生成 Jenkins API Token
2. 检查用户名是否正确
3. 确认用户有足够的权限

### 3. 作业创建失败

**问题：** 无法创建 Jenkins 作业
```
HTTP 403: Forbidden
```

**解决方案：**
1. 检查用户是否有作业创建权限
2. 确认 Jenkins 安全配置
3. 检查 CSRF 保护设置

### 4. 执行监控问题

**问题：** 无法获取执行状态
```
Pipeline execution not found
```

**解决方案：**
1. 检查执行 ID 是否正确
2. 确认 Jenkins 作业是否成功创建
3. 检查 Jenkins 队列状态

## 📝 最佳实践

### 1. 工具配置

- 为每个环境（开发、测试、生产）配置独立的 Jenkins 实例
- 使用专用的服务账户和 API Token
- 定期更新 API Token 确保安全

### 2. 流水线设计

- 将复杂流水线拆分为多个原子步骤
- 使用参数化配置提高复用性
- 设置合理的超时时间

### 3. 监控和日志

- 启用详细日志记录
- 设置关键步骤的通知
- 定期清理历史执行记录

### 4. 安全性

- 限制 API Token 权限范围
- 使用 HTTPS 连接
- 定期审核工具访问权限

## 🔗 相关链接

- [AnsFlow API 文档](http://localhost:8000/api/schema/swagger-ui/)
- [Jenkins REST API 文档](https://www.jenkins.io/doc/book/using/remote-access-api/)
- [管理界面](http://localhost:8000/admin/cicd_integrations/)
- [完整测试脚本](./test_jenkins_integration.py)
