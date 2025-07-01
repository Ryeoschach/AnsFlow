import React, { useEffect, useState } from 'react'
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
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

const { Title, Text, Paragraph } = Typography
const { Step } = Steps

interface ExecutionDetailProps {}

const ExecutionDetail: React.FC<ExecutionDetailProps> = () => {
  console.log('🎯 ExecutionDetail component mounted')
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const executionId = id ? parseInt(id) : null
  console.log('🎯 Execution ID from params:', id, 'parsed:', executionId)
  
  const { getExecutionById } = useAppStore()
  const [execution, setExecution] = useState<PipelineExecution | null>(null)
  const [loading, setLoading] = useState(true)
  const [isLogsModalVisible, setIsLogsModalVisible] = useState(false)
  const [debugInfo, setDebugInfo] = useState<string>('')
  
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

  // 加载执行记录
  useEffect(() => {
    const loadExecution = async () => {
      if (executionId) {
        setLoading(true)
        try {
          // 检查token
          const token = localStorage.getItem('authToken')
          console.log('🔐 Token in localStorage:', token ? 'exists' : 'missing')
          setDebugInfo(`Token: ${token ? 'exists' : 'missing'}`)
          
          // 如果没有token，设置一个测试token
          if (!token) {
            console.log('🔐 Setting test token...')
            localStorage.setItem('authToken', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUxMzQ1NzE3LCJpYXQiOjE3NTEzNDIxMTcsImp0aSI6ImUzMGQzYWIwOTEzNTRjNjJiOWU3ZTdiOTM4NzVlMWJhIiwidXNlcl9pZCI6MX0.FJHQB0srOuzc5unDjj_8OcaJ86jNBLNt3pzXqHJ-4k8')
            setDebugInfo(prev => prev + ' | Token set')
          }
          
          const result = await getExecutionById(executionId)
          console.log('从store获取到的执行数据:', result)
          setDebugInfo(prev => prev + ` | API result: ${result ? 'success' : 'null'}`)
          if (result) {
            setExecution(result)
            setDebugInfo(prev => prev + ` | Step executions: ${result.step_executions?.length || 0}`)
          }
        } catch (error) {
          console.error('❌ 加载执行记录失败:', error)
          setDebugInfo(prev => prev + ` | Error: ${error}`)
          message.error(`加载执行记录失败: ${error}`)
        } finally {
          setLoading(false)
        }
      }
    }
    
    loadExecution()
  }, [executionId, getExecutionById])

  // 获取状态标签
  const getStatusTag = (status: string) => {
    const statusConfig = {
      success: { color: 'green', text: '成功' },
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
  const getStepStatus = (status: string): 'wait' | 'process' | 'finish' | 'error' => {
    const statusMap = {
      pending: 'wait',
      running: 'process',
      success: 'finish',
      failed: 'error',
      skipped: 'wait',
      cancelled: 'wait'
    } as const
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
    console.log('🔄 renderSteps called')
    console.log('🌐 WebSocket stepStates:', stepStates)
    console.log('🌐 WebSocket stepStates length:', stepStates.length)
    console.log('📦 execution:', execution)
    console.log('📊 execution?.step_executions:', execution?.step_executions)
    console.log('📊 execution?.step_executions length:', execution?.step_executions?.length || 0)
    
    // 优先使用实时WebSocket数据
    if (stepStates.length > 0) {
      console.log('✅ Using WebSocket stepStates data')
      return (
        <Steps direction="vertical" current={-1}>
          {stepStates.map((step) => (
            <Step
              key={step.stepId}
              title={step.stepName}
              status={getStepStatus(step.status)}
              description={
                <div>
                  <div>状态: {getStatusTag(step.status)}</div>
                  {step.executionTime && (
                    <div>执行时间: {step.executionTime.toFixed(2)}s</div>
                  )}
                  {step.errorMessage && (
                    <Text type="danger">{step.errorMessage}</Text>
                  )}
                  {step.output && (
                    <Paragraph style={{ marginTop: 8 }}>
                      <Text code>{step.output.substring(0, 200)}</Text>
                      {step.output.length > 200 && '...'}
                    </Paragraph>
                  )}
                </div>
              }
            />
          ))}
        </Steps>
      )
    }
    
    // 如果没有实时数据，使用静态数据（从API返回的step_executions）
    if (execution?.step_executions && execution.step_executions.length > 0) {
      console.log('✅ Using static step_executions data:', execution.step_executions)
      return (
        <Steps direction="vertical" current={-1}>
          {execution.step_executions.map((step) => (
            <Step
              key={step.id}
              title={step.atomic_step_name || `步骤 ${step.order}`}
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
    
    // 没有步骤数据
    console.log('❌ No step data available')
    return (
      <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
        暂无步骤信息
      </div>
    )
  }

  // 渲染日志时间线
  const renderLogTimeline = () => {
    console.log('🔄 renderLogTimeline called')
    console.log('🌐 WebSocket logs:', logs)
    console.log('🌐 WebSocket logs length:', logs.length)
    console.log('📦 execution:', execution)
    console.log('📊 execution?.step_executions:', execution?.step_executions)
    console.log('📝 execution?.logs:', execution?.logs)
    
    // 首先尝试从实时WebSocket获取日志
    if (logs.length > 0) {
      console.log('✅ Using WebSocket logs data')
      const displayLogs = logs.slice(-20) // 只显示最新20条
      
      return (
        <Timeline
          style={{ maxHeight: 400, overflow: 'auto' }}
          items={displayLogs.map((log) => ({
            key: log.id,
            color: log.level === 'error' ? 'red' : log.level === 'warning' ? 'orange' : 'blue',
            children: (
              <div>
                <Text strong>{new Date(log.timestamp).toLocaleTimeString()}</Text>
                {log.stepName && <Tag style={{ marginLeft: 8 }}>{log.stepName}</Tag>}
                <div style={{ marginTop: 4 }}>
                  <Text type={log.level === 'error' ? 'danger' : undefined}>
                    {log.message}
                  </Text>
                </div>
              </div>
            )
          }))}
        />
      )
    }
    
    // 如果没有实时日志，从步骤执行中构建日志
    if (execution?.step_executions && execution.step_executions.length > 0) {
      console.log('✅ Using static step_executions for logs')
      const stepLogs = execution.step_executions
        .filter(step => step.logs && step.logs.trim() !== '')
        .map((step, index) => ({
          key: `step-${step.id}`,
          color: step.status === 'success' ? 'green' : step.status === 'failed' ? 'red' : 'blue',
          children: (
            <div>
              <Text strong>{step.atomic_step_name}</Text>
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
      
      return (
        <Timeline
          style={{ maxHeight: 400, overflow: 'auto' }}
          items={stepLogs}
        />
      )
    }
    
    // 如果执行有整体日志，显示整体日志
    if (execution?.logs && execution.logs.trim() !== '') {
      console.log('✅ Using execution logs')
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
    console.log('❌ No log data available')
    return (
      <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
        暂无日志信息
      </div>
    )
  }

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

  console.log('🎯 Rendering ExecutionDetail - execution:', execution)
  console.log('🎯 Rendering ExecutionDetail - loading:', loading)
  console.log('🎯 Rendering ExecutionDetail - currentState:', currentState)

  return (
    <div style={{ padding: '24px' }}>
      {/* 头部操作栏 */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Space>
            <Button 
              icon={<ArrowLeftOutlined />} 
              onClick={() => navigate('/executions')}
            >
              返回
            </Button>
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
            <Button
              type="dashed"
              onClick={async () => {
                try {
                  const token = localStorage.getItem('authToken')
                  const response = await fetch(`/api/v1/cicd/executions/${executionId}/`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                  })
                  const data = await response.json()
                  setDebugInfo(`直接API调用: ${response.status} | step_executions: ${data.step_executions?.length || 0}`)
                } catch (error) {
                  setDebugInfo(`直接API调用失败: ${error}`)
                }
              }}
            >
              测试API
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

      {/* 调试信息 */}
      {debugInfo && (
        <Alert
          type="info"
          message="调试信息"
          description={debugInfo}
          style={{ marginBottom: 16 }}
          closable
        />
      )}

      {/* 连接状态提示 */}
      {connectionError && (
        <Alert
          type="warning"
          message="WebSocket连接失败"
          description={`无法获取实时更新: ${connectionError}`}
          style={{ marginBottom: 16 }}
          closable
        />
      )}

      {isConnected && (
        <Alert
          type="success"
          message="实时监控已连接"
          description="正在接收实时执行状态更新"
          style={{ marginBottom: 16 }}
          closable
        />
      )}

      <Row gutter={[16, 16]}>
        {/* 执行概览 */}
        <Col span={24}>
          <Card title="执行概览">
            <Descriptions bordered column={2}>
              <Descriptions.Item label="流水线名称">
                {currentState?.pipeline_name || execution?.pipeline_name}
              </Descriptions.Item>
              <Descriptions.Item label="执行状态">
                {getStatusTag(currentState?.status || 'unknown')}
              </Descriptions.Item>
              <Descriptions.Item label="触发方式">
                {execution?.trigger_type || 'unknown'}
              </Descriptions.Item>
              <Descriptions.Item label="触发者">
                {execution?.triggered_by || 'system'}
              </Descriptions.Item>
              <Descriptions.Item label="开始时间">
                {execution?.started_at ? 
                  formatDistanceToNow(new Date(execution.started_at), {
                    addSuffix: true,
                    locale: zhCN
                  }) : '-'
                }
              </Descriptions.Item>
              <Descriptions.Item label="执行时长">
                {executionState?.executionTime ? 
                  `${executionState.executionTime.toFixed(2)}s` : 
                  (execution?.completed_at && execution?.started_at ? 
                    `${((new Date(execution.completed_at).getTime() - new Date(execution.started_at).getTime()) / 1000).toFixed(2)}s` : 
                    '-'
                  )
                }
              </Descriptions.Item>
            </Descriptions>
            
            <div style={{ marginTop: 16 }}>
              <Text strong>总体进度:</Text>
              <Progress 
                percent={calculateProgress()} 
                status={currentState?.status === 'failed' ? 'exception' : 
                       currentState?.status === 'success' ? 'success' : 'active'}
                style={{ marginTop: 8 }}
              />
            </div>
          </Card>
        </Col>

        {/* 步骤执行状态 */}
        <Col span={12}>
          <Card 
            title="执行步骤" 
            style={{ height: 600, overflow: 'auto' }}
          >
            {renderSteps()}
          </Card>
        </Col>

        {/* 实时日志 */}
        <Col span={12}>
          <Card 
            title={
              <Space>
                <span>实时日志</span>
                <Button 
                  size="small" 
                  icon={<FullscreenOutlined />}
                  onClick={() => setIsLogsModalVisible(true)}
                >
                  查看全部
                </Button>
                <Button 
                  size="small" 
                  onClick={clearLogs}
                >
                  清空
                </Button>
              </Space>
            }
            style={{ height: 600 }}
          >
            {renderLogTimeline()}
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
          <Button key="close" onClick={() => setIsLogsModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        <div style={{ height: '60vh', overflow: 'auto', backgroundColor: '#f5f5f5', padding: 16 }}>
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
      </Modal>
    </div>
  )
}

export default ExecutionDetail
