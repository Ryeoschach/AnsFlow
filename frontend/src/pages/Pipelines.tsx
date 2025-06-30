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
  Popconfirm,
  Drawer,
  Row,
  Col,
  Statistic
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  EyeOutlined,
  CopyOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  AppstoreOutlined,
  DeploymentUnitOutlined,
  PoweroffOutlined
} from '@ant-design/icons'
import { ColumnsType } from 'antd/es/table'
import { Pipeline, Tool } from '../types'
import { useAppStore } from '../stores/app'
import apiService from '../services/api'
import { useNavigate } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import PipelineEditor from '../components/pipeline/PipelineEditor'

const { Option } = Select
const { TextArea } = Input

const Pipelines: React.FC = () => {
  const navigate = useNavigate()
  const { tools, loadTools } = useAppStore()
  
  const [pipelines, setPipelines] = useState<Pipeline[]>([])
  const [loading, setLoading] = useState(false)
  const [formVisible, setFormVisible] = useState(false)
  const [detailVisible, setDetailVisible] = useState(false)
  const [editorVisible, setEditorVisible] = useState(false)
  const [editingPipeline, setEditingPipeline] = useState<Pipeline | null>(null)
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null)
  const [projects, setProjects] = useState<any[]>([])
  const [form] = Form.useForm()

  useEffect(() => {
    loadPipelines()
    loadTools()
    loadProjects()
  }, [loadTools])

  const loadPipelines = async () => {
    setLoading(true)
    try {
      const response = await apiService.getPipelines()
      // 兼容分页格式和数组格式
      const pipelines = Array.isArray(response) 
        ? response 
        : (response as any)?.results || []
      setPipelines(pipelines)
    } catch (error) {
      console.error('Failed to load pipelines:', error)
      message.error('加载流水线列表失败')
      setPipelines([]) // 保证类型安全
    } finally {
      setLoading(false)
    }
  }

  const loadProjects = async () => {
    try {
      const projectList = await apiService.getProjects()
      setProjects(projectList)
    } catch (error) {
      console.error('Failed to load projects:', error)
    }
  }

  const handleCreatePipeline = () => {
    setEditingPipeline(null)
    form.resetFields()
    // 设置默认值
    form.setFieldsValue({
      is_active: true
    })
    setFormVisible(true)
  }

  const handleEditPipeline = (pipeline: Pipeline) => {
    setEditingPipeline(pipeline)
    form.setFieldsValue({
      name: pipeline.name,
      description: pipeline.description,
      project: pipeline.project,
      is_active: pipeline.is_active,
      execution_mode: pipeline.execution_mode || 'local',
      execution_tool: pipeline.execution_tool,
      tool_job_name: pipeline.tool_job_name
    })
    setFormVisible(true)
  }

  const handleViewPipeline = async (pipeline: Pipeline) => {
    try {
      // 获取完整的流水线详情（包含steps数组）
      const fullPipeline = await apiService.getPipeline(pipeline.id)
      setSelectedPipeline(fullPipeline)
      setDetailVisible(true)
    } catch (error) {
      console.error('Failed to load pipeline details:', error)
      message.error('加载流水线详情失败')
    }
  }

  const handleExecutePipeline = async (pipeline: Pipeline) => {
    try {
      const execution = await apiService.createExecution({
        pipeline: pipeline.id,
        trigger_type: 'manual',
        parameters: {}
      })
      message.success('流水线执行已启动')
      navigate(`/executions/${execution.id}`)
    } catch (error) {
      console.error('Failed to execute pipeline:', error)
      message.error('启动流水线失败')
    }
  }

  const handleDeletePipeline = async (pipeline: Pipeline) => {
    try {
      await apiService.deletePipeline(pipeline.id)
      message.success('流水线删除成功')
      loadPipelines()
    } catch (error) {
      console.error('Failed to delete pipeline:', error)
      message.error('删除流水线失败')
    }
  }

  const handleFormSubmit = async () => {
    try {
      const values = await form.validateFields()
      
      if (editingPipeline) {
        await apiService.updatePipeline(editingPipeline.id, values)
        message.success('流水线更新成功')
      } else {
        await apiService.createPipeline(values)
        message.success('流水线创建成功')
      }
      
      setFormVisible(false)
      loadPipelines()
    } catch (error) {
      console.error('Failed to save pipeline:', error)
      message.error(editingPipeline ? '更新流水线失败' : '创建流水线失败')
    }
  }

  const handleOpenEditor = async (pipeline?: Pipeline) => {
    if (pipeline) {
      try {
        // 获取完整的流水线详情（包含steps数组）
        const fullPipeline = await apiService.getPipeline(pipeline.id)
        setSelectedPipeline(fullPipeline)
      } catch (error) {
        console.error('Failed to load pipeline details:', error)
        message.error('加载流水线详情失败')
        return
      }
    } else {
      setSelectedPipeline(null)
    }
    setEditorVisible(true)
  }

  const handleEditorSave = async (pipeline: Pipeline) => {
    try {
      // 重新加载流水线列表以获取最新数据
      await loadPipelines()
      message.success('流水线保存成功')
    } catch (error) {
      console.error('Failed to reload pipelines:', error)
      // 即使刷新失败，也要关闭编辑器，因为保存操作已经在编辑器内部完成
    } finally {
      // 关闭编辑器
      setEditorVisible(false)
      // 清理选中状态
      setSelectedPipeline(null)
    }
  }

  const handleToggleStatus = async (pipeline: Pipeline) => {
    try {
      const newStatus = !pipeline.is_active
      await apiService.togglePipelineStatus(pipeline.id, newStatus)
      message.success(`流水线已${newStatus ? '激活' : '停用'}`)
      loadPipelines()
    } catch (error) {
      console.error('Failed to toggle pipeline status:', error)
      message.error('切换状态失败')
    }
  }

  const getStatusTag = (pipeline: Pipeline) => {
    if (pipeline.is_active) {
      return <Tag color="green" icon={<CheckCircleOutlined />}>活跃</Tag>
    } else {
      return <Tag color="red" icon={<CloseCircleOutlined />}>停用</Tag>
    }
  }

  const columns: ColumnsType<Pipeline> = [
    {
      title: '流水线名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Pipeline) => (
        <a onClick={() => handleViewPipeline(record)} style={{ fontWeight: 500 }}>
          {name}
        </a>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: { showTitle: false },
      render: (description: string) => (
        <Tooltip title={description}>
          {description || '-'}
        </Tooltip>
      ),
    },
    {
      title: '步骤数',
      key: 'stepsCount',
      render: (_, record: Pipeline) => (
        <span>{record.steps_count ?? record.steps?.length ?? 0}</span>
      ),
    },
    {
      title: 'CI/CD工具',
      key: 'execution_tool',
      render: (_, record: Pipeline) => {
        if (record.execution_tool_name) {
          return (
            <Tag color={record.execution_tool_type === 'jenkins' ? 'blue' : 'default'}>
              {record.execution_tool_name}
            </Tag>
          )
        }
        return <span style={{ color: '#999' }}>本地执行</span>
      },
    },
    {
      title: '状态',
      key: 'status',
      render: (_, record: Pipeline) => getStatusTag(record),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (created_at: string) => (
        <span style={{ fontSize: 12, color: '#666' }}>
          {formatDistanceToNow(new Date(created_at), {
            addSuffix: true,
            locale: zhCN
          })}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: Pipeline) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button 
              type="text" 
              icon={<EyeOutlined />} 
              onClick={() => handleViewPipeline(record)}
            />
          </Tooltip>
          <Tooltip title="执行流水线">
            <Button 
              type="text" 
              icon={<PlayCircleOutlined />} 
              onClick={() => handleExecutePipeline(record)}
              disabled={!record.is_active}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button 
              type="text" 
              icon={<EditOutlined />} 
              onClick={() => handleEditPipeline(record)}
            />
          </Tooltip>
          <Tooltip title="拖拽式编辑器">
            <Button 
              type="text" 
              icon={<DeploymentUnitOutlined />} 
              onClick={() => handleOpenEditor(record)}
            />
          </Tooltip>
          <Tooltip title={record.is_active ? "停用流水线" : "激活流水线"}>
            <Button 
              type="text" 
              icon={<PoweroffOutlined />} 
              onClick={() => handleToggleStatus(record)}
              style={{ color: record.is_active ? '#ff4d4f' : '#52c41a' }}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确认删除此流水线？"
              description="删除后将无法恢复，相关执行记录也会受到影响。"
              onConfirm={() => handleDeletePipeline(record)}
              okText="确认删除"
              cancelText="取消"
            >
              <Button type="text" icon={<DeleteOutlined />} danger />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: '24px' }}>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总流水线数"
              value={pipelines.length}
              prefix={<AppstoreOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃流水线"
              value={pipelines.filter(p => p.is_active).length}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="停用流水线"
              value={pipelines.filter(p => !p.is_active).length}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均步骤数"
              value={pipelines.length > 0 ? Math.round(pipelines.reduce((sum, p) => sum + (p.steps_count ?? p.steps?.length ?? 0), 0) / pipelines.length) : 0}
              prefix={<SettingOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 流水线列表 */}
      <Card 
        title="流水线列表" 
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={handleCreatePipeline}
          >
            新建流水线
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={pipelines}
          rowKey="id"
          loading={loading}
          pagination={{
            total: pipelines.length,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>

      {/* 创建/编辑表单 */}
      <Modal
        title={editingPipeline ? '编辑流水线' : '新建流水线'}
        open={formVisible}
        onCancel={() => setFormVisible(false)}
        onOk={handleFormSubmit}
        okText={editingPipeline ? '更新' : '创建'}
        cancelText="取消"
        width={600}
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
            label="流水线名称"
            rules={[{ required: true, message: '请输入流水线名称' }]}
          >
            <Input placeholder="输入流水线名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea 
              placeholder="输入流水线描述（可选）" 
              rows={3} 
            />
          </Form.Item>

          <Form.Item
            name="execution_mode"
            label="执行模式"
            initialValue="local"
          >
            <Select placeholder="选择执行模式">
              <Option value="local">
                <div>
                  <div>本地执行</div>
                  <div style={{ fontSize: 12, color: '#999' }}>使用本地Celery执行所有步骤</div>
                </div>
              </Option>
              <Option value="remote">
                <div>
                  <div>远程工具</div>
                  <div style={{ fontSize: 12, color: '#999' }}>在CI/CD工具中执行</div>
                </div>
              </Option>
              <Option value="hybrid">
                <div>
                  <div>混合模式</div>
                  <div style={{ fontSize: 12, color: '#999' }}>部分本地、部分远程执行</div>
                </div>
              </Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="execution_tool"
            label="执行工具"
            tooltip="选择用于远程或混合模式执行的CI/CD工具"
          >
            <Select placeholder="选择CI/CD工具（可选）" allowClear>
              {tools.map(tool => (
                <Option key={tool.id} value={tool.id}>
                  <div>
                    <div>{tool.name}</div>
                    <div style={{ fontSize: 12, color: '#999' }}>{tool.tool_type} - {tool.base_url}</div>
                  </div>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="tool_job_name"
            label="工具作业名称"
            tooltip="在CI/CD工具中的作业名称"
          >
            <Input placeholder="输入工具中的作业名称（可选）" />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="状态"
            initialValue={true}
          >
            <Select>
              <Option value={true}>活跃</Option>
              <Option value={false}>停用</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 流水线详情抽屉 */}
      <Drawer
        title="流水线详情"
        open={detailVisible}
        onClose={() => setDetailVisible(false)}
        width={600}
      >
        {selectedPipeline && (
          <div>
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={12}>
                <Card size="small" title="基本信息">
                  <p><strong>名称:</strong> {selectedPipeline.name}</p>
                  <p><strong>状态:</strong> {getStatusTag(selectedPipeline)}</p>
                  <p><strong>创建时间:</strong> {new Date(selectedPipeline.created_at).toLocaleString('zh-CN')}</p>
                  <p><strong>更新时间:</strong> {new Date(selectedPipeline.updated_at).toLocaleString('zh-CN')}</p>
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" title="执行配置">
                  <p><strong>步骤数:</strong> {selectedPipeline.steps_count ?? selectedPipeline.steps?.length ?? 0}</p>
                  <p><strong>项目ID:</strong> {selectedPipeline.project}</p>
                  <p><strong>执行模式:</strong> 
                    <Tag color={selectedPipeline.execution_mode === 'remote' ? 'green' : 'blue'}>
                      {selectedPipeline.execution_mode === 'remote' ? '远程工具' : 
                       selectedPipeline.execution_mode === 'hybrid' ? '混合模式' : '本地执行'}
                    </Tag>
                  </p>
                  {selectedPipeline.execution_tool_name && (
                    <>
                      <p><strong>CI/CD工具:</strong> 
                        <Tag color={selectedPipeline.execution_tool_type === 'jenkins' ? 'blue' : 'default'}>
                          {selectedPipeline.execution_tool_name}
                        </Tag>
                      </p>
                      {selectedPipeline.tool_job_name && (
                        <p><strong>作业名称:</strong> {selectedPipeline.tool_job_name}</p>
                      )}
                    </>
                  )}
                </Card>
              </Col>
            </Row>
            
            {selectedPipeline.description && (
              <Card size="small" title="描述" style={{ marginBottom: 16 }}>
                <p>{selectedPipeline.description}</p>
              </Card>
            )}

            <Card size="small" title="流水线步骤">
              {selectedPipeline.steps && selectedPipeline.steps.length > 0 ? (
                <div>
                  {selectedPipeline.steps.map((step, index) => (
                    <Card key={step.id} size="small" style={{ marginBottom: 8 }}>
                      <p><strong>步骤 {index + 1}:</strong> {step.name}</p>
                      <p><strong>类型:</strong> {step.step_type}</p>
                      <p><strong>顺序:</strong> {step.order}</p>
                    </Card>
                  ))}
                </div>
              ) : (
                <p style={{ color: '#999', textAlign: 'center', padding: 20 }}>
                  暂无步骤配置
                </p>
              )}
            </Card>
          </div>
        )}
      </Drawer>

      {/* 拖拽式编辑器 */}
      <PipelineEditor
        visible={editorVisible}
        pipeline={selectedPipeline || undefined}
        onClose={() => setEditorVisible(false)}
        onSave={handleEditorSave}
        tools={tools}
      />
    </div>
  )
}

export default Pipelines
