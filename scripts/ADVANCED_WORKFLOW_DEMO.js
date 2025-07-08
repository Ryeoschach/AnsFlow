/**
 * 高级工作流功能演示脚本
 * 用于测试条件分支、并行执行、手动审批等功能
 */

console.log('🚀 开始高级工作流功能演示...')

// 模拟测试数据
const testPipeline = {
  id: 1,
  name: '高级工作流演示流水线',
  description: '展示条件分支、并行执行、手动审批等功能'
}

const testSteps = [
  {
    id: 1,
    name: '代码检出',
    step_type: 'fetch_code',
    description: '从Git仓库拉取代码',
    order: 1,
    parameters: {
      repository: 'https://github.com/example/repo.git',
      branch: 'main'
    }
  },
  {
    id: 2,
    name: '单元测试',
    step_type: 'test',
    description: '执行单元测试',
    order: 2,
    parameters: {
      test_command: 'npm test',
      coverage: true
    },
    parallel_group_id: 'parallel_1',
    retry_policy: {
      max_retries: 3,
      retry_delay_seconds: 30,
      retry_on_failure: true
    }
  },
  {
    id: 3,
    name: '代码质量检查',
    step_type: 'security_scan',
    description: '执行代码质量和安全扫描',
    order: 3,
    parameters: {
      tools: ['eslint', 'sonarqube'],
      fail_on_error: false
    },
    parallel_group_id: 'parallel_1'
  },
  {
    id: 4,
    name: '构建应用',
    step_type: 'build',
    description: '编译和打包应用',
    order: 4,
    parameters: {
      build_command: 'npm run build',
      output_dir: 'dist'
    },
    condition: {
      type: 'on_success',
      depends_on: [2, 3]
    }
  },
  {
    id: 5,
    name: '生产环境部署审批',
    step_type: 'custom',
    description: '等待生产环境部署审批',
    order: 5,
    parameters: {},
    requires_approval: true,
    approval_config: {
      approvers: ['tech_lead', 'product_manager'],
      approval_message: '请审批生产环境部署，确认版本质量和部署时间',
      timeout_hours: 24,
      auto_approve_on_timeout: false,
      required_approvals: 2
    },
    condition: {
      type: 'expression',
      expression: '$variables.deploy_env === "production"'
    },
    notification_config: {
      on_approval_required: true,
      channels: ['email', 'dingtalk']
    }
  },
  {
    id: 6,
    name: '部署到生产环境',
    step_type: 'deploy',
    description: '部署应用到生产环境',
    order: 6,
    parameters: {
      environment: 'production',
      strategy: 'blue-green'
    },
    condition: {
      type: 'on_success',
      depends_on: [5]
    },
    notification_config: {
      on_success: true,
      on_failure: true,
      channels: ['email', 'dingtalk', 'slack']
    }
  },
  {
    id: 7,
    name: '回滚处理',
    step_type: 'deploy',
    description: '如果部署失败，执行回滚',
    order: 7,
    parameters: {
      action: 'rollback',
      to_version: 'previous'
    },
    condition: {
      type: 'on_failure',
      depends_on: [6]
    }
  }
]

const testParallelGroups = [
  {
    id: 'parallel_1',
    name: '测试和检查并行组',
    description: '单元测试和代码质量检查可以并行执行',
    steps: [2, 3],
    sync_policy: 'wait_all',
    timeout_seconds: 1800
  }
]

// 测试功能函数
function testWorkflowFeatures() {
  console.log('📋 测试流水线配置:')
  console.log('- 流水线:', testPipeline.name)
  console.log('- 步骤数量:', testSteps.length)
  console.log('- 并行组数量:', testParallelGroups.length)
  
  console.log('\n🔍 分析高级功能:')
  
  // 分析条件执行
  const conditionalSteps = testSteps.filter(s => s.condition && s.condition.type !== 'always')
  console.log('- 条件执行步骤:', conditionalSteps.length)
  conditionalSteps.forEach(step => {
    console.log(`  ✓ ${step.name}: ${step.condition.type}`)
  })
  
  // 分析并行执行
  const parallelSteps = testSteps.filter(s => s.parallel_group_id)
  console.log('- 并行执行步骤:', parallelSteps.length)
  testParallelGroups.forEach(group => {
    const groupSteps = testSteps.filter(s => s.parallel_group_id === group.id)
    console.log(`  ✓ ${group.name}: ${groupSteps.map(s => s.name).join(', ')} (${group.sync_policy})`)
  })
  
  // 分析审批节点
  const approvalSteps = testSteps.filter(s => s.requires_approval)
  console.log('- 审批节点:', approvalSteps.length)
  approvalSteps.forEach(step => {
    console.log(`  ✓ ${step.name}: ${step.approval_config.approvers.join(', ')}`)
  })
  
  // 分析重试策略
  const retrySteps = testSteps.filter(s => s.retry_policy?.retry_on_failure)
  console.log('- 配置重试的步骤:', retrySteps.length)
  retrySteps.forEach(step => {
    console.log(`  ✓ ${step.name}: 最多${step.retry_policy.max_retries}次`)
  })
  
  // 分析通知配置
  const notificationSteps = testSteps.filter(s => s.notification_config)
  console.log('- 配置通知的步骤:', notificationSteps.length)
  notificationSteps.forEach(step => {
    const config = step.notification_config
    const triggers = []
    if (config.on_success) triggers.push('成功')
    if (config.on_failure) triggers.push('失败')
    if (config.on_approval_required) triggers.push('需要审批')
    console.log(`  ✓ ${step.name}: ${triggers.join('、')}时通知`)
  })
}

