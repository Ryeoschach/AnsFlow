import React, { useState, useEffect } from 'react'
import {
  Form,
  Input,
  Select,
  Switch,
  Collapse,
  Card,
  Space,
  Button,
  InputNumber,
  Divider,
  Tag,
  Alert,
  Typography,
  Modal,
  Drawer
} from 'antd'
import {
  BranchesOutlined,
  ClusterOutlined,
  AuditOutlined,
  SettingOutlined,
  PlusOutlined,
  DeleteOutlined,
  ShareAltOutlined,
  ThunderboltOutlined
} from '@ant-design/icons'
import { 
  EnhancedPipelineStep, 
  StepCondition, 
  ApprovalConfig, 
  ParallelGroup,
  WorkflowContext,
  ConditionEvaluationResult
} from '../../types'

const { Option } = Select
const { TextArea } = Input
const { Text } = Typography
const { Panel } = Collapse

interface WorkflowStepFormProps {
  visible: boolean
  editingStep: EnhancedPipelineStep | null
  availableSteps: EnhancedPipelineStep[]
  parallelGroups: ParallelGroup[]
  pipelineId?: number
  executionContext?: WorkflowContext
  approvers?: string[]  // 可选的审批人员列表
  notificationChannels?: string[]  // 可用的通知渠道
  variables?: Record<string, any>  // 流水线变量，用于条件表达式验证
  onClose: () => void
  onSave: (step: EnhancedPipelineStep) => Promise<void>
  onParallelGroupChange: (groups: ParallelGroup[]) => void
  onTestCondition?: (expression: string, context: any) => Promise<ConditionEvaluationResult>
  onPreviewApproval?: (config: ApprovalConfig) => void
  onValidateExpression?: (expression: string) => Promise<{ valid: boolean; error?: string }>
}

