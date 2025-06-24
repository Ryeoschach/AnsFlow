# 🏗️ AnsFlow CI/CD 平台项目结构

## 📁 项目总体结构

```
ansflow/
├── 📋 README.md                     # 项目主文档
├── 📄 LICENSE                       # 开源协议
├── 🐳 docker-compose.yml            # 本地开发环境
├── 🐳 docker-compose.prod.yml       # 生产环境
├── 📦 requirements.txt               # Python依赖总览
├── ⚙️ .env.example                  # 环境变量示例
├── 🚀 Makefile                      # 便捷命令
├── 📊 项目说明/                      # 项目文档
│   ├── 说明文档.md                   # 原始需求文档
│   └── 技术架构分析报告.md            # 技术架构分析
├── 🔧 backend/                       # 后端服务
│   ├── django_service/               # Django 管理服务
│   ├── fastapi_service/              # FastAPI 高性能服务
│   └── shared/                       # 共享代码库
├── 🎨 frontend/                      # React 前端
├── 🚀 deployment/                    # 部署配置
│   ├── docker/                       # Docker 配置
│   ├── kubernetes/                   # K8s 部署配置
│   ├── terraform/                    # 基础设施即代码
│   └── ansible/                      # 配置管理
├── 📚 docs/                          # 项目文档
│   ├── api/                          # API 文档
│   ├── development/                  # 开发指南
│   ├── deployment/                   # 部署指南
│   └── architecture/                 # 架构设计文档
├── 🧪 tests/                         # 集成测试
├── 📊 monitoring/                    # 监控配置
└── 🔧 scripts/                       # 工具脚本
```

## 🎯 微服务架构说明

### Django 管理服务 (Port: 8000)
- **功能**: 用户认证、流水线管理、审批流程、数据分析
- **数据库**: MySQL (主要数据存储)
- **缓存**: Redis (会话、缓存)

### FastAPI 高性能服务 (Port: 8001)
- **功能**: Webhook接收、实时推送、外部工具回调
- **通信**: WebSocket, 消息队列
- **性能**: 高并发、低延迟

### React 前端 (Port: 3000)
- **功能**: 用户界面、流水线可视化、实时状态展示
- **通信**: REST API + WebSocket

### 消息队列 (RabbitMQ: Port 5672)
- **功能**: 服务间异步通信
- **队列**: 触发事件、状态更新、通知消息

## 🔧 开发环境启动

```bash
# 1. 克隆项目
git clone <repository-url>
cd ansflow

# 2. 启动开发环境
make dev-up

# 3. 初始化数据库
make db-init

# 4. 访问服务
# - 前端: http://localhost:3000
# - Django Admin: http://localhost:8000/admin
# - FastAPI Docs: http://localhost:8001/docs
# - RabbitMQ Management: http://localhost:15672
```

## 📦 技术栈总览

| 组件 | 技术选型 | 端口 | 说明 |
|------|----------|------|------|
| Django 服务 | Django + DRF | 8000 | 管理核心 |
| FastAPI 服务 | FastAPI + Uvicorn | 8001 | 高性能API |
| 前端 | React + Vite | 3000 | 用户界面 |
| 数据库 | MySQL | 3306 | 主数据存储 |
| 缓存 | Redis | 6379 | 缓存+会话 |
| 消息队列 | RabbitMQ | 5672 | 异步通信 |
| 监控 | Prometheus + Grafana | 9090/3001 | 系统监控 |

---

**创建时间**: 2025年6月24日  
**版本**: v1.0  
**基于**: 技术架构分析报告
