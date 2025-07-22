# AnsFlow 调试工具集合

本目录包含了 AnsFlow 项目的各种调试脚本和演示工具，用于问题诊断、功能验证和开发调试。

## 文件分类

### Docker 调试工具
- `docker_push_*` - Docker 推送相关的调试和修复脚本
- `docker_registry_*` - Docker 注册表相关的调试工具
- `docker_tag_fix_demo.py` - Docker 标签修复演示

### Git 调试工具
- `debug_git_clone_detection.py` - Git 克隆检测调试
- `demo_git_credential_auth_fix.py` - Git 凭据认证修复演示

### 系统诊断工具
- `diagnose_auth_system.py` - 认证系统诊断
- `diagnose_docker_pull_params.py` - Docker 拉取参数诊断
- `debug_docker_push_step_issue.py` - Docker 推送步骤问题调试

### 演示脚本
- `demo_command_usage_fixed.py` - 命令使用修复演示
- `directory_continuity_demo.py` - 目录连续性演示

### 修复工具
- `fix_step_executor.py` - 步骤执行器修复工具
- `restart_guide.py` - 重启指南脚本

### 前端验证工具
- `frontend_docker_registry_fix_verification.js` - 前端 Docker 注册表修复验证
- `frontend_image_tag_test.js` - 前端镜像标签测试

## 使用方法

### 运行调试脚本
```bash
cd /path/to/ansflow
uv run python scripts/debug/debug_docker_push_step_issue.py
```

### 运行诊断工具
```bash
uv run python scripts/debug/diagnose_auth_system.py
uv run python scripts/debug/diagnose_docker_pull_params.py
```

### 运行演示脚本
```bash
uv run python scripts/debug/demo_command_usage_fixed.py
uv run python scripts/debug/directory_continuity_demo.py
```

## 功能说明

### Docker 相关调试
这些脚本用于调试 Docker 集成中的各种问题：
- 推送失败排查
- 注册表连接问题
- 镜像标签处理
- 认证配置验证

### Git 相关调试
用于排查 Git 集成问题：
- 克隆目录检测
- 凭据认证
- 权限配置

### 系统诊断
提供系统级别的诊断工具：
- 认证系统状态检查
- 服务连接验证
- 配置完整性检查

## 开发建议

1. **问题复现**：使用相应的调试脚本复现问题
2. **逐步排查**：从简单的连接测试开始，逐步深入
3. **日志分析**：注意查看脚本输出的详细日志信息
4. **环境检查**：确保开发环境配置正确

## 注意事项

- 调试脚本可能包含敏感信息，请勿提交到版本控制
- 部分脚本需要特定的网络环境或服务依赖
- 运行前请确保有足够的权限和资源
- 建议在隔离的开发环境中运行