const WorkflowStepForm: React.FC<WorkflowStepFormProps> = ({
  visible,
  editingStep,
  availableSteps,
  parallelGroups,
  pipelineId,
  executionContext,
  approvers = [],
  notificationChannels = ['email', 'slack', 'webhook'],
  variables = {},
  onClose,
  onSave,
  onParallelGroupChange,
  onTestCondition,
  onPreviewApproval,
  onValidateExpression
}) => {
  const [form] = Form.useForm()
  const [conditionType, setConditionType] = useState<string>('always')
  const [requiresApproval, setRequiresApproval] = useState(false)
  const [isInParallel, setIsInParallel] = useState(false)
  const [selectedParallelGroup, setSelectedParallelGroup] = useState<string>('')

  // 初始化表单值
  useEffect(() => {
    if (editingStep) {
      // 条件配置
      const condition = editingStep.condition
      if (condition) {
        setConditionType(condition.type)
        form.setFieldsValue({
          'condition_type': condition.type,
          'condition_expression': condition.expression,
          'condition_depends_on': condition.depends_on
        })
      } else {
        setConditionType('always')
      }

      // 审批配置
      const approval = editingStep.requires_approval
      setRequiresApproval(!!approval)
      if (approval && editingStep.approval_config) {
        form.setFieldsValue({
          'approval_approvers': editingStep.approval_config.approvers,
          'approval_message': editingStep.approval_config.approval_message,
          'approval_timeout': editingStep.approval_config.timeout_hours,
          'approval_auto_approve': editingStep.approval_config.auto_approve_on_timeout,
          'approval_required_count': editingStep.approval_config.required_approvals
        })
      }

      // 并行执行配置
      const parallelGroupId = editingStep.parallel_group_id
      if (parallelGroupId) {
        setIsInParallel(true)
        setSelectedParallelGroup(parallelGroupId)
        form.setFieldsValue({
          'parallel_group_id': parallelGroupId
        })
      }

      // 重试策略
      if (editingStep.retry_policy) {
        form.setFieldsValue({
          'retry_max_retries': editingStep.retry_policy.max_retries,
          'retry_delay_seconds': editingStep.retry_policy.retry_delay_seconds,
          'retry_on_failure': editingStep.retry_policy.retry_on_failure
        })
      }

      // 通知配置
      if (editingStep.notification_config) {
        form.setFieldsValue({
          'notify_on_success': editingStep.notification_config.on_success,
          'notify_on_failure': editingStep.notification_config.on_failure,
          'notify_channels': editingStep.notification_config.channels
        })
      }
    }
  }, [editingStep, form])

  const handleSave = async () => {
    if (!editingStep) return

    try {
      const values = await form.validateFields()
      
      const updatedStep: EnhancedPipelineStep = {
        ...editingStep,
        condition: conditionType !== 'always' ? {
          type: conditionType as 'on_success' | 'on_failure' | 'expression',
          expression: values.condition_expression,
          depends_on: values.condition_depends_on
        } : undefined,
        parallel_group_id: isInParallel ? selectedParallelGroup : undefined,
        requires_approval: requiresApproval,
        approval_config: requiresApproval ? {
          approvers: values.approval_approvers || [],
          approval_message: values.approval_message,
          timeout_hours: values.approval_timeout || 24,
          auto_approve_on_timeout: values.approval_auto_approve || false,
          required_approvals: values.approval_required_count || 1
        } : undefined,
        retry_policy: {
          max_retries: values.retry_max_retries || 0,
          retry_delay_seconds: values.retry_delay_seconds || 30,
          retry_on_failure: values.retry_on_failure !== false
        },
        notification_config: {
          on_success: values.notify_on_success || false,
          on_failure: values.notify_on_failure || false,
          on_approval_required: values.notify_on_approval || false,
          channels: values.notify_channels || []
        }
      }
      
      // 异步调用保存函数
      await onSave(updatedStep)
    } catch (error) {
      console.error('Failed to save workflow step:', error)
      throw error
    }
  }

  return (
    <Drawer
      title={
        <Space>
          <ThunderboltOutlined />
          <span>高级工作流配置</span>
          <Text type="secondary">{editingStep?.name}</Text>
        </Space>
      }
      open={visible}
      onClose={onClose}
      width={700}
      footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={onClose}>取消</Button>
          <Button type="primary" onClick={handleSave}>
            保存配置
          </Button>
        </Space>
      }
    >
      {editingStep && (
        <Form form={form} layout="vertical">
          <Collapse defaultActiveKey={['1', '2', '3']} ghost>
            
            {/* 条件执行配置 */}
            <Panel 
              header={
                <Space>
                  <BranchesOutlined />
                  <span>条件执行分支</span>
                  <Tag color={conditionType !== 'always' ? 'processing' : 'default'}>
                    {conditionType !== 'always' ? '已配置' : '默认'}
                  </Tag>
                </Space>
              } 
              key="1"
            >
              <Card size="small">
                <Form.Item
                  name="condition_type"
                  label="执行条件"
                  tooltip="设置步骤的执行条件"
                >
                  <Select
                    value={conditionType}
                    onChange={setConditionType}
                    placeholder="选择执行条件"
                  >
                    <Option value="always">总是执行</Option>
                    <Option value="on_success">前序步骤成功时执行</Option>
                    <Option value="on_failure">前序步骤失败时执行</Option>
                    <Option value="expression">自定义表达式</Option>
                  </Select>
                </Form.Item>

                {conditionType === 'expression' && (
                  <Form.Item
                    name="condition_expression"
                    label="条件表达式"
                    tooltip="使用JavaScript表达式，可访问 $previous、$variables 等上下文变量"
                    rules={[{ required: true, message: '请输入条件表达式' }]}
                  >
                    <TextArea
                      placeholder='例如: $previous.status === "success" && $variables.deploy_env === "prod"'
                      rows={3}
                    />
                  </Form.Item>
                )}

                {(conditionType === 'on_success' || conditionType === 'on_failure') && (
                  <Form.Item
                    name="condition_depends_on"
                    label="依赖步骤"
                    tooltip="选择此步骤依赖的前序步骤"
                  >
                    <Select
                      mode="multiple"
                      placeholder="选择依赖的步骤"
                      allowClear
                    >
                      {availableSteps
                        .filter(step => step.id !== editingStep.id)
                        .map(step => (
                          <Option key={step.id} value={step.id}>
                            <Space>
                              <Tag>{step.step_type}</Tag>
                              {step.name}
                            </Space>
                          </Option>
                        ))}
                    </Select>
                  </Form.Item>
                )}
              </Card>
            </Panel>

            {/* 并行执行配置 */}
            <Panel 
              header={
                <Space>
                  <ShareAltOutlined />
                  <span>并行执行策略</span>
                  <Tag color={isInParallel ? 'success' : 'default'}>
                    {isInParallel ? '已启用' : '顺序执行'}
                  </Tag>
                </Space>
              } 
              key="2"
            >
              <Card size="small">
                <Form.Item
                  name="parallel_enabled"
                  label="启用并行执行"
                  tooltip="将此步骤加入并行组中执行"
                >
                  <Switch
                    checked={isInParallel}
                    onChange={setIsInParallel}
                  />
                </Form.Item>

                {isInParallel && (
                  <Form.Item
                    name="parallel_group_id"
                    label="选择并行组"
                    tooltip="选择要加入的并行组"
                    rules={[{ required: true, message: '请选择并行组' }]}
                  >
                    <Select
                      value={selectedParallelGroup}
                      onChange={setSelectedParallelGroup}
                      placeholder="选择并行组"
                      allowClear
                    >
                      {parallelGroups.map(group => (
                        <Option key={group.id} value={group.id}>
                          <Space>
                            <Tag color="green">{group.sync_policy}</Tag>
                            {group.name}
                          </Space>
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                )}

                <Alert
                  message="并行执行说明"
                  description="并行执行可以提高流水线效率，但请确保步骤之间没有依赖关系。可在并行组管理中创建和配置并行组。"
                  type="info"
                  showIcon
                  style={{ marginTop: 16 }}
                />
              </Card>
            </Panel>

            {/* 审批节点配置 */}
            <Panel 
              header={
                <Space>
                  <AuditOutlined />
                  <span>手动审批节点</span>
                  <Tag color={requiresApproval ? 'orange' : 'default'}>
                    {requiresApproval ? '需要审批' : '无需审批'}
                  </Tag>
                </Space>
              } 
              key="3"
            >
              <Card size="small">
                <Form.Item
                  name="requires_approval"
                  label="是否需要审批"
                  tooltip="启用后，流水线执行到此步骤时将暂停等待人工审批"
                >
                  <Switch
                    checked={requiresApproval}
                    onChange={setRequiresApproval}
                  />
                </Form.Item>

                {requiresApproval && (
                  <>
                    <Form.Item
                      name="approval_approvers"
                      label="审批人员"
                      tooltip="输入审批人员的用户名或邮箱地址"
                      rules={[{ required: true, message: '请设置审批人员' }]}
                    >
                      <Select
                        mode="tags"
                        placeholder="输入审批人员用户名或邮箱"
                        tokenSeparators={[',', ' ']}
                      />
                    </Form.Item>

                    <Form.Item
                      name="approval_required_count"
                      label="最少审批人数"
                      tooltip="需要多少人审批通过才能继续执行"
                    >
                      <InputNumber
                        min={1}
                        max={10}
                        placeholder="1"
                        style={{ width: '100%' }}
                      />
                    </Form.Item>

                    <Form.Item
                      name="approval_timeout"
                      label="审批超时时间（小时）"
                      tooltip="超过此时间未审批的处理方式"
                    >
                      <InputNumber
                        min={1}
                        max={168}
                        placeholder="24"
                        style={{ width: '100%' }}
                      />
                    </Form.Item>

                    <Form.Item
                      name="approval_auto_approve"
                      label="超时后自动批准"
                      tooltip="超时后是否自动批准继续执行"
                    >
                      <Switch />
                    </Form.Item>

                    <Form.Item
                      name="approval_message"
                      label="审批消息"
                      tooltip="发送给审批人员的消息内容"
                    >
                      <TextArea
                        placeholder="请审批此步骤的执行..."
                        rows={3}
                      />
                    </Form.Item>
                  </>
                )}
              </Card>
            </Panel>

            {/* 重试策略配置 */}
            <Panel 
              header={
                <Space>
                  <SettingOutlined />
                  <span>重试策略</span>
                </Space>
              } 
              key="4"
            >
              <Card size="small">
                <Form.Item
                  name="retry_max_retries"
                  label="最大重试次数"
                  tooltip="步骤失败时的最大重试次数"
                >
                  <InputNumber
                    min={0}
                    max={10}
                    placeholder="0"
                    style={{ width: '100%' }}
                  />
                </Form.Item>

                <Form.Item
                  name="retry_delay_seconds"
                  label="重试延迟（秒）"
                  tooltip="两次重试之间的延迟时间"
                >
                  <InputNumber
                    min={1}
                    max={3600}
                    placeholder="30"
                    style={{ width: '100%' }}
                  />
                </Form.Item>

                <Form.Item
                  name="retry_on_failure"
                  label="仅在失败时重试"
                  tooltip="只有在步骤执行失败时才进行重试"
                >
                  <Switch defaultChecked />
                </Form.Item>
              </Card>
            </Panel>

            {/* 通知配置 */}
            <Panel 
              header={
                <Space>
                  <span>📢</span>
                  <span>通知配置</span>
                </Space>
              } 
              key="5"
            >
              <Card size="small">
                <Form.Item
                  name="notify_on_success"
                  label="成功时发送通知"
                  tooltip="步骤执行成功时发送通知"
                >
                  <Switch />
                </Form.Item>

                <Form.Item
                  name="notify_on_failure"
                  label="失败时发送通知"
                  tooltip="步骤执行失败时发送通知"
                >
                  <Switch />
                </Form.Item>

                <Form.Item
                  name="notify_channels"
                  label="通知渠道"
                  tooltip="选择通知发送的渠道"
                >
                  <Select
                    mode="multiple"
                    placeholder="选择通知渠道"
                    allowClear
                  >
                    <Option value="email">邮件</Option>
                    <Option value="slack">Slack</Option>
                    <Option value="webhook">Webhook</Option>
                    <Option value="sms">短信</Option>
                  </Select>
                </Form.Item>
              </Card>
            </Panel>

          </Collapse>
        </Form>
      )}
    </Drawer>
  )
}

export default WorkflowStepForm
