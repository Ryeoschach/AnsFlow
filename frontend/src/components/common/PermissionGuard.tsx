import React from 'react'
import { usePermissions, Permission, UserRole } from '../../hooks/usePermissions'

// 权限检查组件
interface PermissionGuardProps {
  permission?: Permission | Permission[]
  role?: UserRole | UserRole[]
  fallback?: React.ReactNode
  children: React.ReactNode
}

export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  permission,
  role,
  fallback = null,
  children
}) => {
  const { hasPermission, hasRole } = usePermissions()

  // 检查权限
  const hasRequiredPermission = permission ? hasPermission(permission) : true
  
  // 检查角色
  const hasRequiredRole = role ? hasRole(role) : true

  // 只有同时满足权限和角色要求才显示内容
  if (hasRequiredPermission && hasRequiredRole) {
    return <>{children}</>
  }

  return <>{fallback}</>
}

export default PermissionGuard
