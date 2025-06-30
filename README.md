# 🚀 AnsFlow CI/CD 平台

> 基于微服务架构的下一代企业级 CI/CD 平台，致力于通过原子化流水线设计和智能化管理，提供灵活、高效、安全的持续集成与交付解决方案。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18+-blue.svg)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![WebSocket](https://img.shields.io/badge/websocket-realtime-green.svg)](https://websockets.spec.whatwg.org/)

## 🎯 当前项目状态 

**📅 最新更新**: 2025年6月30日 | **🚧 当前阶段**: Phase 3 - Jenkins工具集成完善

- ✅ **Phase 1 完成**: 核心执行引擎 (7种原子步骤，Celery异步执行)
- ✅ **Phase 2 完成**: WebSocket实时监控系统 (<100ms延迟，完整前后端集成)
- ✅ **Jenkins集成专项**: 工具状态系统、作业管理、构建监控、智能状态同步
- 🚧 **Phase 3 进行中**: 多CI/CD工具集成 + 可视化流水线编辑器
- 🎯 **下一步**: GitLab CI & GitHub Actions 集成 (预计2周)

## ✨ 核心特性

### 🎯 原子化流水线设计
- **原子步骤库**: 预定义的可复用构建块
- **可视化编排**: 拖拽式流水线构建
- **动态组合**: 灵活的步骤组装和配置

### 🏗️ 微服务架构
- **Django 管理服务**: 用户管理、流水线编排、审批流程
- **FastAPI 高性能服务**: Webhook 处理、实时推送、外部集成
- **消息队列通信**: 基于 RabbitMQ 的异步解耦

### 🔌 智能集成适配
- **多样化触发源**: Git 仓库、定时任务、手动触发、外部 API
- **丰富的工具集成**: Jenkins、GitLab CI、Docker、Kubernetes
- **灵活的通知机制**: 邮件、Slack、企业微信、自定义 Webhook

### 🛡️ 企业级安全
- **细粒度权限控制**: 基于角色的访问控制 (RBAC)
- **多层审批流程**: 可配置的审批工作流
- **操作审计**: 完整的操作日志和追踪

## 🏗️ 技术架构

```mermaid
graph TB
    subgraph "前端层"
        A[React Frontend<br/>端口: 3000]
    end
    
    subgraph "API网关层"
        B[Nginx<br/>负载均衡]
    end
    
    subgraph "微服务层"
        C[Django Service<br/>管理核心<br/>端口: 8000]
        D[FastAPI Service<br/>高性能API<br/>端口: 8001]
    end
    
    subgraph "消息队列"
        E[RabbitMQ<br/>端口: 5672]
    end
    
    subgraph "数据存储层"
        F[MySQL<br/>端口: 3306]
        G[Redis<br/>端口: 6379]
    end
    
    subgraph "监控层"
        H[Prometheus<br/>端口: 9090]
        I[Grafana<br/>端口: 3001]
    end
    
    A --> B
    B --> C
    B --> D
    C <--> E
    D <--> E
    C --> F
    C --> G
    D --> G
    C --> H
    D --> H
    H --> I
```

## 🚀 快速开始

### 环境要求

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Node.js**: 16+ (本地开发)
- **Python**: 3.8+ (本地开发)

### 一键启动

```bash
# 1. 克隆项目
git clone https://github.com/your-org/ansflow.git
cd ansflow

# 2. 复制环境变量配置
cp .env.example .env

# 3. 启动开发环境
make dev-up

# 4. 初始化数据库
make db-init

# 5. 创建超级用户
make superuser
```

### 访问服务

| 服务 | URL | 说明 |
|------|-----|------|
| 🎨 前端界面 | http://localhost:3000 | React 用户界面 |
| 🔧 Django 管理 | http://localhost:8000/admin | 后台管理界面 |
| ⚡ FastAPI 文档 | http://localhost:8001/docs | API 接口文档 |
| 🐰 RabbitMQ 管理 | http://localhost:15672 | 消息队列监控 |
| 📊 Grafana 监控 | http://localhost:3001 | 系统监控面板 |

默认登录凭据：
- **用户名**: admin
- **密码**: admin123

## 📚 项目结构

```
ansflow/
├── 🔧 backend/                 # 后端微服务
│   ├── django_service/         # Django 管理服务
│   ├── fastapi_service/        # FastAPI 高性能服务
│   └── shared/                 # 共享代码库
├── 🎨 frontend/                # React 前端应用
├── 🚀 deployment/              # 部署配置
│   ├── docker/                 # Docker 配置
│   ├── kubernetes/             # K8s 部署配置
│   ├── terraform/              # 基础设施即代码
│   └── ansible/                # 配置管理
├── 📚 docs/                    # 项目文档
├── 🧪 tests/                   # 集成测试
├── 📊 monitoring/              # 监控配置
└── 🔧 scripts/                 # 工具脚本
```

详细结构说明请参考 [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)

## 🛠️ 开发指南

### 后端开发

```bash
# 进入 Django 服务目录
cd backend/django_service

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
python manage.py runserver 8000

# 运行测试
python manage.py test
```

### 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 运行测试
npm run test

# 构建生产版本
npm run build
```

### 常用命令

```bash
# 开发环境管理
make dev-up          # 启动开发环境
make dev-down        # 停止开发环境
make dev-logs        # 查看日志
make dev-restart     # 重启服务

# 数据库管理
make db-init         # 初始化数据库
make db-migrate      # 运行迁移
make db-seed         # 填充测试数据
make db-backup       # 备份数据库

# 测试相关
make test            # 运行所有测试
make test-backend    # 运行后端测试
make test-frontend   # 运行前端测试
make lint            # 代码检查

# 生产部署
make prod-deploy     # 生产环境部署
make prod-logs       # 生产环境日志
make prod-backup     # 生产环境备份
```

## 📋 开发路线图 / TODO List

### 🎉 最新完成：拖拽式流水线编辑器完整修复 ✅
**完成日期**: 2025年6月30日 | **阶段**: Phase 3 核心功能完善
- ✅ **原子步骤状态隔离** - 修复不同流水线编辑器间的状态污染问题
- ✅ **数据持久化修复** - 解决页面刷新后拖拽内容丢失问题
- ✅ **详情数据获取优化** - 修复查看详情和编辑器中步骤显示为空的问题
- ✅ **前端数据流重构** - 详情和编辑器自动获取完整流水线数据
- ✅ **后端API完善** - Pipeline模型与AtomicStep模型正确关联，支持steps字段
- ✅ **前端组件优化** - PipelineEditor组件状态管理，正确的生命周期处理
- ✅ **序列化器重构** - 后端PipelineSerializer支持atomic_steps字段映射
- ✅ **类型定义统一** - 前后端数据格式完全一致，消除字段不匹配问题

> 🎯 **访问地址**: http://localhost:3000/pipelines | **功能**: 流水线管理→编辑器→拖拽式步骤配置→完整功能可用

### 🎉 已完成：Jenkins工具集成与状态系统完善 ✅
**完成日期**: 2025年6月30日 | **阶段**: Jenkins集成专项修复
- ✅ **Jenkins工具状态系统** - 四种状态分类(authenticated/needs_auth/offline/unknown)
- ✅ **健康检查机制** - 智能区分在线已认证、在线需认证、离线等状态
- ✅ **Jenkins作业列表API** - 完整的作业信息展示，支持状态、描述、构建历史
- ✅ **Jenkins构建历史API** - 实时获取构建记录，智能状态同步机制
- ✅ **Jenkins构建日志API** - 支持查看详细的构建日志和控制台输出
- ✅ **前端状态显示优化** - 清晰的颜色图标区分，用户体验友好
- ✅ **智能构建状态同步** - 解决构建完成后状态滞后问题，自动轮询机制

> 🎯 **访问地址**: http://localhost:3000/tools | **功能**: 工具管理→Jenkins集成→作业列表→构建历史

### 🎉 已完成：WebSocket实时监控系统 ✅
**完成日期**: 2025年6月26日 | **阶段**: Phase 2 完成
- ✅ **Django Channels + Redis** 实时通信架构
- ✅ **前后端WebSocket集成** - React useWebSocket Hook
- ✅ **流水线实时监控** - <100ms延迟状态更新
- ✅ **步骤级进度显示** - 6种原子步骤并行执行监控
- ✅ **实时日志流** - 执行过程完整可见
- ✅ **用户认证集成** - 安全的WebSocket连接

> 🎯 **访问地址**: http://localhost:3000/executions/{id} | **登录**: admin/admin123

---

### 🚀 第一阶段：核心功能完善 (v1.1.0) ✅ 已完成
- [x] ✅ **前端身份验证修复** - 修复JWT登录系统404错误
- [x] ✅ **基础流水线管理** - 流水线的创建、编辑、删除功能
- [x] ✅ **用户权限系统** - 基于角色的访问控制(RBAC)
- [x] ✅ **流水线执行引擎** - 7种原子步骤类型，Celery异步执行
- [x] ✅ **实时执行监控** - WebSocket实时状态推送，<100ms延迟
- [x] ✅ **Jenkins工具集成** - 完整的Jenkins CI/CD工具管理和监控
- [ ] 🔄 **Webhook 集成** - Git 仓库事件触发流水线
- [ ] ⏳ **基础通知系统** - 邮件和Slack通知集成

### 🎯 第二阶段：完整UI生态与多工具集成 (v1.2.0) 🚧 当前重点
- [x] ✅ **可视化流水线编辑器** - 拖拽式流水线构建界面 ✅ 已完成 (2025-06-30)
- [ ] 🔄 **多CI/CD工具集成** - GitLab CI、GitHub Actions、Azure DevOps集成
- [ ] 🔄 **工具管理界面优化** - 统一的工具配置、健康检查、状态监控
- [ ] 🔄 **流水线管理界面** - 完整的CRUD操作界面和项目管理
- [ ] 🔄 **数据可视化仪表板** - 执行历史分析和性能监控
- [ ] ⏳ **原子步骤商店** - 预定义步骤库和自定义步骤
- [ ] ⏳ **条件执行逻辑** - 基于条件的分支执行
- [ ] ⏳ **并行执行支持** - 多任务并行处理能力
- [ ] ⏳ **环境变量管理** - 安全的配置和密钥管理
- [ ] ⏳ **审批工作流** - 多级审批流程

### 📋 Phase 3 立即行动计划 (未来6周)
#### Week 1-2: 多工具集成与管理界面 🎯 优先级1
- [ ] 🔄 **GitLab CI 集成** - 基于Jenkins集成经验的GitLab CI工具适配
- [ ] 🔄 **GitHub Actions 集成** - GitHub Actions工具集成和作业管理
- [ ] 🔄 **工具管理统一界面** - 多种CI/CD工具的统一管理入口
- [ ] 🔄 **流水线与工具关联** - 流水线中选择和配置不同的执行工具
- [x] ✅ **拖拽式流水线编辑器** - 可视化步骤编辑和依赖关系配置 ✅ 已完成

#### Week 3-4: 监控仪表板与数据可视化 📊 优先级2
- [ ] 🔄 **跨工具执行监控** - 统一监控不同CI/CD工具的执行状态
- [ ] 🔄 **执行历史与统计分析** - Charts.js集成，成功率趋势分析
- [ ] 🔄 **系统监控仪表板** - 实时系统指标，资源使用监控
- [ ] 🔄 **告警与通知系统** - 执行失败告警，邮件/Slack集成
- [ ] 🔄 **性能分析报告** - 基于WebSocket监控数据的深度分析

#### Week 5-6: 企业级功能增强 🏢 优先级3
- [ ] 🔄 **高级流水线功能** - 条件分支、并行执行、手动审批节点
- [ ] 🔄 **外部系统集成** - Git代码库、Docker构建、第三方API集成
- [ ] 🔄 **安全与权限管理** - RBAC模型、密钥管理、审计日志
- [ ] 🔄 **流水线模板市场** - 预定义模板库和分享机制

### 🔧 第三阶段：企业级功能 (v1.3.0)
- [ ] ⏳ **多租户支持** - 企业级多组织架构
- [ ] ⏳ **高级监控面板** - 全面的系统监控和告警
- [ ] ⏳ **API 网关集成** - 统一的API管理和限流
- [ ] ⏳ **容器化部署支持** - Docker/Kubernetes 原生支持
- [ ] ⏳ **插件系统** - 第三方工具扩展机制
- [ ] ⏳ **数据备份恢复** - 自动化数据备份策略
- [ ] ⏳ **性能优化** - 大规模并发处理优化

### 🚀 第四阶段：AI 智能化 (v2.0.0)
- [ ] ⏳ **智能流水线推荐** - 基于项目类型的流水线模板推荐
- [ ] ⏳ **异常检测与自愈** - AI驱动的问题检测和自动修复
- [ ] ⏳ **性能预测分析** - 基于历史数据的性能预测
- [ ] ⏳ **智能资源调度** - 动态资源分配和优化
- [ ] ⏳ **代码质量分析** - 集成AI代码审查和建议

### 🛠️ 技术债务和优化
- [ ] ⏳ **代码覆盖率提升** - 目标达到90%以上测试覆盖率
- [ ] ⏳ **API 文档完善** - 完整的OpenAPI规范和示例
- [ ] ⏳ **前端组件库** - 构建可复用的UI组件库
- [ ] ⏳ **国际化支持** - 多语言界面支持
- [ ] ⏳ **移动端适配** - 响应式设计和移动端优化
- [ ] ⏳ **安全加固** - 安全漏洞扫描和修复

### 🔍 已知问题修复
- [x] ✅ **拖拽式编辑器完整修复** - 解决状态污染、数据持久化、详情显示等全部问题
- [x] ✅ **流水线详情数据获取修复** - 修复查看详情和编辑器中步骤显示为空的问题
- [x] ✅ **前端数据获取逻辑优化** - 详情和编辑器自动获取完整流水线数据
- [x] ✅ **流水线列表步骤数显示修复** - 修复前端页面显示"暂无步骤配置"问题，正确显示步骤数量
- [x] ✅ **Pipeline与AtomicStep模型关联修复** - 修正后端数据模型，确保steps字段正确序列化
- [x] ✅ **前后端字段映射优化** - 列表API返回steps_count，详情API返回完整steps数组
- [x] ✅ **Jenkins API 404错误修复** - 修复构建历史和日志查看API路径问题
- [x] ✅ **formatDistanceToNow错误修复** - 解决时间戳无效导致的前端页面空白问题
- [x] ✅ **Jenkins认证字段错误修复** - 修正token字段引用，确保API调用正确认证
- [x] ✅ **构建状态同步延迟问题** - 实现智能状态检测和自动刷新机制
- [x] ✅ **前端API路径不匹配** - 统一前后端API路径，使用查询参数优化复杂路径
- [ ] ⏳ **数据库连接池优化** - 解决高并发下的连接问题
- [ ] ⏳ **内存泄漏修复** - 长时间运行的内存使用优化
- [ ] ⏳ **错误处理改进** - 更友好的错误提示和恢复机制

### 📝 图例说明
- ✅ **已完成** - 功能已实现并测试通过
- 🔄 **进行中** - 正在开发中
- ⏳ **计划中** - 已列入开发计划

> 💡 **贡献建议**: 如果您对某个功能有特别的需求或建议，欢迎在 [Issues](https://github.com/your-org/ansflow/issues) 中提出讨论！

## 📖 文档导航

- [🏗️ 项目结构](./PROJECT_STRUCTURE.md) - 详细的项目组织结构
- [🎯 技术架构分析](./项目说明/技术架构分析报告.md) - 深度技术架构解析
- [🎨 拖拽式流水线编辑器修复报告](./PIPELINE_EDITOR_FIX_REPORT.md) - 完整修复过程与验证结果
- [🔧 Jenkins工具状态系统完善](./STATUS_SYSTEM_DEMO.md) - 工具集成与状态管理完整方案
- [🎉 WebSocket监控系统完成报告](./WEBSOCKET_MONITORING_COMPLETION_REPORT.md) - Phase 2 完成总结
- [🚀 下一阶段开发计划](./NEXT_PHASE_DEVELOPMENT_PLAN.md) - Phase 3 详细规划
- [🔧 API 文档](./docs/api/) - RESTful API 接口文档
- [🚀 部署指南](./docs/deployment/) - 生产环境部署指南
- [👨‍💻 开发指南](./docs/development/) - 开发环境配置与规范
- [📊 监控指南](./docs/monitoring/) - 系统监控与运维

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

1. **Fork** 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 **Pull Request**

### 开发规范

- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) Python 代码规范
- 遵循 [ESLint](https://eslint.org/) JavaScript/TypeScript 代码规范
- 提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/)
- 确保所有测试通过
- 更新相关文档

## 🔄 版本发布

我们使用 [语义化版本](https://semver.org/) 进行版本管理。查看 [Releases](https://github.com/your-org/ansflow/releases) 了解版本历史。

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系我们


## 🙏 致谢

感谢所有为 AnsFlow 项目做出贡献的开发者和社区成员！

---

**⚡ 让 CI/CD 更简单，让开发更高效 - AnsFlow 与您同行！**
