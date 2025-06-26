import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { 
  Tool, Pipeline, PipelineExecution, 
  JenkinsJob, JenkinsBuild, User,
  CreatePipelineRequest, UpdatePipelineRequest,
  CreateExecutionRequest, UpdateExecutionRequest
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
    const response = await this.api.get('/tools/')
    return response.data
  }

  async getTool(id: number): Promise<Tool> {
    const response = await this.api.get(`/tools/${id}/`)
    return response.data
  }

  async createTool(tool: Partial<Tool>): Promise<Tool> {
    const response = await this.api.post('/tools/', tool)
    return response.data
  }

  async updateTool(id: number, tool: Partial<Tool>): Promise<Tool> {
    const response = await this.api.put(`/tools/${id}/`, tool)
    return response.data
  }

  async deleteTool(id: number): Promise<void> {
    await this.api.delete(`/tools/${id}/`)
  }

  async testToolConnection(id: number): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post(`/tools/${id}/test_connection/`)
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
    const url = pipelineId ? `/pipelines/${pipelineId}/executions/` : '/executions/'
    const response = await this.api.get(url)
    return response.data
  }

  async getExecution(id: number): Promise<PipelineExecution> {
    const response = await this.api.get(`/executions/${id}/`)
    return response.data
  }

  async getExecutionById(id: number): Promise<PipelineExecution> {
    return this.getExecution(id)
  }

  async createExecution(execution: CreateExecutionRequest): Promise<PipelineExecution> {
    const response = await this.api.post('/executions/', execution)
    return response.data
  }

  async updateExecution(id: number, execution: UpdateExecutionRequest): Promise<PipelineExecution> {
    const response = await this.api.put(`/executions/${id}/`, execution)
    return response.data
  }

  async cancelExecution(id: number): Promise<void> {
    await this.api.post(`/executions/${id}/cancel/`)
  }

  async retryExecution(id: number): Promise<PipelineExecution> {
    const response = await this.api.post(`/executions/${id}/retry/`)
    return response.data
  }

  async getExecutionLogs(id: number): Promise<string> {
    const response = await this.api.get(`/executions/${id}/logs/`)
    return response.data.logs
  }

  // Jenkins Integration
  async getJenkinsJobs(toolId: number): Promise<JenkinsJob[]> {
    const response = await this.api.get(`/tools/${toolId}/jenkins/jobs/`)
    return response.data
  }

  async getJenkinsJob(toolId: number, jobName: string): Promise<JenkinsJob> {
    const response = await this.api.get(`/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/`)
    return response.data
  }

  async createJenkinsJob(toolId: number, jobName: string, config: string): Promise<JenkinsJob> {
    const response = await this.api.post(`/tools/${toolId}/jenkins/jobs/`, {
      name: jobName,
      config
    })
    return response.data
  }

  async updateJenkinsJob(toolId: number, jobName: string, config: string): Promise<JenkinsJob> {
    const response = await this.api.put(`/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/`, {
      config
    })
    return response.data
  }

  async deleteJenkinsJob(toolId: number, jobName: string): Promise<void> {
    await this.api.delete(`/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/`)
  }

  async enableJenkinsJob(toolId: number, jobName: string): Promise<void> {
    await this.api.post(`/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/enable/`)
  }

  async disableJenkinsJob(toolId: number, jobName: string): Promise<void> {
    await this.api.post(`/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/disable/`)
  }

  async buildJenkinsJob(toolId: number, jobName: string, parameters?: Record<string, any>): Promise<{ queueId: number }> {
    const response = await this.api.post(`/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/build/`, {
      parameters
    })
    return response.data
  }

  async stopJenkinsBuild(toolId: number, jobName: string, buildNumber: number): Promise<void> {
    await this.api.post(`/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/builds/${buildNumber}/stop/`)
  }

  async getJenkinsBuilds(toolId: number, jobName: string): Promise<JenkinsBuild[]> {
    const response = await this.api.get(`/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/builds/`)
    return response.data
  }

  async getJenkinsBuild(toolId: number, jobName: string, buildNumber: number): Promise<JenkinsBuild> {
    const response = await this.api.get(`/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/builds/${buildNumber}/`)
    return response.data
  }

  async getJenkinsBuildLogs(toolId: number, jobName: string, buildNumber: number): Promise<string> {
    const response = await this.api.get(`/tools/${toolId}/jenkins/jobs/${encodeURIComponent(jobName)}/builds/${buildNumber}/logs/`)
    return response.data.logs
  }

  async getJenkinsQueue(toolId: number): Promise<any[]> {
    const response = await this.api.get(`/tools/${toolId}/jenkins/queue/`)
    return response.data
  }

  async cancelJenkinsQueueItem(toolId: number, queueId: number): Promise<void> {
    await this.api.delete(`/tools/${toolId}/jenkins/queue/${queueId}/`)
  }
}

export const apiService = new ApiService()
export default apiService
