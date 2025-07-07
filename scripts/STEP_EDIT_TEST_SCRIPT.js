/**
 * 步骤编辑功能测试脚本
 * 在浏览器开发者工具控制台中运行此脚本来验证修复效果
 */

// 测试函数：模拟步骤编辑流程
function testStepEdit() {
  console.log('🧪 开始测试步骤编辑功能...')
  
  // 1. 检查当前页面是否在流水线编辑器
  if (!window.location.pathname.includes('/pipeline')) {
    console.log('❌ 请先导航到流水线编辑页面')
    return
  }
  
  // 2. 检查是否有步骤可以编辑
  const editButtons = document.querySelectorAll('[data-testid="edit-step"], .edit-step-btn, button[title*="编辑"]')
  if (editButtons.length === 0) {
    console.log('❌ 未找到可编辑的步骤，请先添加步骤')
    return
  }
  
  console.log(`✅ 找到 ${editButtons.length} 个可编辑步骤`)
  
  // 3. 提供手动测试指南
  console.log(`
📋 手动测试步骤：
1. 点击任意步骤的"编辑"按钮
2. 修改步骤内容（如名称、描述、参数等）
3. 点击"更新"按钮
4. 观察控制台日志，查看以下关键信息：
   - 📝 Step edit - constructed stepData (表单数据构建)
   - 🔄 Step edit - step after update (本地状态更新)
   - 🔍 Step X - building API payload (API请求构建)
   - 🚀 Step edit - API payload (完整API请求)
   - ✅ Step edit - API request successful (API响应)
   - ✅ Step edit - auto-save completed successfully (保存完成)

🔍 重点检查：
- 修改的内容是否正确反映在 "constructed stepData" 中
- "step after update" 中的 parameters 是否包含最新修改
- "API payload" 中对应步骤的 parameters 是否正确
- API 响应是否成功，没有错误

🎯 预期结果：
- 页面不会跳转，保持在当前编辑页面
- 修改的内容立即生效并保存到后端
- 刷新页面后修改内容仍然存在
`)
  
  // 4. 监听控制台输出
  const originalLog = console.log
  console.log = function(...args) {
    if (args[0] && typeof args[0] === 'string' && args[0].includes('Step edit')) {
      originalLog('🧪 TEST CAPTURED:', ...args)
    }
    originalLog(...args)
  }
  
  console.log('🎯 测试监听已启动，请开始手动测试')
}

// 恢复正常日志的函数
function restoreConsole() {
  location.reload() // 简单粗暴的方式恢复
}

// 立即运行测试
testStepEdit()

// 暴露到全局作用域
window.testStepEdit = testStepEdit
window.restoreConsole = restoreConsole
