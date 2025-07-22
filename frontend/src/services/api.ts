import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { 
  Tool, Pipeline, PipelineExecution, 
  JenkinsJob, JenkinsBuild, User,
  CreatePipelineRequest, UpdatePipelineRequest,
  CreateExecutionRequest, UpdateExecutionRequest,
  AtomicStep, PipelineRun, PipelineToolMapping,
  AnsibleInventory, AnsiblePlaybook, AnsibleCredential,
  ValidationResult, ExecutePlaybookRequest, ExecutePlaybookResponse,
  ExecutionLogsResponse, AnsibleStats, AnsibleExecutionList, AnsibleExecution,
  AnsibleHost, AnsibleHostGroup, AnsibleHostGroupMembership,
  AnsibleInventoryVersion, AnsiblePlaybookVersion,
  FileUploadRequest, FileUploadResponse, HostConnectivityResult, HostFactsResult, BatchHostOperation,
  ConditionEvaluationResult, ApprovalConfig, ApprovalRequest, ParallelGroup,
  // Settings 相关类型
  AuditLog, SystemAlert, GlobalConfig, UserProfile, BackupRecord, SystemMonitoringData,
  CreateUserRequest, UpdateUserRequest, CreateGlobalConfigRequest, UpdateGlobalConfigRequest,
  CreateBackupRequest, UpdateNotificationConfigRequest, NotificationConfig, PaginatedResponse,
  APIKey, APIEndpoint, APIStatistics, SystemSetting, Team, TeamMembership, BackupSchedule
} from '../types'

// Docker types
import {
  DockerRegistry, DockerImage, DockerImageVersion, DockerContainer, 
  DockerContainerStats, DockerCompose, DockerRegistryList, DockerImageList,
  DockerContainerList, DockerComposeList, DockerApiResponse, DockerActionResponse,
  DockerImageBuildRequest, DockerImagePushRequest, DockerContainerActionRequest,
  DockerContainerLogsRequest, DockerContainerLogsResponse, DockerComposeActionRequest,
  DockerImageVersionCreateRequest, DockerRegistryTestResponse, DockerResourceStats,
  DockerRegistryFormData, DockerImageFormData, DockerContainerFormData, DockerComposeFormData
} from '../types/docker'

class ApiService {
  private api: AxiosInstance

