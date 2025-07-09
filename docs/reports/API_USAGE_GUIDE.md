# AnsFlow API 使用指南

## 快速开始

### 1. 环境设置
```bash
# 后端服务地址
export ANSFLOW_API_BASE="http://localhost:8000/api/v1"

# 认证Token（获取后设置）
export ANSFLOW_TOKEN="your_jwt_token_here"
```

### 2. 获取认证Token
```bash
# 登录获取Token
curl -X POST ${ANSFLOW_API_BASE}/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_password"
  }' | jq -r '.access'
```

## 完整工作流示例

### 1. 创建项目
```bash
# 创建项目
PROJECT_ID=$(curl -X POST ${ANSFLOW_API_BASE}/projects/projects/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Web应用项目",
    "description": "一个示例Web应用项目",
    "repository_url": "https://github.com/user/webapp.git",
    "settings": {
      "build_tool": "npm",
      "test_framework": "jest"
    }
  }' | jq -r '.id')

echo "创建的项目ID: ${PROJECT_ID}"
```

### 2. 创建Git凭据
```bash
# 创建Git凭据（如果需要私有仓库访问）
GIT_CREDENTIAL_ID=$(curl -X POST ${ANSFLOW_API_BASE}/cicd/git-credentials/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GitHub Personal Token",
    "platform": "github",
    "server_url": "https://github.com",
    "username": "your_username",
    "password": "ghp_your_personal_access_token"
  }' | jq -r '.id')

echo "创建的Git凭据ID: ${GIT_CREDENTIAL_ID}"
```

### 3. 创建Ansible资源
```bash
# 创建Ansible凭据
ANSIBLE_CREDENTIAL_ID=$(curl -X POST ${ANSFLOW_API_BASE}/ansible/credentials/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "服务器SSH密钥",
    "credential_type": "ssh_key",
    "username": "deploy",
    "ssh_private_key": "-----BEGIN OPENSSH PRIVATE KEY-----\n...\n-----END OPENSSH PRIVATE KEY-----"
  }' | jq -r '.id')

# 创建Inventory
INVENTORY_ID=$(curl -X POST ${ANSFLOW_API_BASE}/ansible/inventories/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "生产服务器",
    "description": "生产环境服务器清单",
    "content": "[webservers]\nweb1.example.com\nweb2.example.com\n\n[dbservers]\ndb1.example.com",
    "inventory_type": "static"
  }' | jq -r '.id')

# 创建Playbook
PLAYBOOK_ID=$(curl -X POST ${ANSFLOW_API_BASE}/ansible/playbooks/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "部署Web应用",
    "description": "部署Node.js Web应用到生产环境",
    "category": "deployment",
    "content": "---\n- hosts: webservers\n  become: yes\n  tasks:\n    - name: 停止应用服务\n      systemd:\n        name: webapp\n        state: stopped\n    - name: 更新应用代码\n      git:\n        repo: \"{{ app_repo }}\"\n        dest: /opt/webapp\n        version: \"{{ app_version }}\"\n    - name: 安装依赖\n      npm:\n        path: /opt/webapp\n        production: yes\n    - name: 启动应用服务\n      systemd:\n        name: webapp\n        state: started\n        enabled: yes",
    "variables": {
      "app_repo": "https://github.com/user/webapp.git",
      "app_version": "main"
    }
  }' | jq -r '.id')
```

