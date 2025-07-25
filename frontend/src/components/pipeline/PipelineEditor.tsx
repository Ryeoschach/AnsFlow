import React, { useState, useEffect } from 'react'
import { 
  Space, 
  message, 
  Typography,
  Drawer,
  Form,
  Modal,
  Button,
  Dropdown
} from 'antd'
import { 
  SettingOutlined,
  EyeOutlined,
  PlusOutlined,
  SaveOutlined,
  ThunderboltOutlined,
  ShareAltOutlined,
  BarChartOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  MoreOutlined
} from '@ant-design/icons'
import { 
  AtomicStep, 
  Pipeline, 
  GitCredential, 
  PipelineStep, 
  EnhancedPipelineStep,
  ParallelGroup,
  ValidationResult
} from '../../types'
import apiService from '../../services/api'
import PipelineStepList from './PipelineStepList'
import PipelineStepForm from './PipelineStepForm'
import PipelineInfoForm from './PipelineInfoForm'
import PipelineToolbar from './PipelineToolbar'
import PipelinePreview from './PipelinePreview'
import WorkflowStepFormNew from './WorkflowStepFormNew'
import ParallelGroupManager from './ParallelGroupManager'
import SimpleParallelGroupManager from './SimpleParallelGroupManager'
import WorkflowAnalyzerEnhanced from './WorkflowAnalyzerEnhanced'
import ExecutionRecovery from './ExecutionRecovery'
import WorkflowValidation from './WorkflowValidation'

