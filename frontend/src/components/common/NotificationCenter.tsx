import React from 'react'
import { List, Tag, Button, Empty, Typography } from 'antd'
import { 
  InfoCircleOutlined, 
  WarningOutlined, 
  CloseCircleOutlined,
  CheckCircleOutlined,
  CloseOutlined 
} from '@ant-design/icons'
import { useAppStore } from '../../stores/app'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

const { Text, Paragraph } = Typography

const NotificationCenter: React.FC = () => {
  const { notifications, removeNotification } = useAppStore()

  const getIcon = (level: string) => {
    switch (level) {
      case 'info':
        return <InfoCircleOutlined style={{ color: '#1890ff' }} />
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14' }} />
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      default:
        return <InfoCircleOutlined />
    }
  }

  const getTagColor = (level: string) => {
    switch (level) {
      case 'info':
        return 'blue'
      case 'warning':
        return 'orange'
      case 'error':
        return 'red'
      case 'success':
        return 'green'
      default:
        return 'default'
    }
  }

  const getLevelText = (level: string) => {
    switch (level) {
      case 'info':
        return '信息'
      case 'warning':
        return '警告'
      case 'error':
        return '错误'
      case 'success':
        return '成功'
      default:
        return '通知'
    }
  }

  if (notifications.length === 0) {
    return (
      <Empty
        description="暂无通知"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    )
  }

  return (
    <div>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 16 
      }}>
        <Text strong>通知列表 ({notifications.length})</Text>
        {notifications.length > 0 && (
          <Button 
            type="link" 
            size="small"
            onClick={() => {
              notifications.forEach(n => removeNotification(n.id))
            }}
          >
            清空所有
          </Button>
        )}
      </div>

      <List
        dataSource={notifications.slice().reverse()}
        renderItem={(notification) => (
          <List.Item
            key={notification.id}
            style={{
              border: '1px solid #f0f0f0',
              borderRadius: 8,
              marginBottom: 8,
              padding: 16,
            }}
            actions={[
              <Button
                type="text"
                icon={<CloseOutlined />}
                size="small"
                onClick={() => removeNotification(notification.id)}
              />
            ]}
          >
            <List.Item.Meta
              avatar={getIcon(notification.level)}
              title={
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 8,
                  marginBottom: 4 
                }}>
                  <Text strong>{notification.title}</Text>
                  <Tag color={getTagColor(notification.level)} size="small">
                    {getLevelText(notification.level)}
                  </Tag>
                </div>
              }
              description={
                <div>
                  <Paragraph 
                    style={{ marginBottom: 8, color: '#666' }}
                    ellipsis={{ rows: 2, expandable: true, symbol: '展开' }}
                  >
                    {notification.message}
                  </Paragraph>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {formatDistanceToNow(new Date(notification.timestamp), {
                      addSuffix: true,
                      locale: zhCN
                    })}
                  </Text>
                </div>
              }
            />
          </List.Item>
        )}
      />
    </div>
  )
}

export default NotificationCenter
