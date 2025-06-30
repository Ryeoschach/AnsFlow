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
  Divider
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SaveOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  SettingOutlined
} from '@ant-design/icons'
import { AtomicStep, Pipeline } from '../../types'
import apiService from '../../services/api'

const { Text } = Typography
const { Option } = Select
const { TextArea } = Input

interface PipelineEditorProps {
  visible?: boolean
  pipeline?: Pipeline
  onSave?: (pipeline: Pipeline) => void
  onClose?: () => void
  tools?: any[]
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

  // 清理状态的effect
  useEffect(() => {
    if (visible && pipeline) {
      // 每次打开编辑器时重新初始化steps - 深拷贝避免引用污染
      const initialSteps = pipeline.steps ? 
        pipeline.steps.map(step => ({ ...step })).sort((a, b) => a.order - b.order) : 
        []
      setSteps(initialSteps)
    } else if (!visible) {
      // 关闭编辑器时清理状态
      setSteps([])
      setStepFormVisible(false)
      setEditingStep(null)
      form.resetFields()
    }
  }, [visible, pipeline?.id]) // 只监听visible和pipeline.id的变化

  // 当pipeline内容变化时不自动更新steps，避免污染编辑中的内容
  // 用户需要手动重新打开编辑器来获取最新数据

  const handleAddStep = () => {
    setEditingStep(null)
    form.resetFields()
    form.setFieldsValue({
      order: steps.length + 1,
      parameters: '{}'
    })
    setStepFormVisible(true)
  }

  const handleEditStep = (step: AtomicStep) => {
    setEditingStep(step)
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

  const handleSavePipeline = async () => {
    if (!pipeline) {
      message.error('请先选择或创建流水线')
      return
    }

    try {
      // 准备更新数据，确保每个步骤都有唯一的临时ID（用于前端显示）
      // 后端保存时会重新生成正确的ID
      const updateData = {
        name: pipeline.name,
        description: pipeline.description,
        project: pipeline.project,
        is_active: pipeline.is_active,
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
            <Select placeholder="选择步骤类型">
              {STEP_TYPES.map(type => (
                <Option key={type.value} value={type.value}>
                  <div>
                    <div>{type.label}</div>
                    <div style={{ fontSize: 12, color: '#999' }}>{type.description}</div>
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
          
          <Form.Item
            name="parameters"
            label="步骤参数"
          >
            <TextArea 
              placeholder='输入JSON格式的参数，例如: {"timeout": 300, "retry": 3}'
              rows={6}
            />
          </Form.Item>
        </Form>
      </Drawer>
    </Drawer>
  )
}

export default PipelineEditor