const { Text } = Typography

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
    
    // 如果是Docker步骤，从独立字段构建Docker参数
    if (step.step_type?.startsWith('docker_')) {
      return {
        ...parameters,
        image: step.docker_image,
        tag: step.docker_tag,
        registry_id: step.docker_registry,
        // 注意：PipelineStep 模型中可能没有 docker_project 字段，
        // 所以项目ID可能存储在parameters中
        ...(step.docker_config && { docker_config: step.docker_config })
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
      ansible_credential: step.ansible_credential,
      parallel_group: step.parallel_group || ''  // 添加并行组字段
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
  // Docker 步骤类型
  { value: 'docker_build', label: 'Docker Build', description: '构建 Docker 镜像' },
  { value: 'docker_run', label: 'Docker Run', description: '运行 Docker 容器' },
  { value: 'docker_push', label: 'Docker Push', description: '推送镜像到注册表' },
  { value: 'docker_pull', label: 'Docker Pull', description: '从注册表拉取镜像' },
  // Kubernetes 步骤类型
  { value: 'k8s_deploy', label: 'Kubernetes Deploy', description: '部署应用到 K8s 集群' },
  { value: 'k8s_scale', label: 'Kubernetes Scale', description: '扩缩容 K8s 部署' },
  { value: 'k8s_delete', label: 'Kubernetes Delete', description: '删除 K8s 资源' },
  { value: 'k8s_wait', label: 'Kubernetes Wait', description: '等待 K8s 资源状态' },
  { value: 'k8s_exec', label: 'Kubernetes Exec', description: '在 Pod 中执行命令' },
  { value: 'k8s_logs', label: 'Kubernetes Logs', description: '获取 Pod 日志' },
  // 其他步骤类型
  { value: 'approval', label: '手动审批', description: '需要人工审批才能继续执行' },
  { value: 'condition', label: '条件分支', description: '根据条件决定是否执行后续步骤' },
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
  
  // 添加Docker和Kubernetes资源状态
  const [dockerRegistries, setDockerRegistries] = useState<any[]>([])
  const [k8sClusters, setK8sClusters] = useState<any[]>([])
  const [k8sNamespaces, setK8sNamespaces] = useState<any[]>([])
  
  // 高级工作流功能状态
  const [parallelGroups, setParallelGroups] = useState<ParallelGroup[]>([])
  const [parallelGroupManagerVisible, setParallelGroupManagerVisible] = useState(false)
  const [workflowAnalyzerVisible, setWorkflowAnalyzerVisible] = useState(false)
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false)
  const [workflowStepFormVisible, setWorkflowStepFormVisible] = useState(false)
  const [editingEnhancedStep, setEditingEnhancedStep] = useState<EnhancedPipelineStep | null>(null)
  
  // 执行恢复功能状态
  const [executionRecoveryVisible, setExecutionRecoveryVisible] = useState(false)
  const [currentExecution, setCurrentExecution] = useState<any>(null)
  
  // 工作流验证状态
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null)
  const [showValidationPanel, setShowValidationPanel] = useState(false)

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
          
          // 加载并行组数据
          try {
            const parallelGroupsData = await apiService.getParallelGroups(pipeline.id)
            console.log('Loaded parallel groups:', parallelGroupsData.length, 'groups')
            setParallelGroups(parallelGroupsData)
          } catch (parallelGroupError) {
            console.error('Failed to load parallel groups:', parallelGroupError)
            // 并行组加载失败不影响主流程，设置为空数组
            setParallelGroups([])
          }
          
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

      // 获取Docker和Kubernetes资源
      fetchDockerK8sResources()
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
      setDockerRegistries([])
      setK8sClusters([])
      setK8sNamespaces([])
      // 清理高级工作流状态
      setParallelGroups([])
      setParallelGroupManagerVisible(false)
      setWorkflowAnalyzerVisible(false)
      setShowAdvancedOptions(false)
      setWorkflowStepFormVisible(false)
      setEditingEnhancedStep(null)
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

  // 获取Docker和Kubernetes资源
  const fetchDockerK8sResources = async () => {
    try {
      // 临时使用模拟数据，实际API需要后端提供
      const mockRegistries = [
        { id: 1, name: 'Docker Hub', url: 'https://registry-1.docker.io', username: '', description: '官方Docker Hub' },
        { id: 2, name: '阿里云容器镜像', url: 'registry.cn-hangzhou.aliyuncs.com', username: '', description: '阿里云ACR' }
      ]
      const mockClusters = [
        { id: 1, name: '开发集群', endpoint: 'https://dev-k8s.example.com', description: '开发环境K8s集群' },
        { id: 2, name: '生产集群', endpoint: 'https://prod-k8s.example.com', description: '生产环境K8s集群' }
      ]
      const mockNamespaces = [
        { id: 1, name: 'default', cluster_id: 1, description: '默认命名空间' },
        { id: 2, name: 'development', cluster_id: 1, description: '开发命名空间' },
        { id: 3, name: 'production', cluster_id: 2, description: '生产命名空间' }
      ]
      
      setDockerRegistries(mockRegistries)
      setK8sClusters(mockClusters)
      setK8sNamespaces(mockNamespaces)
    } catch (error) {
      console.error('Failed to fetch docker/k8s resources:', error)
      // 设置空数组作为兜底
      setDockerRegistries([])
      setK8sClusters([])
      setK8sNamespaces([])
    }
  }

  // 当pipeline内容变化时不自动更新steps，避免污染编辑中的内容
  // 用户需要手动重新打开编辑器来获取最新数据

  // 高级工作流功能处理函数
  const handleWorkflowStepEdit = (step: PipelineStep | AtomicStep) => {
    // 将普通步骤转换为增强步骤
    const enhancedStep: EnhancedPipelineStep = {
      ...step,
      condition: undefined,
      parallel_group_id: undefined,
      approval_config: undefined,
      retry_policy: undefined,
      notification_config: undefined
    }
    setEditingEnhancedStep(enhancedStep)
    setWorkflowStepFormVisible(true)
  }

  const handleWorkflowStepSave = async (enhancedStep: EnhancedPipelineStep) => {
    try {
      // 更新本地状态
      setSteps(prevSteps => 
        prevSteps.map(step => 
          step.id === enhancedStep.id ? enhancedStep : step
        )
      )

      // 持久化到后端
      if (pipeline) {
        const advancedConfig = {
          condition: enhancedStep.condition,
          parallel_group_id: enhancedStep.parallel_group_id,
          approval_config: enhancedStep.approval_config,
          retry_policy: enhancedStep.retry_policy,
          notification_config: enhancedStep.notification_config
        }

        await apiService.updateStepAdvancedConfig(
          pipeline.id,
          enhancedStep.id,
          advancedConfig
        )

        message.success('高级配置已保存并同步到服务器')
      } else {
        message.success('高级配置已保存（将在保存流水线时同步）')
      }

      setWorkflowStepFormVisible(false)
      setEditingEnhancedStep(null)
    } catch (error) {
      console.error('Failed to save advanced config:', error)
      message.error('高级配置保存失败')
    }
  }

  const handleParallelGroupSave = async (groups: ParallelGroup[]) => {
    try {
      if (!pipeline) {
        message.error('请先选择流水线')
        return
      }

      console.log('🔄 开始保存并行组:', groups.length, '个组')
      console.log('📊 当前并行组状态:', groups)

      // 数据验证
      const safeGroups = Array.isArray(groups) ? groups : []
      const safeParallelGroups = Array.isArray(parallelGroups) ? parallelGroups : []
      
      // 验证步骤数据
      if (!Array.isArray(steps) || steps.length === 0) {
        message.error('没有可分配的步骤')
        return
      }

      // 验证并行组数据
      for (const group of safeGroups) {
        if (!group.id || !group.name) {
          message.error('并行组数据不完整')
          return
        }
        
        if (group.steps && group.steps.length > 0) {
          // 验证步骤是否存在
          const invalidSteps = group.steps.filter(stepId => !steps.find(s => s.id === stepId))
          if (invalidSteps.length > 0) {
            message.error(`并行组 ${group.name} 中包含不存在的步骤: ${invalidSteps.join(', ')}`)
            return
          }
        }
      }

      // 1. 保存并行组到后端
      console.log('💾 第一步：保存并行组到后端...')
      const savePromises = safeGroups.map(async (group) => {
        const groupWithPipeline = {
          ...group,
          pipeline: pipeline.id
        }

        console.log('💾 处理并行组:', group.id, group.name, '包含步骤:', group.steps)

        try {
          // 判断是否为新创建的组
          const isNewGroup = group.id.startsWith('parallel_') && !safeParallelGroups.find(existing => existing.id === group.id)
          
          if (isNewGroup) {
            console.log('🆕 创建新并行组:', group.id)
            return await apiService.createParallelGroup(groupWithPipeline)
          } else {
            console.log('📝 更新现有并行组:', group.id)
            return await apiService.updateParallelGroup(group.id, groupWithPipeline)
          }
        } catch (error: any) {
          console.error('❌ 保存并行组失败:', group.id, error)
          throw new Error(`保存并行组 ${group.name} 失败: ${error?.message || '未知错误'}`)
        }
      })

      // 2. 删除本地已删除但后端仍存在的组
      const deletedGroups = safeParallelGroups.filter(
        existing => !safeGroups.find(group => group.id === existing.id)
      )
      console.log('🗑️ 需要删除的并行组:', deletedGroups.length, '个')
      
      const deletePromises = deletedGroups.map(async (group) => {
        console.log('🗑️ 删除并行组:', group.id)
        try {
          return await apiService.deleteParallelGroup(group.id)
        } catch (error) {
          console.error('❌ 删除并行组失败:', group.id, error)
          // 删除失败不阻塞整个流程
          return null
        }
      })

      // 3. 等待并行组操作完成
      console.log('⏳ 等待并行组操作完成...')
      const savedGroups = await Promise.all(savePromises)
      await Promise.all(deletePromises)
      
      console.log('✅ 并行组操作完成:', savedGroups.length, '个组已保存')

      // 4. 同步更新步骤的并行组关联
      console.log('🔗 第二步：同步步骤的并行组关联...')
      
      // 创建步骤的深拷贝并重新分配并行组
      const updatedSteps = steps.map(step => {
        // 查找步骤属于哪个并行组
        const belongsToGroup = safeGroups.find(group => 
          group.steps && Array.isArray(group.steps) && group.steps.includes(step.id)
        )
        
        return {
          ...step,
          parallel_group: belongsToGroup ? belongsToGroup.id : undefined
        }
      })

      console.log('� 步骤并行组分配结果:')
      updatedSteps.forEach(step => {
        if (step.parallel_group) {
          console.log(`  - 步骤 ${step.name} (${step.id}) → 并行组 ${step.parallel_group}`)
        }
      })

      // 5. 保存更新后的步骤到后端
      console.log('💾 第三步：保存步骤的并行组关联到后端...')
      
      try {
        const pipelineInfo = await pipelineForm.validateFields().catch(() => ({
          name: pipeline.name,
          description: pipeline.description,
          execution_mode: pipeline.execution_mode,
          execution_tool: pipeline.execution_tool,
          tool_job_name: pipeline.tool_job_name,
          is_active: pipeline.is_active
        }))

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
            const stepParams = getStepParameters(step)
            return {
              id: step.id,
              name: step.name,
              step_type: step.step_type,
              description: step.description || '',
              parameters: stepParams,
              order: index + 1,
              is_active: true,
              parallel_group: step.parallel_group, // 保存并行组关联
              git_credential: isAtomicStep(step) ? step.git_credential : null
            }
          })
        }

        console.log('🚀 保存包含并行组关联的流水线数据...')
        console.log('📊 准备保存的步骤数据:')
        updateData.steps.forEach(step => {
          if (step.parallel_group) {
            console.log(`  - 步骤 ${step.name} (ID: ${step.id}) → 并行组: ${step.parallel_group}`)
          } else {
            console.log(`  - 步骤 ${step.name} (ID: ${step.id}) → 无并行组`)
          }
        })
        
        const updatedPipeline = await apiService.updatePipeline(pipeline.id, updateData)
        
        // 6. 更新本地状态
        if (updatedPipeline.steps && updatedPipeline.steps.length > 0) {
          const sortedSteps = updatedPipeline.steps.sort((a, b) => a.order - b.order)
          setSteps(sortedSteps)
          console.log('✅ 本地步骤状态已更新:', sortedSteps.length, '个步骤')
        }
        
        // 更新并行组状态
        setParallelGroups(safeGroups)
        console.log('✅ 本地并行组状态已更新:', safeGroups.length, '个组')
        
        // 7. 关闭对话框并显示成功消息
        setParallelGroupManagerVisible(false)
        console.log('🎉 并行组保存完成!')
        message.success(`并行组配置已保存，共 ${safeGroups.length} 个组，步骤关联已同步`)
        
        // 8. 可选：刷新数据确保一致性
        setTimeout(async () => {
          try {
            const refreshedGroups = await apiService.getParallelGroups(pipeline.id)
            setParallelGroups(refreshedGroups)
            console.log('🔄 并行组数据已刷新')
          } catch (error) {
            console.warn('⚠️ 刷新并行组数据失败:', error)
          }
        }, 1000)
        
      } catch (error: any) {
        console.error('❌ 保存流水线失败:', error)
        message.error('保存流水线失败: ' + (error?.message || '未知错误'))
        throw error
      }

    } catch (error: any) {
      console.error('❌ 并行组保存失败:', error)
      message.error('并行组保存失败: ' + (error?.message || '未知错误'))
    }
  }

  const handleAdvancedOptionsToggle = () => {
    setShowAdvancedOptions(!showAdvancedOptions)
  }

  const handleParallelGroupManager = () => {
    setParallelGroupManagerVisible(true)
  }

  const handleWorkflowAnalyzer = () => {
    setWorkflowAnalyzerVisible(true)
  }

  const handleExecutionRecovery = async () => {
    if (!pipeline) {
      message.error('请先选择流水线')
      return
    }

    try {
      // 获取最近的失败执行
      const executions = await apiService.getExecutions(pipeline.id)
      const failedExecution = executions.find((exec: any) => exec.status === 'failed')
      
      if (!failedExecution) {
        message.warning('没有找到失败的执行记录')
        return
      }

      setCurrentExecution(failedExecution)
      setExecutionRecoveryVisible(true)
    } catch (error) {
      console.error('Failed to load executions:', error)
      message.error('加载执行记录失败')
    }
  }

  const handleExecutionResumeSuccess = (resumedExecution: any) => {
    setExecutionRecoveryVisible(false)
    setCurrentExecution(null)
    message.success(`执行已恢复，执行ID: ${resumedExecution.id}`)
  }

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
    } else if (step.step_type?.startsWith('docker_')) {
      // 如果是Docker步骤，从步骤字段和参数中提取Docker相关字段
      console.log('🐳 Loading Docker step for editing:', {
        stepType: step.step_type,
        originalStep: step,
        stepParams: stepParams
      })
      
      // 从步骤直接字段获取Docker配置（PipelineStep模型字段）
      formValues.docker_image = isPipelineStep(step) ? step.docker_image : stepParams.image
      formValues.docker_tag = isPipelineStep(step) ? (step.docker_tag || 'latest') : (stepParams.tag || 'latest')
      formValues.docker_registry = isPipelineStep(step) ? step.docker_registry : stepParams.registry_id
      // 添加项目回填支持（从参数中获取）
      formValues.docker_project = stepParams.project_id
      
      // 从docker_config字段或参数中获取配置
      const dockerConfig = isPipelineStep(step) ? step.docker_config : stepParams.docker_config
      if (dockerConfig) {
        formValues.docker_config = dockerConfig
      }
      
      // 清理参数中的Docker字段，避免重复显示
      const cleanParameters = { ...stepParams }
      delete cleanParameters.image
      delete cleanParameters.tag
      delete cleanParameters.registry_id
      delete cleanParameters.project_id
      delete cleanParameters.docker_config
      delete cleanParameters.dockerfile
      delete cleanParameters.context
      delete cleanParameters.build_args
      delete cleanParameters.ports
      delete cleanParameters.volumes
      delete cleanParameters.env_vars
      
      // 只有在清理后的参数不为空时才显示
      formValues.parameters = Object.keys(cleanParameters).length > 0 
        ? JSON.stringify(cleanParameters, null, 2) 
        : '{}'
      
      console.log('🐳 Docker step form values prepared:', {
        docker_image: formValues.docker_image,
        docker_tag: formValues.docker_tag,
        docker_registry: formValues.docker_registry,
        docker_project: formValues.docker_project,
        docker_config: formValues.docker_config,
        cleanParameters: cleanParameters
      })
    } else {
      // 非ansible和Docker步骤直接使用原始参数
      formValues.parameters = JSON.stringify(stepParams, null, 2)
    }

    form.setFieldsValue(formValues)
    
    // 对于Docker步骤，延迟强制更新表单值以确保覆盖initialValue
    if (step.step_type?.startsWith('docker_')) {
      setTimeout(() => {
        console.log('🔄 强制更新Docker表单值:', formValues)
        form.setFieldsValue(formValues)
        // 强制重新渲染表单
        form.validateFields().catch(() => {})
      }, 100)
    }
    
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

      // 处理Docker步骤的特殊字段
      if (values.step_type?.startsWith('docker_')) {
        // 将Docker相关字段添加到parameters中
        parameters = {
          ...parameters,
          // 核心参数
          image: values.docker_image,
          tag: values.docker_tag || 'latest',
          // 注册表关联
          registry_id: values.docker_registry,
          // 项目关联 - 新增项目选择支持
          project_id: values.docker_project,
          // 其他Docker特定参数
          ...(values.docker_dockerfile && { dockerfile: values.docker_dockerfile }),
          ...(values.docker_context && { context: values.docker_context }),
          ...(values.docker_build_args && { build_args: values.docker_build_args }),
          ...(values.docker_ports && { ports: values.docker_ports }),
          ...(values.docker_volumes && { volumes: values.docker_volumes }),
          ...(values.docker_env_vars && { env_vars: values.docker_env_vars })
        }
      }

      const stepData: StepFormData = {
        ...values,
        parameters,
        // 同时保存为独立字段（兼容性）
        ansible_playbook: values.step_type === 'ansible' ? values.ansible_playbook_id : undefined,
        ansible_inventory: values.step_type === 'ansible' ? values.ansible_inventory_id : undefined,
        ansible_credential: values.step_type === 'ansible' ? values.ansible_credential_id : undefined,
        // Docker步骤的兼容性字段
        docker_registry: values.step_type?.startsWith('docker_') ? values.docker_registry : undefined,
        docker_project: values.step_type?.startsWith('docker_') ? values.docker_project : undefined
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
              step_type: stepData.step_type as any,
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
          step_type: stepData.step_type as any,
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

      // 如果是本地执行模式且没有配置工具，自动获取本地执行器
      if (!toolId && pipeline.execution_mode === 'local') {
        try {
          const localTool = tools.find(tool => tool.tool_type === 'local')
          if (localTool) {
            toolId = localTool.id
          } else {
            message.error('未找到本地执行器工具，请联系系统管理员')
            return
          }
        } catch (error) {
          console.error('Failed to get local executor:', error)
          message.error('获取本地执行器失败')
          return
        }
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
            git_credential: isAtomicStep(step) ? step.git_credential : null,
            // 🔥 关键修复：保留并行组关联
            parallel_group: isPipelineStep(step) ? (step.parallel_group || '') : ''
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
      case 'approval':
        return '✋'
      case 'condition':
        return '🔀'
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

  // 响应式计算函数
  const getDrawerWidth = () => {
    const screenWidth = typeof window !== 'undefined' ? window.innerWidth : 1200
    if (screenWidth < 768) {
      return '100%' // 小屏幕全屏显示
    } else if (screenWidth < 1024) {
      return '90%' // 中等屏幕90%
    } else if (screenWidth < 1440) {
      return '85%' // 大屏幕85%
    } else {
      return '80%' // 超大屏幕80%
    }
  }

  // 现代化头部组件
  const renderModernHeader = () => {
    const screenWidth = typeof window !== 'undefined' ? window.innerWidth : 1200
    const pipelineName = pipeline ? pipeline.name : '新建流水线'
    const isMobile = screenWidth < 768
    const isTablet = screenWidth >= 768 && screenWidth < 1024
    
    return (
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        padding: isMobile ? '24px 16px 16px 24px' : '36px 20px 20px 32px',
        margin: '-24px -24px 0 -24px',
        borderRadius: '0 0 12px 12px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
      }}>
        {/* 标题行 */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginBottom: isMobile ? '12px' : '16px',
          marginLeft: isMobile ? '0' : '8px' // 与下面的卡片标题对齐
        }}>
          <div style={{
            background: 'rgba(255,255,255,0.2)',
            padding: '8px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <SettingOutlined style={{ fontSize: isMobile ? '16px' : '18px' }} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <h3 style={{
              margin: 0,
              fontSize: isMobile ? '16px' : '18px',
              fontWeight: 600,
              color: 'white',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              {pipelineName}
            </h3>
            <p style={{
              margin: 0,
              fontSize: isMobile ? '12px' : '14px',
              opacity: 0.8,
              color: 'white'
            }}>
              {pipeline ? '编辑流水线配置' : '创建新的流水线'}
            </p>
          </div>
        </div>
        
        {/* 工具栏 */}
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: isMobile ? '8px' : '12px',
          alignItems: 'center',
          justifyContent: 'flex-end', // 右对齐按钮组
          marginRight: isMobile ? '0' : '35px' // 与下面的步骤卡片按钮对齐
        }}>
          {/* 主要操作按钮 */}
          <div style={{
            display: 'flex',
            gap: isMobile ? '6px' : '8px',
            flexWrap: 'wrap'
          }}>
            <Button 
              size={isMobile ? 'small' : 'middle'}
              style={{ 
                background: 'rgba(255,255,255,0.2)', 
                borderColor: 'rgba(255,255,255,0.3)',
                color: 'white'
              }}
              onClick={onClose}
            >
              取消
            </Button>
            <Button 
              size={isMobile ? 'small' : 'middle'}
              style={{ 
                background: 'rgba(255,255,255,0.2)', 
                borderColor: 'rgba(255,255,255,0.3)',
                color: 'white'
              }}
              icon={<SettingOutlined />} 
              onClick={handleEditPipelineInfo}
            >
              {isMobile ? '编辑' : '编辑信息'}
            </Button>
            <Button 
              size={isMobile ? 'small' : 'middle'}
              style={{ 
                background: 'rgba(255,255,255,0.2)', 
                borderColor: 'rgba(255,255,255,0.3)',
                color: 'white'
              }}
              icon={<EyeOutlined />} 
              onClick={handlePreviewPipeline}
            >
              {isMobile ? '预览' : '预览Pipeline'}
            </Button>
            <Button 
              size={isMobile ? 'small' : 'middle'}
              style={{ 
                background: 'rgba(255,255,255,0.2)', 
                borderColor: 'rgba(255,255,255,0.3)',
                color: 'white'
              }}
              icon={<PlusOutlined />} 
              onClick={handleAddStep}
            >
              {isMobile ? '添加' : '添加步骤'}
            </Button>
          </div>
          
          {/* 分隔线 */}
          {!isMobile && (
            <div style={{
              width: '1px',
              height: '24px',
              background: 'rgba(255,255,255,0.3)'
            }} />
          )}
          
          {/* 高级功能按钮组 */}
          <div style={{
            display: 'flex',
            gap: isMobile ? '6px' : '8px',
            flexWrap: 'wrap'
          }}>
            <Button 
              size={isMobile ? 'small' : 'middle'}
              type={showAdvancedOptions ? "primary" : "default"}
              style={showAdvancedOptions ? {} : { 
                background: 'rgba(255,255,255,0.15)', 
                borderColor: 'rgba(255,255,255,0.3)',
                color: 'white'
              }}
              icon={<ThunderboltOutlined />} 
              onClick={handleAdvancedOptionsToggle}
            >
              {isMobile ? '高级' : '高级功能'}
            </Button>
            {!isMobile && (
              <>
                <Button 
                  size="middle"
                  style={{ 
                    background: 'rgba(255,255,255,0.15)', 
                    borderColor: 'rgba(255,255,255,0.3)',
                    color: 'white'
                  }}
                  icon={<ShareAltOutlined />} 
                  onClick={handleParallelGroupManager}
                >
                  并行组
                </Button>
                <Button 
                  size="middle"
                  style={{ 
                    background: 'rgba(255,255,255,0.15)', 
                    borderColor: 'rgba(255,255,255,0.3)',
                    color: 'white'
                  }}
                  icon={<BarChartOutlined />} 
                  onClick={handleWorkflowAnalyzer}
                >
                  分析
                </Button>
                <Button 
                  size="middle"
                  style={{ 
                    background: 'rgba(255,255,255,0.15)', 
                    borderColor: 'rgba(255,255,255,0.3)',
                    color: 'white'
                  }}
                  icon={<ReloadOutlined />} 
                  onClick={handleExecutionRecovery}
                >
                  恢复
                </Button>
                <Button 
                  size="middle"
                  style={{ 
                    background: 'rgba(255,255,255,0.15)', 
                    borderColor: 'rgba(255,255,255,0.3)',
                    color: 'white'
                  }}
                  icon={<CheckCircleOutlined />} 
                  onClick={() => setShowValidationPanel(!showValidationPanel)}
                >
                  {showValidationPanel ? '隐藏验证' : '验证'}
                </Button>
              </>
            )}
            {isMobile && (
              <Dropdown 
                menu={{ 
                  items: [
                    {
                      key: 'parallel',
                      label: '并行组管理',
                      icon: <ShareAltOutlined />,
                      onClick: handleParallelGroupManager
                    },
                    {
                      key: 'analyzer',
                      label: '工作流分析',
                      icon: <BarChartOutlined />,
                      onClick: handleWorkflowAnalyzer
                    },
                    {
                      key: 'recovery',
                      label: '执行恢复',
                      icon: <ReloadOutlined />,
                      onClick: handleExecutionRecovery
                    },
                    {
                      key: 'validation',
                      label: showValidationPanel ? '隐藏验证' : '工作流验证',
                      icon: <CheckCircleOutlined />,
                      onClick: () => setShowValidationPanel(!showValidationPanel)
                    }
                  ]
                }}
                trigger={['click']}
                placement="bottomRight"
              >
                <Button 
                  size="small"
                  style={{ 
                    background: 'rgba(255,255,255,0.15)', 
                    borderColor: 'rgba(255,255,255,0.3)',
                    color: 'white'
                  }}
                  icon={<MoreOutlined />}
                >
                  更多
                </Button>
              </Dropdown>
            )}
          </div>
          
          {/* 分隔线 */}
          {!isMobile && (
            <div style={{
              width: '1px',
              height: '24px',
              background: 'rgba(255,255,255,0.3)'
            }} />
          )}
          
          {/* 保存按钮 */}
          <Button 
            size={isMobile ? 'small' : 'middle'}
            type="primary"
            style={{
              background: 'rgba(255,255,255,0.9)',
              borderColor: 'rgba(255,255,255,0.9)',
              color: '#667eea',
              fontWeight: 600,
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}
            icon={<SaveOutlined />} 
            onClick={handleSavePipeline}
          >
            {isMobile ? '保存' : '保存流水线'}
          </Button>
        </div>
      </div>
    )
  }

  return (
    <Drawer
      title={null}
      open={visible}
      onClose={onClose}
      width={getDrawerWidth()}
      placement="right"
      headerStyle={{ display: 'none' }}
      bodyStyle={{ padding: 0 }}
    >
      {/* 现代化自定义头部 */}
      {renderModernHeader()}
      
      {/* 主要内容区域 */}
      <div style={{ 
        padding: typeof window !== 'undefined' && window.innerWidth < 768 ? '16px' : '24px',
        paddingTop: '20px'
      }}>
        <PipelineStepList
          steps={steps}
          showAdvancedOptions={showAdvancedOptions}
          onAddStep={handleAddStep}
          onEditStep={handleEditStep}
          onDeleteStep={handleDeleteStep}
          onMoveStep={handleMoveStep}
          onWorkflowStepEdit={handleWorkflowStepEdit}
          getStepTypeLabel={getStepTypeLabel}
          getStepIcon={getStepIcon}
          getStepParameters={getStepParameters}
          getStepAnsibleConfig={getStepAnsibleConfig}
        />
      </div>

      <PipelineStepForm
        visible={stepFormVisible}
        form={form}
        editingStep={editingStep}
        selectedStepType={selectedStepType}
        showParameterDoc={showParameterDoc}
        gitCredentials={gitCredentials}
        ansiblePlaybooks={ansiblePlaybooks}
        ansibleInventories={ansibleInventories}
        ansibleCredentials={ansibleCredentials}
        dockerRegistries={dockerRegistries}
        k8sClusters={k8sClusters}
        k8sNamespaces={k8sNamespaces}
        stepTypes={STEP_TYPES}
        onClose={() => setStepFormVisible(false)}
        onSubmit={handleStepSubmit}
        onStepTypeChange={(value: string) => {
          setSelectedStepType(value)
          setShowParameterDoc(true)
          
          // 为特殊步骤类型提供自动配置提示
          if (value === 'approval') {
            message.info('审批步骤已选择，建议使用高级配置设置审批人员')
          } else if (value === 'condition') {
            message.info('条件步骤已选择，建议使用高级配置设置执行条件')
          }
        }}
        onToggleParameterDoc={() => setShowParameterDoc(!showParameterDoc)}
        onParameterSelect={(paramKey: string, paramValue: any) => {
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
        onCreateDockerRegistry={() => {
          message.info('正在跳转到Docker注册表管理页面...')
          window.open('/settings?module=docker-registries', '_blank')
        }}
        onCreateK8sCluster={() => {
          message.info('正在跳转到Kubernetes集群管理页面...')
          window.open('/settings?module=k8s-clusters', '_blank')
        }}
      />

      {/* 流水线基本信息编辑 */}
      <PipelineInfoForm
        visible={pipelineInfoVisible}
        form={pipelineForm}
        tools={tools}
        onClose={() => setPipelineInfoVisible(false)}
        onSubmit={handlePipelineInfoSubmit}
      />

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

      {/* 高级工作流功能组件 */}
      
      {/* 步骤高级配置组件 */}
      <WorkflowStepFormNew
        visible={workflowStepFormVisible}
        editingStep={editingEnhancedStep}
        availableSteps={steps as EnhancedPipelineStep[]}
        parallelGroups={parallelGroups}
        onClose={() => {
          setWorkflowStepFormVisible(false)
          setEditingEnhancedStep(null)
        }}
        onSave={handleWorkflowStepSave}
        onParallelGroupChange={setParallelGroups}
      />

      {/* 并行组管理组件 */}
      <ParallelGroupManager
        visible={parallelGroupManagerVisible}
        parallelGroups={parallelGroups}
        availableSteps={steps as EnhancedPipelineStep[]}
        onClose={() => setParallelGroupManagerVisible(false)}
        onChange={handleParallelGroupSave}
      />

      {/* 工作流分析组件 */}
      <WorkflowAnalyzerEnhanced
        visible={workflowAnalyzerVisible}
        steps={steps}
        parallelGroups={parallelGroups}
        onClose={() => setWorkflowAnalyzerVisible(false)}
      />

      {/* 执行恢复组件 */}
      <ExecutionRecovery
        visible={executionRecoveryVisible}
        execution={currentExecution}
        onClose={() => {
          setExecutionRecoveryVisible(false)
          setCurrentExecution(null)
        }}
        onResumeSuccess={handleExecutionResumeSuccess}
      />

      {/* 流水线验证组件 */}
      {showValidationPanel && (
        <div style={{ marginTop: 16 }}>
          <WorkflowValidation
            steps={steps as PipelineStep[]}
            onValidationComplete={setValidationResult}
            autoValidate={true}
          />
        </div>
      )}
    </Drawer>
  )
}

export default PipelineEditor