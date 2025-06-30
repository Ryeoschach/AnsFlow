# 测试脚本归档

本目录包含了在开发过程中使用的各种测试和验证脚本。这些脚本用于验证特定功能修复和API测试。

## 📁 脚本分类

### 🔧 执行模式相关测试
- `test_execution_mode_update.py` - 测试流水线执行模式更新功能
- `test_frontend_data_sync.py` - 测试前端数据同步机制
- `test_complete_workflow.py` - 完整的执行模式更新和显示流程验证

### 📝 流水线功能测试
- `test_pipeline_update_without_steps.py` - 测试不包含steps字段的流水线更新
- `test_list_api_fields.py` - 测试流水线列表API字段完整性

### 🔍 功能验证脚本
- `verify_pipeline_editor.py` - 验证PipelineEditor新功能数据结构

## 🚀 使用方法

所有脚本都需要在后端服务运行的情况下执行：

```bash
# 确保后端服务运行在 localhost:8000
cd /Users/creed/Workspace/OpenSource/ansflow/backend/django_service

# 使用 uv 运行测试脚本
uv run ../../tests/archive/test_execution_mode_update.py
uv run ../../tests/archive/test_complete_workflow.py
```

## 📋 测试覆盖的功能

### ✅ 已验证功能
1. **执行模式更新** - local/remote/hybrid 三种模式切换
2. **API字段一致性** - 列表API和详情API字段对比
3. **前端数据同步** - 保存后状态刷新机制
4. **PipelineEditor功能** - 基本信息编辑和步骤管理
5. **序列化器兼容性** - steps字段可选更新支持

### 🎯 修复验证
- ✅ 流水线执行模式编辑和保存功能
- ✅ 前端页面实时显示执行模式变化
- ✅ 列表API包含完整的执行配置字段
- ✅ PipelineEditor新增的基本信息编辑功能
- ✅ 前后端数据同步机制优化

## 📝 脚本维护说明

这些测试脚本是开发过程中的临时验证工具，主要用于：

1. **功能验证** - 确认新功能正常工作
2. **回归测试** - 验证修复没有破坏现有功能
3. **API测试** - 验证后端API行为符合预期
4. **数据一致性检查** - 确保前后端数据格式一致

**注意**: 这些脚本可能依赖特定的测试数据和环境配置，在不同环境中运行时可能需要调整参数。

## 🔄 后续计划

随着项目的发展，建议：

1. 将关键的测试逻辑集成到正式的单元测试中
2. 建立自动化的回归测试套件
3. 定期清理过时的临时测试脚本
4. 将通用的测试工具提取为可复用的测试库

---

**最后更新**: 2025年6月30日 | **相关功能**: 流水线执行模式编辑和保存修复
