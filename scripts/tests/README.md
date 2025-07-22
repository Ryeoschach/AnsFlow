# AnsFlow 测试脚本集合

本目录包含了 AnsFlow 项目的各种测试脚本，用于验证系统功能、调试问题和确保代码质量。

## 文件分类

### Docker 相关测试
- `test_docker_*` - Docker 执行器、注册表、推送/拉取功能测试
- `test_registry_*` - Docker 注册表配置和认证测试
- `test_complete_docker_push.py` - 完整的 Docker 推送流程测试

### Git 相关测试
- `test_git_*` - Git 克隆、凭据、目录切换功能测试
- `test_gitlab_connection_fix.py` - GitLab 连接修复验证

### 目录和工作空间测试
- `test_directory_*` - 目录连续性和切换功能测试
- `test_workspace_*` - 工作空间管理和保留功能测试
- `test_code_fetch_root.py` - 代码获取根目录测试

### 命令执行测试
- `test_command_*` - 命令字段和执行逻辑测试
- `test_run_command_direct.py` - 直接命令执行测试
- `test_subprocess_fix.py` - 子进程调用修复测试

### 流水线执行测试
- `test_retry_logic_fix.py` - 步骤重试逻辑测试
- `test_parallel_execution.py` - 并行执行测试
- `test_enhanced_logging.py` - 增强日志记录测试

### API 和认证测试
- `test_api_fix.py` - API 修复验证
- `test_auth_config_fix.py` - 认证配置修复测试
- `jwt_token_test.py` - JWT 令牌测试
- `simple_api_test.py` - 简单 API 测试

### 综合测试
- `test_end_to_end_*` - 端到端功能测试
- `final_docker_push_test.py` - 最终 Docker 推送测试
- `verify_*.py` - 各种功能验证脚本

## 使用方法

### 运行单个测试
```bash
cd /path/to/ansflow
uv run python scripts/tests/test_docker_push_fix.py
```

### 运行相关测试组
```bash
# Docker 相关测试
uv run python scripts/tests/test_docker_push_fix.py
uv run python scripts/tests/test_registry_configuration_fix.py

# Git 相关测试
uv run python scripts/tests/test_git_clone_detection.py
uv run python scripts/tests/test_git_credential_fix.py
```

## 测试环境要求

- Python 3.11+
- Django 环境已配置
- uv 包管理器
- 相关服务（数据库、Redis 等）已启动

## 注意事项

1. 测试脚本需要在 Django 环境中运行
2. 部分测试需要实际的网络连接和外部服务
3. 测试可能会创建临时文件和目录
4. 建议在开发环境中运行，避免影响生产数据

## 贡献指南

添加新测试时请遵循以下规范：
- 文件名以 `test_` 开头
- 包含完整的文档字符串
- 使用适当的错误处理
- 清理测试过程中创建的临时资源
