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

### React 前端 (Port: 5173)
- **功能**: 用户界面、流水线可视化、实时状态展示
- **通信**: REST API + WebSocket

### 消息队列 (RabbitMQ: Port 5672)
- **功能**: 服务间异步通信
- **队列**: 触发事件、状态更新、通知消息



## 📦 技术栈总览

| 组件 | 技术选型 | 端口 | 说明 |
|------|----------|------|------|
| Django 服务 | Django + DRF | 8000 | 管理核心 |
| FastAPI 服务 | FastAPI + Uvicorn | 8001 | 高性能API |
| 前端 | React + Vite | 5173 | 用户界面 |
| 数据库 | MySQL | 3306 | 主数据存储 |
| 缓存 | Redis | 6379 | 缓存+会话 |
| 消息队列 | RabbitMQ | 5672 | 异步通信 |
| 监控 | Prometheus + Grafana | 9090/3001 | 系统监控 |

## 🤖 自定义提示词（Prompt）

- “你是 AnsFlow 项目的智能助手，熟悉 Django、FastAPI、React 微服务架构，能根据目录结构和文档快速定位相关代码和配置。”
- “如果涉及后端管理、用户、权限、流水线、项目等复杂业务，请优先查找 backend/django_service 目录。”
- “如需高性能API、Webhook、WebSocket、实时推送等功能，请查找 backend/fastapi_service 目录。”
- “前端相关问题请定位 frontend 目录，涉及状态管理、UI 组件、API 调用等。”
- “所有脚本、批量导入、API 管理相关内容请查找 scripts 目录。”
- “如需查找测试、监控、性能优化、容器部署等内容，请优先查阅 docs/ 下的相关子目录。”
- “遇到 API 端点、认证、权限、批量导入等问题，可结合 docs/api/、scripts/API_IMPORT_GUIDE.md 和 scripts/import-apis.js。”
- “如需环境变量、依赖、启动命令、健康检查等信息，请查阅 .env.example、docs/deployment/。”
- “backend/django_service 目录与 backend/fastapi_service 目录 都是用的uv来管理虚拟环境，所以执行脚本或者命令时需要加上uv run”
- “请一直使用中文来回答问题或者添加注释等”
- “启动前后端项目我会在另外的终端来进行，你无需关心项目重启的问题”
- “暂时不考虑docker部署”
---

**创建时间**: 2025年6月24日  
**版本**: v1.0  
**基于**: 技术架构分析报告
