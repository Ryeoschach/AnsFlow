# AnsFlow Django Management Service

> AnsFlow CI/CD平台的Django管理服务 - 负责项目管理、用户管理和系统配置

## 🚀 快速开始

### 前置要求
- Python 3.11+
- uv包管理器
- MySQL 8.0 (通过Docker运行)
- Redis (通过Docker运行)

### 安装和启动

1. **启动依赖服务** (在项目根目录)
   ```bash
   cd /Users/creed/workspace/sourceCode/AnsFlow
   docker-compose up -d mysql redis
   ```

2. **安装依赖**
   ```bash
   cd backend/django_service
   uv sync
   ```

3. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，配置数据库连接等
   ```

4. **数据库迁移**
   ```bash
   uv run python manage.py migrate --settings=ansflow.settings.development
   ```

5. **创建超级用户**
   ```bash
   uv run python manage.py createsuperuser --settings=ansflow.settings.development
   ```

6. **加载示例数据**
   ```bash
   uv run python manage.py load_sample_data --settings=ansflow.settings.development
   ```

7. **启动开发服务器**
   ```bash
   uv run python manage.py runserver 0.0.0.0:8000 --settings=ansflow.settings.development
   ```

## 📋 功能特性

- ✅ **项目管理** - 创建、配置和管理CI/CD项目
- ✅ **管道管理** - 定义和执行CI/CD管道
- ✅ **用户认证** - JWT令牌认证系统
- ✅ **权限控制** - 基于角色的访问控制
- ✅ **API文档** - 自动生成的Swagger/ReDoc文档
- ✅ **环境管理** - 开发/测试/生产环境配置

## 🌐 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| Django服务 | http://localhost:8000 | 主服务 |
| API文档 | http://localhost:8000/api/schema/swagger-ui/ | Swagger UI |
| 管理界面 | http://localhost:8000/admin/ | Django Admin |
| 健康检查 | http://localhost:8000/api/health/ | 健康状态 |

## 🔧 主要API端点

### 认证
- `POST /api/v1/auth/token/` - 获取JWT令牌
- `POST /api/v1/auth/token/refresh/` - 刷新令牌

### 项目管理
- `GET /api/v1/projects/projects/` - 项目列表
- `POST /api/v1/projects/projects/` - 创建项目
- `GET /api/v1/projects/projects/{id}/` - 项目详情

### 管道管理
- `GET /api/v1/pipelines/pipelines/` - 管道列表
- `POST /api/v1/pipelines/pipelines/` - 创建管道
- `GET /api/v1/pipelines/pipelines/{id}/` - 管道详情

## 🧪 测试

运行综合测试：
```bash
uv run python final_test.py
```

运行认证测试：
```bash
uv run python test_auth.py
```

## 📊 示例数据

系统包含以下示例数据：
- 4个示例用户 (包含不同角色)
- 3个示例项目 (电商平台、API网关、数据分析)
- 3个示例管道 (构建、部署、测试)
- 7个环境配置

## 🛠 技术栈

- **Django 4.2** - Web框架
- **Django REST Framework** - API框架
- **JWT认证** - 身份认证
- **MySQL 8.0** - 数据库
- **Redis** - 缓存和任务队列
- **Celery** - 异步任务
- **uv** - 包管理

## 📁 项目结构

```
django_service/
├── ansflow/              # Django项目配置
│   ├── settings/        # 环境配置
│   ├── urls.py          # URL路由
│   └── celery.py        # Celery配置
├── pipelines/           # 管道管理应用
├── project_management/  # 项目管理应用
├── user_management/     # 用户管理应用
├── workflow/            # 工作流应用
├── audit/               # 审计应用
├── manage.py            # Django管理命令
└── pyproject.toml       # 项目配置
```

## 🔐 示例用户

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin | 超级用户 |
| john_doe | password123 | 项目所有者 |
| jane_smith | password123 | 项目成员 |

## 📖 更多文档

- [项目完成报告](PROJECT_COMPLETION_REPORT.md) - 详细的功能说明和架构文档
- [API文档](http://localhost:8000/api/schema/swagger-ui/) - 在线API文档

## 🤝 贡献

这是AnsFlow CI/CD平台的一个组件，与以下服务协同工作：
- FastAPI高性能服务 (执行引擎)
- React前端界面 (用户界面)
- 监控和日志系统

## 📄 许可证

MIT License - 详见项目根目录的LICENSE文件

---

**状态**: ✅ 生产就绪  
**版本**: 1.0.0  
**最后更新**: 2025年6月25日