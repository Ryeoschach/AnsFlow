# Settings 页面快速启动指南

## 🚀 快速启动

### 1. 启动后端服务
```bash
cd backend/django_service
python manage.py migrate  # 如果是首次运行
python manage.py runserver
```

后端服务将在 `http://localhost:8000` 启动

### 2. 启动前端服务
```bash
cd frontend
npm install  # 如果是首次运行
npm start
```

前端服务将在 `http://localhost:3000` 启动

### 3. 访问 Settings 页面
打开浏览器，访问：`http://localhost:3000/settings`

## 🔑 获取访问令牌

### 方法1: 使用 Django Admin
1. 访问 `http://localhost:8000/admin`
2. 使用超级用户账号登录
3. 创建或查看用户

### 方法2: 使用 API
```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

## 📋 功能验证清单

### 用户管理
- [ ] 查看用户列表
- [ ] 创建新用户
- [ ] 编辑用户信息
- [ ] 切换用户状态
- [ ] 删除用户

### 审计日志
- [ ] 查看审计日志列表
- [ ] 筛选日志记录
- [ ] 查看日志详情
- [ ] 导出日志（如果已实现）

### 系统监控
- [ ] 查看系统指标
- [ ] 实时数据刷新
- [ ] 系统健康状态
- [ ] 服务状态列表

## 🔧 故障排除

### 常见问题

1. **后端启动失败**
   - 检查 Python 依赖是否安装
   - 确认数据库连接正常
   - 运行数据库迁移

2. **前端编译错误**
   - 确保 Node.js 版本兼容
   - 清除 node_modules 重新安装
   - 检查 TypeScript 错误

3. **API 调用失败**
   - 确认后端服务正在运行
   - 检查 JWT token 是否有效
   - 验证 API 路由配置

4. **页面显示异常**
   - 检查浏览器控制台错误
   - 确认组件导入正确
   - 验证数据格式匹配

## 📞 技术支持

如遇到问题，请检查：
1. 控制台错误日志
2. 网络请求状态
3. 数据库连接
4. 服务配置文件

## 🎉 开发完成！

Settings 页面现已完全就绪，包含：
- ✅ 完整的后端 API
- ✅ 现代化前端界面
- ✅ 企业级功能模块
- ✅ TypeScript 类型安全
- ✅ 响应式设计

祝开发愉快！ 🚀
