# 🔧 流水线步骤编辑问题排查指南

## 问题描述
用户反馈：在流水线拖拽式页面编辑步骤后点击"更新"，页面显示"更新成功"，但控制台没有看到API请求，实际保存没有生效。

## 已添加的调试日志

我已经在代码中添加了详细的调试日志，请按以下步骤进行排查：

### 1. 打开浏览器开发者工具
- 按 F12 或右键"检查"
- 切换到 Console 标签

### 2. 重现问题操作
1. 打开流水线编辑器
2. 点击某个步骤的"编辑"按钮
3. 修改步骤内容
4. 点击"更新"按钮

### 3. 查看控制台输出

你应该看到以下日志信息：

```
🔍 Step edit - checking if pipeline exists: true 123
📋 Step edit - validating pipeline form...
📋 Step edit - pipeline info: {name: "...", description: "..."}
🚀 Step edit - sending API request to update pipeline: 3 steps
🚀 Step edit - API payload: {name: "...", steps: [...]}
🌐 Step edit - calling apiService.updatePipeline...
✅ Step edit - API request successful: {id: 123, ...}
🔄 Step edit - updating local state with API response steps
✅ Step edit - auto-save completed successfully
```

### 4. 问题排查

#### 情况A：没有看到任何日志
**可能原因**：
- 代码更新没有生效，需要刷新页面
- 控制台被清理了

**解决方案**：
1. 强制刷新页面 (Ctrl+Shift+R 或 Cmd+Shift+R)
2. 重新操作

#### 情况B：看到日志但停在某个步骤
根据最后一条日志判断问题：

**停在 "checking if pipeline exists"**：
- pipeline 对象可能为空
- 检查流水线是否正确加载

**停在 "validating pipeline form"**：
- 流水线基本信息表单验证失败
- 检查流水线名称等必填字段

**停在 "calling apiService.updatePipeline"**：
- API请求发送失败
- 检查网络连接和认证状态

#### 情况C：看到错误日志 "❌ Step edit - auto-save failed"
- API请求失败
- 查看详细错误信息
- 可能是后端服务问题

### 5. 网络请求检查

即使控制台没有显示API请求，也要检查 Network 标签：

1. 切换到 Network 标签
2. 确保勾选了 "Preserve log"
3. 重现操作
4. 查找以下请求：
   - `PUT /api/v1/pipelines/pipelines/{id}/`

### 6. 手动测试API

如果自动保存失败，可以手动点击"保存流水线"按钮测试：
- 这会调用相同的API
- 如果手动保存成功，说明API本身是正常的
- 问题可能在步骤编辑的自动保存逻辑中

## 临时解决方案

如果步骤编辑的自动保存有问题，可以使用以下工作流程：

1. **编辑步骤**：点击步骤的编辑按钮，修改内容
2. **点击更新**：更新本地状态（会看到"步骤更新成功"）
3. **手动保存**：点击右上角的"保存流水线"按钮
4. **验证保存**：使用"预览Pipeline"功能验证内容是否正确

## 代码回滚选项

如果你希望暂时禁用自动保存，回到原来的工作模式（需要手动保存），我可以提供一个简化版本的代码修改。

## 下一步行动

请按照上述步骤进行排查，并反馈：
1. 控制台看到了哪些日志？
2. Network 标签是否有API请求？
3. 手动"保存流水线"是否正常？

这将帮助我们精确定位问题所在。
