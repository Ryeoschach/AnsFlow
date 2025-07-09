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
  
  steps?: PipelineStep[]  // 主要步骤列表 (新的PipelineStep模型)
  atomic_steps?: AtomicStep[]  // 兼容的原子步骤列表
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

// 流水线步骤类型 (新的主要步骤模型)
export interface PipelineStep {
  id: number
  name: string
  description?: string
  status?: 'pending' | 'running' | 'success' | 'failed' | 'skipped' | 'cancelled'
  step_type: 'fetch_code' | 'build' | 'test' | 'security_scan' | 'deploy' | 'ansible' | 'notify' | 'custom' | 'script' |
             'docker_build' | 'docker_run' | 'docker_push' | 'docker_pull' |
             'k8s_deploy' | 'k8s_scale' | 'k8s_delete' | 'k8s_wait' | 'k8s_exec' | 'k8s_logs' | 'approval' | 'shell_script'
  command?: string
  environment_vars?: Record<string, any>
  timeout_seconds?: number
  timeout?: number  // 兼容字段
  order: number
  
  // 高级工作流字段
  dependencies?: number[]  // 依赖的步骤ID列表
  parallel_group?: string  // 并行组ID (与后端字段名一致)
  parallelGroup?: string  // 兼容字段，用于向后兼容
  conditions?: Array<{
    field: string
    operator: 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'greater_than' | 'less_than'
    value: any
    logic?: 'and' | 'or'
  }>
  approval_required?: boolean
  approval_users?: string[]
  retry_policy?: RetryPolicy
  notification_config?: NotificationOptions
  
  // Ansible配置
  ansible_playbook?: number | null
  ansible_playbook_name?: string
  ansible_inventory?: number | null
  ansible_inventory_name?: string
  ansible_credential?: number | null
  ansible_credential_name?: string
  ansible_parameters?: Record<string, any>
  
  // Docker 相关
  docker_image?: string
  docker_tag?: string
  docker_registry?: number | null
  docker_config?: DockerStepConfig
  
  // Kubernetes 相关
  k8s_cluster?: number | null
  k8s_namespace?: string
  k8s_resource_name?: string
  k8s_config?: KubernetesStepConfig
  
  // 执行结果
  output_log?: string
  error_log?: string
  exit_code?: number
  started_at?: string | null
  completed_at?: string | null
}

// 原子步骤类型
export interface AtomicStep {
  id: number
  name: string
  step_type: 'fetch_code' | 'build' | 'test' | 'security_scan' | 'deploy' | 'ansible' | 'notify' | 'custom' | 'script' |
             'docker_build' | 'docker_run' | 'docker_push' | 'docker_pull' |
             'k8s_deploy' | 'k8s_scale' | 'k8s_delete' | 'k8s_wait' | 'k8s_exec' | 'k8s_logs' | 'approval' | 'shell_script'
  description?: string
  parameters: Record<string, any>
  order: number
  pipeline: number
  is_active: boolean
  created_at: string
  git_credential?: number | null  // Git凭据ID
  ansible_playbook?: number | null  // Ansible Playbook ID
  ansible_inventory?: number | null  // Ansible Inventory ID
  ansible_credential?: number | null  // Ansible Credential ID
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

// 工作流高级功能类型定义

// 步骤执行条件类型
export interface StepCondition {
  type: 'always' | 'on_success' | 'on_failure' | 'expression'
  expression?: string  // 条件表达式，如 "${previous_step.result.status} == 'success'"
  depends_on?: number[]  // 依赖的步骤ID列表
}

// 并行执行组类型
export interface ParallelGroup {
  id: string
  name: string
  description?: string
  steps: number[]  // 并行执行的步骤ID列表
  sync_policy: 'wait_all' | 'wait_any' | 'fail_fast'  // 同步策略
  timeout_seconds?: number
}

// 手动审批配置类型
export interface ApprovalConfig {
  approvers: string[]  // 审批人用户名列表
  approval_message?: string  // 审批提示信息
  timeout_hours?: number  // 审批超时时间（小时）
  auto_approve_on_timeout?: boolean  // 超时后是否自动批准
  required_approvals?: number  // 需要的最少审批数量，默认为1
}

// 增强的流水线步骤类型，支持高级工作流功能
export interface EnhancedPipelineStep extends PipelineStep {
  // 条件执行
  condition?: StepCondition
  
