# AnsFlow 项目文档

## 📄 文档目录说明

本目录包含 AnsFlow CI/CD 平台的完整文档集合，涵盖项目开发、部署、API文档和历史归档。

## 📂 文档结构

```
docs/
├── 📁 archive/                        # 历史修复报告和技术文档归档
├── 📁 api/                           # API文档
├── 📁 deployment/                    # 部署相关文档
├── 📁 development/                   # 开发指南和规范
├── 📄 NEXT_PHASE_DEVELOPMENT_PLAN.md      # 下一阶段开发计划
├── 📄 PIPELINE_PARAMETER_HELP_FEATURE.md  # 流水线参数帮助功能文档
├── 📄 PROJECT_STATUS_SUMMARY.md           # 项目当前状态总结
├── 📄 PROJECT_STRUCTURE.md               # 项目整体结构说明
├── 📄 QUICK_FIX_GUIDE.md                 # 常见问题快速修复指南
├── 📄 QUICK_START_GUIDE.md               # 快速开始使用指南
├── 📄 pipeline-parameter-help-feature.md  # 流水线参数帮助功能（详细版）
└── 📄 pipeline-steps-parameters.md        # 流水线步骤参数说明
```

## 📖 主要文档说明

### 🚀 快速开始
- **[QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)** - 新用户快速上手指南
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - 项目整体架构和结构说明

### 📊 项目状态
- **[PROJECT_STATUS_SUMMARY.md](PROJECT_STATUS_SUMMARY.md)** - 项目当前开发状态和进展
- **[NEXT_PHASE_DEVELOPMENT_PLAN.md](NEXT_PHASE_DEVELOPMENT_PLAN.md)** - 下一阶段开发规划

### 🔧 开发与维护
- **[QUICK_FIX_GUIDE.md](QUICK_FIX_GUIDE.md)** - 常见问题的快速解决方案
- **[development/](development/)** - 开发规范、代码风格、贡献指南

### 🚀 部署相关
- **[deployment/](deployment/)** - 生产环境部署指南、Docker配置、环境配置

### 📡 API文档
- **[api/](api/)** - REST API文档、WebSocket API文档、认证说明

### 💡 功能文档
- **[PIPELINE_PARAMETER_HELP_FEATURE.md](PIPELINE_PARAMETER_HELP_FEATURE.md)** - 流水线参数帮助功能说明
- **[pipeline-steps-parameters.md](pipeline-steps-parameters.md)** - 各种流水线步骤的参数详细说明

### 📚 历史归档
- **[archive/](archive/)** - 所有历史修复报告、技术决策文档、开发过程记录

## 🔍 文档查找指南

### 按用户类型查找

#### 👨‍💻 开发者
1. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 了解项目架构
2. [development/](development/) - 开发规范和指南
3. [api/](api/) - API文档
4. [archive/](archive/) - 历史技术决策

#### 🚀 运维人员
1. [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) - 快速部署
2. [deployment/](deployment/) - 部署配置详情
3. [QUICK_FIX_GUIDE.md](QUICK_FIX_GUIDE.md) - 故障排除

#### 📝 产品经理
1. [PROJECT_STATUS_SUMMARY.md](PROJECT_STATUS_SUMMARY.md) - 项目现状
2. [NEXT_PHASE_DEVELOPMENT_PLAN.md](NEXT_PHASE_DEVELOPMENT_PLAN.md) - 开发规划
3. [archive/](archive/) - 功能完成历史

#### 👤 最终用户
1. [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) - 使用入门
2. [PIPELINE_PARAMETER_HELP_FEATURE.md](PIPELINE_PARAMETER_HELP_FEATURE.md) - 功能说明
3. [pipeline-steps-parameters.md](pipeline-steps-parameters.md) - 参数配置

### 按问题类型查找

#### 🐛 遇到问题
1. [QUICK_FIX_GUIDE.md](QUICK_FIX_GUIDE.md) - 常见问题解决
2. [archive/](archive/) - 历史问题修复记录

#### 🏗️ 想要扩展功能
1. [development/](development/) - 开发指南
2. [api/](api/) - API参考
3. [archive/](archive/) - 类似功能实现参考

#### 📈 了解项目进展
1. [PROJECT_STATUS_SUMMARY.md](PROJECT_STATUS_SUMMARY.md) - 当前状态
2. [NEXT_PHASE_DEVELOPMENT_PLAN.md](NEXT_PHASE_DEVELOPMENT_PLAN.md) - 未来规划
3. [archive/](archive/) - 历史完成项目

## 📝 文档贡献指南

### 新增文档
1. 确定文档类型和目标目录
2. 使用统一的Markdown格式
3. 添加适当的目录和链接
4. 更新相关目录的README文件

### 文档更新
1. 保持文档的时效性
2. 重要变更需要更新多个相关文档
3. 废弃的文档移至archive目录

### 命名规范
- 使用大写字母和下划线：`DOCUMENT_NAME.md`
- 功能文档使用小写和连字符：`feature-name.md`
- 归档文档保持原有命名

---

**文档维护**: AnsFlow开发团队  
**最后更新**: 2025年7月2日  
**文档总数**: 40+ 个文档文件  
**覆盖范围**: 开发、部署、API、用户指南、历史归档
