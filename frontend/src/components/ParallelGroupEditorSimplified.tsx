import React, { useState, useCallback, useMemo } from 'react'
import {
  Card,
  Button,
  Space,
  Tag,
  Dropdown,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  message,
  Tooltip,
  Row,
  Col,
  Divider,
  Typography,
  List,
  Transfer,
  Tabs,
  Timeline,
  Progress,
  Alert
} from 'antd'
import type { MenuProps } from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  GroupOutlined,
  BranchesOutlined,
  SettingOutlined,
  PlayCircleOutlined,
  SwapOutlined,
  UngroupOutlined,
  ClockCircleOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons'

const { TextArea } = Input
const { Text, Title } = Typography
const { TabPane } = Tabs

interface Step {
  id: string
  name: string
  type: string
  order: number
  parameters: Record<string, any>
  parallel_group?: string
  dependencies?: string[]
  estimated_duration?: number
  status?: 'pending' | 'running' | 'success' | 'failed' | 'skipped'
  stepType?: 'step' | 'parallel_group'  // 添加步骤类型字段以支持并行组
}

interface ParallelGroup {
  id: string
  name: string
  description?: string
  steps: Step[]
  sync_policy: 'wait_all' | 'wait_any' | 'fail_fast'
  timeout_seconds?: number
  order: number
  color?: string
}

interface ParallelGroupEditorProps {
  steps: Step[]
  parallelGroups: ParallelGroup[]
  onStepsChange: (steps: Step[]) => void
  onParallelGroupsChange: (groups: ParallelGroup[]) => void
  readonly?: boolean
}

const GROUP_COLORS = [
  '#1890ff', '#52c41a', '#faad14', '#f5222d', 
  '#722ed1', '#13c2c2', '#eb2f96', '#fa8c16'
]

// 步骤卡片组件
const StepCard: React.FC<{
  step: Step
  groupId?: string
  onEdit: (step: Step) => void
  onDelete: (stepId: string) => void
  onMoveToGroup: (stepId: string, groupId: string | null) => void
  availableGroups: ParallelGroup[]
  readonly?: boolean
}> = ({ step, groupId, onEdit, onDelete, onMoveToGroup, availableGroups, readonly = false }) => {
  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'running': return 'blue'
      case 'success': return 'green'
      case 'failed': return 'red'
      case 'skipped': return 'orange'
      default: return 'default'
    }
  }

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'running': return <ClockCircleOutlined />
      case 'success': return <CheckCircleOutlined />
      case 'failed': return <ExclamationCircleOutlined />
      default: return null
    }
  }

  const menuItems: MenuProps['items'] = [
    {
      key: 'edit',
      icon: <EditOutlined />,
      label: '编辑步骤',
      onClick: () => onEdit(step)
    },
    {
      type: 'divider'
    },
    {
      key: 'move-to-new',
      icon: <PlusOutlined />,
      label: '移动到新并行组',
      onClick: () => onMoveToGroup(step.id, 'new')
    },
    {
      key: 'move-to-sequential',
      icon: <PlayCircleOutlined />,
      label: '移动到顺序执行',
      onClick: () => onMoveToGroup(step.id, null)
    },
    ...(availableGroups.filter(g => g.id !== groupId).map(group => ({
      key: `move-to-${group.id}`,
      icon: <BranchesOutlined />,
      label: `移动到 ${group.name}`,
      onClick: () => onMoveToGroup(step.id, group.id)
    }))),
    {
      type: 'divider' as const
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: '删除步骤',
      danger: true,
      onClick: () => onDelete(step.id)
    }
  ]

  return (
    <Card
      size="small"
      hoverable={!readonly}
      bodyStyle={{ padding: '12px 16px' }}
      style={{ marginBottom: 8 }}
      extra={
        !readonly && (
          <Dropdown
            menu={{ items: menuItems }}
            trigger={['click']}
            placement="bottomRight"
          >
            <Button type="text" size="small" icon={<SettingOutlined />} />
          </Dropdown>
        )
      }
    >
      <Row justify="space-between" align="middle">
        <Col flex="auto">
          <Space direction="vertical" size={4}>
            <Space align="center">
              {getStatusIcon(step.status)}
              <Text strong>{step.name}</Text>
            </Space>
            <Space size={4}>
              <Tag color="blue">{step.type}</Tag>
              {step.status && (
                <Tag color={getStatusColor(step.status)}>{step.status}</Tag>
              )}
              <Text type="secondary">Order: {step.order}</Text>
            </Space>
          </Space>
        </Col>
        {step.estimated_duration && (
          <Col>
            <Tooltip title="预估执行时间">
              <Tag icon={<ClockCircleOutlined />} color="orange">
                {step.estimated_duration}s
              </Tag>
            </Tooltip>
          </Col>
        )}
      </Row>
    </Card>
  )
}

