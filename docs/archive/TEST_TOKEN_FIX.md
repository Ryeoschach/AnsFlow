# 工具Token/密码更新问题修复测试

## 问题描述
用户反馈："工具的密码/token 更新后再打开消失了"

## 问题原因分析

### 1. 后端序列化器问题
- `CICDToolSerializer` 将 `token` 字段设置为 `write_only=True`
- GET请求时不返回token值，导致前端无法知道是否已设置密码
- 缺少专门的更新序列化器处理token字段的可选更新

### 2. 前端表单逻辑问题  
- 编辑时用 `form.setFieldsValue(tool)` 直接设置，但tool对象中没有token字段
- 前端password字段始终为空
- 无法区分"未设置密码"和"不修改密码"两种情况

### 3. 数据模型不一致
- 后端模型中token是必填字段，但前端无法获取其状态

## 修复方案

### 后端修复

1. **新增has_token字段**：
   ```python
   def get_has_token(self, obj):
       """返回是否已设置token"""
       return bool(obj.token)
   ```

2. **创建专门的更新序列化器**：
   ```python
   class CICDToolUpdateSerializer(serializers.ModelSerializer):
       token = serializers.CharField(required=False, allow_blank=True)
       
       def update(self, instance, validated_data):
           token = validated_data.get('token')
           if not token:
               validated_data.pop('token', None)
           return super().update(instance, validated_data)
   ```

3. **视图集序列化器选择**：
   ```python
   def get_serializer_class(self):
       if self.action == 'create':
           return CICDToolCreateSerializer
       elif self.action in ['update', 'partial_update']:
           return CICDToolUpdateSerializer
       return CICDToolSerializer
   ```

### 前端修复

1. **表单初始化修复**：
   ```typescript
   const handleEditTool = (tool: Tool) => {
     const formValues = {
       ...tool,
       password: '' // 密码字段总是为空，用户需要重新输入
     }
     form.setFieldsValue(formValues)
   }
   ```

2. **表单提交逻辑**：
   ```typescript
   // 如果是编辑模式且password为空，则不发送token字段
   if (editingTool && !values.password) {
     delete toolData.token
   }
   ```

3. **添加认证状态显示**：
   ```typescript
   {
     title: '认证状态',
     render: (_, record: Tool) => (
       record.has_token ? 
       <Tag color="green">已配置</Tag> : 
       <Tag color="red">未配置</Tag>
     ),
   }
   ```

4. **用户体验优化**：
   ```typescript
   rules={[
     { 
       required: !editingTool, // 创建时必填，编辑时可选
       message: editingTool ? '' : '请输入密码或访问令牌' 
     }
   ]}
   extra={editingTool ? "留空表示不修改当前密码/Token" : ""}
   ```

## 测试步骤

### 1. 创建新工具测试
1. 访问 http://localhost:3000/tools
2. 点击"添加工具"
3. 填写必要信息，包括密码/Token
4. 创建成功后，应该显示"认证状态：已配置"

### 2. 编辑工具测试（不修改密码）
1. 点击已有工具的"编辑"按钮
2. 修改名称等其他字段，密码字段保持为空
3. 点击更新
4. 重新打开编辑，应该显示"认证状态：已配置"

### 3. 编辑工具测试（修改密码）
1. 点击已有工具的"编辑"按钮
2. 在密码字段输入新的密码/Token
3. 点击更新
4. 重新打开编辑，应该显示"认证状态：已配置"

### 4. 健康检查测试
1. 点击"测试连接"按钮
2. 应该能正确使用保存的Token进行认证

## 预期结果

1. ✅ 创建工具时密码正确保存
2. ✅ 编辑工具时密码留空不会清空已保存的密码
3. ✅ 编辑工具时输入新密码会正确更新
4. ✅ 界面显示清晰的认证状态指示
5. ✅ 健康检查使用正确的认证信息

## 验证命令

```bash
# 后端日志查看
docker logs ansflow-django-1 -f

# 前端开发服务器
cd frontend && npm run dev

# 检查API响应
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/cicd/tools/1/ | jq
```

## 修复文件清单

### 后端文件
- `/backend/django_service/cicd_integrations/serializers.py` - 新增CICDToolUpdateSerializer
- `/backend/django_service/cicd_integrations/views/tools.py` - 更新序列化器选择逻辑

### 前端文件  
- `/frontend/src/pages/Tools.tsx` - 修复表单逻辑和UI显示
- `/frontend/src/types/index.ts` - 更新Tool类型定义

## 关键改进点

1. **数据一致性**：后端不再暴露敏感token，但提供has_token状态
2. **用户体验**：清晰的认证状态指示和操作提示
3. **安全性**：密码字段始终不回显，避免敏感信息泄露
4. **灵活性**：支持"仅更新其他字段"和"同时更新密码"两种场景
