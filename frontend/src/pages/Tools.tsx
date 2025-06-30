import React, { useEffect, useState } from 'react'
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Tag, 
  Modal, 
  Form, 
  Input, 
  Select,
  message,
  Tooltip,
  Tabs
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  ApiOutlined
} from '@ant-design/icons'
import { ColumnsType } from 'antd/es/table'
import { Tool } from '../types'
import { useAppStore } from '../stores/app'
import apiService from '../services/api'
import JenkinsJobList from '../components/jenkins/JenkinsJobList'

const { Option } = Select
const { TabPane } = Tabs

const Tools: React.FC = () => {
  const { tools, toolsLoading, loadTools, selectedTool, selectTool } = useAppStore()
  const [formVisible, setFormVisible] = useState(false)
  const [editingTool, setEditingTool] = useState<Tool | null>(null)
  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('list')
  const [projects, setProjects] = useState<any[]>([])

  useEffect(() => {
    loadTools()
    loadProjects()
  }, [loadTools])

  const loadProjects = async () => {
    try {
      const projectList = await apiService.getProjects()
      setProjects(projectList)
    } catch (error) {
      console.error('Failed to load projects:', error)
      message.error('加载项目列表失败')
    }
  }

  const handleAddTool = () => {
    setEditingTool(null)
    form.resetFields()
    setFormVisible(true)
  }

  const handleEditTool = (tool: Tool) => {
    setEditingTool(tool)
    form.setFieldsValue(tool)
    setFormVisible(true)
  }

  const handleDeleteTool = (tool: Tool) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除工具 "${tool.name}" 吗？`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await apiService.deleteTool(tool.id!)
          message.success('工具删除成功')
          loadTools()
          if (selectedTool?.id === tool.id) {
            selectTool(null)
          }
        } catch (error) {
          console.error('Failed to delete tool:', error)
          message.error('删除工具失败')
        }
      }
    })
  }

  const handleTestConnection = async (tool: Tool) => {
    try {
      const result = await apiService.testToolConnection(tool.id!)
      
      // 根据详细状态显示不同的消息
      switch (result.detailed_status) {
        case 'authenticated':
          message.success(`连接测试成功: ${result.message}`)
          break
        case 'needs_auth':
          message.warning(`连接测试: ${result.message}`)
          break
        case 'offline':
          message.error(`连接测试失败: ${result.message}`)
          break
        default:
          message.info(`连接测试: ${result.message}`)
      }
      
      // 重新加载工具列表以更新状态
      loadTools()
    } catch (error) {
      console.error('Connection test failed:', error)
      message.error('连接测试失败')
    }
  }

  const handleFormSubmit = async () => {
    try {
      const values = await form.validateFields()
      console.log('Form values:', values)
      
      // 映射字段名
      const toolData = {
        ...values,
        token: values.password // 将 password 字段映射为 token
      }
      delete toolData.password // 删除原 password 字段
      
      console.log('Tool data to be sent:', toolData)
      
      if (editingTool) {
        await apiService.updateTool(editingTool.id!, toolData)
        message.success('工具更新成功')
      } else {
        await apiService.createTool(toolData)
        message.success('工具创建成功')
      }
      
      setFormVisible(false)
      loadTools()
    } catch (error) {
      console.error('Failed to save tool:', error)
      message.error(editingTool ? '更新工具失败' : '创建工具失败')
    }
  }

  const getStatusTag = (tool: Tool) => {
    // 优先使用详细状态，如果没有则使用基本状态
    const status = tool.detailed_status || tool.status;
    
    switch (status) {
      case 'authenticated':
        return <Tag color="green" icon={<CheckCircleOutlined />}>在线已认证</Tag>
      case 'needs_auth':
        return <Tag color="orange" icon={<ApiOutlined />}>在线需认证</Tag>
      case 'offline':
        return <Tag color="red" icon={<CloseCircleOutlined />}>离线</Tag>
      case 'active':
        return <Tag color="green" icon={<CheckCircleOutlined />}>活跃</Tag>
      case 'error':
        return <Tag color="red" icon={<CloseCircleOutlined />}>错误</Tag>
      default:
        return <Tag color="gray">未知</Tag>
    }
  }

  const getTypeTag = (type: string) => {
    const colors = {
      jenkins: 'blue',
      gitlab: 'orange',
      github: 'purple',
      azure: 'cyan'
    }
    return <Tag color={colors[type as keyof typeof colors] || 'default'}>{type.toUpperCase()}</Tag>
  }

  const columns: ColumnsType<Tool> = [
    {
      title: '工具名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Tool) => (
        <Button 
          type="link" 
          onClick={() => {
            selectTool(record)
            setActiveTab('jenkins')
          }}
        >
          {name}
        </Button>
      ),
    },
    {
      title: '类型',
      dataIndex: 'tool_type',
      key: 'tool_type',
      render: (type: string) => getTypeTag(type),
    },
    {
      title: '服务器地址',
      dataIndex: 'base_url',
      key: 'base_url',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (_, record: Tool) => getStatusTag(record),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: Tool) => (
        <Space>
          <Tooltip title="测试连接">
            <Button
              icon={<ApiOutlined />}
              size="small"
              onClick={() => handleTestConnection(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              icon={<EditOutlined />}
              size="small"
              onClick={() => handleEditTool(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              danger
              icon={<DeleteOutlined />}
              size="small"
              onClick={() => handleDeleteTool(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        items={[
          {
            key: 'list',
            label: 'CI/CD工具列表',
            children: (
              <Card
                title="CI/CD工具管理"
                extra={
                  <Space>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={handleAddTool}
                    >
                      添加工具
                    </Button>
                    <Button
                      icon={<ReloadOutlined />}
                      onClick={loadTools}
                      loading={toolsLoading}
                    >
                      刷新
                    </Button>
                  </Space>
                }
              >
                <Table
                  columns={columns}
                  dataSource={tools}
                  loading={toolsLoading}
                  rowKey="id"
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) => 
                      `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
                  }}
                />
              </Card>
            )
          },
          ...(selectedTool && selectedTool.tool_type === 'jenkins' ? [{
            key: 'jenkins',
            label: `Jenkins - ${selectedTool.name}`,
            children: <JenkinsJobList tool={selectedTool} />
          }] : [])
        ]}
      />

      <Modal
        title={editingTool ? '编辑工具' : '添加工具'}
        open={formVisible}
        onCancel={() => setFormVisible(false)}
        onOk={handleFormSubmit}
        okText={editingTool ? '更新' : '创建'}
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="project"
            label="所属项目"
            rules={[{ required: true, message: '请选择项目' }]}
          >
            <Select placeholder="选择项目">
              {projects.map(project => (
                <Option key={project.id} value={project.id}>
                  {project.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="name"
            label="工具名称"
            rules={[{ required: true, message: '请输入工具名称' }]}
          >
            <Input placeholder="输入工具名称" />
          </Form.Item>

          <Form.Item
            name="tool_type"
            label="工具类型"
            rules={[{ required: true, message: '请选择工具类型' }]}
          >
            <Select placeholder="选择工具类型">
              <Option value="jenkins">Jenkins</Option>
              <Option value="gitlab">GitLab CI</Option>
              <Option value="github">GitHub Actions</Option>
              <Option value="azure">Azure DevOps</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="base_url"
            label="服务器地址"
            rules={[
              { required: true, message: '请输入服务器地址' },
              { type: 'url', message: '请输入有效的URL地址' }
            ]}
          >
            <Input placeholder="https://jenkins.example.com" />
          </Form.Item>

          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="输入用户名" />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码/Token"
            rules={[{ required: true, message: '请输入密码或访问令牌' }]}
          >
            <Input.Password placeholder="输入密码或访问令牌" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea 
              placeholder="输入工具描述（可选）" 
              rows={3} 
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Tools
