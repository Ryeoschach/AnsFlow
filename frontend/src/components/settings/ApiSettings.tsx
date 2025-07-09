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
  DatePicker,
  InputNumber,
  Switch,
  Tabs,
  Row,
  Col,
  Statistic,
  Progress
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  KeyOutlined,
  ApiOutlined,
  EyeOutlined,
  CopyOutlined,
  StopOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { apiService } from '../../services/api'
import { APIKey, APIEndpoint } from '../../types'

const { TextArea } = Input
const { Text, Title } = Typography
const { TabPane } = Tabs

interface ApiSettingsProps {}

const ApiSettings: React.FC<ApiSettingsProps> = () => {
  const [apiKeys, setApiKeys] = useState<APIKey[]>([])
  const [apiEndpoints, setApiEndpoints] = useState<APIEndpoint[]>([])
  const [loading, setLoading] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [endpointModalVisible, setEndpointModalVisible] = useState(false)
  const [currentApiKey, setCurrentApiKey] = useState<APIKey | null>(null)
  const [currentEndpoint, setCurrentEndpoint] = useState<APIEndpoint | null>(null)
  const [form] = Form.useForm()
  const [endpointForm] = Form.useForm()
  const [keyDetailVisible, setKeyDetailVisible] = useState(false)

  // 加载数据
  const fetchData = async () => {
    setLoading(true)
    try {
      const [keysResponse, endpointsResponse] = await Promise.all([
        apiService.getAPIKeys(),
        apiService.getAPIEndpoints()
      ])
      setApiKeys(keysResponse.results || keysResponse)
      setApiEndpoints(endpointsResponse.results || endpointsResponse)
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

  // API密钥操作
  const handleAddApiKey = () => {
    setCurrentApiKey(null)
    form.resetFields()
    setEditModalVisible(true)
  }

  const handleEditApiKey = (record: APIKey) => {
    setCurrentApiKey(record)
    form.setFieldsValue({
      ...record,
      expires_at: record.expires_at ? new Date(record.expires_at) : null,
      permissions: Array.isArray(record.permissions) ? record.permissions.join(', ') : ''
    })
    setEditModalVisible(true)
  }

  const handleDeleteApiKey = async (id: number) => {
    try {
      await apiService.deleteAPIKey(id)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      message.error('删除失败')
      console.error('Failed to delete api key:', error)
    }
  }

  const handleRegenerateKey = async (record: APIKey) => {
    try {
      await apiService.regenerateAPIKey(record.id)
      message.success('API密钥已重新生成')
      fetchData()
    } catch (error) {
      message.error('重新生成失败')
      console.error('Failed to regenerate key:', error)
    }
  }

  const handleRevokeKey = async (record: APIKey) => {
    try {
      await apiService.revokeAPIKey(record.id)
      message.success('API密钥已撤销')
      fetchData()
    } catch (error) {
      message.error('撤销失败')
      console.error('Failed to revoke key:', error)
    }
  }

  const handleSubmitApiKey = async (values: any) => {
    try {
      const data = {
        ...values,
        expires_at: values.expires_at ? values.expires_at.toISOString() : null,
        permissions: values.permissions ? values.permissions.split(',').map((p: string) => p.trim()) : []
      }

      if (currentApiKey) {
        await apiService.updateAPIKey(currentApiKey.id, data)
        message.success('更新成功')
      } else {
        await apiService.createAPIKey(data)
        message.success('创建成功')
      }
      
      setEditModalVisible(false)
      fetchData()
    } catch (error) {
      message.error(currentApiKey ? '更新失败' : '创建失败')
      console.error('Failed to save api key:', error)
    }
  }

  // API端点操作
  const handleAddEndpoint = () => {
    setCurrentEndpoint(null)
    endpointForm.resetFields()
    setEndpointModalVisible(true)
  }

  const handleEditEndpoint = (record: APIEndpoint) => {
    setCurrentEndpoint(record)
    endpointForm.setFieldsValue(record)
    setEndpointModalVisible(true)
  }

  const handleDeleteEndpoint = async (id: number) => {
    try {
      await apiService.deleteAPIEndpoint(id)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      message.error('删除失败')
      console.error('Failed to delete endpoint:', error)
    }
  }

  const handleSubmitEndpoint = async (values: any) => {
    try {
      if (currentEndpoint) {
        await apiService.updateAPIEndpoint(currentEndpoint.id, values)
        message.success('更新成功')
      } else {
        await apiService.createAPIEndpoint(values)
        message.success('创建成功')
      }
      
      setEndpointModalVisible(false)
      fetchData()
    } catch (error) {
      message.error(currentEndpoint ? '更新失败' : '创建失败')
      console.error('Failed to save endpoint:', error)
    }
  }

  // 复制密钥
  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key)
    message.success('已复制到剪贴板')
  }

  // API密钥表格列
  const apiKeyColumns: ColumnsType<APIKey> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <KeyOutlined />
          <span>{text}</span>
        </Space>
      )
    },
    {
      title: '密钥',
      dataIndex: 'key',
      key: 'key',
      render: (text) => (
        <Space>
          <Text code copyable={{ text }}>{text.substring(0, 20)}...</Text>
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const colors = {
          'active': 'green',
          'inactive': 'red',
          'expired': 'orange'
        }
        return <Tag color={colors[status as keyof typeof colors]}>{status}</Tag>
      }
    },
    {
      title: '使用次数',
      dataIndex: 'usage_count',
      key: 'usage_count'
    },
    {
      title: '过期时间',
      dataIndex: 'expires_at',
      key: 'expires_at',
      render: (date) => date ? new Date(date).toLocaleDateString() : '永不过期'
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
            icon={<EyeOutlined />}
            onClick={() => {
              setCurrentApiKey(record)
              setKeyDetailVisible(true)
            }}
          >
            详情
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEditApiKey(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            icon={<ReloadOutlined />}
            onClick={() => handleRegenerateKey(record)}
          >
            重新生成
          </Button>
          <Popconfirm
            title="确定要撤销这个API密钥吗？"
            onConfirm={() => handleRevokeKey(record)}
          >
            <Button
              type="link"
              icon={<StopOutlined />}
              danger
            >
              撤销
            </Button>
          </Popconfirm>
          <Popconfirm
            title="确定要删除这个API密钥吗？"
            onConfirm={() => handleDeleteApiKey(record.id)}
          >
            <Button
              type="link"
              icon={<DeleteOutlined />}
              danger
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  // API端点表格列
  const endpointColumns: ColumnsType<APIEndpoint> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name'
    },
    {
      title: '路径',
      dataIndex: 'path',
      key: 'path',
      render: (path) => <Text code>{path}</Text>
    },
    {
      title: '方法',
      dataIndex: 'method',
      key: 'method',
      render: (method) => <Tag color="blue">{method}</Tag>
    },
    {
      title: '状态',
      dataIndex: 'is_enabled',
      key: 'is_enabled',
      render: (enabled) => (
        <Tag color={enabled ? 'green' : 'red'}>
          {enabled ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '需要认证',
      dataIndex: 'auth_required',
      key: 'auth_required',
      render: (required) => required ? '是' : '否'
    },
    {
      title: '限流(次/分钟)',
      dataIndex: 'rate_limit',
      key: 'rate_limit'
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEditEndpoint(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个端点吗？"
            onConfirm={() => handleDeleteEndpoint(record.id)}
          >
            <Button
              type="link"
              icon={<DeleteOutlined />}
              danger
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
    totalKeys: apiKeys.length,
    activeKeys: apiKeys.filter(k => k.status === 'active').length,
    totalEndpoints: apiEndpoints.length,
    enabledEndpoints: apiEndpoints.filter(e => e.is_enabled).length
  }

  return (
    <div>
      <Title level={4}>API 设置管理</Title>
      
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="API密钥总数" value={stats.totalKeys} prefix={<KeyOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="活跃密钥" value={stats.activeKeys} prefix={<KeyOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="API端点总数" value={stats.totalEndpoints} prefix={<ApiOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="启用端点" value={stats.enabledEndpoints} prefix={<ApiOutlined />} />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="api-keys">
        <TabPane tab="API密钥管理" key="api-keys">
          <Card
            title="API密钥列表"
            extra={
              <Space>
                <Button icon={<ReloadOutlined />} onClick={fetchData}>
                  刷新
                </Button>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleAddApiKey}
                >
                  新增密钥
                </Button>
              </Space>
            }
          >
            <Table
              columns={apiKeyColumns}
              dataSource={apiKeys}
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
        </TabPane>

        <TabPane tab="API端点管理" key="api-endpoints">
          <Card
            title="API端点列表"
            extra={
              <Space>
                <Button icon={<ReloadOutlined />} onClick={fetchData}>
                  刷新
                </Button>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleAddEndpoint}
                >
                  新增端点
                </Button>
              </Space>
            }
          >
            <Table
              columns={endpointColumns}
              dataSource={apiEndpoints}
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
        </TabPane>
      </Tabs>

      {/* API密钥编辑模态框 */}
      <Modal
        title={currentApiKey ? '编辑API密钥' : '新增API密钥'}
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        width={600}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmitApiKey}
        >
          <Form.Item
            label="密钥名称"
            name="name"
            rules={[{ required: true, message: '请输入密钥名称' }]}
          >
            <Input placeholder="请输入密钥名称" />
          </Form.Item>

          <Form.Item
            label="权限列表"
            name="permissions"
            help="请输入权限标识，用逗号分隔"
          >
            <TextArea
              rows={3}
              placeholder="例如：read,write,admin"
            />
          </Form.Item>

          <Form.Item
            label="速率限制"
            name="rate_limit"
            help="每小时允许的请求次数"
          >
            <InputNumber
              min={1}
              max={10000}
              defaultValue={1000}
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item
            label="过期时间"
            name="expires_at"
            help="不设置则永不过期"
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {currentApiKey ? '更新' : '创建'}
              </Button>
              <Button onClick={() => setEditModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* API端点编辑模态框 */}
      <Modal
        title={currentEndpoint ? '编辑API端点' : '新增API端点'}
        open={endpointModalVisible}
        onCancel={() => setEndpointModalVisible(false)}
        width={600}
        footer={null}
      >
        <Form
          form={endpointForm}
          layout="vertical"
          onFinish={handleSubmitEndpoint}
        >
          <Form.Item
            label="端点名称"
            name="name"
            rules={[{ required: true, message: '请输入端点名称' }]}
          >
            <Input placeholder="请输入端点名称" />
          </Form.Item>

          <Form.Item
            label="API路径"
            name="path"
            rules={[{ required: true, message: '请输入API路径' }]}
          >
            <Input placeholder="例如：/api/v1/users" />
          </Form.Item>

          <Form.Item
            label="HTTP方法"
            name="method"
            rules={[{ required: true, message: '请选择HTTP方法' }]}
          >
            <Select placeholder="请选择HTTP方法">
              <Select.Option value="GET">GET</Select.Option>
              <Select.Option value="POST">POST</Select.Option>
              <Select.Option value="PUT">PUT</Select.Option>
              <Select.Option value="DELETE">DELETE</Select.Option>
              <Select.Option value="PATCH">PATCH</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="描述"
            name="description"
          >
            <TextArea rows={3} placeholder="请输入端点描述" />
          </Form.Item>

          <Form.Item
            label="启用状态"
            name="is_enabled"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            label="需要认证"
            name="auth_required"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            label="速率限制"
            name="rate_limit"
            help="每分钟允许的请求次数"
          >
            <InputNumber
              min={1}
              max={1000}
              defaultValue={100}
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {currentEndpoint ? '更新' : '创建'}
              </Button>
              <Button onClick={() => setEndpointModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* API密钥详情抽屉 */}
      <Drawer
        title="API密钥详情"
        open={keyDetailVisible}
        onClose={() => setKeyDetailVisible(false)}
        width={500}
      >
        {currentApiKey && (
          <div>
            <Row gutter={16}>
              <Col span={24}>
                <Card size="small" title="基本信息">
                  <p><strong>名称：</strong>{currentApiKey.name}</p>
                  <p><strong>状态：</strong>
                    <Tag color={currentApiKey.status === 'active' ? 'green' : 'red'}>
                      {currentApiKey.status}
                    </Tag>
                  </p>
                  <p><strong>使用次数：</strong>{currentApiKey.usage_count}</p>
                  <p><strong>创建时间：</strong>{new Date(currentApiKey.created_at).toLocaleString()}</p>
                  <p><strong>最后使用：</strong>
                    {currentApiKey.last_used_at ? new Date(currentApiKey.last_used_at).toLocaleString() : '从未使用'}
                  </p>
                </Card>
              </Col>
            </Row>
            
            <Divider />
            
            <Row gutter={16}>
              <Col span={24}>
                <Card size="small" title="密钥信息">
                  <p><strong>API Key：</strong></p>
                  <Text code copyable={{ text: currentApiKey.key }}>
                    {currentApiKey.key}
                  </Text>
                </Card>
              </Col>
            </Row>

            <Divider />

            <Row gutter={16}>
              <Col span={24}>
                <Card size="small" title="权限信息">
                  <p><strong>权限列表：</strong></p>
                  {currentApiKey.permissions && currentApiKey.permissions.length > 0 ? (
                    <div>
                      {currentApiKey.permissions.map((permission: string, index: number) => (
                        <Tag key={index} color="blue">{permission}</Tag>
                      ))}
                    </div>
                  ) : (
                    <Text type="secondary">暂无权限</Text>
                  )}
                </Card>
              </Col>
            </Row>
          </div>
        )}
      </Drawer>
    </div>
  )
}

export default ApiSettings
