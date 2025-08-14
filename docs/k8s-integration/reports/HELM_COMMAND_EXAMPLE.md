# Kubernetes Deploy Helm 命令示例

## 基于你的本地Chart配置

### 📁 你的Chart目录结构
```
/Users/creed/Workspace/k8s_images/temp/fe-app/
├── Chart.yaml          # Chart元数据
├── charts/             # 依赖Chart目录
├── templates/          # K8s模板文件
└── values.yaml         # 默认配置值
```

### 🎯 流水线步骤配置
1. **第一步**: `cd /Users/creed/Workspace/k8s_images/temp/fe-app`
2. **第二步**: Kubernetes Deploy (选择Helm)
   - Chart名称: `fe-app`
   - Release名称: `fe-app-release` (用户配置)
   - 命名空间: `default` (用户配置)

### 🚀 系统生成的实际Helm命令

#### 基础命令 (最小配置)
```bash
helm upgrade --install fe-app-release . \
  --namespace default --create-namespace \
  --wait
```

#### 完整命令 (包含所有可选配置)
```bash
helm upgrade --install fe-app-release . \
  --namespace default \
  --create-namespace \
  --version 1.0.0 \
  --values ./custom-values.yaml \
  --values /tmp/custom_values_temp.yaml \
  --wait \
  --atomic \
  --timeout 600s \
  --dry-run
```

### 📝 命令参数详解

| 参数 | 说明 | 前端配置对应 |
|------|------|-------------|
| `upgrade --install` | 如果Release不存在则安装，存在则升级 | `helm_upgrade: true` (默认) |
| `fe-app-release` | Release名称，用户自定义 | `release_name` 字段 |
| `.` | Chart路径，当前目录(智能识别结果) | `chart_name: "fe-app"` → 智能转换 |
| `--namespace default` | 目标命名空间 | `k8s_namespace` 字段 |
| `--create-namespace` | 如果命名空间不存在则创建 | 系统自动添加 |
| `--version 1.0.0` | Chart版本 | `chart_version` 字段 |
| `--values file.yaml` | Values文件路径 | `values_file` 字段 |
| `--values /tmp/xxx.yaml` | 自定义Values临时文件 | `custom_values` 字段内容 |
| `--wait` | 等待部署完成 | `helm_wait: true` (默认) |
| `--atomic` | 失败时自动回滚 | `helm_atomic` 选项 |
| `--timeout 600s` | 超时时间 | `helm_timeout` 字段 |
| `--dry-run` | 模拟运行，不实际部署 | `dry_run` 选项 |

### 🔧 智能识别逻辑

当你输入Chart名称 `fe-app` 时，系统会依次尝试：

#### ✅ 策略1: 当前目录检查 (你的情况)
```python
# 检查 /Users/creed/Workspace/k8s_images/temp/fe-app/Chart.yaml
if os.path.exists('Chart.yaml'):
    final_chart_name = "."  # 使用当前目录
```

#### 策略2: 常见目录查找 (如果策略1失败)
```python
possible_paths = [
    "./fe-app",           # ./fe-app/Chart.yaml
    "./charts/fe-app",    # ./charts/fe-app/Chart.yaml  
    "./helm/fe-app",      # ./helm/fe-app/Chart.yaml
    "./k8s/fe-app",       # ./k8s/fe-app/Chart.yaml
    "fe-app"              # fe-app/Chart.yaml
]
```

#### 策略3: 远程仓库回退 (如果本地都找不到)
```bash
helm repo add stable https://charts.helm.sh/stable && \
helm repo update && \
helm upgrade --install fe-app-release stable/fe-app ...
```

### 📊 你的实际情况分析

✅ **完美匹配策略1**: 
- 工作目录: `/Users/creed/Workspace/k8s_images/temp/fe-app` 
- Chart.yaml存在: ✅ 
- 最终Chart路径: `.` (当前目录)
- 命令效果: 直接使用你本地的Chart进行部署

### 🎉 执行结果

系统会执行类似这样的命令：
```bash
helm upgrade --install fe-app-release . \
  --namespace default --create-namespace \
  --wait --timeout 300s
```

这个命令会：
1. 在`default`命名空间中创建或更新名为`fe-app-release`的Release
2. 使用当前目录(`.`)的Chart文件
3. 等待所有资源部署完成
4. 最大等待5分钟(300秒)

### 🔍 调试信息

执行时你会在日志中看到：
```
🔧 Chart名称 'fe-app' 看起来像是Chart包名，开始智能识别...
✅ 当前工作目录就是Chart目录: /Users/creed/Workspace/k8s_images/temp/fe-app
🚀 构建的Helm命令: helm upgrade --install fe-app-release . --namespace default --create-namespace --wait --timeout 300s
```