  constructor() {
    this.api = axios.create({
      baseURL: '/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('authToken')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('authToken')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  // Authentication
  async login(username: string, password: string): Promise<{ token: string; user: User }> {
    const response = await this.api.post('/auth/token/', { username, password })
    // JWT endpoint returns { access, refresh }, but we need { token, user }
    const { access } = response.data
    
    // Get user info using the token
    const userResponse = await this.api.get('/auth/users/me/', {
      headers: { Authorization: `Bearer ${access}` }
    })
    
    return {
      token: access,
      user: userResponse.data
    }
  }

  async logout(): Promise<void> {
    await this.api.post('/auth/logout/')
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get('/auth/users/me/')
    return response.data
  }

  // Tools
  async getTools(): Promise<Tool[]> {
    const response = await this.api.get('/cicd/tools/')
    return response.data.results || response.data
  }

  async getTool(id: number): Promise<Tool> {
    const response = await this.api.get(`/cicd/tools/${id}/`)
    return response.data
  }

  async createTool(tool: Partial<Tool>): Promise<Tool> {
    const response = await this.api.post('/cicd/tools/', tool)
    return response.data
  }

  async updateTool(id: number, tool: Partial<Tool>): Promise<Tool> {
    const response = await this.api.put(`/cicd/tools/${id}/`, tool)
    return response.data
  }

  async deleteTool(id: number): Promise<void> {
    await this.api.delete(`/cicd/tools/${id}/`)
  }

  async testToolConnection(id: number): Promise<{ 
    tool_id: number; 
    tool_name: string; 
    tool_type: string; 
    status: string;
    detailed_status: string;
    is_healthy: boolean; 
    last_check: string;
    message: string 
  }> {
    const response = await this.api.post(`/cicd/tools/${id}/health_check/`)
    return response.data
  }

  async createLocalExecutor(): Promise<{
    success: boolean;
    message: string;
    tool?: {
      id: number;
      name: string;
      tool_type: string;
      status: string;
      base_url: string;
      description: string;
    };
    error?: string;
  }> {
    const response = await this.api.post('/cicd/tools/create_local_executor/')
    return response.data
  }

  // Projects
  async getProjects(): Promise<any[]> {
    const response = await this.api.get('/projects/projects/')
    return response.data.results || response.data
  }

  async getProject(id: number): Promise<any> {
    const response = await this.api.get(`/projects/projects/${id}/`)
    return response.data
  }

  // Projects - Extended methods
  async createProject(project: any): Promise<any> {
    const response = await this.api.post('/projects/projects/', project)
    return response.data
  }

  async updateProject(id: number, project: any): Promise<any> {
    const response = await this.api.put(`/projects/projects/${id}/`, project)
    return response.data
  }

  async deleteProject(id: number): Promise<void> {
    await this.api.delete(`/projects/projects/${id}/`)
  }

  async getProjectEnvironments(projectId: number): Promise<any[]> {
    const response = await this.api.get(`/projects/projects/${projectId}/environments/`)
    return response.data
  }

  async getProjectMembers(projectId: number): Promise<any[]> {
    const response = await this.api.get(`/projects/memberships/?project=${projectId}`)
    return response.data.results || response.data
  }

  async addProjectMember(projectId: number, memberData: any): Promise<any> {
    const response = await this.api.post(`/projects/projects/${projectId}/add_member/`, memberData)
    return response.data
  }

  async removeProjectMember(projectId: number, userId: number): Promise<void> {
    await this.api.delete(`/projects/projects/${projectId}/remove_member/`, {
      data: { user_id: userId }
    })
  }

  async createEnvironment(projectId: number, envData: any): Promise<any> {
    const response = await this.api.post(`/projects/projects/${projectId}/create_environment/`, envData)
    return response.data
  }

  // Pipelines
  async getPipelines(): Promise<Pipeline[]> {
    const response = await this.api.get('/pipelines/pipelines/')
    return response.data
  }

  async getPipeline(id: number): Promise<Pipeline> {
    const response = await this.api.get(`/pipelines/pipelines/${id}/`)
    return response.data
  }

  async createPipeline(pipeline: CreatePipelineRequest): Promise<Pipeline> {
    const response = await this.api.post('/pipelines/pipelines/', pipeline)
    return response.data
  }

  async updatePipeline(id: number, pipeline: UpdatePipelineRequest): Promise<Pipeline> {
    const response = await this.api.put(`/pipelines/pipelines/${id}/`, pipeline)
    return response.data
  }

  async togglePipelineStatus(id: number, isActive: boolean): Promise<Pipeline> {
    const response = await this.api.patch(`/pipelines/pipelines/${id}/`, { is_active: isActive })
    return response.data
  }

  async deletePipeline(id: number): Promise<void> {
    await this.api.delete(`/pipelines/pipelines/${id}/`)
  }

  async clonePipeline(id: number): Promise<Pipeline> {
    const response = await this.api.post(`/pipelines/pipelines/${id}/clone/`)
    return response.data
  }

  async exportPipeline(id: number): Promise<Blob> {
    const response = await this.api.get(`/pipelines/pipelines/${id}/export/`, {
      responseType: 'blob'
    })
    return response.data
  }

  async importPipeline(file: File): Promise<Pipeline> {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.api.post('/pipelines/pipelines/import/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  }

  // Pipeline Executions
  async getExecutions(pipelineId?: number): Promise<PipelineExecution[]> {
    const url = pipelineId ? `/pipelines/${pipelineId}/executions/` : '/cicd/executions/'
    const response = await this.api.get(url)
    return response.data.results || response.data
  }

  async getExecution(id: number): Promise<PipelineExecution> {
    const response = await this.api.get(`/cicd/executions/${id}/`)
    return response.data
  }

  async getExecutionById(id: number): Promise<PipelineExecution> {
    return this.getExecution(id)
  }

  async createExecution(execution: CreateExecutionRequest): Promise<PipelineExecution> {
    const response = await this.api.post('/cicd/executions/', execution)
    return response.data
  }

  async updateExecution(id: number, execution: UpdateExecutionRequest): Promise<PipelineExecution> {
    const response = await this.api.put(`/cicd/executions/${id}/`, execution)
    return response.data
  }

  async cancelExecution(id: number): Promise<void> {
    await this.api.post(`/cicd/executions/${id}/cancel/`)
  }

  async retryExecution(id: number): Promise<PipelineExecution> {
    const response = await this.api.post(`/cicd/executions/${id}/retry/`)
    return response.data
  }

  async getExecutionLogs(id: number): Promise<string> {
    const response = await this.api.get(`/cicd/executions/${id}/logs/`)
    return response.data.logs
  }

  // Atomic Steps
  async getAtomicSteps(): Promise<AtomicStep[]> {
    const response = await this.api.get('/cicd/atomic-steps/')
    return response.data
  }

  async getAtomicStep(id: number): Promise<AtomicStep> {
    const response = await this.api.get(`/cicd/atomic-steps/${id}/`)
    return response.data
  }

  async createAtomicStep(step: Partial<AtomicStep>): Promise<AtomicStep> {
    const response = await this.api.post('/cicd/atomic-steps/', step)
    return response.data
  }

  async updateAtomicStep(id: number, step: Partial<AtomicStep>): Promise<AtomicStep> {
    const response = await this.api.put(`/cicd/atomic-steps/${id}/`, step)
    return response.data
  }

  async deleteAtomicStep(id: number): Promise<void> {
    await this.api.delete(`/cicd/atomic-steps/${id}/`)
  }

  async testAtomicStep(id: number, toolId: number, parameters?: Record<string, any>): Promise<any> {
    const response = await this.api.post(`/cicd/atomic-steps/${id}/test/`, {
      tool_id: toolId,
      parameters: parameters || {}
    })
    return response.data
  }

  async validateAtomicStep(id: number, parameters?: Record<string, any>, toolType?: string): Promise<any> {
    const response = await this.api.post(`/cicd/atomic-steps/${id}/validate/`, {
      parameters: parameters || {},
      tool_type: toolType
    })
    return response.data
  }

  async cloneAtomicStep(id: number, newName: string, newDescription?: string): Promise<AtomicStep> {
    const response = await this.api.post(`/cicd/atomic-steps/${id}/clone/`, {
      new_name: newName,
      new_description: newDescription
    })
    return response.data
  }

  async getAtomicStepStats(): Promise<any> {
    const response = await this.api.get('/cicd/atomic-steps/stats/')
    return response.data
  }

  // Jenkins Integration
  async getJenkinsJobs(toolId: number): Promise<JenkinsJob[]> {
    const response = await this.api.get(`/cicd/tools/${toolId}/jenkins/jobs/`)
    // 后端返回格式: { tool_id, jobs: [...], total_jobs }
    // 前端需要的是 jobs 数组
    return response.data.jobs || []
  }

  async getJenkinsJob(toolId: number, jobName: string): Promise<JenkinsJob> {
    const response = await this.api.get(`/cicd/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/`)
    return response.data
  }

  async createJenkinsJob(toolId: number, jobName: string, config: string): Promise<JenkinsJob> {
    const response = await this.api.post(`/cicd/tools/${toolId}/jenkins/jobs/`, {
      name: jobName,
      config
    })
    return response.data
  }

  async updateJenkinsJob(toolId: number, jobName: string, config: string): Promise<JenkinsJob> {
    const response = await this.api.put(`/cicd/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/`, {
      config
    })
    return response.data
  }

  async deleteJenkinsJob(toolId: number, jobName: string): Promise<void> {
    await this.api.delete(`/cicd/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/`)
  }

  async enableJenkinsJob(toolId: number, jobName: string): Promise<void> {
    await this.api.post(`/cicd/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/enable/`)
  }

  async disableJenkinsJob(toolId: number, jobName: string): Promise<void> {
    await this.api.post(`/cicd/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/disable/`)
  }

  async buildJenkinsJob(toolId: number, jobName: string, parameters?: Record<string, any>): Promise<{ queueId: number }> {
    const response = await this.api.post(`/cicd/tools/${toolId}/jenkins/build/`, {
      job_name: jobName,
      parameters
    })
    return response.data
  }

  async stopJenkinsBuild(toolId: number, jobName: string, buildNumber: number): Promise<void> {
    await this.api.post(`/cicd/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/builds/${buildNumber}/stop/`)
  }

  async getJenkinsBuilds(toolId: number, jobName: string): Promise<JenkinsBuild[]> {
    const response = await this.api.get(`/cicd/tools/${toolId}/jenkins/builds/?job_name=${encodeURIComponent(jobName)}`)
    return response.data.builds || response.data
  }

  async getJenkinsBuild(toolId: number, jobName: string, buildNumber: number): Promise<JenkinsBuild> {
    const response = await this.api.get(`/cicd/tools/${toolId}/jenkins/build-info/?job_name=${encodeURIComponent(jobName)}&build_number=${buildNumber}`)
    return response.data.build_info || response.data
  }

  async getJenkinsBuildLogs(toolId: number, jobName: string, buildNumber: number): Promise<string> {
    const response = await this.api.get(`/cicd/tools/${toolId}/jenkins/build-logs/?job_name=${encodeURIComponent(jobName)}&build_number=${buildNumber}`)
    return response.data.logs
  }

  async getJenkinsQueue(toolId: number): Promise<any[]> {
    const response = await this.api.get(`/cicd/tools/${toolId}/jenkins/queue/`)
    return response.data
  }

  async cancelJenkinsQueueItem(toolId: number, queueId: number): Promise<void> {
    await this.api.delete(`/cicd/tools/${toolId}/jenkins/queue/${queueId}/`)
  }

  // 新增：流水线工具同步相关方法
  async syncPipelineToTool(pipelineId: number, toolId: number): Promise<{
    success: boolean
    message: string
    external_job_id?: string
    external_job_name?: string
  }> {
    const response = await this.api.post(`/pipelines/pipelines/${pipelineId}/sync_to_tool/`, {
      tool_id: toolId
    })
    return response.data
  }

  async getPipelineToolMappings(pipelineId: number): Promise<PipelineToolMapping[]> {
    const response = await this.api.get(`/pipelines/pipelines/${pipelineId}/tool_mappings/`)
    return response.data
  }

  async triggerExternalBuild(pipelineId: number, toolId: number, parameters: Record<string, any> = {}): Promise<{
    success: boolean
    message: string
    build_number?: number
    build_url?: string
  }> {
    const response = await this.api.post(`/pipelines/pipelines/${pipelineId}/trigger_external_build/`, {
      tool_id: toolId,
      parameters
    })
    return response.data
  }

  async runPipeline(pipelineId: number): Promise<PipelineRun> {
    const response = await this.api.post(`/pipelines/pipelines/${pipelineId}/run/`)
    return response.data
  }

  // 流水线工具映射管理
  async getAllPipelineToolMappings(params?: { pipeline?: number, tool?: number }): Promise<PipelineToolMapping[]> {
    const response = await this.api.get('/pipelines/pipeline-mappings/', { params })
    return response.data.results || response.data
  }

  async createPipelineToolMapping(mapping: Partial<PipelineToolMapping>): Promise<PipelineToolMapping> {
    const response = await this.api.post('/pipelines/pipeline-mappings/', mapping)
    return response.data
  }

  async updatePipelineToolMapping(id: number, mapping: Partial<PipelineToolMapping>): Promise<PipelineToolMapping> {
    const response = await this.api.put(`/pipelines/pipeline-mappings/${id}/`, mapping)
    return response.data
  }

  async deletePipelineToolMapping(id: number): Promise<void> {
    await this.api.delete(`/pipelines/pipeline-mappings/${id}/`)
  }

  // Git凭据管理
  async getGitCredentials(): Promise<any[]> {
    const response = await this.api.get('/cicd/git-credentials/')
    return response.data.results || response.data
  }

  async createGitCredential(credential: any): Promise<any> {
    const response = await this.api.post('/cicd/git-credentials/', credential)
    return response.data
  }

  async updateGitCredential(id: number, credential: any): Promise<any> {
    const response = await this.api.put(`/cicd/git-credentials/${id}/`, credential)
    return response.data
  }

  async deleteGitCredential(id: number): Promise<void> {
    await this.api.delete(`/cicd/git-credentials/${id}/`)
  }

  async testGitCredential(id: number): Promise<{ success: boolean; message: string; tested_at?: string }> {
    const response = await this.api.post(`/cicd/git-credentials/${id}/test_connection/`)
    return response.data
  }

  // Analytics相关API
  async getExecutionStats(params?: any): Promise<any> {
    const response = await this.api.get('/analytics/execution-stats/', { params })
    return response.data
  }

  async getExecutionTrends(params?: any): Promise<any[]> {
    const response = await this.api.get('/analytics/execution-trends/', { params })
    return response.data.results || response.data
  }

  async getPipelineStats(params?: any): Promise<any[]> {
    const response = await this.api.get('/analytics/pipeline-stats/', { params })
    return response.data.results || response.data
  }

  async getRecentExecutions(params?: any): Promise<any[]> {
    const response = await this.api.get('/analytics/recent-executions/', { params })
    return response.data.results || response.data
  }

  // Ansible Integration API Methods
  
  // Inventories
  async getAnsibleInventories(params?: any): Promise<AnsibleInventory[]> {
    const response = await this.api.get('/ansible/inventories/', { params })
    return response.data.results || response.data
  }

  async getAnsibleInventory(id: number): Promise<AnsibleInventory> {
    const response = await this.api.get(`/ansible/inventories/${id}/`)
    return response.data
  }

  async createAnsibleInventory(data: Partial<AnsibleInventory>): Promise<AnsibleInventory> {
    const response = await this.api.post('/ansible/inventories/', data)
    return response.data
  }

  async updateAnsibleInventory(id: number, data: Partial<AnsibleInventory>): Promise<AnsibleInventory> {
    const response = await this.api.put(`/ansible/inventories/${id}/`, data)
    return response.data
  }

  async deleteAnsibleInventory(id: number): Promise<void> {
    await this.api.delete(`/ansible/inventories/${id}/`)
  }

  async validateAnsibleInventory(id: number): Promise<ValidationResult> {
    const response = await this.api.post(`/ansible/inventories/${id}/validate_inventory/`)
    return response.data
  }

  // Playbooks
  async getAnsiblePlaybooks(params?: any): Promise<AnsiblePlaybook[]> {
    const response = await this.api.get('/ansible/playbooks/', { params })
    return response.data.results || response.data
  }

  async getAnsiblePlaybook(id: number): Promise<AnsiblePlaybook> {
    const response = await this.api.get(`/ansible/playbooks/${id}/`)
    return response.data
  }

  async createAnsiblePlaybook(data: Partial<AnsiblePlaybook>): Promise<AnsiblePlaybook> {
    const response = await this.api.post('/ansible/playbooks/', data)
    return response.data
  }

  async updateAnsiblePlaybook(id: number, data: Partial<AnsiblePlaybook>): Promise<AnsiblePlaybook> {
    const response = await this.api.put(`/ansible/playbooks/${id}/`, data)
    return response.data
  }

  async deleteAnsiblePlaybook(id: number): Promise<void> {
    await this.api.delete(`/ansible/playbooks/${id}/`)
  }

  async validateAnsiblePlaybook(id: number): Promise<ValidationResult> {
    const response = await this.api.post(`/ansible/playbooks/${id}/validate_playbook/`)
    return response.data
  }

  async validatePlaybookContent(content: string): Promise<ValidationResult> {
    const response = await this.api.post('/ansible/playbooks/validate/', { content })
    return response.data
  }

  async createPlaybookFromTemplate(id: number, data: any): Promise<AnsiblePlaybook> {
    const response = await this.api.post(`/ansible/playbooks/${id}/create_from_template/`, data)
    return response.data
  }

  // Credentials
  async getAnsibleCredentials(params?: any): Promise<AnsibleCredential[]> {
    const response = await this.api.get('/ansible/credentials/', { params })
    return response.data.results || response.data
  }

  async getAnsibleCredential(id: number): Promise<AnsibleCredential> {
    const response = await this.api.get(`/ansible/credentials/${id}/`)
    return response.data
  }

  async createAnsibleCredential(data: any): Promise<AnsibleCredential> {
    const response = await this.api.post('/ansible/credentials/', data)
    return response.data
  }

  async updateAnsibleCredential(id: number, data: any): Promise<AnsibleCredential> {
    const response = await this.api.put(`/ansible/credentials/${id}/`, data)
    return response.data
  }

  async deleteAnsibleCredential(id: number): Promise<void> {
    await this.api.delete(`/ansible/credentials/${id}/`)
  }

  async testAnsibleCredential(id: number): Promise<any> {
    const response = await this.api.post(`/ansible/credentials/${id}/test_connection/`)
    return response.data
  }

  // Executions
  async getAnsibleExecutions(params?: any): Promise<AnsibleExecutionList[]> {
    const response = await this.api.get('/ansible/executions/', { params })
    return response.data.results || response.data
  }

  async getAnsibleExecution(id: number): Promise<AnsibleExecution> {
    const response = await this.api.get(`/ansible/executions/${id}/`)
    return response.data
  }

  async executeAnsiblePlaybook(playbookId: number, data: ExecutePlaybookRequest): Promise<ExecutePlaybookResponse> {
    const response = await this.api.post(`/ansible/playbooks/${playbookId}/execute/`, data)
    return response.data
  }

  async cancelAnsibleExecution(id: number): Promise<any> {
    const response = await this.api.post(`/ansible/executions/${id}/cancel/`)
    return response.data
  }

  async getAnsibleExecutionLogs(id: number): Promise<ExecutionLogsResponse> {
    const response = await this.api.get(`/ansible/executions/${id}/logs/`)
    return response.data
  }

  // Statistics
  async getAnsibleStats(): Promise<AnsibleStats> {
    const response = await this.api.get('/ansible/stats/overview/')
    return response.data
  }

  async getRecentAnsibleExecutions(limit: number = 10): Promise<AnsibleExecutionList[]> {
    const response = await this.api.get(`/ansible/executions/recent/?limit=${limit}`)
    return response.data
  }

  // Advanced Workflow Features
  
  // 从失败步骤恢复执行流水线
  async resumePipelineFromStep(executionId: number, stepId: number, parameters?: Record<string, any>): Promise<PipelineExecution> {
    const response = await this.api.post(`/pipelines/executions/${executionId}/resume/`, {
      step_id: stepId,
      parameters: parameters || {}
    })
    return response.data
  }

  // 获取执行历史和失败步骤信息
  async getExecutionStepHistory(executionId: number): Promise<any[]> {
    const response = await this.api.get(`/pipelines/executions/${executionId}/steps/`)
    return response.data
  }

  // 评估条件表达式
  async evaluateStepCondition(
    pipelineId: number, 
    stepId: number, 
    condition: any, 
    context: Record<string, any>
  ): Promise<{ result: boolean; error?: string }> {
    const response = await this.api.post(`/pipelines/${pipelineId}/steps/${stepId}/evaluate-condition/`, {
      condition,
      context
    })
    return response.data
  }

  // 审批相关API
  async submitApproval(
    executionId: number, 
    stepId: number, 
    approved: boolean, 
    comment?: string
  ): Promise<{ success: boolean }> {
    const response = await this.api.post(`/pipelines/executions/${executionId}/steps/${stepId}/approve/`, {
      approved,
      comment
    })
    return response.data
  }

  // 并行组执行相关API
  async createParallelGroup(groupData: any): Promise<any> {
    console.log('🔄 API调用: 创建并行组', groupData)
    const response = await this.api.post('/pipelines/parallel-groups/', groupData)
    console.log('✅ API响应: 创建并行组', response.data)
    return response.data
  }

  async updateParallelGroup(groupId: string, groupData: any): Promise<any> {
    console.log('🔄 API调用: 更新并行组', groupId, groupData)
    const response = await this.api.put(`/pipelines/parallel-groups/${groupId}/`, groupData)
    console.log('✅ API响应: 更新并行组', response.data)
    return response.data
  }

  async deleteParallelGroup(groupId: string): Promise<void> {
    console.log('🔄 API调用: 删除并行组', groupId)
    await this.api.delete(`/pipelines/parallel-groups/${groupId}/`)
    console.log('✅ API响应: 删除并行组成功')
  }

  async getParallelGroups(pipelineId?: number): Promise<any[]> {
    const url = pipelineId ? `/pipelines/parallel-groups/?pipeline=${pipelineId}` : '/pipelines/parallel-groups/'
    console.log('🔄 API调用: 获取并行组', url)
    const response = await this.api.get(url)
    console.log('✅ API响应: 获取并行组', response.data)
    
    // 处理Django Rest Framework的分页响应
    if (response.data && Array.isArray(response.data.results)) {
      return response.data.results
    } else if (Array.isArray(response.data)) {
      return response.data
    } else {
      console.warn('Unexpected parallel groups data format:', response.data)
      return []
    }
  }

  // 工作流分析API
  async analyzeWorkflowDependencies(pipelineId: number): Promise<{
    dependencies: any[];
    cycles: any[];
    critical_path: any[];
    parallelization_suggestions: any[];
  }> {
    const response = await this.api.get(`/pipelines/${pipelineId}/analyze-workflow/`)
    return response.data
  }

  async getWorkflowMetrics(pipelineId: number): Promise<{
    total_steps: number;
    parallel_steps: number;
    conditional_steps: number;
    approval_steps: number;
    estimated_duration: number;
    complexity_score: number;
  }> {
    const response = await this.api.get(`/pipelines/${pipelineId}/workflow-metrics/`)
    return response.data
  }

  // 重试机制API
  async retryFailedStep(
    executionId: number, 
    stepId: number, 
    retryConfig?: { max_retries?: number; delay_seconds?: number }
  ): Promise<PipelineExecution> {
    const response = await this.api.post(`/pipelines/executions/${executionId}/steps/${stepId}/retry/`, retryConfig)
    return response.data
  }

  // 通知配置API
  async updateNotificationConfig(pipelineId: number, stepId: number, config: any): Promise<any> {
    const response = await this.api.put(`/pipelines/${pipelineId}/steps/${stepId}/notifications/`, config)
    return response.data
  }

  async testNotification(config: any): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post('/notifications/test/', config)
    return response.data
  }

  // 高级步骤配置持久化
  async updateStepAdvancedConfig(
    pipelineId: number, 
    stepId: number, 
    config: {
      condition?: any;
      parallel_group_id?: string;
      approval_config?: any;
      retry_policy?: any;
      notification_config?: any;
    }
  ): Promise<any> {
    const response = await this.api.put(`/pipelines/${pipelineId}/steps/${stepId}/advanced-config/`, config)
    return response.data
  }

  async getStepAdvancedConfig(pipelineId: number, stepId: number): Promise<any> {
    const response = await this.api.get(`/pipelines/${pipelineId}/steps/${stepId}/advanced-config/`)
    return response.data
  }

  // 条件表达式验证和测试
  async validateConditionExpression(expression: string, context?: any): Promise<{ valid: boolean; error?: string }> {
    const response = await this.api.post('/workflow/validate-condition/', { 
      expression,
      context 
    })
    return response.data
  }

  async testStepCondition(
    pipelineId: number, 
    stepId: number, 
    expression: string, 
    context: any
  ): Promise<ConditionEvaluationResult> {
    const response = await this.api.post(`/pipelines/${pipelineId}/steps/${stepId}/test-condition/`, {
      expression,
      context
    })
    return response.data
  }

  // 审批管理API
  async createApprovalRequest(
    executionId: number,
    stepId: number,
    config: ApprovalConfig
  ): Promise<ApprovalRequest> {
    const response = await this.api.post('/workflow/approvals/', {
      pipeline_execution: executionId,
      step_id: stepId,
      approval_config: config
    })
    return response.data
  }

  async submitApprovalResponse(
    approvalId: number,
    response: { action: 'approve' | 'reject'; comment?: string }
  ): Promise<ApprovalRequest> {
    const apiResponse = await this.api.post(`/workflow/approvals/${approvalId}/respond/`, response)
    return apiResponse.data
  }

  async getPendingApprovals(userId?: string): Promise<ApprovalRequest[]> {
    const params = userId ? { user: userId } : {}
    const response = await this.api.get('/workflow/approvals/pending/', { params })
    return response.data.results || response.data
  }

  async getApprovalHistory(pipelineId?: number, stepId?: number): Promise<ApprovalRequest[]> {
    const params: any = {}
    if (pipelineId) params.pipeline_id = pipelineId
    if (stepId) params.step_id = stepId
    
    const response = await this.api.get('/workflow/approvals/history/', { params })
    return response.data.results || response.data
  }

  // 执行恢复API (从失败步骤继续)
  async getExecutionRecoveryInfo(executionId: number): Promise<{
    failed_steps: any[];
    recovery_points: any[];
    can_recover: boolean;
    last_successful_step?: number;
  }> {
    const response = await this.api.get(`/pipelines/executions/${executionId}/recovery-info/`)
    return response.data
  }

  async resumeFromFailedStep(
    executionId: number, 
    fromStepId: number, 
    skipFailed?: boolean,
    parameters?: Record<string, any>
  ): Promise<PipelineExecution> {
    const response = await this.api.post(`/pipelines/executions/${executionId}/resume/`, {
      from_step_id: fromStepId,
      skip_failed: skipFailed || false,
      parameters: parameters || {}
    })
    return response.data
  }

  async getStepExecutionLogs(executionId: number, stepId: number): Promise<{
    logs: string[];
    status: string;
    error?: string;
    start_time?: string;
    end_time?: string;
  }> {
    const response = await this.api.get(`/pipelines/executions/${executionId}/steps/${stepId}/logs/`)
    return response.data
  }

  // 工作流分析增强API
  async getWorkflowPerformanceMetrics(pipelineId: number, timeRange?: string): Promise<{
    avg_execution_time: number;
    success_rate: number;
    failure_patterns: any[];
    step_performance: any[];
    bottlenecks: any[];
  }> {
    const params = timeRange ? { time_range: timeRange } : {}
    const response = await this.api.get(`/pipelines/${pipelineId}/analytics/performance/`, { params })
    return response.data
  }

  async getWorkflowDependencyGraph(pipelineId: number): Promise<{
    nodes: any[];
    edges: any[];
    critical_path: number[];
    parallel_groups: any[];
  }> {
    const response = await this.api.get(`/pipelines/${pipelineId}/analytics/dependency-graph/`)
    return response.data
  }

  async getWorkflowOptimizationSuggestions(pipelineId: number): Promise<{
    suggestions: Array<{
      type: 'parallelization' | 'caching' | 'timeout' | 'retry';
      description: string;
      impact: 'high' | 'medium' | 'low';
      affected_steps: number[];
    }>;
  }> {
    const response = await this.api.get(`/pipelines/${pipelineId}/analytics/optimization-suggestions/`)
    return response.data
  }

  // 通知配置API
  async testNotificationChannel(channelType: string, config: any): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post('/notifications/test/', {
      channel_type: channelType,
      config
    })
    return response.data
  }

  async getAvailableNotificationChannels(): Promise<string[]> {
    const response = await this.api.get('/notifications/channels/')
    return response.data
  }

  // 并行组增强管理
  async optimizeParallelGroups(pipelineId: number): Promise<{
    suggestions: Array<{
      current_groups: ParallelGroup[];
      optimized_groups: ParallelGroup[];
      performance_gain: number;
    }>;
  }> {
    const response = await this.api.get(`/pipelines/${pipelineId}/parallel-groups/optimize/`)
    return response.data
  }

  async validateParallelGroupConfiguration(
    pipelineId: number, 
    groups: ParallelGroup[]
  ): Promise<{
    valid: boolean;
    errors: string[];
    warnings: string[];
  }> {
    const response = await this.api.post(`/pipelines/${pipelineId}/parallel-groups/validate/`, {
      groups
    })
    return response.data
  }

  // Hosts Management
  async getAnsibleHosts(params?: any): Promise<AnsibleHost[]> {
    const response = await this.api.get('/ansible/hosts/', { params })
    return response.data.results || response.data
  }

  async getAnsibleHost(id: number): Promise<AnsibleHost> {
    const response = await this.api.get(`/ansible/hosts/${id}/`)
    return response.data
  }

  async createAnsibleHost(data: Partial<AnsibleHost>): Promise<AnsibleHost> {
    const response = await this.api.post('/ansible/hosts/', data)
    return response.data
  }

  async updateAnsibleHost(id: number, data: Partial<AnsibleHost>): Promise<AnsibleHost> {
    const response = await this.api.put(`/ansible/hosts/${id}/`, data)
    return response.data
  }

  async deleteAnsibleHost(id: number): Promise<void> {
    await this.api.delete(`/ansible/hosts/${id}/`)
  }

  async checkHostConnectivity(id: number): Promise<HostConnectivityResult> {
    const response = await this.api.post(`/ansible/hosts/${id}/check_connectivity/`)
    return response.data
  }

  async gatherHostFacts(id: number): Promise<HostFactsResult> {
    const response = await this.api.post(`/ansible/hosts/${id}/gather_facts/`)
    return response.data
  }

  async batchHostOperation(data: BatchHostOperation): Promise<any> {
    const response = await this.api.post('/ansible/hosts/batch_operation/', data)
    return response.data
  }

  // Host Groups Management
  async getAnsibleHostGroups(params?: any): Promise<AnsibleHostGroup[]> {
    const response = await this.api.get('/ansible/host-groups/', { params })
    return response.data.results || response.data
  }

  async getAnsibleHostGroup(id: number): Promise<AnsibleHostGroup> {
    const response = await this.api.get(`/ansible/host-groups/${id}/`)
    return response.data
  }

  async createAnsibleHostGroup(data: Partial<AnsibleHostGroup>): Promise<AnsibleHostGroup> {
    const response = await this.api.post('/ansible/host-groups/', data)
    return response.data
  }

  async updateAnsibleHostGroup(id: number, data: Partial<AnsibleHostGroup>): Promise<AnsibleHostGroup> {
    const response = await this.api.put(`/ansible/host-groups/${id}/`, data)
    return response.data
  }

  async deleteAnsibleHostGroup(id: number): Promise<void> {
    await this.api.delete(`/ansible/host-groups/${id}/`)
  }

  async addHostToGroup(groupId: number, hostId: number): Promise<void> {
    await this.api.post(`/ansible/host-groups/${groupId}/add_host/`, { host_id: hostId })
  }

  async removeHostFromGroup(groupId: number, hostId: number): Promise<void> {
    await this.api.post(`/ansible/host-groups/${groupId}/remove_host/`, { host_id: hostId })
  }

  // File Upload
  async uploadInventoryFile(data: FormData): Promise<FileUploadResponse> {
    const response = await this.api.post('/ansible/inventories/upload/', data, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async uploadPlaybookFile(data: FormData): Promise<FileUploadResponse> {
    const response = await this.api.post('/ansible/playbooks/upload/', data, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  // Version Management
  async getInventoryVersions(inventoryId: number): Promise<AnsibleInventoryVersion[]> {
    const response = await this.api.get(`/ansible/inventories/${inventoryId}/versions/`)
    return response.data.results || response.data
  }

  async createInventoryVersion(inventoryId: number, data: { version: string; changelog?: string }): Promise<AnsibleInventoryVersion> {
    const response = await this.api.post(`/ansible/inventories/${inventoryId}/create_version/`, data)
    return response.data
  }

  async restoreInventoryVersion(inventoryId: number, versionId: number): Promise<AnsibleInventory> {
    const response = await this.api.post(`/ansible/inventories/${inventoryId}/restore_version/`, { version_id: versionId })
    return response.data
  }

  async getPlaybookVersions(playbookId: number): Promise<AnsiblePlaybookVersion[]> {
    const response = await this.api.get(`/ansible/playbooks/${playbookId}/versions/`)
    return response.data.results || response.data
  }

  async createPlaybookVersion(playbookId: number, data: { version: string; changelog?: string; is_release?: boolean }): Promise<AnsiblePlaybookVersion> {
    const response = await this.api.post(`/ansible/playbooks/${playbookId}/create_version/`, data)
    return response.data
  }

  async restorePlaybookVersion(playbookId: number, versionId: number): Promise<AnsiblePlaybook> {
    const response = await this.api.post(`/ansible/playbooks/${playbookId}/restore_version/`, { version_id: versionId })
    return response.data
  }

  // Docker methods
  
  // Docker Registries
  async getDockerRegistries(): Promise<DockerApiResponse<DockerRegistry>> {
    const response = await this.api.get('/docker/registries/')
    return response.data
  }

  async getDockerRegistry(id: number): Promise<DockerRegistry> {
    const response = await this.api.get(`/docker/registries/${id}/`)
    return response.data
  }

  async createDockerRegistry(data: DockerRegistryFormData): Promise<DockerRegistry> {
    const response = await this.api.post('/docker/registries/', data)
    return response.data
  }

  async updateDockerRegistry(id: number, data: Partial<DockerRegistryFormData>): Promise<DockerRegistry> {
    const response = await this.api.put(`/docker/registries/${id}/`, data)
    return response.data
  }

  async deleteDockerRegistry(id: number): Promise<void> {
    await this.api.delete(`/docker/registries/${id}/`)
  }

  async testDockerRegistry(id: number): Promise<DockerRegistryTestResponse> {
    const response = await this.api.post(`/docker/registries/${id}/test_connection/`)
    return response.data
  }

  // Docker Images
  async getDockerImages(): Promise<DockerApiResponse<DockerImageList>> {
    const response = await this.api.get('/docker/images/')
    return response.data
  }

  async getDockerImage(id: number): Promise<DockerImage> {
    const response = await this.api.get(`/docker/images/${id}/`)
    return response.data
  }

  async createDockerImage(data: DockerImageFormData): Promise<DockerImage> {
    const response = await this.api.post('/docker/images/', data)
    return response.data
  }

  async updateDockerImage(id: number, data: Partial<DockerImageFormData>): Promise<DockerImage> {
    const response = await this.api.put(`/docker/images/${id}/`, data)
    return response.data
  }

  async deleteDockerImage(id: number): Promise<void> {
    await this.api.delete(`/docker/images/${id}/`)
  }

  async buildDockerImage(id: number, data: DockerImageBuildRequest): Promise<DockerActionResponse> {
    const response = await this.api.post(`/docker/images/${id}/build/`, data)
    return response.data
  }

  async pushDockerImage(id: number, data: DockerImagePushRequest): Promise<DockerActionResponse> {
    const response = await this.api.post(`/docker/images/${id}/push/`, data)
    return response.data
  }

  async pullDockerImage(id: number): Promise<DockerActionResponse> {
    const response = await this.api.post(`/docker/images/${id}/pull/`)
    return response.data
  }

  async scanDockerImage(id: number): Promise<DockerActionResponse> {
    const response = await this.api.post(`/docker/images/${id}/scan/`)
    return response.data
  }

  // Docker Image Versions
  async getDockerImageVersions(imageId: number): Promise<DockerImageVersion[]> {
    const response = await this.api.get(`/docker/images/${imageId}/versions/`)
    return response.data.results || response.data
  }

  async createDockerImageVersion(imageId: number, data: DockerImageVersionCreateRequest): Promise<DockerImageVersion> {
    const response = await this.api.post(`/docker/images/${imageId}/versions/`, data)
    return response.data
  }

  async deleteDockerImageVersion(imageId: number, versionId: number): Promise<void> {
    await this.api.delete(`/docker/images/${imageId}/versions/${versionId}/`)
  }

  // Docker Containers
  async getDockerContainers(): Promise<DockerApiResponse<DockerContainerList>> {
    const response = await this.api.get('/docker/containers/')
    return response.data
  }

  async getDockerContainer(id: number): Promise<DockerContainer> {
    const response = await this.api.get(`/docker/containers/${id}/`)
    return response.data
  }

  async createDockerContainer(data: DockerContainerFormData): Promise<DockerContainer> {
    const response = await this.api.post('/docker/containers/', data)
    return response.data
  }

  async updateDockerContainer(id: number, data: Partial<DockerContainerFormData>): Promise<DockerContainer> {
    const response = await this.api.put(`/docker/containers/${id}/`, data)
    return response.data
  }

  async deleteDockerContainer(id: number): Promise<void> {
    await this.api.delete(`/docker/containers/${id}/`)
  }

  async startDockerContainer(id: number): Promise<DockerActionResponse> {
    const response = await this.api.post(`/docker/containers/${id}/start/`)
    return response.data
  }

  async stopDockerContainer(id: number): Promise<DockerActionResponse> {
    const response = await this.api.post(`/docker/containers/${id}/stop/`)
    return response.data
  }

  async restartDockerContainer(id: number): Promise<DockerActionResponse> {
    const response = await this.api.post(`/docker/containers/${id}/restart/`)
    return response.data
  }

  async pauseDockerContainer(id: number): Promise<DockerActionResponse> {
    const response = await this.api.post(`/docker/containers/${id}/pause/`)
    return response.data
  }

  async unpauseDockerContainer(id: number): Promise<DockerActionResponse> {
    const response = await this.api.post(`/docker/containers/${id}/unpause/`)
    return response.data
  }

  async getDockerContainerLogs(id: number, options: DockerContainerLogsRequest = {}): Promise<DockerContainerLogsResponse> {
    const response = await this.api.post(`/docker/containers/${id}/logs/`, options)
    return response.data
  }

  async getDockerContainerStats(id: number): Promise<DockerContainerStats> {
    const response = await this.api.get(`/docker/containers/${id}/stats/`)
    return response.data
  }

  async execDockerContainer(id: number, data: { command: string; workdir?: string }): Promise<DockerActionResponse> {
    const response = await this.api.post(`/docker/containers/${id}/exec/`, data)
    return response.data
  }

  // Docker Compose
  async getDockerComposes(): Promise<DockerApiResponse<DockerComposeList>> {
    const response = await this.api.get('/docker/compose/')
    return response.data
  }

  async getDockerCompose(id: number): Promise<DockerCompose> {
    const response = await this.api.get(`/docker/compose/${id}/`)
    return response.data
  }

  async createDockerCompose(data: DockerComposeFormData): Promise<DockerCompose> {
    const response = await this.api.post('/docker/compose/', data)
    return response.data
  }

  async updateDockerCompose(id: number, data: Partial<DockerComposeFormData>): Promise<DockerCompose> {
    const response = await this.api.put(`/docker/compose/${id}/`, data)
    return response.data
  }

  async deleteDockerCompose(id: number): Promise<void> {
    await this.api.delete(`/docker/compose/${id}/`)
  }

  async startDockerCompose(id: number, options: { services?: string[]; build?: boolean } = {}): Promise<DockerActionResponse> {
    const response = await this.api.post(`/docker/compose/${id}/up/`, options)
    return response.data
  }

  async stopDockerCompose(id: number): Promise<DockerActionResponse> {
    const response = await this.api.post(`/docker/compose/${id}/down/`)
    return response.data
  }

  async restartDockerCompose(id: number): Promise<DockerActionResponse> {
    const response = await this.api.post(`/docker/compose/${id}/restart/`)
    return response.data
  }

  async buildDockerCompose(id: number, options: { services?: string[]; no_cache?: boolean } = {}): Promise<DockerActionResponse> {
    const response = await this.api.post(`/docker/compose/${id}/build/`, options)
    return response.data
  }

  async getDockerComposeStatus(id: number): Promise<DockerActionResponse> {
    const response = await this.api.get(`/docker/compose/${id}/status/`)
    return response.data
  }

  async getDockerComposeLogs(id: number, options: { services?: string[]; follow?: boolean; tail?: number } = {}): Promise<DockerContainerLogsResponse> {
    const response = await this.api.post(`/docker/compose/${id}/logs/`, options)
    return response.data
  }

  // Docker System Info
  async getDockerSystemInfo(): Promise<any> {
    const response = await this.api.get('/docker/system/info/')
    return response.data
  }

  async getDockerSystemStats(): Promise<DockerResourceStats> {
    const response = await this.api.get('/docker/system/stats/')
    return response.data
  }

  async cleanupDockerSystem(options: { containers?: boolean; images?: boolean; volumes?: boolean; networks?: boolean } = {}): Promise<DockerActionResponse> {
    const response = await this.api.post('/docker/system/cleanup/', options)
    return response.data
  }

  // Local Docker Resources API
  async getLocalDockerImages(): Promise<any[]> {
    const response = await this.api.get('/docker/local/images/')
    return response.data.images || []
  }

  async getLocalDockerContainers(): Promise<any[]> {
    const response = await this.api.get('/docker/local/containers/')
    return response.data.containers || []
  }

  async importLocalDockerImages(): Promise<any> {
    const response = await this.api.post('/docker/local/import/images/')
    return response.data
  }

  async importLocalDockerContainers(): Promise<any> {
    const response = await this.api.post('/docker/local/import/containers/')
    return response.data
  }

  async syncLocalDockerResources(): Promise<any> {
    const response = await this.api.post('/docker/local/sync/')
    return response.data
  }

  // ============================================================================
  // Settings Management API Methods
  // ============================================================================

  // 用户管理
  async getUsers(): Promise<PaginatedResponse<User>> {
    const response = await this.api.get('/settings/users/')
    return response.data
  }

  async getUser(id: number): Promise<User> {
    const response = await this.api.get(`/settings/users/${id}/`)
    return response.data
  }

  async createUser(userData: CreateUserRequest): Promise<User> {
    const response = await this.api.post('/settings/users/', userData)
    return response.data
  }

  async updateUser(id: number, userData: UpdateUserRequest): Promise<User> {
    const response = await this.api.put(`/settings/users/${id}/`, userData)
    return response.data
  }

  async deleteUser(id: number): Promise<void> {
    await this.api.delete(`/settings/users/${id}/`)
  }

  async resetUserPassword(id: number, newPassword: string): Promise<void> {
    await this.api.post(`/settings/users/${id}/reset_password/`, { password: newPassword })
  }

  // 审计日志
  async getAuditLogs(params?: { 
    page?: number, 
    page_size?: number, 
    user?: number, 
    action?: string, 
    resource_type?: string,
    start_date?: string,
    end_date?: string 
  }): Promise<PaginatedResponse<AuditLog>> {
    const response = await this.api.get('/settings/audit-logs/', { params })
    return response.data
  }

  async getAuditLog(id: number): Promise<AuditLog> {
    const response = await this.api.get(`/settings/audit-logs/${id}/`)
    return response.data
  }

  async exportAuditLogs(params?: { 
    format?: 'csv' | 'excel' | 'json',
    start_date?: string,
    end_date?: string,
    user?: number,
    action?: string,
    resource_type?: string
  }): Promise<Blob> {
    const response = await this.api.get('/settings/audit-logs/export/', { 
      params,
      responseType: 'blob'
    })
    return response.data
  }

  // 系统告警
  async getSystemAlerts(params?: { 
    page?: number, 
    page_size?: number, 
    alert_type?: string, 
    is_active?: boolean 
  }): Promise<PaginatedResponse<SystemAlert>> {
    const response = await this.api.get('/settings/system-alerts/', { params })
    return response.data
  }

  async getSystemAlert(id: number): Promise<SystemAlert> {
    const response = await this.api.get(`/settings/system-alerts/${id}/`)
    return response.data
  }

  async createSystemAlert(alertData: Partial<SystemAlert>): Promise<SystemAlert> {
    const response = await this.api.post('/settings/system-alerts/', alertData)
    return response.data
  }

  async updateSystemAlert(id: number, alertData: Partial<SystemAlert>): Promise<SystemAlert> {
    const response = await this.api.put(`/settings/system-alerts/${id}/`, alertData)
    return response.data
  }

  async deleteSystemAlert(id: number): Promise<void> {
    await this.api.delete(`/settings/system-alerts/${id}/`)
  }

  async resolveSystemAlert(id: number): Promise<SystemAlert> {
    const response = await this.api.post(`/settings/system-alerts/${id}/resolve/`)
    return response.data
  }

  // 全局配置
  async getGlobalConfigs(params?: { 
    page?: number, 
    page_size?: number, 
    category?: string, 
    key?: string 
  }): Promise<PaginatedResponse<GlobalConfig>> {
    const response = await this.api.get('/settings/global-configs/', { params })
    return response.data
  }

  async getGlobalConfig(id: number): Promise<GlobalConfig> {
    const response = await this.api.get(`/settings/global-configs/${id}/`)
    return response.data
  }

  async getGlobalConfigByKey(key: string): Promise<GlobalConfig> {
    const response = await this.api.get(`/settings/global-configs/by-key/${key}/`)
    return response.data
  }

  async createGlobalConfig(configData: CreateGlobalConfigRequest): Promise<GlobalConfig> {
    const response = await this.api.post('/settings/global-configs/', configData)
    return response.data
  }

  async updateGlobalConfig(id: number, configData: UpdateGlobalConfigRequest): Promise<GlobalConfig> {
    const response = await this.api.put(`/settings/global-configs/${id}/`, configData)
    return response.data
  }

  async deleteGlobalConfig(id: number): Promise<void> {
    await this.api.delete(`/settings/global-configs/${id}/`)
  }

  // 用户配置文件
  async getUserProfiles(params?: { 
    page?: number, 
    page_size?: number, 
    user?: number 
  }): Promise<PaginatedResponse<UserProfile>> {
    const response = await this.api.get('/settings/user-profiles/', { params })
    return response.data
  }

  async getUserProfile(id: number): Promise<UserProfile> {
    const response = await this.api.get(`/settings/user-profiles/${id}/`)
    return response.data
  }

  async getCurrentUserProfile(): Promise<UserProfile> {
    const response = await this.api.get('/settings/user-profiles/current/')
    return response.data
  }

  async updateUserProfile(id: number, profileData: Partial<UserProfile>): Promise<UserProfile> {
    const response = await this.api.put(`/settings/user-profiles/${id}/`, profileData)
    return response.data
  }

  async updateCurrentUserProfile(profileData: Partial<UserProfile>): Promise<UserProfile> {
    const response = await this.api.put('/settings/user-profiles/current/', profileData)
    return response.data
  }

  // 通知配置
  async getNotificationConfigs(params?: { 
    page?: number, 
    page_size?: number, 
    config_type?: string 
  }): Promise<PaginatedResponse<NotificationConfig>> {
    const response = await this.api.get('/settings/notification-configs/', { params })
    return response.data
  }

  async getNotificationConfig(id: number): Promise<NotificationConfig> {
    const response = await this.api.get(`/settings/notification-configs/${id}/`)
    return response.data
  }

  async updateSettingsNotificationConfig(id: number, configData: UpdateNotificationConfigRequest): Promise<NotificationConfig> {
    const response = await this.api.put(`/settings/notification-configs/${id}/`, configData)
    return response.data
  }

  async createNotificationConfig(configData: {
    name: string
    type: 'email' | 'webhook' | 'slack' | 'dingtalk' | 'wechat'
    config: Record<string, any>
    enabled?: boolean
  }): Promise<NotificationConfig> {
    const response = await this.api.post('/settings/notification-configs/', configData)
    return response.data
  }

  async deleteNotificationConfig(id: number): Promise<void> {
    await this.api.delete(`/settings/notification-configs/${id}/`)
  }

  // 备份记录
  async getBackupRecords(params?: { 
    page?: number, 
    page_size?: number, 
    backup_type?: string, 
    status?: string 
  }): Promise<PaginatedResponse<BackupRecord>> {
    const response = await this.api.get('/settings/backup-records/', { params })
    return response.data
  }

  async getBackupRecord(id: number): Promise<BackupRecord> {
    const response = await this.api.get(`/settings/backup-records/${id}/`)
    return response.data
  }

  async createBackup(backupData: CreateBackupRequest): Promise<BackupRecord> {
    const response = await this.api.post('/settings/backup-records/', backupData)
    return response.data
  }

  async downloadBackup(id: number): Promise<Blob> {
    const response = await this.api.get(`/settings/backup-records/${id}/download/`, {
      responseType: 'blob'
    })
    return response.data
  }

  async deleteBackupRecord(id: number): Promise<void> {
    await this.api.delete(`/settings/backup-records/${id}/`)
  }

  // 备份计划
  async getBackupSchedules(params?: { 
    page?: number
    page_size?: number
    search?: string
  }): Promise<PaginatedResponse<BackupSchedule>> {
    const response = await this.api.get('/settings/backup-schedules/', { params })
    return response.data
  }

  async getBackupSchedule(id: number): Promise<BackupSchedule> {
    const response = await this.api.get(`/settings/backup-schedules/${id}/`)
    return response.data
  }

  async createBackupSchedule(scheduleData: {
    name: string
    description?: string
    backup_type: string
    cron_expression: string
    is_active?: boolean
    retention_days?: number
  }): Promise<BackupSchedule> {
    const response = await this.api.post('/settings/backup-schedules/', scheduleData)
    return response.data
  }

  async updateBackupSchedule(id: number, scheduleData: {
    name?: string
    description?: string
    backup_type?: string
    cron_expression?: string
    is_active?: boolean
    retention_days?: number
  }): Promise<BackupSchedule> {
    const response = await this.api.put(`/settings/backup-schedules/${id}/`, scheduleData)
    return response.data
  }

  async deleteBackupSchedule(id: number): Promise<void> {
    await this.api.delete(`/settings/backup-schedules/${id}/`)
  }

  // 团队成员管理
  async getTeamMemberships(teamId?: number, params?: { 
    page?: number
    page_size?: number
    search?: string
  }): Promise<PaginatedResponse<TeamMembership>> {
    const url = teamId ? `/settings/teams/${teamId}/members/` : '/settings/team-memberships/'
    const response = await this.api.get(url, { params })
    return response.data
  }

  async addTeamMember(teamId: number, memberData: {
    user: number
    role: 'admin' | 'member' | 'viewer'
  }): Promise<TeamMembership> {
    const response = await this.api.post(`/settings/teams/${teamId}/members/`, memberData)
    return response.data
  }

  async updateTeamMember(teamId: number, userId: number, memberData: {
    role?: 'admin' | 'member' | 'viewer'
  }): Promise<TeamMembership> {
    const response = await this.api.put(`/settings/teams/${teamId}/members/${userId}/`, memberData)
    return response.data
  }

  async removeTeamMember(teamId: number, userId: number): Promise<void> {
    await this.api.delete(`/settings/teams/${teamId}/members/${userId}/`)
  }

  // 团队管理
  async getTeams(params?: { 
    page?: number
    page_size?: number
    search?: string
  }): Promise<PaginatedResponse<Team>> {
    const response = await this.api.get('/settings/teams/', { params })
    return response.data
  }

  async getTeam(id: number): Promise<Team> {
    const response = await this.api.get(`/settings/teams/${id}/`)
    return response.data
  }

  async createTeam(teamData: {
    name: string
    description?: string
    is_private?: boolean
  }): Promise<Team> {
    const response = await this.api.post('/settings/teams/', teamData)
    return response.data
  }

  async updateTeam(id: number, teamData: {
    name?: string
    description?: string
    is_private?: boolean
  }): Promise<Team> {
    const response = await this.api.put(`/settings/teams/${id}/`, teamData)
    return response.data
  }

  async deleteTeam(id: number): Promise<void> {
    await this.api.delete(`/settings/teams/${id}/`)
  }

  // API Keys 管理
  async getAPIKeys(params?: { 
    page?: number
    page_size?: number
    search?: string
  }): Promise<PaginatedResponse<APIKey>> {
    const response = await this.api.get('/settings/api-keys/', { params })
    return response.data
  }

  async getAPIKey(id: number): Promise<APIKey> {
    const response = await this.api.get(`/settings/api-keys/${id}/`)
    return response.data
  }

  async createAPIKey(keyData: {
    name: string
    permissions: string[]
    rate_limit?: number
    expires_at?: string
  }): Promise<APIKey> {
    const response = await this.api.post('/settings/api-keys/', keyData)
    return response.data
  }

  async updateAPIKey(id: number, keyData: {
    name?: string
    permissions?: string[]
    rate_limit?: number
    expires_at?: string
    status?: 'active' | 'inactive' | 'expired'
  }): Promise<APIKey> {
    const response = await this.api.put(`/settings/api-keys/${id}/`, keyData)
    return response.data
  }

  async deleteAPIKey(id: number): Promise<void> {
    await this.api.delete(`/settings/api-keys/${id}/`)
  }

  async regenerateAPIKey(id: number): Promise<APIKey> {
    const response = await this.api.post(`/settings/api-keys/${id}/regenerate/`)
    return response.data
  }

  async revokeAPIKey(id: number): Promise<void> {
    await this.api.post(`/settings/api-keys/${id}/revoke/`)
  }

  // API Endpoints 管理
  async getAPIEndpoints(params?: { 
    page?: number
    page_size?: number
    search?: string
  }): Promise<PaginatedResponse<APIEndpoint>> {
    const response = await this.api.get('/settings/api-endpoints/', { params })
    return response.data
  }

  async getAPIEndpoint(id: number): Promise<APIEndpoint> {
    const response = await this.api.get(`/settings/api-endpoints/${id}/`)
    return response.data
  }

  async createAPIEndpoint(endpointData: Partial<APIEndpoint>): Promise<APIEndpoint> {
    // 直接发送数据，序列化器会处理字段映射
    const cleanData = {
      ...endpointData
    };
    
    // 清理不需要发送到后端的字段
    delete cleanData.id;
    delete cleanData.created_at;
    delete cleanData.updated_at;
    delete cleanData.usage_stats;
    delete cleanData.is_deprecated;
    
    const response = await this.api.post('/settings/api-endpoints/', cleanData)
    return response.data
  }

  async updateAPIEndpoint(id: number, endpointData: Partial<APIEndpoint>): Promise<APIEndpoint> {
    // 直接发送数据，序列化器会处理字段映射
    const cleanData = {
      ...endpointData
    };
    
    // 清理不需要发送到后端的字段
    delete cleanData.id;
    delete cleanData.created_at;
    delete cleanData.updated_at;
    delete cleanData.usage_stats;
    delete cleanData.is_deprecated;
    
    const response = await this.api.put(`/settings/api-endpoints/${id}/`, cleanData)
    return response.data
  }

  async deleteAPIEndpoint(id: number): Promise<void> {
    await this.api.delete(`/settings/api-endpoints/${id}/`)
  }

  async discoverAPIEndpoints(): Promise<{
    message: string
    discovered_count: number
    created_count: number
    updated_count: number
    endpoints: APIEndpoint[]
  }> {
    const response = await this.api.post('/settings/api-endpoints/auto_discover/')
    return response.data
  }

  async testAPIEndpoint(id: number, testData?: {
    params?: Record<string, any>
    body?: Record<string, any>
  }): Promise<{
    success: boolean
    status_code?: number
    response_time_ms?: number
    response_data?: any
    headers?: Record<string, string>
    error?: string
    tested_at: string
  }> {
    const response = await this.api.post(`/settings/api-endpoints/${id}/test_endpoint/`, testData || {})
    return response.data
  }

  async getAPIEndpointStatistics(): Promise<APIStatistics> {
    const response = await this.api.get('/settings/api-endpoints/statistics/')
    return response.data
  }

  // 系统设置管理方法
  async getSystemSettings(params?: { 
    page?: number
    page_size?: number
    search?: string
    category?: string
  }): Promise<PaginatedResponse<SystemSetting>> {
    const response = await this.api.get('/settings/system-settings/', { params })
    return response.data
  }

  async getSystemSettingsByCategory(category: string): Promise<PaginatedResponse<SystemSetting>> {
    const response = await this.api.get(`/settings/system-settings/`, { 
      params: { category, page_size: 1000 } 
    })
    return response.data
  }

  async getSystemSetting(id: number): Promise<SystemSetting> {
    const response = await this.api.get(`/settings/system-settings/${id}/`)
    return response.data
  }

  async updateSystemSetting(id: number, settingData: {
    value?: string
    description?: string
    is_encrypted?: boolean
  }): Promise<SystemSetting> {
    const response = await this.api.put(`/settings/system-settings/${id}/`, settingData)
    return response.data
  }

  async bulkUpdateSystemSettings(updates: Array<{
    id: number
    value: string
  }>): Promise<SystemSetting[]> {
    const response = await this.api.post('/settings/system-settings/bulk-update/', { updates })
    return response.data
  }

  // 系统监控方法
  async getSystemMonitoring(): Promise<SystemMonitoringData> {
    const response = await this.api.get('/settings/system-monitoring/')
    return response.data
  }

  async getSystemHealth(): Promise<{
    status: string
    services: Record<string, any>
    database: { status: string; connection_count?: number }
    redis: { status: string; memory_usage?: number }
  }> {
    const response = await this.api.get('/settings/system-monitoring/health/')
    return response.data
  }
}

export const apiService = new ApiService()
export default apiService