// 并行组卡片组件
const ParallelGroupCard: React.FC<{
  group: ParallelGroup
  onEdit: (group: ParallelGroup) => void
  onDelete: (groupId: string) => void
  onStepEdit: (step: Step) => void
  onStepDelete: (stepId: string) => void
  onStepMove: (stepId: string, groupId: string | null) => void
  availableGroups: ParallelGroup[]
  readonly?: boolean
}> = ({ 
  group, 
  onEdit, 
  onDelete, 
  onStepEdit, 
  onStepDelete, 
  onStepMove, 
  availableGroups,
  readonly = false 
}) => {
  const totalEstimatedTime = useMemo(() => {
    const maxTime = Math.max(...group.steps.map(step => step.estimated_duration || 0))
    return maxTime > 0 ? maxTime : undefined
  }, [group.steps])

  const getGroupProgress = () => {
    if (group.steps.length === 0) return 0
    const completedSteps = group.steps.filter(step => step.status === 'success').length
    return (completedSteps / group.steps.length) * 100
  }

  const hasRunningSteps = group.steps.some(step => step.status === 'running')
  const hasFailedSteps = group.steps.some(step => step.status === 'failed')

  return (
    <Card
      title={
        <Space>
          <BranchesOutlined style={{ color: group.color || '#1890ff' }} />
          <Text strong>{group.name}</Text>
          <Tag color={group.color || 'blue'}>{group.steps.length} 步骤</Tag>
          {totalEstimatedTime && (
            <Tooltip title="并行执行预估时间（最长步骤时间）">
              <Tag color="orange" icon={<ClockCircleOutlined />}>
                ~{totalEstimatedTime}s
              </Tag>
            </Tooltip>
          )}
        </Space>
      }
      extra={
        !readonly && (
          <Space>
            <Tooltip title="编辑并行组">
              <Button 
                type="text" 
                size="small" 
                icon={<EditOutlined />}
                onClick={() => onEdit(group)}
              />
            </Tooltip>
            <Tooltip title="删除并行组">
              <Button 
                type="text" 
                size="small" 
                icon={<DeleteOutlined />}
                danger
                onClick={() => onDelete(group.id)}
              />
            </Tooltip>
          </Space>
        )
      }
      style={{
        marginBottom: 16,
        border: `2px solid ${group.color || '#1890ff'}`,
      }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size={12}>
        {/* 进度条 */}
        {group.steps.some(step => step.status && step.status !== 'pending') && (
          <Progress
            percent={getGroupProgress()}
            status={hasFailedSteps ? 'exception' : hasRunningSteps ? 'active' : 'normal'}
            size="small"
            showInfo={false}
          />
        )}

        {group.description && (
          <Alert
            message={group.description}
            type="info"
            showIcon={false}
            style={{ fontSize: '12px' }}
          />
        )}
        
        <Row gutter={[8, 8]}>
          <Col span={8}>
            <Text type="secondary">同步策略:</Text>
            <br />
            <Tag color="green">{group.sync_policy}</Tag>
          </Col>
          {group.timeout_seconds && (
            <Col span={8}>
              <Text type="secondary">超时时间:</Text>
              <br />
              <Tag color="orange">{group.timeout_seconds}s</Tag>
            </Col>
          )}
          <Col span={8}>
            <Text type="secondary">执行顺序:</Text>
            <br />
            <Tag>{group.order}</Tag>
          </Col>
        </Row>

        <Divider style={{ margin: '8px 0' }} />

        {group.steps.length === 0 ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '20px 0',
            color: '#999',
            border: '1px dashed #d9d9d9',
            borderRadius: 4,
            backgroundColor: '#fafafa'
          }}>
            <InfoCircleOutlined style={{ marginRight: 8 }} />
            暂无步骤，请通过步骤管理添加
          </div>
        ) : (
          group.steps.map(step => (
            <StepCard
              key={step.id}
              step={step}
              groupId={group.id}
              onEdit={onStepEdit}
              onDelete={onStepDelete}
              onMoveToGroup={onStepMove}
              availableGroups={availableGroups}
              readonly={readonly}
            />
          ))
        )}
      </Space>
    </Card>
  )
}

