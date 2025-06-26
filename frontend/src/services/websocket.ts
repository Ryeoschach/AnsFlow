import { PipelineExecution } from '../types'

// WebSocket消息类型定义
type WebSocketMessage = {
  type: 'execution_update' | 'step_update' | 'log_update' | 'error_update' | 'tool_status' | 'jenkins_event' | 'system_notification'
  data: any
}

// 执行状态更新消息
type ExecutionUpdateMessage = {
  type: 'execution_status'
  execution_id: number
  status: 'starting' | 'running' | 'success' | 'failed' | 'cancelled'
  timestamp: string
  pipeline_name?: string
  total_steps?: number
  successful_steps?: number
  failed_steps?: number
  execution_time?: number
  message?: string
}

// 步骤更新消息
type StepUpdateMessage = {
  type: 'step_progress'
  execution_id: number
  step_id?: number
  step_name: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped'
  timestamp: string
  step_type?: string
  execution_time?: number
  output?: string
  error_message?: string
  message?: string
}

// 日志更新消息
type LogUpdateMessage = {
  type: 'log_entry'
  execution_id: number
  timestamp: string
  level: 'info' | 'warning' | 'error' | 'debug'
  message: string
  step_name?: string
  source?: string
}

type MessageHandler = (message: WebSocketMessage) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private handlers: Map<string, MessageHandler[]> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 1000
  private url: string

  constructor() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    this.url = `${protocol}//${host}/ws/monitor/`
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
        
        // Send authentication if available
        const token = localStorage.getItem('authToken')
        if (token) {
          this.send({
            type: 'auth',
            token
          })
        }
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.attemptReconnect()
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
      this.attemptReconnect()
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.handlers.clear()
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    setTimeout(() => {
      console.log(`Attempting to reconnect WebSocket (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`)
      this.reconnectAttempts++
      this.connect()
    }, this.reconnectInterval * Math.pow(2, this.reconnectAttempts))
  }

  private send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.handlers.get(message.type) || []
    handlers.forEach(handler => {
      try {
        handler(message)
      } catch (error) {
        console.error(`Error in WebSocket message handler for type ${message.type}:`, error)
      }
    })
  }

  // Event subscription methods for real-time monitoring
  onExecutionUpdate(handler: (data: ExecutionUpdateMessage) => void): () => void {
    return this.subscribe('execution_update', (message) => {
      handler(message.data)
    })
  }

  onStepUpdate(handler: (data: StepUpdateMessage) => void): () => void {
    return this.subscribe('step_update', (message) => {
      handler(message.data)
    })
  }

  onLogUpdate(handler: (data: LogUpdateMessage) => void): () => void {
    return this.subscribe('log_update', (message) => {
      handler(message.data)
    })
  }

  onErrorUpdate(handler: (data: { execution_id: number; error_message: string; timestamp: string }) => void): () => void {
    return this.subscribe('error_update', (message) => {
      handler(message.data)
    })
  }

  onToolStatus(handler: (status: { toolId: number; isOnline: boolean; message?: string }) => void): () => void {
    return this.subscribe('tool_status', (message) => {
      handler(message.data)
    })
  }

  onJenkinsEvent(handler: (event: { 
    toolId: number; 
    jobName: string; 
    event: 'job_started' | 'job_completed' | 'job_failed' | 'build_started' | 'build_completed'
    data: any 
  }) => void): () => void {
    return this.subscribe('jenkins_event', (message) => {
      handler(message.data)
    })
  }

  onSystemNotification(handler: (notification: {
    level: 'info' | 'warning' | 'error'
    title: string
    message: string
    timestamp: string
  }) => void): () => void {
    return this.subscribe('system_notification', (message) => {
      handler(message.data)
    })
  }

  private subscribe(type: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, [])
    }
    
    this.handlers.get(type)!.push(handler)

    // Return unsubscribe function
    return () => {
      const handlers = this.handlers.get(type)
      if (handlers) {
        const index = handlers.indexOf(handler)
        if (index > -1) {
          handlers.splice(index, 1)
        }
      }
    }
  }

  // Pipeline execution specific methods
  subscribeToExecution(executionId: number): void {
    this.send({
      type: 'subscribe_execution',
      executionId
    })
  }

  unsubscribeFromExecution(executionId: number): void {
    this.send({
      type: 'unsubscribe_execution',
      executionId
    })
  }

  // Execution control commands
  stopExecution(executionId: number): void {
    this.send({
      type: 'control_command',
      command: 'stop',
      execution_id: executionId
    })
  }

  restartExecution(executionId: number): void {
    this.send({
      type: 'control_command',
      command: 'restart',
      execution_id: executionId
    })
  }

  // Jenkins job subscription
  subscribeToJenkinsJob(toolId: number, jobName: string): void {
    this.send({
      type: 'subscribe_jenkins_job',
      toolId,
      jobName
    })
  }

  unsubscribeFromJenkinsJob(toolId: number, jobName: string): void {
    this.send({
      type: 'unsubscribe_jenkins_job',
      toolId,
      jobName
    })
  }
}

