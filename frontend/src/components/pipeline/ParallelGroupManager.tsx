import React, { useState } from 'react'
import {
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Space,
  Button,
  Card,
  List,
  Tag,
  Typography,
  Divider,
  Alert,
  Popconfirm
} from 'antd'
import {
  ClusterOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  SyncOutlined,
  ClockCircleOutlined
} from '@ant-design/icons'
import { ParallelGroup, EnhancedPipelineStep } from '../../types'

const { Option } = Select
const { TextArea } = Input
const { Text } = Typography

interface ParallelGroupManagerProps {
  visible: boolean
  parallelGroups: ParallelGroup[]
  availableSteps: EnhancedPipelineStep[]
  onClose: () => void
  onChange: (groups: ParallelGroup[]) => void
}

const ParallelGroupManager: React.FC<ParallelGroupManagerProps> = ({
  visible,
  parallelGroups,
  availableSteps,
  onClose,
  onChange
}) => {
  const [form] = Form.useForm()
  const [editingGroup, setEditingGroup] = useState<ParallelGroup | null>(null)
  const [formVisible, setFormVisible] = useState(false)

  // 数据验证和默认值
  const safeParallelGroups = Array.isArray(parallelGroups) ? parallelGroups : []
  const safeAvailableSteps = Array.isArray(availableSteps) ? availableSteps : []

  console.log('🔍 ParallelGroupManager 渲染:', {
    visible,
    parallelGroupsCount: safeParallelGroups.length,
    availableStepsCount: safeAvailableSteps.length,
    formVisible,
    editingGroup: editingGroup?.id || null
  })

  // 数据同步验证方法
  const validateDataSync = () => {
    console.log('🔍 验证数据同步状态...')
    
    const issues: string[] = []
    
    // 检查每个并行组的步骤配置
    safeParallelGroups.forEach(group => {
      const groupId = group.id
      const groupSteps = group.steps || []
      
      // 检查组中配置的步骤是否实际存在
      groupSteps.forEach(stepId => {
        const step = safeAvailableSteps.find(s => s.id === stepId)
        if (!step) {
          issues.push(`并行组 ${groupId} 中的步骤 ${stepId} 不存在`)
        } else if (step.parallel_group !== groupId) {
          issues.push(`步骤 ${stepId} 的parallel_group字段(${step.parallel_group})与所属组(${groupId})不匹配`)
        }
      })
    })
    
    // 检查有parallel_group字段的步骤是否都在对应的并行组中
    safeAvailableSteps.forEach(step => {
      if (step.parallel_group) {
        const group = safeParallelGroups.find(g => g.id === step.parallel_group)
        if (!group) {
          issues.push(`步骤 ${step.id} 引用的并行组 ${step.parallel_group} 不存在`)
        } else if (!group.steps || !group.steps.includes(step.id)) {
          issues.push(`步骤 ${step.id} 未在其所属并行组 ${step.parallel_group} 的steps数组中`)
        }
      }
    })
    
    if (issues.length > 0) {
      console.warn('⚠️ 发现数据同步问题:', issues)
    } else {
      console.log('✅ 数据同步验证通过')
    }
    
    return issues
  }

  // 在组件挂载时验证数据
  React.useEffect(() => {
    if (visible && safeParallelGroups.length > 0 && safeAvailableSteps.length > 0) {
      validateDataSync()
    }
  }, [visible, safeParallelGroups, safeAvailableSteps])

  // 创建新并行组
  const handleCreateGroup = () => {
    setEditingGroup(null)
    form.resetFields()
    form.setFieldsValue({
      sync_policy: 'wait_all',
      timeout_seconds: 3600
    })
    setFormVisible(true)
  }

  // 编辑并行组
  const handleEditGroup = (group: ParallelGroup) => {
    setEditingGroup(group)
    
    // 动态获取属于该组的步骤
    const groupSteps = getStepsForGroup(group.id)
    
    console.log('📝 编辑并行组:', group.id, '包含步骤:', groupSteps)
    console.log('📋 组配置的步骤:', group.steps)
    console.log('📋 从字段获取的步骤:', groupSteps)
    
    // 设置表单值，优先使用组配置的步骤，如果为空则使用动态获取的步骤
    const stepsToUse = (group.steps && group.steps.length > 0) ? group.steps : groupSteps
    
    form.setFieldsValue({
      ...group,
      steps: stepsToUse
    })
    
    console.log('📝 最终使用的步骤:', stepsToUse)
    setFormVisible(true)
  }

  // 删除并行组
  const handleDeleteGroup = (groupId: string) => {
    const updatedGroups = safeParallelGroups.filter(g => g.id !== groupId)
    console.log('🗑️ 删除并行组:', groupId, '剩余:', updatedGroups.length, '个组')
    // 调用父组件的保存函数，会同步到后端
    onChange(updatedGroups)
  }

  // 保存并行组
  const handleSaveGroup = async () => {
    try {
      const values = await form.validateFields()
      console.log('📝 保存并行组表单数据:', values)
      
      let updatedGroups
      if (editingGroup) {
        // 更新现有组
        console.log('📝 更新现有组:', editingGroup.id)
        updatedGroups = safeParallelGroups.map(g => 
          g.id === editingGroup.id ? { ...g, ...values } : g
        )
      } else {
        // 创建新组
        const newGroup: ParallelGroup = {
          id: `parallel_${Date.now()}`,
          ...values,
          steps: Array.isArray(values.steps) ? values.steps : []
        }
        console.log('🆕 创建新组:', newGroup.id, newGroup.name)
        updatedGroups = [...safeParallelGroups, newGroup]
      }
      
      console.log('💾 调用onChange，共', updatedGroups.length, '个组')
      // 调用父组件的保存函数，会同步到后端
      onChange(updatedGroups)
      setFormVisible(false)
      setEditingGroup(null)
      form.resetFields()
    } catch (error) {
      console.error('Failed to save parallel group:', error)
    }
  }

  // 获取同步策略的显示文本
  const getSyncPolicyText = (policy: string) => {
    switch (policy) {
      case 'wait_all':
        return '等待所有步骤完成'
      case 'wait_any':
        return '等待任一步骤完成'
      case 'fail_fast':
        return '快速失败模式'
      default:
        return policy
    }
  }

  // 获取同步策略的颜色
  const getSyncPolicyColor = (policy: string) => {
    switch (policy) {
      case 'wait_all':
        return 'blue'
      case 'wait_any':
        return 'green'
      case 'fail_fast':
        return 'red'
      default:
        return 'default'
    }
  }

  // 获取组中的步骤名称
  const getGroupStepNames = (stepIds: number[]) => {
    if (!Array.isArray(stepIds) || stepIds.length === 0) return []
    if (!Array.isArray(safeAvailableSteps) || safeAvailableSteps.length === 0) return stepIds.map(id => `步骤 ${id}`)
    
    return stepIds.map(id => {
      const step = safeAvailableSteps.find(s => s.id === id)
      return step ? (step.name || `步骤 ${id}`) : `步骤 ${id}`
    })
  }

  // 根据步骤的parallel_group字段动态获取属于该组的步骤
  const getStepsForGroup = (groupId: string) => {
    console.log('🔍 获取并行组步骤:', groupId, '可用步骤:', safeAvailableSteps.length)
    
    if (!Array.isArray(safeAvailableSteps) || safeAvailableSteps.length === 0) {
      console.warn('⚠️ availableSteps 不是数组或为空')
      return []
    }
    
    // 方法1: 从步骤的parallel_group字段获取（主要数据源）
    const stepsFromField = safeAvailableSteps
      .filter(step => step.parallel_group === groupId)
      .map(step => step.id)
    
    console.log('📋 从步骤字段获取:', stepsFromField)
    
    // 方法2: 从并行组的steps数组获取（备选数据源）
    let stepsFromGroup: number[] = []
    const group = safeParallelGroups.find(g => g.id === groupId)
    if (group && Array.isArray(group.steps)) {
      stepsFromGroup = group.steps
    }
    
    console.log('📋 从并行组配置获取:', stepsFromGroup)
    
    // 优先使用步骤字段的数据，如果为空则使用并行组配置的数据
    const result = stepsFromField.length > 0 ? stepsFromField : stepsFromGroup
    
    console.log('✅ 最终结果:', result)
    return result
  }

  return (
    <>
      <Modal
        title={
          <Space>
            <ClusterOutlined />
            <span>并行组管理</span>
          </Space>
        }
        open={visible}
        onCancel={onClose}
        width={800}
        footer={[
          <Button key="close" onClick={onClose}>
            关闭
          </Button>,
          <Button key="create" type="primary" icon={<PlusOutlined />} onClick={handleCreateGroup}>
            创建并行组
          </Button>
        ]}
      >
        <div>
          <Alert
            message="并行组说明"
            description="并行组用于配置可以同时执行的步骤。同一组内的步骤会并行启动，根据同步策略决定何时继续执行后续步骤。"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          {safeParallelGroups.length === 0 ? (
            <Card style={{ textAlign: 'center', padding: '40px' }}>
              <Text type="secondary">暂无并行组配置</Text>
              <br />
              <Button type="dashed" icon={<PlusOutlined />} onClick={handleCreateGroup} style={{ marginTop: 16 }}>
                创建第一个并行组
              </Button>
            </Card>
          ) : (
            <List
              dataSource={safeParallelGroups}
              renderItem={(group) => (
                <List.Item>
                  <Card
                    style={{ width: '100%' }}
                    title={
                      <Space>
                        <ClusterOutlined />
                        <span>{group.name}</span>
                        <Tag color={getSyncPolicyColor(group.sync_policy)}>
                          {getSyncPolicyText(group.sync_policy)}
                        </Tag>
                      </Space>
                    }
                    extra={
                      <Space>
                        <Button
                          type="text"
                          size="small"
                          icon={<EditOutlined />}
                          onClick={() => handleEditGroup(group)}
                        />
                        <Popconfirm
                          title="确定要删除这个并行组吗？"
                          description="删除后，组内步骤将变为普通顺序执行。"
                          onConfirm={() => handleDeleteGroup(group.id)}
                          okText="确定"
                          cancelText="取消"
                        >
                          <Button
                            type="text"
                            size="small"
                            icon={<DeleteOutlined />}
                            danger
                          />
                        </Popconfirm>
                      </Space>
                    }
                  >
                    <Space direction="vertical" style={{ width: '100%' }}>
                      {group.description && (
                        <Text type="secondary">{group.description}</Text>
                      )}
                      
                      <Space>
                        <ClockCircleOutlined />
                        <Text>超时时间: {group.timeout_seconds}秒</Text>
                      </Space>

                      {(() => {
                        // 动态获取属于该组的步骤
                        const groupSteps = getStepsForGroup(group.id)
                        return groupSteps.length > 0 ? (
                          <div>
                            <Text strong>包含步骤: </Text>
                            {getGroupStepNames(groupSteps).map((name, index) => (
                              <Tag key={index} style={{ margin: '2px' }}>
                                {name}
                              </Tag>
                            ))}
                          </div>
                        ) : (
                          <Text type="secondary">暂无步骤分配到此组</Text>
                        )
                      })()}
                    </Space>
                  </Card>
                </List.Item>
              )}
            />
          )}
        </div>
      </Modal>

      {/* 并行组编辑表单 */}
      <Modal
        title={editingGroup ? '编辑并行组' : '创建并行组'}
        open={formVisible}
        onOk={handleSaveGroup}
        onCancel={() => {
          setFormVisible(false)
          setEditingGroup(null)
          form.resetFields()
        }}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="并行组名称"
            rules={[{ required: true, message: '请输入并行组名称' }]}
          >
            <Input placeholder="输入并行组名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea placeholder="输入描述（可选）" rows={2} />
          </Form.Item>

          <Form.Item
            name="sync_policy"
            label="同步策略"
            rules={[{ required: true, message: '请选择同步策略' }]}
            tooltip="决定何时继续执行后续步骤"
          >
            <Select placeholder="选择同步策略">
              <Option value="wait_all">
                <Space>
                  <SyncOutlined />
                  <span>等待所有步骤完成</span>
                </Space>
              </Option>
              <Option value="wait_any">
                <Space>
                  <SyncOutlined />
                  <span>等待任一步骤完成</span>
                </Space>
              </Option>
              <Option value="fail_fast">
                <Space>
                  <SyncOutlined />
                  <span>快速失败模式</span>
                </Space>
              </Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="timeout_seconds"
            label="超时时间（秒）"
            rules={[{ required: true, message: '请输入超时时间' }]}
            tooltip="并行组执行的最大时间限制"
          >
            <InputNumber
              min={60}
              max={86400}
              placeholder="3600"
              style={{ width: '100%' }}
              addonAfter="秒"
            />
          </Form.Item>

          <Form.Item
            name="steps"
            label="分配步骤"
            tooltip="选择要加入此并行组的步骤"
          >
            <Select
              mode="multiple"
              placeholder="选择要并行执行的步骤"
              style={{ width: '100%' }}
              optionFilterProp="label"
              showSearch
              filterOption={(input, option) =>
                (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
              }
            >
              {Array.isArray(safeAvailableSteps) && safeAvailableSteps.length > 0 ? (
                safeAvailableSteps
                  .filter(step => {
                    // 如果正在编辑现有组，显示该组的步骤以及未分配的步骤
                    if (editingGroup) {
                      return !step.parallel_group || step.parallel_group === editingGroup.id
                    }
                    // 如果创建新组，只显示未分配的步骤
                    return !step.parallel_group
                  })
                  .map(step => (
                    <Option key={step.id} value={step.id} label={`${step.step_type || 'unknown'} - ${step.name || 'unnamed'}`}>
                      <Space>
                        <Tag color="blue">{step.step_type || 'unknown'}</Tag>
                        {step.name || 'unnamed'}
                      </Space>
                    </Option>
                  ))
              ) : (
                <Option key="no-steps" value="" disabled>
                  暂无可用步骤
                </Option>
              )}
            </Select>
          </Form.Item>
        </Form>

        <Alert
          message="同步策略说明"
          description={
            <div>
              <p><strong>等待所有步骤完成：</strong>所有并行步骤都成功后才继续</p>
              <p><strong>等待任一步骤完成：</strong>任意一个步骤成功后就继续</p>
              <p><strong>快速失败模式：</strong>任意一个步骤失败时立即停止整个流水线</p>
            </div>
          }
          type="info"
          showIcon
          style={{ marginTop: 16 }}
        />
      </Modal>
    </>
  )
}

export default ParallelGroupManager
