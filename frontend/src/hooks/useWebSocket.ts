import { useEffect, useRef, useState, useCallback } from 'react'
import { PipelineExecutionWebSocket, ExecutionUpdateMessage, StepUpdateMessage, LogUpdateMessage } from '../services/websocket'

// 实时监控状态接口
interface RealtimeExecutionState {
  status: 'starting' | 'running' | 'success' | 'failed' | 'cancelled'
  totalSteps: number
  successfulSteps: number
  failedSteps: number
  executionTime: number
  message?: string
  lastUpdated: string
  pipeline_name?: string  // 添加流水线名称字段
}

interface RealtimeStepState {
  stepId: number
  stepName: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped'
  executionTime?: number
  output?: string
  errorMessage?: string
  lastUpdated: string
  type?: 'step' | 'parallel_group'  // 步骤类型字段
  steps?: RealtimeStepState[]  // 并行组内的步骤
}

interface RealtimeLogEntry {
  id: string
  timestamp: string
  level: 'info' | 'warning' | 'error' | 'debug'
  message: string
  stepName?: string
  source?: string
}

// WebSocket连接Hook
export function useWebSocket(executionId: number | null) {
  const wsRef = useRef<PipelineExecutionWebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(null)

  // 实时状态
  const [executionState, setExecutionState] = useState<RealtimeExecutionState | null>(null)
  const [stepStates, setStepStates] = useState<Map<number, RealtimeStepState>>(new Map())
  const [logs, setLogs] = useState<RealtimeLogEntry[]>([])

  // 连接WebSocket
  const connect = useCallback(async () => {
    if (!executionId || wsRef.current) {
      return
    }

    try {
      setConnectionError(null)
      const ws = new PipelineExecutionWebSocket(executionId)
      
      // 设置事件监听器
      ws.onExecutionUpdate((data: any) => {
        console.log('Execution update received:', data)
        
        // 处理 execution_status 类型的消息
        if (data.type === 'execution_status' || data.execution) {
          const execData = data.execution || data
          setExecutionState({
            status: execData.status || data.status,
            totalSteps: data.total_steps || execData.total_steps || 0,
            successfulSteps: data.successful_steps || execData.successful_steps || 0,
            failedSteps: data.failed_steps || execData.failed_steps || 0,
            executionTime: data.execution_time || execData.execution_time || 0,
            message: data.message || execData.message,
            lastUpdated: data.timestamp || new Date().toISOString(),
            pipeline_name: data.pipeline_name || execData.pipeline_name
          })
          
          // 同时更新步骤状态
          if (data.steps || execData.steps) {
            const steps = data.steps || execData.steps
            const newStepStates = new Map()
            steps.forEach((step: any, index: number) => {
              newStepStates.set(step.id || index, {
                stepId: step.id || index,
                stepName: step.name || step.step_name || `步骤 ${index + 1}`,
                status: step.status || 'pending',
                executionTime: step.execution_time,
                output: step.output || step.logs,
                errorMessage: step.error_message,
                lastUpdated: new Date().toISOString()
              })
            })
            setStepStates(newStepStates)
          }
        } else {
          // 处理旧格式
          setExecutionState({
            status: data.status,
            totalSteps: data.total_steps || 0,
            successfulSteps: data.successful_steps || 0,
            failedSteps: data.failed_steps || 0,
            executionTime: data.execution_time || 0,
            message: data.message,
            lastUpdated: data.timestamp,
            pipeline_name: data.pipeline_name
          })
        }
      })

      ws.onStepUpdate((data: StepUpdateMessage) => {
        setStepStates(prev => new Map(prev.set(data.step_id || 0, {
          stepId: data.step_id || 0,
          stepName: data.step_name,
          status: data.status,
          executionTime: data.execution_time,
          output: data.output,
          errorMessage: data.error_message,
          lastUpdated: data.timestamp
        })))
      })

      ws.onLogUpdate((data: LogUpdateMessage) => {
        const logEntry: RealtimeLogEntry = {
          id: `${data.timestamp}-${Math.random()}`,
          timestamp: data.timestamp,
          level: data.level,
          message: data.message,
          stepName: data.step_name,
          source: data.source
        }
        
        setLogs(prev => [...prev, logEntry].slice(-1000)) // 保留最新1000条日志
      })

      await ws.connect()
      wsRef.current = ws
      setIsConnected(true)
      
    } catch (error) {
      setConnectionError(error instanceof Error ? error.message : 'WebSocket连接失败')
      console.error('WebSocket连接失败:', error)
    }
  }, [executionId])

  // 断开WebSocket
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.disconnect()
      wsRef.current = null
      setIsConnected(false)
    }
  }, [])

  // 控制命令
  const stopExecution = useCallback(() => {
    wsRef.current?.stopExecution()
  }, [])

  const restartExecution = useCallback(() => {
    wsRef.current?.restartExecution()
  }, [])

  // 清空日志
  const clearLogs = useCallback(() => {
    setLogs([])
  }, [])

  // 自动连接和清理
  useEffect(() => {
    if (executionId) {
      connect()
    }
    
    return () => {
      disconnect()
    }
  }, [executionId, connect, disconnect])

  // 页面卸载时断开连接
  useEffect(() => {
    const handleBeforeUnload = () => {
      disconnect()
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
      disconnect()
    }
  }, [disconnect])

  return {
    // 连接状态
    isConnected,
    connectionError,
    
    // 实时数据
    executionState,
    stepStates: Array.from(stepStates.values()),
    logs,
    
    // 控制方法
    connect,
    disconnect,
    stopExecution,
    restartExecution,
    clearLogs
  }
}

// 全局监控Hook
export function useGlobalWebSocket() {
  const [isConnected, setIsConnected] = useState(false)
  const [globalExecutions, setGlobalExecutions] = useState<Map<number, RealtimeExecutionState>>(new Map())
  const [systemNotifications, setSystemNotifications] = useState<any[]>([])

  useEffect(() => {
    // 这里可以连接到全局监控WebSocket
    // 实现类似于useWebSocket但监听所有执行的逻辑
    
    return () => {
      // 清理连接
    }
  }, [])

  return {
    isConnected,
    globalExecutions: Array.from(globalExecutions.values()),
    systemNotifications
  }
}

export default useWebSocket