// 执行时间轴组件
const ExecutionTimeline: React.FC<{
  steps: Step[]
  parallelGroups: ParallelGroup[]
}> = ({ steps, parallelGroups }) => {
  const timelineItems = useMemo(() => {
    const allItems: any[] = []
    const groupStepIds = new Set(
      parallelGroups.flatMap(group => group.steps.map(step => step.id))
    )
    
    // 获取顺序步骤
    const sequentialSteps = steps.filter(step => !groupStepIds.has(step.id))
    
    // 合并并排序所有项目
    const allExecutionItems = [
      ...sequentialSteps.map(step => ({ type: 'step', item: step, order: step.order })),
      ...parallelGroups.map(group => ({ type: 'group', item: group, order: group.order }))
    ].sort((a, b) => a.order - b.order)
    
    return allExecutionItems.map((item, index) => {
      if (item.type === 'step') {
        const step = item.item as Step
        return {
          color: step.status === 'success' ? 'green' : step.status === 'failed' ? 'red' : 'blue',
          children: (
            <div>
              <Text strong>{step.name}</Text>
              <br />
              <Tag color="blue">{step.type}</Tag>
              {step.estimated_duration && (
                <Tag color="orange">{step.estimated_duration}s</Tag>
              )}
            </div>
          )
        }
      } else {
        const group = item.item as ParallelGroup
        const maxDuration = Math.max(...group.steps.map(s => s.estimated_duration || 0))
        return {
          color: group.color || '#1890ff',
          children: (
            <div>
              <Space>
                <BranchesOutlined />
                <Text strong>{group.name}</Text>
                <Tag color={group.color || 'blue'}>{group.steps.length} 并行步骤</Tag>
                {maxDuration > 0 && (
                  <Tag color="orange">~{maxDuration}s</Tag>
                )}
              </Space>
              <div style={{ marginTop: 8, marginLeft: 16 }}>
                {group.steps.map(step => (
                  <div key={step.id} style={{ marginBottom: 4 }}>
                    <Text>{step.name}</Text>
                    <Tag color="blue" style={{ marginLeft: 8, fontSize: '12px' }}>
                      {step.type}
                    </Tag>
                  </div>
                ))}
              </div>
            </div>
          )
        }
      }
    })
  }, [steps, parallelGroups])

  return (
    <Card title="执行时间轴预览" style={{ marginTop: 16 }}>
      <Timeline items={timelineItems} />
    </Card>
  )
}

