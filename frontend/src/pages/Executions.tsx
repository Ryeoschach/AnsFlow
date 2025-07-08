import React, { useEffect, useState } from 'react'
import { 
  Card, 
  Table, 
  Space, 
  Button, 
  Tag, 
  Progress, 
  Input,
  Select,
  DatePicker,
  Statistic,
  Row,
  Col,
  Typography,
  Dropdown,
  message
} from 'antd'
import type { Dayjs } from 'dayjs'
import { 
  PlayCircleOutlined,
  StopOutlined,
  RedoOutlined,
  EyeOutlined,
  SearchOutlined,
  FilterOutlined,
  DownloadOutlined,
  ReloadOutlined,
  BarChartOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  MoreOutlined
} from '@ant-design/icons'
import { ColumnsType } from 'antd/es/table'
import { PipelineExecution } from '../types'
import { useAppStore } from '../stores/app'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { useNavigate } from 'react-router-dom'

const { Title, Text } = Typography
const { Search } = Input
const { RangePicker } = DatePicker

const Executions: React.FC = () => {
  const navigate = useNavigate()
  const { executions, executionsLoading, loadExecutions } = useAppStore()
  
  // 新增状态管理
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined)
  const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null)

  useEffect(() => {
    loadExecutions()
  }, [loadExecutions])

  // 统计数据计算
  const getStatistics = () => {
    const total = executions.length
    const success = executions.filter(e => e.status === 'success').length
    const failed = executions.filter(e => e.status === 'failed').length
    const running = executions.filter(e => e.status === 'running').length
    const pending = executions.filter(e => e.status === 'pending').length
    
    return { total, success, failed, running, pending }
  }

  const statistics = getStatistics()

  // 过滤后的数据
  const filteredExecutions = executions.filter(execution => {
    // 搜索过滤
    if (searchText && !execution.pipeline_name?.toLowerCase().includes(searchText.toLowerCase())) {
      return false
    }
    
    // 状态过滤
    if (statusFilter && execution.status !== statusFilter) {
      return false
    }
    
    // 日期范围过滤
    if (dateRange && dateRange[0] && dateRange[1] && execution.started_at) {
      const executionDate = new Date(execution.started_at)
      const startDate = dateRange[0].toDate()
      const endDate = dateRange[1].toDate()
      if (executionDate < startDate || executionDate > endDate) {
        return false
      }
    }
    
    return true
  })

  const getStatusTag = (status: string) => {
    const statusConfig = {
      success: { 
        color: 'green', 
        text: '成功',
        icon: <CheckCircleOutlined />,
        bgColor: '#f6ffed',
        borderColor: '#b7eb8f'
      },
      failed: { 
        color: 'red', 
        text: '失败',
        icon: <CloseCircleOutlined />,
        bgColor: '#fff2f0',
        borderColor: '#ffccc7'
      },
      running: { 
        color: 'blue', 
        text: '运行中',
        icon: <SyncOutlined spin />,
        bgColor: '#f0f5ff',
        borderColor: '#adc6ff'
      },
      pending: { 
        color: 'orange', 
        text: '等待中',
        icon: <ClockCircleOutlined />,
        bgColor: '#fff7e6',
        borderColor: '#ffd591'
      },
      cancelled: { 
        color: 'default', 
        text: '已取消',
        icon: <StopOutlined />,
        bgColor: '#fafafa',
        borderColor: '#d9d9d9'
      }
    }
    
    const config = statusConfig[status as keyof typeof statusConfig] || 
                  { color: 'default', text: status, icon: null, bgColor: '#fafafa', borderColor: '#d9d9d9' }
    
    return (
      <Tag 
        color={config.color}
        style={{
          background: config.bgColor,
          borderColor: config.borderColor,
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '4px 8px',
          borderRadius: '6px'
        }}
      >
        {config.icon}
        {config.text}
      </Tag>
    )
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
            onClick={() => navigate(`/executions/${record.id}`)}
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
    <div style={{ padding: '24px' }}>
      {/* 头部统计卡片 */}
      <Card style={{
        borderRadius: '12px',
        padding: '8px',
        marginBottom: '24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px'
        }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              执行记录
            </Title>
            <Text style={{ color: 'rgba(0,0,0,0.6)', fontSize: '14px' }}>
              流水线执行历史和状态监控
            </Text>
          </div>
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={() => loadExecutions()}
            loading={executionsLoading}
          >
            刷新数据
          </Button>
        </div>

        {/* 统计数据 */}
        <Row gutter={[16, 16]}>
          <Col xs={12} sm={12} md={8} lg={5} xl={5}>
            <div style={{
              background: '#fafafa',
              borderRadius: '8px',
              padding: '16px',
              textAlign: 'center',
              border: '1px solid #f0f0f0'
            }}>
              <Statistic
                title="总执行次数"
                value={statistics.total}
                valueStyle={{ fontSize: '24px' }}
                prefix={<BarChartOutlined />}
              />
            </div>
          </Col>
          <Col xs={12} sm={12} md={8} lg={5} xl={5}>
            <div style={{
              background: '#f6ffed',
              borderRadius: '8px',
              padding: '16px',
              textAlign: 'center',
              border: '1px solid #b7eb8f'
            }}>
              <Statistic
                title="成功"
                value={statistics.success}
                valueStyle={{ color: '#52c41a', fontSize: '24px' }}
                prefix={<CheckCircleOutlined />}
              />
            </div>
          </Col>
          <Col xs={12} sm={12} md={8} lg={5} xl={5}>
            <div style={{
              background: '#fff2f0',
              borderRadius: '8px',
              padding: '16px',
              textAlign: 'center',
              border: '1px solid #ffccc7'
            }}>
              <Statistic
                title="失败"
                value={statistics.failed}
                valueStyle={{ color: '#ff4d4f', fontSize: '24px' }}
                prefix={<CloseCircleOutlined />}
              />
            </div>
          </Col>
          <Col xs={12} sm={12} md={8} lg={5} xl={5}>
            <div style={{
              background: '#f0f5ff',
              borderRadius: '8px',
              padding: '16px',
              textAlign: 'center',
              border: '1px solid #adc6ff'
            }}>
              <Statistic
                title="运行中"
                value={statistics.running}
                valueStyle={{ color: '#1890ff', fontSize: '24px' }}
                prefix={<SyncOutlined spin />}
              />
            </div>
          </Col>
          <Col xs={12} sm={12} md={8} lg={4} xl={4}>
            <div style={{
              background: '#fff7e6',
              borderRadius: '8px',
              padding: '16px',
              textAlign: 'center',
              border: '1px solid #ffd591'
            }}>
              <Statistic
                title="等待中"
                value={statistics.pending}
                valueStyle={{ color: '#faad14', fontSize: '24px' }}
                prefix={<ClockCircleOutlined />}
              />
            </div>
          </Col>
        </Row>
      </Card>

      {/* 过滤和搜索区域 */}
      <Card style={{ marginBottom: '16px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8} md={6}>
            <Search
              placeholder="搜索流水线名称"
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="选择状态"
              allowClear
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: '100%' }}
              options={[
                { label: '成功', value: 'success' },
                { label: '失败', value: 'failed' },
                { label: '运行中', value: 'running' },
                { label: '等待中', value: 'pending' },
                { label: '已取消', value: 'cancelled' }
              ]}
            />
          </Col>
          <Col xs={12} sm={10} md={8}>
            <RangePicker
              placeholder={['开始时间', '结束时间']}
              value={dateRange}
              onChange={setDateRange}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={24} md={6}>
            <Space>
              <Button
                icon={<FilterOutlined />}
                onClick={() => {
                  setSearchText('')
                  setStatusFilter(undefined)
                  setDateRange(null)
                }}
              >
                清空筛选
              </Button>
              <Button
                icon={<DownloadOutlined />}
                onClick={() => message.info('导出功能开发中')}
              >
                导出
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 主要表格区域 */}
      <Card
        style={{
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}
      >
        <Table
          columns={columns}
          dataSource={filteredExecutions}
          loading={executionsLoading}
          rowKey="id"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }}
          scroll={{ x: 1200 }}
        />
      </Card>
    </div>
  )
}

export default Executions
