import React, { useEffect, useState } from 'react'
import { 
  Row, 
  Col, 
  Card, 
  Statistic, 
  Table, 
  Progress, 
  Timeline,
  List,
  Tag,
  Button,
  Tooltip,
  Space,
  Alert,
  Badge,
  Divider,
  Typography,
  Empty,
  Tabs,
  Spin,
  Descriptions,
  message,
  Grid
} from 'antd'
import {
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  ToolOutlined,
  AppstoreOutlined,
  RocketOutlined,
  TeamOutlined,
  CalendarOutlined,
  BarChartOutlined,
  WarningOutlined,
  TrophyOutlined,
  FireOutlined,
  ReloadOutlined,
  EyeOutlined,
  SettingOutlined,
  DatabaseOutlined,
  CloudOutlined,
  SafetyCertificateOutlined,
  BugOutlined,
  CiOutlined,
  HddOutlined,
  DashboardOutlined,
  LineChartOutlined,
  AreaChartOutlined,
  NodeIndexOutlined,
  SyncOutlined,
  MonitorOutlined,
  AlertOutlined,
  RiseOutlined,
  ClusterOutlined,
  BookOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../stores/app'
import { ColumnsType } from 'antd/es/table'
import { PipelineExecution } from '../types'
import { formatDistanceToNow, format, subDays, startOfDay, endOfDay } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import apiService from '../services/api'

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs
const { useBreakpoint } = Grid

const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const { 
    tools,
    toolsLoading,
    loadTools,
    executions,
    executionsLoading,
    loadExecutions
  } = useAppStore()

  // 新增状态
  const [systemStats, setSystemStats] = useState<any>(null)
  const [ansibleStats, setAnsibleStats] = useState<any>(null)
  const [pipelines, setPipelines] = useState<any[]>([])
  const [pipelineStats, setPipelineStats] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [lastRefresh, setLastRefresh] = useState(new Date())
  const [activeTab, setActiveTab] = useState('overview')
  const [refreshInterval, setRefreshInterval] = useState<number | null>(null)
  const screens = useBreakpoint()

  useEffect(() => {
    loadDashboardData()
    
    // 设置自动刷新
    const interval = setInterval(() => {
      loadDashboardData()
    }, 30000) // 30秒刷新一次
    
    setRefreshInterval(interval)
    
    return () => {
      if (interval) {
        clearInterval(interval)
      }
    }
  }, [loadTools, loadExecutions])

  const loadDashboardData = async () => {
    setLoading(true)
    try {
      await Promise.all([
        loadTools(),
        loadExecutions(),
        loadSystemStats(),
        loadAnsibleStats(),
        loadPipelines(),
        loadPipelineStats()
      ])
      setLastRefresh(new Date())
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      message.error('加载仪表板数据失败')
    } finally {
      setLoading(false)
    }
  }

  const loadSystemStats = async () => {
    try {
      // 模拟系统统计数据，实际应该从API获取
      const stats = {
        cpu_usage: Math.floor(Math.random() * 100),
        memory_usage: Math.floor(Math.random() * 100),
        disk_usage: Math.floor(Math.random() * 100),
        active_connections: Math.floor(Math.random() * 50) + 10,
        uptime: '15天 8小时 32分钟'
      }
      setSystemStats(stats)
    } catch (error) {
      console.error('Failed to load system stats:', error)
    }
  }

  const loadAnsibleStats = async () => {
    try {
      const stats = await apiService.getAnsibleStats()
      setAnsibleStats(stats)
    } catch (error) {
      console.error('Failed to load ansible stats:', error)
    }
  }

  const loadPipelines = async () => {
    try {
      const response = await apiService.getPipelines()
      setPipelines(Array.isArray(response) ? response : (response as any).results || [])
    } catch (error) {
      console.error('Failed to load pipelines:', error)
    }
  }

  const loadPipelineStats = async () => {
    try {
      const stats = await apiService.getPipelineStats()
      setPipelineStats(stats)
    } catch (error) {
      console.error('Failed to load pipeline stats:', error)
    }
  }

  const handleRefresh = () => {
    loadDashboardData()
  }

  const handleExecutionClick = (executionId: number) => {
    navigate(`/executions/${executionId}`)
  }

  const getExecutionStats = () => {
    const total = (executions || []).length
    const running = (executions || []).filter(e => e.status === 'running').length
    const success = (executions || []).filter(e => e.status === 'success').length
    const failed = (executions || []).filter(e => e.status === 'failed').length
    const pending = (executions || []).filter(e => e.status === 'pending').length

    return { total, running, success, failed, pending }
  }

  const getToolStats = () => {
    const total = (tools || []).length
    const active = (tools || []).filter(t => t.is_active).length
    const jenkins = (tools || []).filter(t => t.tool_type === 'jenkins').length
    const others = total - jenkins
    
    return { total, active, jenkins, others }
  }

  const getPipelineStatsData = () => {
    const total = pipelines.length
    const active = pipelines.filter(p => p.is_active).length
    const withAnsible = pipelines.filter(p => 
      p.steps && p.steps.some((step: any) => step.step_type === 'ansible')
    ).length
    
    return { total, active, withAnsible }
  }

  const getSystemHealthStatus = () => {
    if (!systemStats) return 'unknown'
    
    const { cpu_usage, memory_usage, disk_usage } = systemStats
    const maxUsage = Math.max(cpu_usage, memory_usage, disk_usage)
    
    if (maxUsage >= 90) return 'critical'
    if (maxUsage >= 75) return 'warning'
    if (maxUsage >= 50) return 'good'
    return 'excellent'
  }

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'excellent': return '#52c41a'
      case 'good': return '#1890ff'
      case 'warning': return '#faad14'
      case 'critical': return '#ff4d4f'
      default: return '#d9d9d9'
    }
  }

  const executionStats = getExecutionStats()
  const toolStats = getToolStats()
  const pipelineStatsData = getPipelineStatsData()
  const systemHealthStatus = getSystemHealthStatus()

  const recentExecutions = (executions || [])
    .filter(e => e.started_at) // 先过滤掉没有开始时间的
    .sort((a, b) => new Date(b.started_at!).getTime() - new Date(a.started_at!).getTime())
    .slice(0, 5)

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'running':
        return <PlayCircleOutlined style={{ color: '#1890ff' }} />
      case 'pending':
        return <ClockCircleOutlined style={{ color: '#faad14' }} />
      case 'cancelled':
        return <CloseCircleOutlined style={{ color: '#8c8c8c' }} />
      case 'timeout':
        return <CloseCircleOutlined style={{ color: '#fa8c16' }} />
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />
    }
  }

  const recentExecutionColumns: ColumnsType<PipelineExecution> = [
    {
      title: '流水线',
      dataIndex: 'pipeline_name',
      key: 'pipeline_name',
      width: 150,
      render: (pipeline_name: string, record: PipelineExecution) => (
        <a 
          onClick={() => handleExecutionClick(record.id)}
          style={{ cursor: 'pointer', color: '#1890ff' }}
        >
          {pipeline_name || `Pipeline ${record.pipeline}`}
        </a>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => getStatusIcon(status),
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      width: 120,
      render: (started_at: string) => started_at ? (
        <div style={{ fontSize: 12, color: '#666' }}>
          {formatDistanceToNow(new Date(started_at), {
            addSuffix: true,
            locale: zhCN
          })}
        </div>
      ) : '-',
    },
  ]

  return (
    <div style={{ padding: screens.md ? '24px' : '16px' }}>
      {/* 页面头部 */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
        <Title level={2} style={{ margin: 0 }}>
          <DashboardOutlined /> 运营仪表板
        </Title>
        <Space>
          <Text type="secondary">
            最后更新: {format(lastRefresh, 'yyyy-MM-dd HH:mm:ss')}
          </Text>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={handleRefresh}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      </div>

      {/* 系统健康警告 */}
      {systemStats && systemHealthStatus === 'critical' && (
        <Alert
          message="系统资源警告"
          description="系统资源使用率过高，请及时处理"
          type="error"
          showIcon
          style={{ marginBottom: 24 }}
          action={
            <Button size="small" danger>
              查看详情
            </Button>
          }
        />
      )}

      {/* 主要统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card>
            <Statistic
              title="总执行次数"
              value={executionStats.total}
              prefix={<PlayCircleOutlined />}
              suffix={
                <Badge 
                  count={executionStats.running} 
                  style={{ backgroundColor: '#1890ff' }}
                />
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card>
            <Statistic
              title="成功率"
              value={
                executionStats.total > 0 
                  ? Math.round((executionStats.success / executionStats.total) * 100)
                  : 0
              }
              suffix="%"
              prefix={<TrophyOutlined />}
              valueStyle={{ 
                color: executionStats.total > 0 && executionStats.success / executionStats.total > 0.8 
                  ? '#3f8600' 
                  : '#faad14' 
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card>
            <Statistic
              title="活跃流水线"
              value={pipelineStatsData.active}
              prefix={<RocketOutlined />}
              suffix={`/ ${pipelineStatsData.total}`}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card>
            <Statistic
              title="Ansible集成"
              value={pipelineStatsData.withAnsible}
              prefix={<ClusterOutlined />}
              suffix="条流水线"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card>
            <Statistic
              title="系统健康"
              value={systemHealthStatus}
              prefix={<MonitorOutlined />}
              valueStyle={{ color: getHealthColor(systemHealthStatus) }}
              formatter={(value) => {
                const statusMap: Record<string, string> = {
                  excellent: '优秀',
                  good: '良好', 
                  warning: '警告',
                  critical: '危险',
                  unknown: '未知'
                }
                return statusMap[value as string] || '未知'
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card>
            <Statistic
              title="工具连接"
              value={toolStats.active}
              prefix={<ToolOutlined />}
              suffix={`/ ${toolStats.total}`}
              valueStyle={{ 
                color: toolStats.total > 0 && toolStats.active === toolStats.total 
                  ? '#3f8600' 
                  : '#faad14' 
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 详细信息选项卡 */}
      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        items={[
          {
            key: 'overview',
            label: (
              <span>
                <BarChartOutlined />
                概览
              </span>
            ),
            children: (
              <Row gutter={[16, 16]}>
                {/* 系统资源监控 */}
                <Col xs={24} lg={8}>
                  <Card 
                    title={
                      <span>
                        <MonitorOutlined /> 系统资源
                      </span>
                    }
                    extra={
                      <Badge 
                        status={systemHealthStatus === 'excellent' ? 'success' : 
                               systemHealthStatus === 'good' ? 'processing' :
                               systemHealthStatus === 'warning' ? 'warning' : 'error'} 
                        text={systemHealthStatus === 'excellent' ? '正常' : 
                              systemHealthStatus === 'good' ? '良好' :
                              systemHealthStatus === 'warning' ? '注意' : '告警'}
                      />
                    }
                  >
                    {systemStats ? (
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                            <span><CiOutlined /> CPU使用率</span>
                            <span>{systemStats.cpu_usage}%</span>
                          </div>
                          <Progress 
                            percent={systemStats.cpu_usage} 
                            strokeColor={systemStats.cpu_usage > 80 ? '#ff4d4f' : systemStats.cpu_usage > 60 ? '#faad14' : '#52c41a'}
                            size="small"
                          />
                        </div>
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                            <span><HddOutlined /> 内存使用率</span>
                            <span>{systemStats.memory_usage}%</span>
                          </div>
                          <Progress 
                            percent={systemStats.memory_usage} 
                            strokeColor={systemStats.memory_usage > 80 ? '#ff4d4f' : systemStats.memory_usage > 60 ? '#faad14' : '#52c41a'}
                            size="small"
                          />
                        </div>
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                            <span><DatabaseOutlined /> 磁盘使用率</span>
                            <span>{systemStats.disk_usage}%</span>
                          </div>
                          <Progress 
                            percent={systemStats.disk_usage} 
                            strokeColor={systemStats.disk_usage > 80 ? '#ff4d4f' : systemStats.disk_usage > 60 ? '#faad14' : '#52c41a'}
                            size="small"
                          />
                        </div>
                        <Divider />
                        <Descriptions size="small" column={1}>
                          <Descriptions.Item label="活跃连接">{systemStats.active_connections}</Descriptions.Item>
                          <Descriptions.Item label="运行时间">{systemStats.uptime}</Descriptions.Item>
                        </Descriptions>
                      </Space>
                    ) : (
                      <Spin />
                    )}
                  </Card>
                </Col>

                {/* Ansible统计 */}
                <Col xs={24} lg={8}>
                  <Card 
                    title={
                      <span>
                        <ClusterOutlined /> Ansible统计
                      </span>
                    }
                  >
                    {ansibleStats ? (
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Row gutter={16}>
                          <Col span={12}>
                            <Statistic
                              title="Playbook总数"
                              value={ansibleStats.total_playbooks || 0}
                              prefix={<BookOutlined />}
                              valueStyle={{ fontSize: 20 }}
                            />
                          </Col>
                          <Col span={12}>
                            <Statistic
                              title="清单文件"
                              value={ansibleStats.total_inventories || 0}
                              prefix={<AppstoreOutlined />}
                              valueStyle={{ fontSize: 20 }}
                            />
                          </Col>
                        </Row>
                        <Row gutter={16}>
                          <Col span={12}>
                            <Statistic
                              title="执行次数"
                              value={ansibleStats.total_executions || 0}
                              prefix={<PlayCircleOutlined />}
                              valueStyle={{ fontSize: 20 }}
                            />
                          </Col>
                          <Col span={12}>
                            <Statistic
                              title="成功率"
                              value={ansibleStats.success_rate || 0}
                              suffix="%"
                              prefix={<CheckCircleOutlined />}
                              valueStyle={{ 
                                fontSize: 20,
                                color: (ansibleStats.success_rate || 0) > 80 ? '#3f8600' : '#faad14'
                              }}
                            />
                          </Col>
                        </Row>
                      </Space>
                    ) : (
                      <Spin />
                    )}
                  </Card>
                </Col>

                {/* 流水线分析 */}
                <Col xs={24} lg={8}>
                  <Card 
                    title={
                      <span>
                        <RocketOutlined /> 流水线分析
                      </span>
                    }
                  >
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div style={{ textAlign: 'center' }}>
                        <Progress
                          type="circle"
                          percent={
                            pipelineStatsData.total > 0 
                              ? Math.round((pipelineStatsData.active / pipelineStatsData.total) * 100)
                              : 0
                          }
                          strokeColor={{
                            '0%': '#108ee9',
                            '100%': '#87d068',
                          }}
                          format={(percent) => `${percent}%\n活跃率`}
                        />
                      </div>
                      <Divider />
                      <Descriptions size="small" column={1}>
                        <Descriptions.Item label="总流水线数">{pipelineStatsData.total}</Descriptions.Item>
                        <Descriptions.Item label="活跃流水线">{pipelineStatsData.active}</Descriptions.Item>
                        <Descriptions.Item label="集成Ansible">{pipelineStatsData.withAnsible}</Descriptions.Item>
                        <Descriptions.Item label="今日执行">
                          {(executions || []).filter(e => 
                            e.started_at && 
                            new Date(e.started_at).toDateString() === new Date().toDateString()
                          ).length}
                        </Descriptions.Item>
                      </Descriptions>
                    </Space>
                  </Card>
                </Col>
              </Row>
            )
          },
          {
            key: 'executions',
            label: (
              <span>
                <PlayCircleOutlined />
                执行记录
              </span>
            ),
            children: (
              <Row gutter={[16, 16]}>
                {/* 执行状态分布 */}
                <Col xs={24} lg={12}>
                  <Card title="执行状态分布">
                    <Row gutter={16}>
                      <Col span={8}>
                        <Statistic
                          title="运行中"
                          value={executionStats.running}
                          prefix={<PlayCircleOutlined />}
                          valueStyle={{ color: '#1890ff' }}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="等待中"
                          value={executionStats.pending}
                          prefix={<ClockCircleOutlined />}
                          valueStyle={{ color: '#faad14' }}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="已完成"
                          value={executionStats.success + executionStats.failed}
                          prefix={<CheckCircleOutlined />}
                          valueStyle={{ color: '#52c41a' }}
                        />
                      </Col>
                    </Row>
                  </Card>
                </Col>

                {/* 最近活动时间线 */}
                <Col xs={24} lg={12}>
                  <Card title="最近活动" extra={<CalendarOutlined />}>
                    <Timeline
                      items={recentExecutions.map(execution => ({
                        dot: getStatusIcon(execution.status),
                        children: (
                          <div>
                            <div 
                              style={{ 
                                fontWeight: 500, 
                                cursor: 'pointer', 
                                color: '#1890ff',
                                textDecoration: 'none'
                              }}
                              onClick={() => handleExecutionClick(execution.id)}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.textDecoration = 'underline'
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.textDecoration = 'none'
                              }}
                            >
                              {execution.pipeline_name || `Pipeline ${execution.pipeline}`}
                            </div>
                            <div style={{ fontSize: 12, color: '#666' }}>
                              {execution.started_at && formatDistanceToNow(new Date(execution.started_at), {
                                addSuffix: true,
                                locale: zhCN
                              })}
                            </div>
                          </div>
                        )
                      }))}
                    />
                  </Card>
                </Col>

                {/* 详细执行表格 */}
                <Col span={24}>
                  <Card title="最近执行记录" extra={<EyeOutlined />}>
                    <Table
                      columns={recentExecutionColumns}
                      dataSource={recentExecutions}
                      loading={executionsLoading}
                      pagination={false}
                      size="small"
                      rowKey="id"
                    />
                  </Card>
                </Col>
              </Row>
            )
          },
          {
            key: 'tools',
            label: (
              <span>
                <ToolOutlined />
                工具管理
              </span>
            ),
            children: (
              <Row gutter={[16, 16]}>
                {/* 工具概览 */}
                <Col xs={24} lg={12}>
                  <Card title="工具连接状态">
                    <div style={{ marginBottom: 16 }}>
                      <Progress 
                        percent={toolStats.total > 0 ? Math.round((toolStats.active / toolStats.total) * 100) : 0} 
                        strokeColor={{
                          '0%': '#108ee9',
                          '100%': '#87d068',
                        }}
                        format={(percent) => `${toolStats.active}/${toolStats.total} 活跃`}
                      />
                    </div>
                    <Descriptions column={1}>
                      <Descriptions.Item label="总工具数">{toolStats.total}</Descriptions.Item>
                      <Descriptions.Item label="活跃连接">{toolStats.active}</Descriptions.Item>
                      <Descriptions.Item label="Jenkins实例">{toolStats.jenkins}</Descriptions.Item>
                      <Descriptions.Item label="其他工具">{toolStats.others}</Descriptions.Item>
                    </Descriptions>
                  </Card>
                </Col>

                {/* 工具类型分布 */}
                <Col xs={24} lg={12}>
                  <Card title="工具类型分布">
                    <List
                      dataSource={[
                        { name: 'Jenkins', count: toolStats.jenkins, icon: <ToolOutlined />, color: '#1890ff' },
                        { name: '其他工具', count: toolStats.others, icon: <AppstoreOutlined />, color: '#52c41a' }
                      ]}
                      renderItem={item => (
                        <List.Item>
                          <List.Item.Meta
                            avatar={<div style={{ color: item.color }}>{item.icon}</div>}
                            title={item.name}
                            description={`${item.count} 个实例`}
                          />
                          <div>
                            <Progress 
                              percent={toolStats.total > 0 ? Math.round((item.count / toolStats.total) * 100) : 0}
                              strokeColor={item.color}
                              size="small"
                              style={{ width: 100 }}
                            />
                          </div>
                        </List.Item>
                      )}
                    />
                  </Card>
                </Col>
              </Row>
            )
          }
        ]}
      />
    </div>
  )
}

export default Dashboard
