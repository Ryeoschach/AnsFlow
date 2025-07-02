# Git凭据测试工具集

## 工具概述

本目录包含AnsFlow Git凭据管理的完整测试和诊断工具链，用于排查和修复Git凭据连接问题。

## 工具列表

### 1. diagnose_git_credentials.py - 全面诊断工具

**用途：** 对所有Git凭据进行全面诊断和测试

**功能：**
- 获取所有Git凭据列表
- 逐一测试每个凭据的连接状态
- 分析错误原因并提供修复建议
- 支持GitHub、GitLab、Gitee等多平台

**使用方法：**
```bash
cd /Users/creed/workspace/sourceCode/AnsFlow
python scripts/git_credential_tools/diagnose_git_credentials.py
```

**适用场景：**
- 系统性检查所有凭据状态
- 初次部署后的验证
- 定期健康检查

### 2. test_gitlab_only.py - GitLab专项测试

**用途：** 专门测试GitLab凭据，排除其他平台干扰

**功能：**
- 过滤并测试所有GitLab凭据
- 测试GitLab连通性（Web + API）
- 提供GitLab特定的错误分析
- 专门的GitLab问题解决方案

**使用方法：**
```bash
cd /Users/creed/workspace/sourceCode/AnsFlow
python scripts/git_credential_tools/test_gitlab_only.py
```

**适用场景：**
- GitLab凭据连接问题
- 本地GitLab服务验证
- GitLab特定的故障排查

### 3. reset_gitlab_credential.py - 凭据重置工具

**用途：** 重置损坏或有问题的GitLab凭据

**功能：**
- 交互式选择要重置的凭据
- 安全更新凭据密码
- 立即测试更新后的连接
- 支持批量重置

**使用方法：**
```bash
cd /Users/creed/workspace/sourceCode/AnsFlow
python scripts/git_credential_tools/reset_gitlab_credential.py
```

**适用场景：**
- 凭据密码修改后出现问题
- 加密解密失败
- 需要强制更新凭据

### 4. test_direct_gitlab.py - 直接测试工具

**用途：** 绕过API直接调用后端测试类，用于调试

**功能：**
- 直接调用GitCredentialTester类
- 绕过API层进行测试
- 调试后端测试逻辑
- 验证加密解密功能

**使用方法：**
```bash
cd /Users/creed/workspace/sourceCode/AnsFlow
python scripts/git_credential_tools/test_direct_gitlab.py
```

**适用场景：**
- 后端逻辑调试
- API层问题排查
- 加密解密验证

### 5. test_api_fields.py - API字段测试

**用途：** 验证API返回的字段是否正确

**功能：**
- 测试凭据列表API字段
- 测试凭据详情API字段
- 验证新增字段（has_password, has_ssh_key）
- API结构验证

**使用方法：**
```bash
cd /Users/creed/workspace/sourceCode/AnsFlow
python scripts/git_credential_tools/test_api_fields.py
```

**适用场景：**
- API开发验证
- 字段更新后的测试
- 前后端接口联调

## 使用流程

### 日常故障排查流程

1. **初步诊断**
   ```bash
   python scripts/git_credential_tools/diagnose_git_credentials.py
   ```

2. **GitLab专项检查**（如果是GitLab问题）
   ```bash
   python scripts/git_credential_tools/test_gitlab_only.py
   ```

3. **凭据重置**（如果凭据损坏）
   ```bash
   python scripts/git_credential_tools/reset_gitlab_credential.py
   ```

### 开发调试流程

1. **API字段验证**
   ```bash
   python scripts/git_credential_tools/test_api_fields.py
   ```

2. **后端逻辑测试**
   ```bash
   python scripts/git_credential_tools/test_direct_gitlab.py
   ```

3. **完整功能验证**
   ```bash
   python scripts/git_credential_tools/test_gitlab_only.py
   ```

## 常见问题解决

### 问题1: 认证失败

**症状：** API返回"authentication failed"

**排查步骤：**
1. 运行`test_gitlab_only.py`检查GitLab连通性
2. 确认用户名密码正确
3. 检查GitLab是否启用2FA
4. 使用`reset_gitlab_credential.py`重新设置凭据

### 问题2: 密码解密失败

**症状：** 出现"密码解密失败"错误

**排查步骤：**
1. 检查Django settings中的`GIT_CREDENTIAL_ENCRYPTION_KEY`
2. 运行`test_direct_gitlab.py`验证加密解密
3. 使用`reset_gitlab_credential.py`重新设置凭据

### 问题3: 仓库不存在

**症状：** "repository not found"错误

**解释：** 这通常是正常的，只要认证成功即可

**验证：** 运行`test_gitlab_only.py`查看完整测试结果

### 问题4: API字段缺失

**症状：** 前端无法获取正确的凭据状态

**排查步骤：**
1. 运行`test_api_fields.py`检查API返回
2. 确认Django服务已重启
3. 检查序列化器配置

## 配置要求

### 环境要求
- Python 3.8+
- Django项目正常运行
- AnsFlow服务启动（http://localhost:8000）

### 依赖包
- requests
- django（通过项目环境）
- cryptography（通过项目环境）

### 认证配置
- AnsFlow管理员账号：admin/admin123
- GitLab服务运行：http://127.0.0.1:8929
- GitLab root账号配置

## 注意事项

1. **运行环境：** 所有脚本需要在AnsFlow项目根目录运行
2. **服务依赖：** 确保Django服务和GitLab服务正常运行
3. **权限要求：** 使用admin账号进行测试
4. **数据安全：** 重置工具会修改数据库中的凭据，请谨慎使用
5. **网络连接：** 确保能访问GitLab服务（127.0.0.1:8929）

## 脚本维护

### 添加新的测试脚本
1. 在此目录创建新的`.py`文件
2. 更新本README文档
3. 确保脚本包含适当的错误处理和用户提示

### 修改现有脚本
1. 测试修改后的功能
2. 更新相关文档
3. 验证不影响其他工具的使用

---

**维护者：** AnsFlow开发团队  
**最后更新：** 2025年7月2日  
**版本：** v1.0
