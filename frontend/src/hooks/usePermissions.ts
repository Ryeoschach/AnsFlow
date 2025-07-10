import React, { useState, useEffect } from 'react'
import { useAuthStore } from '../stores/auth'

// 权限枚举
export enum Permission {
  // 用户管理权限
  USER_VIEW = 'user:view',
  USER_CREATE = 'user:create', 
  USER_EDIT = 'user:edit',
  USER_DELETE = 'user:delete',
  
  // 团队管理权限
  TEAM_VIEW = 'team:view',
  TEAM_CREATE = 'team:create',
  TEAM_EDIT = 'team:edit',
  TEAM_DELETE = 'team:delete',
  
  // Git凭据管理权限
  GIT_CREDENTIAL_VIEW = 'git_credential:view',
  GIT_CREDENTIAL_CREATE = 'git_credential:create',
  GIT_CREDENTIAL_EDIT = 'git_credential:edit',
  GIT_CREDENTIAL_DELETE = 'git_credential:delete',
  GIT_CREDENTIAL_TEST = 'git_credential:test',
  
  // 系统设置权限
  SYSTEM_CONFIG_VIEW = 'system_config:view',
  SYSTEM_CONFIG_EDIT = 'system_config:edit',
  
  // 安全设置权限
  SECURITY_CONFIG_VIEW = 'security_config:view',
  SECURITY_CONFIG_EDIT = 'security_config:edit',
  
  // 审计日志权限
  AUDIT_LOG_VIEW = 'audit_log:view',
  
  // API设置权限
  API_CONFIG_VIEW = 'api_config:view',
  API_CONFIG_EDIT = 'api_config:edit',
  API_ENDPOINT_VIEW = 'api_endpoint:view',
  API_ENDPOINT_CREATE = 'api_endpoint:create',
  API_ENDPOINT_EDIT = 'api_endpoint:edit',
  API_ENDPOINT_DELETE = 'api_endpoint:delete',
  API_ENDPOINT_TEST = 'api_endpoint:test',
  API_ENDPOINT_DISCOVER = 'api_endpoint:discover',
  
  // 监控权限
  MONITORING_VIEW = 'monitoring:view',
  
  // 备份权限
  BACKUP_VIEW = 'backup:view',
  BACKUP_CREATE = 'backup:create',
  BACKUP_RESTORE = 'backup:restore',
  
  // 集成配置权限
  INTEGRATION_VIEW = 'integration:view',
  INTEGRATION_EDIT = 'integration:edit',
  
  // 超级管理员权限
  SUPER_ADMIN = 'super_admin'
}

// 用户角色枚举
export enum UserRole {
  SUPER_ADMIN = 'super_admin',
  ADMIN = 'admin',
  MANAGER = 'manager',
  DEVELOPER = 'developer',
  VIEWER = 'viewer',
  USER = 'user'
}

// 角色权限映射
const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  [UserRole.SUPER_ADMIN]: Object.values(Permission),
  
  [UserRole.ADMIN]: [
    Permission.USER_VIEW,
    Permission.USER_CREATE,
    Permission.USER_EDIT,
    Permission.TEAM_VIEW,
    Permission.TEAM_CREATE,
    Permission.TEAM_EDIT,
    Permission.GIT_CREDENTIAL_VIEW,
    Permission.GIT_CREDENTIAL_CREATE,
    Permission.GIT_CREDENTIAL_EDIT,
    Permission.GIT_CREDENTIAL_DELETE,
    Permission.GIT_CREDENTIAL_TEST,
    Permission.SYSTEM_CONFIG_VIEW,
    Permission.SYSTEM_CONFIG_EDIT,
    Permission.SECURITY_CONFIG_VIEW,
    Permission.SECURITY_CONFIG_EDIT,
    Permission.AUDIT_LOG_VIEW,
    Permission.API_CONFIG_VIEW,
    Permission.API_CONFIG_EDIT,
    Permission.API_ENDPOINT_VIEW,
    Permission.API_ENDPOINT_CREATE,
    Permission.API_ENDPOINT_EDIT,
    Permission.API_ENDPOINT_DELETE,
    Permission.API_ENDPOINT_TEST,
    Permission.API_ENDPOINT_DISCOVER,
    Permission.MONITORING_VIEW,
    Permission.BACKUP_VIEW,
    Permission.BACKUP_CREATE,
    Permission.INTEGRATION_VIEW,
    Permission.INTEGRATION_EDIT
  ],
  
  [UserRole.MANAGER]: [
    Permission.USER_VIEW,
    Permission.TEAM_VIEW,
    Permission.TEAM_EDIT,
    Permission.GIT_CREDENTIAL_VIEW,
    Permission.GIT_CREDENTIAL_CREATE,
    Permission.GIT_CREDENTIAL_EDIT,
    Permission.GIT_CREDENTIAL_TEST,
    Permission.SYSTEM_CONFIG_VIEW,
    Permission.AUDIT_LOG_VIEW,
    Permission.API_ENDPOINT_VIEW,
    Permission.API_ENDPOINT_TEST,
    Permission.MONITORING_VIEW,
    Permission.INTEGRATION_VIEW
  ],
  
  [UserRole.DEVELOPER]: [
    Permission.GIT_CREDENTIAL_VIEW,
    Permission.GIT_CREDENTIAL_CREATE,
    Permission.GIT_CREDENTIAL_EDIT,
    Permission.GIT_CREDENTIAL_TEST,
    Permission.MONITORING_VIEW
  ],
  
  [UserRole.VIEWER]: [
    Permission.GIT_CREDENTIAL_VIEW,
    Permission.MONITORING_VIEW
  ],
  
  [UserRole.USER]: [
    Permission.GIT_CREDENTIAL_VIEW,
    Permission.MONITORING_VIEW
  ]
}

