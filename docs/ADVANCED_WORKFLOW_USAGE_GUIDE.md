
# 高级工作流功能使用指南

## 功能概览

### 1. 高级步骤配置
- **位置**: 流水线编辑器 → 步骤卡片 → 高级配置按钮
- **功能**: 条件执行、并行分组、审批节点、重试策略、通知配置
- **使用**: 点击步骤的高级配置按钮，配置各项高级功能

### 2. 并行组管理
- **位置**: 流水线编辑器工具栏 → "并行组管理"按钮
- **功能**: 创建、管理并行执行组，分配步骤到并行组
- **使用**: 配置同步策略（wait_all/wait_any），选择要并行执行的步骤

### 3. 工作流分析
- **位置**: 流水线编辑器工具栏 → "工作流分析"按钮  
- **功能**: 依赖分析、性能指标、优化建议、复杂度评估
- **使用**: 查看流水线的分析报告，获取优化建议

### 4. 执行恢复
- **位置**: 流水线编辑器工具栏 → "执行恢复"按钮
- **功能**: 从失败步骤恢复执行，支持多种恢复策略
- **使用**: 选择失败的执行，配置恢复选项，重新启动流水线

## 配置示例

### 条件执行配置
```javascript
// 表达式条件
condition: {
  type: 'expression',
  expression: '$variables.env === "production"'
}

// 依赖条件
condition: {
  type: 'on_success', 
  depends_on: [previousStepId]
}
```

### 审批配置
```javascript
approval_config: {
  approvers: ['admin@example.com', 'manager@example.com'],
  required_approvals: 1,
  timeout_hours: 24,
  approval_message: '请审批生产环境部署'
}
```

### 重试策略
```javascript
retry_policy: {
  max_retries: 3,
  retry_delay_seconds: 10,
  retry_on_failure: true
}
```

### 通知配置
```javascript
notification_config: {
  on_success: false,
  on_failure: true,
  on_approval_required: true,
  channels: ['email', 'dingtalk']
}
```

## 最佳实践

1. **并行执行**: 将独立的步骤分组到并行组中，提高执行效率
2. **条件控制**: 使用条件执行避免不必要的步骤执行
3. **审批控制**: 在关键步骤（如生产部署）设置审批节点
4. **错误恢复**: 配置重试策略和执行恢复，提高可靠性
5. **监控告警**: 配置关键步骤的失败通知

## 故障排除

### 常见问题
1. **高级配置不生效**: 确保已保存流水线，高级配置会自动同步到后端
2. **并行组无法创建**: 检查步骤之间的依赖关系，避免循环依赖
3. **执行恢复失败**: 确保有失败的执行记录，且流水线状态支持恢复
4. **审批超时**: 检查审批人员配置和超时设置

### 调试技巧
1. 使用工作流分析查看依赖关系和潜在问题
2. 查看浏览器开发者工具的Network和Console面板
3. 检查后端日志获取详细错误信息
