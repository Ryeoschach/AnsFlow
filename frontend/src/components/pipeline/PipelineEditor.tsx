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
  Collapse,
  Modal
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SaveOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  SettingOutlined,
  QuestionCircleOutlined,
  EyeOutlined
} from '@ant-design/icons'
import { AtomicStep, Pipeline, GitCredential, PipelineStep } from '../../types'
import apiService from '../../services/api'
import ParameterDocumentation from '../ParameterDocumentation'
import PipelinePreview from './PipelinePreview'

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
  git_credential_id?: number | null
  ansible_playbook?: number | null
  ansible_inventory?: number | null
  ansible_credential?: number | null
}

// 工具函数：判断是否为AtomicStep
const isAtomicStep = (step: PipelineStep | AtomicStep): step is AtomicStep => {
  return 'parameters' in step && 'pipeline' in step && 'is_active' in step && 'created_at' in step
}

// 工具函数：判断是否为PipelineStep
const isPipelineStep = (step: PipelineStep | AtomicStep): step is PipelineStep => {
  return !isAtomicStep(step)
}

// 工具函数：获取步骤参数
const getStepParameters = (step: PipelineStep | AtomicStep): Record<string, any> => {
  if (isAtomicStep(step)) {
    return step.parameters || {}
  } else {
    // 对于旧的PipelineStep，需要从独立字段构建参数
    const parameters = step.ansible_parameters || {}
    
    // 如果是ansible步骤，确保从独立字段获取ansible配置
    if (step.step_type === 'ansible') {
      return {
        ...parameters,
        playbook_id: step.ansible_playbook,
        inventory_id: step.ansible_inventory,
        credential_id: step.ansible_credential
      }
    }
    
    return parameters
  }
}

// 工具函数：获取步骤的Ansible配置
const getStepAnsibleConfig = (step: PipelineStep | AtomicStep) => {
  if (isAtomicStep(step)) {
    return {
      playbook_id: step.parameters?.playbook_id || step.ansible_playbook,
      inventory_id: step.parameters?.inventory_id || step.ansible_inventory,
      credential_id: step.parameters?.credential_id || step.ansible_credential
    }
  } else {
    return {
      playbook_id: step.ansible_playbook,
      inventory_id: step.ansible_inventory,
      credential_id: step.ansible_credential
    }
  }
}

// 工具函数：规范化步骤数据用于显示
const normalizeStepForDisplay = (step: PipelineStep | AtomicStep): AtomicStep => {
  if (isAtomicStep(step)) {
    return step
  } else {
    // 将PipelineStep转换为AtomicStep格式用于显示
    // 确保正确传递参数，包括ansible相关的ID
    const parameters = step.ansible_parameters || {}
    
    // 如果有ansible相关的ID，添加到parameters中
    if (step.ansible_playbook) {
      parameters.playbook_id = step.ansible_playbook
    }
    if (step.ansible_inventory) {
      parameters.inventory_id = step.ansible_inventory
    }
    if (step.ansible_credential) {
      parameters.credential_id = step.ansible_credential
    }
    
    return {
      id: step.id,
      name: step.name,
      step_type: step.step_type,
      description: step.description || '',
      order: step.order,
      parameters: parameters,
      pipeline: 0, // 临时值
      is_active: true,
      created_at: new Date().toISOString(),
      ansible_playbook: step.ansible_playbook,
      ansible_inventory: step.ansible_inventory,
      ansible_credential: step.ansible_credential
    }
  }
}