  // 并行执行 (使用与后端一致的字段名)
  parallel_group_id?: string  // 兼容字段
  
  // 手动审批
  requires_approval?: boolean
  approval_config?: ApprovalConfig
  approval_status?: 'pending' | 'approved' | 'rejected' | 'timeout'
  approved_by?: string
  approved_at?: string
  
  // 执行策略
  retry_policy?: {
    max_retries: number
    retry_delay_seconds: number
    retry_on_failure: boolean
  }
  
  // 通知配置
  notification_config?: NotificationOptions
}

// 工作流执行上下文
export interface WorkflowContext {
  pipeline_id: number
  execution_id: number
  variables: Record<string, any>  // 全局变量
  step_results: Record<number, any>  // 各步骤执行结果
  current_step?: number
  parallel_groups: ParallelGroup[]
  pending_approvals: number[]  // 等待审批的步骤ID
}

// 条件表达式评估结果
export interface ConditionEvaluationResult {
  should_execute: boolean
  reason?: string
  evaluated_expression?: string
}

// 并行执行状态
export interface ParallelExecutionStatus {
  group_id: string
  status: 'running' | 'completed' | 'failed' | 'waiting'
  completed_steps: number[]
  failed_steps: number[]
  running_steps: number[]
  start_time?: string
  end_time?: string
}

// 审批请求类型
export interface ApprovalRequest {
  id: number
  pipeline_execution: number
  step_id: number
  step_name: string
  requester: string
  approval_config: ApprovalConfig
  status: 'pending' | 'approved' | 'rejected' | 'timeout'
  requested_at: string
  responded_at?: string
  responder?: string
  response_comment?: string
  timeout_at?: string
}

// 审批响应类型
export interface ApprovalResponse {
  action: 'approve' | 'reject'
  comment?: string
}

// 工作流分析结果
export interface WorkflowAnalysis {
  total_steps: number
  parallel_groups: number
  approval_steps: number
  conditional_steps: number
  estimated_duration_minutes?: number
  critical_path?: number[]  // 关键路径上的步骤ID
  potential_bottlenecks?: string[]
}

// 重试策略配置
export interface RetryPolicy {
  max_retries: number
  retry_delay_seconds: number
  retry_on_failure: boolean
  backoff_strategy?: 'fixed' | 'linear' | 'exponential'
  max_delay_seconds?: number
}

// 通知配置
// 通知配置类型（作为步骤级别的配置选项）
export interface NotificationOptions {
  on_success?: boolean
  on_failure?: boolean
  on_approval_required?: boolean
  channels?: Array<'email' | 'dingtalk' | 'wechat' | 'slack' | 'webhook'>
  recipients?: string[]
  webhook_url?: string
  message_template?: string
}

// 通知配置模型（系统级别的通知配置实体）
export interface NotificationConfig {
  id: number
  name: string
  type: 'email' | 'webhook' | 'slack' | 'dingtalk' | 'wechat'
  config: Record<string, any>
  enabled: boolean
  created_by: number
  created_by_username?: string
  created_at: string
  updated_at: string
}

// 工作流指标数据
export interface WorkflowMetrics {
  total_steps: number
  parallel_steps: number
  conditional_steps: number
  approval_steps: number
  estimated_duration: number
  complexity_score: number
  critical_path: number[]
  risk_factors: Array<{
    type: 'high' | 'medium' | 'low'
    message: string
    step_id?: number
  }>
  performance_metrics: {
    avg_step_duration: number
    failure_rate: number
    success_rate: number
    retry_rate: number
  }
  historical_data: Array<{
    date: string
    duration: number
    success: boolean
    steps_count: number
  }>
}

// 依赖关系信息
export interface DependencyInfo {
  step_id: number
  step_name: string
  dependencies: number[]
  dependents: number[]
  is_critical: boolean
  parallel_group?: string
  depth_level: number
}

// 优化建议
export interface OptimizationSuggestion {
  type: 'performance' | 'reliability' | 'maintainability' | 'security'
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  impact: string
  effort: string
  steps_affected: number[]
  implementation_guide?: string
  estimated_benefit?: string
}

// 执行恢复相关类型
export interface ExecutionRecoveryInfo {
  failed_steps: Array<{
    id: number
    name: string
    error: string
    failed_at: string
    logs?: string[]
    retry_count: number
    max_retries: number
  }>
  recovery_points: Array<{
    step_id: number
    step_name: string
    description: string
    recommended: boolean
  }>
  can_recover: boolean
  last_successful_step?: number
  execution_progress: {
    total_steps: number
    completed_steps: number
    failed_steps: number
    pending_steps: number
  }
}

// 步骤执行信息
export interface StepExecutionInfo {
  id: number
  name: string
  step_type: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled'
  started_at?: string
  completed_at?: string
  error_message?: string
  order: number
  logs?: string[]
  retry_count?: number
  max_retries?: number
  duration_seconds?: number
}

// 恢复选项
export interface RecoveryOptions {
  from_step_id: number
  skip_failed: boolean
  modify_parameters: boolean
  parameters: Record<string, any>
  recovery_strategy: 'continue' | 'restart_from' | 'skip_and_continue'
  force_retry: boolean
  custom_timeout?: number
  notification_settings?: NotificationOptions
}

// 工作流验证相关类型
export interface ValidationIssue {
  type: 'success' | 'warning' | 'error' | 'info'
  message: string
  stepId?: number
  field?: string
  suggestion?: string
}

export interface ValidationResult {
  isValid: boolean
  hasWarnings?: boolean
  issues: ValidationIssue[]
  suggestions: string[]
}

// Docker/Kubernetes 相关类型
export interface DockerRegistry {
  id: number
  name: string
  url: string
  username?: string
  email?: string
  is_default: boolean
  is_active: boolean
  auth_config?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface KubernetesCluster {
  id: number
  name: string
  description: string
  api_server: string
  auth_config: Record<string, any>
  status: 'connected' | 'disconnected' | 'error'
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface KubernetesNamespace {
  id: number
  name: string
  cluster: number
  cluster_name?: string
  status: 'active' | 'terminating'
  labels?: Record<string, string>
  created_at: string
  updated_at: string
}

export interface DockerStepConfig {
  dockerfile_path?: string
  context_path?: string
  build_args?: Record<string, string>
  labels?: Record<string, string>
  target_stage?: string
  platform?: string
  cache_from?: string[]
  cache_to?: string[]
  no_cache?: boolean
  pull?: boolean
  squash?: boolean
}

export interface KubernetesStepConfig {
  manifest_path?: string
  manifest_content?: string
  deployment_name?: string
  container_name?: string
  command?: string[]
  args?: string[]
  replicas?: number
  timeout?: number
  wait_for_rollout?: boolean
  rollback_on_failure?: boolean
  dry_run?: boolean
  force?: boolean
}



// Settings 管理相关类型

// 审计日志
export interface AuditLog {
  id: number
  user: number
  user_username?: string
  action: string
  resource_type: string
  resource_id?: string
  details: Record<string, any>
  ip_address?: string
  user_agent?: string
  timestamp: string
  result?: 'success' | 'failure' | 'warning'  // 添加结果字段
}

// 系统告警
export interface SystemAlert {
  id: number
  title: string
  message: string
  alert_type: 'info' | 'warning' | 'error' | 'critical'
  is_active: boolean
  created_at: string
  updated_at: string
  resolved_at?: string
  resolved_by?: number
  resolved_by_username?: string
}

// 全局配置
export interface GlobalConfig {
  id: number
  key: string
  value: string
  description?: string
  config_type: 'string' | 'number' | 'boolean' | 'json'
  is_encrypted: boolean
  category: string
  created_at: string
  updated_at: string
}

// 用户配置文件扩展
export interface UserProfile {
  id: number
  user: number
  user_username?: string
  timezone: string
  language: string
  theme: 'light' | 'dark' | 'auto'
  notification_preferences: Record<string, any>
  dashboard_layout?: Record<string, any>
  created_at: string
  updated_at: string
}

// 备份记录
export interface BackupRecord {
  id: number
  name?: string
  backup_type: 'full' | 'incremental' | 'differential' | 'configuration'
  file_path: string
  filename?: string
  file_size?: number
  backup_time: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress?: number
  error_message?: string
  description?: string
  created_by: number
  created_by_username?: string
  created_at: string
  metadata?: Record<string, any>
}

// 备份计划
export interface BackupSchedule {
  id: number
  name: string
  description?: string
  backup_type: string
  frequency: 'daily' | 'weekly' | 'monthly' | 'custom'
  cron_expression?: string
  retain_days: number
  retention_days?: number  // 别名，向后兼容
  status: 'active' | 'inactive' | 'paused'
  is_active?: boolean  // 别名字段
  notification_config: Record<string, any>
  last_run_at?: string
  last_run_time?: string  // 别名
  next_run_at?: string
  next_run_time?: string  // 别名
  created_by: number
  created_at: string
  updated_at: string
}

// 系统监控数据
export interface SystemMonitoringData {
  system_info: {
    hostname: string
    platform: string
    cpu_count: number
    memory_total: number
    disk_total: number
  }
  performance_metrics: {
    cpu_usage: number
    memory_usage: number
    disk_usage: number
    network_io: {
      bytes_sent: number
      bytes_recv: number
    }
    disk_io: {
      read_bytes: number
      write_bytes: number
    }
  }
  database_metrics: {
    connection_count: number
    active_queries: number
    slow_queries: number
    database_size: number
  }
  application_metrics: {
    active_users: number
    active_pipelines: number
    queue_size: number
    error_rate: number
  }
  timestamp: string
}

// Settings API 请求/响应类型
export interface CreateUserRequest {
  username: string
  email: string
  first_name: string
  last_name: string
  password: string
  is_staff?: boolean
  is_active?: boolean
}

export interface UpdateUserRequest {
  username?: string
  email?: string
  first_name?: string
  last_name?: string
  is_staff?: boolean
  is_active?: boolean
}

export interface CreateGlobalConfigRequest {
  key: string
  value: string
  description?: string
  config_type: 'string' | 'number' | 'boolean' | 'json'
  is_encrypted?: boolean
  category: string
}

export interface UpdateGlobalConfigRequest {
  value?: string
  description?: string
  is_encrypted?: boolean
}

export interface UpdateNotificationConfigRequest {
  name?: string
  type?: 'email' | 'webhook' | 'slack' | 'dingtalk' | 'wechat'
  config?: Record<string, any>
  enabled?: boolean
}

export interface CreateBackupRequest {
  name: string
  backup_type: 'full' | 'incremental' | 'differential'
  description?: string
}

// API 管理相关类型
export interface APIKey {
  id: number
  name: string
  key: string
  secret?: string
  permissions: string[]
  rate_limit: number
  status: 'active' | 'inactive' | 'expired'
  created_by: number
  created_by_username?: string
  expires_at?: string
  last_used_at?: string
  usage_count: number
  created_at: string
  updated_at: string
}

export interface APIEndpoint {
  id: number
  path: string
  method: string
  description?: string
  rate_limit?: number
  auth_required: boolean
  permissions: string[]
  is_active: boolean
  is_enabled?: boolean  // 别名字段
  usage_count: number
  created_by: number
  created_by_username?: string
  created_at: string
  updated_at: string
}

// 系统设置
export interface SystemSetting {
  id: number
  key: string
  value: string
  category: 'system' | 'feature' | 'environment' | 'integration'
  data_type?: 'string' | 'number' | 'boolean' | 'json' | 'password'
  description: string
  is_encrypted: boolean
  is_public?: boolean
  validation_rules?: Record<string, any>
  created_by: number
  created_by_username?: string
  created_at: string
  updated_at: string
}

// 团队管理
export interface Team {
  id: number
  name: string
  description?: string
  avatar?: string
  is_private: boolean
  is_active?: boolean
  members_count?: number
  created_by: number
  created_by_username?: string
  created_at: string
  updated_at: string
}

export interface TeamMembership {
  id: number
  team: number
  team_name?: string
  user: number
  user_username?: string
  user_email?: string
  user_info?: {
    username: string
    email: string
    avatar?: string
  }
  role: 'admin' | 'member' | 'viewer'
  joined_at: string
  created_at: string
}
