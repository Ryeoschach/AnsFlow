import React, { useState, useEffect } from 'react'
import { 
  Card, Button, Space, Table, message, Modal, Form, 
  Input, Select, Switch, Tag, Tooltip, Typography, Alert 
} from 'antd'
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, 
  ExperimentOutlined, KeyOutlined, SafetyOutlined 
} from '@ant-design/icons'
import { GitCredential } from '../../types'
import apiService from '../../services/api'

const { Text } = Typography
const { TextArea } = Input

const PLATFORMS = [
  { value: 'gitlab', label: 'GitLab', icon: '🦊' },
  { value: 'github', label: 'GitHub', icon: '🐙' },
  { value: 'gitee', label: 'Gitee', icon: '🎯' },
  { value: 'bitbucket', label: 'Bitbucket', icon: '🪣' },
  { value: 'azure_devops', label: 'Azure DevOps', icon: '☁️' },
  { value: 'other', label: '其他Git服务', icon: '⚙️' },
]

const CREDENTIAL_TYPES = [
  { value: 'username_password', label: '用户名密码', description: '使用用户名和密码认证' },
  { value: 'access_token', label: '访问令牌', description: '使用Personal Access Token' },
  { value: 'ssh_key', label: 'SSH密钥', description: '使用SSH公私钥对认证' },
  { value: 'oauth', label: 'OAuth认证', description: '使用OAuth访问令牌' },
]

