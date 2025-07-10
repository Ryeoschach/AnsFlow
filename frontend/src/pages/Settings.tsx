import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { 
  Card, 
  Menu, 
  Layout, 
  Typography, 
  Space, 
  Badge,
  Alert,
  Button,
  Spin
} from 'antd'
import {
  SettingOutlined,
  KeyOutlined,
  UserOutlined,
  SecurityScanOutlined,
  NotificationOutlined,
  DatabaseOutlined,
  CloudOutlined,
  ExperimentOutlined,
  TeamOutlined,
  LockOutlined,
  SafetyOutlined,
  AuditOutlined,
  ApiOutlined,
  ToolOutlined,
  GlobalOutlined,
  ClusterOutlined,
  CloudUploadOutlined
} from '@ant-design/icons'
import GitCredentialManager from '../components/git/GitCredentialManager'
import KubernetesSettings from '../components/kubernetes/KubernetesSettings'
import DockerRegistrySettings from '../components/docker/DockerRegistrySettings'
import UserManagement from '../components/settings/UserManagement'
import AuditLogs from '../components/settings/AuditLogs'
import SystemMonitoring from '../components/settings/SystemMonitoring'
import { ApiManagement } from '../components/settings/ApiManagement'
import TeamManagement from '../components/settings/TeamManagement'
import GlobalConfiguration from '../components/settings/GlobalConfiguration'
import NotificationSettingsComponent from '../components/settings/NotificationSettings'
import SystemBackup from '../components/settings/SystemBackup'
import { usePermissions, Permission } from '../hooks/usePermissions'
import PermissionGuard from '../components/common/PermissionGuard'

const { Title, Text } = Typography
const { Sider, Content } = Layout

// 设置模块配置
interface SettingModule {
  key: string
  title: string
  description: string
  icon: React.ReactNode
  component: React.ComponentType
  badge?: string | number
  permission?: Permission | Permission[]
  category: 'security' | 'integration' | 'system' | 'user'
}

// 通知设置组件
const NotificationSettings: React.FC = () => (
  <Card title="通知设置" size="small">
    <Alert
      message="功能开发中"
      description="邮件通知、Webhook、消息推送等配置功能正在开发中..."
      type="info"
      showIcon
    />
  </Card>
)

// 安全设置组件
const SecuritySettings: React.FC = () => (
  <Card title="安全设置" size="small">
    <Alert
      message="功能开发中"
      description="密码策略、登录限制、二次认证等安全配置正在开发中..."
      type="info"
      showIcon
    />
  </Card>
)

// API设置组件
const ApiSettings: React.FC = () => (
  <Card title="API设置" size="small">
    <Alert
      message="功能开发中"
      description="API密钥管理、访问控制、限流配置等功能正在开发中..."
      type="info"
      showIcon
    />
  </Card>
)

// 数据备份组件
const DataBackup: React.FC = () => (
  <Card title="数据备份" size="small">
    <Alert
      message="功能开发中"
      description="数据备份策略、恢复管理、存储配置等功能正在开发中..."
      type="info"
      showIcon
    />
  </Card>
)

// 云集成设置组件
const CloudIntegration: React.FC = () => (
  <Card title="云服务集成" size="small">
    <Alert
      message="功能开发中"
      description="AWS、Azure、阿里云等云服务集成配置正在开发中..."
      type="info"
      showIcon
    />
  </Card>
)

// 实验性功能组件
const ExperimentalFeatures: React.FC = () => (
  <Card title="实验性功能" size="small">
    <Alert
      message="功能开发中"
      description="Beta功能、预览特性、实验性配置等正在开发中..."
      type="warning"
      showIcon
    />
  </Card>
)

// 团队管理组件
const TeamManagementComponent: React.FC = () => <TeamManagement />

// 全局配置组件
const GlobalConfigurationComponent: React.FC = () => <GlobalConfiguration />

// 工具集成组件
const ToolIntegration: React.FC = () => (
  <Card title="工具集成" size="small">
    <Alert
      message="功能开发中"
      description="第三方工具集成、插件管理、扩展配置等功能正在开发中..."
      type="info"
      showIcon
    />
  </Card>
)

