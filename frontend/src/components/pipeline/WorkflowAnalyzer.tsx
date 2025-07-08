import React, { useMemo } from 'react'
import {
  Modal,
  Card,
  Space,
  Tag,
  Typography,
  Alert,
  Descriptions,
  Timeline,
  Divider,
  List
} from 'antd'
import {
  FundOutlined,
  ClockCircleOutlined,
  BranchesOutlined,
  ClusterOutlined,
  AuditOutlined,
  WarningOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'
import { EnhancedPipelineStep, ParallelGroup, WorkflowAnalysis } from '../../types'

const { Text, Title } = Typography

interface WorkflowAnalyzerProps {
  visible: boolean
  steps: EnhancedPipelineStep[]
  parallelGroups: ParallelGroup[]
  onClose: () => void
}

const WorkflowAnalyzer: React.FC<WorkflowAnalyzerProps> = ({
  visible,
  steps,
  parallelGroups,
  onClose
}) => {
  // 分析工作流
  const analysis = useMemo(() => {
    const result: WorkflowAnalysis = {
      total_steps: steps.length,
      parallel_groups: parallelGroups.length,
      approval_steps: steps.filter(s => s.requires_approval).length,
      conditional_steps: steps.filter(s => s.condition && s.condition.type !== 'always').length,
      critical_path: [],
      potential_bottlenecks: []
    }

    // 分析关键路径（简化版本）
    const criticalPath: number[] = []
    const processedSteps = new Set<number>()
    
    // 找到没有依赖的起始步骤
    const startSteps = steps.filter(step => 
      !step.condition?.depends_on || step.condition.depends_on.length === 0
    )
    
    // 构建执行路径
    const buildPath = (currentSteps: EnhancedPipelineStep[]) => {
      for (const step of currentSteps) {
        if (!processedSteps.has(step.id)) {
          criticalPath.push(step.id)
          processedSteps.add(step.id)
          
          // 找到依赖当前步骤的下一个步骤
          const nextSteps = steps.filter(s => 
            s.condition?.depends_on?.includes(step.id)
          )
          
          if (nextSteps.length > 0) {
            buildPath(nextSteps)
          }
        }
      }
    }
    
    buildPath(startSteps)
    result.critical_path = criticalPath

    // 识别潜在瓶颈
    const bottlenecks: string[] = []
    
    // 检查审批步骤
    const approvalSteps = steps.filter(s => s.requires_approval)
    if (approvalSteps.length > 0) {
      bottlenecks.push(`${approvalSteps.length}个审批节点可能导致执行延迟`)
    }
    
    // 检查条件分支
    const conditionalSteps = steps.filter(s => 
      s.condition && s.condition.type === 'expression'
    )
    if (conditionalSteps.length > 0) {
      bottlenecks.push(`${conditionalSteps.length}个复杂条件判断可能影响执行`)
    }
    
    // 检查并行组配置
    const waitAllGroups = parallelGroups.filter(g => g.sync_policy === 'wait_all')
    if (waitAllGroups.length > 0) {
      bottlenecks.push(`${waitAllGroups.length}个"等待所有"并行组可能形成瓶颈`)
    }
    
    result.potential_bottlenecks = bottlenecks
    
    // 估算执行时间（简化计算）
    let estimatedMinutes = 0
    
    // 基础步骤时间估算
    const regularSteps = steps.filter(s => !s.parallel_group_id)
    estimatedMinutes += regularSteps.length * 2 // 假设每个步骤平均2分钟
    
    // 并行组时间估算（取最长的那个）
    for (const group of parallelGroups) {
      const groupSteps = steps.filter(s => s.parallel_group_id === group.id)
      if (groupSteps.length > 0) {
        estimatedMinutes += Math.max(groupSteps.length * 2, 5) // 并行组至少5分钟
      }
    }
    
    // 审批时间估算
    estimatedMinutes += approvalSteps.length * 60 // 假设每个审批1小时
    
    result.estimated_duration_minutes = estimatedMinutes
    
    return result
  }, [steps, parallelGroups])

  // 获取步骤的执行类型标签
  const getStepTypeTag = (step: EnhancedPipelineStep) => {
    const tags = []
    
    if (step.condition && step.condition.type !== 'always') {
      tags.push(
        <Tag key="condition" color="blue" icon={<BranchesOutlined />}>
          条件执行
        </Tag>
      )
    }
    
    if (step.parallel_group_id) {
      tags.push(
        <Tag key="parallel" color="cyan" icon={<ClusterOutlined />}>
          并行执行
        </Tag>
      )
    }
    
    if (step.requires_approval) {
      tags.push(
        <Tag key="approval" color="orange" icon={<AuditOutlined />}>
          需要审批
        </Tag>
      )
    }
    
    return tags
  }

  // 获取条件描述
  const getConditionDescription = (step: EnhancedPipelineStep) => {
    if (!step.condition || step.condition.type === 'always') {
      return '总是执行'
    }
    
    switch (step.condition.type) {
      case 'on_success':
        return '前序步骤成功时执行'
      case 'on_failure':
        return '前序步骤失败时执行'
      case 'expression':
        return `自定义条件: ${step.condition.expression}`
      default:
        return step.condition.type
    }
  }

  return (
    <Modal
      title={
        <Space>
          <FundOutlined />
          <span>工作流分析</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={1000}
      footer={null}
    >
      <div>
        {/* 总览统计 */}
        <Card title="流水线概览" style={{ marginBottom: 16 }}>
          <Descriptions column={4}>
            <Descriptions.Item label="总步骤数">
              <Text strong>{analysis.total_steps}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="并行组数">
              <Text strong>{analysis.parallel_groups}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="审批节点">
              <Text strong>{analysis.approval_steps}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="条件步骤">
              <Text strong>{analysis.conditional_steps}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="预估执行时间" span={2}>
              <Space>
                <ClockCircleOutlined />
                <Text strong>
                  {analysis.estimated_duration_minutes 
                    ? `${Math.floor(analysis.estimated_duration_minutes / 60)}小时${analysis.estimated_duration_minutes % 60}分钟`
                    : '无法估算'
                  }
                </Text>
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="复杂度评估" span={2}>
              {analysis.conditional_steps + analysis.parallel_groups + analysis.approval_steps > 5 ? (
                <Tag color="red" icon={<WarningOutlined />}>复杂</Tag>
              ) : analysis.conditional_steps + analysis.parallel_groups + analysis.approval_steps > 2 ? (
                <Tag color="orange" icon={<WarningOutlined />}>中等</Tag>
              ) : (
                <Tag color="green" icon={<CheckCircleOutlined />}>简单</Tag>
              )}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* 潜在瓶颈警告 */}
        {analysis.potential_bottlenecks && analysis.potential_bottlenecks.length > 0 && (
          <Alert
            message="潜在瓶颈提醒"
            description={
              <List
                size="small"
                dataSource={analysis.potential_bottlenecks}
                renderItem={(item) => (
                  <List.Item>
                    <WarningOutlined style={{ color: '#faad14', marginRight: 8 }} />
                    {item}
                  </List.Item>
                )}
              />
            }
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {/* 执行流程分析 */}
        <Card title="执行流程分析">
          <Timeline>
            {steps.map((step, index) => {
              const isInCriticalPath = analysis.critical_path?.includes(step.id)
              const parallelGroup = step.parallel_group_id 
                ? parallelGroups.find(g => g.id === step.parallel_group_id)
                : null
              
              return (
                <Timeline.Item
                  key={step.id}
                  color={
                    step.requires_approval ? 'orange' :
                    isInCriticalPath ? 'red' :
                    step.parallel_group_id ? 'blue' : 'green'
                  }
                  dot={
                    step.requires_approval ? <AuditOutlined /> :
                    step.parallel_group_id ? <ClusterOutlined /> :
                    step.condition && step.condition.type !== 'always' ? <BranchesOutlined /> :
                    undefined
                  }
                >
                  <div>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Space>
                        <Text strong>{step.name}</Text>
                        <Tag>{step.step_type}</Tag>
                        {getStepTypeTag(step)}
                        {isInCriticalPath && (
                          <Tag color="red">关键路径</Tag>
                        )}
                      </Space>
                      
                      <Text type="secondary">
                        执行条件: {getConditionDescription(step)}
                      </Text>
                      
                      {parallelGroup && (
                        <Text type="secondary">
                          并行组: {parallelGroup.name} ({parallelGroup.sync_policy})
                        </Text>
                      )}
                      
                      {step.requires_approval && step.approval_config && (
                        <Text type="secondary">
                          审批人: {step.approval_config.approvers.join(', ')}
                          {step.approval_config.timeout_hours && 
                            ` (${step.approval_config.timeout_hours}小时内)`
                          }
                        </Text>
                      )}
                      
                      {step.retry_policy?.retry_on_failure && (
                        <Text type="secondary">
                          重试策略: 最多{step.retry_policy.max_retries}次，
                          间隔{step.retry_policy.retry_delay_seconds}秒
                        </Text>
                      )}
                    </Space>
                  </div>
                </Timeline.Item>
              )
            })}
          </Timeline>
        </Card>

        {/* 并行组详情 */}
        {parallelGroups.length > 0 && (
          <Card title="并行组配置" style={{ marginTop: 16 }}>
            {parallelGroups.map(group => {
              const groupSteps = steps.filter(s => s.parallel_group_id === group.id)
              return (
                <Card key={group.id} size="small" style={{ marginBottom: 8 }}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Space>
                      <ClusterOutlined />
                      <Text strong>{group.name}</Text>
                      <Tag color="blue">{group.sync_policy}</Tag>
                      <Tag>超时: {group.timeout_seconds}秒</Tag>
                    </Space>
                    
                    {group.description && (
                      <Text type="secondary">{group.description}</Text>
                    )}
                    
                    <div>
                      <Text>包含步骤: </Text>
                      {groupSteps.map(step => (
                        <Tag key={step.id} style={{ margin: '2px' }}>
                          {step.name}
                        </Tag>
                      ))}
                    </div>
                  </Space>
                </Card>
              )
            })}
          </Card>
        )}

        {/* 优化建议 */}
        <Card title="优化建议" style={{ marginTop: 16 }}>
          <List
            size="small"
            dataSource={[
              analysis.approval_steps > 3 ? '考虑减少审批节点数量或设置并行审批' : null,
              analysis.conditional_steps > 5 ? '复杂的条件逻辑可能影响可维护性，建议简化' : null,
              parallelGroups.filter(g => g.sync_policy === 'wait_all').length > 2 ? 
                '过多的"等待所有"策略可能降低并行效率' : null,
              analysis.total_steps > 20 ? '考虑将大型流水线拆分为多个子流水线' : null,
              steps.filter(s => !s.retry_policy?.retry_on_failure && s.step_type !== 'notify').length > 0 ? 
                '关键步骤建议配置重试策略以提高稳定性' : null
            ].filter(Boolean)}
            renderItem={(item) => (
              <List.Item>
                <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                {item}
              </List.Item>
            )}
          />
        </Card>
      </div>
    </Modal>
  )
}

export default WorkflowAnalyzer
