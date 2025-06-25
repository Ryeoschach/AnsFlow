# AnsFlow CI/CD 集成扩展指南

## 概述

AnsFlow 平台现已支持多个主流 CI/CD 工具的统一集成，包括：

- ✅ **Jenkins** - 企业级 CI/CD 平台
- ✅ **GitLab CI** - GitLab 内置 CI/CD 系统
- ✅ **GitHub Actions** - GitHub 原生工作流自动化

通过统一的适配器模式和原子步骤系统，您可以在一个控制面板中管理和协调多个 CI/CD 工具。

## 新增功能

### GitLab CI 集成

#### 功能特性
- **完整的 GitLab CI 适配器**：支持 GitLab.com 和私有 GitLab 实例
- **`.gitlab-ci.yml` 自动生成**：基于原子步骤生成标准 GitLab CI 配置
- **流水线管理**：触发、监控、取消和获取日志
- **项目级集成**：支持特定项目的流水线管理
- **状态映射**：将 GitLab CI 状态映射到统一状态模型

#### 支持的原子步骤转换
- `git_checkout` → 自动 Git 检出配置
- `shell_script` → 自定义脚本执行
- `maven_build` → Maven 构建（包含缓存）
- `gradle_build` → Gradle 构建（包含缓存）
- `npm_build` → Node.js 构建（包含依赖缓存）
- `docker_build` → Docker 镜像构建
- `kubernetes_deploy` → Kubernetes 部署
- `test_execution` → 测试执行（包含报告）
- `security_scan` → 安全扫描
- `artifact_upload` → 构件上传
- `notification` → 通知发送
- `environment_setup` → 环境变量配置

#### 使用示例
```bash
# 测试 GitLab CI 连接
python manage.py test_gitlab_ci --gitlab-url https://gitlab.com --token your_token --project-id 12345 --register

# 测试 GitLab CI 流水线执行
python manage.py test_gitlab_pipeline --project-id 12345 --branch main --monitor
```

### GitHub Actions 集成

#### 功能特性
- **GitHub Actions 适配器**：支持 GitHub.com 和 GitHub Enterprise
- **工作流 YAML 生成**：基于原子步骤生成 GitHub Actions 工作流
- **仓库级集成**：支持特定仓库的工作流管理
- **Action 生态系统**：利用 GitHub Actions Marketplace
- **并行作业支持**：支持多阶段并行执行

#### 支持的原子步骤转换
- `git_checkout` → `actions/checkout@v4`
- `maven_build` → Java 环境配置 + Maven 缓存 + 构建
- `gradle_build` → Java 环境配置 + Gradle 配置 + 构建
- `npm_build` → Node.js 环境配置 + npm 缓存 + 构建
- `docker_build` → Docker 构建命令
- `kubernetes_deploy` → kubectl 配置 + 部署
- `test_execution` → 测试执行 + 结果上传
- `security_scan` → 安全扫描工具集成
- `artifact_upload` → `actions/upload-artifact@v3`

#### 使用示例
```bash
# 测试 GitHub Actions 连接
python manage.py test_github_actions --token your_token --owner username --repo repository --register

# 运行统一集成测试
python test_unified_cicd_integration.py --tools github_actions gitlab_ci jenkins
```

## 配置要求

### GitLab CI 配置

#### 环境变量
```bash
export GITLAB_URL="https://gitlab.com"  # 或您的 GitLab 实例 URL
export GITLAB_TOKEN="your_gitlab_token"  # GitLab 个人访问令牌
export GITLAB_PROJECT_ID="12345"  # GitLab 项目 ID
```

#### GitLab Token 权限要求
- `api` - 访问 GitLab API
- `read_api` - 读取 API 信息
- `read_repository` - 读取仓库信息
- `write_repository` - 写入仓库（如需要）

### GitHub Actions 配置

#### 环境变量
```bash
export GITHUB_URL="https://api.github.com"  # GitHub API URL
export GITHUB_TOKEN="your_github_token"  # GitHub 个人访问令牌
export GITHUB_OWNER="username"  # GitHub 用户名或组织名
export GITHUB_REPO="repository"  # GitHub 仓库名
```

#### GitHub Token 权限要求
- `repo` - 完整的仓库访问权限
- `workflow` - 更新 GitHub Actions 工作流
- `actions:read` - 读取 Actions 信息
- `actions:write` - 写入 Actions 配置

## 架构设计

### 适配器模式扩展

```python
# 支持的 CI/CD 工具适配器
_adapters = {
    'jenkins': JenkinsAdapter,
    'gitlab_ci': GitLabCIAdapter,        # 新增
    'github_actions': GitHubActionsAdapter,  # 新增
}
```

### 统一状态映射

| 工具状态 | 统一状态 | Jenkins | GitLab CI | GitHub Actions |
|---------|---------|---------|-----------|----------------|
| 等待中 | `pending` | `null` | `created`, `pending` | `queued`, `waiting` |
| 运行中 | `running` | `building=true` | `running` | `in_progress` |
| 成功 | `success` | `SUCCESS` | `success` | `success` |
| 失败 | `failed` | `FAILURE` | `failed` | `failure` |
| 取消 | `cancelled` | `ABORTED` | `canceled` | `cancelled` |

## 使用指南

### 1. 注册 CI/CD 工具

