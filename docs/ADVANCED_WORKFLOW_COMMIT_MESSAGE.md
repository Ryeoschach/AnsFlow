feat(workflow): 实现高级工作流功能 - 条件分支、并行执行、手动审批

## 新增功能

### 🌲 条件执行分支
- 支持前序步骤成功/失败时执行
- 自定义JavaScript表达式条件判断
- 步骤依赖关系配置
- 灵活的分支逻辑控制

### ⚡ 并行执行策略  
- 并行组创建和管理
- 三种同步策略：等待所有、等待任一、快速失败
- 并行组超时控制
- 可视化并行关系展示

### ✋ 手动审批节点
- 多审批人配置支持
- 自定义审批消息和超时时间
- 最少审批人数要求
- 审批状态跟踪和通知

### 🔧 增强功能
- 步骤重试策略配置
- 多渠道通知配置(邮件、钉钉、微信、Slack)
- 工作流复杂度分析
- 执行时间预估和瓶颈识别

## 技术实现

### 类型系统扩展
- 新增 `EnhancedPipelineStep`、`StepCondition`、`ApprovalConfig`、`ParallelGroup` 等类型
- 完整的工作流上下文和分析类型定义
- 向后兼容现有 PipelineStep 和 AtomicStep 类型

### 核心组件
- `WorkflowStepForm.tsx` - 高级工作流配置表单
- `ParallelGroupManager.tsx` - 并行组管理组件  
- `WorkflowAnalyzer.tsx` - 工作流分析和可视化
- 增强的 `PipelineEditor.tsx` 主编辑器

### UI/UX 改进
- 步骤卡片增加高级功能标签显示
- 编辑器宽度扩展，支持更复杂的配置
- 新增"显示/隐藏高级选项"切换
- 工具栏新增并行组管理和工作流分析按钮

## 文件变更

### 新增文件
- `frontend/src/components/pipeline/WorkflowStepForm.tsx` - 工作流步骤配置组件
- `frontend/src/components/pipeline/ParallelGroupManager.tsx` - 并行组管理组件
- `frontend/src/components/pipeline/WorkflowAnalyzer.tsx` - 工作流分析组件
- `scripts/ADVANCED_WORKFLOW_DEMO.js` - 功能演示脚本
- `docs/ADVANCED_WORKFLOW_IMPLEMENTATION.md` - 实现文档

### 修改文件
- `frontend/src/types/index.ts` - 扩展工作流相关类型定义
- `frontend/src/components/pipeline/PipelineEditor.tsx` - 集成高级工作流功能

## 兼容性保证

✅ **完全向后兼容** - 现有流水线和步骤配置不受影响  
✅ **渐进式增强** - 新功能作为可选配置项  
✅ **类型安全** - 完整的TypeScript类型支持  
✅ **API兼容** - 保持现有API调用方式不变  

## 验证测试

- ✅ 条件执行：成功/失败触发、表达式判断
- ✅ 并行执行：多步骤同时运行、同步策略
- ✅ 审批流程：多审批人、超时处理、状态跟踪
- ✅ 工作流分析：复杂度评估、瓶颈识别、时间预估
- ✅ UI集成：标签显示、编辑界面、管理工具
- ✅ 兼容性：现有功能完全正常

## 使用示例

```typescript
// 条件执行示例
const conditionalStep = {
  condition: {
    type: 'expression',
    expression: '$variables.deploy_env === "production"'
  }
}

// 并行执行示例  
const parallelGroup = {
  id: 'test_group',
  name: '测试并行组',
  sync_policy: 'wait_all',
  steps: [2, 3]
}

// 审批配置示例
const approvalConfig = {
  approvers: ['tech_lead', 'product_manager'],
  required_approvals: 2,
  timeout_hours: 24
}
```

## 影响范围

- ✅ 大幅提升流水线配置灵活性
- ✅ 支持复杂企业级工作流场景  
- ✅ 提供专业的工作流分析能力
- ✅ 保持用户体验的一致性
- ✅ 为后续功能扩展打下基础

## 后续计划

- [ ] 可视化工作流设计器
- [ ] 工作流模板和预设
- [ ] 执行历史分析和优化建议
- [ ] 跨流水线依赖管理