// 流水线执行专用WebSocket连接类
class PipelineExecutionWebSocket {
  private ws: WebSocket | null = null
  private executionId: number
  private handlers: Map<string, MessageHandler[]> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 1000
  private url: string

  constructor(executionId: number) {
    this.executionId = executionId
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    this.url = `${protocol}//${host}/ws/executions/${executionId}/`
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      try {
        this.ws = new WebSocket(this.url)

        this.ws.onopen = () => {
          console.log(`WebSocket connected for execution ${this.executionId}`)
          this.reconnectAttempts = 0
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        this.ws.onclose = () => {
          console.log(`WebSocket disconnected for execution ${this.executionId}`)
          this.attemptReconnect()
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          reject(error)
        }
      } catch (error) {
        console.error('Failed to connect WebSocket:', error)
        reject(error)
      }
    })
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.handlers.clear()
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    setTimeout(() => {
      console.log(`Attempting to reconnect WebSocket (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`)
      this.reconnectAttempts++
      this.connect()
    }, this.reconnectInterval * Math.pow(2, this.reconnectAttempts))
  }

  private send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.handlers.get(message.type) || []
    handlers.forEach(handler => {
      try {
        handler(message)
      } catch (error) {
        console.error(`Error in WebSocket message handler for type ${message.type}:`, error)
      }
    })
  }

  private subscribe(type: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, [])
    }
    
    this.handlers.get(type)!.push(handler)

    // Return unsubscribe function
    return () => {
      const handlers = this.handlers.get(type)
      if (handlers) {
        const index = handlers.indexOf(handler)
        if (index > -1) {
          handlers.splice(index, 1)
        }
      }
    }
  }

  // Event subscription methods
  onExecutionUpdate(handler: (data: ExecutionUpdateMessage) => void): () => void {
    return this.subscribe('execution_update', (message) => {
      handler(message.data)
    })
  }

  onStepUpdate(handler: (data: StepUpdateMessage) => void): () => void {
    return this.subscribe('step_update', (message) => {
      handler(message.data)
    })
  }

  onLogUpdate(handler: (data: LogUpdateMessage) => void): () => void {
    return this.subscribe('log_update', (message) => {
      handler(message.data)
    })
  }

  // Control commands
  stopExecution(): void {
    this.send({
      type: 'control_command',
      command: 'stop'
    })
  }

  restartExecution(): void {
    this.send({
      type: 'control_command',
      command: 'restart'
    })
  }
}

export const wsService = new WebSocketService()
export { PipelineExecutionWebSocket }
export type { 
  WebSocketMessage, 
  ExecutionUpdateMessage, 
  StepUpdateMessage, 
  LogUpdateMessage 
}
export default wsService
