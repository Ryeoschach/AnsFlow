import React, { useState, useEffect, useMemo } from 'react'
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
  List,
  Progress,
  Statistic,
  Row,
  Col,
  Tabs,
  Table,
  Button,
  message,
  Spin,
  Empty,
  Select,
  DatePicker,
  Tooltip
} from 'antd'
import {
  FundOutlined,
  ClockCircleOutlined,
  BranchesOutlined,
  ClusterOutlined,
  AuditOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ThunderboltOutlined,
  ShareAltOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  BarChartOutlined,
  LineChartOutlined,
  DashboardOutlined,
  BugOutlined,
  TrophyOutlined,
  RocketOutlined
} from '@ant-design/icons'
import { EnhancedPipelineStep, ParallelGroup, Pipeline } from '../../types'
import apiService from '../../services/api'

const { Text, Title } = Typography
const { TabPane } = Tabs
const { Option } = Select
const { RangePicker } = DatePicker

interface WorkflowAnalyzerProps {
  visible: boolean
  pipeline?: Pipeline
  steps: EnhancedPipelineStep[]
  parallelGroups: ParallelGroup[]
  onClose: () => void
}

interface WorkflowMetrics {
  total_steps: number
  parallel_steps: number
  conditional_steps: number
  approval_steps: number
  estimated_duration: number
  complexity_score: number
  critical_path: number[]
  risk_factors: Array<{
    type: 'high' | 'medium' | 'low'
    message: string
    step_id?: number
  }>
  performance_metrics: {
    avg_step_duration: number
    failure_rate: number
    success_rate: number
    retry_rate: number
  }
  historical_data: Array<{
    date: string
    duration: number
    success: boolean
    steps_count: number
  }>
}

interface DependencyInfo {
  step_id: number
  step_name: string
  dependencies: number[]
  dependents: number[]
  is_critical: boolean
  parallel_group?: string
}

interface OptimizationSuggestion {
  type: 'performance' | 'reliability' | 'maintainability' | 'security'
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  impact: string
  effort: string
  steps_affected: number[]
}

interface DependencyAnalysis {
  dependencies: Array<{
    step_id: number
    depends_on: number[]
    step_name: string
  }>
  cycles: Array<{
    cycle_steps: number[]
    severity: 'warning' | 'error'
  }>
  critical_path: Array<{
    step_id: number
    step_name: string
    estimated_duration: number
  }>
  parallelization_suggestions: Array<{
    suggestion: string
    affected_steps: number[]
    potential_improvement: string
  }>
}

