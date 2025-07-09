# Git凭据管理 - 快速访问指南

## 📁 文件组织结构

```
AnsFlow/
├── 📋 CHANGELOG_GIT_CREDENTIALS.md           # 更新日志
├── 📋 docs/GIT_CREDENTIAL_FIX_REPORT.md      # 详细修复报告
├── 🔧 scripts/git_credential_tools/          # 测试工具集
│   ├── 📖 README.md                          # 工具使用指南
│   ├── 🔍 diagnose_git_credentials.py        # 全面诊断
│   ├── 🎯 test_gitlab_only.py                # GitLab专项测试
│   ├── 🔄 reset_gitlab_credential.py         # 凭据重置
│   ├── ⚙️ test_direct_gitlab.py              # 直接测试
│   └── 🧪 test_api_fields.py                 # API字段验证
└── 🛠️ backend/django_service/cicd_integrations/
    ├── git_credential_tester.py              # 核心测试类
    ├── models.py                             # 数据模型
    ├── serializers.py                        # API序列化
    └── views/git_credentials.py              # API视图
```

## 🚀 快速开始

### 问题排查（推荐流程）

1. **一键诊断**
   ```bash
   cd /Users/creed/workspace/sourceCode/AnsFlow
   python scripts/git_credential_tools/diagnose_git_credentials.py
   ```

2. **GitLab专项测试**
   ```bash
   python scripts/git_credential_tools/test_gitlab_only.py
   ```

3. **凭据重置**（如果需要）
   ```bash
   python scripts/git_credential_tools/reset_gitlab_credential.py
   ```

### 开发调试

1. **API验证**
   ```bash
   python scripts/git_credential_tools/test_api_fields.py
   ```

2. **后端测试**
   ```bash
   python scripts/git_credential_tools/test_direct_gitlab.py
   ```

## 📚 文档导航

| 文档 | 用途 | 位置 |
|------|------|------|
| **修复报告** | 了解问题原因和解决方案 | `docs/GIT_CREDENTIAL_FIX_REPORT.md` |
| **更新日志** | 查看版本变更和新功能 | `CHANGELOG_GIT_CREDENTIALS.md` |
| **工具指南** | 学习测试工具使用方法 | `scripts/git_credential_tools/README.md` |
| **快速访问** | 快速查找文件和命令 | `docs/GIT_CREDENTIAL_QUICK_ACCESS.md` |

## 🔧 常用命令

### 健康检查
```bash
# 完整诊断
python scripts/git_credential_tools/diagnose_git_credentials.py

# GitLab连接测试
python scripts/git_credential_tools/test_gitlab_only.py
```

### 问题修复
```bash
# 重置损坏的凭据
python scripts/git_credential_tools/reset_gitlab_credential.py

# 直接测试认证逻辑
python scripts/git_credential_tools/test_direct_gitlab.py
```

### 开发验证
```bash
# 验证API字段
python scripts/git_credential_tools/test_api_fields.py

# 重启Django服务
cd backend/django_service && python manage.py runserver 0.0.0.0:8000
```

## 🎯 常见场景

### 场景1: 新部署验证
1. 检查加密密钥配置
2. 运行完整诊断
3. 测试GitLab连接
4. 验证前端功能

### 场景2: 凭据连接失败
1. 运行GitLab专项测试
2. 检查错误信息分析
3. 根据建议修复配置
4. 重置凭据（如需要）

### 场景3: 开发调试
1. 验证API字段返回
2. 直接测试后端逻辑
3. 检查加密解密功能
4. 确认前后端一致性

## 📞 支持联系

- **技术文档**: `docs/GIT_CREDENTIAL_FIX_REPORT.md`
- **工具说明**: `scripts/git_credential_tools/README.md`
- **更新记录**: `CHANGELOG_GIT_CREDENTIALS.md`

---
**创建时间**: 2025年7月2日  
**维护团队**: AnsFlow开发组
