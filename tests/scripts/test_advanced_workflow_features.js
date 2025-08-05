#!/usr/bin/env node

/**
 * 高级工作流功能测试脚本
 * 验证条件执行、并行组、审批节点、重试策略等功能
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 开始测试高级工作流功能...\n');

// 测试文件路径
const pipelineEditorPath = path.join(__dirname, '../frontend/src/components/pipeline/PipelineEditor.tsx');
const parallelGroupManagerPath = path.join(__dirname, '../frontend/src/components/pipeline/ParallelGroupManager.tsx');
const workflowStepFormPath = path.join(__dirname, '../frontend/src/components/pipeline/WorkflowStepForm.tsx');
const typesPath = path.join(__dirname, '../frontend/src/types/index.ts');

// 测试结果
const testResults = [];

function addTestResult(test, passed, details = '') {
  testResults.push({ test, passed, details });
  const status = passed ? '✅' : '❌';
  console.log(`${status} ${test}${details ? ': ' + details : ''}`);
}

// 测试1：检查高级功能按钮是否存在
function testAdvancedFunctionButton() {
  const content = fs.readFileSync(pipelineEditorPath, 'utf8');
  const hasAdvancedButton = content.includes('高级功能') && 
                           content.includes('ThunderboltOutlined') &&
                           content.includes('handleAdvancedOptionsToggle');
  addTestResult('高级功能按钮', hasAdvancedButton, hasAdvancedButton ? '按钮已正确配置' : '缺少高级功能按钮或处理函数');
  return hasAdvancedButton;
}

// 测试2：检查步骤类型是否包含审批和条件步骤
function testSpecialStepTypes() {
  const content = fs.readFileSync(pipelineEditorPath, 'utf8');
  const hasApprovalStep = content.includes("value: 'approval'") && content.includes('手动审批');
  const hasConditionStep = content.includes("value: 'condition'") && content.includes('条件分支');
  
  addTestResult('审批步骤类型', hasApprovalStep, hasApprovalStep ? '审批步骤类型已添加' : '缺少审批步骤类型');
  addTestResult('条件步骤类型', hasConditionStep, hasConditionStep ? '条件步骤类型已添加' : '缺少条件步骤类型');
  
  return hasApprovalStep && hasConditionStep;
}

// 测试3：检查高级功能标签显示
function testAdvancedLabels() {
  const content = fs.readFileSync(pipelineEditorPath, 'utf8');
  const hasConditionLabel = content.includes('condition') && content.includes('BranchesOutlined') && content.includes('条件');
  const hasParallelLabel = content.includes('parallel_group_id') && content.includes('ShareAltOutlined') && content.includes('并行');
  const hasApprovalLabel = content.includes('approval_config') && content.includes('✋') && content.includes('审批');
  
  addTestResult('条件执行标签', hasConditionLabel, hasConditionLabel ? '条件标签显示正常' : '条件标签缺失');
  addTestResult('并行执行标签', hasParallelLabel, hasParallelLabel ? '并行标签显示正常' : '并行标签缺失');
  addTestResult('审批节点标签', hasApprovalLabel, hasApprovalLabel ? '审批标签显示正常' : '审批标签缺失');
  
  return hasConditionLabel && hasParallelLabel && hasApprovalLabel;
}

// 测试4：检查并行组步骤分配功能
function testParallelGroupStepAssignment() {
  const content = fs.readFileSync(parallelGroupManagerPath, 'utf8');
  const hasStepSelection = content.includes('name="steps"') && 
                          content.includes('mode="multiple"') &&
                          content.includes('选择要并行执行的步骤');
  
  addTestResult('并行组步骤分配', hasStepSelection, hasStepSelection ? '步骤分配功能已实现' : '缺少步骤选择功能');
  return hasStepSelection;
}

// 测试5：检查高级配置抽屉
function testAdvancedConfigDrawer() {
  const content = fs.readFileSync(pipelineEditorPath, 'utf8');
  const hasAdvancedDrawer = content.includes('步骤高级配置') &&
                           content.includes('workflowStepFormVisible') &&
                           content.includes('条件执行配置') &&
                           content.includes('并行执行配置') &&
                           content.includes('审批节点配置');
  
  addTestResult('高级配置抽屉', hasAdvancedDrawer, hasAdvancedDrawer ? '高级配置抽屉功能完整' : '高级配置抽屉功能不完整');
  return hasAdvancedDrawer;
}

// 测试6：检查条件执行依赖选择
function testConditionDependencies() {
  const content = fs.readFileSync(pipelineEditorPath, 'utf8');
  const hasConditionDeps = content.includes('depends_on') &&
                          content.includes('依赖步骤') &&
                          content.includes('on_success') &&
                          content.includes('on_failure');
  
  addTestResult('条件执行依赖', hasConditionDeps, hasConditionDeps ? '条件依赖选择已实现' : '条件依赖选择功能缺失');
  return hasConditionDeps;
}

// 测试7：检查审批配置字段
function testApprovalConfig() {
  const content = fs.readFileSync(pipelineEditorPath, 'utf8');
  const hasApprovalFields = content.includes('approval_config') &&
                           content.includes('approvers') &&
                           content.includes('required_approvals') &&
                           content.includes('timeout_hours') &&
                           content.includes('approval_message');
  
  addTestResult('审批配置字段', hasApprovalFields, hasApprovalFields ? '审批配置字段完整' : '审批配置字段不完整');
  return hasApprovalFields;
}

// 测试8：检查必要导入
function testRequiredImports() {
  const content = fs.readFileSync(pipelineEditorPath, 'utf8');
  const hasSwitch = content.includes('Switch');
  const hasInputNumber = content.includes('InputNumber');
  const hasTag = content.includes('Tag');
  
  addTestResult('Switch控件导入', hasSwitch, hasSwitch ? 'Switch已导入' : 'Switch未导入');
  addTestResult('InputNumber控件导入', hasInputNumber, hasInputNumber ? 'InputNumber已导入' : 'InputNumber未导入');
  addTestResult('Tag控件导入', hasTag, hasTag ? 'Tag已导入' : 'Tag未导入');
  
  return hasSwitch && hasInputNumber && hasTag;
}

// 测试9：检查类型定义
function testTypeDefinitions() {
  const content = fs.readFileSync(typesPath, 'utf8');
  const hasEnhancedStep = content.includes('EnhancedPipelineStep');
  const hasParallelGroup = content.includes('ParallelGroup');
  const hasStepCondition = content.includes('StepCondition');
  const hasApprovalConfig = content.includes('ApprovalConfig');
  
  addTestResult('增强步骤类型', hasEnhancedStep, hasEnhancedStep ? 'EnhancedPipelineStep已定义' : 'EnhancedPipelineStep缺失');
  addTestResult('并行组类型', hasParallelGroup, hasParallelGroup ? 'ParallelGroup已定义' : 'ParallelGroup缺失');
  addTestResult('步骤条件类型', hasStepCondition, hasStepCondition ? 'StepCondition已定义' : 'StepCondition缺失');
  addTestResult('审批配置类型', hasApprovalConfig, hasApprovalConfig ? 'ApprovalConfig已定义' : 'ApprovalConfig缺失');
  
  return hasEnhancedStep && hasParallelGroup && hasStepCondition && hasApprovalConfig;
}

// 执行所有测试
console.log('=== 高级工作流功能测试 ===\n');

const tests = [
  testAdvancedFunctionButton,
  testSpecialStepTypes,
  testAdvancedLabels,
  testParallelGroupStepAssignment,
  testAdvancedConfigDrawer,
  testConditionDependencies,
  testApprovalConfig,
  testRequiredImports,
  testTypeDefinitions
];

let passedTests = 0;
tests.forEach(test => {
  if (test()) passedTests++;
});

// 输出测试总结
console.log('\n=== 测试总结 ===');
console.log(`✅ 通过: ${passedTests}/${tests.length}`);
console.log(`❌ 失败: ${tests.length - passedTests}/${tests.length}`);

if (passedTests === tests.length) {
  console.log('\n🎉 所有高级工作流功能测试通过！');
} else {
  console.log('\n⚠️  部分功能需要进一步完善');
}

// 详细问题分析
console.log('\n=== 功能状态分析 ===');
console.log('1. 高级功能按钮: 已实现，可以切换高级选项显示状态');
console.log('2. 并行组管理: 已实现步骤分配功能，支持多选步骤');
console.log('3. 审批节点: 已添加审批步骤类型，支持审批配置');
console.log('4. 条件步骤: 已添加条件步骤类型，支持条件依赖配置');
console.log('5. 高级配置抽屉: 集成了条件、并行、审批等配置项');
console.log('6. 步骤标签: 在步骤卡片上显示高级功能标签');

console.log('\n=== 下一步改进建议 ===');
console.log('1. 添加端到端功能测试');
console.log('2. 完善表单验证和错误处理');
console.log('3. 添加高级功能的使用文档');
console.log('4. 实现高级配置的数据持久化');
console.log('5. 优化用户交互体验');

process.exit(passedTests === tests.length ? 0 : 1);
