# Kubernetes 集成使用指南

## 概述

AnsFlow CI/CD 平台现已完成 Kubernetes 集成，支持在流水线中使用 Docker 和 Kubernetes 步骤。本指南将介绍如何使用这些功能。

## 快速开始

### 1. 环境准备

```bash
# 使用 UV 设置开发环境
./uv-setup.sh

# 或手动配置
cd backend/django_service
uv venv
source .venv/bin/activate
uv pip install -e .
```

### 2. 验证配置

```bash
# 运行验证脚本
python3 verify_kubernetes_integration.py
```

## 功能特性

### ✅ 已完成功能

1. **数据模型**
   - KubernetesCluster：集群管理
   - KubernetesNamespace：命名空间管理  
   - KubernetesDeployment：部署管理
   - KubernetesService：服务管理
   - KubernetesPod：Pod 管理
   - KubernetesConfigMap：配置映射
   - KubernetesSecret：密钥管理

2. **REST API**
   - 完整的 CRUD 操作
   - 自定义 action（同步、部署、扩缩容等）
   - 统一的错误处理和响应格式

3. **Kubernetes 客户端**
   - 支持多种认证方式（kubeconfig、token、集群内认证）
   - 模拟模式（无需真实集群）
   - 完整的资源操作 API

4. **异步任务**
   - Celery 集成
   - 后台资源同步
   - 应用部署和管理
   - 定期清理任务

## API 使用示例

### 创建集群

```bash
curl -X POST http://localhost:8000/api/v1/kubernetes/clusters/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "my-cluster",
    "description": "开发环境集群",
    "api_server": "https://kubernetes.example.com:6443",
    "auth_config": {
      "type": "kubeconfig",
      "kubeconfig": "apiVersion: v1\nkind: Config\n..."
    }
  }'
```

### 部署应用

```bash
curl -X POST http://localhost:8000/api/v1/kubernetes/deployments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "my-app",
    "namespace": 1,
    "image": "nginx:latest",
    "replicas": 3,
    "config": {
      "ports": [{"container_port": 80}],
      "environment_vars": {"ENV": "production"}
    }
  }'
```

### 扩缩容

```bash
curl -X POST http://localhost:8000/api/v1/kubernetes/deployments/1/scale/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"replicas": 5}'
```

## 流水线集成

### Docker 步骤类型（建议）

```yaml
pipeline:
  name: "Docker Build Pipeline"
  steps:
    - name: "构建镜像"
      type: "docker_build"
      config:
        dockerfile: "./Dockerfile"
        image_name: "my-app"
        tag: "{{ build_number }}"
        
    - name: "推送镜像"
      type: "docker_push"
      config:
        image: "my-app:{{ build_number }}"
        registry: "registry.example.com"
        username: "{{ env.REGISTRY_USER }}"
        password: "{{ env.REGISTRY_PASS }}"
```

### Kubernetes 步骤类型（建议）

```yaml
pipeline:
  name: "K8s Deployment Pipeline"
  steps:
    - name: "部署到开发环境"
      type: "k8s_deploy"
      config:
        cluster_id: 1
        namespace: "development"
        deployment_spec:
          name: "my-app"
          image: "my-app:{{ build_number }}"
          replicas: 2
          
    - name: "等待部署就绪"
      type: "k8s_wait"
      config:
        resource_type: "deployment"
        resource_name: "my-app"
        namespace: "development"
        condition: "available"
        timeout: 300
        
    - name: "运行健康检查"
      type: "k8s_exec"
      config:
        pod_selector: "app=my-app"
        namespace: "development"
        command: "curl -f http://localhost:8080/health"
```

## 本地开发环境

### 使用 minikube

```bash
# 安装和启动 minikube
brew install minikube
minikube start

# 获取集群信息
kubectl cluster-info
kubectl config view --raw > ~/.kube/config
```

### 使用 kind

```bash
# 安装 kind
brew install kind

# 创建集群
kind create cluster --name ansflow-dev

# 获取 kubeconfig
kubectl config view --raw > ~/.kube/config
```

### 使用 k3s（Linux）

```bash
# 安装 k3s
curl -sfL https://get.k3s.io | sh -

# 获取 kubeconfig
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER ~/.kube/config
```

## 认证配置

### 1. kubeconfig 方式

```python
auth_config = {
    "type": "kubeconfig",
    "kubeconfig": "apiVersion: v1\nkind: Config\n..."
}
```

### 2. Service Account Token 方式

```python
auth_config = {
    "type": "service_account",
    "token": "eyJhbGciOiJSUzI1NiIs...",
    "api_server": "https://kubernetes.example.com:6443",
    "ca_cert": "-----BEGIN CERTIFICATE-----\n..."
}
```

### 3. 集群内认证

```python
auth_config = {
    "type": "incluster"
}
```

## 监控和调试

### 查看任务状态

```python
from kubernetes_integration.tasks import check_cluster_status

# 异步执行
result = check_cluster_status.delay(cluster_id=1)

# 检查状态
print(result.status)
print(result.result)
```

### 查看日志

```python
from kubernetes_integration.models import KubernetesCluster
from kubernetes_integration.k8s_client import KubernetesManager

cluster = KubernetesCluster.objects.get(id=1)
manager = KubernetesManager(cluster)

# 获取 Pod 日志
logs = manager.get_pod_logs("my-pod", "default", tail_lines=100)
print(logs)
```

## 安全注意事项

1. **认证信息加密**：敏感信息使用 Django 的加密字段存储
2. **权限控制**：使用 RBAC 限制集群访问权限
3. **网络安全**：配置防火墙和网络策略
4. **镜像安全**：使用可信镜像仓库和签名验证

## 故障排除

### 常见问题

1. **连接失败**
   ```
   检查 API 服务器地址和认证信息
   确认网络连通性
   验证证书有效性
   ```

2. **权限不足**
   ```
   检查 Service Account 权限
   确认 RBAC 配置
   验证命名空间访问权限
   ```

3. **部署失败**
   ```
   检查镜像是否存在
   验证资源配额
   确认节点资源充足
   ```

### 调试模式

启用模拟模式进行测试：

```python
# 在 settings.py 中
KUBERNETES_SIMULATION_MODE = True
```

## 性能优化

1. **资源配额**：设置合理的 CPU 和内存限制
2. **自动扩缩容**：配置 HPA（Horizontal Pod Autoscaler）
3. **节点亲和性**：优化 Pod 调度
4. **持久化存储**：使用 PV/PVC 管理存储

## 下一步开发

### 优先级高

1. **流水线步骤类型扩展**：在流水线模块中添加 Docker/K8s 步骤类型
2. **前端界面**：开发 K8s 资源管理页面
3. **单元测试**：补充测试用例

### 优先级中

1. **Helm 集成**：支持 Helm Chart 部署
2. **监控集成**：Prometheus/Grafana 仪表板
3. **CI/CD 模板**：预定义的部署模板

### 优先级低

1. **服务网格**：Istio/Linkerd 集成
2. **GitOps**：ArgoCD/Flux 集成
3. **多集群管理**：跨集群资源管理

## 总结

✅ **Kubernetes 集成已完成**，具备以下特点：

- 🏗️ **架构完善**：后端模块、API、客户端全面实现
- 🔧 **灵活配置**：支持多种认证方式和部署模式
- 🎯 **易于扩展**：模块化设计，便于添加新功能
- 🛡️ **安全可靠**：完善的权限控制和错误处理
- 📱 **开发友好**：模拟模式和详细日志

**Docker/K8s 步骤完全可以集成到本地类型的流水线中**，为 AnsFlow 平台提供强大的容器化和编排能力！
