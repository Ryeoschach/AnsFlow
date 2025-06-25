import React, { useEffect } from 'react'
import { Row, Col, Card, Statistic, Table, Progress, Timeline } from 'antd'
import {
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  ToolOutlined,
  AppstoreOutlined
} from '@ant-design/icons'
import { useAppStore } from '../stores/app'
import { ColumnsType } from 'antd/es/table'
import { PipelineExecution } from '../types'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

const Dashboard: React.FC = () => {
  const { 
    tools, 
    pipelines, 
    executions, 
    loadTools, 
    loadPipelines, 
    loadExecutions 
  } = useAppStore()

  useEffect(() => {
    loadTools()
    loadPipelines()
    loadExecutions()
  }, [loadTools, loadPipelines, loadExecutions])

  const getExecutionStats = () => {
    const total = executions.length
    const running = executions.filter(e => e.status === 'running').length
    const success = executions.filter(e => e.status === 'success').length
    const failed = executions.filter(e => e.status === 'failed').length
    const pending = executions.filter(e => e.status === 'pending').length

    return { total, running, success, failed, pending }
  }

  const getToolStats = () => {
    const total = tools.length
    const active = tools.filter(t => t.is_active).length
    const jenkins = tools.filter(t => t.tool_type === 'jenkins').length
    
    return { total, active, jenkins }
  }

  const executionStats = getExecutionStats()
  const toolStats = getToolStats()

  const recentExecutions = executions
    .sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime())
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
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />
    }
  }

  const getStatusText = (status: string) => {
    const statusMap = {
      success: '成功',
      failed: '失败',
      running: '运行中',
      pending: '等待中',
      cancelled: '已取消'
    }
    return statusMap[status as keyof typeof statusMap] || status
  }

  const executionColumns: ColumnsType<PipelineExecution> = [
    {
      title: '流水线',
      dataIndex: 'pipeline_name',
      key: 'pipeline_name',
      width: 200,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <span>
          {getStatusIcon(status)} {getStatusText(status)}
        </span>
      ),
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      width: 120,
      render: (started_at: string) => 
        formatDistanceToNow(new Date(started_at), {
          addSuffix: true,
          locale: zhCN
        }),
    },
  ]

  const getSuccessRate = () => {
    if (executionStats.total === 0) return 0
    return Math.round((executionStats.success / executionStats.total) * 100)
  }

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总流水线数"
              value={pipelines.length}
              prefix={<AppstoreOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃工具数"
              value={toolStats.active}
              prefix={<ToolOutlined />}
              suffix={`/ ${toolStats.total}`}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="执行中任务"
              value={executionStats.running}
              prefix={<PlayCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功率"
              value={getSuccessRate()}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title="执行状态分布" style={{ height: 400 }}>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <div style={{ textAlign: 'center' }}>
                  <Progress
                    type="circle"
                    percent={getSuccessRate()}
                    format={() => `${getSuccessRate()}%`}
                    strokeColor="#52c41a"
                  />
                  <div style={{ marginTop: 8, fontWeight: 'bold' }}>成功率</div>
                </div>
              </Col>
              <Col span={12}>
                <div>
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>成功</span>
                      <span style={{ color: '#52c41a' }}>{executionStats.success}</span>
                    </div>
                    <Progress
                      percent={executionStats.total > 0 ? (executionStats.success / executionStats.total) * 100 : 0}
                      showInfo={false}
                      strokeColor="#52c41a"
                    />
                  </div>
                  
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>失败</span>
                      <span style={{ color: '#ff4d4f' }}>{executionStats.failed}</span>
                    </div>
                    <Progress
                      percent={executionStats.total > 0 ? (executionStats.failed / executionStats.total) * 100 : 0}
                      showInfo={false}
                      strokeColor="#ff4d4f"
                    />
                  </div>
                  
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>运行中</span>
                      <span style={{ color: '#1890ff' }}>{executionStats.running}</span>
                    </div>
                    <Progress
                      percent={executionStats.total > 0 ? (executionStats.running / executionStats.total) * 100 : 0}
                      showInfo={false}
                      strokeColor="#1890ff"
                    />
                  </div>
                  
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>等待中</span>
                      <span style={{ color: '#faad14' }}>{executionStats.pending}</span>
                    </div>
                    <Progress
                      percent={executionStats.total > 0 ? (executionStats.pending / executionStats.total) * 100 : 0}
                      showInfo={false}
                      strokeColor="#faad14"
                    />
                  </div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
        
        <Col span={12}>
          <Card title="最近执行记录" style={{ height: 400 }}>
            {recentExecutions.length > 0 ? (
              <Timeline
                items={recentExecutions.map(execution => ({
                  dot: getStatusIcon(execution.status),
                  children: (
                    <div>
                      <div style={{ fontWeight: 'bold' }}>{execution.pipeline_name}</div>
                      <div style={{ fontSize: 12, color: '#666' }}>
                        {getStatusText(execution.status)} • {
                          formatDistanceToNow(new Date(execution.started_at), {
                            addSuffix: true,
                            locale: zhCN
                          })
                        }
                      </div>
                    </div>
                  )
                }))}
              />
            ) : (
              <div style={{ textAlign: 'center', color: '#999', marginTop: 50 }}>
                暂无执行记录
              </div>
            )}
          </Card>
        </Col>
      </Row>

      <Row style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="最近执行详情">
            <Table
              columns={executionColumns}
              dataSource={recentExecutions}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
