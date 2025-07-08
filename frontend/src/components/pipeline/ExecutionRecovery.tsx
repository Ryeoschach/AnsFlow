import React, { useState, useEffect } from 'react'
import {
  Modal,
  Form,
  Select,
  Button,
  Space,
  Alert,
  Typography,
  Divider,
  Card,
  Tag,
  List,
  message,
  Steps,
  Switch,
  Input,
  Collapse,
  Timeline,
  Spin,
  Row,
  Col,
  Progress
} from 'antd'
import {
  PlayCircleOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
  WarningOutlined,
  SettingOutlined,
  BugOutlined,
  FileTextOutlined
} from '@ant-design/icons'
import { PipelineExecution, PipelineStep, EnhancedPipelineStep } from '../../types'
import apiService from '../../services/api'

const { Text, Title } = Typography
const { Option } = Select
const { TextArea } = Input
const { Panel } = Collapse

interface ExecutionRecoveryProps {
  visible: boolean
  execution: PipelineExecution | null
  onClose: () => void
  onResumeSuccess: (execution: PipelineExecution) => void
}

interface StepExecutionInfo {
  id: number
  name: string
  step_type: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled'
  started_at?: string
  completed_at?: string
  error_message?: string
  order: number
  logs?: string[]
  retry_count?: number
  max_retries?: number
}

interface RecoveryInfo {
  failed_steps: Array<{
    id: number
    name: string
    error: string
    failed_at: string
    logs?: string[]
    retry_count: number
    max_retries: number
  }>
  recovery_points: Array<{
    step_id: number
    step_name: string
    description: string
    recommended: boolean
  }>
  can_recover: boolean
  last_successful_step?: number
  execution_progress: {
    total_steps: number
    completed_steps: number
    failed_steps: number
    pending_steps: number
  }
}

interface RecoveryOptions {
  from_step_id: number
  skip_failed: boolean
  modify_parameters: boolean
  parameters: Record<string, any>
  recovery_strategy: 'continue' | 'restart_from' | 'skip_and_continue'
  force_retry: boolean
  custom_timeout?: number
}

