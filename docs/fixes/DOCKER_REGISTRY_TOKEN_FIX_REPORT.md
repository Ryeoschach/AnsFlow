# Docker Registry API Token键名不一致修复报告

## 📋 问题概述

在AnsFlow项目中发现前端代码存在JWT Token键名不一致的问题，导致Docker Registry API调用时出现401认证错误。

## 🔍 问题分析

### 根本原因
- **主API服务** (`src/services/api.ts`) 使用 `localStorage.getItem('authToken')` 获取JWT token
- **Docker Registry服务** (`src/services/dockerRegistryService.ts`) 使用 `localStorage.getItem('token')` 获取JWT token
- **登录存储** (`src/stores/auth.ts`) 使用 `localStorage.setItem('authToken', token)` 存储JWT token

### 影响范围
Docker Registry API的所有操作都会出现401认证错误，包括：
- 获取注册表列表
- 创建/更新/删除注册表
- 测试注册表连接
- 注册表相关的所有操作

## 🛠️ 修复方案

### 修复内容
将 `dockerRegistryService.ts` 中所有的 `localStorage.getItem('token')` 统一修改为 `localStorage.getItem('authToken')`，确保与系统其他部分保持一致。

### 修改的方法
1. `getRegistries()` - 获取注册表列表
2. `getRegistry(id)` - 获取单个注册表详情
3. `createRegistry(data)` - 创建新注册表
4. `updateRegistry(id, data)` - 更新注册表
5. `deleteRegistry(id)` - 删除注册表
6. `testRegistry(id)` - 测试注册表连接
7. `setDefaultRegistry(id)` - 设置默认注册表
8. `getRegistryImages(registryId)` - 获取注册表镜像列表
9. `searchImages(registryId, query)` - 搜索镜像
10. `getRegistryStats(id)` - 获取注册表统计
11. `syncRegistry(id)` - 同步注册表信息

## ✅ 验证结果

### 前端代码验证
- ✅ `dockerRegistryService.ts` 中 `authToken` 使用次数: 11
- ✅ `dockerRegistryService.ts` 中 `token` 使用次数: 0 (已修复)
- ✅ 与 `api.ts` 保持一致

### API调用测试
- ✅ JWT Token获取成功
- ✅ Docker Registry API调用返回200状态码
- ✅ 成功获取注册表数据
- ✅ 响应数据格式正确

### 测试响应示例
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Local Registry",
      "url": "local://",
      "registry_type": "private",
      "status": "active",
      "is_default": true
    }
  ]
}
```

## 🎯 修复效果

1. **401认证错误完全解决** - Docker Registry API现在可以正确获取JWT token
2. **前端代码统一性** - 所有服务都使用统一的token键名 `authToken`
3. **用户体验改善** - 用户登录后可以正常访问Docker Registry管理功能
4. **系统稳定性提升** - 消除了由于token键名不一致导致的认证问题

## 📝 后续建议

1. **代码审查规范** - 在代码审查时注意检查localStorage键名的一致性
2. **统一常量管理** - 考虑将 `authToken` 定义为常量，避免硬编码
3. **单元测试覆盖** - 为authentication相关功能增加单元测试
4. **API文档更新** - 确保API文档中的认证说明与实际实现一致

## 🔗 相关文件

- `/frontend/src/services/dockerRegistryService.ts` - 主要修复文件
- `/frontend/src/services/api.ts` - 参考实现
- `/frontend/src/stores/auth.ts` - Token存储逻辑
- `/test_docker_registry_token_fix.py` - 验证脚本

---

**修复完成时间**: 2025年7月22日  
**修复验证**: ✅ 所有测试通过  
**影响用户**: 所有使用Docker Registry功能的用户  
**紧急程度**: 高（已解决）
