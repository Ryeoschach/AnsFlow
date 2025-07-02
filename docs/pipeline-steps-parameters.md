# AnsFlow 流水线步骤参数说明文档

## 概述

本文档详细说明了AnsFlow平台中各种流水线步骤类型支持的参数，以及这些参数如何转换为不同CI/CD工具（如Jenkins）的Pipeline脚本。

## 通用参数

所有步骤类型都支持以下通用参数：

| 参数名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `command` | string | 自定义shell命令，优先级最高 | `"npm run build"` |
| `script` | string | 自定义脚本内容（备选参数名） | `"echo 'Hello World'"` |

## 步骤类型详细参数

### 1. 代码拉取 (fetch_code / 代码拉取)

从版本控制系统获取源代码。

| 参数名 | 类型 | 默认值 | 说明 | Jenkins转换 |
|--------|------|--------|------|-------------|
| `command` | string | - | 自定义Git命令 | `sh 'command'` |
| `repository` | string | - | Git仓库URL | `userRemoteConfigs: [[url: 'repo_url']]` |
| `repository_url` | string | - | Git仓库URL（别名） | 同上 |
| `branch` | string | `"main"` | 分支名称 | `branches: [[name: 'branch']]` |

**Jenkins转换示例：**
```groovy
// 自定义命令
sh 'git clone https://github.com/user/repo.git'

// 标准checkout
checkout([
    $class: 'GitSCM',
    branches: [[name: 'main']],
    userRemoteConfigs: [[url: 'https://github.com/user/repo.git']]
])
```

### 2. 构建 (build / 构建)

编译和构建应用程序。

| 参数名 | 类型 | 默认值 | 说明 | Jenkins转换 |
|--------|------|--------|------|-------------|
| `command` | string | - | 自定义构建命令（优先级最高） | `sh 'command'` |
| `build_tool` | string | `"npm"` | 构建工具类型 | 决定具体的构建步骤 |
| `build_command` | string | - | 工具特定的构建命令 | 根据build_tool转换 |
| `dockerfile` | string | `"Dockerfile"` | Docker构建文件路径 | `sh 'docker build -f dockerfile'` |
| `tag` | string | `"latest"` | Docker镜像标签 | `sh 'docker build -t tag'` |
| `context` | string | `"."` | Docker构建上下文 | `sh 'docker build context'` |

**构建工具支持：**

#### NPM构建
```json
{
  "build_tool": "npm",
  "build_command": "build"
}
```
转换为：
```groovy
sh 'npm ci'
sh 'npm run build'
```

#### Maven构建
```json
{
  "build_tool": "maven",
  "build_command": "clean compile package"
}
```
转换为：
```groovy
sh 'mvn clean compile package'
```

#### Gradle构建
```json
{
  "build_tool": "gradle",
  "build_command": "build"
}
```
转换为：
```groovy
sh './gradlew build'
```

#### Docker构建
```json
{
  "build_tool": "docker",
  "dockerfile": "Dockerfile.prod",
  "tag": "myapp:v1.0",
  "context": "./src"
}
```
转换为：
```groovy
sh 'docker build -f Dockerfile.prod -t myapp:v1.0 ./src'
```

### 3. 测试 (test / test_execution)

执行各种类型的测试。

| 参数名 | 类型 | 默认值 | 说明 | Jenkins转换 |
|--------|------|--------|------|-------------|
| `test_command` | string | `"npm test"` | 测试执行命令 | `sh 'test_command'` |
| `coverage` | boolean | `false` | 是否生成覆盖率报告 | 添加`publishHTML`步骤 |

**示例配置：**
```json
{
  "test_command": "jest --coverage --watchAll=false",
  "coverage": true
}
```

**Jenkins转换：**
```groovy
sh 'jest --coverage --watchAll=false'
publishHTML([
    allowMissing: false, 
    alwaysLinkToLastBuild: true, 
    keepAll: true, 
    reportDir: 'coverage', 
    reportFiles: 'index.html', 
    reportName: 'Coverage Report'
])
```

### 4. 部署 (deploy)

将应用部署到目标环境。

| 参数名 | 类型 | 默认值 | 说明 | Jenkins转换 |
|--------|------|--------|------|-------------|
| `deploy_type` | string | `"kubernetes"` | 部署类型 | 决定部署策略 |
| `namespace` | string | `"default"` | Kubernetes命名空间 | `kubectl -n namespace` |
| `manifest_path` | string | `"k8s/"` | K8s清单文件路径 | `kubectl apply -f path` |
| `image` | string | `"app:latest"` | Docker镜像名称 | `docker run image` |
| `container_name` | string | `"app"` | 容器名称 | `docker run --name name` |
| `deploy_command` | string | - | 自定义部署命令 | `sh 'deploy_command'` |

**部署类型支持：**

#### Kubernetes部署
```json
{
  "deploy_type": "kubernetes",
  "namespace": "production",
  "manifest_path": "k8s/prod/"
}
```
转换为：
```groovy
sh 'kubectl apply -f k8s/prod/ -n production'
```

#### Docker部署
```json
{
  "deploy_type": "docker",
  "image": "myapp:v1.0",
  "container_name": "myapp-prod"
}
```
转换为：
```groovy
sh 'docker stop myapp-prod || true'
sh 'docker rm myapp-prod || true'
sh 'docker run -d --name myapp-prod myapp:v1.0'
```

### 5. 安全扫描 (security_scan)

执行安全漏洞扫描。

