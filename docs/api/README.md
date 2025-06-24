# 🔌 AnsFlow API 文档

## 📋 目录
- [API 概览](#api-概览)
- [认证机制](#认证机制)
- [Django REST API](#django-rest-api)
- [FastAPI 接口](#fastapi-接口)
- [错误处理](#错误处理)
- [接口测试](#接口测试)

## 🌐 API 概览

AnsFlow 提供两套 API 服务：

### Django REST API (端口: 8000)
- **用途**: 管理功能、用户认证、流水线 CRUD
- **文档**: http://localhost:8000/api/docs/
- **Swagger**: http://localhost:8000/api/schema/swagger-ui/
- **风格**: RESTful API

### FastAPI 接口 (端口: 8001)
- **用途**: 高性能操作、Webhook、实时通信
- **文档**: http://localhost:8001/docs
- **风格**: OpenAPI 3.0

## 🔐 认证机制

### JWT Token 认证

所有需要认证的 API 都使用 JWT Token：

```http
Authorization: Bearer <your-jwt-token>
```

#### 获取 Token

```bash
# 登录获取 Token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

响应：
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com"
  }
}
```

#### 刷新 Token

```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "your-refresh-token"
  }'
```

## 🔧 Django REST API

### 用户管理 API

#### 用户信息
```http
GET /api/users/me/
Authorization: Bearer <token>
```

响应：
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "first_name": "Admin",
  "last_name": "User",
  "is_active": true,
  "date_joined": "2025-06-24T10:00:00Z"
}
```

#### 用户列表
```http
GET /api/users/
Authorization: Bearer <token>
```

### 流水线管理 API

#### 获取流水线列表
```http
GET /api/pipelines/
Authorization: Bearer <token>
```

查询参数：
- `page`: 页码 (默认: 1)
- `page_size`: 每页数量 (默认: 20)
- `search`: 搜索关键词
- `status`: 流水线状态 (`active`, `inactive`)
- `created_by`: 创建者 ID

响应：
```json
{
  "count": 10,
  "next": "http://localhost:8000/api/pipelines/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Frontend Build Pipeline",
      "description": "Build and deploy frontend application",
      "status": "active",
      "created_by": {
        "id": 1,
        "username": "admin"
      },
      "created_at": "2025-06-24T10:00:00Z",
      "updated_at": "2025-06-24T10:30:00Z",
      "steps_count": 5,
      "last_run": {
        "id": 123,
        "status": "success",
        "started_at": "2025-06-24T12:00:00Z",
        "finished_at": "2025-06-24T12:05:00Z"
      }
    }
  ]
}
```

#### 创建流水线
```http
POST /api/pipelines/
Authorization: Bearer <token>
Content-Type: application/json
```

请求体：
```json
{
  "name": "New Pipeline",
  "description": "Pipeline description",
  "repository_url": "https://github.com/user/repo.git",
  "branch": "main",
  "trigger_events": ["push", "pull_request"],
  "steps": [
    {
      "name": "Checkout Code",
      "type": "git_checkout",
      "config": {
        "repository": "https://github.com/user/repo.git",
        "branch": "main"
      }
    },
    {
      "name": "Install Dependencies",
      "type": "shell_command",
      "config": {
        "command": "npm install"
      }
    }
  ]
}
```

#### 获取流水线详情
```http
GET /api/pipelines/{id}/
Authorization: Bearer <token>
```

#### 更新流水线
```http
PUT /api/pipelines/{id}/
Authorization: Bearer <token>
Content-Type: application/json
```

#### 删除流水线
```http
DELETE /api/pipelines/{id}/
Authorization: Bearer <token>
```

### 流水线执行 API

#### 获取执行历史
```http
GET /api/pipelines/{id}/runs/
Authorization: Bearer <token>
```

#### 手动触发执行
```http
POST /api/pipelines/{id}/run/
Authorization: Bearer <token>
Content-Type: application/json
```

请求体：
```json
{
  "branch": "main",
  "variables": {
    "ENVIRONMENT": "staging",
    "VERSION": "1.0.0"
  }
}
```

#### 获取执行详情
```http
GET /api/pipeline-runs/{run_id}/
Authorization: Bearer <token>
```

#### 取消执行
```http
POST /api/pipeline-runs/{run_id}/cancel/
Authorization: Bearer <token>
```

### 步骤库 API

#### 获取可用步骤类型
```http
GET /api/step-types/
Authorization: Bearer <token>
```

响应：
```json
{
  "results": [
    {
      "id": "git_checkout",
      "name": "Git Checkout",
      "description": "检出 Git 代码",
      "category": "source_control",
      "icon": "git",
      "config_schema": {
        "type": "object",
        "properties": {
          "repository": {
            "type": "string",
            "title": "仓库地址"
          },
          "branch": {
            "type": "string",
            "title": "分支名称",
            "default": "main"
          }
        },
        "required": ["repository"]
      }
    }
  ]
}
```

## ⚡ FastAPI 接口

### Webhook API

#### GitHub Webhook
```http
POST /api/v1/webhooks/github
Content-Type: application/json
X-GitHub-Event: push
X-GitHub-Delivery: 12345678-1234-1234-1234-123456789012
```

请求体（Push 事件）：
```json
{
  "ref": "refs/heads/main",
  "repository": {
    "id": 123456789,
    "name": "repo-name",
    "full_name": "user/repo-name",
    "clone_url": "https://github.com/user/repo-name.git"
  },
  "pusher": {
    "name": "username",
    "email": "user@example.com"
  },
  "commits": [
    {
      "id": "abc123def456",
      "message": "Update README",
      "author": {
        "name": "Author Name",
        "email": "author@example.com"
      }
    }
  ]
}
```

#### GitLab Webhook
```http
POST /api/v1/webhooks/gitlab
Content-Type: application/json
X-Gitlab-Event: Push Hook
```

### 实时 API

#### WebSocket 连接
```javascript
// 连接到实时更新
const ws = new WebSocket('ws://localhost:8001/ws/pipeline-runs/{run_id}');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Pipeline update:', data);
};

// 数据格式
{
  "type": "pipeline_status_update",
  "data": {
    "run_id": 123,
    "status": "running",
    "current_step": {
      "id": 1,
      "name": "Build",
      "status": "running",
      "started_at": "2025-06-24T12:00:00Z"
    },
    "progress": 60
  }
}
```

#### 系统状态 API
```http
GET /api/v1/system/status
```

响应：
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "rabbitmq": "healthy"
  },
  "metrics": {
    "active_pipelines": 5,
    "running_jobs": 2,
    "queue_size": 10
  }
}
```

### 外部集成 API

#### Jenkins 集成
```http
POST /api/v1/integrations/jenkins/trigger
Authorization: Bearer <token>
Content-Type: application/json
```

请求体：
```json
{
  "job_name": "build-frontend",
  "parameters": {
    "BRANCH": "main",
    "ENVIRONMENT": "staging"
  }
}
```

## ❌ 错误处理

### 错误响应格式

所有 API 错误都遵循统一格式：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求数据验证失败",
    "details": {
      "name": ["此字段不能为空"],
      "email": ["请输入有效的邮箱地址"]
    }
  },
  "timestamp": "2025-06-24T12:00:00Z",
  "path": "/api/pipelines/"
}
```

### HTTP 状态码

| 状态码 | 说明 | 示例场景 |
|--------|------|----------|
| 200 | 成功 | GET、PUT 成功 |
| 201 | 创建成功 | POST 创建资源 |
| 204 | 无内容 | DELETE 成功 |
| 400 | 请求错误 | 参数验证失败 |
| 401 | 未认证 | Token 无效或过期 |
| 403 | 无权限 | 权限不足 |
| 404 | 资源不存在 | 请求的资源未找到 |
| 409 | 冲突 | 资源已存在 |
| 422 | 实体错误 | 业务逻辑验证失败 |
| 500 | 服务器错误 | 内部服务器错误 |

### 常见错误代码

| 错误代码 | 说明 |
|----------|------|
| `VALIDATION_ERROR` | 数据验证错误 |
| `AUTHENTICATION_ERROR` | 认证失败 |
| `PERMISSION_DENIED` | 权限不足 |
| `RESOURCE_NOT_FOUND` | 资源不存在 |
| `RESOURCE_CONFLICT` | 资源冲突 |
| `RATE_LIMIT_EXCEEDED` | 请求频率超限 |
| `INTERNAL_ERROR` | 内部服务器错误 |

## 🧪 接口测试

### 使用 curl 测试

```bash
# 1. 获取认证 Token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access')

# 2. 使用 Token 访问 API
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/pipelines/

# 3. 创建流水线
curl -X POST http://localhost:8000/api/pipelines/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Pipeline",
    "description": "API Test Pipeline"
  }'
```

### 使用 Postman

1. 导入 API 集合：`docs/api/postman_collection.json`
2. 设置环境变量：
   - `base_url`: http://localhost:8000
   - `fastapi_url`: http://localhost:8001
   - `token`: {{access_token}}

### 使用 HTTPie

```bash
# 安装 HTTPie
pip install httpie

# 登录
http POST localhost:8000/api/auth/login/ username=admin password=admin123

# 使用 Token
http localhost:8000/api/pipelines/ "Authorization:Bearer <token>"

# 创建资源
http POST localhost:8000/api/pipelines/ "Authorization:Bearer <token>" \
  name="Test Pipeline" description="HTTPie Test"
```

---

📚 **相关文档**:
- [开发指南](../development/README.md)
- [部署指南](../deployment/README.md)
- [项目结构](../../PROJECT_STRUCTURE.md)
