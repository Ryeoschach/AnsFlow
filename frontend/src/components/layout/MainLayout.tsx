import React, { useEffect } from 'react'
import { Layout, Menu, Avatar, Dropdown, Button, Badge, Drawer } from 'antd'
import { 
  DashboardOutlined, 
  AppstoreOutlined, 
  ToolOutlined, 
  PlayCircleOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  FolderOutlined,
  BarChartOutlined,
  ApiOutlined,
  ContainerOutlined
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth'
import { useAppStore } from '../../stores/app'
import wsService from '../../services/websocket'
import NotificationCenter from '../common/NotificationCenter'

const { Header, Sider, Content } = Layout

interface MainLayoutProps {
  children: React.ReactNode
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const { notifications, addNotification } = useAppStore()
  const [collapsed, setCollapsed] = React.useState(false)
  const [notificationVisible, setNotificationVisible] = React.useState(false)

  useEffect(() => {
    // Connect to WebSocket
    wsService.connect()

    // Subscribe to system notifications
    const unsubscribeNotifications = wsService.onSystemNotification((notification) => {
      addNotification(notification)
    })

    return () => {
      unsubscribeNotifications()
      wsService.disconnect()
    }
  }, [addNotification])

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/analytics',
      icon: <BarChartOutlined />,
      label: '数据分析',
    },
    {
      key: '/projects',
      icon: <FolderOutlined />,
      label: '项目管理',
    },
    {
      key: '/pipelines',
      icon: <AppstoreOutlined />,
      label: '流水线',
    },
    {
      key: '/tools',
      icon: <ToolOutlined />,
      label: 'CI/CD工具',
    },
    {
      key: '/executions',
      icon: <PlayCircleOutlined />,
      label: '执行记录',
    },
    {
      key: '/ansible',
      icon: <ApiOutlined />,
      label: 'Ansible',
    },
    {
      key: '/docker',
      icon: <ContainerOutlined />,
      label: 'Docker',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
  ]

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: logout,
    },
  ]

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  const unreadNotifications = notifications.filter(n => 
    ['warning', 'error'].includes(n.level)
  ).length

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider 
        trigger={null} 
        collapsible 
        collapsed={collapsed}
        style={{
          background: '#fff',
          borderRight: '1px solid #f0f0f0',
        }}
      >
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          borderBottom: '1px solid #f0f0f0',
          fontSize: collapsed ? 14 : 18,
          fontWeight: 'bold',
          color: '#1890ff'
        }}>
          {collapsed ? 'AF' : 'AnsFlow'}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
        />
      </Sider>
      
      <Layout>
        <Header style={{ 
          background: '#fff', 
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid #f0f0f0'
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: 16 }}
          />
          
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <Badge count={unreadNotifications} size="small">
              <Button
                type="text"
                icon={<BellOutlined />}
                onClick={() => setNotificationVisible(true)}
              />
            </Badge>
            
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
            >
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                cursor: 'pointer',
                gap: 8
              }}>
                <Avatar icon={<UserOutlined />} />
                <span>{user?.username}</span>
              </div>
            </Dropdown>
          </div>
        </Header>
        
        <Content style={{ 
          margin: 24, 
          padding: 24, 
          background: '#fff',
          borderRadius: 8,
          overflow: 'auto'
        }}>
          {children}
        </Content>
      </Layout>

      <Drawer
        title="通知中心"
        placement="right"
        onClose={() => setNotificationVisible(false)}
        open={notificationVisible}
        width={400}
      >
        <NotificationCenter />
      </Drawer>
    </Layout>
  )
}

export default MainLayout
