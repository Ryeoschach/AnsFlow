# AnsFlow 系统设置模块设计文档

## 概述

AnsFlow系统设置模块是一个高度模块化、可扩展的配置管理系统，提供了统一的界面来管理平台的各项设置和配置。

## 核心特性

### 🔐 权限与安全
- **细粒度权限控制**：基于角色和权限的访问控制
- **模块级权限**：每个设置模块都可以独立配置访问权限
- **安全审计**：完整的操作日志和审计追踪

### 🧩 模块化设计
- **可插拔架构**：新模块可以轻松添加或移除
- **分类管理**：设置按功能分类组织（安全、集成、系统、用户）
- **灵活配置**：每个模块都有独立的配置和生命周期

### 🎨 用户体验
- **响应式设计**：自适应不同屏幕尺寸
- **快速导航**：侧边栏分类导航，支持收折
- **URL路由**：支持深度链接，可直接访问特定设置模块

## 架构设计

### 权限系统

```typescript
// 权限枚举
enum Permission {
  GIT_CREDENTIAL_VIEW = 'git_credential:view',
  GIT_CREDENTIAL_CREATE = 'git_credential:create',
  USER_MANAGE = 'user:manage',
  SYSTEM_CONFIG = 'system_config:edit',
  // ... 更多权限
}

// 角色定义
enum UserRole {
  SUPER_ADMIN = 'super_admin',
  ADMIN = 'admin',
  MANAGER = 'manager',
  DEVELOPER = 'developer',
  VIEWER = 'viewer'
}
```

### 模块配置

```typescript
interface SettingModule {
  key: string                    // 模块唯一标识
  title: string                  // 显示名称
  description: string            // 描述信息
  icon: React.ReactNode         // 图标
  component: React.ComponentType // 组件
  badge?: string | number       // 徽章（如：Beta、New）
  permission?: Permission[]     // 访问权限
  category: Category            // 所属分类
}
```

### 分类系统

设置模块按以下四大类别组织：

#### 🔒 安全与认证
- **Git凭据管理**：管理Git仓库认证凭据
- **安全设置**：密码策略、登录限制
- **API设置**：API密钥和访问控制
- **审计日志**：操作记录和合规报告

#### 🔗 集成与通知
- **云服务集成**：AWS、Azure、阿里云等
- **工具集成**：第三方工具和插件
- **通知设置**：邮件、Webhook、消息推送

#### ⚙️ 系统与监控
- **全局配置**：系统级配置和环境变量
- **系统监控**：性能监控和健康检查
- **数据备份**：备份策略和恢复管理
- **实验性功能**：Beta功能和预览特性

#### 👥 用户与团队
- **用户管理**：用户账户和角色管理
- **团队管理**：团队创建和协作配置

## 当前实现状态

### ✅ 已完成
1. **Git凭据管理模块**
   - 完整的CRUD功能
   - 多平台支持（GitHub、GitLab、Gitee等）
   - 多认证方式（用户名密码、SSH密钥、访问令牌）
   - 加密存储敏感信息
   - 连接测试功能

2. **权限管理系统**
   - 角色权限映射
   - 权限检查Hook
   - 权限守卫组件
   - 模块级访问控制

3. **系统设置主框架**
   - 响应式布局
   - 分类导航
   - URL路由支持
   - 模块懒加载

### 🚧 开发中
其他11个设置模块的具体实现（当前显示"功能开发中"占位页面）

## 扩展指南

### 添加新的设置模块

1. **创建组件**
```typescript
// 创建新的设置组件
const MyNewSetting: React.FC = () => {
  return (
    <Card title="我的新设置">
      {/* 设置内容 */}
    </Card>
  )
}
```

2. **定义权限**
```typescript
// 在 usePermissions.ts 中添加新权限
enum Permission {
  // ... 现有权限
  MY_NEW_SETTING_VIEW = 'my_new_setting:view',
  MY_NEW_SETTING_EDIT = 'my_new_setting:edit',
}
```

3. **注册模块**
```typescript
// 在 Settings.tsx 中添加模块配置
const settingModules: SettingModule[] = [
  // ... 现有模块
  {
    key: 'my-new-setting',
    title: '我的新设置',
    description: '这是一个新的设置模块',
    icon: <SettingOutlined />,
    component: MyNewSetting,
    category: 'system', // 选择合适的分类
    permission: Permission.MY_NEW_SETTING_VIEW
  }
]
```

### 添加新的权限

1. **定义权限枚举**
2. **更新角色权限映射**
3. **在组件中使用权限检查**

```typescript
// 使用权限守卫
<PermissionGuard permission={Permission.MY_PERMISSION}>
  <SensitiveComponent />
</PermissionGuard>

// 使用权限Hook
const { hasPermission } = usePermissions()
const canEdit = hasPermission(Permission.MY_PERMISSION)
```

## 安全考虑

### 前端安全
- 权限检查只是UI层面的控制
- 所有敏感操作必须在后端验证权限
- 敏感信息不在前端显示

### 后端安全
- API级别的权限验证
- 敏感数据加密存储
- 操作审计日志

### 最佳实践
- 最小权限原则
- 定期权限审计
- 敏感操作二次确认

## 技术栈

- **前端框架**：React 18 + TypeScript
- **UI组件库**：Ant Design 5
- **路由管理**：React Router v6
- **状态管理**：Zustand
- **构建工具**：Vite

## 未来计划

### 短期目标（1-2个月）
1. 完成用户管理模块
2. 实现系统监控模块
3. 添加通知设置模块

### 中期目标（3-6个月）
1. 实现云服务集成
2. 完善审计日志系统
3. 添加数据备份功能

### 长期目标（6个月+）
1. 插件化架构
2. 第三方扩展支持
3. 多租户支持

## 总结

AnsFlow系统设置模块提供了一个坚实的基础，支持平台的持续发展和功能扩展。通过模块化设计和细粒度权限控制，确保了系统的安全性、可维护性和可扩展性。
