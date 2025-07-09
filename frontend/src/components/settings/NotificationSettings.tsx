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
  Typography,
  Row,
  Col,
  Statistic,
  Switch,
  Tabs
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  NotificationOutlined,
  MailOutlined,
  MessageOutlined,
  BellOutlined,
  SendOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { apiService } from '../../services/api'
import { NotificationConfig } from '../../types'

const { TextArea } = Input
const { Text, Title } = Typography

interface NotificationSettingsProps {}

const NotificationSettings: React.FC<NotificationSettingsProps> = () => {
  const [configs, setConfigs] = useState<NotificationConfig[]>([])
  const [loading, setLoading] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [currentConfig, setCurrentConfig] = useState<NotificationConfig | null>(null)
  const [form] = Form.useForm()

  // 加载数据
  const fetchData = async () => {
    setLoading(true)
    try {
      const response = await apiService.getNotificationConfigs()
      setConfigs(response.results || response)
    } catch (error) {
      message.error('加载数据失败')
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  // 配置操作
  const handleEdit = (record: NotificationConfig) => {
    setCurrentConfig(record)
    const formData = {
      ...record,
      config: typeof record.config === 'object' ? JSON.stringify(record.config, null, 2) : record.config
    }
    form.setFieldsValue(formData)
    setEditModalVisible(true)
  }

  const handleSubmit = async (values: any) => {
    try {
      if (currentConfig) {
        // 处理 config 字段，如果是字符串需要解析为 JSON
        const configData = { ...values }
        if (typeof configData.config === 'string') {
          try {
            configData.config = JSON.parse(configData.config)
          } catch (error) {
            message.error('配置参数格式错误，请输入有效的 JSON')
            return
          }
        }
        
        await apiService.updateSettingsNotificationConfig(currentConfig.id, configData)
        message.success('更新成功')
      } else {
        // 创建新配置
        const configData = { ...values }
        if (typeof configData.config === 'string') {
          try {
            configData.config = JSON.parse(configData.config)
          } catch (error) {
            message.error('配置参数格式错误，请输入有效的 JSON')
            return
          }
        }
        
        await apiService.createNotificationConfig(configData)
        message.success('创建成功')
      }
      
      setEditModalVisible(false)
      form.resetFields()
      fetchData()
    } catch (error) {
      message.error(currentConfig ? '更新失败' : '创建失败')
      console.error('Failed to save config:', error)
    }
  }

  const handleCreate = () => {
    setCurrentConfig(null)
    form.resetFields()
    setEditModalVisible(true)
  }

  const handleTest = async (record: NotificationConfig) => {
    try {
      // 使用通用的测试通知方法
      await apiService.testNotification({
        type: record.type,
        config: record.config,
        message: '这是一条测试通知消息'
      })
      message.success('测试通知已发送')
    } catch (error) {
      message.error('测试失败')
      console.error('Failed to test config:', error)
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await apiService.deleteNotificationConfig(id)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      message.error('删除失败')
      console.error('Failed to delete config:', error)
    }
  }

  // 表格列
  const columns: ColumnsType<NotificationConfig> = [
    {
      title: '配置名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          {record.type === 'email' && <MailOutlined />}
          {record.type === 'webhook' && <SendOutlined />}
          {record.type === 'dingtalk' && <MessageOutlined />}
          {record.type === 'slack' && <MessageOutlined />}
          <span>{text}</span>
        </Space>
      )
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type) => {
        const colors = {
          'email': 'blue',
          'webhook': 'green',
          'dingtalk': 'orange',
          'slack': 'purple',
          'wechat': 'green'
        }
        return <Tag color={colors[type as keyof typeof colors]}>{type}</Tag>
      }
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled) => (
        <Tag color={enabled ? 'green' : 'red'}>
          {enabled ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '配置详情',
      dataIndex: 'config',
      key: 'config',
      render: (config) => (
        <div>
          {config && Object.keys(config).length > 0 ? (
            <Text type="secondary">{Object.keys(config).length} 项配置</Text>
          ) : (
            <Text type="secondary">无配置</Text>
          )}
        </div>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleDateString()
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<SendOutlined />}
            onClick={() => handleTest(record)}
            size="small"
          >
            测试
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            size="small"
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个配置吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="删除"
            cancelText="取消"
          >
            <Button
              type="link"
              icon={<DeleteOutlined />}
              danger
              size="small"
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  // 统计数据
  const stats = {
    totalConfigs: configs.length,
    enabledConfigs: configs.filter(c => c.enabled).length,
    emailConfigs: configs.filter(c => c.type === 'email').length,
    webhookConfigs: configs.filter(c => c.type === 'webhook').length
  }

  return (
    <div>
      <Title level={4}>通知设置</Title>
      
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic 
              title="总配置数" 
              value={stats.totalConfigs} 
              prefix={<NotificationOutlined />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="启用配置" 
              value={stats.enabledConfigs} 
              prefix={<BellOutlined />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="邮件配置" 
              value={stats.emailConfigs} 
              prefix={<MailOutlined />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="Webhook配置" 
              value={stats.webhookConfigs} 
              prefix={<SendOutlined />} 
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="通知配置列表"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={fetchData}>
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              创建配置
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={configs}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>

      {/* 编辑/创建模态框 */}
      <Modal
        title={currentConfig ? "编辑通知配置" : "创建通知配置"}
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        width={600}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            label="配置名称"
            name="name"
            rules={[{ required: true, message: '请输入配置名称' }]}
          >
            <Input disabled={!!currentConfig} placeholder="输入配置名称" />
          </Form.Item>

          <Form.Item
            label="配置类型"
            name="type"
            rules={[{ required: true, message: '请选择配置类型' }]}
          >
            {currentConfig ? (
              <Input disabled />
            ) : (
              <Select placeholder="选择配置类型">
                <Select.Option value="email">邮件</Select.Option>
                <Select.Option value="webhook">Webhook</Select.Option>
                <Select.Option value="slack">Slack</Select.Option>
                <Select.Option value="dingtalk">钉钉</Select.Option>
                <Select.Option value="wechat">微信</Select.Option>
              </Select>
            )}
          </Form.Item>

          <Form.Item
            label="启用状态"
            name="enabled"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            label="配置参数"
            name="config"
            help="JSON 格式的配置参数"
            rules={[{ required: true, message: '请输入配置参数' }]}
          >
            <TextArea
              rows={6}
              placeholder='{"webhook_url": "https://...", "template": "..."}'
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {currentConfig ? '更新' : '创建'}
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

export default NotificationSettings
