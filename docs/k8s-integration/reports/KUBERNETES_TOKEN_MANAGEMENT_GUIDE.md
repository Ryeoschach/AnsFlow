# Kubernetes Token 智能管理使用指南

## 🎯 功能概述

AnsFlow 的 Kubernetes Token 智能管理系统解决了 Kubernetes 集群 Token 过期的常见问题，提供全面的 Token 生命周期管理解决方案。

### ✨ 主要功能

1. **智能 Token 分析** - 自动检测 Token 类型、过期时间和有效性
2. **实时连接验证** - 缓存优化的连接状态检查
3. **个性化更新建议** - 基于当前状态的智能建议系统
4. **完整更新指南** - 详细的步骤说明和命令示例
5. **自动化脚本生成** - 提供现成的自动化更新脚本

---

## 🚀 快速开始

### 1. 访问 Token 管理器

在 **Kubernetes 集群管理** 页面中：

1. 找到需要管理 Token 的集群
2. 点击操作列中的 **🔧 Token 管理** 按钮
3. Token 管理器将自动打开并分析当前状态

### 2. 查看 Token 状态

Token 管理器会显示：

- **状态概览** - Token 的整体健康状况
- **过期时间** - 剩余有效期和使用进度
- **连接信息** - 集群版本、节点状态等
- **智能建议** - 基于当前状态的行动建议

---

## 📊 状态解读

### Token 状态类型

| 状态 | 图标 | 含义 | 建议行动 |
|------|------|------|----------|
| ✅ **有效** | 🟢 | Token 工作正常 | 定期检查即可 |
| ⚠️ **警告** | 🟡 | Token 即将过期 | 准备更新计划 |
| ❌ **无效** | 🔴 | Token 无法连接 | 立即更新 Token |
| ℹ️ **未配置** | 🔵 | 未设置 Token | 配置新 Token |

### 状态详情说明

#### 🟢 Token 有效
- **过期时间**: 显示具体过期日期和剩余天数
- **连接状态**: 显示集群版本和节点信息
- **建议**: 考虑实施长期认证策略

#### 🟡 Token 警告
- **即将过期**: 通常在 24 小时内过期
- **建议**: 提前准备新 Token，避免服务中断
- **预警阈值**: 可在设置中调整

#### 🔴 Token 无效
- **常见原因**:
  - Token 已过期
  - Token 格式错误
  - 集群连接问题
  - 权限不足
- **立即行动**: 按照更新指南生成新 Token

---

## 🛠️ Token 更新流程

### 方法一：快速更新（推荐）

1. **打开更新指南**
   - 在 Token 管理器中点击 "更新指南"
   - 按照步骤执行命令

2. **生成新 Token**
   ```bash
   # 创建 Service Account
   kubectl create serviceaccount ansflow-sa -n default
   
   # 绑定权限
   kubectl create clusterrolebinding ansflow-binding \
     --clusterrole=cluster-admin \
     --serviceaccount=default:ansflow-sa
   
   # 生成 Token（1年有效期）
   kubectl create token ansflow-sa --duration=8760h
   ```

3. **更新 AnsFlow 配置**
   - 编辑集群配置
   - 粘贴新 Token
   - 测试连接
   - 保存配置

### 方法二：永久 Token（适合生产环境）

