# AnsFlow 后端 API 接口文档

## 基础信息

**Base URL**: `http://localhost:8000/api/v1/`  
**认证方式**: JWT Token  
**Content-Type**: `application/json`

## 认证 API

### 1. 获取Token
- **URL**: `/api/v1/auth/token/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **响应**:
  ```json
  {
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token"
  }
  ```

### 2. 刷新Token
- **URL**: `/api/v1/auth/token/refresh/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "refresh": "jwt_refresh_token"
  }
  ```

### 3. 验证Token
- **URL**: `/api/v1/auth/token/verify/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "token": "jwt_access_token"
  }
  ```

## 流水线管理 API (Pipelines)

### 1. 流水线列表
- **URL**: `/api/v1/pipelines/pipelines/`
- **方法**: GET
- **查询参数**:
  - `project`: 项目ID
  - `status`: 流水线状态
- **响应**: 流水线列表

### 2. 创建流水线
- **URL**: `/api/v1/pipelines/pipelines/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "name": "流水线名称",
    "description": "描述",
    "project": 1,
    "execution_mode": "local|remote|hybrid",
    "execution_tool": 1,
    "tool_job_name": "jenkins_job_name",
    "is_active": true,
    "steps": [
      {
        "name": "步骤名称",
        "step_type": "fetch_code|build|test|deploy|ansible|custom",
        "description": "步骤描述",
        "parameters": {},
        "order": 1,
        "is_active": true,
        "git_credential": 1
      }
    ]
  }
  ```

### 3. 获取流水线详情
- **URL**: `/api/v1/pipelines/pipelines/{id}/`
- **方法**: GET
- **响应**: 完整的流水线信息（包含步骤）

### 4. 更新流水线
- **URL**: `/api/v1/pipelines/pipelines/{id}/`
- **方法**: PUT/PATCH
- **请求参数**: 同创建流水线

### 5. 删除流水线
- **URL**: `/api/v1/pipelines/pipelines/{id}/`
- **方法**: DELETE

### 6. 运行流水线
- **URL**: `/api/v1/pipelines/pipelines/{id}/run/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "parameters": {
      "custom_param": "value"
    }
  }
  ```

### 7. 同步到CI/CD工具
- **URL**: `/api/v1/pipelines/pipelines/{id}/sync_to_tool/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "tool_id": 1
  }
  ```

### 8. 获取工具映射
- **URL**: `/api/v1/pipelines/pipelines/{id}/tool_mappings/`
- **方法**: GET

### 9. 触发外部构建
- **URL**: `/api/v1/pipelines/pipelines/{id}/trigger_external_build/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "tool_id": 1,
    "parameters": {}
  }
  ```

## 项目管理 API (Projects)

### 1. 项目列表
- **URL**: `/api/v1/projects/projects/`
- **方法**: GET

### 2. 创建项目
- **URL**: `/api/v1/projects/projects/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "name": "项目名称",
    "description": "项目描述",
    "repository_url": "https://github.com/user/repo.git",
    "settings": {}
  }
  ```

### 3. 项目详情
- **URL**: `/api/v1/projects/projects/{id}/`
- **方法**: GET

### 4. 更新项目
- **URL**: `/api/v1/projects/projects/{id}/`
- **方法**: PUT/PATCH

### 5. 删除项目
- **URL**: `/api/v1/projects/projects/{id}/`
- **方法**: DELETE

### 环境管理

### 1. 环境列表
- **URL**: `/api/v1/projects/environments/`
- **方法**: GET

### 2. 创建环境
- **URL**: `/api/v1/projects/environments/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "name": "环境名称",
    "project": 1,
    "environment_type": "development|testing|staging|production",
    "configuration": {}
  }
  ```

## CI/CD 集成 API

### 1. CI/CD工具列表
- **URL**: `/api/v1/cicd/tools/`
- **方法**: GET

### 2. 创建CI/CD工具
- **URL**: `/api/v1/cicd/tools/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "name": "工具名称",
    "tool_type": "jenkins|gitlab|github",
    "base_url": "http://jenkins.example.com",
    "authentication": {
      "username": "admin",
      "password": "secret"
    },
    "configuration": {}
  }
  ```

### 3. Git凭据管理

#### 获取Git凭据列表
- **URL**: `/api/v1/cicd/git-credentials/`
- **方法**: GET

#### 创建Git凭据
- **URL**: `/api/v1/cicd/git-credentials/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "name": "凭据名称",
    "platform": "github|gitlab|bitbucket|other",
    "server_url": "https://github.com",
    "username": "用户名",
    "password": "密码或token",
    "ssh_private_key": "SSH私钥"
  }
  ```

### 4. 流水线执行

#### 执行列表
- **URL**: `/api/v1/cicd/executions/`
- **方法**: GET

#### 获取执行详情
- **URL**: `/api/v1/cicd/executions/{id}/`
- **方法**: GET

## Ansible 集成 API

### 1. Playbook管理

#### 获取Playbook列表
- **URL**: `/api/v1/ansible/playbooks/`
- **方法**: GET

#### 创建Playbook
- **URL**: `/api/v1/ansible/playbooks/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "name": "Playbook名称",
    "description": "描述",
    "content": "playbook yaml内容",
    "variables": {},
    "tags": ["tag1", "tag2"]
  }
  ```

#### 执行Playbook
- **URL**: `/api/v1/ansible/playbooks/{id}/execute/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "inventory_id": 1,
    "credential_id": 1,
    "variables": {},
    "tags": ["specific_tag"],
    "limit": "host_pattern"
  }
  ```

### 2. Inventory管理

#### 获取Inventory列表
- **URL**: `/api/v1/ansible/inventories/`
- **方法**: GET

#### 创建Inventory
- **URL**: `/api/v1/ansible/inventories/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "name": "Inventory名称",
    "description": "描述",
    "content": "inventory内容",
    "inventory_type": "static|dynamic"
  }
  ```

### 3. 凭据管理

#### 获取凭据列表
- **URL**: `/api/v1/ansible/credentials/`
- **方法**: GET

#### 创建凭据
- **URL**: `/api/v1/ansible/credentials/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "name": "凭据名称",
    "credential_type": "ssh_key|password|vault",
    "username": "用户名",
    "password": "密码",
    "ssh_private_key": "SSH私钥",
    "vault_password": "Vault密码"
  }
  ```

### 4. 执行管理

#### 获取执行列表
- **URL**: `/api/v1/ansible/executions/`
- **方法**: GET

#### 获取执行日志
- **URL**: `/api/v1/ansible/executions/{id}/logs/`
- **方法**: GET

#### 取消执行
- **URL**: `/api/v1/ansible/executions/{id}/cancel/`
- **方法**: POST

### 5. 统计信息

#### 获取Ansible统计
- **URL**: `/api/v1/ansible/stats/overview/`
- **方法**: GET

#### 获取最近执行
- **URL**: `/api/v1/ansible/executions/recent/`
- **方法**: GET

## 用户管理 API

### 1. 用户列表
- **URL**: `/api/v1/auth/users/`
- **方法**: GET

### 2. 创建用户
- **URL**: `/api/v1/auth/users/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "username": "用户名",
    "email": "email@example.com",
    "password": "密码",
    "first_name": "名",
    "last_name": "姓"
  }
  ```

### 3. 用户详情
- **URL**: `/api/v1/auth/users/{id}/`
- **方法**: GET

## 分析统计 API

### 1. 执行统计
- **URL**: `/api/v1/analytics/execution-stats/`
- **方法**: GET

### 2. 执行趋势
- **URL**: `/api/v1/analytics/execution-trends/`
- **方法**: GET

### 3. 流水线统计
- **URL**: `/api/v1/analytics/pipeline-stats/`
- **方法**: GET

### 4. 最近执行
- **URL**: `/api/v1/analytics/recent-executions/`
- **方法**: GET

## 健康检查 API

### 1. 总体健康检查
- **URL**: `/health/`
- **方法**: GET
- **响应**:
  ```json
  {
    "status": "healthy",
    "service": "AnsFlow Django Service",
    "version": "1.0.0"
  }
  ```

### 2. 流水线服务健康检查
- **URL**: `/api/v1/pipelines/health/`
- **方法**: GET

## API文档

### 1. OpenAPI Schema
- **URL**: `/api/schema/`
- **方法**: GET

### 2. Swagger UI
- **URL**: `/api/schema/swagger-ui/`
- **方法**: GET

### 3. ReDoc
- **URL**: `/api/schema/redoc/`
- **方法**: GET

## 错误码说明

- **200**: 成功
- **201**: 创建成功
- **400**: 请求参数错误
- **401**: 未认证
- **403**: 权限不足
- **404**: 资源不存在
- **500**: 服务器内部错误

## 使用示例

### 1. 获取认证Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

### 2. 创建流水线
```bash
curl -X POST http://localhost:8000/api/v1/pipelines/pipelines/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试流水线",
    "description": "这是一个测试流水线",
    "project": 1,
    "execution_mode": "local",
    "is_active": true,
    "steps": [
      {
        "name": "代码拉取",
        "step_type": "fetch_code",
        "description": "从Git拉取代码",
        "parameters": {
          "repository": "https://github.com/user/repo.git",
          "branch": "main"
        },
        "order": 1,
        "is_active": true
      }
    ]
  }'
