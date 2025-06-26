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
    toolsLoading,
    loadTools,
    executions,
    executionsLoading,
    loadExecutions
  } = useAppStore()

  useEffect(() => {
    loadTools()
    loadExecutions()
  }, [loadTools, loadExecutions])

  const getExecutionStats = () => {
    const total = executions.length
    const running = executions.filter(e => e.status === 'running').length
    const success = executions.filter(e => e.status === 'completed').length
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
    .filter(e => e.started_at) // 先过滤掉没有开始时间的
    .sort((a, b) => new Date(b.started_at!).getTime() - new Date(a.started_at!).getTime())
    .slice(0, 5)

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'running':
        return <PlayCircleOutlined style={{ color: '#1890ff' }} />
      default:
        return <ClockCircleOutlined style={{ color: '#faad14' }} />
    }
  }

  const recentExecutionColumns: ColumnsType<PipelineExecution> = [
    {
      title: '流水线',
      dataIndex: 'pipeline_name',
      key: 'pipeline_name',
      width: 150,
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
    <div style={{ padding: '24px' }}>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总执行次数"
              value={executionStats.total}
              prefix={<PlayCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="运行中"
              value={executionStats.running}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功执行"
              value={executionStats.success}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="失败执行"
              value={executionStats.failed}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card title="工具概览" extra={<ToolOutlined />}>
            <div style={{ marginBottom: 16 }}>
              <div>总工具数: {toolStats.total}</div>
              <div>活跃工具: {toolStats.active}</div>
              <div>Jenkins实例: {toolStats.jenkins}</div>
            </div>
            <Progress 
              percent={toolStats.total > 0 ? Math.round((toolStats.active / toolStats.total) * 100) : 0} 
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="执行成功率" extra={<AppstoreOutlined />}>
            <div style={{ textAlign: 'center' }}>
              <Progress
                type="circle"
                percent={
                  executionStats.total > 0 
                    ? Math.round((executionStats.success / executionStats.total) * 100)
                    : 0
                }
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
              />
            </div>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="最近活动" extra={<PlayCircleOutlined />}>
            <Timeline
              items={recentExecutions.map(execution => ({
                dot: getStatusIcon(execution.status),
                children: (
                  <div>
                    <div style={{ fontWeight: 500 }}>
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
      </Row>

      <Row gutter={16}>
        <Col span={24}>
          <Card title="最近执行" extra={<PlayCircleOutlined />}>
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
    </div>
  )
}

export default Dashboard
