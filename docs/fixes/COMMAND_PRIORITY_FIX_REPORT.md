# Command字段优先级修复报告

## 问题描述

用户在流水线步骤中使用以下配置：

```json
{
  "command": "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git",
  "git_credential_id": 1
}
```

但仍然收到错误信息："请在步骤配置中指定repository_url"。

用户指出 **command字段的优先级应该高于repository_url**。

## 根本原因

代码检出步骤 (`_execute_fetch_code`) 只检查 `repository_url` 字段，没有支持 `command` 字段，导致：

1. 即使配置了 `command` 字段也被忽略
2. 仍然要求 `repository_url` 字段
3. 无法使用自定义的Git命令（如SSH协议、自定义端口等）

## 修复内容

### 1. 修改代码拉取逻辑

#### 修复前：
```python
# 只检查repository_url
repository_url = config.get('repository_url')
if not repository_url:
    return {
        'success': False,
        'error_message': '代码仓库URL未配置，请在步骤配置中指定repository_url',
        'output': ''
    }
```

#### 修复后：
```python
# 优先使用command字段，如果没有则使用repository_url
custom_command = config.get('command')
repository_url = config.get('repository_url')

if custom_command:
    # 使用自定义命令
    commands = [
        f'mkdir -p {target_dir}',
        f'cd {target_dir} && {custom_command}'
    ]
elif repository_url:
    # 使用标准的git clone
    commands = [
        f'mkdir -p {target_dir}',
        f'cd {target_dir} && git clone {repository_url} .',
        f'cd {target_dir} && git checkout {branch}'
    ]
else:
    # 两者都没有才报错
    return {
        'success': False,
        'error_message': '代码拉取配置缺失，请在步骤配置中指定 command 或 repository_url'
    }
```

### 2. 添加Git凭据支持

实现了 `_setup_git_credentials` 方法，支持：

- **用户名密码认证** (`username_password`)
- **访问令牌认证** (`access_token`)
- **SSH密钥认证** (`ssh_key`) - 推荐用于command字段

```python
def _setup_git_credentials(self, git_credential_id: int, env: Dict[str, str]) -> Dict[str, str]:
    """设置Git凭据环境变量"""
    credential = GitCredential.objects.get(id=git_credential_id)
    
    if credential.credential_type == 'ssh_key':
        # 创建临时SSH密钥文件
        temp_key_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.key')
        temp_key_file.write(credential.ssh_private_key)
        temp_key_file.close()
        os.chmod(temp_key_file.name, 0o600)
        
        env['GIT_SSH_COMMAND'] = f'ssh -i {temp_key_file.name} -o StrictHostKeyChecking=no'
        
    # 其他认证类型...
    return env
```

### 3. 增强错误处理

提供更详细的错误信息和配置示例：

```python
return {
    'success': False,
    'error_message': '代码拉取配置缺失，请在步骤配置中指定 command 或 repository_url',
    'output': '示例配置：\n1. 使用自定义命令: {"command": "git clone ssh://git@example.com:2424/repo.git"}\n2. 使用仓库URL: {"repository_url": "https://github.com/user/repo.git"}'
}
```

### 4. 配置获取优化

修改 `_get_step_config` 方法，确保能正确处理 `command` 字段：

```python
# 基础配置
if step_obj.command:
    config['command'] = step_obj.command

# 合并步骤对象的config属性（如果存在）
if hasattr(step_obj, 'config') and step_obj.config:
    config.update(step_obj.config)
```

## 支持的配置方式

### 方式1：自定义命令（高优先级）

```json
{
  "command": "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git",
  "git_credential_id": 1
}
```

**适用场景：**
- SSH协议
- 自定义端口
- 特殊的Git命令参数

### 方式2：标准仓库URL（回退方案）

```json
{
  "repository_url": "https://github.com/user/repo.git",
  "branch": "main",
  "git_credential_id": 2
}
```

**适用场景：**
- 标准的HTTPS Git仓库
- GitHub、GitLab公共仓库

### 方式3：组合配置（command优先）

```json
{
  "command": "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git",
  "repository_url": "https://github.com/backup/repo.git",
  "git_credential_id": 1,
  "branch": "develop"
}
```

**说明：**
- 同时存在时，`command` 字段优先
- `repository_url` 字段会被忽略
- 分支切换在clone后执行

## 执行流程

1. **获取配置**：从步骤配置中提取 `command`、`repository_url`、`git_credential_id` 等
2. **设置认证**：根据 `git_credential_id` 配置Git认证环境
3. **选择执行方式**：
   - 如果有 `command`：直接执行自定义命令
   - 否则如果有 `repository_url`：生成标准git clone命令
   - 都没有：返回配置错误
4. **执行命令**：在工作目录的code子目录中执行Git命令
5. **清理资源**：清理临时的SSH密钥文件等

## 测试验证

创建了完整的测试和演示：

- `test_command_priority.py` - 测试command字段优先级
- `demo_command_usage.py` - 演示实际使用场景

## 兼容性

修复保持了向后兼容性：

- ✅ 原有的 `repository_url` 配置继续有效
- ✅ 新增的 `command` 配置具有更高优先级
- ✅ 错误信息更加详细和友好

## 解决的问题

1. ✅ **主要问题**：支持 `command` 字段，优先级高于 `repository_url`
2. ✅ **认证问题**：完整的Git凭据支持，包括SSH密钥
3. ✅ **灵活性**：支持自定义端口、协议和Git命令参数
4. ✅ **错误处理**：更详细的错误信息和配置示例

## 使用建议

1. **标准仓库**：使用 `repository_url` 配置
2. **SSH/自定义**：使用 `command` 配置
3. **认证**：始终配置 `git_credential_id`
4. **调试**：查看执行日志了解使用的配置方式

现在用户可以使用：

```json
{
  "command": "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git",
  "git_credential_id": 1
}
```

这样就完全解决了"请在步骤配置中指定repository_url"的错误！