// 主编辑器组件
export const ParallelGroupEditor: React.FC<ParallelGroupEditorProps> = ({
  steps,
  parallelGroups,
  onStepsChange,
  onParallelGroupsChange,
  readonly = false
}) => {
  const [editingStep, setEditingStep] = useState<Step | null>(null)
  const [editingGroup, setEditingGroup] = useState<ParallelGroup | null>(null)
  const [stepModalVisible, setStepModalVisible] = useState(false)
  const [groupModalVisible, setGroupModalVisible] = useState(false)
  const [stepForm] = Form.useForm()
  const [groupForm] = Form.useForm()
  const [activeTab, setActiveTab] = useState('editor')

  // 获取顺序执行的步骤（不在任何并行组中）
  const sequentialSteps = useMemo(() => {
    const groupStepIds = new Set(
      parallelGroups.flatMap(group => group.steps.map(step => step.id))
    )
    return steps.filter(step => !groupStepIds.has(step.id))
  }, [steps, parallelGroups])

  // 创建新并行组
  const createNewGroup = useCallback(() => {
    const newGroup: ParallelGroup = {
      id: `group_${Date.now()}`,
      name: `并行组 ${parallelGroups.length + 1}`,
      steps: [],
      sync_policy: 'wait_all',
      order: Math.max(...parallelGroups.map(g => g.order), 0) + 1,
      color: GROUP_COLORS[parallelGroups.length % GROUP_COLORS.length]
    }
    setEditingGroup(newGroup)
    groupForm.setFieldsValue(newGroup)
    setGroupModalVisible(true)
  }, [parallelGroups, groupForm])

  // 处理步骤移动
  const handleStepMove = useCallback((stepId: string, targetGroupId: string | null) => {
    if (targetGroupId === 'new') {
      // 创建新组并添加步骤
      const targetStep = steps.find(step => step.id === stepId)
      if (!targetStep) return

      const newGroup: ParallelGroup = {
        id: `group_${Date.now()}`,
        name: `并行组 ${parallelGroups.length + 1}`,
        steps: [targetStep],
        sync_policy: 'wait_all',
        order: targetStep.order,
        color: GROUP_COLORS[parallelGroups.length % GROUP_COLORS.length]
      }

      // 从其他组中移除该步骤
      const updatedGroups = parallelGroups.map(group => ({
        ...group,
        steps: group.steps.filter(step => step.id !== stepId)
      }))

      onParallelGroupsChange([...updatedGroups, newGroup])
      message.success('已创建新并行组')
    } else if (targetGroupId === null) {
      // 移动到顺序执行
      const updatedGroups = parallelGroups.map(group => ({
        ...group,
        steps: group.steps.filter(step => step.id !== stepId)
      }))
      onParallelGroupsChange(updatedGroups)
      message.success('步骤已移动到顺序执行')
    } else {
      // 移动到指定并行组
      const targetStep = steps.find(step => step.id === stepId)
      if (!targetStep) return

      const updatedGroups = parallelGroups.map(group => {
        if (group.id === targetGroupId) {
          // 添加到目标组
          return {
            ...group,
            steps: [...group.steps.filter(s => s.id !== stepId), targetStep]
          }
        } else {
          // 从其他组移除
          return {
            ...group,
            steps: group.steps.filter(step => step.id !== stepId)
          }
        }
      })

      onParallelGroupsChange(updatedGroups)
      message.success('步骤已移动到指定并行组')
    }
  }, [parallelGroups, steps, onParallelGroupsChange])

  // 保存步骤
  const handleSaveStep = useCallback(() => {
    stepForm.validateFields().then(values => {
      if (editingStep) {
        // 更新现有步骤
        const updatedSteps = steps.map(step => 
          step.id === editingStep.id ? { ...step, ...values } : step
        )
        onStepsChange(updatedSteps)

        // 更新并行组中的步骤
        const updatedGroups = parallelGroups.map(group => ({
          ...group,
          steps: group.steps.map(step => 
            step.id === editingStep.id ? { ...step, ...values } : step
          )
        }))
        onParallelGroupsChange(updatedGroups)
      }
      
      setStepModalVisible(false)
      setEditingStep(null)
      stepForm.resetFields()
      message.success('步骤已保存')
    })
  }, [editingStep, steps, parallelGroups, onStepsChange, onParallelGroupsChange, stepForm])

  // 保存并行组
  const handleSaveGroup = useCallback(() => {
    groupForm.validateFields().then(values => {
      if (editingGroup) {
        const updatedGroups = parallelGroups.find(g => g.id === editingGroup.id)
          ? parallelGroups.map(group => 
              group.id === editingGroup.id ? { ...group, ...values } : group
            )
          : [...parallelGroups, { ...editingGroup, ...values }]
        
        onParallelGroupsChange(updatedGroups)
      }
      
      setGroupModalVisible(false)
      setEditingGroup(null)
      groupForm.resetFields()
      message.success('并行组已保存')
    })
  }, [editingGroup, parallelGroups, onParallelGroupsChange, groupForm])

  return (
    <div style={{ padding: '16px' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Title level={4}>
            <BranchesOutlined /> 并行组编辑器
          </Title>
        </Col>
        <Col>
          {!readonly && (
            <Space>
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={createNewGroup}
              >
                创建并行组
              </Button>
            </Space>
          )}
        </Col>
      </Row>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="编辑器" key="editor">
          {/* 并行组列表 */}
          {parallelGroups.map(group => (
            <ParallelGroupCard
              key={group.id}
              group={group}
              onEdit={(group) => {
                setEditingGroup(group)
                groupForm.setFieldsValue(group)
                setGroupModalVisible(true)
              }}
              onDelete={(groupId) => {
                const updatedGroups = parallelGroups.filter(g => g.id !== groupId)
                onParallelGroupsChange(updatedGroups)
                message.success('并行组已删除')
              }}
              onStepEdit={(step) => {
                setEditingStep(step)
                stepForm.setFieldsValue(step)
                setStepModalVisible(true)
              }}
              onStepDelete={(stepId) => {
                const updatedSteps = steps.filter(s => s.id !== stepId)
                onStepsChange(updatedSteps)
                const updatedGroups = parallelGroups.map(group => ({
                  ...group,
                  steps: group.steps.filter(step => step.id !== stepId)
                }))
                onParallelGroupsChange(updatedGroups)
                message.success('步骤已删除')
              }}
              onStepMove={handleStepMove}
              availableGroups={parallelGroups}
              readonly={readonly}
            />
          ))}

          {/* 顺序执行步骤 */}
          {sequentialSteps.length > 0 && (
            <Card
              title={
                <Space>
                  <PlayCircleOutlined />
                  <Text strong>顺序执行步骤</Text>
                  <Tag>{sequentialSteps.length} 步骤</Tag>
                </Space>
              }
              style={{ marginBottom: 16 }}
            >
              {sequentialSteps.map(step => (
                <StepCard
                  key={step.id}
                  step={step}
                  onEdit={(step) => {
                    setEditingStep(step)
                    stepForm.setFieldsValue(step)
                    setStepModalVisible(true)
                  }}
                  onDelete={(stepId) => {
                    const updatedSteps = steps.filter(s => s.id !== stepId)
                    onStepsChange(updatedSteps)
                    message.success('步骤已删除')
                  }}
                  onMoveToGroup={handleStepMove}
                  availableGroups={parallelGroups}
                  readonly={readonly}
                />
              ))}
            </Card>
          )}
        </TabPane>

        <TabPane tab="执行预览" key="timeline">
          <ExecutionTimeline 
            steps={steps} 
            parallelGroups={parallelGroups} 
          />
        </TabPane>
      </Tabs>

      {/* 步骤编辑弹窗 */}
      <Modal
        title="编辑步骤"
        open={stepModalVisible}
        onOk={handleSaveStep}
        onCancel={() => {
          setStepModalVisible(false)
          setEditingStep(null)
          stepForm.resetFields()
        }}
        width={600}
      >
        <Form form={stepForm} layout="vertical">
          <Form.Item name="name" label="步骤名称" rules={[{ required: true }]}>
            <Input placeholder="输入步骤名称" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="type" label="步骤类型" rules={[{ required: true }]}>
                <Select>
                  <Select.Option value="build">构建</Select.Option>
                  <Select.Option value="test">测试</Select.Option>
                  <Select.Option value="deploy">部署</Select.Option>
                  <Select.Option value="fetch_code">代码检出</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="order" label="执行顺序" rules={[{ required: true }]}>
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="estimated_duration" label="预估执行时间(秒)">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="parameters" label="步骤参数">
            <TextArea rows={4} placeholder="JSON格式的参数配置" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 并行组编辑弹窗 */}
      <Modal
        title={editingGroup?.id.startsWith('group_') ? "新建并行组" : "编辑并行组"}
        open={groupModalVisible}
        onOk={handleSaveGroup}
        onCancel={() => {
          setGroupModalVisible(false)
          setEditingGroup(null)
          groupForm.resetFields()
        }}
        width={600}
      >
        <Form form={groupForm} layout="vertical">
          <Form.Item name="name" label="并行组名称" rules={[{ required: true }]}>
            <Input placeholder="输入并行组名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={2} placeholder="可选的描述信息" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="sync_policy" label="同步策略" rules={[{ required: true }]}>
                <Select>
                  <Select.Option value="wait_all">等待所有步骤完成</Select.Option>
                  <Select.Option value="wait_any">等待任一步骤完成</Select.Option>
                  <Select.Option value="fail_fast">快速失败</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="order" label="执行顺序" rules={[{ required: true }]}>
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="timeout_seconds" label="超时时间(秒)">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="color" label="显示颜色">
            <Select>
              {GROUP_COLORS.map((color, index) => (
                <Select.Option key={color} value={color}>
                  <Space>
                    <div style={{ 
                      width: 16, 
                      height: 16, 
                      backgroundColor: color, 
                      borderRadius: 2 
                    }} />
                    {color}
                  </Space>
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ParallelGroupEditor
