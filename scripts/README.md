# AnsFlow 项目脚本目录

## 📄 脚本说明

本目录包含 AnsFlow 项目的所有测试脚本、验证脚本和实用工具脚本。

## 📂 脚本目录结构

```
scripts/
├── archive/                           # 历史脚本归档
├── check_logs_status.py              # 检查日志状态脚本
├── check_system_status.sh            # 检查系统状态脚本
├── final_logs_fix_verification.py    # 最终日志修复验证脚本
├── final_verification.py             # 最终验证脚本
├── jenkins_fix_demo.py               # Jenkins修复演示脚本
├── jenkins_test_pipeline.py          # Jenkins测试流水线脚本
├── quick_verify.py                   # 快速验证脚本
├── setup.sh                         # 项目设置脚本
├── test_*.py                         # 各种测试脚本
├── test_frontend_ui_optimization_july2_2025.js  # 前端UI优化测试脚本
└── update_frontend_token.js          # 更新前端Token脚本
```

## 🧪 测试脚本分类

### 🎨 前端UI测试
- `test_frontend_ui_optimization_july2_2025.js` - 前端UI优化验证测试
  - 验证Select组件样式统一
  - 检查表格操作列优化
  - 自动化回归测试

### 🔧 后端功能测试
- `test_frontend_api.py` - 前端API连接测试
- `jenkins_test_pipeline.py` - Jenkins流水线测试
- `jenkins_fix_demo.py` - Jenkins修复功能演示

### 🛡️ 安全与转义测试
- `test_backslash_escaping.py` - 反斜杠转义测试
- `test_comprehensive_escaping.py` - 综合转义测试
- `test_jenkins_escaping.py` - Jenkins转义测试

### 🔍 系统验证脚本
- `check_logs_status.py` - 检查日志系统状态
- `check_system_status.sh` - 检查整体系统状态
- `final_verification.py` - 最终功能验证
- `final_logs_fix_verification.py` - 日志修复最终验证
- `quick_verify.py` - 快速系统验证

### ⚙️ 实用工具脚本
- `setup.sh` - 项目环境设置
- `update_frontend_token.js` - 前端认证Token更新

## 🚀 使用指南

### 前端UI测试
```bash
# 运行前端UI优化验证测试
node scripts/test_frontend_ui_optimization_july2_2025.js
```

### 系统状态检查
```bash
# 检查系统状态
./scripts/check_system_status.sh

# 检查日志状态
python scripts/check_logs_status.py
```

### Jenkins相关测试
```bash
# 测试Jenkins集成
python scripts/jenkins_test_pipeline.py

# Jenkins修复演示
python scripts/jenkins_fix_demo.py
```

### 安全转义测试
```bash
# 运行转义测试套件
python scripts/test_comprehensive_escaping.py
python scripts/test_backslash_escaping.py
python scripts/test_jenkins_escaping.py
```

### 快速验证
```bash
# 快速验证系统功能
python scripts/quick_verify.py

# 最终验证
python scripts/final_verification.py
```

## 📋 脚本维护说明

### 添加新脚本
1. 在相应分类下创建脚本文件
2. 添加适当的文档注释
3. 更新本README文件
4. 确保脚本具有执行权限

### 脚本命名规范
- `test_*.py` - 测试脚本
- `check_*.py/sh` - 检查/验证脚本
- `setup_*.sh` - 设置脚本
- `*_demo.py` - 演示脚本

### 归档规则
- 超过3个月未使用的脚本移至 `archive/` 目录
- 已被新脚本替代的旧脚本移至 `archive/` 目录
- 保留重要的历史测试脚本用于回归测试

---

**最后更新**: 2025年7月2日  
**脚本总数**: 14个活跃脚本  
**测试覆盖**: 前端UI、后端API、安全、Jenkins集成、系统验证
