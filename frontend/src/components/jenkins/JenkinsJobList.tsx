import React, { useState, useEffect } from 'react'
import { 
  Table, 
  Button, 
  Space, 
  Tag, 
  Modal, 
  message, 
  Tooltip,
  Input,
  Select,
  Card,
  Row,
  Col,
  Statistic,
  Badge
} from 'antd'
import {
  PlayCircleOutlined,
  StopOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
  PoweroffOutlined,
  CheckCircleOutlined,
  SearchOutlined,
  FilterOutlined
} from '@ant-design/icons'
import { ColumnsType } from 'antd/es/table'
import { JenkinsJob, Tool } from '../../types'
import apiService from '../../services/api'
import wsService from '../../services/websocket'
import { useAppStore } from '../../stores/app'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import JenkinsJobForm from './JenkinsJobForm'
import JenkinsJobDetail from './JenkinsJobDetail'

const { Search } = Input
const { Option } = Select

interface JenkinsJobListProps {
  tool: Tool
}

const JenkinsJobList: React.FC<JenkinsJobListProps> = ({ tool }) => {
  const [jobs, setJobs] = useState<JenkinsJob[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedJob, setSelectedJob] = useState<JenkinsJob | null>(null)
  const [formVisible, setFormVisible] = useState(false)
  const [detailVisible, setDetailVisible] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const { addNotification } = useAppStore()

  useEffect(() => {
    loadJobs()
  }, [tool.id])

  useEffect(() => {
    // Subscribe to Jenkins events for this tool
    const unsubscribe = wsService.onJenkinsEvent((event) => {
      if (event.toolId === tool.id) {
        // Refresh jobs when there's an event
        loadJobs()
        
        // Show notification
        const eventMessages = {
          job_started: '作业已启动',
          job_completed: '作业已完成',
          job_failed: '作业执行失败',
          build_started: '构建已开始',
          build_completed: '构建已完成'
        }
        
        addNotification({
          level: event.event.includes('failed') ? 'error' : 'info',
          title: `Jenkins ${eventMessages[event.event]}`,
          message: `作业 ${event.jobName} ${eventMessages[event.event]}`
        })
      }
    })

    return unsubscribe
  }, [tool.id, addNotification])

  const loadJobs = async () => {
    setLoading(true)
    try {
      const jobsData = await apiService.getJenkinsJobs(tool.id)
      setJobs(jobsData)
    } catch (error) {
      console.error('Failed to load Jenkins jobs:', error)
      addNotification({
        level: 'error',
        title: '加载Jenkins作业失败',
        message: '无法获取Jenkins作业列表，请检查连接'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleBuildJob = async (job: JenkinsJob) => {
    try {
      await apiService.buildJenkinsJob(tool.id, job.name)
      message.success(`作业 ${job.name} 构建已启动`)
      loadJobs()
    } catch (error) {
      console.error('Failed to build job:', error)
      message.error('启动构建失败')
    }
  }

  const handleToggleJob = async (job: JenkinsJob) => {
    try {
      if (job.buildable) {
        await apiService.disableJenkinsJob(tool.id, job.name)
        message.success(`作业 ${job.name} 已禁用`)
      } else {
        await apiService.enableJenkinsJob(tool.id, job.name)
        message.success(`作业 ${job.name} 已启用`)
      }
      loadJobs()
    } catch (error) {
      console.error('Failed to toggle job:', error)
      message.error('操作失败')
    }
  }

  const handleDeleteJob = async (job: JenkinsJob) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除作业 "${job.name}" 吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await apiService.deleteJenkinsJob(tool.id, job.name)
          message.success(`作业 ${job.name} 已删除`)
          loadJobs()
        } catch (error) {
          console.error('Failed to delete job:', error)
          message.error('删除失败')
        }
      }
    })
  }

  const getStatusTag = (job: JenkinsJob) => {
    if (!job.buildable) {
      return <Tag color="red">已禁用</Tag>
    }
    
    switch (job.color) {
      case 'blue':
        return <Tag color="green">成功</Tag>
      case 'red':
        return <Tag color="red">失败</Tag>
      case 'yellow':
        return <Tag color="orange">不稳定</Tag>
      case 'grey':
        return <Tag color="default">未构建</Tag>
      case 'blue_anime':
        return <Tag color="blue">构建中</Tag>
      case 'red_anime':
        return <Tag color="red">构建中</Tag>
      default:
        return <Tag color="default">未知</Tag>
    }
  }

  const filteredJobs = jobs.filter(job => {
    const matchesSearch = job.name.toLowerCase().includes(searchText.toLowerCase())
    const matchesStatus = !statusFilter || 
      (statusFilter === 'enabled' && job.buildable) ||
      (statusFilter === 'disabled' && !job.buildable) ||
      (statusFilter === 'success' && job.color === 'blue') ||
      (statusFilter === 'failed' && job.color === 'red') ||
      (statusFilter === 'building' && job.color.includes('anime'))
    
    return matchesSearch && matchesStatus
  })

  const columns: ColumnsType<JenkinsJob> = [
    {
      title: '作业名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: JenkinsJob) => (
        <Button 
          type="link" 
          onClick={() => {
            setSelectedJob(record)
            setDetailVisible(true)
          }}
        >
          {name}
        </Button>
      ),
    },
    {
      title: '状态',
      dataIndex: 'color',
      key: 'status',
      render: (_, record: JenkinsJob) => getStatusTag(record),
    },
    {
      title: '最后构建',
      dataIndex: 'lastBuild',
      key: 'lastBuild',
      render: (lastBuild: any) => {
        if (!lastBuild) return '-'
        return (
          <div>
            <div>#{lastBuild.number}</div>
            <div style={{ fontSize: 12, color: '#666' }}>
              {formatDistanceToNow(new Date(lastBuild.timestamp), {
                addSuffix: true,
                locale: zhCN
              })}
            </div>
          </div>
        )
      },
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: JenkinsJob) => (
        <Space>
          <Tooltip title="构建">
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              size="small"
              disabled={!record.buildable}
              onClick={() => handleBuildJob(record)}
            />
          </Tooltip>
          
          <Tooltip title={record.buildable ? '禁用' : '启用'}>
            <Button
              icon={record.buildable ? <PoweroffOutlined /> : <CheckCircleOutlined />}
              size="small"
              onClick={() => handleToggleJob(record)}
            />
          </Tooltip>
          
          <Tooltip title="编辑">
            <Button
              icon={<EditOutlined />}
              size="small"
              onClick={() => {
                setSelectedJob(record)
                setFormVisible(true)
              }}
            />
          </Tooltip>
          
          <Tooltip title="删除">
            <Button
              danger
              icon={<DeleteOutlined />}
              size="small"
              onClick={() => handleDeleteJob(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  const getStatsData = () => {
    const total = jobs.length
    const enabled = jobs.filter(j => j.buildable).length
    const success = jobs.filter(j => j.color === 'blue').length
    const failed = jobs.filter(j => j.color === 'red').length
    const building = jobs.filter(j => j.color.includes('anime')).length

    return { total, enabled, success, failed, building }
  }

  const stats = getStatsData()

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={5}>
            <Statistic title="总作业数" value={stats.total} />
          </Col>
          <Col span={5}>
            <Statistic 
              title="已启用" 
              value={stats.enabled} 
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col span={4}>
            <Statistic 
              title="成功" 
              value={stats.success} 
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col span={4}>
            <Statistic 
              title="失败" 
              value={stats.failed} 
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Col>
          <Col span={6}>
            <Badge count={stats.building} offset={[10, 0]}>
              <Statistic 
                title="构建中" 
                value={stats.building}
                valueStyle={{ color: '#faad14' }}
              />
            </Badge>
          </Col>
        </Row>
      </Card>

      <Card
        title={`Jenkins 作业 - ${tool.name}`}
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setSelectedJob(null)
                setFormVisible(true)
              }}
            >
              新建作业
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadJobs}
              loading={loading}
            >
              刷新
            </Button>
          </Space>
        }
      >
        <Space style={{ marginBottom: 16 }}>
          <Search
            placeholder="搜索作业名称"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
            prefix={<SearchOutlined />}
          />
          
          <Select
            placeholder="筛选状态"
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 120 }}
            allowClear
            suffixIcon={<FilterOutlined />}
          >
            <Option value="enabled">已启用</Option>
            <Option value="disabled">已禁用</Option>
            <Option value="success">成功</Option>
            <Option value="failed">失败</Option>
            <Option value="building">构建中</Option>
          </Select>
        </Space>

        <Table
          columns={columns}
          dataSource={filteredJobs}
          loading={loading}
          rowKey="name"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }}
        />
      </Card>

      {formVisible && (
        <JenkinsJobForm
          tool={tool}
          job={selectedJob}
          visible={formVisible}
          onCancel={() => {
            setFormVisible(false)
            setSelectedJob(null)
          }}
          onSuccess={() => {
            setFormVisible(false)
            setSelectedJob(null)
            loadJobs()
          }}
        />
      )}

      {detailVisible && selectedJob && (
        <JenkinsJobDetail
          tool={tool}
          job={selectedJob}
          visible={detailVisible}
          onClose={() => {
            setDetailVisible(false)
            setSelectedJob(null)
          }}
          onJobUpdate={loadJobs}
        />
      )}
    </div>
  )
}

export default JenkinsJobList
