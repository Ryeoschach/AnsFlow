import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { 
  Tool, Pipeline, PipelineExecution, 
  JenkinsJob, JenkinsBuild, User,
  CreatePipelineRequest, UpdatePipelineRequest,
  CreateExecutionRequest, UpdateExecutionRequest,
  AtomicStep
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

  async testToolConnection(id: number): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post(`/cicd/tools/${id}/test_connection/`)
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

  // Pipelines
  async getPipelines(): Promise<Pipeline[]> {
    const response = await this.api.get('/pipelines/')
    return response.data
  }

  async getPipeline(id: number): Promise<Pipeline> {
    const response = await this.api.get(`/pipelines/${id}/`)
    return response.data
  }

  async createPipeline(pipeline: CreatePipelineRequest): Promise<Pipeline> {
    const response = await this.api.post('/pipelines/', pipeline)
    return response.data
  }

  async updatePipeline(id: number, pipeline: UpdatePipelineRequest): Promise<Pipeline> {
    const response = await this.api.put(`/pipelines/${id}/`, pipeline)
    return response.data
  }

  async deletePipeline(id: number): Promise<void> {
    await this.api.delete(`/pipelines/${id}/`)
  }

  async clonePipeline(id: number): Promise<Pipeline> {
    const response = await this.api.post(`/pipelines/${id}/clone/`)
    return response.data
  }

  async exportPipeline(id: number): Promise<Blob> {
    const response = await this.api.get(`/pipelines/${id}/export/`, {
      responseType: 'blob'
    })
    return response.data
  }

  async importPipeline(file: File): Promise<Pipeline> {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.api.post('/pipelines/import/', formData, {
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
    return response.data
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
    const response = await this.api.post(`/cicd/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/build/`, {
      parameters
    })
    return response.data
  }

  async stopJenkinsBuild(toolId: number, jobName: string, buildNumber: number): Promise<void> {
    await this.api.post(`/cicd/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/builds/${buildNumber}/stop/`)
  }

  async getJenkinsBuilds(toolId: number, jobName: string): Promise<JenkinsBuild[]> {
    const response = await this.api.get(`/cicd/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/builds/`)
    return response.data
  }

  async getJenkinsBuild(toolId: number, jobName: string, buildNumber: number): Promise<JenkinsBuild> {
    const response = await this.api.get(`/cicd/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/builds/${buildNumber}/`)
    return response.data
  }

  async getJenkinsBuildLogs(toolId: number, jobName: string, buildNumber: number): Promise<string> {
    const response = await this.api.get(`/cicd/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/builds/${buildNumber}/logs/`)
    return response.data.logs
  }

  async getJenkinsQueue(toolId: number): Promise<any[]> {
    const response = await this.api.get(`/cicd/tools/${toolId}/jenkins/queue/`)
    return response.data
  }

  async cancelJenkinsQueueItem(toolId: number, queueId: number): Promise<void> {
    await this.api.delete(`/cicd/tools/${toolId}/jenkins/queue/${queueId}/`)
  }
}

export const apiService = new ApiService()
export default apiService