const WorkflowAnalyzerEnhanced: React.FC<WorkflowAnalyzerProps> = ({
  visible,
  pipeline,
  steps,
  parallelGroups,
  onClose
}) => {
  const [loading, setLoading] = useState(false)
  const [metrics, setMetrics] = useState<WorkflowMetrics | null>(null)
  const [dependencies, setDependencies] = useState<DependencyAnalysis | null>(null)
  const [activeTab, setActiveTab] = useState('overview')

  // 本地分析
  const localAnalysis = useMemo(() => {
    const totalSteps = steps.length
    const parallelSteps = steps.filter(s => s.parallel_group_id).length
    const conditionalSteps = steps.filter(s => s.condition && s.condition.type !== 'always').length
    const approvalSteps = steps.filter(s => s.requires_approval).length
    
    // 计算复杂度分数 (0-100)
    let complexityScore = 0
    complexityScore += conditionalSteps * 10  // 条件步骤增加复杂度
    complexityScore += approvalSteps * 15     // 审批步骤增加更多复杂度
    complexityScore += parallelGroups.length * 5  // 并行组增加复杂度
    
    // 估算执行时间（分钟）
    let estimatedDuration = 0
    steps.forEach(step => {
      switch (step.step_type) {
        case 'fetch_code':
          estimatedDuration += 2
          break
        case 'build':
          estimatedDuration += 10
          break
        case 'test':
          estimatedDuration += 15
          break
        case 'deploy':
          estimatedDuration += 5
          break
        case 'approval':
          estimatedDuration += 60 // 审批可能需要很长时间
          break
        default:
          estimatedDuration += 3
      }
    })
    
    // 并行执行可以减少总时间
    if (parallelSteps > 0) {
      estimatedDuration *= 0.7 // 假设能节省30%时间
    }

    return {
      totalSteps,
      parallelSteps,
      conditionalSteps,
      approvalSteps,
      complexityScore: Math.min(complexityScore, 100),
      estimatedDuration,
      parallelGroups: parallelGroups.length
    }
  }, [steps, parallelGroups])

  const loadAnalytics = async () => {
    if (!pipeline) return

    try {
      setLoading(true)
      const [metricsData, dependencyData]: [any, any] = await Promise.all([
        apiService.getWorkflowMetrics(pipeline.id),
        apiService.analyzeWorkflowDependencies(pipeline.id)
      ])
      
      // 确保metrics数据完整
      const completeMetrics: WorkflowMetrics = {
        ...metricsData,
        critical_path: metricsData.critical_path || [],
        risk_factors: metricsData.risk_factors || [],
        performance_metrics: metricsData.performance_metrics || {
          avg_step_duration: 0,
          failure_rate: 0,
          success_rate: 100,
          retry_rate: 0
        },
        historical_data: metricsData.historical_data || []
      }
      
      setMetrics(completeMetrics)
      setDependencies(dependencyData)
    } catch (error) {
      console.error('Failed to load workflow analytics:', error)
      message.error('加载工作流分析失败，显示本地分析结果')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (visible && pipeline) {
      loadAnalytics()
    }
  }, [visible, pipeline])

  const getComplexityColor = (score: number) => {
    if (score < 30) return '#52c41a'
    if (score < 60) return '#faad14'
    return '#ff4d4f'
  }

  const getDurationStatus = (duration: number) => {
    if (duration < 30) return 'success'
    if (duration < 120) return 'normal'
    return 'exception'
  }

  const dependencyColumns = [
    {
      title: '步骤',
      dataIndex: 'step_name',
      key: 'step_name',
      render: (text: string, record: any) => (
        <Space>
          <Text strong>{text}</Text>
          <Tag>{steps.find(s => s.id === record.step_id)?.step_type}</Tag>
        </Space>
      )
    },
    {
      title: '依赖步骤',
      dataIndex: 'depends_on',
      key: 'depends_on',
      render: (depends: number[]) => (
        <Space wrap>
          {depends.map(stepId => {
            const step = steps.find(s => s.id === stepId)
            return step ? (
              <Tag key={stepId} color="blue">{step.name}</Tag>
            ) : null
          })}
          {depends.length === 0 && <Text type="secondary">无依赖</Text>}
        </Space>
      )
    }
  ]

  const suggestionColumns = [
    {
      title: '优化建议',
      dataIndex: 'suggestion',
      key: 'suggestion',
      width: '40%'
    },
    {
      title: '影响步骤',
      dataIndex: 'affected_steps',
      key: 'affected_steps',
      render: (stepIds: number[]) => (
        <Space wrap>
          {stepIds.map(id => {
            const step = steps.find(s => s.id === id)
            return step ? (
              <Tag key={id}>{step.name}</Tag>
            ) : null
          })}
        </Space>
      )
    },
    {
      title: '预期改进',
      dataIndex: 'potential_improvement',
      key: 'potential_improvement',
      width: '30%'
    }
  ]

  return (
    <Modal
      title={
        <Space>
          <FundOutlined />
          <span>工作流分析</span>
          {pipeline && <Text type="secondary">- {pipeline.name}</Text>}
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={1000}
      footer={
        <Space>
          <Button onClick={onClose}>关闭</Button>
          {pipeline && (
            <Button 
              icon={<ReloadOutlined />} 
              onClick={loadAnalytics}
              loading={loading}
            >
              重新分析
            </Button>
          )}
        </Space>
      }
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        
        {/* 概览标签页 */}
        <TabPane tab="概览" key="overview">
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="总步骤数"
                  value={localAnalysis.totalSteps}
                  prefix={<ThunderboltOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="并行步骤"
                  value={localAnalysis.parallelSteps}
                  prefix={<ShareAltOutlined />}
                  suffix={`/ ${localAnalysis.totalSteps}`}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="条件步骤"
                  value={localAnalysis.conditionalSteps}
                  prefix={<BranchesOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="审批节点"
                  value={localAnalysis.approvalSteps}
                  prefix={<AuditOutlined />}
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={12}>
              <Card title="复杂度评分" size="small">
                <Progress
                  type="circle"
                  percent={localAnalysis.complexityScore}
                  strokeColor={getComplexityColor(localAnalysis.complexityScore)}
                  format={(percent) => `${percent}/100`}
                />
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary">
                    {localAnalysis.complexityScore < 30 && '简单'}
                    {localAnalysis.complexityScore >= 30 && localAnalysis.complexityScore < 60 && '中等'}
                    {localAnalysis.complexityScore >= 60 && '复杂'}
                    的工作流配置
                  </Text>
                </div>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="预估执行时间" size="small">
                <Progress
                  type="circle"
                  percent={Math.min((localAnalysis.estimatedDuration / 180) * 100, 100)}
                  status={getDurationStatus(localAnalysis.estimatedDuration)}
                  format={() => `${localAnalysis.estimatedDuration}分钟`}
                />
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary">
                    基于步骤类型和并行配置的预估
                  </Text>
                </div>
              </Card>
            </Col>
          </Row>

          <Alert
            message="分析说明"
            description={
              <div>
                <p>• <strong>复杂度评分</strong>: 基于条件步骤、审批节点、并行组数量计算</p>
                <p>• <strong>执行时间</strong>: 考虑步骤类型和并行优化的预估时间</p>
                <p>• <strong>建议</strong>: 合理使用并行执行可以显著减少总执行时间</p>
              </div>
            }
            type="info"
            showIcon
          />
        </TabPane>

        {/* 依赖分析标签页 */}
        <TabPane tab="依赖分析" key="dependencies">
          {dependencies ? (
            <>
              <Card title="依赖关系" size="small" style={{ marginBottom: 16 }}>
                <Table
                  dataSource={dependencies.dependencies}
                  columns={dependencyColumns}
                  rowKey="step_id"
                  size="small"
                  pagination={false}
                />
              </Card>

              {dependencies.cycles.length > 0 && (
                <Card title="循环依赖检测" size="small" style={{ marginBottom: 16 }}>
                  <Alert
                    message="发现循环依赖"
                    description="以下步骤存在循环依赖关系，这会导致流水线无法正常执行"
                    type="error"
                    showIcon
                  />
                  {dependencies.cycles.map((cycle, index) => (
                    <Alert
                      key={index}
                      message={`循环 ${index + 1}`}
                      description={
                        <Space wrap>
                          {cycle.cycle_steps.map(stepId => {
                            const step = steps.find(s => s.id === stepId)
                            return step ? (
                              <Tag key={stepId} color="red">{step.name}</Tag>
                            ) : null
                          })}
                        </Space>
                      }
                      type={cycle.severity}
                      style={{ marginTop: 8 }}
                    />
                  ))}
                </Card>
              )}

              <Card title="关键路径" size="small">
                <Timeline>
                  {dependencies.critical_path.map((item, index) => (
                    <Timeline.Item
                      key={item.step_id}
                      color={index === 0 ? 'green' : 'blue'}
                    >
                      <Space>
                        <Text strong>{item.step_name}</Text>
                        <Tag>预计 {item.estimated_duration} 分钟</Tag>
                      </Space>
                    </Timeline.Item>
                  ))}
                </Timeline>
              </Card>
            </>
          ) : (
            <Card title="依赖关系分析" size="small">
              <Alert
                message="本地分析模式"
                description="当前显示基于客户端的简化分析结果。连接到服务器后可获得更详细的依赖分析。"
                type="info"
                showIcon
              />
              
              <Divider />
              
              <List
                header="步骤执行顺序"
                dataSource={steps.sort((a, b) => a.order - b.order)}
                renderItem={(step, index) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<Tag color="blue">{index + 1}</Tag>}
                      title={
                        <Space>
                          <span>{step.name}</span>
                          <Tag>{step.step_type}</Tag>
                          {step.condition && step.condition.type !== 'always' && (
                            <Tag color="orange">条件执行</Tag>
                          )}
                          {step.parallel_group_id && (
                            <Tag color="green">并行执行</Tag>
                          )}
                          {step.requires_approval && (
                            <Tag color="red">需要审批</Tag>
                          )}
                        </Space>
                      }
                      description={step.description}
                    />
                  </List.Item>
                )}
              />
            </Card>
          )}
        </TabPane>

        {/* 优化建议标签页 */}
        <TabPane tab="优化建议" key="suggestions">
          {dependencies?.parallelization_suggestions ? (
            <Card title="并行化建议" size="small">
              <Table
                dataSource={dependencies.parallelization_suggestions}
                columns={suggestionColumns}
                rowKey={(record, index) => index!}
                size="small"
                pagination={false}
              />
            </Card>
          ) : (
            <Card title="工作流优化建议" size="small">
              <List
                dataSource={[
                  {
                    title: '并行执行优化',
                    description: `当前有 ${localAnalysis.parallelSteps} 个步骤配置了并行执行，可以考虑将更多独立的步骤加入并行组。`,
                    icon: <ShareAltOutlined style={{ color: '#52c41a' }} />
                  },
                  {
                    title: '审批节点优化',
                    description: `当前有 ${localAnalysis.approvalSteps} 个审批节点，过多的审批可能导致执行延迟，建议合并相关审批。`,
                    icon: <AuditOutlined style={{ color: '#faad14' }} />
                  },
                  {
                    title: '条件复杂度',
                    description: `当前有 ${localAnalysis.conditionalSteps} 个条件步骤，复杂的条件判断可能影响执行效率。`,
                    icon: <BranchesOutlined style={{ color: '#1890ff' }} />
                  },
                  {
                    title: '执行时间预估',
                    description: `预估总执行时间约 ${localAnalysis.estimatedDuration} 分钟，可通过优化并行配置进一步缩短。`,
                    icon: <ClockCircleOutlined style={{ color: '#722ed1' }} />
                  }
                ]}
                renderItem={item => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={item.icon}
                      title={item.title}
                      description={item.description}
                    />
                  </List.Item>
                )}
              />
            </Card>
          )}
        </TabPane>

        {/* 性能指标标签页 */}
        <TabPane tab="性能指标" key="metrics">
          {metrics ? (
            <Row gutter={16}>
              <Col span={8}>
                <Card title="执行效率" size="small">
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="总步骤数">
                      {metrics.total_steps}
                    </Descriptions.Item>
                    <Descriptions.Item label="并行步骤数">
                      {metrics.parallel_steps}
                    </Descriptions.Item>
                    <Descriptions.Item label="并行化率">
                      {((metrics.parallel_steps / metrics.total_steps) * 100).toFixed(1)}%
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
              <Col span={8}>
                <Card title="复杂度分析" size="small">
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="条件步骤">
                      {metrics.conditional_steps}
                    </Descriptions.Item>
                    <Descriptions.Item label="审批节点">
                      {metrics.approval_steps}
                    </Descriptions.Item>
                    <Descriptions.Item label="复杂度评分">
                      <Progress
                        percent={metrics.complexity_score}
                        size="small"
                        strokeColor={getComplexityColor(metrics.complexity_score)}
                      />
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
              <Col span={8}>
                <Card title="时间预估" size="small">
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="预估时长">
                      {metrics.estimated_duration} 分钟
                    </Descriptions.Item>
                    <Descriptions.Item label="执行模式">
                      {localAnalysis.parallelSteps > 0 ? '混合并行' : '顺序执行'}
                    </Descriptions.Item>
                    <Descriptions.Item label="优化潜力">
                      {localAnalysis.parallelSteps / localAnalysis.totalSteps < 0.3 ? '高' : '中'}
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
            </Row>
          ) : (
            <Alert
              message="性能指标分析"
              description="连接到服务器后可获得详细的性能指标分析"
              type="info"
              showIcon
            />
          )}
        </TabPane>

      </Tabs>
    </Modal>
  )
}

export default WorkflowAnalyzerEnhanced
