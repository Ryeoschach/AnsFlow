import React, { useEffect } from 'react'
import { Card, Table, Space, Button, Tag, Progress } from 'antd'
import { 
  PlayCircleOutlined,
  StopOutlined,
  RedoOutlined,
  EyeOutlined
} from '@ant-design/icons'
import { ColumnsType } from 'antd/es/table'
import { PipelineExecution } from '../types'
import { useAppStore } from '../stores/app'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

const Executions: React.FC = () => {
  const { executions, executionsLoading, loadExecutions } = useAppStore()

  useEffect(() => {
    loadExecutions()
  }, [loadExecutions])

  const getStatusTag = (status: string) => {
    const statusConfig = {
      success: { color: 'green', text: '成功' },
      failed: { color: 'red', text: '失败' },
      running: { color: 'blue', text: '运行中' },
      pending: { color: 'orange', text: '等待中' },
      cancelled: { color: 'default', text: '已取消' }
    }
    
    const config = statusConfig[status as keyof typeof statusConfig] || 
                  { color: 'default', text: status }
    
    return <Tag color={config.color}>{config.text}</Tag>
  }

  const getProgressPercent = (execution: PipelineExecution) => {
    if (execution.status === 'success') return 100
    if (execution.status === 'failed' || execution.status === 'cancelled') return 100
    if (execution.status === 'running') {
      // 简单估算，实际应该根据步骤进度计算
      return 50
    }
    return 0
  }

  const columns: ColumnsType<PipelineExecution> = [
    {
      title: '执行ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      render: (id: number) => `#${id}`,
    },
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
      width: 120,
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '进度',
      key: 'progress',
      width: 150,
      render: (_, record: PipelineExecution) => {
        const percent = getProgressPercent(record)
        const status = record.status === 'failed' ? 'exception' : 
                      record.status === 'success' ? 'success' : 'active'
        
        return (
          <Progress 
            percent={percent} 
            size="small" 
            status={status}
            showInfo={false}
          />
        )
      },
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      width: 150,
      render: (started_at: string) => 
        formatDistanceToNow(new Date(started_at), {
          addSuffix: true,
          locale: zhCN
        }),
    },
    {
      title: '持续时间',
      key: 'duration',
      width: 120,
      render: (_, record: PipelineExecution) => {
        if (!record.started_at) return '-'
        
        const start = new Date(record.started_at)
        const end = record.completed_at ? new Date(record.completed_at) : new Date()
        const duration = end.getTime() - start.getTime()
        
        const seconds = Math.floor(duration / 1000)
        const minutes = Math.floor(seconds / 60)
        const hours = Math.floor(minutes / 60)
        
        if (hours > 0) {
          return `${hours}h ${minutes % 60}m`
        } else if (minutes > 0) {
          return `${minutes}m ${seconds % 60}s`
        } else {
          return `${seconds}s`
        }
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record: PipelineExecution) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            size="small"
          >
            查看详情
          </Button>
          
          {record.status === 'running' && (
            <Button
              type="link"
              icon={<StopOutlined />}
              size="small"
              danger
            >
              停止
            </Button>
          )}
          
          {['failed', 'cancelled'].includes(record.status) && (
            <Button
              type="link"
              icon={<RedoOutlined />}
              size="small"
            >
              重试
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <Card
      title="执行记录"
      extra={
        <Button
          icon={<PlayCircleOutlined />}
          onClick={loadExecutions}
          loading={executionsLoading}
        >
          刷新
        </Button>
      }
    >
      <Table
        columns={columns}
        dataSource={executions}
        loading={executionsLoading}
        rowKey="id"
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => 
            `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
        }}
      />
    </Card>
  )
}

export default Executions
