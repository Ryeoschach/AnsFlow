import React, { useState, useEffect } from 'react'
import { 
  Card, 
  Button, 
  Space, 
  message, 
  Typography,
  Drawer,
  Form,
  Input,
  Select,
  Divider,
  Alert,
  Collapse
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SaveOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  SettingOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons'
import { AtomicStep, Pipeline } from '../../types'
import apiService from '../../services/api'
import ParameterDocumentation from '../ParameterDocumentation'

const { Text } = Typography
const { Option } = Select
const { TextArea } = Input

// 优化Select组件的样式
const selectStyles = `
  .ant-select-dropdown .ant-select-item-option-content {
    white-space: normal !important;
    height: auto !important;
    padding: 8px 12px !important;
  }
  
  .ant-select-dropdown .ant-select-item {
    height: auto !important;
    min-height: 32px !important;
    padding: 0 !important;
  }
  
  .ant-select-dropdown .ant-select-item-option-content > div {
    width: 100%;
  }
  
  .ant-select-selector {
    height: auto !important;
    min-height: 32px !important;
  }
  
  .ant-select-selection-item {
    line-height: 30px !important;
    padding: 0 8px !important;
    height: 30px !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
  }
  
  /* 强制隐藏选中项中的第二个div */
  .ant-select-selection-item > div > div:nth-child(2) {
    display: none !important;
  }
`

// 将样式注入到页面中
if (typeof document !== 'undefined' && !document.getElementById('pipeline-editor-styles')) {
  const style = document.createElement('style')
  style.id = 'pipeline-editor-styles'
  style.textContent = selectStyles
  document.head.appendChild(style)
}

interface PipelineEditorProps {
  visible?: boolean
  pipeline?: Pipeline
  onSave?: (pipeline: Pipeline) => void
  onClose?: () => void
  tools?: { id: number; name: string; tool_type: string; base_url: string }[]
}

interface StepFormData {
  name: string
  step_type: string
  description?: string
  parameters: Record<string, any>
  order: number
}

const STEP_TYPES = [
  { value: 'fetch_code', label: '代码拉取', description: '从版本控制系统拉取代码' },
  { value: 'build', label: '构建', description: '编译和打包代码' },
  { value: 'test', label: '测试', description: '运行自动化测试' },
  { value: 'security_scan', label: '安全扫描', description: '安全漏洞扫描' },
  { value: 'deploy', label: '部署', description: '部署到目标环境' },
  { value: 'notify', label: '通知', description: '发送通知消息' },
  { value: 'custom', label: '自定义', description: '自定义步骤' },
]

const PipelineEditor: React.FC<PipelineEditorProps> = ({ 
  visible = true, 
  pipeline, 
  onSave, 
  onClose,
  tools = []
}) => {
  const [steps, setSteps] = useState<AtomicStep[]>([])
  const [stepFormVisible, setStepFormVisible] = useState(false)
  const [editingStep, setEditingStep] = useState<AtomicStep | null>(null)
  const [form] = Form.useForm()
  // 添加流水线基本信息编辑表单
  const [pipelineForm] = Form.useForm()
  const [pipelineInfoVisible, setPipelineInfoVisible] = useState(false)
  // 添加参数说明状态
  const [selectedStepType, setSelectedStepType] = useState<string>('')
  const [showParameterDoc, setShowParameterDoc] = useState(false)

  // 清理状态的effect
  useEffect(() => {
    if (visible && pipeline) {
      // 每次打开编辑器时重新初始化steps - 深拷贝避免引用污染
      const initialSteps = pipeline.steps ? 
        pipeline.steps.map(step => ({ ...step })).sort((a, b) => a.order - b.order) : 
        []
      setSteps(initialSteps)
      
      // 初始化流水线基本信息表单
      pipelineForm.setFieldsValue({
        name: pipeline.name,
        description: pipeline.description,
        execution_mode: pipeline.execution_mode || 'local',
        execution_tool: pipeline.execution_tool,
        tool_job_name: pipeline.tool_job_name,
        is_active: pipeline.is_active
      })
    } else if (!visible) {
      // 关闭编辑器时清理状态
      setSteps([])
      setStepFormVisible(false)
      setEditingStep(null)
      setPipelineInfoVisible(false)
      setSelectedStepType('')
      setShowParameterDoc(false)
      form.resetFields()
      pipelineForm.resetFields()
    }
  }, [visible, pipeline?.id]) // 只监听visible和pipeline.id的变化

  // 当pipeline内容变化时不自动更新steps，避免污染编辑中的内容
  // 用户需要手动重新打开编辑器来获取最新数据

  const handleAddStep = () => {
    setEditingStep(null)
    setSelectedStepType('')
    setShowParameterDoc(false)
    form.resetFields()
    form.setFieldsValue({
      order: steps.length + 1,
      parameters: '{}'
    })
    setStepFormVisible(true)
  }

  const handleEditStep = (step: AtomicStep) => {
    setEditingStep(step)
    setSelectedStepType(step.step_type)
    setShowParameterDoc(false)
    form.setFieldsValue({
      name: step.name,
      step_type: step.step_type,
      description: step.description,
      order: step.order,
      parameters: JSON.stringify(step.parameters, null, 2)
    })
    setStepFormVisible(true)
  }

  const handleDeleteStep = (stepId: number) => {
    setSteps(steps.filter(step => step.id !== stepId))
    message.success('步骤删除成功')
  }

  const handleMoveStep = (stepId: number, direction: 'up' | 'down') => {
    const stepIndex = steps.findIndex(step => step.id === stepId)
    if (stepIndex === -1) return

    const newSteps = [...steps]
    const targetIndex = direction === 'up' ? stepIndex - 1 : stepIndex + 1

    if (targetIndex < 0 || targetIndex >= newSteps.length) return

    [newSteps[stepIndex], newSteps[targetIndex]] = [newSteps[targetIndex], newSteps[stepIndex]]
    
    newSteps.forEach((step, index) => {
      step.order = index + 1
    })

    setSteps(newSteps)
    message.success('步骤顺序调整成功')
  }

  const handleStepSubmit = async () => {
    try {
      const values = await form.validateFields()
      
      let parameters = {}
      if (values.parameters) {
        try {
          parameters = JSON.parse(values.parameters)
        } catch (e) {
          message.error('参数格式错误，请输入有效的JSON')
          return
        }
      }

      const stepData: StepFormData = {
        ...values,
        parameters
      }

      if (editingStep) {
        const updatedSteps = steps.map(step => 
          step.id === editingStep.id 
            ? { ...step, ...stepData }
            : step
        )
        setSteps(updatedSteps)
        message.success('步骤更新成功')
      } else {
        const newStep: AtomicStep = {
          id: Date.now(), // 临时ID，后端会重新分配
          ...stepData,
          pipeline: pipeline?.id || 0,
          is_active: true,
          created_at: new Date().toISOString()
        }
        setSteps([...steps, newStep])
        message.success('步骤添加成功')
      }

      setStepFormVisible(false)
    } catch (error) {
      console.error('Failed to save step:', error)
    }
  }

  // 处理流水线基本信息编辑
  const handleEditPipelineInfo = () => {
    setPipelineInfoVisible(true)
  }

  const handlePipelineInfoSubmit = async () => {
    if (!pipeline) return

    try {
      const values = await pipelineForm.validateFields()
      
      // 更新本地 pipeline 状态
      const updatedPipelineData = {
        ...pipeline,
        ...values
      }
      
      console.log('Updating pipeline info:', values)
      
      // 通知父组件 pipeline 数据已更新
      if (onSave) {
        onSave(updatedPipelineData)
      }
      
      setPipelineInfoVisible(false)
      message.success('流水线信息更新成功')
    } catch (error) {
      console.error('Failed to update pipeline info:', error)
      message.error('更新流水线信息失败')
    }
  }

  const handleSavePipeline = async () => {
    if (!pipeline) {
      message.error('请先选择或创建流水线')
      return
    }

    try {
      // 获取最新的流水线基本信息
      const pipelineInfo = await pipelineForm.validateFields()
      
      // 准备更新数据，确保每个步骤都有唯一的临时ID（用于前端显示）
      // 后端保存时会重新生成正确的ID
      // 确保 steps 字段始终存在，即使是空数组
      const updateData = {
        name: pipelineInfo.name || pipeline.name,
        description: pipelineInfo.description || pipeline.description,
        project: pipeline.project,
        is_active: pipelineInfo.is_active !== undefined ? pipelineInfo.is_active : pipeline.is_active,
        execution_mode: pipelineInfo.execution_mode || pipeline.execution_mode,
        execution_tool: pipelineInfo.execution_tool || pipeline.execution_tool,
        tool_job_name: pipelineInfo.tool_job_name || pipeline.tool_job_name,
        tool_job_config: pipeline.tool_job_config,
        steps: steps.map((step, index) => ({
          name: step.name,
          step_type: step.step_type,
          description: step.description || '',
          parameters: step.parameters || {},
          order: index + 1, // 重新排序，确保顺序正确
          is_active: true
        }))
      }

      console.log('Saving pipeline with data:', updateData)
      console.log('Steps being sent:', updateData.steps)

      // 使用API服务保存流水线
      const updatedPipeline = await apiService.updatePipeline(pipeline.id, updateData)
      
      message.success('流水线保存成功')
      
      // 更新本地状态为服务器返回的最新数据
      if (updatedPipeline.steps) {
        setSteps(updatedPipeline.steps.sort((a, b) => a.order - b.order))
      }
      
      onSave?.(updatedPipeline)
    } catch (error) {
      console.error('Failed to save pipeline:', error)
      message.error('保存流水线失败')
    }
  }

  const getStepTypeLabel = (stepType: string) => {
    const type = STEP_TYPES.find(t => t.value === stepType)
    return type?.label || stepType
  }

  const getStepIcon = (stepType: string) => {
    switch (stepType) {
      case 'fetch_code':
        return '📥'
      case 'build':
        return '🔨'
      case 'test':
        return '🧪'
      case 'security_scan':
        return '🛡️'
      case 'deploy':
        return '🚀'
      case 'notify':
        return '📢'
      default:
        return '⚙️'
    }
  }

  if (!visible) {
    return null
  }

  return (
    <Drawer
      title={
        <Space>
          <SettingOutlined />
          <span>{pipeline ? `编辑流水线: ${pipeline.name}` : '新建流水线'}</span>
        </Space>
      }
      open={visible}
      onClose={onClose}
      width="80%"
      placement="right"
      extra={
        <Space>
          <Button onClick={onClose}>取消</Button>
          <Button icon={<SettingOutlined />} onClick={handleEditPipelineInfo}>
            编辑信息
          </Button>
          <Button icon={<PlusOutlined />} onClick={handleAddStep}>
            添加步骤
          </Button>
          <Button type="primary" icon={<SaveOutlined />} onClick={handleSavePipeline}>
            保存流水线
          </Button>
        </Space>
      }
    >
      <div style={{ padding: '0' }}>
        <Card 
          title="流水线步骤配置"
          size="small"
        >
          {steps.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
              <p>暂无流水线步骤</p>
              <Button type="dashed" icon={<PlusOutlined />} onClick={handleAddStep}>
                添加第一个步骤
              </Button>
            </div>
          ) : (
            <div>
              {steps.map((step, index) => (
                <Card
                  key={step.id}
                  size="small"
                  style={{ marginBottom: 16 }}
                  title={
                    <Space>
                      <span>{getStepIcon(step.step_type)}</span>
                      <span>步骤 {index + 1}: {step.name}</span>
                      <Text type="secondary">({getStepTypeLabel(step.step_type)})</Text>
                    </Space>
                  }
                  extra={
                    <Space>
                      <Button 
                        type="text" 
                        size="small" 
                        icon={<ArrowUpOutlined />}
                        onClick={() => handleMoveStep(step.id, 'up')}
                        disabled={index === 0}
                      />
                      <Button 
                        type="text" 
                        size="small" 
                        icon={<ArrowDownOutlined />}
                        onClick={() => handleMoveStep(step.id, 'down')}
                        disabled={index === steps.length - 1}
                      />
                      <Button 
                        type="text" 
                        size="small" 
                        icon={<EditOutlined />}
                        onClick={() => handleEditStep(step)}
                      />
                      <Button 
                        type="text" 
                        size="small" 
                        icon={<DeleteOutlined />}
                        danger
                        onClick={() => handleDeleteStep(step.id)}
                      />
                    </Space>
                  }
                >
                  {step.description && (
                    <Text type="secondary">{step.description}</Text>
                  )}
                  {Object.keys(step.parameters || {}).length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <Text strong>参数: </Text>
                      <Text code>{JSON.stringify(step.parameters, null, 2)}</Text>
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Drawer
        title={editingStep ? '编辑步骤' : '新建步骤'}
        open={stepFormVisible}
        onClose={() => setStepFormVisible(false)}
        width={500}
        footer={
          <Space style={{ float: 'right' }}>
            <Button onClick={() => setStepFormVisible(false)}>取消</Button>
            <Button type="primary" onClick={handleStepSubmit}>
              {editingStep ? '更新' : '添加'}
            </Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="步骤名称"
            rules={[{ required: true, message: '请输入步骤名称' }]}
          >
            <Input placeholder="输入步骤名称" />
          </Form.Item>

          <Form.Item
            name="step_type"
            label="步骤类型"
            rules={[{ required: true, message: '请选择步骤类型' }]}
          >
            <Select 
              placeholder="选择步骤类型"
              optionLabelProp="label"
              onChange={(value) => {
                setSelectedStepType(value)
                setShowParameterDoc(true)
              }}
            >
              {STEP_TYPES.map(type => (
                <Option 
                  key={type.value} 
                  value={type.value}
                  label={type.label}
                >
                  <div style={{ lineHeight: '1.4', padding: '4px 0' }}>
                    <div style={{ fontWeight: 500, marginBottom: 2 }}>
                      {type.label}
                    </div>
                    <div style={{ 
                      fontSize: 12, 
                      color: '#999',
                      whiteSpace: 'normal',
                      wordBreak: 'break-word',
                      lineHeight: '1.3'
                    }}>
                      {type.description}
                    </div>
                  </div>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="步骤描述"
          >
            <Input placeholder="输入步骤描述（可选）" />
          </Form.Item>

          <Form.Item
            name="order"
            label="执行顺序"
            rules={[{ required: true, message: '请输入执行顺序' }]}
          >
            <Input type="number" placeholder="执行顺序" />
          </Form.Item>

          <Divider>参数配置</Divider>
          
          {/* 参数说明按钮 */}
          {selectedStepType && (
            <Alert
              message={
                <Space>
                  <span>需要参数配置帮助？</span>
                  <Button 
                    type="link" 
                    size="small" 
                    icon={<QuestionCircleOutlined />}
                    onClick={() => setShowParameterDoc(!showParameterDoc)}
                  >
                    {showParameterDoc ? '隐藏参数说明' : '查看参数说明'}
                  </Button>
                </Space>
              }
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          {/* 参数说明组件 */}
          {selectedStepType && showParameterDoc && (
            <div style={{ marginBottom: 16 }}>
              <ParameterDocumentation 
                stepType={selectedStepType}
                visible={showParameterDoc}
                onParameterSelect={(paramKey, paramValue) => {
                  // 将选择的参数示例插入到参数文本框
                  const currentParams = form.getFieldValue('parameters') || '{}'
                  try {
                    const params = JSON.parse(currentParams)
                    params[paramKey] = paramValue
                    form.setFieldsValue({
                      parameters: JSON.stringify(params, null, 2)
                    })
                    message.success(`已插入参数: ${paramKey}`)
                  } catch (error) {
                    // 如果当前参数不是有效JSON，直接替换
                    const newParams = { [paramKey]: paramValue }
                    form.setFieldsValue({
                      parameters: JSON.stringify(newParams, null, 2)
                    })
                    message.success(`已插入参数: ${paramKey}`)
                  }
                }}
              />
            </div>
          )}
          
          <Form.Item
            name="parameters"
            label={
              <Space>
                <span>步骤参数</span>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  (JSON格式)
                </Typography.Text>
              </Space>
            }
          >
            <TextArea 
              placeholder='输入JSON格式的参数，例如: {"timeout": 300, "retry": 3}'
              rows={6}
            />
          </Form.Item>
        </Form>
      </Drawer>

      {/* 流水线基本信息编辑 Drawer */}
      <Drawer
        title="编辑流水线信息"
        open={pipelineInfoVisible}
        onClose={() => setPipelineInfoVisible(false)}
        width={500}
        footer={
          <Space style={{ float: 'right' }}>
            <Button onClick={() => setPipelineInfoVisible(false)}>取消</Button>
            <Button type="primary" onClick={handlePipelineInfoSubmit}>
              保存
            </Button>
          </Space>
        }
      >
        <Form form={pipelineForm} layout="vertical">
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
            <Input.TextArea 
              placeholder="输入流水线描述（可选）" 
              rows={3} 
            />
          </Form.Item>

          <Form.Item
            name="execution_mode"
            label="执行模式"
            tooltip="本地执行：使用本地Celery执行；远程工具：在CI/CD工具中执行；混合模式：部分本地、部分远程执行"
          >
            <Select placeholder="选择执行模式">
              <Select.Option value="local">本地执行</Select.Option>
              <Select.Option value="remote">远程工具</Select.Option>
              <Select.Option value="hybrid">混合模式</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="execution_tool"
            label="执行工具"
            tooltip="选择用于远程或混合模式执行的CI/CD工具"
          >
            <Select 
              placeholder="选择CI/CD工具（可选）" 
              allowClear
            >
              {tools.map((tool: any) => (
                <Select.Option 
                  key={tool.id} 
                  value={tool.id}
                >
                  {tool.name} ({tool.tool_type})
                </Select.Option>
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
          >
            <Select>
              <Select.Option value={true}>活跃</Select.Option>
              <Select.Option value={false}>停用</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Drawer>
    </Drawer>
  )
}

export default PipelineEditor