const ExecutionRecovery: React.FC<ExecutionRecoveryProps> = ({
  visible,
  execution,
  onClose,
  onResumeSuccess
}) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [steps, setSteps] = useState<StepExecutionInfo[]>([])
  const [selectedStepId, setSelectedStepId] = useState<number | null>(null)
  const [recoveryInfo, setRecoveryInfo] = useState<RecoveryInfo | null>(null)
  const [recoveryOptions, setRecoveryOptions] = useState<RecoveryOptions>({
    from_step_id: 0,
    skip_failed: false,
    modify_parameters: false,
    parameters: {},
    recovery_strategy: 'continue',
    force_retry: false
  })
  const [stepLogs, setStepLogs] = useState<Record<number, any>>({})
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false)

  useEffect(() => {
    if (visible && execution) {
      loadExecutionSteps()
      loadRecoveryInfo()
    }
  }, [visible, execution])

  const loadExecutionSteps = async () => {
    if (!execution) return

    try {
      setLoading(true)
      const stepHistory = await apiService.getExecutionStepHistory(execution.id)
      setSteps(stepHistory)
      
      // 找到第一个失败的步骤作为默认恢复点
      const failedStep = stepHistory.find(step => step.status === 'failed')
      if (failedStep) {
        setSelectedStepId(failedStep.id)
        setRecoveryOptions(prev => ({ ...prev, from_step_id: failedStep.id }))
        form.setFieldsValue({ step_id: failedStep.id })
      }
    } catch (error) {
      console.error('Failed to load execution steps:', error)
      message.error('加载执行步骤失败')
    } finally {
      setLoading(false)
    }
  }

  const loadRecoveryInfo = async () => {
    if (!execution) return

    try {
      const info: any = await apiService.getExecutionRecoveryInfo(execution.id)
      const enhancedInfo: RecoveryInfo = {
        ...info,
        execution_progress: info.execution_progress || {
          total_steps: steps.length,
          completed_steps: steps.filter(s => s.status === 'success').length,
          failed_steps: steps.filter(s => s.status === 'failed').length,
          pending_steps: steps.filter(s => s.status === 'pending').length
        }
      }
      setRecoveryInfo(enhancedInfo)
      
      // 设置推荐的恢复点
      if (info.recovery_points && info.recovery_points.length > 0) {
        const recommended = info.recovery_points.find((p: any) => p.recommended)
        const defaultPoint = recommended || info.recovery_points[0]
        setSelectedStepId(defaultPoint.step_id)
        setRecoveryOptions(prev => ({
          ...prev,
          from_step_id: defaultPoint.step_id
        }))
      }

      // 加载失败步骤的详细日志
      if (info.failed_steps) {
        for (const failedStep of info.failed_steps) {
          try {
            const logs = await apiService.getStepExecutionLogs(execution.id, failedStep.id)
            setStepLogs(prev => ({
              ...prev,
              [failedStep.id]: logs
            }))
          } catch (error) {
            console.warn(`Failed to load logs for step ${failedStep.id}:`, error)
          }
        }
      }
    } catch (error) {
      console.error('Failed to load recovery info:', error)
      message.error('获取恢复信息失败')
    }
  }

  const handleRecoveryStrategyChange = (strategy: string) => {
    setRecoveryOptions(prev => ({ ...prev, recovery_strategy: strategy as any }))
    
    if (strategy === 'restart_from') {
      message.info('将从选定步骤重新开始执行，包括该步骤本身')
    } else if (strategy === 'skip_and_continue') {
      message.info('将跳过失败的步骤，从下一个步骤继续执行')
    } else {
      message.info('将尝试继续从失败点执行')
    }
  }

  const handleResumeExecution = async () => {
    if (!execution || !selectedStepId) return

    try {
      setLoading(true)
      const values = await form.validateFields()
      
      // 构建恢复请求参数
      const resumeParams = {
        execution_id: execution.id,
        from_step_id: selectedStepId,
        recovery_strategy: recoveryOptions.recovery_strategy,
        skip_failed: recoveryOptions.skip_failed,
        force_retry: recoveryOptions.force_retry,
        parameters: recoveryOptions.modify_parameters ? recoveryOptions.parameters : {},
        custom_timeout: recoveryOptions.custom_timeout
      }
      
      console.log('Resuming execution with params:', resumeParams)
      
      const resumedExecution = await apiService.resumePipelineFromStep(
        execution.id,
        selectedStepId,
        resumeParams
      )
      
      message.success('流水线恢复执行成功')
      onResumeSuccess(resumedExecution)
      onClose()
    } catch (error) {
      console.error('Failed to resume execution:', error)
      const errorMessage = error instanceof Error ? error.message : '恢复执行失败'
      message.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'running':
        return <PlayCircleOutlined style={{ color: '#1890ff' }} />
      case 'pending':
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />
      case 'cancelled':
        return <ExclamationCircleOutlined style={{ color: '#fa8c16' }} />
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'success'
      case 'failed':
        return 'error'
      case 'running':
        return 'processing'
      case 'pending':
        return 'default'
      case 'cancelled':
        return 'warning'
      default:
        return 'default'
    }
  }

  const failedSteps = steps.filter(step => step.status === 'failed')
  const canResume = failedSteps.length > 0 && recoveryInfo?.can_recover

  const getExecutionProgress = () => {
    if (!recoveryInfo) return 0
    const { total_steps, completed_steps } = recoveryInfo.execution_progress
    return total_steps > 0 ? Math.round((completed_steps / total_steps) * 100) : 0
  }

  return (
    <Modal
      title={
        <Space>
          <ReloadOutlined />
          <span>从失败步骤恢复执行</span>
          {execution && <Tag color="blue">执行ID: {execution.id}</Tag>}
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={900}
      footer={
        <Space>
          <Button onClick={onClose}>取消</Button>
          <Button
            icon={<SettingOutlined />}
            onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
          >
            {showAdvancedOptions ? '隐藏' : '显示'}高级选项
          </Button>
          <Button 
            type="primary" 
            icon={<PlayCircleOutlined />}
            onClick={handleResumeExecution}
            loading={loading}
            disabled={!canResume || !selectedStepId}
          >
            恢复执行
          </Button>
        </Space>
      }
    >
      {execution && (
        <div>
          {/* 执行概览 */}
          {recoveryInfo && (
            <Card size="small" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={6}>
                  <div style={{ textAlign: 'center' }}>
                    <Progress
                      type="circle"
                      percent={getExecutionProgress()}
                      size={80}
                      format={() => `${recoveryInfo.execution_progress.completed_steps}/${recoveryInfo.execution_progress.total_steps}`}
                    />
                    <div style={{ marginTop: 8 }}>
                      <Text type="secondary">执行进度</Text>
                    </div>
                  </div>
                </Col>
                <Col span={18}>
                  <Row gutter={[16, 8]}>
                    <Col span={8}>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: 20, fontWeight: 'bold', color: '#52c41a' }}>
                          {recoveryInfo.execution_progress.completed_steps}
                        </div>
                        <Text type="secondary">已完成</Text>
                      </div>
                    </Col>
                    <Col span={8}>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: 20, fontWeight: 'bold', color: '#ff4d4f' }}>
                          {recoveryInfo.execution_progress.failed_steps}
                        </div>
                        <Text type="secondary">失败</Text>
                      </div>
                    </Col>
                    <Col span={8}>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: 20, fontWeight: 'bold', color: '#d9d9d9' }}>
                          {recoveryInfo.execution_progress.pending_steps}
                        </div>
                        <Text type="secondary">待执行</Text>
                      </div>
                    </Col>
                  </Row>
                </Col>
              </Row>
            </Card>
          )}

          <Alert
            message="执行恢复说明"
            description="选择要从哪个失败的步骤开始恢复执行。系统会从该步骤开始重新执行流水线，之前成功的步骤将保持原状。"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          {/* 步骤列表 */}
          <Card title="执行历史" size="small" style={{ marginBottom: 16 }}>
            <List
              loading={loading}
              dataSource={steps.sort((a, b) => a.order - b.order)}
              renderItem={(step) => (
                <List.Item
                  key={step.id}
                  style={{
                    background: step.id === selectedStepId ? '#f0f2ff' : undefined,
                    border: step.id === selectedStepId ? '1px solid #1890ff' : undefined,
                    borderRadius: step.id === selectedStepId ? '4px' : undefined,
                    padding: '12px'
                  }}
                >
                  <List.Item.Meta
                    avatar={getStatusIcon(step.status)}
                    title={
                      <Space>
                        <span>步骤 {step.order}: {step.name}</span>
                        <Tag color={getStatusColor(step.status)}>
                          {step.status}
                        </Tag>
                        <Tag>{step.step_type}</Tag>
                        {step.retry_count && step.retry_count > 0 && (
                          <Tag color="orange">
                            重试 {step.retry_count}/{step.max_retries || 3}
                          </Tag>
                        )}
                      </Space>
                    }
                    description={
                      <div>
                        {step.started_at && (
                          <Text type="secondary">
                            开始时间: {new Date(step.started_at).toLocaleString()}
                          </Text>
                        )}
                        {step.completed_at && (
                          <Text type="secondary" style={{ marginLeft: 16 }}>
                            完成时间: {new Date(step.completed_at).toLocaleString()}
                          </Text>
                        )}
                        {step.error_message && (
                          <div style={{ marginTop: 4, color: '#ff4d4f' }}>
                            <BugOutlined /> 错误信息: {step.error_message}
                          </div>
                        )}
                        {stepLogs[step.id] && (
                          <Collapse size="small" style={{ marginTop: 8 }}>
                            <Panel header={<Space><FileTextOutlined />查看日志</Space>} key="logs">
                              <pre style={{ background: '#f5f5f5', padding: 8, fontSize: 12 }}>
                                {stepLogs[step.id]}
                              </pre>
                            </Panel>
                          </Collapse>
                        )}
                      </div>
                    }
                  />
                  <div>
                    {step.status === 'failed' && (
                      <Button
                        size="small"
                        type={step.id === selectedStepId ? "primary" : "default"}
                        icon={<ReloadOutlined />}
                        onClick={() => {
                          setSelectedStepId(step.id)
                          form.setFieldsValue({ step_id: step.id })
                          setRecoveryOptions(prev => ({ ...prev, from_step_id: step.id }))
                        }}
                      >
                        从此步骤恢复
                      </Button>
                    )}
                  </div>
                </List.Item>
              )}
            />
          </Card>

          {/* 恢复配置表单 */}
          {canResume && (
            <Form form={form} layout="vertical">
              <Card title="恢复配置" size="small">
                <Form.Item
                  name="step_id"
                  label="选择恢复起点"
                  rules={[{ required: true, message: '请选择要恢复的步骤' }]}
                >
                  <Select
                    placeholder="选择从哪个失败步骤开始恢复"
                    value={selectedStepId}
                    onChange={(value) => {
                      setSelectedStepId(value)
                      setRecoveryOptions(prev => ({ ...prev, from_step_id: value }))
                    }}
                  >
                    {failedSteps.map(step => (
                      <Option key={step.id} value={step.id}>
                        <Space>
                          <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                          <span>步骤 {step.order}: {step.name}</span>
                          <Tag color="error">失败</Tag>
                        </Space>
                      </Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item label="恢复策略">
                  <Select
                    value={recoveryOptions.recovery_strategy}
                    onChange={handleRecoveryStrategyChange}
                  >
                    <Option value="continue">继续执行（从失败点继续）</Option>
                    <Option value="restart_from">重新执行（从选定步骤重新开始）</Option>
                    <Option value="skip_and_continue">跳过失败（跳过失败步骤继续执行）</Option>
                  </Select>
                </Form.Item>

                {/* 高级选项 */}
                {showAdvancedOptions && (
                  <Card title="高级选项" size="small" style={{ background: '#fafafa' }}>
                    <Form.Item label="强制重试">
                      <Switch
                        checked={recoveryOptions.force_retry}
                        onChange={(checked) => 
                          setRecoveryOptions(prev => ({ ...prev, force_retry: checked }))
                        }
                      />
                      <Text type="secondary" style={{ marginLeft: 8 }}>
                        即使达到最大重试次数也强制重试
                      </Text>
                    </Form.Item>

                    <Form.Item label="跳过失败步骤">
                      <Switch
                        checked={recoveryOptions.skip_failed}
                        onChange={(checked) => 
                          setRecoveryOptions(prev => ({ ...prev, skip_failed: checked }))
                        }
                      />
                      <Text type="secondary" style={{ marginLeft: 8 }}>
                        自动跳过无法恢复的失败步骤
                      </Text>
                    </Form.Item>

                    <Form.Item label="修改参数">
                      <Switch
                        checked={recoveryOptions.modify_parameters}
                        onChange={(checked) => 
                          setRecoveryOptions(prev => ({ ...prev, modify_parameters: checked }))
                        }
                      />
                    </Form.Item>

                    {recoveryOptions.modify_parameters && (
                      <Form.Item label="自定义参数">
                        <TextArea
                          placeholder="输入JSON格式的参数覆盖"
                          value={JSON.stringify(recoveryOptions.parameters, null, 2)}
                          onChange={(e) => {
                            try {
                              const params = JSON.parse(e.target.value)
                              setRecoveryOptions(prev => ({ ...prev, parameters: params }))
                            } catch (error) {
                              // 忽略JSON解析错误，用户输入过程中
                            }
                          }}
                          rows={4}
                        />
                      </Form.Item>
                    )}
                  </Card>
                )}

                {selectedStepId && (
                  <Alert
                    message="恢复策略说明"
                    description={
                      <div>
                        <p>• 选择的步骤及其后续步骤将重新执行</p>
                        <p>• 已成功执行的步骤将跳过，避免重复执行</p>
                        <p>• 如果步骤有重试配置，将按照原有策略进行重试</p>
                        <p>• 强制重试选项将忽略原有的重试限制</p>
                      </div>
                    }
                    type="warning"
                    showIcon
                    style={{ marginTop: 16 }}
                  />
                )}
              </Card>
            </Form>
          )}

          {!canResume && (
            <Alert
              message="无法恢复执行"
              description={
                recoveryInfo?.can_recover === false 
                  ? "当前执行状态不支持恢复，可能需要重新启动流水线。"
                  : "当前执行没有失败的步骤，无需恢复。"
              }
              type={failedSteps.length === 0 ? "success" : "error"}
              showIcon
            />
          )}
        </div>
      )}
    </Modal>
  )
}

export default ExecutionRecovery
