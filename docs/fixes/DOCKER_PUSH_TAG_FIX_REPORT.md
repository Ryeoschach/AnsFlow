# Docker Push 标签修复报告

## 🎯 问题描述
用户报告 Docker push 失败，错误信息为：
```
Docker push failed: Docker标记失败: Error response from daemon: No such image: myapp:latest
```

**用户配置：**
```json
{
  "tag": "0722",
  "image": "myapp",
  "project_id": 5,
  "registry_id": 5,
  "docker_config": {}
}
```

**问题分析：**
- 用户明确指定了 tag 为 "0722"
- 但错误信息显示系统在寻找 "myapp:latest"
- 表明标签参数未正确传递给 Docker 命令

## 🔍 根本原因
在 `DockerStepExecutor._execute_docker_push` 方法中，调用 `docker_manager.tag_image(image_name, full_image_name)` 时：

**修复前的问题代码：**
```python
# 标记镜像
if full_image_name != image_name:
    docker_manager.tag_image(image_name, full_image_name)  # ❌ image_name 只是 "myapp"，没有标签
```

**问题分析：**
1. `image_name` 变量只包含镜像名（如 "myapp"），不包含标签
2. Docker 的 `tag` 命令需要完整的源镜像名（包括标签）
3. 当 `image_name` 不包含标签时，Docker 默认查找 `:latest` 标签
4. 因此 `docker tag myapp reg.cyfee.com:10443/production/myapp:0722` 实际执行的是 `docker tag myapp:latest ...`

## 🛠️ 修复方案

**修复后的代码：**
```python
# 构建本地镜像名称（包含标签）
local_image_name = f"{image_name}:{tag}" if ':' not in image_name else image_name

# 标记镜像
if full_image_name != local_image_name:
    logger.info(f"Docker push - 标记镜像: {local_image_name} -> {full_image_name}")
    docker_manager.tag_image(local_image_name, full_image_name)  # ✅ 使用包含标签的完整镜像名
```

**修复内容：**
1. 创建 `local_image_name` 变量，确保包含正确的标签
2. 如果 `image_name` 不包含 `:`，则添加用户指定的标签
3. 如果已包含 `:`，则保持原样（用户可能已指定完整名称）
4. 在 `tag_image` 调用中使用 `local_image_name` 而不是 `image_name`

## ✅ 修复验证

**测试结果：**
```bash
🚀 执行Docker Push步骤...
INFO Docker push - 使用参数指定的注册表: harbor (ID: 5)
INFO Docker push - 使用项目路径: production
INFO Docker push - 完整镜像名称: reg.cyfee.com:10443/production/myapp:0722
INFO Docker push - 标记镜像: myapp:0722 -> reg.cyfee.com:10443/production/myapp:0722  # ✅ 正确
INFO [模拟] 执行Docker命令: docker tag myapp:0722 reg.cyfee.com:10443/production/myapp:0722
INFO [模拟] 执行Docker命令: docker push reg.cyfee.com:10443/production/myapp:0722
✅ Docker Push执行成功!
```

**修复前后对比：**
- **修复前**：`docker tag myapp:latest reg.cyfee.com:10443/production/myapp:0722` ❌
- **修复后**：`docker tag myapp:0722 reg.cyfee.com:10443/production/myapp:0722` ✅

## 🎯 影响范围
- **修复文件**：`backend/django_service/pipelines/services/docker_executor.py`
- **修复方法**：`DockerStepExecutor._execute_docker_push`
- **影响功能**：所有 Docker push 操作的标签处理
- **向后兼容**：✅ 完全兼容，不影响现有功能

## 📋 测试用例验证
测试了多种镜像名格式，均正确处理：

| 输入镜像 | 输入标签 | 期望结果 | 实际结果 | 状态 |
|---------|----------|----------|----------|------|
| `myapp` | `0722` | `myapp:0722` | `myapp:0722` | ✅ |
| `myapp:latest` | `0722` | `myapp:latest` | `myapp:latest` | ✅ |
| `nginx` | `alpine` | `nginx:alpine` | `nginx:alpine` | ✅ |
| `registry.com/myapp` | `v1.0` | `registry.com/myapp:v1.0` | `registry.com/myapp:v1.0` | ✅ |

## 🚀 用户操作指南
修复后，用户可以正常使用原配置：
```json
{
  "tag": "0722",
  "image": "myapp",
  "project_id": 5,
  "registry_id": 5,
  "docker_config": {}
}
```

系统现在会：
1. 正确识别用户指定的标签 "0722"
2. 构建本地镜像名 "myapp:0722"
3. 执行正确的标记命令
4. 成功推送到目标仓库

## 📝 总结
这是一个标准的参数传递和字符串处理问题。修复确保了 Docker 标签参数的正确处理，解决了用户遇到的 "No such image: myapp:latest" 错误。修复具有完全的向后兼容性，不会影响现有的工作流程。
