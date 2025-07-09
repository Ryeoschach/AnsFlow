# 流水线步骤参数说明功能演示

## 功能概述

在AnsFlow流水线编辑页面中，为每个步骤类型增加了参数说明功能，帮助用户了解：
- 可使用的参数key
- 参数类型和说明
- 参数与Jenkins Pipeline的转换示例
- 参数优先级和使用建议

## 功能特性

### 1. 动态参数说明
- 当用户在编辑步骤时选择步骤类型后，会显示"查看参数说明"按钮
- 点击按钮可展开该步骤类型的详细参数配置说明

### 2. 参数表格展示
- 参数名称、类型、是否必需
- 参数描述和使用说明
- 默认值和示例值
- 参数优先级（数字越小优先级越高）

### 3. Jenkins转换示例
- 展示该步骤类型在Jenkins Pipeline中的转换结果
- 提供多种场景的代码示例
- 支持代码语法高亮显示

### 4. 一键插入参数
- 支持点击参数行快速插入示例参数到表单中
- 自动合并现有参数JSON
- 智能处理JSON格式错误

### 5. 条件参数说明
- 显示依赖于其他参数的条件参数
- 提供参数间依赖关系说明

## 使用方法

### 步骤1：编辑或新建步骤
1. 在流水线编辑页面点击"添加步骤"或编辑现有步骤
2. 选择步骤类型（如：代码拉取、构建、测试等）

### 步骤2：查看参数说明
1. 选择步骤类型后，会出现蓝色信息提示框
2. 点击"查看参数说明"按钮展开参数文档

### 步骤3：了解参数配置
参数说明包含以下部分：
- **基本信息**：步骤名称、描述、分类
- **参数表格**：详细的参数列表
- **Jenkins转换**：Pipeline代码示例
- **条件参数**：依赖参数说明（如果有）

### 步骤4：配置参数
1. 在参数表格中点击任意参数行可自动插入示例值
2. 手动编辑parameters字段的JSON内容
3. 参考Jenkins转换示例了解最终执行效果

## 支持的步骤类型

### 1. 代码拉取 (fetch_code)
- **command**: 自定义Git命令（优先级最高）
- **repository**: Git仓库URL
- **branch**: 分支名称

### 2. 构建 (build)
- **command**: 自定义构建命令（优先级最高）
- **build_tool**: 构建工具类型（npm/maven/gradle/docker）
- **build_command**: 工具特定的构建命令
- **dockerfile/tag/context**: Docker构建参数

### 3. 测试 (test)
- **test_command**: 测试执行命令
- **coverage**: 是否生成覆盖率报告

### 4. 部署 (deploy)
- **deploy_type**: 部署类型（kubernetes/docker）
- **namespace**: Kubernetes命名空间
- **manifest_path**: K8s清单文件路径
- **image/container_name**: Docker部署参数

### 5. 安全扫描 (security_scan)
- **scan_type**: 扫描工具类型（zap/sonarqube）
- **target_url**: 扫描目标URL
- **project_key**: SonarQube项目key

### 6. 通知 (notify)
- **message**: 通知消息内容
- **webhook_url**: Webhook URL

### 7. 自定义 (custom)
- **command**: 自定义shell命令
- **script**: 自定义脚本内容

## 参数优先级说明

大部分步骤类型都支持参数优先级：

1. **最高优先级**: `command` - 自定义命令会覆盖所有其他参数
2. **中等优先级**: 步骤特定参数（如build_tool、deploy_type等）
3. **低优先级**: 通用参数和默认值

## Jenkins转换示例

### 代码拉取示例
```json
{
  "repository": "https://github.com/user/repo.git",
  "branch": "develop"
}
```

转换为Jenkins Pipeline：
```groovy
checkout([
    $class: 'GitSCM',
    branches: [[name: 'develop']],
    userRemoteConfigs: [[url: 'https://github.com/user/repo.git']]
])
```

### 构建示例
```json
{
  "build_tool": "docker",
  "dockerfile": "Dockerfile.prod",
  "tag": "myapp:v1.0.0"
}
```

转换为Jenkins Pipeline：
```groovy
sh 'docker build -f Dockerfile.prod -t myapp:v1.0.0 .'
```

## 注意事项

1. **JSON格式**: 参数必须是有效的JSON格式
2. **参数转义**: Jenkins Pipeline中的shell命令会自动进行安全转义
3. **参数组合**: 某些参数会相互影响，请参考优先级说明
4. **类型检查**: 系统会在执行时验证参数类型和必需参数

## 技术实现

### 前端组件
- `ParameterDocumentation.tsx`: 参数说明展示组件
- `PipelineEditor.tsx`: 集成参数说明功能的流水线编辑器

### 配置文件
- `pipeline-steps-config.json`: 步骤类型和参数的结构化配置
- `pipeline-steps-parameters.md`: 详细的参数说明文档

### 后端适配
- `jenkins.py`: Jenkins适配器，负责参数到Pipeline代码的转换
- 支持安全的shell命令转义（单引号转为\'）

## 扩展性

该功能设计具有良好的扩展性：
1. 可轻松添加新的步骤类型
2. 支持多种CI/CD工具适配
3. 可自定义参数验证规则
4. 支持条件参数和动态参数

通过这个功能，用户可以更方便地配置流水线步骤参数，减少配置错误，提高开发效率。