// 用户信息接口
interface UserInfo {
  id: number
  username: string
  email: string
  role: UserRole
  permissions: Permission[]
  is_staff: boolean
  is_superuser: boolean
}

// 权限管理Hook
export const usePermissions = () => {
  const { user, isAuthenticated } = useAuthStore()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 如果用户已认证，则权限已经加载完成
    if (isAuthenticated && user) {
      setLoading(false)
    } else if (!isAuthenticated) {
      setLoading(false)
    }
  }, [isAuthenticated, user])

  // 构建用户信息，包括权限
  const userInfo: UserInfo | null = user ? {
    id: user.id,
    username: user.username,
    email: user.email,
    role: user.is_staff ? (user.is_superuser ? UserRole.SUPER_ADMIN : UserRole.ADMIN) : UserRole.USER,
    permissions: user.is_superuser 
      ? ROLE_PERMISSIONS[UserRole.SUPER_ADMIN]
      : user.is_staff 
        ? ROLE_PERMISSIONS[UserRole.ADMIN]
        : ROLE_PERMISSIONS[UserRole.USER],
    is_staff: user.is_staff,
    is_superuser: user.is_superuser || false
  } : null

  // 检查是否有指定权限
  const hasPermission = (permission: Permission | Permission[]): boolean => {
    if (!userInfo) return false
    
    // 超级管理员拥有所有权限
    if (userInfo.is_superuser) return true
    
    const permissions = Array.isArray(permission) ? permission : [permission]
    return permissions.every(perm => userInfo.permissions.includes(perm))
  }

  // 检查是否有任意一个权限
  const hasAnyPermission = (permissions: Permission[]): boolean => {
    if (!userInfo) return false
    
    // 超级管理员拥有所有权限
    if (userInfo.is_superuser) return true
    
    return permissions.some(perm => userInfo.permissions.includes(perm))
  }

  // 检查角色
  const hasRole = (role: UserRole | UserRole[]): boolean => {
    if (!userInfo) return false
    
    const roles = Array.isArray(role) ? role : [role]
    return roles.includes(userInfo.role)
  }

  // 获取角色的所有权限
  const getRolePermissions = (role: UserRole): Permission[] => {
    return ROLE_PERMISSIONS[role] || []
  }

  // 检查是否是管理员
  const isAdmin = (): boolean => {
    return hasRole([UserRole.SUPER_ADMIN, UserRole.ADMIN])
  }

  // 检查是否是超级管理员
  const isSuperAdmin = (): boolean => {
    return userInfo?.is_superuser || false
  }

  return {
    userInfo,
    loading,
    hasPermission,
    hasAnyPermission,
    hasRole,
    getRolePermissions,
    isAdmin,
    isSuperAdmin,
    // API端点相关权限便捷方法 - 使用函数形式避免初始化时权限检查失败
    canViewAPIEndpoints: () => hasPermission(Permission.API_ENDPOINT_VIEW),
    canEditAPIEndpoints: () => hasPermission(Permission.API_ENDPOINT_EDIT),
    canDeleteAPIEndpoints: () => hasPermission(Permission.API_ENDPOINT_DELETE),
    canTestAPIEndpoints: () => hasPermission(Permission.API_ENDPOINT_TEST),
    canDiscoverAPIEndpoints: () => hasPermission(Permission.API_ENDPOINT_DISCOVER),
  }
}

export default usePermissions
