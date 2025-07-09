import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  message,
  Space,
  Tag,
  Popconfirm,
  Drawer,
  Typography,
  Divider,
  Row,
  Col,
  Statistic,
  Switch,
  Tabs,
  InputNumber,
  Collapse
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  SettingOutlined,
  SecurityScanOutlined,
  GlobalOutlined,
  EyeOutlined,
  SaveOutlined,
  LockOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { apiService } from '../../services/api'
import { SystemSetting } from '../../types'

const { TextArea } = Input
const { Text, Title } = Typography
const { TabPane } = Tabs
const { Panel } = Collapse

interface GlobalConfigurationProps {}

const GlobalConfiguration: React.FC<GlobalConfigurationProps> = () => {
  const [settings, setSettings] = useState<SystemSetting[]>([])
  const [loading, setLoading] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [currentSetting, setCurrentSetting] = useState<SystemSetting | null>(null)
  const [form] = Form.useForm()
  const [bulkUpdates, setBulkUpdates] = useState<Record<string, any>>({})
  const [activeTab, setActiveTab] = useState<string>('general')

  // 设置分类
  const categories = [
    { key: 'general', label: '常规设置', icon: <SettingOutlined /> },
    { key: 'security', label: '安全设置', icon: <SecurityScanOutlined /> },
    { key: 'notification', label: '通知设置', icon: <GlobalOutlined /> },
    { key: 'performance', label: '性能设置', icon: <SettingOutlined /> },
    { key: 'integration', label: '集成设置', icon: <GlobalOutlined /> },
    { key: 'backup', label: '备份设置', icon: <SettingOutlined /> },
    { key: 'monitoring', label: '监控设置', icon: <SettingOutlined /> }
  ]

  // 加载数据
  const fetchData = async () => {
    setLoading(true)
    try {
      const response = await apiService.getSystemSettings()
      setSettings(response.results || response)
    } catch (error) {
      message.error('加载数据失败')
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  // 按分类加载数据
  const fetchCategoryData = async (category: string) => {
    setLoading(true)
    try {
      const response = await apiService.getSystemSettingsByCategory(category)
      setSettings(response.results || [])
    } catch (error) {
      message.error('加载数据失败')
      console.error('Failed to fetch category data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCategoryData(activeTab)
  }, [activeTab])

  // 设置操作
  const handleEditSetting = (record: SystemSetting) => {
    setCurrentSetting(record)
    let value: any = record.value
    
    // 根据数据类型转换值
    if (record.data_type === 'boolean') {
      value = record.value === 'true'
    } else if (record.data_type === 'number') {
      value = Number(record.value)
    } else if (record.data_type === 'json') {
      try {
        value = JSON.stringify(JSON.parse(record.value), null, 2)
      } catch {
        value = record.value
      }
    }
    
    form.setFieldsValue({
      ...record,
      value
    })
    setEditModalVisible(true)
  }

  const handleSubmitSetting = async (values: any) => {
    try {
      let processedValue = values.value
      
      // 根据数据类型处理值
      if (currentSetting?.data_type === 'boolean') {
        processedValue = values.value ? 'true' : 'false'
      } else if (currentSetting?.data_type === 'number') {
        processedValue = String(values.value)
      } else if (currentSetting?.data_type === 'json') {
        try {
          JSON.parse(values.value) // 验证JSON格式
          processedValue = values.value
        } catch {
          message.error('JSON格式不正确')
          return
        }
      }

      const data = {
        ...values,
        value: processedValue
      }

      if (currentSetting) {
        await apiService.updateSystemSetting(currentSetting.id, data)
        message.success('更新成功')
      }
      
      setEditModalVisible(false)
      fetchCategoryData(activeTab)
    } catch (error) {
      message.error('更新失败')
      console.error('Failed to save setting:', error)
    }
  }

  // 批量更新
  const handleBulkUpdate = async () => {
    try {
      const updates = Object.entries(bulkUpdates).map(([settingId, value]) => {
        const setting = settings.find(s => s.id.toString() === settingId)
        return {
          id: parseInt(settingId),
          value: String(value)
        }
      }).filter(update => update.id)
      
      if (updates.length === 0) {
        message.warning('没有要更新的设置')
        return
      }

      await apiService.bulkUpdateSystemSettings(updates)
      message.success(`成功更新 ${updates.length} 项设置`)
      setBulkUpdates({})
      fetchCategoryData(activeTab)
    } catch (error) {
      message.error('批量更新失败')
      console.error('Failed to bulk update:', error)
    }
  }

  // 处理快速编辑
  const handleQuickEdit = (key: string, value: any) => {
    setBulkUpdates(prev => ({
      ...prev,
      [key]: value
    }))
  }

  // 渲染设置值编辑器
  const renderValueEditor = (record: SystemSetting) => {
    const hasUpdate = bulkUpdates.hasOwnProperty(record.key)
    const currentValue = hasUpdate ? bulkUpdates[record.key] : record.value

    switch (record.data_type) {
      case 'boolean':
        return (
          <Switch
            checked={currentValue === 'true' || currentValue === true}
            onChange={(checked) => handleQuickEdit(record.key, checked)}
            size="small"
          />
        )
      case 'number':
        return (
          <InputNumber
            value={Number(currentValue)}
            onChange={(value) => handleQuickEdit(record.key, value)}
            size="small"
            style={{ width: '100%' }}
          />
        )
      case 'password':
        return (
          <Input.Password
            value={currentValue}
            onChange={(e) => handleQuickEdit(record.key, e.target.value)}
            size="small"
            placeholder="输入新密码"
          />
        )
      default:
        return (
          <Input
            value={currentValue}
            onChange={(e) => handleQuickEdit(record.key, e.target.value)}
            size="small"
          />
        )
    }
  }

  // 表格列
  const columns: ColumnsType<SystemSetting> = [
    {
      title: '设置键',
      dataIndex: 'key',
      key: 'key',
      width: 200,
      fixed: 'left',
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.description}
          </Text>
        </Space>
      )
    },
    {
      title: '当前值',
      dataIndex: 'value',
      key: 'value',
      width: 200,
      render: (value, record) => {
        if (record.is_encrypted) {
          return <Text>••••••••</Text>
        }
        
        if (record.data_type === 'boolean') {
          return (
            <Tag color={value === 'true' ? 'green' : 'red'}>
              {value === 'true' ? '启用' : '禁用'}
            </Tag>
          )
        }
        
        if (record.data_type === 'json') {
          return (
            <Text code ellipsis style={{ maxWidth: 150 }}>
              {value}
            </Text>
          )
        }
        
        return <Text ellipsis style={{ maxWidth: 150 }}>{value}</Text>
      }
    },
    {
      title: '快速编辑',
      key: 'quick_edit',
      width: 200,
      render: (_, record) => {
        if (!record.is_public && record.is_encrypted) {
          return <Text type="secondary">需要详细编辑</Text>
        }
        return renderValueEditor(record)
      }
    },
    {
      title: '数据类型',
      dataIndex: 'data_type',
      key: 'data_type',
      width: 100,
      render: (type) => <Tag>{type}</Tag>
    },
    {
      title: '状态',
      key: 'status',
      width: 120,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          {record.is_encrypted && (
            <Tag icon={<LockOutlined />} color="orange">加密</Tag>
          )}
          {record.is_public ? (
            <Tag color="green">公开</Tag>
          ) : (
            <Tag color="red">私有</Tag>
          )}
        </Space>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEditSetting(record)}
            size="small"
          >
            编辑
          </Button>
        </Space>
      )
    }
  ]

  // 统计数据
  const stats = {
    totalSettings: settings.length,
    publicSettings: settings.filter(s => s.is_public).length,
    encryptedSettings: settings.filter(s => s.is_encrypted).length,
    pendingUpdates: Object.keys(bulkUpdates).length
  }

  // 按分类分组设置
  const groupedSettings = settings.reduce((acc, setting) => {
    if (!acc[setting.category]) {
      acc[setting.category] = []
    }
    acc[setting.category].push(setting)
    return acc
  }, {} as Record<string, SystemSetting[]>)

  return (
    <div>
      <Title level={4}>全局配置管理</Title>
      
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic 
              title="总设置数" 
              value={stats.totalSettings} 
              prefix={<SettingOutlined />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="公开设置" 
              value={stats.publicSettings} 
              prefix={<GlobalOutlined />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="加密设置" 
              value={stats.encryptedSettings} 
              prefix={<LockOutlined />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="待更新" 
              value={stats.pendingUpdates} 
              prefix={<SaveOutlined />} 
              valueStyle={{ color: stats.pendingUpdates > 0 ? '#cf1322' : undefined }}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="系统设置"
        extra={
          <Space>
            {stats.pendingUpdates > 0 && (
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleBulkUpdate}
              >
                保存更改 ({stats.pendingUpdates})
              </Button>
            )}
            <Button icon={<ReloadOutlined />} onClick={() => fetchCategoryData(activeTab)}>
              刷新
            </Button>
          </Space>
        }
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {categories.map(category => (
            <TabPane
              tab={
                <span>
                  {category.icon}
                  {category.label}
                </span>
              }
              key={category.key}
            >
              <Table
                columns={columns}
                dataSource={settings.filter(s => s.category === category.key)}
                rowKey="id"
                loading={loading}
                scroll={{ x: 1000 }}
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共 ${total} 条记录`
                }}
                rowClassName={(record) => 
                  bulkUpdates.hasOwnProperty(record.key) ? 'table-row-modified' : ''
                }
              />
            </TabPane>
          ))}
        </Tabs>
      </Card>

      {/* 设置编辑模态框 */}
      <Modal
        title="编辑系统设置"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        width={600}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmitSetting}
        >
          <Form.Item
            label="设置键"
            name="key"
          >
            <Input disabled />
          </Form.Item>

          <Form.Item
            label="描述"
            name="description"
          >
            <Input disabled />
          </Form.Item>

          <Form.Item
            label="数据类型"
            name="data_type"
          >
            <Input disabled />
          </Form.Item>

          <Form.Item
            label="默认值"
            name="default_value"
          >
            <Input disabled />
          </Form.Item>

          <Form.Item
            label="当前值"
            name="value"
            rules={[{ required: true, message: '请输入设置值' }]}
          >
            {currentSetting?.data_type === 'boolean' ? (
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            ) : currentSetting?.data_type === 'number' ? (
              <InputNumber style={{ width: '100%' }} />
            ) : currentSetting?.data_type === 'json' ? (
              <TextArea rows={6} placeholder="请输入有效的JSON格式" />
            ) : currentSetting?.data_type === 'password' ? (
              <Input.Password placeholder="请输入密码" />
            ) : (
              <Input placeholder="请输入设置值" />
            )}
          </Form.Item>

          {currentSetting?.validation_rules && Object.keys(currentSetting.validation_rules).length > 0 && (
            <Form.Item label="验证规则">
              <Text code>
                {JSON.stringify(currentSetting.validation_rules, null, 2)}
              </Text>
            </Form.Item>
          )}

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                更新
              </Button>
              <Button onClick={() => setEditModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default GlobalConfiguration
