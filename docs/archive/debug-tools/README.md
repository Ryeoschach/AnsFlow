# 调试工具归档说明

## 📋 归档概述

本目录包含了 AnsFlow 项目中开发的各种调试工具和相关文档。这些工具主要用于诊断和修复系统中的问题，特别是 Ansible 集成、JWT 认证和清单管理相关的问题。

## 📁 目录结构

```
docs/archive/debug-tools/
├── README.md                    # 本文档
├── components/                  # 调试组件归档
│   ├── AuthDebugPanel.tsx      # JWT认证调试面板
│   ├── SimpleDebugTool.tsx     # 简化版API调试工具
│   ├── InventoryGroupsDebugTool.tsx # 清单主机组详细调试工具
│   ├── InventoryDynamicDebugTool.tsx # 清单动态管理调试工具
│   ├── InventoryStatsDebugTool.tsx # 清单统计数据调试工具
│   └── PermissionDebug.tsx     # 权限调试工具
├── pages/                      # 调试页面归档
│   ├── Debug.tsx              # 统一调试页面
│   └── InventoryGroupTest.tsx # 清单主机组模态框测试页面
└── reports/                    # 修复报告归档
    └── inventory_dynamic_management_fix_report.md # 清单动态管理修复报告
```

## 🛠️ 工具说明

### 核心调试组件

#### 1. AuthDebugPanel.tsx
**用途**: JWT认证系统调试
**功能**:
- Token状态检查和刷新
- 认证流程可视化监控
- 登录/登出状态管理
- Token过期时间跟踪

#### 2. SimpleDebugTool.tsx
**用途**: 快速API调试
**功能**:
- 直接HTTP请求测试
- 响应数据结构分析
- 错误状态码诊断
- Token认证验证

#### 3. InventoryGroupsDebugTool.tsx
**用途**: 清单主机组详细调试
**功能**:
- 完整的API调用诊断流程
- 数据结构深度分析
- 字段映射问题识别
- 多API联合测试

#### 4. InventoryDynamicDebugTool.tsx
**用途**: 清单动态管理专用调试
**功能**:
- 4个核心API测试 (getAnsibleHosts, getAnsibleHostGroups, getInventoryHosts, getInventoryGroups)
- 数据映射逻辑验证
- 字段结构分析
- 修复建议生成

#### 5. InventoryStatsDebugTool.tsx
**用途**: 清单统计数据调试
**功能**:
- 统计数据一致性检查
- 计数同步状态验证
- 数据修复建议

#### 6. PermissionDebug.tsx
**用途**: 权限系统调试
**功能**:
- 用户权限检查
- 角色权限映射
- API权限验证

### 调试页面

#### 1. Debug.tsx
**用途**: 统一调试界面
**功能**:
- 集成所有调试工具的标签页界面
- 导航路径: `/debug`
- 已添加到主菜单系统

#### 2. InventoryGroupTest.tsx
**用途**: 清单主机组模态框测试
**功能**:
- 直接测试 InventoryGroupModal 组件
- 模拟用户操作场景
- 实时控制台日志监控

## 🔍 使用场景

### 1. API调用问题诊断
当遇到"获取清单主机组失败"等错误时：
1. 使用 SimpleDebugTool 快速测试API连通性
2. 使用 InventoryDynamicDebugTool 深度分析数据结构
3. 使用 InventoryGroupsDebugTool 进行完整诊断

### 2. 认证问题排查
当遇到JWT Token相关问题时：
1. 使用 AuthDebugPanel 检查Token状态
2. 验证Token刷新机制
3. 监控认证流程

### 3. 数据一致性问题
当清单统计数据不一致时：
1. 使用 InventoryStatsDebugTool 检查计数
2. 验证数据同步状态
3. 执行修复操作

## 📊 修复记录

### 主要修复问题
1. **清单动态管理API错误** - 修复了数据映射不匹配问题
2. **JWT认证Token管理** - 完善了Token生命周期管理
3. **清单主机组获取失败** - 解决了字段映射不一致问题

### 技术改进
1. 增强错误处理和日志记录
2. 改进数据结构类型安全
3. 统一API调用标准
4. 完善调试工具集

## 🚀 开发环境集成

### 路由配置
```typescript
// 已添加到 App.tsx
<Route path="/debug" element={<Debug />} />
```

### 菜单配置
```typescript
// 已添加到 MainLayout.tsx
{
  key: '/debug',
  icon: <BugOutlined />,
  label: '调试工具',
}
```

## 📝 使用建议

1. **开发阶段**: 可继续使用这些工具进行开发调试
2. **生产环境**: 建议移除或限制访问调试工具
3. **问题排查**: 按照工具分类使用对应的调试组件
4. **新功能开发**: 可参考现有工具创建新的调试组件

## 🔄 后续维护

1. **定期更新**: 随着系统演进更新调试工具
2. **性能优化**: 监控调试工具对系统性能的影响
3. **安全考虑**: 确保调试工具不暴露敏感信息
4. **文档维护**: 及时更新调试工具使用说明

---

*归档时间: 2025年8月1日*
*项目版本: 0718分支*
*维护状态: 已完成，可用于参考*