### 4. 创建完整流水线
```bash
# 创建包含多个步骤的流水线
PIPELINE_ID=$(curl -X POST ${ANSFLOW_API_BASE}/pipelines/pipelines/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Web应用CI/CD流水线",
    "description": "完整的Web应用CI/CD流水线",
    "project": '${PROJECT_ID}',
    "execution_mode": "local",
    "is_active": true,
    "steps": [
      {
        "name": "代码拉取",
        "step_type": "fetch_code",
        "description": "从Git仓库拉取最新代码",
        "parameters": {
          "repository": "https://github.com/user/webapp.git",
          "branch": "main",
          "clone_depth": 1
        },
        "order": 1,
        "is_active": true,
        "git_credential": '${GIT_CREDENTIAL_ID}'
      },
      {
        "name": "安装依赖",
        "step_type": "build",
        "description": "安装npm依赖包",
        "parameters": {
          "build_tool": "npm",
          "build_command": "npm ci",
          "working_directory": "./",
          "cache_dependencies": true
        },
        "order": 2,
        "is_active": true
      },
      {
        "name": "代码构建",
        "step_type": "build",
        "description": "构建生产版本",
        "parameters": {
          "build_tool": "npm",
          "build_command": "npm run build",
          "working_directory": "./",
          "artifact_path": "dist/"
        },
        "order": 3,
        "is_active": true
      },
      {
        "name": "单元测试",
        "step_type": "test",
        "description": "运行单元测试",
        "parameters": {
          "test_framework": "jest",
          "test_command": "npm test",
          "coverage": true,
          "test_results_path": "test-results.xml"
        },
        "order": 4,
        "is_active": true
      },
      {
        "name": "安全扫描",
        "step_type": "security_scan",
        "description": "扫描安全漏洞",
        "parameters": {
          "scan_tool": "npm audit",
          "scan_command": "npm audit --audit-level moderate",
          "fail_on_critical": true
        },
        "order": 5,
        "is_active": true
      },
      {
        "name": "部署到生产环境",
        "step_type": "ansible",
        "description": "使用Ansible部署到生产服务器",
        "parameters": {
          "playbook_id": '${PLAYBOOK_ID}',
          "inventory_id": '${INVENTORY_ID}',
          "credential_id": '${ANSIBLE_CREDENTIAL_ID}',
          "variables": {
            "app_version": "${BUILD_NUMBER}",
            "deploy_env": "production"
          },
          "tags": ["deploy"]
        },
        "order": 6,
        "is_active": true
      },
      {
        "name": "部署通知",
        "step_type": "notify",
        "description": "发送部署成功通知",
        "parameters": {
          "notification_type": "slack",
          "webhook_url": "https://hooks.slack.com/services/...",
          "message": "🚀 Web应用已成功部署到生产环境",
          "channels": ["#deployments", "#team"]
        },
        "order": 7,
        "is_active": true
      }
    ]
  }' | jq -r '.id')

echo "创建的流水线ID: ${PIPELINE_ID}"
```

### 5. 运行流水线
```bash
# 运行流水线
EXECUTION_ID=$(curl -X POST ${ANSFLOW_API_BASE}/pipelines/pipelines/${PIPELINE_ID}/run/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "branch": "main",
      "environment": "production",
      "notify_on_failure": true
    }
  }' | jq -r '.id')

echo "流水线执行ID: ${EXECUTION_ID}"
```

### 6. 监控执行状态
```bash
# 查看执行状态
curl -X GET ${ANSFLOW_API_BASE}/cicd/executions/${EXECUTION_ID}/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" | jq '.'

# 实时监控执行状态
while true; do
  STATUS=$(curl -s -X GET ${ANSFLOW_API_BASE}/cicd/executions/${EXECUTION_ID}/ \
    -H "Authorization: Bearer ${ANSFLOW_TOKEN}" | jq -r '.status')
  echo "当前状态: ${STATUS}"
  
  if [[ "${STATUS}" == "completed" || "${STATUS}" == "failed" ]]; then
    break
  fi
  
  sleep 5
done
```

## 高级用法

### 1. 批量操作
```bash
# 批量创建多个环境
for env in development staging production; do
  curl -X POST ${ANSFLOW_API_BASE}/projects/environments/ \
    -H "Authorization: Bearer ${ANSFLOW_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
      "name": "'${env}'环境",
      "project": '${PROJECT_ID}',
      "environment_type": "'${env}'",
      "configuration": {
        "database_url": "postgresql://user:pass@'${env}'-db:5432/webapp",
        "redis_url": "redis://'${env}'-redis:6379"
      }
    }'
done
```

### 2. 条件执行
```bash
# 创建带条件的流水线步骤
curl -X POST ${ANSFLOW_API_BASE}/pipelines/pipelines/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "条件部署流水线",
    "project": '${PROJECT_ID}',
    "steps": [
      {
        "name": "条件部署",
        "step_type": "custom",
        "parameters": {
          "condition": "branch == \"main\"",
          "command": "echo \"部署到生产环境\"",
          "else_command": "echo \"跳过生产部署\""
        }
      }
    ]
  }'
```

### 3. 并行执行
```bash
# 创建并行测试步骤
curl -X POST ${ANSFLOW_API_BASE}/pipelines/pipelines/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "并行测试流水线",
    "project": '${PROJECT_ID}',
    "steps": [
      {
        "name": "单元测试",
        "step_type": "test",
        "parameters": {
          "test_command": "npm run test:unit",
          "parallel_group": "tests"
        }
      },
      {
        "name": "集成测试",
        "step_type": "test",
        "parameters": {
          "test_command": "npm run test:integration",
          "parallel_group": "tests"
        }
      },
      {
        "name": "E2E测试",
        "step_type": "test",
        "parameters": {
          "test_command": "npm run test:e2e",
          "parallel_group": "tests"
        }
      }
    ]
  }'
```

