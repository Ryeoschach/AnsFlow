# 🚀 AnsFlow 快速启动指南

> **🎯 目标**: 5分钟内启动完整的AnsFlow CI/CD平台  
> **📋 前提**: 已安装Docker和Docker Compose

## ⚡ 一键启动

```bash
# 1. 克隆项目
git clone <repository-url>
cd ansflow

# 2. 一键启动所有服务
make dev-start

# 3. 等待服务启动完成 (约30-60秒)
# 看到 "✅ All services are ready!" 表示启动完成
```

## 🔗 访问链接

启动完成后，可以通过以下链接访问：

| 服务 | 地址 | 用途 |
|------|------|------|
| 🌐 **前端主界面** | http://localhost:3000 | 流水线管理、监控面板 |
| 🔧 **Django管理** | http://localhost:8000/admin/ | 后台管理、用户管理 |
| 📡 **FastAPI文档** | http://localhost:8001/docs | API文档、接口测试 |
| 📊 **流水线管理** | http://localhost:3000/pipelines | 创建和管理流水线 |
| 🔗 **工具集成** | http://localhost:3000/tools | Jenkins等工具配置 |

## 👤 默认账户

```
用户名: admin
密码: admin123
```

## 🎯 核心功能演示路径

### 1️⃣ 流水线管理 (5分钟体验)
```
访问: http://localhost:3000/pipelines
1. 点击"创建流水线" → 填写基本信息
2. 选择执行模式 (本地/远程/混合)
3. 点击"编辑器" → 拖拽添加原子步骤
4. 配置步骤参数 → 保存流水线
5. 点击"执行" → 查看实时执行状态
```

### 2️⃣ Jenkins工具集成 (3分钟体验)
```
访问: http://localhost:3000/tools
1. 点击"添加工具" → 选择Jenkins
2. 填写Jenkins服务器信息
3. 测试连接 → 查看工具状态
4. 浏览Jenkins作业列表
5. 查看构建历史和日志
```

### 3️⃣ 实时监控 (2分钟体验)
```
访问: http://localhost:3000/pipelines
1. 选择任意流水线 → 点击"执行"
2. 观察实时执行状态变化
3. 查看步骤执行日志
4. 体验WebSocket实时推送
```

## 🛠️ 开发模式

### 前端开发
```bash
# 启动前端开发服务器
cd frontend
npm install
npm run dev
# 访问: http://localhost:3000
```

### 后端开发
```bash
# Django开发
cd backend/django_service
python manage.py runserver 0.0.0.0:8000

# FastAPI开发
cd backend/fastapi_service
uvicorn ansflow_api.main:app --reload --host 0.0.0.0 --port 8001
```

### 数据库操作
```bash
# 创建迁移
make db-migrate

# 创建超级用户
make db-create-user

# 重置数据库
make db-reset
```

## 🔍 系统检查

运行系统状态检查脚本：
```bash
./scripts/check_system_status.sh
```

该脚本会检查：
- ✅ 所有服务运行状态
- ✅ API端点可用性  
- ✅ 数据库连接
- ✅ Redis和Celery状态
- ✅ 系统资源使用

## 🚨 常见问题

### 端口冲突
```bash
# 检查端口占用
lsof -i :3000  # 前端
lsof -i :8000  # Django
lsof -i :8001  # FastAPI

# 停止冲突服务
sudo kill -9 <PID>
```

### 容器启动失败
```bash
# 查看容器日志
docker-compose logs django
docker-compose logs fastapi
docker-compose logs frontend

# 重新构建容器
docker-compose build --no-cache
```

### 数据库问题
```bash
# 重置数据库
make db-reset

# 手动迁移
docker-compose exec django python manage.py migrate
```

### 前端页面空白
```bash
# 重新安装依赖
cd frontend
rm -rf node_modules package-lock.json
npm install

# 清理缓存
npm run build
```

## 📝 开发工作流

### 1. 功能开发
```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 启动开发环境
make dev-start

# 3. 进行代码修改
# 4. 运行测试
make test

# 5. 提交代码
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

### 2. 测试流程
```bash
# 后端测试
make test-backend

# 前端测试  
make test-frontend

# 集成测试
./scripts/check_system_status.sh
```

### 3. 代码质量
```bash
# 代码检查
make lint

# 格式化代码
make format

# 类型检查
make type-check
```

## 🎯 下一步学习

1. **📖 阅读文档**: 查看 `docs/` 目录下的详细文档
2. **🧪 运行测试**: 执行 `tests/archive/` 中的功能测试
3. **🔧 自定义开发**: 参考 `CONTRIBUTING.md` 贡献指南
4. **📊 监控数据**: 体验WebSocket实时监控功能
5. **🔌 工具集成**: 配置和测试Jenkins集成功能

## 🆘 获取帮助

- 📚 **文档**: 查看 `README.md` 和 `docs/` 目录
- 🐛 **问题报告**: 创建 GitHub Issue
- 💬 **讨论交流**: 参与 GitHub Discussions
- 📧 **直接联系**: 通过项目维护者邮箱

---

**🎉 开始你的AnsFlow CI/CD平台探索之旅！**