```python
# GitLab CI
python manage.py test_gitlab_ci --register

# GitHub Actions  
python manage.py test_github_actions --register
```

### 2. 创建流水线

```python
from cicd_integrations.adapters import PipelineDefinition
from cicd_integrations.services import UnifiedCICDEngine

# 创建流水线定义
pipeline_def = PipelineDefinition(
    name='multi-tool-pipeline',
    steps=[
        {
            'type': 'git_checkout',
            'parameters': {'branch': 'main'}
        },
        {
            'type': 'npm_build',
            'parameters': {'script': 'build'}
        },
        {
            'type': 'test_execution',
            'parameters': {'test_command': 'npm test'}
        }
    ],
    triggers={'branch': 'main'},
    environment={'NODE_ENV': 'production'}
)

# 在不同工具中执行
engine = UnifiedCICDEngine()

# GitLab CI 执行
gitlab_execution = await engine.execute_pipeline(
    tool_id=gitlab_tool.id,
    pipeline_definition=pipeline_def,
    project_path="your-project-id"
)

# GitHub Actions 执行
github_execution = await engine.execute_pipeline(
    tool_id=github_tool.id,
    pipeline_definition=pipeline_def,
    project_path="owner/repo"
)
```

### 3. 监控执行状态

```python
# 统一状态监控
status = await engine.get_execution_status(execution.id)
logs = await engine.get_execution_logs(execution.id)
```

## 测试验证

### 完整集成测试

```bash
# 运行全面测试（需要配置所有工具的环境变量）
python test_unified_cicd_integration.py

# 测试特定工具
python test_unified_cicd_integration.py --tools gitlab_ci github_actions

# 单独测试
python test_gitlab_ci_integration.py
```

### 测试流程

1. **连接测试** - 验证 API 连接和权限
2. **工具注册** - 注册工具到 AnsFlow 数据库
3. **配置生成** - 测试原子步骤到目标格式的转换
4. **流水线执行** - 实际触发流水线执行
5. **状态监控** - 验证状态更新和日志获取

## API 接口

### REST API 端点

```
GET    /api/v1/cicd/tools/                    # 获取所有 CI/CD 工具
POST   /api/v1/cicd/tools/                    # 注册新工具
GET    /api/v1/cicd/tools/{id}/health/        # 工具健康检查
POST   /api/v1/cicd/tools/{id}/execute/       # 执行流水线
GET    /api/v1/cicd/executions/               # 获取执行记录
GET    /api/v1/cicd/executions/{id}/status/   # 获取执行状态
GET    /api/v1/cicd/executions/{id}/logs/     # 获取执行日志
```

### WebSocket 实时通知

```javascript
// 连接 WebSocket 监听执行状态
const ws = new WebSocket('ws://localhost:8001/ws/cicd/executions/{execution_id}');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('状态更新:', data.status);
};
```

## 扩展开发

### 添加新的 CI/CD 工具

1. **创建适配器类**
```python
class CustomCICDAdapter(CICDAdapter):
    async def trigger_pipeline(self, pipeline_def: PipelineDefinition, project_path: str) -> ExecutionResult:
        # 实现流水线触发逻辑
        pass
    
    async def get_pipeline_status(self, execution_id: str) -> Dict[str, Any]:
        # 实现状态查询逻辑
        pass
```

2. **注册适配器**
```python
CICDAdapterFactory.register_adapter('custom_tool', CustomCICDAdapter)
```

3. **添加测试命令**
```python
# management/commands/test_custom_tool.py
```

### 自定义原子步骤

```python
# 创建自定义原子步骤
custom_step = AtomicStep.objects.create(
    name='Custom Deploy',
    step_type='custom_deploy',
    description='Custom deployment step',
    default_parameters={
        'target_env': 'staging',
        'deploy_script': 'deploy.sh'
    },
    visibility='public'
)
```

## 故障排除

### 常见问题

1. **认证失败**
   - 检查 Token 权限和有效性
   - 确认 API URL 正确

2. **流水线执行失败**
   - 检查项目访问权限
   - 验证流水线配置语法

3. **状态同步延迟**
   - CI/CD 工具可能有状态更新延迟
   - 增加轮询间隔时间

### 调试模式

```bash
# 启用详细日志
export DJANGO_LOG_LEVEL=DEBUG
python manage.py test_gitlab_ci --gitlab-url https://gitlab.com --token your_token --project-id 12345
```

## 最佳实践

1. **权限管理**
   - 使用最小权限原则配置 Token
   - 定期轮换访问令牌

2. **流水线设计**
   - 合理使用原子步骤组合
   - 设置适当的超时时间

3. **监控告警**
   - 配置流水线失败通知
   - 监控工具健康状态

4. **性能优化**
   - 使用缓存减少构建时间
   - 并行执行独立步骤

## 后续规划

- 🔄 **CircleCI 适配器** - 支持 CircleCI 平台
- 🔄 **Azure DevOps 适配器** - 支持 Microsoft Azure DevOps
- 🔄 **流水线模板** - 预定义常用流水线模板
- 🔄 **条件执行** - 支持基于条件的步骤执行
- 🔄 **多工具协调** - 跨工具的流水线协调执行

---

## 贡献指南

欢迎为 AnsFlow CI/CD 集成功能贡献代码！请参考 [CONTRIBUTING.md](../CONTRIBUTING.md) 了解详细的贡献流程。
