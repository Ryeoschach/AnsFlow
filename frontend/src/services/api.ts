import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { 
  Tool, Pipeline, PipelineExecution, 
  JenkinsJob, JenkinsBuild, User,
  CreatePipelineRequest, UpdatePipelineRequest,
  CreateExecutionRequest, UpdateExecutionRequest,
  AtomicStep, PipelineRun, PipelineToolMapping,
  AnsibleInventory, AnsiblePlaybook, AnsibleCredential,
  ValidationResult, ExecutePlaybookRequest, ExecutePlaybookResponse,
  ExecutionLogsResponse, AnsibleStats, AnsibleExecutionList, AnsibleExecution
} from '../types'

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
}

export const apiService = new ApiService()
export default apiService
