# 工作目录保留功能说明

## 📖 功能概述

AnsFlow 流水线执行系统现已支持工作目录保留功能。执行完成后，流水线的工作目录默认会被保留，以便用户查看执行结果、调试问题和分析日志。

## ✨ 主要特性

### 🔧 默认保留行为
- 流水线执行完成后，工作目录默认**不会被删除**
- 保留所有执行过程中的文件、日志、构建产物和中间结果
- 在日志中记录工作目录位置，便于用户查找

### 🎯 灵活控制选项
- **单次强制清理**：`context.cleanup_workspace(force_cleanup=True)`
- **全局设置控制**：`workspace_manager.set_preserve_workspaces(False)`
- **便捷清理方法**：`context.force_cleanup_workspace()`

### 🔍 工作目录管理
- 查看保留的工作目录：`workspace_manager.list_preserved_workspaces()`
- 强制清理指定目录：`workspace_manager.force_cleanup_workspace(execution_id)`

## 📁 工作目录结构

保留的工作目录包含：
```
/tmp/pipeline_name_execution_id/
├── 代码文件/             # Git clone 的源代码
├── 构建产物/             # 编译、打包的结果文件
├── 日志文件/             # 各步骤的执行日志
├── 测试报告/             # 单元测试、集成测试结果
├── 配置文件/             # 动态生成的配置
└── 中间文件/             # 临时文件和处理过程文件
```

## 🛠️ 使用方法

### 1. 默认行为（推荐）
```python
# 流水线执行完成后，工作目录自动保留
# 无需任何额外代码，现有流水线自动获得此功能
```

### 2. 强制清理单个工作目录
```python
# 方法1：使用force_cleanup参数
context.cleanup_workspace(force_cleanup=True)

# 方法2：使用便捷方法
context.force_cleanup_workspace()
```

### 3. 全局控制保留行为
```python
# 关闭保留功能（恢复原有清理行为）
workspace_manager.set_preserve_workspaces(False)

# 重新开启保留功能
workspace_manager.set_preserve_workspaces(True)
```

### 4. 查看和管理保留的工作目录
```python
# 列出所有保留的工作目录
preserved_workspaces = workspace_manager.list_preserved_workspaces()
for execution_id, workspace_path in preserved_workspaces.items():
    print(f"执行ID {execution_id}: {workspace_path}")

# 强制清理指定的工作目录
workspace_manager.force_cleanup_workspace(execution_id)
```

## 🔄 修改的文件

### 1. `execution_context.py`
- `cleanup_workspace(force_cleanup=False)`：支持强制清理参数
- `force_cleanup_workspace()`：便捷的强制清理方法

### 2. `workspace_manager.py`
- `preserve_workspaces = True`：默认保留工作目录
- `cleanup_workspace(execution_id, force_cleanup=False)`：支持强制清理
- `set_preserve_workspaces(preserve)`：全局设置控制
- `list_preserved_workspaces()`：列出保留的目录
- `force_cleanup_workspace(execution_id)`：强制清理指定目录

### 3. `sync_pipeline_executor.py`
- 修改流水线完成后的清理逻辑，默认保留工作目录
- 在日志中记录工作目录位置和清理说明

## 🎯 使用场景

### 🐛 问题调试
当流水线执行失败时，保留的工作目录包含：
- 完整的错误日志
- 失败时的文件状态
- 中间执行结果
- 环境配置信息

### 📊 结果分析
成功执行后，可以查看：
- 构建产物和文件
- 测试报告和覆盖率
- 性能分析结果
- 生成的配置文件

### 🔧 开发调试
在开发和测试阶段：
- 验证步骤执行结果
- 检查文件生成是否正确
- 分析执行性能
- 优化流水线配置

## ⚠️ 注意事项

### 💾 磁盘空间
- 保留的工作目录会占用磁盘空间
- 建议定期清理不需要的历史目录
- 可以通过全局设置关闭保留功能

### 🔒 安全考虑
- 工作目录可能包含敏感信息
- 确保适当的文件权限设置
- 及时清理包含敏感数据的目录

### 🧹 清理策略
```python
# 示例：定期清理策略
def cleanup_old_workspaces(days_old=7):
    \"\"\"清理7天前的工作目录\"\"\"
    preserved = workspace_manager.list_preserved_workspaces()
    for execution_id, path in preserved.items():
        # 检查目录创建时间，清理过期目录
        # ... 实现清理逻辑
```

## 🚀 优势总结

1. **便于调试**：完整保留执行状态，快速定位问题
2. **结果查看**：方便查看构建产物和执行结果
3. **灵活控制**：支持全局和单次的清理控制
4. **向后兼容**：现有代码无需修改即可获得保留功能
5. **清晰日志**：提供详细的目录位置和清理说明

## 📝 版本兼容性

- ✅ **向后兼容**：现有流水线无需修改
- ✅ **平滑升级**：默认行为改为保留目录
- ✅ **灵活控制**：可恢复原有清理行为
- ✅ **扩展性强**：支持未来的清理策略扩展

---

> 💡 **提示**：这个功能特别适合开发和调试阶段使用。在生产环境中，建议根据实际需求配置适当的清理策略。