## 错误处理

### 1. 常见错误及解决方案

#### 认证错误 (401)
```bash
# 检查token是否过期
curl -X POST ${ANSFLOW_API_BASE}/auth/token/verify/ \
  -H "Content-Type: application/json" \
  -d '{"token": "'${ANSFLOW_TOKEN}'"}'

# 如果过期，使用refresh token获取新token
NEW_TOKEN=$(curl -X POST ${ANSFLOW_API_BASE}/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "'${REFRESH_TOKEN}'"}' | jq -r '.access')
```

#### 参数验证错误 (400)
```bash
# 详细的错误信息会在响应中返回
curl -X POST ${ANSFLOW_API_BASE}/pipelines/pipelines/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}' | jq '.errors'
```

### 2. 调试技巧
```bash
# 启用详细输出
curl -v -X GET ${ANSFLOW_API_BASE}/pipelines/pipelines/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}"

# 使用jq格式化JSON响应
curl -X GET ${ANSFLOW_API_BASE}/pipelines/pipelines/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" | jq '.'

# 保存响应到文件进行分析
curl -X GET ${ANSFLOW_API_BASE}/pipelines/pipelines/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" \
  -o pipelines_response.json
```

## 性能优化

### 1. 分页处理
```bash
# 使用分页获取大量数据
curl -X GET "${ANSFLOW_API_BASE}/pipelines/pipelines/?page=1&page_size=20" \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}"
```

### 2. 字段过滤
```bash
# 只获取需要的字段
curl -X GET "${ANSFLOW_API_BASE}/pipelines/pipelines/?fields=id,name,status" \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}"
```

### 3. 条件查询
```bash
# 根据条件过滤数据
curl -X GET "${ANSFLOW_API_BASE}/pipelines/pipelines/?project=${PROJECT_ID}&status=active" \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}"
```

## 集成示例

### 1. 与Jenkins集成
```bash
# 创建Jenkins工具
JENKINS_TOOL_ID=$(curl -X POST ${ANSFLOW_API_BASE}/cicd/tools/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jenkins生产环境",
    "tool_type": "jenkins",
    "base_url": "http://jenkins.company.com:8080",
    "authentication": {
      "username": "admin",
      "api_token": "your_jenkins_api_token"
    },
    "configuration": {
      "verify_ssl": false,
      "timeout": 300
    }
  }' | jq -r '.id')

# 同步流水线到Jenkins
curl -X POST ${ANSFLOW_API_BASE}/pipelines/pipelines/${PIPELINE_ID}/sync_to_tool/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"tool_id": '${JENKINS_TOOL_ID}'}'
```

### 2. Webhook集成
```bash
# 设置Webhook触发器
curl -X POST ${ANSFLOW_API_BASE}/pipelines/pipelines/${PIPELINE_ID}/webhooks/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_type": "git_push",
    "source": "github",
    "conditions": {
      "branch": "main",
      "file_patterns": ["src/**", "package.json"]
    }
  }'
```

### 3. 监控集成
```bash
# 获取执行统计
curl -X GET ${ANSFLOW_API_BASE}/analytics/execution-stats/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}"

# 获取最近执行记录
curl -X GET ${ANSFLOW_API_BASE}/analytics/recent-executions/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}"
```

## 备份和恢复

### 1. 导出配置
```bash
# 导出所有流水线配置
curl -X GET ${ANSFLOW_API_BASE}/pipelines/pipelines/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" > pipelines_backup.json

# 导出项目配置
curl -X GET ${ANSFLOW_API_BASE}/projects/projects/ \
  -H "Authorization: Bearer ${ANSFLOW_TOKEN}" > projects_backup.json
```

### 2. 导入配置
```bash
# 从备份文件恢复流水线
cat pipelines_backup.json | jq -r '.results[]' | while read pipeline; do
  curl -X POST ${ANSFLOW_API_BASE}/pipelines/pipelines/ \
    -H "Authorization: Bearer ${ANSFLOW_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${pipeline}"
done
```

## 最佳实践

### 1. 安全性
- 定期轮换API Token
- 使用HTTPS进行API调用
- 敏感信息使用环境变量存储
- 限制API访问权限

### 2. 可靠性
- 实现重试机制
- 添加超时设置
- 监控API响应时间
- 记录详细的调用日志

### 3. 性能
- 使用分页处理大数据集
- 缓存频繁访问的数据
- 使用字段过滤减少传输量
- 并行处理独立的API调用

### 4. 维护性
- 版本化API调用脚本
- 文档化自定义集成
- 使用配置文件管理环境差异
- 实现自动化测试