const Settings: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [selectedModule, setSelectedModule] = useState<string>('git-credentials')
  const [collapsedSider, setCollapsedSider] = useState(false)
  const { hasPermission, loading: permissionLoading } = usePermissions()

  // 从URL参数获取模块
  useEffect(() => {
    const moduleFromUrl = searchParams.get('module')
    if (moduleFromUrl) {
      setSelectedModule(moduleFromUrl)
    }
  }, [searchParams])

  // 设置模块配置 - 按类别组织，便于扩展
  const settingModules: SettingModule[] = [
    // 安全类
    {
      key: 'git-credentials',
      title: 'Git凭据管理',
      description: '管理Git仓库的认证凭据',
      icon: <KeyOutlined />,
      component: GitCredentialManager,
      category: 'security',
      permission: Permission.GIT_CREDENTIAL_VIEW
    },
    {
      key: 'security',
      title: '安全设置',
      description: '密码策略、登录安全等',
      icon: <SecurityScanOutlined />,
      component: SecuritySettings,
      category: 'security',
      permission: Permission.SECURITY_CONFIG_VIEW
    },
    {
      key: 'api-management',
      title: 'API接口管理',
      description: 'API端点配置和管理',
      icon: <ApiOutlined />,
      component: ApiManagement,
      category: 'security',
      permission: Permission.API_ENDPOINT_VIEW
    },
    {
      key: 'audit-logs',
      title: '审计日志',
      description: '系统操作和访问记录',
      icon: <AuditOutlined />,
      component: AuditLogs,
      category: 'security',
      permission: Permission.AUDIT_LOG_VIEW
    },

    // 集成类
    {
      key: 'docker-registries',
      title: 'Docker 注册表',
      description: 'Docker 镜像仓库配置管理',
      icon: <CloudUploadOutlined />,
      component: DockerRegistrySettings,
      category: 'integration',
      permission: Permission.INTEGRATION_VIEW
    },
    {
      key: 'kubernetes-clusters',
      title: 'Kubernetes 集群',
      description: 'K8s 集群和命名空间管理',
      icon: <ClusterOutlined />,
      component: KubernetesSettings,
      category: 'integration',
      permission: Permission.INTEGRATION_VIEW
    },
    {
      key: 'cloud-integration',
      title: '云服务集成',
      description: '云平台和服务集成',
      icon: <CloudOutlined />,
      component: CloudIntegration,
      category: 'integration',
      permission: Permission.INTEGRATION_VIEW
    },
    {
      key: 'tool-integration',
      title: '工具集成',
      description: '第三方工具和插件',
      icon: <ToolOutlined />,
      component: ToolIntegration,
      category: 'integration',
      permission: Permission.INTEGRATION_VIEW
    },
    {
      key: 'notifications',
      title: '通知设置',
      description: '邮件、Webhook等通知配置',
      icon: <NotificationOutlined />,
      component: NotificationSettingsComponent,
      category: 'integration',
      permission: Permission.INTEGRATION_VIEW
    },

    // 系统类
    {
      key: 'global-config',
      title: '全局配置',
      description: '系统级配置和环境设置',
      icon: <GlobalOutlined />,
      component: GlobalConfigurationComponent,
      category: 'system',
      permission: Permission.SYSTEM_CONFIG_VIEW
    },
    {
      key: 'monitoring',
      title: '系统监控',
      description: '性能监控和健康检查',
      icon: <DatabaseOutlined />,
      component: SystemMonitoring,
      category: 'system',
      permission: Permission.MONITORING_VIEW
    },
    {
      key: 'backup',
      title: '数据备份',
      description: '数据备份和恢复管理',
      icon: <SafetyOutlined />,
      component: SystemBackup,
      category: 'system',
      permission: Permission.BACKUP_VIEW
    },
    {
      key: 'experimental',
      title: '实验性功能',
      description: 'Beta功能和预览特性',
      icon: <ExperimentOutlined />,
      component: ExperimentalFeatures,
      badge: 'Beta',
      category: 'system',
      permission: Permission.SYSTEM_CONFIG_VIEW
    },

    // 用户类
    {
      key: 'users',
      title: '用户管理',
      description: '用户账户和角色管理',
      icon: <UserOutlined />,
      component: UserManagement,
      category: 'user',
      permission: Permission.USER_VIEW
    },
    {
      key: 'teams',
      title: '团队管理',
      description: '团队和协作管理',
      icon: <TeamOutlined />,
      component: TeamManagementComponent,
      category: 'user',
      permission: Permission.TEAM_VIEW
    }
  ]

  // 过滤用户有权限访问的模块
  const accessibleModules = settingModules.filter(module => {
    if (!module.permission) return true
    return hasPermission(module.permission)
  })

  // 按类别分组模块
  const modulesByCategory = accessibleModules.reduce((acc, module) => {
    if (!acc[module.category]) {
      acc[module.category] = []
    }
    acc[module.category].push(module)
    return acc
  }, {} as Record<string, SettingModule[]>)

  // 类别配置
  const categoryConfig = {
    security: { title: '安全与认证', icon: <LockOutlined /> },
    integration: { title: '集成与通知', icon: <ApiOutlined /> },
    system: { title: '系统与监控', icon: <SettingOutlined /> },
    user: { title: '用户与团队', icon: <TeamOutlined /> }
  }

  // 获取当前选中的模块
  const currentModule = accessibleModules.find(m => m.key === selectedModule)
  const CurrentComponent = currentModule?.component || (() => <div>模块不存在或无权限访问</div>)

  // 确保默认选中的模块用户有权限访问
  useEffect(() => {
    if (!permissionLoading && accessibleModules.length > 0) {
      const hasAccessToSelected = accessibleModules.some(m => m.key === selectedModule)
      if (!hasAccessToSelected) {
        setSelectedModule(accessibleModules[0].key)
      }
    }
  }, [permissionLoading, accessibleModules, selectedModule])

  // 显示加载状态
  if (permissionLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    )
  }

  // 如果没有任何可访问的模块
  if (accessibleModules.length === 0) {
    return (
      <Card title="系统设置">
        <Alert
          message="访问受限"
          description="您当前没有权限访问任何系统设置模块。请联系管理员获取相应权限。"
          type="warning"
          showIcon
        />
      </Card>
    )
  }

  // 生成菜单项
  const generateMenuItems = () => {
    return Object.entries(categoryConfig).map(([categoryKey, categoryInfo]) => {
      const categoryModules = modulesByCategory[categoryKey] || []
      
      return {
        key: `category-${categoryKey}`,
        label: categoryInfo.title,
        icon: categoryInfo.icon,
        type: 'group' as const,
        children: categoryModules.map(module => ({
          key: module.key,
          label: (
            <Space>
              <span>{module.title}</span>
              {module.badge && <Badge count={module.badge} size="small" />}
            </Space>
          ),
          icon: module.icon
        }))
      }
    })
  }

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Sider
        theme="light"
        width={280}
        collapsible
        collapsed={collapsedSider}
        onCollapse={setCollapsedSider}
        style={{
          boxShadow: '2px 0 8px rgba(0,0,0,0.1)',
          zIndex: 1
        }}
      >
        <div style={{ padding: '16px', borderBottom: '1px solid #f0f0f0' }}>
          {!collapsedSider && (
            <Space direction="vertical" size={4}>
              <Title level={4} style={{ margin: 0 }}>
                <SettingOutlined /> 系统设置
              </Title>
              <Text type="secondary" style={{ fontSize: 12 }}>
                配置和管理系统各项功能
              </Text>
            </Space>
          )}
        </div>
        
        <Menu
          mode="inline"
          selectedKeys={[selectedModule]}
          style={{ border: 'none', height: 'calc(100vh - 120px)', overflowY: 'auto' }}
          items={generateMenuItems()}
          onClick={({ key }) => {
            if (!key.startsWith('category-')) {
              setSelectedModule(key)
              // 更新URL参数
              setSearchParams({ module: key })
            }
          }}
        />
      </Sider>

      <Layout style={{ background: '#f0f2f5' }}>
        <Content style={{ padding: '24px', minHeight: '100vh' }}>
          <Card 
            title={
              <Space>
                {currentModule?.icon}
                <span>{currentModule?.title}</span>
                {currentModule?.badge && <Badge count={currentModule.badge} />}
              </Space>
            }
            extra={
              currentModule?.description && (
                <Text type="secondary">{currentModule.description}</Text>
              )
            }
            bodyStyle={{ padding: 0 }}
          >
            <div style={{ padding: '24px' }}>
              <PermissionGuard
                permission={currentModule?.permission}
                fallback={
                  <Alert
                    message="权限不足"
                    description="您没有权限访问此功能模块。"
                    type="error"
                    showIcon
                  />
                }
              >
                <CurrentComponent />
              </PermissionGuard>
            </div>
          </Card>
        </Content>
      </Layout>
    </Layout>
  )
}

export default Settings