const GitCredentialManager: React.FC = () => {
  const [credentials, setCredentials] = useState<GitCredential[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingCredential, setEditingCredential] = useState<GitCredential | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchCredentials()
  }, [])

  const fetchCredentials = async () => {
    try {
      setLoading(true)
      const data = await apiService.getGitCredentials()
      setCredentials(data)
    } catch (error) {
      console.error('Failed to fetch git credentials:', error)
      message.error('获取Git凭据列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingCredential(null)
    setModalVisible(true)
    form.resetFields()
    form.setFieldsValue({
      is_active: true,
      platform: 'gitlab',
      credential_type: 'username_password'
    })
  }

  const handleEdit = (record: GitCredential) => {
    setEditingCredential(record)
    setModalVisible(true)
    form.setFieldsValue({
      name: record.name,
      platform: record.platform,
      credential_type: record.credential_type,
      server_url: record.server_url,
      username: record.username,
      description: record.description,
      is_active: record.is_active
    })
  }

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个Git凭据吗？此操作不可恢复。',
      onOk: async () => {
        try {
          await apiService.deleteGitCredential(id)
          message.success('Git凭据删除成功')
          fetchCredentials()
        } catch (error) {
          console.error('Failed to delete git credential:', error)
          message.error('删除Git凭据失败')
        }
      }
    })
  }

  const handleSubmit = async (values: any) => {
    try {
      setLoading(true)
      if (editingCredential) {
        await apiService.updateGitCredential(editingCredential.id, values)
        message.success('Git凭据更新成功')
      } else {
        await apiService.createGitCredential(values)
        message.success('Git凭据创建成功')
      }
      setModalVisible(false)
      fetchCredentials()
    } catch (error) {
      console.error('Failed to save git credential:', error)
      message.error('保存Git凭据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleTestConnection = async (id: number) => {
    try {
      setLoading(true)
      const result = await apiService.testGitCredential(id)
      
      if (result.success) {
        message.success('连接测试成功')
      } else {
        message.error(`连接测试失败: ${result.message}`)
      }
      
      fetchCredentials() // 刷新列表以显示最新测试结果
    } catch (error) {
      message.error('测试连接时发生错误')
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: GitCredential) => (
        <Space>
          <KeyOutlined />
          <Text strong>{text}</Text>
          {!record.is_active && <Tag color="red">停用</Tag>}
        </Space>
      ),
    },
    {
      title: 'Git平台',
      dataIndex: 'platform',
      key: 'platform',
      render: (platform: string) => {
        const platformInfo = PLATFORMS.find(p => p.value === platform)
        return (
          <Space>
            <span>{platformInfo?.icon}</span>
            <span>{platformInfo?.label}</span>
          </Space>
        )
      },
    },
    {
      title: '认证类型',
      dataIndex: 'credential_type_display',
      key: 'credential_type',
      render: (type: string) => <Tag color="blue">{type}</Tag>,
    },
    {
      title: '服务器地址',
      dataIndex: 'server_url',
      key: 'server_url',
      render: (url: string) => <Text code>{url}</Text>,
    },
    {
      title: '连接状态',
      key: 'test_result',
      render: (record: GitCredential) => {
        if (record.last_test_result === null || record.last_test_result === undefined) {
          return <Tag color="default">未测试</Tag>
        }
        return record.last_test_result ? 
          <Tag color="green">连接正常</Tag> : 
          <Tag color="red">连接失败</Tag>
      },
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: GitCredential) => (
        <Space>
          <Tooltip title="测试连接">
            <Button 
              icon={<ExperimentOutlined />} 
              size="small"
              onClick={() => handleTestConnection(record.id)}
              loading={loading}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button 
              icon={<EditOutlined />} 
              size="small"
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button 
              icon={<DeleteOutlined />} 
              size="small" 
              danger
              onClick={() => handleDelete(record.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  return (
    <Card 
      title={
        <Space>
          <SafetyOutlined />
          <span>Git认证凭据管理</span>
        </Space>
      }
      extra={
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={handleAdd}
        >
          添加凭据
        </Button>
      }
    >
      <Table 
        columns={columns}
        dataSource={credentials}
        rowKey="id"
        loading={loading}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`
        }}
      />

      {/* 添加/编辑凭据的模态框 */}
      <Modal
        title={editingCredential ? '编辑Git凭据' : '添加Git凭据'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
        destroyOnClose
      >
        <Form 
          form={form} 
          layout="vertical" 
          onFinish={handleSubmit}
          initialValues={{
            is_active: true,
            platform: 'gitlab',
            credential_type: 'username_password'
          }}
        >
          <Form.Item
            name="name"
            label="凭据名称"
            rules={[{ required: true, message: '请输入凭据名称' }]}
          >
            <Input placeholder="如: 公司GitLab主账号" />
          </Form.Item>

          <Form.Item
            name="platform"
            label="Git平台"
            rules={[{ required: true, message: '请选择Git平台' }]}
          >
            <Select placeholder="选择Git平台">
              {PLATFORMS.map(platform => (
                <Select.Option key={platform.value} value={platform.value}>
                  <Space>
                    <span>{platform.icon}</span>
                    <span>{platform.label}</span>
                  </Space>
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="server_url"
            label="服务器地址"
            rules={[
              { required: true, message: '请输入服务器地址' },
              { type: 'url', message: '请输入有效的URL地址' }
            ]}
          >
            <Input placeholder="https://gitlab.company.com" />
          </Form.Item>

          <Form.Item
            name="credential_type"
            label="认证类型"
            rules={[{ required: true, message: '请选择认证类型' }]}
          >
            <Select 
              placeholder="选择认证类型"
              optionLabelProp="label"
            >
              {CREDENTIAL_TYPES.map(type => (
                <Select.Option 
                  key={type.value} 
                  value={type.value}
                  label={type.label}
                >
                  <div>
                    <div style={{ fontWeight: 500 }}>{type.label}</div>
                    <div style={{ fontSize: 12, color: '#999' }}>
                      {type.description}
                    </div>
                  </div>
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          {/* 根据认证类型显示不同的表单字段 */}
          <Form.Item noStyle shouldUpdate>
            {({ getFieldValue }) => {
              const credentialType = getFieldValue('credential_type')
              
              if (credentialType === 'username_password' || credentialType === 'personal_token') {
                return (
                  <>
                    <Form.Item
                      name="username"
                      label={credentialType === 'personal_token' ? '用户名(可选)' : '用户名'}
                      rules={credentialType === 'username_password' ? 
                        [{ required: true, message: '请输入用户名' }] : []
                      }
                    >
                      <Input placeholder="输入用户名" />
                    </Form.Item>
                    
                    <Form.Item
                      name="password"
                      label={credentialType === 'personal_token' ? '访问令牌' : '密码'}
                      rules={editingCredential && (editingCredential.has_password || editingCredential.has_credentials) ? 
                        [] : // 编辑时如果已有密码，则不强制要求
                        [{ required: true, message: '请输入密码或令牌' }]
                      }
                      extra={editingCredential && (editingCredential.has_password || editingCredential.has_credentials) ? 
                        <span style={{ color: '#666' }}>
                          🔒 当前已设置密码，留空则保持不变
                        </span> : null
                      }
                    >
                      <Input.Password 
                        placeholder={editingCredential && (editingCredential.has_password || editingCredential.has_credentials) ? 
                          "留空保持原密码不变" : 
                          "输入密码或访问令牌"
                        } 
                      />
                    </Form.Item>
                  </>
                )
              }
              
              if (credentialType === 'ssh_key') {
                return (
                  <>
                    <Form.Item
                      name="ssh_private_key"
                      label="SSH私钥"
                      rules={editingCredential && (editingCredential.has_ssh_key || editingCredential.has_credentials) ? 
                        [] : // 编辑时如果已有SSH密钥，则不强制要求
                        [{ required: true, message: '请输入SSH私钥' }]
                      }
                      extra={editingCredential && (editingCredential.has_ssh_key || editingCredential.has_credentials) ? 
                        <span style={{ color: '#666' }}>
                          🔒 当前已设置SSH私钥，留空则保持不变
                        </span> : null
                      }
                    >
                      <TextArea 
                        rows={8}
                        placeholder={editingCredential && (editingCredential.has_ssh_key || editingCredential.has_credentials) ? 
                          "留空保持原SSH私钥不变" : 
                          "-----BEGIN OPENSSH PRIVATE KEY-----\n...\n-----END OPENSSH PRIVATE KEY-----"
                        }
                      />
                    </Form.Item>
                    
                    <Form.Item
                      name="ssh_public_key"
                      label="SSH公钥(可选)"
                    >
                      <TextArea 
                        rows={3}
                        placeholder="ssh-rsa AAAAB3NzaC1yc2EAAAADA... user@host"
                      />
                    </Form.Item>
                  </>
                )
              }
              
              return null
            }}
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea 
              placeholder="描述这个凭据的用途，如：用于拉取公司内部GitLab代码"
              rows={3}
            />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="启用状态"
            valuePropName="checked"
          >
            <Switch checkedChildren="启用" unCheckedChildren="停用" />
          </Form.Item>

          <Alert
            message="安全提示"
            description="所有敏感信息（密码、令牌、SSH私钥）都会在后端进行加密存储，确保数据安全。"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={loading}>
                {editingCredential ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

export default GitCredentialManager
