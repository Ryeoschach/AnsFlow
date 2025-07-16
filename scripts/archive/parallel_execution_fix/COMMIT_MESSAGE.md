fix: 修复本地执行流水线并行组功能和命令执行问题

## 问题描述
- 本地执行的流水线并行组没有生效，仍按顺序执行
- 新建的本地流水线显示"No command to execute"错误

## 修复内容

### 1. 修复并行组检测逻辑
- **文件**: `backend/django_service/cicd_integrations/services.py`
- **修改**: 在 `_perform_local_execution` 方法中同时检查 AtomicStep 和 PipelineStep 的并行组
- **原因**: 原逻辑只检查 PipelineStep，导致 AtomicStep 的并行组无法被检测

### 2. 修复命令字段设置
- **文件**: `backend/django_service/pipelines/serializers.py`
- **修改**: 在创建 PipelineStep 时从 `parameters` 中提取 `command` 字段
- **原因**: 命令信息存储在 parameters 中，但没有设置到 command 字段

### 3. 增强序列化器支持
- **文件**: `backend/django_service/cicd_integrations/serializers.py`
- **修改**: 添加 `pipeline_step_name` 和 `step_name` 字段支持
- **原因**: 统一步骤名称显示，支持 AtomicStep 和 PipelineStep

### 4. 优化并行执行引擎
- **文件**: `backend/django_service/cicd_integrations/engines/parallel_execution.py`
- **修改**: 增强 `_execute_parallel_pipeline_steps` 和 `_execute_sequential_pipeline_steps` 方法
- **原因**: 确保 StepExecution 记录正确创建，支持实时日志监控

## 测试验证
✅ 并行组检测功能正常，能检测到 AtomicStep 和 PipelineStep 的并行组
✅ 命令执行功能正常，新建流水线不再显示"No command to execute"
✅ 执行详情页面显示正常，步骤信息完整
✅ 实时日志和全部日志功能正常

## 影响评估
- ✅ 无破坏性变更，保持向后兼容
- ✅ 支持 AtomicStep 和 PipelineStep 双模型
- ✅ 提升用户体验，修复核心功能缺陷

## 归档文件
- `scripts/archive/parallel_execution_fix/README.md` - 详细修复说明
- `scripts/archive/parallel_execution_fix/fix_pipeline_steps.py` - 修复脚本
- `scripts/archive/parallel_execution_fix/test_command_fix.py` - 命令配置测试
- `scripts/archive/parallel_execution_fix/test_parallel_groups.py` - 并行组测试
- `scripts/archive/parallel_execution_fix/test_full_parallel.py` - 完整并行执行测试

Co-authored-by: GitHub Copilot <copilot@github.com>
