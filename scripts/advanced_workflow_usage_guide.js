#!/usr/bin/env node

/**
 * 高级工作流功能使用演示脚本
 * 展示如何使用条件执行、并行组、审批节点等高级功能
 */

console.log('🚀 高级工作流功能使用指南\n');

console.log('=== ✨ 功能概览 ===');
console.log('1. 🔀 条件执行分支 - 根据条件决定步骤是否执行');
console.log('2. ⚡ 并行执行策略 - 多个步骤同时执行，提高效率');
console.log('3. ✋ 手动审批节点 - 需要人工审批才能继续');
console.log('4. 🔄 重试策略 - 失败时自动重试');
console.log('5. 📢 通知配置 - 执行状态变化时发送通知');

console.log('\n=== 📋 使用步骤指南 ===');

console.log('\n🎯 步骤1: 启用高级功能');
console.log('   • 在流水线编辑器中点击 "高级功能" 按钮');
console.log('   • 按钮会高亮显示，表示高级选项已启用');
console.log('   • 此时步骤卡片会显示 "⚡" 高级配置按钮');

console.log('\n🏷️  步骤2: 添加特殊步骤类型');
console.log('   • 点击 "添加步骤" 按钮');
console.log('   • 在步骤类型中选择:');
console.log('     - "✋ 手动审批" - 创建审批节点');
console.log('     - "🔀 条件分支" - 创建条件步骤');
console.log('   • 系统会自动提示配置建议');

console.log('\n🔧 步骤3: 配置高级选项');
console.log('   • 点击步骤卡片上的 "⚡" 高级配置按钮');
console.log('   • 在弹出的抽屉中配置:');

console.log('\n   📝 条件执行配置:');
console.log('     - 总是执行 (默认)');
console.log('     - 前序步骤成功时执行');
console.log('     - 前序步骤失败时执行');
console.log('     - 自定义表达式 (如: $variables.env === "prod")');
console.log('     - 选择依赖的前序步骤');

console.log('\n   ⚡ 并行执行配置:');
console.log('     - 选择现有并行组');
console.log('     - 通过 "并行组管理" 创建新组');
console.log('     - 配置同步策略 (等待所有/任一/快速失败)');

console.log('\n   ✋ 审批节点配置:');
console.log('     - 启用 "是否需要审批" 开关');
console.log('     - 设置审批人员 (用户名或邮箱)');
console.log('     - 配置最少审批人数');
console.log('     - 设置审批超时时间');
console.log('     - 编写审批消息');

console.log('\n🔗 步骤4: 管理并行组');
console.log('   • 点击 "并行组管理" 按钮');
console.log('   • 创建新的并行组:');
console.log('     - 设置组名称和描述');
console.log('     - 选择同步策略');
console.log('     - 分配要并行执行的步骤');
console.log('     - 设置超时时间');

console.log('\n📊 步骤5: 分析工作流');
console.log('   • 点击 "工作流分析" 按钮');
console.log('   • 查看工作流的依赖关系');
console.log('   • 验证配置的正确性');

console.log('\n=== 🏷️  视觉标识说明 ===');
console.log('步骤卡片上会显示相应的标签:');
console.log('   🔀 条件 - 蓝色标签，表示有条件执行配置');
console.log('   ⚡ 并行 - 绿色标签，表示加入了并行组');
console.log('   ✋ 审批 - 橙色标签，表示需要审批');

console.log('\n=== 💡 最佳实践建议 ===');

console.log('\n🎯 条件执行最佳实践:');
console.log('   • 使用条件步骤控制不同环境的部署');
console.log('   • 在测试失败时执行清理步骤');
console.log('   • 根据代码变更类型执行不同的构建策略');

console.log('\n⚡ 并行执行最佳实践:');
console.log('   • 将独立的测试套件放入并行组');
console.log('   • 并行执行构建和安全扫描');
console.log('   • 多环境部署时使用并行组');

console.log('\n✋ 审批节点最佳实践:');
console.log('   • 在生产环境部署前添加审批');
console.log('   • 重要的数据库变更需要审批');
console.log('   • 设置合理的审批超时时间');

console.log('\n🔄 重试策略最佳实践:');
console.log('   • 网络相关步骤设置重试');
console.log('   • 设置适当的重试延迟');
console.log('   • 避免对破坏性操作设置重试');

console.log('\n=== 🚨 注意事项 ===');
console.log('   • 保存流水线后，高级配置才会持久化');
console.log('   • 并行组中的步骤应该是独立的');
console.log('   • 条件表达式支持JavaScript语法');
console.log('   • 审批人员需要有相应的权限');
console.log('   • 重试次数不宜设置过高');

console.log('\n=== 🔧 故障排除 ===');
console.log('   问题: 高级配置按钮不显示');
console.log('   解决: 先点击 "高级功能" 按钮启用');

console.log('\n   问题: 并行组中没有步骤可选');
console.log('   解决: 先创建普通步骤，再分配到并行组');

console.log('\n   问题: 条件表达式不生效');
console.log('   解决: 检查JavaScript语法，确保变量存在');

console.log('\n   问题: 审批流程被跳过');
console.log('   解决: 检查审批人员配置和权限设置');

console.log('\n🎉 恭喜! 您现在已经掌握了高级工作流功能的使用方法。');
console.log('开始创建更智能、更高效的CI/CD流水线吧! 🚀');
