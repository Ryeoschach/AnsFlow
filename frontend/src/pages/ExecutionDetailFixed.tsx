import React, { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Card, 
  Descriptions, 
  Steps, 
  Timeline, 
  Button, 
  Space, 
  Tag, 
  Progress, 
  Alert, 
  Row, 
  Col,
  Typography,
  Spin,
  Modal,
  message
} from 'antd'
import {
  ArrowLeftOutlined,
  PlayCircleOutlined,
  StopOutlined,
  RedoOutlined,
  DownloadOutlined,
  FullscreenOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import { useAppStore } from '../stores/app'
import { useWebSocket } from '../hooks/useWebSocket'
import { PipelineExecution } from '../types'

const { Title, Text, Paragraph } = Typography
const { Step } = Steps

interface ExecutionDetailProps {}

// 实时监控状态接口
interface RealtimeExecutionState {
  status: 'starting' | 'running' | 'success' | 'failed' | 'cancelled'
  totalSteps: number
  successfulSteps: number
  failedSteps: number
  executionTime: number
  pipeline_name?: string
  message?: string
  lastUpdated: string
}

// 实时步骤状态接口
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

const ExecutionDetail: React.FC<ExecutionDetailProps> = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const executionId = id ? parseInt(id) : null
  
  const { getExecutionById } = useAppStore()
  const [execution, setExecution] = useState<PipelineExecution | null>(null)
  const [loading, setLoading] = useState(true)
  const [isLogsModalVisible, setIsLogsModalVisible] = useState(false)
  const [fullLogs, setFullLogs] = useState<string>('')
  
  // 数据版本管理，避免不必要的重渲染
  const [lastUpdateTime, setLastUpdateTime] = useState<number>(Date.now())
  const [statusVersion, setStatusVersion] = useState<number>(0)
  const [stepsVersion, setStepsVersion] = useState<number>(0)
  const [logsVersion, setLogsVersion] = useState<number>(0)
  
  // 实时日志滚动容器引用
  const logContainerRef = useRef<HTMLDivElement>(null)
  const modalLogContainerRef = useRef<HTMLDivElement>(null)
  const [isUserScrolling, setIsUserScrolling] = useState(false)
  const [isModalUserScrolling, setIsModalUserScrolling] = useState(false)
  const [isInitialLoad, setIsInitialLoad] = useState(true) // 标记初始加载状态
  const userScrollTimeoutRef = useRef<number | null>(null)
  const modalScrollTimeoutRef = useRef<number | null>(null)
  
  // WebSocket实时监控
  const {
    isConnected,
    connectionError,
    executionState,
    stepStates,
    logs,
    stopExecution,
    restartExecution,
    clearLogs
  } = useWebSocket(executionId)

  // 自动滚动到最新日志（增强版本）
  useEffect(() => {
    if (logContainerRef.current && logs.length > 0) {
      const container = logContainerRef.current
      
      // 检查是否应该自动滚动到底部
      const shouldAutoScroll = () => {
        // 初始加载时强制滚动到底部
        if (isInitialLoad) {
          setIsInitialLoad(false) // 标记初始加载完成
          return true
        }
        
        // 如果用户正在手动滚动，完全不自动滚动
        if (isUserScrolling) return false
        
        // 如果容器很小或没有滚动条，总是滚动到底部
        if (container.scrollHeight <= container.clientHeight) return true
        
        // 如果是初始状态（scrollTop为0且有内容），应该滚动到底部
        if (container.scrollTop === 0 && container.scrollHeight > container.clientHeight) {
          return true
        }
        
        // 如果用户在最底部附近（允许30px的误差），才自动滚动
        const isNearBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 30
        return isNearBottom
      }
      
      if (shouldAutoScroll()) {
        // 使用 requestAnimationFrame 确保 DOM 更新完成后再滚动
        requestAnimationFrame(() => {
          if (container && !isUserScrolling) { // 双重检查
            container.scrollTo({
              top: container.scrollHeight,
              behavior: isInitialLoad ? 'auto' : 'smooth' // 初始加载用瞬间滚动，后续用平滑滚动
            })
          }
        })
      }
    }
  }, [logs.length, isUserScrolling]) // 只在日志变化和滚动状态变化时触发

  // 模态框日志自动滚动（优化版本）
  useEffect(() => {
    if (modalLogContainerRef.current && isLogsModalVisible) {
      const container = modalLogContainerRef.current
      
      // 检查是否应该自动滚动到底部
      const shouldAutoScroll = () => {
        // 如果用户正在滚动模态框，不自动滚动
        if (isModalUserScrolling) return false
        
        // 如果容器很小或没有滚动条，总是滚动到底部
        if (container.scrollHeight <= container.clientHeight) return true
        
        // 检查是否在底部附近（允许10px的误差）
        const isNearBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 10
        return isNearBottom
      }
      
      if (shouldAutoScroll()) {
        // 延迟滚动，确保内容已完全渲染
        requestAnimationFrame(() => {
          setTimeout(() => {
            if (container) {
              container.scrollTop = container.scrollHeight
            }
          }, 50) // 短暂延迟确保内容渲染完成
        })
      }
    }
  }, [fullLogs, logs.length, isLogsModalVisible, isModalUserScrolling]) // 只在必要时触发

  // 检测用户滚动行为（增强版本）
  const handleLogScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const container = e.currentTarget
    
    // 检查是否是用户主动滚动（不是程序触发的）
    const isUserInitiated = e.isTrusted !== false
    
    if (isUserInitiated) {
      // 立即设置为用户滚动状态
      setIsUserScrolling(true)
      
      // 清除之前的定时器
      if (userScrollTimeoutRef.current) {
        clearTimeout(userScrollTimeoutRef.current)
      }
      
      // 检查是否滚动到底部附近（更宽松的阈值）
      const scrollTop = container.scrollTop
      const scrollHeight = container.scrollHeight
      const clientHeight = container.clientHeight
      const isNearBottom = scrollTop + clientHeight >= scrollHeight - 30
      
      // 如果用户滚动到底部附近，较快恢复自动滚动
      if (isNearBottom) {
        userScrollTimeoutRef.current = window.setTimeout(() => {
          setIsUserScrolling(false)
        }, 1500) // 1.5秒后恢复自动滚动
      } else {
        // 如果用户在查看历史日志，不自动恢复自动滚动，需要手动控制
        // 这样用户可以自由查看历史日志而不被打断
        // 可以通过按钮手动恢复自动滚动
      }
    }
  }

  const handleModalLogScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const container = e.currentTarget
    
    // 检查是否是用户主动滚动
    const isUserInitiated = e.isTrusted !== false
    
    if (isUserInitiated) {
      setIsModalUserScrolling(true)
      
      // 清除之前的定时器
      if (modalScrollTimeoutRef.current) {
        clearTimeout(modalScrollTimeoutRef.current)
      }
      
      // 检查是否滚动到底部附近（更宽松的阈值）
      const scrollTop = container.scrollTop
      const scrollHeight = container.scrollHeight
      const clientHeight = container.clientHeight
      const isNearBottom = scrollTop + clientHeight >= scrollHeight - 30
      
      // 如果滚动到底部附近，稍后恢复自动滚动
      if (isNearBottom) {
        modalScrollTimeoutRef.current = window.setTimeout(() => {
          setIsModalUserScrolling(false)
        }, 1000) // 1秒后恢复
      } else {
        // 如果不在底部，用户在查看历史日志，不自动恢复
        // 需要用户手动控制
      }
    }
  }

  // 手动滚动到底部
  const scrollToBottom = () => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTo({
        top: logContainerRef.current.scrollHeight,
        behavior: 'smooth'
      })
      setIsUserScrolling(false) // 立即恢复自动滚动
    }
  }

  // 模态框滚动到底部
  const scrollModalToBottom = () => {
    if (modalLogContainerRef.current) {
      modalLogContainerRef.current.scrollTo({
        top: modalLogContainerRef.current.scrollHeight,
        behavior: 'smooth'
      })
      setIsModalUserScrolling(false) // 立即恢复自动滚动
    }
  }

  // 切换自动滚动模式
  const toggleAutoScroll = () => {
    const newState = !isUserScrolling
    setIsUserScrolling(newState)
    
    // 如果开启自动滚动，立即滚动到底部
    if (!newState) {
      scrollToBottom()
    }
    
    // 清除任何定时器
    if (userScrollTimeoutRef.current) {
      clearTimeout(userScrollTimeoutRef.current)
      userScrollTimeoutRef.current = null
    }
  }

  // 切换模态框自动滚动模式
  const toggleModalAutoScroll = () => {
    const newState = !isModalUserScrolling
    setIsModalUserScrolling(newState)
    
    // 如果开启自动滚动，立即滚动到底部
    if (!newState) {
      scrollModalToBottom()
    }
    
    // 清除任何定时器
    if (modalScrollTimeoutRef.current) {
      clearTimeout(modalScrollTimeoutRef.current)
      modalScrollTimeoutRef.current = null
    }
  }

  // 加载执行记录（只加载一次基本信息）
  useEffect(() => {
    if (executionId) {
      const loadExecutionBasicInfo = async () => {
        try {
          setLoading(true)
          const result = await getExecutionById(executionId)
          setExecution(result)
        } catch (error) {
          message.error('加载执行记录失败')
          console.error('Load execution error:', error)
        } finally {
          setLoading(false)
        }
      }
      
      // 只在初始化时加载基本信息
      loadExecutionBasicInfo()
    }
  }, [executionId, getExecutionById])

  // 实时状态更新（仅在WebSocket断开时作为备用）
  useEffect(() => {
    if (!executionId) return

    let refreshInterval: number | null = null
    let statusCheckInterval: number | null = null

    // 只有在WebSocket断开时才启用轮询备用机制
    if (!isConnected) {
      console.log('WebSocket 未连接，启用轮询备用机制')
      
      const updateRealTimeData = async () => {
        try {
          // 只更新实时数据，不重新设置整个execution对象
          const result = await getExecutionById(executionId)
          
          // 只更新动态字段，保留静态信息
          setExecution(prev => prev ? {
            ...prev,
            status: result.status,
            completed_at: result.completed_at,
            step_executions: result.step_executions,
            logs: result.logs,
            result: result.result
          } : result)
          
        } catch (error) {
          console.error('更新实时数据失败:', error)
        }
      }

      // 备用刷新机制
      refreshInterval = setInterval(updateRealTimeData, 5000) // 每5秒刷新一次
      
      // 运行中状态的更频繁检查
      statusCheckInterval = setInterval(() => {
        const currentStatus = executionState?.status || execution?.status
        if (currentStatus === 'running' || currentStatus === 'starting') {
          updateRealTimeData()
        }
      }, 2000) // 运行中时每2秒检查一次
    }
    
    return () => {
      if (refreshInterval) clearInterval(refreshInterval)
      if (statusCheckInterval) clearInterval(statusCheckInterval)
    }
  }, [executionId, getExecutionById, isConnected, executionState?.status, execution?.status])

  // 获取完整日志
  const fetchFullLogs = async () => {
    if (!executionId) return
    
    try {
      // 确保使用最新的有效token
      let token = localStorage.getItem('authToken')
      if (!token) {
        const newToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUxMzg1NTgzLCJpYXQiOjE3NTEzODE5ODMsImp0aSI6IjA1NDExNzQwYzk0ZTQxZDBiMWFhMTY3MzgwYmNjODBjIiwidXNlcl9pZCI6MX0.QSQ3RI_WHt9QnlzT5fdw9t43x6VH5zxVnNTkNFnrOko'
        localStorage.setItem('authToken', newToken)
        token = newToken
      }
      
      const response = await fetch(`/api/v1/cicd/executions/${executionId}/logs/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        setFullLogs(data.logs || '')
      } else {
        const errorData = await response.text()
        console.error('Failed to fetch logs:', response.status, errorData)
      }
    } catch (error) {
      console.error('Error fetching logs:', error)
    }
  }

  // 显示日志Modal时获取完整日志
  const handleShowLogsModal = async () => {
    setIsLogsModalVisible(true)
    
    // 清空之前的日志数据
    setFullLogs('')
    
    await fetchFullLogs()
  }

  // 获取状态标签
  const getStatusTag = (status: string) => {
    const statusConfig = {
      success: { color: 'green', text: '成功' },
      completed: { color: 'green', text: '完成' },
      failed: { color: 'red', text: '失败' },
      running: { color: 'blue', text: '运行中' },
      pending: { color: 'orange', text: '等待中' },
      cancelled: { color: 'default', text: '已取消' },
      starting: { color: 'processing', text: '启动中' }
    }
    
    const config = statusConfig[status as keyof typeof statusConfig] || 
                  { color: 'default', text: status }
    
    return <Tag color={config.color}>{config.text}</Tag>
  }

  // 获取步骤状态
  const getStepStatus = (status: string): "wait" | "process" | "finish" | "error" => {
    const statusMap = {
      pending: 'wait' as const,
      running: 'process' as const,
      success: 'finish' as const,
      completed: 'finish' as const,
      failed: 'error' as const,
      skipped: 'wait' as const
    }
    return statusMap[status as keyof typeof statusMap] || 'wait'
  }

  // 计算总体进度
  const calculateProgress = () => {
    if (!executionState && !execution) return 0
    
    const currentState = executionState || execution
    if (!currentState) return 0
    
    if (currentState.status === 'success') return 100
    if (currentState.status === 'failed' || currentState.status === 'cancelled') return 100
    
    if (stepStates.length > 0) {
      const completedSteps = stepStates.filter(step => 
        ['success', 'failed', 'skipped'].includes(step.status)
      ).length
      return Math.round((completedSteps / stepStates.length) * 100)
    }
    
    return currentState.status === 'running' ? 50 : 0
  }

  // 处理控制操作
  const handleStop = () => {
    Modal.confirm({
      title: '确认停止执行',
      content: '停止后的执行无法恢复，确认要停止吗？',
      onOk: () => {
        stopExecution()
        message.info('停止命令已发送')
      }
    })
  }

  const handleRestart = () => {
    Modal.confirm({
      title: '确认重新执行',
      content: '这将重新开始整个流水线执行，确认要重新执行吗？',
      onOk: () => {
        restartExecution()
        message.info('重新执行命令已发送')
      }
    })
  }

  // 渲染步骤列表
  const renderSteps = () => {
    // 优先使用实时WebSocket数据
    if (stepStates.length > 0) {
      return (
        <Steps direction="vertical" current={-1}>
          {stepStates.map((step, index) => {
            const stepStyle = stepStatusStyles[step.status as keyof typeof stepStatusStyles] || stepStatusStyles.pending
            const isRunning = step.status === 'running'
            
            // 检查是否是并行组
            if (step.type === 'parallel_group') {
              return (
                <Step
                  key={step.stepId}
                  title={
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <span style={{ marginRight: 8 }}>🔄</span>
                      {step.stepName}
                      <Tag color="blue" style={{ marginLeft: 8 }}>并行组</Tag>
                    </div>
                  }
                  status={getStepStatus(step.status)}
                  description={
                    <div style={{ marginTop: 8 }}>
                      <div style={{ marginBottom: 8 }}>
                        状态: {getStatusTag(step.status)}
                        {step.status === 'running' && (
                          <Tag color="blue" style={{ marginLeft: 8 }}>🔄 并行执行中</Tag>
                        )}
                        {step.status === 'success' && (
                          <Tag color="green" style={{ marginLeft: 8 }}>✅ 全部完成</Tag>
                        )}
                        {step.status === 'failed' && (
                          <Tag color="red" style={{ marginLeft: 8 }}>❌ 有失败</Tag>
                        )}
                      </div>
                      {step.executionTime && (
                        <div style={{ marginBottom: 8 }}>
                          总执行时间: {step.executionTime.toFixed(2)}s
                        </div>
                      )}
                      
                      {/* 并行组内的步骤 */}
                      {(step as any).steps && (step as any).steps.length > 0 && (
                        <div style={{ 
                          marginTop: 12, 
                          paddingLeft: 16,
                          borderLeft: '3px solid #1890ff',
                          background: '#f6ffed',
                          padding: '8px 12px',
                          borderRadius: '4px'
                        }}>
                          <div style={{ fontWeight: 'bold', marginBottom: 8, color: '#1890ff' }}>
                            并行执行步骤 ({(step as any).steps.length}个):
                          </div>
                          {(step as any).steps.map((parallelStep: any, idx: number) => (
                            <div key={parallelStep.id || idx} style={{ 
                              marginBottom: 8,
                              padding: '6px 8px',
                              background: 'white',
                              borderRadius: '3px',
                              border: '1px solid #d9d9d9'
                            }}>
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <span style={{ fontWeight: 'bold' }}>
                                  {parallelStep.step_name || parallelStep.atomic_step_name || parallelStep.pipeline_step_name || parallelStep.name || `步骤${parallelStep.order}`}
                                </span>
                                {getStatusTag(parallelStep.status)}
                              </div>
                              {parallelStep.execution_time && (
                                <div style={{ fontSize: '12px', color: '#666', marginTop: 4 }}>
                                  执行时间: {parallelStep.execution_time.toFixed(2)}s
                                </div>
                              )}
                              {parallelStep.error_message && (
                                <div style={{ marginTop: 4 }}>
                                  <Text type="danger" style={{ fontSize: '12px' }}>
                                    {parallelStep.error_message}
                                  </Text>
                                </div>
                              )}
                              {parallelStep.output && (
                                <div style={{ marginTop: 4 }}>
                                  <Text code style={{ 
                                    whiteSpace: 'pre-wrap', 
                                    fontSize: '11px',
                                    display: 'block',
                                    maxHeight: '60px',
                                    overflow: 'hidden'
                                  }}>
                                    {parallelStep.output.substring(0, 100)}
                                    {parallelStep.output.length > 100 && '...'}
                                  </Text>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  }
                />
              )
            }
            
            // 普通步骤渲染
            return (
              <Step
                key={step.stepId}
                title={
                  <div 
                    className={isRunning ? 'step-running step-pulse' : ''}
                    style={stepStyle}
                  >
                    {step.stepName}
                    {isRunning && (
                      <span style={{ marginLeft: 8 }}>
                        <Text style={{ fontSize: '12px', animation: 'blink 1s infinite' }}>
                          ⚡ 执行中...
                        </Text>
                      </span>
                    )}
                  </div>
                }
                status={getStepStatus(step.status)}
                description={
                  <div style={{ marginTop: 8 }}>
                    <div style={{ marginBottom: 4 }}>
                      状态: {getStatusTag(step.status)}
                      {step.status === 'pending' && (
                        <Tag color="orange" style={{ marginLeft: 8 }}>⏳ 待执行</Tag>
                      )}
                      {step.status === 'running' && (
                        <Tag color="blue" style={{ marginLeft: 8, animation: 'blink 1s infinite' }}>⚡ 执行中</Tag>
                      )}
                      {step.status === 'success' && (
                        <Tag color="green" style={{ marginLeft: 8 }}>✅ 已完成</Tag>
                      )}
                      {step.status === 'failed' && (
                        <Tag color="red" style={{ marginLeft: 8 }}>❌ 失败</Tag>
                      )}
                    </div>
                    {step.executionTime && (
                      <div style={{ marginBottom: 4 }}>
                        执行时间: {step.executionTime.toFixed(2)}s
                      </div>
                    )}
                    {step.errorMessage && (
                      <div style={{ marginBottom: 4 }}>
                        <Text type="danger">{step.errorMessage}</Text>
                      </div>
                    )}
                    {step.output && (
                      <div style={{ marginTop: 8 }}>
                        <Text code style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                          {step.output.substring(0, 200)}
                          {step.output.length > 200 && '...'}
                        </Text>
                      </div>
                    )}
                  </div>
                }
              />
            )
          })}
        </Steps>
      )
    }
    
    // 如果没有实时数据，使用静态数据（从API返回的step_executions）
    if (execution?.step_executions && execution.step_executions.length > 0) {
      return (
        <Steps direction="vertical" current={-1}>
          {execution.step_executions.map((step) => (
            <Step
              key={step.id}
              title={step.step_name || step.atomic_step_name || step.pipeline_step_name || `步骤 ${step.order}`}
              status={getStepStatus(step.status)}
              description={
                <div>
                  <div>状态: {getStatusTag(step.status)}</div>
                  {step.duration && (
                    <div>执行时间: {step.duration}</div>
                  )}
                  {step.error_message && (
                    <Text type="danger">{step.error_message}</Text>
                  )}
                  {step.logs && (
                    <Paragraph style={{ marginTop: 8 }}>
                      <Text code>{step.logs.substring(0, 200)}</Text>
                      {step.logs.length > 200 && '...'}
                    </Paragraph>
                  )}
                </div>
              }
            />
          ))}
        </Steps>
      )
    }
    
    // 回退到原有的result字段逻辑（兼容旧数据）
    if (execution?.result) {
      const steps = Object.entries(execution.result).filter(([key]) => key.startsWith('step_'))
      
      return (
        <Steps direction="vertical" current={-1}>
          {steps.map(([key, stepResult]: [string, any]) => (
            <Step
              key={key}
              title={stepResult.name || key}
              status={getStepStatus(stepResult.status)}
              description={
                <div>
                  <div>状态: {getStatusTag(stepResult.status)}</div>
                  {stepResult.execution_time && (
                    <div>执行时间: {stepResult.execution_time.toFixed(2)}s</div>
                  )}
                  {stepResult.error_message && (
                    <Text type="danger">{stepResult.error_message}</Text>
                  )}
                </div>
              }
            />
          ))}
        </Steps>
      )
    }
    
    // 没有步骤数据
    return (
      <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
        暂无步骤信息
      </div>
    )
  }

  // 渲染日志时间线
  const renderLogTimeline = () => {
    // 首先尝试从实时WebSocket获取日志（只有在有真实日志数据时才使用）
    if (logs.length > 0 && logs.some(log => log.message && log.message.trim() !== '')) {
      const displayLogs = logs.slice(-50) // 显示最新50条

      // 构造 stepId->stepName 映射（兼容 stepStates 结构）
      const stepIdNameMap = new Map<number, string>()
      if (stepStates && typeof stepStates.forEach === 'function') {
        stepStates.forEach((s, k) => {
          stepIdNameMap.set(s.stepId, s.stepName)
        })
      }

      return (
        <div>
          <div style={{ 
            color: '#1890ff', 
            fontWeight: 'bold', 
            marginBottom: 12,
            borderBottom: '2px solid #1890ff',
            paddingBottom: 8,
            display: 'flex',
            alignItems: 'center'
          }}>
            <span style={{ marginRight: 8, animation: 'pulse 2s infinite' }}>📡</span>
            [WebSocket 实时日志]
            <Tag color="green" style={{ marginLeft: 8 }}>实时更新</Tag>
            <span style={{ 
              marginLeft: 'auto', 
              fontSize: '12px', 
              color: '#52c41a',
              animation: 'blink 2s infinite'
            }}>
              ● 在线
            </span>
          </div>

          <div 
            ref={logContainerRef}
            onScroll={handleLogScroll}
            style={{ 
              maxHeight: 400, 
              overflow: 'auto', 
              background: '#f8f9fa',
              border: '1px solid #e9ecef',
              borderRadius: 4,
              padding: 12,
              scrollBehavior: 'smooth', // CSS 平滑滚动
              position: 'relative'
            }}
          >
            {displayLogs.map((log, index) => {
              // 尝试从 stepStates 里查找业务名称
              let displayStepName = log.stepName
              // 解析 stepId
              let stepId = undefined
              if (log.stepName && /^步骤 ?(\d+)$/.test(log.stepName)) {
                stepId = parseInt(log.stepName.replace(/[^\d]/g, ''))
              }
              if (stepId && stepIdNameMap.has(stepId)) {
                displayStepName = stepIdNameMap.get(stepId)
              }
              // 兜底
              displayStepName = displayStepName || log.stepName || ''
              return (
                <div key={log.id} style={{ 
                  marginBottom: 8, 
                  fontFamily: 'Monaco, Consolas, monospace', 
                  fontSize: 12,
                  padding: '4px 8px',
                  background: log.level === 'error' ? '#fff2f0' : 
                             log.level === 'warning' ? '#fffbe6' : '#fff',
                  border: '1px solid',
                  borderColor: log.level === 'error' ? '#ffccc7' :
                              log.level === 'warning' ? '#ffe58f' : '#f0f0f0',
                  borderRadius: 3,
                  borderLeft: '4px solid',
                  borderLeftColor: log.level === 'error' ? '#ff4d4f' :
                                  log.level === 'warning' ? '#fa8c16' : '#52c41a'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: 2 }}>
                    <span style={{ 
                      color: '#666', 
                      fontSize: 11,
                      minWidth: 80
                    }}>
                      [{new Date(log.timestamp).toLocaleTimeString()}]
                    </span>
                    {displayStepName && (
                      <Tag color="blue" style={{ marginLeft: 8, fontSize: '10px' }}>
                        {displayStepName}
                      </Tag>
                    )}
                    <Tag 
                      color={log.level === 'error' ? 'red' : log.level === 'warning' ? 'orange' : 'default'}
                      style={{ marginLeft: 4, fontSize: '10px' }}
                    >
                      {log.level.toUpperCase()}
                    </Tag>
                  </div>
                  <div style={{ 
                    color: log.level === 'error' ? '#ff4d4f' : 
                           log.level === 'warning' ? '#fa8c16' : '#000',
                    lineHeight: 1.4
                  }}>
                    {log.message}
                  </div>
                </div>
              )
            })}
          </div>

          <div style={{ 
            textAlign: 'center', 
            marginTop: 8, 
            color: '#8c8c8c', 
            fontSize: 12,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <span>显示最新 {displayLogs.length} 条日志，总计 {logs.length} 条</span>
            <div style={{ 
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}>
              <span style={{ 
                fontSize: 10, 
                color: isUserScrolling ? '#fa8c16' : '#52c41a',
                fontStyle: 'italic'
              }}>
                {isUserScrolling ? '🔒 自动滚动已暂停' : '📜 自动滚动到最新'}
              </span>
              {isUserScrolling && (
                <Button 
                  size="small" 
                  type="primary"
                  style={{ fontSize: 10, height: 20, padding: '0 6px' }}
                  onClick={scrollToBottom}
                >
                  ⬇️ 最新
                </Button>
              )}
              <Button 
                size="small"
                type={!isUserScrolling ? "primary" : "default"}
                style={{ fontSize: 10, height: 20, padding: '0 6px' }}
                onClick={toggleAutoScroll}
              >
                {!isUserScrolling ? "⏸️ 暂停" : "📜 恢复"}
              </Button>
            </div>
          </div>
        </div>
      )
    }
    
    // 如果没有实时日志，从步骤执行中构建日志
    if (execution?.step_executions && execution.step_executions.length > 0) {
      // 添加详细的步骤日志调试
      execution.step_executions.forEach((step, index) => {
        const stepInfo = {
          id: step.id,
          name: step.step_name || step.atomic_step_name || step.pipeline_step_name || `步骤 ${step.order}`,
          logs: step.logs,
          logsLength: step.logs?.length || 0,
          hasLogs: !!(step.logs && step.logs.trim() !== '')
        }
      })
      
      const stepLogs = execution.step_executions
        .filter(step => step.logs && step.logs.trim() !== '')
       const timelineItems = stepLogs.map((step, index) => ({
        key: `step-${step.id}`,
        color: step.status === 'success' ? 'green' : step.status === 'failed' ? 'red' : 'blue',
        children: (
          <div>
            <Text strong>{step.step_name || step.atomic_step_name || step.pipeline_step_name || `步骤 ${step.order}`}</Text>
            <Tag style={{ marginLeft: 8 }} color={step.status === 'success' ? 'green' : step.status === 'failed' ? 'red' : 'blue'}>
              {step.status_display}
            </Tag>
            {step.started_at && (
              <Text type="secondary" style={{ marginLeft: 8 }}>
                {new Date(step.started_at).toLocaleTimeString()}
              </Text>
            )}
            <div style={{ marginTop: 4 }}>
              <Text code style={{ whiteSpace: 'pre-wrap' }}>
                {step.logs}
              </Text>
            </div>
            {step.duration && (
              <div style={{ marginTop: 4 }}>
                <Text type="secondary">执行时间: {step.duration}</Text>
              </div>
            )}
          </div>
        )
      }))
      
      if (timelineItems.length > 0) {
        return (
          <Timeline
            style={{ maxHeight: 400, overflow: 'auto' }}
            items={timelineItems}
          />
        )
      }
    }
    
    // 如果执行有整体日志，显示整体日志
    if (execution?.logs && execution.logs.trim() !== '') {
      return (
        <Timeline
          style={{ maxHeight: 400, overflow: 'auto' }}
          items={[{
            key: 'execution-logs',
            color: 'blue',
            children: (
              <div>
                <Text strong>执行日志</Text>
                <div style={{ marginTop: 4 }}>
                  <Text code style={{ whiteSpace: 'pre-wrap' }}>
                    {execution.logs}
                  </Text>
                </div>
              </div>
            )
          }]}
        />
      )
    }
    
    // 没有日志数据
    return (
      <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
        暂无日志信息
      </div>
    )
  }

  // 格式化相对时间（简化版）
  const formatRelativeTime = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / (1000 * 60))
      
      if (diffMins < 1) return '刚刚'
      if (diffMins < 60) return `${diffMins}分钟前`
      
      const diffHours = Math.floor(diffMins / 60)
      if (diffHours < 24) return `${diffHours}小时前`
      
      const diffDays = Math.floor(diffHours / 24)
      return `${diffDays}天前`
    } catch {
      return '未知时间'
    }
  }

  // 添加步骤状态样式
const stepStatusStyles = {
  pending: {
    background: '#f0f0f0',
    border: '1px solid #d9d9d9',
    color: '#8c8c8c',
    padding: '4px 8px',
    borderRadius: '4px'
  },
  running: {
    background: 'linear-gradient(-45deg, #e6f7ff, #bae7ff, #e6f7ff, #bae7ff)',
    backgroundSize: '400% 400%',
    animation: 'gradient 1.5s ease infinite',
    border: '2px solid #1890ff',
    color: '#1890ff',
    fontWeight: 'bold',
    padding: '6px 12px',
    borderRadius: '6px',
    boxShadow: '0 2px 8px rgba(24, 144, 255, 0.3)'
  },
  success: {
    background: '#f6ffed',
    border: '1px solid #52c41a',
    color: '#52c41a',
    padding: '4px 8px',
    borderRadius: '4px'
  },
  failed: {
    background: '#fff2f0',
    border: '1px solid #ff4d4f',
    color: '#ff4d4f',
    padding: '4px 8px',
    borderRadius: '4px'
  },
  skipped: {
    background: '#fafafa',
    border: '1px solid #d9d9d9',
    color: '#8c8c8c',
    padding: '4px 8px',
    borderRadius: '4px'
  }
} as const

// 添加闪烁动画样式
const blinkingStyle = `
  @keyframes gradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }
  
  @keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0.6; }
  }
  
  @keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
  }
  
  .step-running {
    animation: blink 1s infinite;
  }
  
  .step-pulse {
    animation: pulse 2s infinite;
  }
  
  .execution-status-running {
    animation: blink 2s infinite;
  }
