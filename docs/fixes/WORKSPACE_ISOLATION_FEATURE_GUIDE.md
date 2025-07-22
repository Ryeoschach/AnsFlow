# 流水线工作目录隔离功能

## 概述

为每个流水线执行创建独立的工作目录，确保不同流水线之间的文件完全隔离，提高执行安全性和调试便利性。

## 功能特性

### ✅ 已实现功能

1. **独立工作目录**
   - 每个流水线执行都有专属的工作目录
   - 目录格式：`/tmp/{流水线名称}_{执行编号}`
   - 支持中文名称和特殊字符的安全处理

2. **自动目录管理**
   - 执行开始时自动创建工作目录
   - 执行结束时自动清理工作目录
   - 支持子目录创建和路径解析

3. **执行上下文集成**
   - ExecutionContext 自动管理工作目录
   - 提供目录切换和路径解析方法
   - 步骤执行器自动使用工作目录

4. **安全命名规则**
   - 自动过滤非法字符
   - 长名称自动截断
   - 确保目录名称系统兼容

## 技术实现

### 核心组件

#### 1. PipelineWorkspaceManager
```python
# backend/django_service/cicd_integrations/executors/workspace_manager.py
class PipelineWorkspaceManager:
    def create_workspace(self, pipeline_name: str, execution_id: int) -> str
    def cleanup_workspace(self, execution_id: int) -> bool
    def _sanitize_name(self, name: str) -> str
```

#### 2. ExecutionContext 增强
```python
# backend/django_service/cicd_integrations/executors/execution_context.py
class ExecutionContext:
    workspace_path: Optional[str]
    
    def get_workspace_path(self) -> str
    def change_directory(self, subdir: str = None) -> str
    def resolve_path(self, relative_path: str) -> str
    def cleanup_workspace(self) -> bool
```

#### 3. 步骤执行器更新
```python
# backend/django_service/cicd_integrations/executors/sync_step_executor.py
# 所有执行方法都已更新为使用工作目录：
# - _execute_fetch_code: 代码检出到 workspace/code
# - _execute_build: 在工作目录中构建
# - _execute_custom: 在工作目录中执行自定义命令
```

### 目录结构示例

```
/tmp/
├── 前端构建_1001/
│   ├── code/           # 代码检出目录
│   │   └── package.json
│   └── build/          # 构建输出目录
├── 后端API_1002/
│   ├── code/
│   │   └── requirements.txt
│   └── tests/          # 测试目录
└── Docker镜像构建_1003/
    ├── code/
    │   └── Dockerfile
    └── output/         # 输出目录
```

## 使用场景

### 1. 代码检出隔离
- 每个流水线在独立目录中检出代码
- 避免不同分支代码相互覆盖
- 支持同时执行多个构建任务

### 2. 构建环境隔离
- 构建文件和依赖完全隔离
- 避免构建缓存冲突
- 提高并行执行的稳定性

### 3. 调试和问题排查
- 可以保留执行过程中的临时文件
- 便于分析执行失败的原因
- 清晰的目录结构便于理解执行流程

### 4. 安全性增强
- 防止恶意代码影响其他流水线
- 限制文件访问范围
- 自动清理临时文件

## 配置说明

### 默认配置
- 工作目录根路径：`/tmp/`
- 目录命名格式：`{流水线名称}_{执行编号}`
- 自动清理：启用（流水线完成后）

### 可配置项
```python
# 在 workspace_manager.py 中可以修改：
BASE_WORKSPACE_DIR = "/tmp"  # 工作目录根路径
MAX_NAME_LENGTH = 100        # 最大目录名长度
```

## API 接口

### ExecutionContext 方法

#### get_workspace_path()
获取当前执行的工作目录路径
```python
workspace_path = context.get_workspace_path()
# 返回: "/tmp/流水线名称_12345"
```

#### change_directory(subdir=None)
切换到工作目录或子目录
```python
# 切换到工作目录
context.change_directory()

# 切换到子目录
context.change_directory("build")
context.change_directory("code/src")
```

#### resolve_path(relative_path)
解析相对于工作目录的路径
```python
full_path = context.resolve_path("config/app.json")
# 返回: "/tmp/流水线名称_12345/config/app.json"
```

#### cleanup_workspace()
清理工作目录
```python
context.cleanup_workspace()
```

## 测试验证

### 功能测试
运行完整的功能测试：
```bash
cd backend/django_service
uv run python test_workspace_feature.py
```

### 演示脚本
查看实际使用效果：
```bash
cd backend/django_service
uv run python demo_workspace_feature.py
```

## 执行流程

### 1. 流水线开始
1. 创建 ExecutionContext
2. 自动创建工作目录 `/tmp/{流水线名称}_{执行编号}`
3. 设置 workspace_path

### 2. 步骤执行
1. 代码检出：创建 `workspace/code` 目录
2. 构建步骤：在工作目录中执行构建
3. 自定义步骤：在工作目录中执行命令

### 3. 流水线结束
1. 更新流水线状态为 success/failed
2. 自动调用 `context.cleanup_workspace()`
3. 删除整个工作目录

## 日志记录

系统会记录工作目录的关键操作：
```
INFO Created workspace for pipeline '前端构建' execution 1001: /tmp/前端构建_1001
INFO Cleaned up workspace for execution 1001: /tmp/前端构建_1001
```

## 错误处理

### 常见问题及解决方案

1. **权限不足**
   - 确保 /tmp 目录有写权限
   - 检查用户权限设置

2. **磁盘空间不足**
   - 定期清理 /tmp 目录
   - 监控磁盘使用情况

3. **目录已存在**
   - 系统会自动处理重复的执行编号
   - 强制删除已存在的目录

## 性能影响

### 优化措施
- 使用 `/tmp` 目录（通常是内存文件系统）
- 执行完成后立即清理
- 轻量级目录操作

### 监控指标
- 工作目录创建耗时
- 磁盘空间使用量
- 清理操作成功率

## 后续改进计划

### 可选功能
1. **配置化工作目录根路径**
   - 支持自定义工作目录位置
   - 支持不同项目使用不同根路径

2. **工作目录保留策略**
   - 可选择保留失败执行的工作目录
   - 支持调试模式下禁用自动清理

3. **工作目录大小限制**
   - 设置单个工作目录的最大大小
   - 超出限制时的处理策略

4. **工作目录压缩归档**
   - 执行完成后打包保存
   - 便于后续分析和审计

## 总结

工作目录隔离功能显著提升了 AnsFlow 平台的：
- **🔒 安全性**：流水线间完全隔离
- **🛡️ 稳定性**：避免文件冲突
- **📊 可调试性**：清晰的目录结构
- **⚡ 性能**：并行执行无干扰

该功能已完全集成到现有的流水线执行系统中，无需额外配置即可使用。