```

### 3. 运行流水线
```bash
curl -X POST http://localhost:8000/api/v1/pipelines/pipelines/1/run/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {}}'
```

### 4. 创建Ansible Playbook
```bash
curl -X POST http://localhost:8000/api/v1/ansible/playbooks/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "部署应用",
    "description": "部署Web应用",
    "content": "---\n- hosts: all\n  tasks:\n    - name: Install nginx\n      package:\n        name: nginx\n        state: present",
    "variables": {
      "app_version": "1.0.0"
    }
  }'
```

## 步骤类型说明

### 支持的步骤类型
1. **fetch_code**: 代码拉取
   - 参数: `repository`, `branch`, `credentials`
2. **build**: 构建
   - 参数: `build_command`, `build_tool`, `build_args`
3. **test**: 测试
   - 参数: `test_command`, `test_framework`, `coverage`
4. **security_scan**: 安全扫描
   - 参数: `scan_tool`, `scan_targets`, `severity_threshold`
5. **deploy**: 部署
   - 参数: `deploy_target`, `deploy_strategy`, `rollback_on_failure`
6. **ansible**: Ansible自动化
   - 参数: `playbook_id`, `inventory_id`, `credential_id`, `variables`
7. **notify**: 通知
   - 参数: `notification_type`, `recipients`, `message`
8. **custom**: 自定义
   - 参数: `command`, `environment`, `timeout`

## 注意事项

1. 所有需要认证的API都需要在请求头中包含JWT Token
2. POST/PUT请求需要设置`Content-Type: application/json`
3. 时间格式使用ISO 8601标准
4. 分页使用标准的`page`和`page_size`参数
5. 搜索和过滤参数请参考各API的查询参数说明
