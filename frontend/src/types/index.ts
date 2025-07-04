// API 响应类型
export interface ApiResponse<T = any> {
  data: T
  success: boolean
  message?: string
  errors?: Record<string, string[]>
}

// 分页响应
export interface PaginatedResponse<T> {
  results: T[]
  count: number
  next: string | null
  previous: string | null
}

// 用户相关类型
export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  is_staff: boolean
  date_joined: string
  last_login?: string
}

// 认证类型
export interface AuthTokens {
  access: string
  refresh: string
}

export interface LoginCredentials {
  username: string
  password: string
}

// CI/CD 工具类型
export interface CICDTool {
  id: number
  name: string
  tool_type: 'jenkins' | 'gitlab' | 'github' | 'azure_devops'
  base_url: string
  username: string
  token?: string  // 前端不会收到实际token值
  has_token?: boolean  // 新增：指示是否已设置token
  config: Record<string, any>
  metadata: Record<string, any>
  status: string  // 数据库状态字段
  detailed_status?: string  // 详细状态
  is_active: boolean  // 计算得出的活跃状态
  health_status?: 'healthy' | 'unhealthy' | 'error' | 'pending'
  last_health_check?: string
  created_at: string
  updated_at: string
  project: number
}

// Tool 类型别名，用于兼容
export type Tool = CICDTool

// Git凭据类型
export interface GitCredential {
  id: number
  name: string
  platform: 'github' | 'gitlab' | 'gitee' | 'bitbucket' | 'azure_devops' | 'other'
  platform_display: string
  server_url: string
  credential_type: 'username_password' | 'ssh_key' | 'access_token' | 'oauth'
  credential_type_display: string
  username?: string
  email?: string
  description?: string
  is_active?: boolean
  last_test_at?: string
  last_test_result?: boolean
  has_credentials?: boolean
  has_password?: boolean
  has_ssh_key?: boolean
  created_by_username?: string
  created_at: string
  updated_at: string
  user: number
  // 兼容新字段名
  auth_type?: string
  auth_type_display?: string
}

// 流水线运行记录类型
export interface PipelineRun {
  id: number
  run_number: number
  status: string
  triggered_by: number
  trigger_type: string
  trigger_data: Record<string, any>
  started_at?: string
  completed_at?: string
  created_at: string
  artifacts: any[]
}

// 流水线类型
export interface Pipeline {
  id: number
  name: string
  description: string
  status: string
  is_active: boolean
  config?: Record<string, any>
  
  // 项目关联
  project: number
  project_name?: string
  created_by?: number
  created_by_username?: string
  
  // 新增：CI/CD工具关联
  execution_tool?: number | CICDTool
  execution_tool_name?: string
  execution_tool_type?: string
  tool_job_name?: string
  tool_job_config?: Record<string, any>
  execution_mode?: 'local' | 'remote' | 'hybrid'
  
  // 兼容字段
  tool?: number
  tool_name?: string
  tool_type?: string
  
  steps?: AtomicStep[]  // 详情API返回
  steps_count?: number  // 列表API返回
  runs?: PipelineRun[]  // 运行历史
  runs_count?: number
  
  metadata?: Record<string, any>
  created_at: string
  updated_at: string
  started_at?: string
  completed_at?: string
}

// 流水线工具映射类型
export interface PipelineToolMapping {
  id: number
  pipeline: number
  pipeline_name?: string
  tool: number
  tool_name?: string
  tool_type?: string
  external_job_id: string
  external_job_name: string
  auto_sync: boolean
  last_sync_at?: string
  sync_status: string
  created_at: string
  updated_at: string
}

// 原子步骤类型
export interface AtomicStep {
  id: number
  name: string
  step_type: string
  description?: string
  parameters: Record<string, any>
  order: number
  pipeline: number
  is_active: boolean
  created_at: string
  git_credential?: number | null  // Git凭据ID
}

// 步骤执行类型
export interface StepExecution {
  id: number
  atomic_step: number
  atomic_step_name: string
  external_id: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled' | 'skipped'
  status_display: string
  order: number
  logs: string
  output: Record<string, any>
  error_message: string
  started_at: string | null
  completed_at: string | null
  duration: string
  created_at: string
  updated_at: string
}

// 流水线执行类型
export interface PipelineExecution {
  id: number
  pipeline: number
  pipeline_name?: string
  cicd_tool?: number
  cicd_tool_name?: string
  cicd_tool_type?: string
  external_id?: string
  external_url?: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled' | 'timeout'
  status_display: string
  trigger_type: 'manual' | 'webhook' | 'schedule' | 'api'
  trigger_type_display: string
  triggered_by?: number
  triggered_by_username?: string
  definition: Record<string, any>
  parameters: Record<string, any>
  logs: string
  artifacts: any[]
  test_results: Record<string, any>
  result?: Record<string, any>  // 添加result字段用于存储步骤执行结果
  started_at?: string
  completed_at?: string
  duration?: string
  trigger_data: Record<string, any>
  step_executions: StepExecution[]  // 添加步骤执行列表
  created_at: string
  updated_at: string
}

// 执行日志类型
export interface ExecutionLog {
  id: number
  execution: number
  step_name: string
  log_level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
  message: string
  timestamp: string
  metadata?: Record<string, any>
}

// WebSocket 消息类型
export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export interface PipelineUpdateMessage extends WebSocketMessage {
  type: 'pipeline_update'
  data: {
    pipeline_id: string
    status: string
    progress?: number
    logs?: any[]
  }
}

export interface SystemNotification extends WebSocketMessage {
  type: 'system_notification'
  data: {
    title: string
    message: string
    level: 'info' | 'warning' | 'error' | 'success'
  }
}

// Jenkins 特定类型
export interface JenkinsJob {
  name: string
  url: string
  color: string
  buildable: boolean
  inQueue: boolean
  description?: string
  config?: Record<string, any>
  lastBuild?: {
    number?: number
    url?: string
    timestamp?: number
    result?: string
    duration?: number
  } | null
  healthReport?: Array<{
    description: string
    iconClassName: string
    iconUrl: string
    score: number
  }>
}

export interface JenkinsBuild {
  number: number
  url: string
  result: string
  timestamp: number
  duration: number
  description?: string
  building: boolean
}

export interface JenkinsQueueItem {
  id: number
  job_name: string
  job_url: string
  why: string
  blocked: boolean
  buildable: boolean
  in_queue_since: number
}

// 表单类型
export interface CreateToolForm {
  name: string
  tool_type: string
  base_url: string
  username: string
  token: string
  project: number
  description?: string
  config?: Record<string, any>
}

export interface CreatePipelineForm {
  name: string
  description: string
  tool: number
  steps: CreateStepForm[]
}

export interface CreateStepForm {
  name: string
  step_type: string
  parameters: Record<string, any>
  order: number
}

export interface CreateExecutionForm {
  pipeline_id: number
  cicd_tool_id: number
  trigger_type: 'manual' | 'webhook' | 'schedule'
  parameters?: Record<string, any>
}

// 请求类型
export interface CreatePipelineRequest extends CreatePipelineForm {}
export interface UpdatePipelineRequest extends Partial<CreatePipelineRequest> {}
export interface CreateExecutionRequest extends CreateExecutionForm {}
export interface UpdateExecutionRequest extends Partial<CreateExecutionRequest> {}

// 系统统计类型
export interface SystemStats {
  total_pipelines: number
  active_executions: number
  total_executions: number
  success_rate: number
  tools_count: number
  healthy_tools: number
}

// 导出Ansible相关类型
export * from './ansible'