const STEP_TYPES = [
  { value: 'fetch_code', label: '代码拉取', description: '从版本控制系统拉取代码' },
  { value: 'build', label: '构建', description: '编译和打包代码' },
  { value: 'test', label: '测试', description: '运行自动化测试' },
  { value: 'security_scan', label: '安全扫描', description: '安全漏洞扫描' },
  { value: 'deploy', label: '部署', description: '部署到目标环境' },
  { value: 'ansible', label: 'Ansible自动化', description: '执行Ansible Playbook自动化任务' },
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
  // 使用统一的步骤类型，兼容PipelineStep和AtomicStep
  const [steps, setSteps] = useState<(PipelineStep | AtomicStep)[]>([])
  const [stepFormVisible, setStepFormVisible] = useState(false)
  const [editingStep, setEditingStep] = useState<(PipelineStep | AtomicStep) | null>(null)
  const [form] = Form.useForm()
  // 添加流水线基本信息编辑表单
  const [pipelineForm] = Form.useForm()
  const [pipelineInfoVisible, setPipelineInfoVisible] = useState(false)
  // 添加参数说明状态
  const [selectedStepType, setSelectedStepType] = useState<string>('')
  const [showParameterDoc, setShowParameterDoc] = useState(false)
  // 添加预览功能状态
  const [previewVisible, setPreviewVisible] = useState(false)
  // 添加Git凭据状态
  const [gitCredentials, setGitCredentials] = useState<GitCredential[]>([])
  // 添加Ansible资源状态
  const [ansiblePlaybooks, setAnsiblePlaybooks] = useState<any[]>([])
  const [ansibleInventories, setAnsibleInventories] = useState<any[]>([])
  const [ansibleCredentials, setAnsibleCredentials] = useState<any[]>([])

  // 清理状态的effect
  useEffect(() => {
    if (visible && pipeline) {
      // 重新获取完整的流水线数据（包含步骤）
      const loadPipelineDetails = async () => {
        try {
          console.log('Loading pipeline details for:', pipeline.name, pipeline.id)
          const fullPipeline = await apiService.getPipeline(pipeline.id)
          console.log('Full pipeline data:', fullPipeline)
          
          // 每次打开编辑器时重新初始化steps - 优先使用PipelineStep，兼容AtomicStep
          let initialSteps: (PipelineStep | AtomicStep)[] = []
          
          if (fullPipeline.steps && fullPipeline.steps.length > 0) {
            // 使用新的PipelineStep数据
            initialSteps = fullPipeline.steps.map(step => ({ ...step })).sort((a, b) => a.order - b.order)
            console.log('Using PipelineStep data:', initialSteps.length, 'steps')
          } else if (fullPipeline.atomic_steps && fullPipeline.atomic_steps.length > 0) {
            // 兼容旧的AtomicStep数据
            initialSteps = fullPipeline.atomic_steps.map(step => ({ ...step })).sort((a, b) => a.order - b.order)
            console.log('Using AtomicStep data (compatibility):', initialSteps.length, 'steps')
          }
          
          setSteps(initialSteps)
          
          // 使用完整的流水线数据初始化表单
          pipelineForm.setFieldsValue({
            name: fullPipeline.name,
            description: fullPipeline.description,
            execution_mode: fullPipeline.execution_mode || 'local',
            execution_tool: fullPipeline.execution_tool,
            tool_job_name: fullPipeline.tool_job_name,
            is_active: fullPipeline.is_active
          })
        } catch (error) {
          console.error('Failed to load pipeline details:', error)
          message.error('加载流水线详情失败')
          
          // 如果获取失败，使用传入的流水线数据作为兜底
          const initialSteps: (PipelineStep | AtomicStep)[] = []
          setSteps(initialSteps)
          
          pipelineForm.setFieldsValue({
            name: pipeline.name,
            description: pipeline.description,
            execution_mode: pipeline.execution_mode || 'local',
            execution_tool: pipeline.execution_tool,
            tool_job_name: pipeline.tool_job_name,
            is_active: pipeline.is_active
          })
        }
      }
      
      loadPipelineDetails()
      
      // 获取Git凭据列表
      fetchGitCredentials()

      // 获取Ansible资源
      fetchAnsibleResources()
    } else if (!visible) {
      // 关闭编辑器时清理状态
      setSteps([])
      setStepFormVisible(false)
      setEditingStep(null)
      setPipelineInfoVisible(false)
      setSelectedStepType('')
      setShowParameterDoc(false)
      setGitCredentials([])
      setAnsiblePlaybooks([])
      setAnsibleInventories([])
      setAnsibleCredentials([])
      form.resetFields()
      pipelineForm.resetFields()
    }
  }, [visible, pipeline?.id]) // 只监听visible和pipeline.id的变化

  // 获取Git凭据列表
  const fetchGitCredentials = async () => {
    try {
      const credentials = await apiService.getGitCredentials()
      setGitCredentials(credentials)
    } catch (error) {
      console.error('Failed to fetch git credentials:', error)
    }
  }

  // 获取Ansible资源列表
  const fetchAnsibleResources = async () => {
    try {
      const [playbooks, inventories, credentials] = await Promise.all([
        apiService.getAnsiblePlaybooks(),
        apiService.getAnsibleInventories(), 
        apiService.getAnsibleCredentials()
      ])
      setAnsiblePlaybooks(playbooks)
      setAnsibleInventories(inventories)
      setAnsibleCredentials(credentials)
    } catch (error) {
      console.error('Failed to fetch ansible resources:', error)
    }
  }

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
    setStepFormVisible(true
    )
  }

  const handleEditStep = (step: PipelineStep | AtomicStep) => {
    setEditingStep(step)
    setSelectedStepType(step.step_type)
    setShowParameterDoc(false)
    
    // 获取步骤的参数和Ansible配置
    const stepParams = getStepParameters(step)
    const ansibleConfig = getStepAnsibleConfig(step)
    
    // 准备基础表单值
    const formValues: any = {
      name: step.name,
      step_type: step.step_type,
      description: step.description,
      order: step.order,
      git_credential_id: isAtomicStep(step) ? step.git_credential : undefined
    }

    // 如果是ansible步骤，从参数中提取ansible相关字段
    if (step.step_type === 'ansible') {
      formValues.ansible_playbook_id = ansibleConfig.playbook_id
      formValues.ansible_inventory_id = ansibleConfig.inventory_id  
      formValues.ansible_credential_id = ansibleConfig.credential_id
      
      // 清理参数中的ansible字段，避免重复显示
      const cleanParameters = { ...stepParams }
      delete cleanParameters.playbook_id
      delete cleanParameters.inventory_id
      delete cleanParameters.credential_id
      
      // 只有在清理后的参数不为空时才显示
      formValues.parameters = Object.keys(cleanParameters).length > 0 
        ? JSON.stringify(cleanParameters, null, 2) 
        : '{}'
      
      console.log('Loading ansible step:', {
        playbook: formValues.ansible_playbook_id,
        inventory: formValues.ansible_inventory_id,
        credential: formValues.ansible_credential_id,
        originalStep: step,
        cleanParameters: cleanParameters
      })
    } else {
      // 非ansible步骤直接使用原始参数
      formValues.parameters = JSON.stringify(stepParams, null, 2)
    }

    form.setFieldsValue(formValues)
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

      // 处理ansible步骤的特殊字段
      if (values.step_type === 'ansible') {
        // 将ansible相关字段添加到parameters中（主要存储方式）
        parameters = {
          ...parameters,
          playbook_id: values.ansible_playbook_id,
          inventory_id: values.ansible_inventory_id,
          credential_id: values.ansible_credential_id
        }
      }

      const stepData: StepFormData = {
        ...values,
        parameters,
        // 同时保存为独立字段（兼容性）
        ansible_playbook: values.step_type === 'ansible' ? values.ansible_playbook_id : undefined,
        ansible_inventory: values.step_type === 'ansible' ? values.ansible_inventory_id : undefined,
        ansible_credential: values.step_type === 'ansible' ? values.ansible_credential_id : undefined
      }

      console.log('📝 Step edit - constructed stepData:', {
        stepType: stepData.step_type,
        parameters: stepData.parameters,
        fullStepData: stepData
      })

      // 更新本地状态
      let updatedSteps
      if (editingStep) {
        console.log('🔄 Step edit - updating existing step:', {
          editingStepId: editingStep.id,
          originalStep: editingStep,
          newStepData: stepData
        })
        
        updatedSteps = steps.map(step => {
          if (step.id === editingStep.id) {
            // 完全替换步骤内容，确保所有字段都更新
            const updatedStep: AtomicStep = {
              // 保留必要的系统字段
              id: step.id,
              pipeline: isAtomicStep(step) ? step.pipeline : (pipeline?.id || 0),
              created_at: isAtomicStep(step) ? step.created_at : new Date().toISOString(),
              // 使用新的表单数据完全替换内容字段
              name: stepData.name,
              step_type: stepData.step_type,
              description: stepData.description,
              parameters: stepData.parameters,
              order: step.order, // 保持原有顺序
              is_active: true,
              git_credential: values.git_credential_id || null,
              // 兼容性字段
              ansible_playbook: stepData.ansible_playbook,
              ansible_inventory: stepData.ansible_inventory,
              ansible_credential: stepData.ansible_credential
            }
            
            console.log('🔄 Step edit - step after update:', {
              originalStep: step,
              newStepData: stepData,
              updatedStep: updatedStep,
              parametersComparison: {
                original: isAtomicStep(step) ? step.parameters : {},
                new: updatedStep.parameters
              }
            })
            return updatedStep
          }
          return step
        })
        
        console.log('🔄 Step edit - all steps after update:', updatedSteps)
      } else {
        const newStep: AtomicStep = {
          id: Date.now(), // 临时ID，后端会重新分配
          ...stepData,
          pipeline: pipeline?.id || 0,
          is_active: true,
          created_at: new Date().toISOString(),
          git_credential: values.git_credential_id || null
        }
        updatedSteps = [...steps, newStep]
        console.log('➕ Step edit - added new step:', newStep)
      }

      setSteps(updatedSteps)

      // 立即保存到后端
      console.log('🔍 Step edit - checking if pipeline exists:', !!pipeline, pipeline?.id)
      
      if (pipeline) {
        try {
          console.log('🚀 Step edit - starting auto-save process')
          
          // 显示保存中状态
          const saveMessage = message.loading('正在保存步骤到数据库...', 0)
          
          // 获取最新的流水线基本信息
          console.log('📋 Step edit - validating pipeline form...')
          const pipelineInfo = await pipelineForm.validateFields().catch((error) => {
            console.log('⚠️ Step edit - pipeline form validation failed:', error)
            return {
              name: pipeline.name,
              description: pipeline.description,
              execution_mode: pipeline.execution_mode,
              execution_tool: pipeline.execution_tool,
              tool_job_name: pipeline.tool_job_name,
              is_active: pipeline.is_active
            }
          })
          
          console.log('📋 Step edit - pipeline info:', pipelineInfo)
          console.log('📋 Step edit - pipeline info:', pipelineInfo)
          
          // 准备保存数据
          const updateData = {
            name: pipelineInfo.name || pipeline.name,
            description: pipelineInfo.description || pipeline.description,
            project: pipeline.project,
            is_active: pipelineInfo.is_active !== undefined ? pipelineInfo.is_active : pipeline.is_active,
            execution_mode: pipelineInfo.execution_mode || pipeline.execution_mode,
            execution_tool: pipelineInfo.execution_tool || pipeline.execution_tool,
            tool_job_name: pipelineInfo.tool_job_name || pipeline.tool_job_name,
            tool_job_config: pipeline.tool_job_config,
            steps: updatedSteps.map((step, index) => {
              // 直接使用步骤的参数，不通过getStepParameters处理
              const stepParams = isAtomicStep(step) ? (step.parameters || {}) : (step.ansible_parameters || {})
              
              console.log(`🔍 Step ${index + 1} (${step.name}) - building API payload:`, {
                stepId: step.id,
                stepName: step.name,
                stepType: step.step_type,
                directParams: stepParams,
                isEditedStep: editingStep && step.id === editingStep.id,
                fullStep: step
              })
              
              return {
                name: step.name,
                step_type: step.step_type,
                description: step.description || '',
                parameters: stepParams,
                order: index + 1,
                is_active: true,
                git_credential: isAtomicStep(step) ? step.git_credential : null
              }
            })
          }

          console.log('🚀 Step edit - sending API request to update pipeline:', updateData.steps.length, 'steps')
          console.log('🚀 Step edit - sending API request to update pipeline:', updateData.steps.length, 'steps')
          console.log('🚀 Step edit - API payload:', updateData)

          // 调用API保存
          console.log('🌐 Step edit - calling apiService.updatePipeline...')
          const updatedPipeline = await apiService.updatePipeline(pipeline.id, updateData)
          console.log('✅ Step edit - API request successful:', {
            returnedSteps: updatedPipeline.steps?.length || 0,
            returnedAtomicSteps: updatedPipeline.atomic_steps?.length || 0,
            fullResponse: updatedPipeline
          })
          
          // 关闭loading消息
          saveMessage()
          
          // 更新本地状态为服务器返回的最新数据
          if (updatedPipeline.steps && updatedPipeline.steps.length > 0) {
            console.log('🔄 Step edit - updating local state with API response steps')
            setSteps(updatedPipeline.steps.sort((a, b) => a.order - b.order))
          } else if (updatedPipeline.atomic_steps && updatedPipeline.atomic_steps.length > 0) {
            console.log('🔄 Step edit - updating local state with API response atomic_steps (compatibility)')
            setSteps(updatedPipeline.atomic_steps.sort((a, b) => a.order - b.order))
          }
          
          message.success(editingStep ? '步骤更新并保存成功' : '步骤添加并保存成功')
          console.log('✅ Step edit - auto-save completed successfully')
          
          // 注意：这里不调用 onSave 回调，避免页面跳转
          // onSave 回调通常用于父组件处理保存后的页面跳转
          // 在步骤编辑的自动保存场景下，我们希望保持在当前页面
          
        } catch (error) {
          console.error('❌ Step edit - auto-save failed:', error)
          console.error('❌ Step edit - error details:', error instanceof Error ? error.message : String(error))
          message.error('步骤保存到数据库失败，请手动点击"保存流水线"')
        }
      } else {
        console.log('⚠️ Step edit - no pipeline found, showing manual save message')
        message.success(editingStep ? '步骤更新成功（请保存流水线）' : '步骤添加成功（请保存流水线）')
      }

      // 不管是添加还是编辑步骤，都关闭步骤编辑抽屉，回到流水线主编辑页面
      setStepFormVisible(false)
      
      // 清理编辑状态
      setEditingStep(null)
      setSelectedStepType('')
      setShowParameterDoc(false)
      form.resetFields()
    } catch (error) {
      console.error('Failed to save step:', error)
      message.error('步骤操作失败')
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
      
      // 注意：这里不调用 onSave 回调，避免页面跳转
      // 流水线基本信息编辑完成后应该保持在当前页面
      
      setPipelineInfoVisible(false)
      message.success('流水线信息更新成功')
    } catch (error) {
      console.error('Failed to update pipeline info:', error)
      message.error('更新流水线信息失败')
    }
  }

  // 添加预览处理函数
  const handlePreviewPipeline = () => {
    if (!pipeline) {
      message.error('请先选择或创建流水线')
      return
    }

    if (steps.length === 0) {
      message.warning('请先添加流水线步骤')
      return
    }

    setPreviewVisible(true)
  }

  const handleExecuteFromPreview = async (pipeline: Pipeline) => {
    try {
      // 首先检查当前编辑的内容是否已保存
      const hasUnsavedChanges = steps.length > 0 && JSON.stringify(steps) !== JSON.stringify(pipeline.steps || [])
      
      if (hasUnsavedChanges) {
        // 询问用户是否要保存当前编辑的内容
        const shouldSave = await new Promise((resolve) => {
          Modal.confirm({
            title: '保存并执行流水线？',
            content: '检测到您有未保存的编辑内容。建议先保存当前内容，以确保执行的流水线与预览一致。',
            okText: '保存并执行',
            cancelText: '直接执行',
            onOk: () => resolve(true),
            onCancel: () => resolve(false),
          })
        })

        if (shouldSave) {
          // 保存当前编辑内容
          await handleSavePipeline()
          message.info('流水线已保存，开始执行...')
        } else {
          message.warning('将执行数据库中已保存的流水线版本')
        }
      }

      // 确保流水线配置了执行工具
      let toolId = null
      if (typeof pipeline.execution_tool === 'number') {
        toolId = pipeline.execution_tool
      } else if (pipeline.execution_tool && typeof pipeline.execution_tool === 'object') {
        toolId = pipeline.execution_tool.id
      }

      // 检查流水线是否配置了执行工具
      if (!toolId) {
        message.error('流水线未配置执行工具，请先编辑流水线设置执行工具')
        return
      }

      // 使用与列表页面相同的API调用方式
      const execution = await apiService.createExecution({
        pipeline_id: pipeline.id,
        cicd_tool_id: toolId,
        trigger_type: 'manual',
        parameters: {}
      })
      
      message.success('流水线执行已启动')
      console.log('执行ID:', execution.id)
      
      // 关闭预览窗口
      setPreviewVisible(false)
      
      // 可以导航到执行详情页面
      // navigate(`/executions/${execution.id}`)
    } catch (error) {
      console.error('执行流水线失败:', error)
      const errorMessage = error instanceof Error ? error.message : '执行流水线失败'
      message.error(errorMessage)
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
        steps: steps.map((step, index) => {
          const stepParams = getStepParameters(step)
          return {
            name: step.name,
            step_type: step.step_type,
            description: step.description || '',
            parameters: stepParams,
            order: index + 1, // 重新排序，确保顺序正确
            is_active: true,
            git_credential: isAtomicStep(step) ? step.git_credential : null
            // 注意：不再传递独立的ansible字段，因为它们已经保存在parameters中
          }
        })
      }

      console.log('Saving pipeline with data:', updateData)
      console.log('Steps being sent:', updateData.steps)

      // 使用API服务保存流水线
      const updatedPipeline = await apiService.updatePipeline(pipeline.id, updateData)
      
      message.success('流水线保存成功')
      
      // 更新本地状态为服务器返回的最新数据
      if (updatedPipeline.steps && updatedPipeline.steps.length > 0) {
        setSteps(updatedPipeline.steps.sort((a, b) => a.order - b.order))
      } else if (updatedPipeline.atomic_steps && updatedPipeline.atomic_steps.length > 0) {
        // 兼容性处理
        setSteps(updatedPipeline.atomic_steps.sort((a, b) => a.order - b.order))
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
      case 'ansible':
        return '🤖'
      case 'notify':
        return '📢'
      case 'custom':
        return '🔧'
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
          <Button icon={<EyeOutlined />} onClick={handlePreviewPipeline}>
            预览Pipeline
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
                  
                  {/* Ansible步骤特殊显示 */}
                  {step.step_type === 'ansible' && (() => {
                    const ansibleConfig = getStepAnsibleConfig(step)
                    return (
                      <div style={{ marginTop: 8 }}>
                        <Text strong>Ansible配置:</Text>
                        <div style={{ marginLeft: 16, marginTop: 4 }}>
                          {ansibleConfig.playbook_id && (
                            <div><Text type="secondary">Playbook ID: </Text>{ansibleConfig.playbook_id}</div>
                          )}
                          {ansibleConfig.inventory_id && (
                            <div><Text type="secondary">Inventory ID: </Text>{ansibleConfig.inventory_id}</div>
                          )}
                          {ansibleConfig.credential_id && (
                            <div><Text type="secondary">Credential ID: </Text>{ansibleConfig.credential_id}</div>
                          )}
                        </div>
                      </div>
                    )
                  })()}
                  
                  {/* 显示清理后的参数（不包含ansible字段） */}
                  {(() => {
                    const stepParams = getStepParameters(step)
                    const displayParams = { ...stepParams }
                    if (step.step_type === 'ansible') {
                      delete displayParams.playbook_id
                      delete displayParams.inventory_id
                      delete displayParams.credential_id
                    }
                    return Object.keys(displayParams).length > 0 && (
                      <div style={{ marginTop: 8 }}>
                        <Text strong>参数: </Text>
                        <Text code>{JSON.stringify(displayParams, null, 2)}</Text>
                      </div>
                    )
                  })()}
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
            <Button onClick={() => setStepFormVisible(false)}>关闭</Button>
            <Button type="primary" onClick={handleStepSubmit}>
              {editingStep ? '更新步骤' : '添加步骤'}
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

          {/* Git凭据选择 - 仅在代码拉取步骤显示 */}
          {selectedStepType === 'fetch_code' && (
            <Form.Item
              name="git_credential_id"
              label={
                <Space>
                  <span>Git认证凭据</span>
                  <Button 
                    type="link" 
                    size="small"
                    onClick={() => {
                      // 打开系统设置中的Git凭据管理
                      window.open('/settings?module=git-credentials', '_blank')
                    }}
                  >
                    管理凭据
                  </Button>
                </Space>
              }
              tooltip="选择用于拉取代码的Git认证凭据，如果不选择则使用公开仓库或默认认证"
            >
              <Select 
                placeholder="选择Git凭据（可选）"
                allowClear
                optionLabelProp="label"
                notFoundContent={
                  <div style={{ textAlign: 'center', padding: '20px' }}>
                    <Text type="secondary">暂无Git凭据</Text>
                    <br />
                    <Button 
                      type="link" 
                      size="small"
                      onClick={() => {
                        window.open('/settings?module=git-credentials', '_blank')
                      }}
                    >
                      去创建凭据
                    </Button>
                  </div>
                }
              >
                {gitCredentials.map(credential => (
                  <Select.Option 
                    key={credential.id} 
                    value={credential.id}
                    label={credential.name}
                  >
                    <div style={{ lineHeight: '1.4', padding: '4px 0' }}>
                      <div style={{ fontWeight: 500, marginBottom: 2 }}>
                        {credential.name}
                      </div>
                      <div style={{ 
                        fontSize: 12, 
                        color: '#999',
                        whiteSpace: 'normal',
                        wordBreak: 'break-word',
                        lineHeight: '1.3'
                      }}>
                        {credential.platform_display} - {credential.server_url}
                      </div>
                    </div>
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          )}
          
          {/* Ansible资源选择 - 仅在ansible步骤显示 */}
          {selectedStepType === 'ansible' && (
            <>
              <Form.Item
                name="ansible_playbook_id"
                label={
                  <Space>
                    <span>Ansible Playbook</span>
                    <Button 
                      type="link" 
                      size="small"
                      onClick={() => {
                        window.open('/ansible?tab=playbooks', '_blank')
                      }}
                    >
                      管理Playbook
                    </Button>
                  </Space>
                }
                tooltip="选择要执行的Ansible Playbook"
                rules={[{ required: true, message: '请选择Ansible Playbook' }]}
              >
                <Select 
                  placeholder="选择Ansible Playbook"
                  optionLabelProp="label"
                  notFoundContent={
                    <div style={{ textAlign: 'center', padding: '20px' }}>
                      <Text type="secondary">暂无Playbook</Text>
                      <br />
                      <Button 
                        type="link" 
                        size="small"
                        onClick={() => {
                          window.open('/ansible?tab=playbooks', '_blank')
                        }}
                      >
                        去创建Playbook
                      </Button>
                    </div>
                  }
                >
                  {ansiblePlaybooks.map(playbook => (
                    <Select.Option 
                      key={playbook.id} 
                      value={playbook.id}
                      label={playbook.name}
                    >
                      <div style={{ lineHeight: '1.4', padding: '4px 0' }}>
                        <div style={{ fontWeight: 500, marginBottom: 2 }}>
                          {playbook.name}
                        </div>
                        <div style={{ 
                          fontSize: 12, 
                          color: '#999',
                          whiteSpace: 'normal',
                          wordBreak: 'break-word',
                          lineHeight: '1.3'
                        }}>
                          {playbook.description || '无描述'}
                        </div>
                      </div>
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="ansible_inventory_id"
                label={
                  <Space>
                    <span>Ansible Inventory</span>
                    <Button 
                      type="link" 
                      size="small"
                      onClick={() => {
                        window.open('/ansible?tab=inventories', '_blank')
                      }}
                    >
                      管理Inventory
                    </Button>
                  </Space>
                }
                tooltip="选择目标主机清单（可选）"
              >
                <Select 
                  placeholder="选择Ansible Inventory（可选）"
                  allowClear
                  optionLabelProp="label"
                  notFoundContent={
                    <div style={{ textAlign: 'center', padding: '20px' }}>
                      <Text type="secondary">暂无Inventory</Text>
                      <br />
                      <Button 
                        type="link" 
                        size="small"
                        onClick={() => {
                          window.open('/ansible?tab=inventories', '_blank')
                        }}
                      >
                        去创建Inventory
                      </Button>
                    </div>
                  }
                >
                  {ansibleInventories.map(inventory => (
                    <Select.Option 
                      key={inventory.id} 
                      value={inventory.id}
                      label={inventory.name}
                    >
                      <div style={{ lineHeight: '1.4', padding: '4px 0' }}>
                        <div style={{ fontWeight: 500, marginBottom: 2 }}>
                          {inventory.name}
                        </div>
                        <div style={{ 
                          fontSize: 12, 
                          color: '#999',
                          whiteSpace: 'normal',
                          wordBreak: 'break-word',
                          lineHeight: '1.3'
                        }}>
                          {inventory.description || '无描述'}
                        </div>
                      </div>
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="ansible_credential_id"
                label={
                  <Space>
                    <span>Ansible Credential</span>
                    <Button 
                      type="link" 
                      size="small"
                      onClick={() => {
                        window.open('/ansible?tab=credentials', '_blank')
                      }}
                    >
                      管理Credential
                    </Button>
                  </Space>
                }
                tooltip="选择SSH认证凭据（可选）"
              >
                <Select 
                  placeholder="选择Ansible Credential（可选）"
                  allowClear
                  optionLabelProp="label"
                  notFoundContent={
                    <div style={{ textAlign: 'center', padding: '20px' }}>
                      <Text type="secondary">暂无Credential</Text>
                      <br />
                      <Button 
                        type="link" 
                        size="small"
                        onClick={() => {
                          window.open('/ansible?tab=credentials', '_blank')
                        }}
                      >
                        去创建Credential
                      </Button>
                    </div>
                  }
                >
                  {ansibleCredentials.map(credential => (
                    <Select.Option 
                      key={credential.id} 
                      value={credential.id}
                      label={credential.name}
                    >
                      <div style={{ lineHeight: '1.4', padding: '4px 0' }}>
                        <div style={{ fontWeight: 500, marginBottom: 2 }}>
                          {credential.name}
                        </div>
                        <div style={{ 
                          fontSize: 12, 
                          color: '#999',
                          whiteSpace: 'normal',
                          wordBreak: 'break-word',
                          lineHeight: '1.3'
                        }}>
                          {credential.username} - {credential.credential_type}
                        </div>
                      </div>
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </>
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

      {/* Pipeline预览组件 */}
      {pipeline && (
        <PipelinePreview
          visible={previewVisible}
          pipeline={pipeline}
          steps={steps.map(normalizeStepForDisplay)}
          onClose={() => setPreviewVisible(false)}
          onExecute={handleExecuteFromPreview}
        />
      )}
    </Drawer>
  )
}

export default PipelineEditor