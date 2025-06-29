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
  token: string
  config: Record<string, any>
  metadata: Record<string, any>
  is_active: boolean
  health_status: 'healthy' | 'unhealthy' | 'error' | 'pending'
  last_health_check?: string
  created_at: string
  updated_at: string
  project: number
}

// Tool 类型别名，用于兼容
export type Tool = CICDTool

// 流水线类型
export interface Pipeline {
  id: number
  name: string
  description: string
  tool: number
  tool_name?: string
  tool_type?: string
  steps: AtomicStep[]
  is_active: boolean
  metadata: Record<string, any>
  created_at: string
  updated_at: string
  project: number
}

// 原子步骤类型
export interface AtomicStep {
  id: number
  name: string
  step_type: string
  parameters: Record<string, any>
  order: number
  pipeline: number
  is_active: boolean
  created_at: string
}

// 流水线执行类型
export interface PipelineExecution {
  id: number
  pipeline: number
  pipeline_name?: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled' | 'timeout'
  trigger_type: 'manual' | 'webhook' | 'schedule' | 'api'
  triggered_by?: string
  parameters: Record<string, any>
  result?: Record<string, any>  // 添加result字段用于存储步骤执行结果
  logs?: string
  external_id?: string
  external_url?: string
  started_at?: string
  completed_at?: string
  created_at: string
  duration?: number
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

// 执行步骤类型
export interface ExecutionStep {
  id: number
  execution: number
  step: number
  step_name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
  started_at?: string
  completed_at?: string
  logs?: string
  output?: Record<string, any>
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
    number: number
    url: string
    timestamp: number
    result: string
  }
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
  pipeline: number
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
