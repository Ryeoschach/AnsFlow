import { PipelineExecution } from '../types'

type WebSocketMessage = {
  type: 'execution_update' | 'tool_status' | 'jenkins_event' | 'system_notification'
  data: any
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
    this.url = `${protocol}//${host}/ws`
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

  // Event subscription methods
  onExecutionUpdate(handler: (execution: PipelineExecution) => void): () => void {
    return this.subscribe('execution_update', (message) => {
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

  // Pipeline execution subscription
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

export const wsService = new WebSocketService()
export default wsService
