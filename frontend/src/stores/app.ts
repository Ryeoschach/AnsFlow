import { create } from 'zustand'
import { Tool, Pipeline, PipelineExecution } from '../types'
import apiService from '../services/api'

interface AppState {
  // Tools
  tools: Tool[]
  selectedTool: Tool | null
  toolsLoading: boolean
  
  // Pipelines
  pipelines: Pipeline[]
  selectedPipeline: Pipeline | null
  pipelinesLoading: boolean
  
  // Executions
  executions: PipelineExecution[]
  selectedExecution: PipelineExecution | null
  executionsLoading: boolean
  
  // Actions
  loadTools: () => Promise<void>
  selectTool: (tool: Tool | null) => void
  
  loadPipelines: () => Promise<void>
  selectPipeline: (pipeline: Pipeline | null) => void
  
  loadExecutions: (pipelineId?: number) => Promise<void>
  selectExecution: (execution: PipelineExecution | null) => void
  getExecutionById: (executionId: number) => Promise<PipelineExecution>
  updateExecution: (execution: PipelineExecution) => void
  
  // Notifications
  notifications: Array<{
    id: string
    level: 'info' | 'warning' | 'error' | 'success'
    title: string
    message: string
    timestamp: string
  }>
  addNotification: (notification: Omit<AppState['notifications'][0], 'id' | 'timestamp'>) => void
  removeNotification: (id: string) => void
}

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  tools: [],
  selectedTool: null,
  toolsLoading: false,
  
  pipelines: [],
  selectedPipeline: null,
  pipelinesLoading: false,
  
  executions: [],
  selectedExecution: null,
  executionsLoading: false,
  
  notifications: [],

  // Tools actions
  loadTools: async () => {
    set({ toolsLoading: true })
    try {
      const tools = await apiService.getTools()
      set({ tools, toolsLoading: false })
    } catch (error) {
      console.error('Failed to load tools:', error)
      set({ toolsLoading: false })
      get().addNotification({
        level: 'error',
        title: '加载工具失败',
        message: '无法加载CI/CD工具列表，请稍后重试'
      })
    }
  },

  selectTool: (tool) => {
    set({ selectedTool: tool })
  },

  // Pipelines actions
  loadPipelines: async () => {
    set({ pipelinesLoading: true })
    try {
      const pipelines = await apiService.getPipelines()
      set({ pipelines, pipelinesLoading: false })
    } catch (error) {
      console.error('Failed to load pipelines:', error)
      set({ pipelinesLoading: false })
      get().addNotification({
        level: 'error',
        title: '加载流水线失败',
        message: '无法加载流水线列表，请稍后重试'
      })
    }
  },

  selectPipeline: (pipeline) => {
    set({ selectedPipeline: pipeline })
  },

  // Executions actions
  loadExecutions: async (pipelineId) => {
    set({ executionsLoading: true })
    try {
      const executions = await apiService.getExecutions(pipelineId)
      set({ executions, executionsLoading: false })
    } catch (error) {
      console.error('Failed to load executions:', error)
      set({ executionsLoading: false })
      get().addNotification({
        level: 'error',
        title: '加载执行记录失败',
        message: '无法加载执行记录列表，请稍后重试'
      })
    }
  },

  selectExecution: (execution) => {
    set({ selectedExecution: execution })
  },

  getExecutionById: async (executionId) => {
    try {
      const execution = await apiService.getExecution(executionId)
      return execution
    } catch (error) {
      console.error('Failed to load execution:', error)
      get().addNotification({
        level: 'error',
        title: '加载执行记录失败',
        message: '无法加载执行记录详情，请稍后重试'
      })
      throw error
    }
  },

  updateExecution: (execution) => {
    set(state => ({
      executions: state.executions.map(e => 
        e.id === execution.id ? execution : e
      ),
      selectedExecution: state.selectedExecution?.id === execution.id 
        ? execution 
        : state.selectedExecution
    }))
  },

  // Notifications actions
  addNotification: (notification) => {
    const id = Math.random().toString(36).substr(2, 9)
    const timestamp = new Date().toISOString()
    
    set(state => ({
      notifications: [
        ...state.notifications,
        { ...notification, id, timestamp }
      ]
    }))

    // Auto remove after 5 seconds for success and info messages
    if (notification.level === 'success' || notification.level === 'info') {
      setTimeout(() => {
        get().removeNotification(id)
      }, 5000)
    }
  },

  removeNotification: (id) => {
    set(state => ({
      notifications: state.notifications.filter(n => n.id !== id)
    }))
  },
}))