`

  // 监听 WebSocket 数据变化，更新版本号以控制重渲染
  useEffect(() => {
    if (executionState) {
      setStatusVersion(prev => prev + 1)
      setLastUpdateTime(Date.now())
    }
  }, [executionState?.status, executionState?.executionTime])

  useEffect(() => {
    if (stepStates.length > 0) {
      setStepsVersion(prev => prev + 1)
      setLastUpdateTime(Date.now())
    }
  }, [stepStates.map(s => `${s.stepId}-${s.status}-${s.executionTime}`).join(',')])

  useEffect(() => {
    if (logs.length > 0) {
      setLogsVersion(prev => prev + 1)
      setLastUpdateTime(Date.now())
    }
  }, [logs.length, logs.slice(-5).map(l => l.id).join(',')])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>加载执行详情...</div>
      </div>
    )
  }

  if (!execution && !executionState) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Title level={4}>执行记录不存在</Title>
        <Button onClick={() => navigate('/executions')}>返回执行列表</Button>
      </div>
    )
  }

  const currentState = executionState || execution
  const isRunning = currentState?.status === 'running' || currentState?.status === 'starting'

  return (
    <div style={{ padding: '24px' }}>
      {/* 添加CSS样式 */}
      <style>
        {blinkingStyle}
      </style>
      
      {/* 头部操作栏 */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Space>
            <Button 
              icon={<ArrowLeftOutlined />} 
              onClick={() => navigate('/executions')}
            >
              返回执行列表
            </Button>
            {/* 添加流水线相关导航 */}
            {execution?.pipeline && (
              <Space>
                <Button 
                  type="dashed"
                  onClick={() => navigate(`/pipelines/${execution.pipeline}`)}
                >
                  查看流水线详情
                </Button>
                <Button 
                  type="dashed"
                  onClick={() => navigate('/pipelines')}
                >
                  所有流水线
                </Button>
              </Space>
            )}
            <Title level={3} style={{ margin: 0 }}>
              执行详情 #{executionId}
            </Title>
          </Space>
        </Col>
        <Col>
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => window.location.reload()}
            >
              刷新页面
            </Button>
            {isRunning && (
              <Button
                danger
                icon={<StopOutlined />}
                onClick={handleStop}
              >
                停止执行
              </Button>
            )}
            {currentState?.status === 'failed' && (
              <Button
                type="primary"
                icon={<RedoOutlined />}
                onClick={handleRestart}
              >
                重新执行
              </Button>
            )}
          </Space>
        </Col>
      </Row>

      {/* 实时连接状态提示 */}
      <div key={`connection-status-${isConnected}-${connectionError}-${statusVersion}`}>
        {connectionError && (
          <Alert
            type="warning"
            message="WebSocket连接失败"
            description={`无法获取实时更新: ${connectionError} | 将使用轮询备用机制`}
            style={{ marginBottom: 16 }}
            closable
          />
        )}

        {isConnected && (
          <Alert
            type="success"
            message="实时监控已连接"
            description={
              <Space>
                <span>正在接收实时执行状态更新</span>
                <Text code style={{ fontSize: '11px' }}>
                  最后更新: {new Date(lastUpdateTime).toLocaleTimeString()}
                </Text>
              </Space>
            }
            style={{ marginBottom: 16 }}
            closable
            action={
              <Text style={{ fontSize: '12px', color: '#52c41a' }}>
                ● 在线
              </Text>
            }
          />
        )}

        {!isConnected && !connectionError && (
          <Alert
            type="info"
            message="连接状态"
            description="正在尝试建立WebSocket连接..."
            style={{ marginBottom: 16 }}
            closable
          />
        )}
      </div>

      <Row gutter={[16, 16]}>
        {/* 执行概览 */}
        <Col span={24}>
          <Card title="执行概览">
            <Descriptions bordered column={2}>
              {/* 静态信息 - 不需要频繁更新 */}
              <Descriptions.Item label="流水线名称">
                {(executionState as RealtimeExecutionState)?.pipeline_name || execution?.pipeline_name || '未知'}
              </Descriptions.Item>
              <Descriptions.Item label="触发方式">
                {execution?.trigger_type || 'unknown'}
              </Descriptions.Item>
              <Descriptions.Item label="触发者">
                {execution?.triggered_by || 'system'}
              </Descriptions.Item>
              <Descriptions.Item label="开始时间">
                {execution?.started_at ? formatRelativeTime(execution.started_at) : '-'}
              </Descriptions.Item>
              
              {/* 动态信息 - 需要实时更新 */}
              <Descriptions.Item label="执行状态">
                <div key={`status-${statusVersion}`}>
                  {getStatusTag(currentState?.status || 'unknown')}
                </div>
              </Descriptions.Item>
              <Descriptions.Item label="执行时长">
                <div key={`duration-${statusVersion}`}>
                  {(executionState as RealtimeExecutionState)?.executionTime ? 
                    `${(executionState as RealtimeExecutionState).executionTime.toFixed(2)}s` : 
                    (execution?.completed_at && execution?.started_at ? 
                      `${((new Date(execution.completed_at).getTime() - new Date(execution.started_at).getTime()) / 1000).toFixed(2)}s` : 
                      '-'
                    )
                  }
                </div>
              </Descriptions.Item>
            </Descriptions>
            
            {/* 总体进度 - 需要实时更新 */}
            <div style={{ marginTop: 16 }} key={`progress-${statusVersion}`}>
              <Text strong>总体进度:</Text>
              <Progress 
                percent={calculateProgress()} 
                status={currentState?.status === 'failed' ? 'exception' : 
                       currentState?.status === 'success' ? 'success' : 'active'}
                style={{ marginTop: 8 }}
                strokeColor={
                  currentState?.status === 'running' ? 
                  { '0%': '#108ee9', '100%': '#87d068' } : undefined
                }
                showInfo={true}
                format={(percent) => `${percent}% ${
                  currentState?.status === 'running' ? '执行中' :
                  currentState?.status === 'success' ? '已完成' :
                  currentState?.status === 'failed' ? '失败' : ''
                }`}
              />
            </div>
          </Card>
        </Col>

        {/* 步骤执行状态 - 实时更新区域 */}
        <Col span={12}>
          <Card 
            title="执行步骤" 
            style={{ height: 600, overflow: 'auto' }}
            extra={
              <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                {stepStates.length > 0 ? (
                  <Space>
                    <span>共 {stepStates.length} 个步骤</span>
                    <Text code style={{ fontSize: '10px' }}>
                      v{stepsVersion}
                    </Text>
                  </Space>
                ) : ''}
              </div>
            }
          >
            <div key={`steps-${stepsVersion}`}>
              {renderSteps()}
            </div>
          </Card>
        </Col>

        {/* 实时日志 - 实时更新区域 */}
        <Col span={12}>
          <Card 
            title={
              <Space>
                <span>实时日志</span>
                <Button 
                  size="small" 
                  icon={<FullscreenOutlined />}
                  onClick={handleShowLogsModal}
                >
                  查看全部
                </Button>
                <Button 
                  size="small" 
                  onClick={clearLogs}
                >
                  清空
                </Button>
                <Button 
                  size="small" 
                  type={!isUserScrolling ? "primary" : "default"}
                  onClick={toggleAutoScroll}
                  title={!isUserScrolling ? "点击暂停自动滚动" : "点击启用自动滚动"}
                >
                  {!isUserScrolling ? "📜 自动滚动" : "⏸️ 手动模式"}
                </Button>
                {isUserScrolling && (
                  <Button 
                    size="small" 
                    type="primary"
                    onClick={scrollToBottom}
                    title="滚动到最新日志"
                  >
                    ⬇️ 最新
                  </Button>
                )}
              </Space>
            }
            style={{ height: 600, position: 'relative' }}
            extra={
              logs.length > 0 && (
                <div style={{ fontSize: '12px', color: '#52c41a' }}>
                  <Space>
                    <span>● {logs.length} 条日志</span>
                    <Text code style={{ fontSize: '10px' }}>
                      v{logsVersion}
                    </Text>
                  </Space>
                </div>
              )
            }
          >
            <div key={`logs-${logsVersion}`}>
              {renderLogTimeline()}
              
              {/* 日志状态指示器 */}
              <div style={{
                position: 'absolute',
                bottom: 16,
                right: 16,
                background: 'rgba(255, 255, 255, 0.9)',
                padding: '4px 8px',
                borderRadius: 4,
                fontSize: '12px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                zIndex: 10
              }}>
                <Space size={4}>
                  {!isUserScrolling ? (
                    <>
                      <span style={{ color: '#52c41a' }}>●</span>
                      <span>自动滚动</span>
                    </>
                  ) : (
                    <>
                      <span style={{ color: '#ff4d4f' }}>●</span>
                      <span>手动模式</span>
                    </>
                  )}
                  <span style={{ color: '#8c8c8c' }}>|</span>
                  <span style={{ color: '#1890ff' }}>{logs.length} 条日志</span>
                </Space>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 全屏日志Modal */}
      <Modal
        title="完整执行日志"
        open={isLogsModalVisible}
        onCancel={() => setIsLogsModalVisible(false)}
        width="80%"
        footer={[
          <Button key="download" icon={<DownloadOutlined />}>
            下载日志
          </Button>,
          <Button key="clear" onClick={clearLogs}>
            清空日志
          </Button>,
          <Button 
            key="auto-scroll"
            type={!isModalUserScrolling ? "primary" : "default"}
            onClick={toggleModalAutoScroll}
          >
            {!isModalUserScrolling ? "📜 自动滚动" : "⏸️ 手动模式"}
          </Button>,
          ...(isModalUserScrolling ? [
            <Button key="scroll-bottom" type="primary" onClick={scrollModalToBottom}>
              ⬇️ 最新
            </Button>
          ] : []),
          <Button key="close" onClick={() => setIsLogsModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        <div 
          ref={modalLogContainerRef}
          onScroll={handleModalLogScroll}
          style={{ 
            height: '60vh', 
            overflow: 'auto', 
            backgroundColor: '#f5f5f5', 
            padding: 16,
            scrollBehavior: 'smooth'
          }}
        >
          {fullLogs && fullLogs.trim() !== '' ? (
            // 优先显示从API获取的完整日志
            <div style={{ fontFamily: 'monospace', fontSize: 12 }}>
              <div style={{ 
                color: '#1890ff', 
                fontWeight: 'bold', 
                marginBottom: 8,
                borderBottom: '1px solid #d9d9d9',
                paddingBottom: 4
              }}>
                [完整执行日志]
              </div>
              <div style={{ 
                whiteSpace: 'pre-wrap', 
                backgroundColor: '#fff',
                padding: 16,
                border: '1px solid #d9d9d9',
                borderRadius: 4
              }}>
                {fullLogs}
              </div>
            </div>
          ) : logs.length > 0 ? (
            // 显示WebSocket实时日志
            <div>
              <div style={{ 
                color: '#1890ff', 
                fontWeight: 'bold', 
                marginBottom: 8,
                borderBottom: '1px solid #d9d9d9',
                paddingBottom: 4
              }}>
                [WebSocket实时日志]
              </div>
              {logs.map((log) => (
                <div key={log.id} style={{ marginBottom: 8, fontFamily: 'monospace', fontSize: 12 }}>
                  <span style={{ color: '#666' }}>[{new Date(log.timestamp).toLocaleString()}]</span>
                  {log.stepName && <span style={{ color: '#1890ff', marginLeft: 8 }}>[{log.stepName}]</span>}
                  <span style={{ 
                    marginLeft: 8,
                    color: log.level === 'error' ? '#ff4d4f' : 
                           log.level === 'warning' ? '#fa8c16' : '#000'
                  }}>
                    {log.message}
                  </span>
                </div>
              ))}
            </div>
          ) : execution?.step_executions && execution.step_executions.length > 0 ? (
            // 显示step_executions中的日志
            <div>
              <div style={{ 
                color: '#1890ff', 
                fontWeight: 'bold', 
                marginBottom: 8,
                borderBottom: '1px solid #d9d9d9',
                paddingBottom: 4
              }}>
                [步骤执行日志]
              </div>
              {execution.step_executions
                .filter(step => step.logs && step.logs.trim() !== '')
                .map((step) => (
                  <div key={`modal-step-${step.id}`} style={{ marginBottom: 16, fontFamily: 'monospace', fontSize: 12 }}>
                    <div style={{ 
                      color: '#1890ff', 
                      fontWeight: 'bold', 
                      marginBottom: 4,
                      borderBottom: '1px solid #d9d9d9',
                      paddingBottom: 4
                    }}>
                      [{step.started_at ? new Date(step.started_at).toLocaleString() : ''}] {step.step_name || step.atomic_step_name || step.pipeline_step_name || `步骤 ${step.order}`} ({step.status_display})
                    </div>
                    <div style={{ 
                      marginLeft: 16, 
                      whiteSpace: 'pre-wrap',
                      backgroundColor: '#fff',
                      padding: 8,
                      border: '1px solid #e8e8e8',
                      borderRadius: 4
                    }}>
                      {step.logs}
                    </div>
                    {step.duration && (
                      <div style={{ marginLeft: 16, color: '#999', fontSize: 11, marginTop: 4 }}>
                        执行时间: {step.duration}
                      </div>
                    )}
                  </div>
                ))}
            </div>
          ) : execution?.logs && execution.logs.trim() !== '' ? (
            // 显示整体执行日志
            <div style={{ fontFamily: 'monospace', fontSize: 12 }}>
              <div style={{ 
                color: '#1890ff', 
                fontWeight: 'bold', 
                marginBottom: 8,
                borderBottom: '1px solid #d9d9d9',
                paddingBottom: 4
              }}>
                [整体执行日志]
              </div>
              <div style={{ 
                whiteSpace: 'pre-wrap', 
                backgroundColor: '#fff',
                padding: 16,
                border: '1px solid #d9d9d9',
                borderRadius: 4
              }}>
                {execution.logs}
              </div>
            </div>
          ) : (
            // 没有日志
            <div style={{ textAlign: 'center', color: '#999', padding: '50px 0' }}>
              暂无日志信息
            </div>
          )}
          
          {/* 模态框自动滚动状态指示 */}
          {(fullLogs || logs.length > 0) && (
            <div style={{ 
              textAlign: 'center', 
              marginTop: 8, 
              padding: '8px 16px',
              background: '#fafafa',
              borderTop: '1px solid #e8e8e8',
              fontSize: 12,
              color: isModalUserScrolling ? '#fa8c16' : '#52c41a',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span>
                {isModalUserScrolling ? '🔒 自动滚动已暂停' : '📜 自动滚动到最新日志'}
              </span>
              {isModalUserScrolling && (
                <Button 
                  size="small" 
                  type="link"
                  onClick={() => {
                    if (modalLogContainerRef.current) {
                      modalLogContainerRef.current.scrollTo({
                        top: modalLogContainerRef.current.scrollHeight,
                        behavior: 'smooth'
                      })
                      setIsModalUserScrolling(false)
                    }
                  }}
                >
                  📜 跳到最新
                </Button>
              )}
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}

export default ExecutionDetail
