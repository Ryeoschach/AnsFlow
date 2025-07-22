# Docker 推送到错误仓库问题诊断与解决方案

## 问题症状
用户报告：Docker 推送失败，推送到了 `registry-1.docker.io` 而不是指定的 Harbor 注册表 (ID: 5)
错误信息：`Docker推送失败: Get "https://registry-1.docker.io/v2/": context deadline exceeded`

## 诊断结果

### ✅ 代码逻辑检查 - 正常
通过详细测试确认：
- 注册表选择逻辑**完全正确**
- 步骤参数 `registry_id: 5` 正确传递
- 镜像名构造正确：`reg.cyfee.com:10443/test:072201`
- DockerStepExecutor 逻辑无问题

### ❌ 认证配置问题 - 已发现
**根本原因**：Harbor 注册表 (ID: 5) 缺少有效的认证配置

#### 问题详情：
1. **缺少密码**: Harbor 注册表的 `auth_config` 为空 `{}`
2. **认证失败**: Docker 登录到 Harbor 时返回 `unauthorized` 错误
3. **回退行为**: Docker 可能因认证失败而回退到 Docker Hub

#### 测试证据：
```bash
# Harbor 注册表配置
ID: 5
名称: harbor
URL: https://reg.cyfee.com:10443
用户名: admin
认证配置: {} # <- 这是问题所在

# 错误信息
ERROR: Docker登录失败: Error response from daemon: Get "https://reg.cyfee.com:10443/v2/": unauthorized
```

## 解决方案

### 方案1: 配置正确的 Harbor 认证信息

#### 1.1 设置 Harbor 管理员密码
```python
# 在 Django shell 中执行
from docker_integration.models import DockerRegistry

harbor = DockerRegistry.objects.get(id=5)
harbor.auth_config = {
    'password': 'YOUR_REAL_HARBOR_PASSWORD'  # 替换为真实密码
}
harbor.save()
```

#### 1.2 验证 Harbor 服务状态
```bash
# 检查 Harbor 服务是否运行
curl -k https://reg.cyfee.com:10443/api/v2.0/health

# 测试 Docker 登录
docker login reg.cyfee.com:10443 -u admin -p YOUR_PASSWORD
```

#### 1.3 网络连接检查
```bash
# 检查网络连通性
ping reg.cyfee.com
telnet reg.cyfee.com 10443

# 检查 SSL 证书
openssl s_client -connect reg.cyfee.com:10443 -servername reg.cyfee.com
```

### 方案2: 使用 GitLab 注册表作为替代

如果 Harbor 不可用，可以使用已配置的 GitLab 注册表：

```python
# 更新步骤使用 GitLab 注册表
step = AtomicStep.objects.get(id=129)
step.parameters['registry_id'] = 4  # GitLab 注册表
step.save()
```

### 方案3: 临时使用 Docker Hub

```python
# 移除 registry_id，使用默认 Docker Hub
step = AtomicStep.objects.get(id=129)
step.parameters.pop('registry_id', None)
step.save()
```

## 预防措施

### 1. 注册表健康检查
添加注册表连接测试功能：
```python
def test_registry_connection(registry_id):
    registry = DockerRegistry.objects.get(id=registry_id)
    # 实现连接测试逻辑
    return success, message
```

### 2. 认证配置验证
在创建/更新注册表时验证认证信息：
```python
def validate_registry_auth(registry):
    if not registry.auth_config or not registry.auth_config.get('password'):
        raise ValidationError("注册表缺少认证配置")
```

### 3. 失败回退策略
修改 DockerStepExecutor 添加更好的错误处理：
```python
def _execute_docker_push_with_fallback(self, step, context):
    try:
        # 尝试使用指定注册表
        return self._execute_docker_push(step, context)
    except AuthenticationError:
        logger.warning("指定注册表认证失败，考虑使用备用注册表")
        # 不要自动回退到 Docker Hub，而是明确报错
        raise Exception("注册表认证失败，请检查配置")
```

## 立即行动项

### 高优先级
1. **配置 Harbor 密码**: 设置正确的 Harbor 管理员密码
2. **验证 Harbor 服务**: 确保 Harbor 在指定地址运行
3. **测试连接**: 手动测试 Docker 登录到 Harbor

### 中优先级
1. **更新前端**: 在注册表管理界面添加连接测试功能
2. **添加验证**: 创建注册表时强制测试连接
3. **改进错误处理**: 提供更明确的错误信息

### 低优先级
1. **监控告警**: 添加注册表健康状态监控
2. **文档更新**: 更新注册表配置文档
3. **自动化测试**: 添加注册表集成测试

## 状态总结

| 组件 | 状态 | 说明 |
|------|------|------|
| 代码逻辑 | ✅ 正常 | 注册表选择和镜像名构造正确 |
| 步骤配置 | ✅ 正常 | `registry_id: 5` 正确传递 |
| Harbor 认证 | ❌ 问题 | 缺少有效密码配置 |
| Harbor 服务 | ❓ 未知 | 需要验证服务状态 |
| 网络连接 | ❓ 未知 | 需要测试连通性 |

**结论**: 问题根源是 Harbor 注册表的认证配置不完整，导致 Docker 登录失败。修复认证配置后，Docker 推送应该能正确推送到指定的 Harbor 注册表。