// 模拟工作流分析
function analyzeWorkflow() {
  console.log('\n📊 工作流分析结果:')
  
  const analysis = {
    total_steps: testSteps.length,
    parallel_groups: testParallelGroups.length,
    approval_steps: testSteps.filter(s => s.requires_approval).length,
    conditional_steps: testSteps.filter(s => s.condition && s.condition.type !== 'always').length,
    estimated_duration_minutes: 0
  }
  
  // 估算执行时间
  const regularSteps = testSteps.filter(s => !s.parallel_group_id)
  analysis.estimated_duration_minutes += regularSteps.length * 2 // 假设每个步骤2分钟
  
  // 并行组时间（取最长的）
  testParallelGroups.forEach(group => {
    const groupSteps = testSteps.filter(s => s.parallel_group_id === group.id)
    analysis.estimated_duration_minutes += Math.max(groupSteps.length * 2, 5)
  })
  
  // 审批时间
  analysis.estimated_duration_minutes += analysis.approval_steps * 60 // 每个审批1小时
  
  console.log('- 总步骤数:', analysis.total_steps)
  console.log('- 并行组数:', analysis.parallel_groups)
  console.log('- 审批节点数:', analysis.approval_steps)
  console.log('- 条件步骤数:', analysis.conditional_steps)
  console.log('- 预估执行时间:', `${Math.floor(analysis.estimated_duration_minutes / 60)}小时${analysis.estimated_duration_minutes % 60}分钟`)
  
  // 复杂度评估
  const complexity = analysis.conditional_steps + analysis.parallel_groups + analysis.approval_steps
  let complexityLevel = '简单'
  if (complexity > 5) complexityLevel = '复杂'
  else if (complexity > 2) complexityLevel = '中等'
  
  console.log('- 复杂度评估:', complexityLevel)
  
  // 潜在瓶颈分析
  console.log('\n⚠️ 潜在瓶颈提醒:')
  if (analysis.approval_steps > 0) {
    console.log(`- ${analysis.approval_steps}个审批节点可能导致执行延迟`)
  }
  
  const expressionSteps = testSteps.filter(s => s.condition?.type === 'expression')
  if (expressionSteps.length > 0) {
    console.log(`- ${expressionSteps.length}个复杂条件判断可能影响执行`)
  }
  
  const waitAllGroups = testParallelGroups.filter(g => g.sync_policy === 'wait_all')
  if (waitAllGroups.length > 0) {
    console.log(`- ${waitAllGroups.length}个"等待所有"并行组可能形成瓶颈`)
  }
}

// 模拟执行流程
function simulateExecution() {
  console.log('\n🎬 模拟执行流程:')
  
  console.log('1. 代码检出 → 开始执行')
  console.log('2. 进入并行组 "测试和检查并行组"')
  console.log('   ├─ 单元测试 (并行)')
  console.log('   └─ 代码质量检查 (并行)')
  console.log('3. 等待并行组完成...')
  console.log('4. 条件判断: 前序步骤成功 → 构建应用')
  console.log('5. 条件判断: 部署环境为生产环境 → 等待审批')
  console.log('6. 发送审批通知到 tech_lead, product_manager')
  console.log('7. 等待审批响应...')
  console.log('8. 审批通过 → 部署到生产环境')
  console.log('9. 部署成功 → 发送成功通知')
  console.log('✅ 工作流执行完成')
}

// 测试前端UI集成点
function testUIIntegration() {
  console.log('\n🖥️ 前端UI集成测试点:')
  
  console.log('1. 步骤卡片显示:')
  console.log('   - 条件执行标签 (蓝色)')
  console.log('   - 并行执行标签 (青色)')
  console.log('   - 审批节点标签 (橙色)')
  
  console.log('2. 步骤编辑抽屉:')
  console.log('   - 基础配置表单')
  console.log('   - 高级工作流配置折叠面板')
  console.log('   - 条件执行分支配置')
  console.log('   - 并行执行策略配置')
  console.log('   - 手动审批节点配置')
  
  console.log('3. 管理组件:')
  console.log('   - 并行组管理弹窗')
  console.log('   - 工作流分析弹窗')
  console.log('   - 执行路径可视化')
  
  console.log('4. 功能按钮:')
  console.log('   - 编辑信息')
  console.log('   - 并行组管理')
  console.log('   - 工作流分析')
  console.log('   - 预览Pipeline')
  console.log('   - 添加步骤')
  console.log('   - 保存流水线')
}

// 执行演示
console.log('=' .repeat(60))
console.log('高级工作流功能演示')
console.log('=' .repeat(60))

testWorkflowFeatures()
analyzeWorkflow()
simulateExecution()
testUIIntegration()

console.log('\n' + '=' .repeat(60))
console.log('✅ 高级工作流功能演示完成')
console.log('💡 提示: 请在浏览器控制台运行此脚本进行测试')
console.log('=' .repeat(60))

// 导出测试数据供前端使用
if (typeof window !== 'undefined') {
  window.workflowTestData = {
    pipeline: testPipeline,
    steps: testSteps,
    parallelGroups: testParallelGroups
  }
  console.log('📦 测试数据已导出到 window.workflowTestData')
}