| 参数名 | 类型 | 默认值 | 说明 | Jenkins转换 |
|--------|------|--------|------|-------------|
| `scan_type` | string | `"zap"` | 扫描工具类型 | 决定扫描命令 |
| `target_url` | string | `"http://localhost"` | 扫描目标URL | 传递给扫描工具 |
| `project_key` | string | `"default"` | SonarQube项目键 | `sonar-scanner -Dsonar.projectKey=key` |
| `scan_command` | string | - | 自定义扫描命令 | `sh 'scan_command'` |

**扫描类型支持：**

#### OWASP ZAP扫描
```json
{
  "scan_type": "zap",
  "target_url": "https://myapp.com"
}
```
转换为：
```groovy
sh 'docker run -t owasp/zap2docker-stable zap-baseline.py -t https://myapp.com'
```

#### SonarQube扫描
```json
{
  "scan_type": "sonarqube",
  "project_key": "my-project"
}
```
转换为：
```groovy
sh 'sonar-scanner -Dsonar.projectKey=my-project'
```

### 6. 通知 (notify / notification)

发送构建状态通知。

| 参数名 | 类型 | 默认值 | 说明 | Jenkins转换 |
|--------|------|--------|------|-------------|
| `message` | string | `"Pipeline completed"` | 通知消息内容 | 消息内容 |
| `webhook_url` | string | - | Webhook URL | `curl -X POST webhook_url` |

**示例配置：**
```json
{
  "message": "部署成功！应用已上线。",
  "webhook_url": "https://hooks.slack.com/services/..."
}
```

**Jenkins转换：**
```groovy
// 有webhook的情况
sh 'curl -X POST -H "Content-Type: application/json" -d {"text": "部署成功！应用已上线。"} https://hooks.slack.com/services/...'

// 无webhook的情况
sh 'echo \'部署成功！应用已上线。\''
```

### 7. 制品上传 (artifact_upload)

上传构建产物。

| 参数名 | 类型 | 默认值 | 说明 | Jenkins转换 |
|--------|------|--------|------|-------------|
| `paths` | array | `[]` | 制品文件路径列表 | `archiveArtifacts artifacts: paths` |

**示例配置：**
```json
{
  "paths": ["dist/**", "*.jar", "reports/*"]
}
```

**Jenkins转换：**
```groovy
archiveArtifacts artifacts: 'dist/**', '*.jar', 'reports/*', allowEmptyArchive: true
```

### 8. 自定义步骤 (custom / shell_script)

执行自定义shell脚本。

| 参数名 | 类型 | 默认值 | 说明 | Jenkins转换 |
|--------|------|--------|------|-------------|
| `command` | string | - | Shell命令 | `sh 'command'` |
| `script` | string | - | Shell脚本内容 | `sh 'script'` |

### 9. 特定构建工具步骤

#### Maven构建 (maven_build)
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `goals` | string | `"clean compile"` | Maven目标 |

#### Gradle构建 (gradle_build)
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `tasks` | string | `"build"` | Gradle任务 |

#### NPM构建 (npm_build)
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `script` | string | `"build"` | NPM脚本名称 |

## 参数优先级

1. **最高优先级**: `command` - 自定义命令，会覆盖所有其他参数
2. **中等优先级**: 步骤特定参数（如`test_command`, `build_tool`等）
3. **最低优先级**: 默认值

## 引号转义说明

所有包含单引号的命令都会自动转义以防止Jenkins Pipeline语法错误：

**输入：**
```json
{
  "command": "echo 'hello world'"
}
```

**Jenkins输出：**
```groovy
sh 'echo \'hello world\''
```

## 环境变量

流水线级别的环境变量通过`PipelineDefinition.environment`设置：

```python
pipeline_def = PipelineDefinition(
    environment={
        "NODE_ENV": "production",
        "API_URL": "https://api.example.com"
    }
)
```

转换为Jenkins：
```groovy
environment {
    NODE_ENV = 'production'
    API_URL = 'https://api.example.com'
}
```

## 最佳实践

1. **使用描述性参数名**: 优先使用明确的参数名如`test_command`而不是通用的`command`
2. **提供默认值**: 为可选参数提供合理的默认值
3. **验证参数**: 在使用前验证必需参数是否存在
4. **引号处理**: 系统会自动处理命令中的引号转义，无需手动处理
5. **错误处理**: 为可能失败的命令添加适当的错误处理（如`|| true`）

## 示例完整流水线

```json
{
  "name": "full-pipeline-example",
  "steps": [
    {
      "name": "获取代码",
      "type": "fetch_code",
      "parameters": {
        "repository": "https://github.com/user/repo.git",
        "branch": "main"
      }
    },
    {
      "name": "安装依赖",
      "type": "build",
      "parameters": {
        "build_tool": "npm",
        "build_command": "install"
      }
    },
    {
      "name": "运行测试",
      "type": "test_execution",
      "parameters": {
        "test_command": "npm test -- --coverage",
        "coverage": true
      }
    },
    {
      "name": "构建应用",
      "type": "build",
      "parameters": {
        "build_tool": "npm",
        "build_command": "build"
      }
    },
    {
      "name": "Docker构建",
      "type": "docker_build",
      "parameters": {
        "dockerfile": "Dockerfile",
        "tag": "myapp:latest",
        "context": "."
      }
    },
    {
      "name": "部署应用",
      "type": "deploy",
      "parameters": {
        "deploy_type": "kubernetes",
        "namespace": "production",
        "manifest_path": "k8s/"
      }
    },
    {
      "name": "发送通知",
      "type": "notification",
      "parameters": {
        "message": "部署完成！",
        "webhook_url": "https://hooks.slack.com/services/..."
      }
    }
  ],
  "environment": {
    "NODE_ENV": "production"
  }
}
```

这个配置将生成完整的Jenkins Pipeline，包含所有必要的构建、测试、部署步骤。
