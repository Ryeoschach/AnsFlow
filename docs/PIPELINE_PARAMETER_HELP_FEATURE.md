# 流水线参数帮助功能使用说明

## 功能概述

在流水线编辑页面，为每个步骤添加了参数说明功能，用户可以方便地查看可用的参数key、类型、说明以及Jenkins转换示例。

## 功能特性

### 1. 参数说明展示
- **参数列表**: 显示所有可用参数的key、类型、默认值和说明
- **Jenkins转换**: 展示参数如何转换为Jenkins Pipeline脚本
- **优先级说明**: 显示参数的优先级（command > 特定参数 > 默认值）
- **示例代码**: 提供完整的Jenkins Pipeline代码示例

### 2. 交互式帮助
- **一键插入**: 点击参数示例可直接插入到参数文本框
- **代码复制**: 支持复制Jenkins Pipeline示例代码
- **可折叠面板**: 用户可以展开/折叠不同的参数说明部分

### 3. 实时更新
- **动态展示**: 根据选择的步骤类型动态显示对应的参数说明
- **智能提示**: 在用户选择步骤类型后自动提示参数帮助

## 使用方法

### 1. 打开流水线编辑器
在Pipelines页面点击"新建流水线"或编辑现有流水线。

### 2. 添加或编辑步骤
1. 点击"添加步骤"按钮
2. 选择步骤类型（如"代码拉取"、"构建"等）
3. 系统会显示参数帮助提示

### 3. 查看参数说明
1. 点击"查看参数说明"按钮
2. 参数说明面板会展开，显示：
   - 参数列表表格
   - Jenkins转换示例
   - 完整的Pipeline代码示例
   - 参数优先级说明

### 4. 使用参数示例
1. 在参数说明中找到需要的参数
2. 点击"使用此示例"按钮
3. 参数会自动插入到参数文本框中
4. 可以继续编辑或添加其他参数

### 5. 复制代码示例
1. 在Jenkins转换示例部分
2. 点击"复制"按钮
3. 可以复制完整的Jenkins Pipeline代码

## 支持的步骤类型

目前支持以下步骤类型的参数说明：

1. **代码拉取 (fetch_code)**
   - repository, branch, command等参数

2. **构建 (build)**
   - build_tool, build_command, dockerfile等参数

3. **测试 (test)**
   - test_command, coverage等参数

4. **部署 (deploy)**
   - deploy_type, namespace, manifest_path等参数

5. **安全扫描 (security_scan)**
   - scan_type, target_url, project_key等参数

6. **通知 (notify)**
   - message, webhook_url等参数

7. **自定义步骤 (custom)**
   - command, script等参数

8. **专用构建步骤**
   - maven_build, gradle_build, npm_build等

## 参数配置示例

### 代码拉取示例
```json
{
  "repository": "https://github.com/user/repo.git",
  "branch": "develop"
}
```

### 构建示例
```json
{
  "build_tool": "npm",
  "build_command": "run build:prod"
}
```

### 部署示例
```json
{
  "deploy_type": "kubernetes",
  "namespace": "production",
  "manifest_path": "k8s/prod/"
}
```

## 技术实现

### 前端组件
- **ParameterDocumentation**: 主要的参数说明展示组件
- **PipelineEditor**: 集成了参数帮助功能的流水线编辑器

### 配置文件
- **pipeline-steps-config.json**: 包含所有步骤类型的参数配置
- **pipeline-steps-parameters.md**: 详细的参数说明文档

### 功能特性
- 响应式设计，支持移动端
- 支持语法高亮显示代码
- 智能参数合并和插入
- 完整的TypeScript类型支持

## 后续改进计划

1. **多语言支持**: 支持中英文切换
2. **参数验证**: 实时验证参数格式和有效性
3. **模板库**: 提供常用的参数配置模板
4. **条件参数**: 根据其他参数动态显示可用参数
5. **历史记录**: 保存用户常用的参数配置

## 故障排除

### 常见问题

1. **参数说明不显示**
   - 确保选择了正确的步骤类型
   - 检查网络连接和配置文件加载

2. **参数插入失败**
   - 确保当前参数文本框内容是有效的JSON格式
   - 手动修正JSON格式后重试

3. **Jenkins转换示例不匹配**
   - 参考最新的参数说明文档
   - 确保使用的参数key和类型正确

## 反馈和建议

如果您在使用过程中遇到问题或有改进建议，请：
1. 查看控制台错误信息
2. 参考参数说明文档
3. 联系开发团队获取支持

这个功能大大简化了流水线参数配置的复杂性，让用户可以快速理解和使用各种步骤参数。