1. **创建 Secret**
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: ansflow-sa-token
     annotations:
       kubernetes.io/service-account.name: ansflow-sa
   type: kubernetes.io/service-account-token
   ```

2. **获取 Token**
   ```bash
   kubectl get secret ansflow-sa-token -o jsonpath="{.data.token}" | base64 -d
   ```

3. **更新配置**
   - 在 AnsFlow 中更新 Token
   - 验证连接状态

---

## 🤖 自动化解决方案

### 自动化脚本

Token 管理器提供完整的自动化脚本，支持：

- **定期检查** Token 状态
- **自动生成** 新 Token
- **API 更新** AnsFlow 配置
- **错误处理** 和重试机制

### 使用自动化脚本

1. **下载脚本**
   - 在 Token 管理器的 "自动化选项" 标签页
   - 复制提供的脚本内容

2. **配置环境变量**
   ```bash
   export ANSFLOW_API_URL="http://your-ansflow-instance/api"
   export CLUSTER_ID="your-cluster-id"
   export ANSFLOW_TOKEN="your-ansflow-api-token"
   ```

3. **设置定时任务**
   ```bash
   # 编辑 crontab
   crontab -e
   
   # 添加每月执行的任务
   0 0 1 * * /path/to/token-update-script.sh --cron
   ```

---

## 🔧 高级配置

### 认证方式对比

| 认证方式 | 有效期 | 安全性 | 管理复杂度 | 推荐场景 |
|----------|--------|--------|------------|----------|
| **Token** | 可配置 | 中等 | 简单 | 开发测试 |
| **Kubeconfig** | 长期 | 高 | 中等 | 生产环境 |
| **证书** | 很长 | 很高 | 复杂 | 企业级 |

### 切换认证方式

#### 从 Token 切换到 Kubeconfig

1. **导出当前配置**
   ```bash
   kubectl config view --raw > kubeconfig.yaml
   ```

2. **在 AnsFlow 中配置**
   - 编辑集群
   - 选择 "Kubeconfig 认证"
   - 上传配置文件

3. **测试新配置**
   - 验证连接状态
   - 确认功能正常

#### 从 Token 切换到证书认证

1. **生成客户端证书**
   ```bash
   # 生成私钥
   openssl genrsa -out client.key 2048
   
   # 生成证书请求
   openssl req -new -key client.key -out client.csr
   
   # 使用 CA 签名
   openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -out client.crt
   ```

2. **配置 AnsFlow**
   - 选择 "证书认证"
   - 上传客户端证书和私钥
   - 配置 CA 证书

---

## 🔍 故障排除

### 常见问题及解决方案

#### 1. Token 生成失败

**问题**: `kubectl create token` 命令失败

**解决方案**:
```bash
# 检查 Service Account 是否存在
kubectl get serviceaccount ansflow-sa

# 检查权限绑定
kubectl get clusterrolebinding ansflow-binding

# 重新创建 Service Account
kubectl delete serviceaccount ansflow-sa
kubectl create serviceaccount ansflow-sa
```

#### 2. 连接测试失败

**问题**: Token 更新后连接仍然失败

**可能原因**:
- API Server 地址错误
- 网络连通性问题
- 证书验证失败
- 权限不足

**排查步骤**:
```bash
# 测试网络连通性
curl -k https://your-k8s-api:6443/version

# 验证 Token 权限
kubectl auth can-i "*" "*" --token="your-token"

# 检查证书
openssl s_client -connect your-k8s-api:6443 -servername kubernetes
```

#### 3. 权限不足

**问题**: Token 有效但操作失败

**解决方案**:
```bash
# 检查当前权限
kubectl auth can-i --list --token="your-token"

# 重新绑定管理员权限
kubectl create clusterrolebinding ansflow-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=default:ansflow-sa
```

#### 4. Token 格式错误

**问题**: Token 无法解析

**解决方案**:
- 确保 Token 完整复制，没有多余空格
- 检查 Token 是否是 Base64 编码
- 验证 Token 格式是否正确

---

## 📈 最佳实践

### 生产环境建议

1. **使用长期有效的 Token**
   - 创建 Secret 方式的永久 Token
   - 或使用 Kubeconfig/证书认证

2. **实施监控机制**
   - 设置定期检查
   - 配置过期提醒
   - 实现自动化更新

3. **遵循最小权限原则**
   - 不要使用 cluster-admin 权限
   - 创建专用的 Role 和 RoleBinding
   - 定期审计权限

4. **备份认证信息**
   - 保存多个有效 Token
   - 备份 Kubeconfig 文件
   - 准备应急恢复方案

### 安全考虑

1. **Token 存储安全**
   - 不要在代码中硬编码 Token
   - 使用环境变量或密钥管理服务
   - 定期轮换 Token

2. **网络安全**
   - 使用 HTTPS 连接
   - 验证 CA 证书
   - 限制网络访问

3. **审计日志**
   - 记录所有 Token 使用
   - 监控异常访问
   - 定期审查权限

---

## 🆘 技术支持

如果您在使用过程中遇到问题：

1. **查看日志**
   - 检查 AnsFlow 服务日志
   - 查看 Kubernetes 审计日志
   - 分析网络连接日志

2. **使用诊断工具**
   - Token 管理器的状态分析
   - 连接测试功能
   - 错误信息提示

3. **联系支持**
   - 技术支持: support@ansflow.com
   - 开发团队: dev@ansflow.com
   - 社区论坛: [GitHub Issues](https://github.com/ansflow/ansflow/issues)

---

## 🔄 版本更新

### v1.0 功能特性
- ✅ 基础 Token 分析和验证
- ✅ 智能更新建议
- ✅ 完整更新指南
- ✅ 自动化脚本生成

### 未来规划
- 🚧 多集群 Token 批量管理
- 🚧 Token 过期邮件提醒
- 🚧 与 CI/CD 系统集成
- 🚧 高级权限管理

---

**最后更新**: 2025年8月12日  
**文档版本**: v1.0  
**维护团队**: AnsFlow 开发团队
