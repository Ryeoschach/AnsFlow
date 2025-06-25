import React, { useState, useEffect } from 'react'
import { 
  Modal, 
  Tabs, 
  Table, 
  Button, 
  Space, 
  Tag, 
  Card, 
  Descriptions,
  Typography,
  message,
  Spin,
  Empty
} from 'antd'
import {
  PlayCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  EyeOutlined,
  DownloadOutlined
} from '@ant-design/icons'
import { ColumnsType } from 'antd/es/table'
import { Tool, JenkinsJob, JenkinsBuild } from '../../types'
import apiService from '../../services/api'
import wsService from '../../services/websocket'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

const { TabPane } = Tabs
const { Text, Paragraph } = Typography

interface JenkinsJobDetailProps {
  tool: Tool
  job: JenkinsJob
  visible: boolean
  onClose: () => void
  onJobUpdate: () => void
}

const JenkinsJobDetail: React.FC<JenkinsJobDetailProps> = ({
  tool,
  job,
  visible,
  onClose,
  onJobUpdate
}) => {
  const [builds, setBuilds] = useState<JenkinsBuild[]>([])
  const [buildsLoading, setBuildsLoading] = useState(false)
  const [selectedBuild, setSelectedBuild] = useState<JenkinsBuild | null>(null)
  const [buildLogs, setBuildLogs] = useState<string>('')
  const [logsLoading, setLogsLoading] = useState(false)
  const [logsVisible, setLogsVisible] = useState(false)

  useEffect(() => {
    if (visible) {
      loadBuilds()
      
      // Subscribe to Jenkins events for this job
      wsService.subscribeToJenkinsJob(tool.id, job.name)
      
      const unsubscribe = wsService.onJenkinsEvent((event) => {
        if (event.toolId === tool.id && event.jobName === job.name) {
          loadBuilds()
        }
      })

      return () => {
        wsService.unsubscribeFromJenkinsJob(tool.id, job.name)
        unsubscribe()
      }
    }
  }, [visible, tool.id, job.name])

  const loadBuilds = async () => {
    setBuildsLoading(true)
    try {
      const buildsData = await apiService.getJenkinsBuilds(tool.id, job.name)
      setBuilds(buildsData)
    } catch (error) {
      console.error('Failed to load builds:', error)
      message.error('加载构建历史失败')
    } finally {
      setBuildsLoading(false)
    }
  }

  const handleBuildJob = async () => {
    try {
      await apiService.buildJenkinsJob(tool.id, job.name)
      message.success('构建已启动')
      loadBuilds()
    } catch (error) {
      console.error('Failed to build job:', error)
      message.error('启动构建失败')
    }
  }

  const handleStopBuild = async (build: JenkinsBuild) => {
    try {
      await apiService.stopJenkinsBuild(tool.id, job.name, build.number)
      message.success('构建已停止')
      loadBuilds()
    } catch (error) {
      console.error('Failed to stop build:', error)
      message.error('停止构建失败')
    }
  }

  const handleViewLogs = async (build: JenkinsBuild) => {
    setLogsLoading(true)
    setLogsVisible(true)
    setSelectedBuild(build)
    
    try {
      const logs = await apiService.getJenkinsBuildLogs(tool.id, job.name, build.number)
      setBuildLogs(logs)
    } catch (error) {
      console.error('Failed to load logs:', error)
      setBuildLogs('加载日志失败')
    } finally {
      setLogsLoading(false)
    }
  }

  const getBuildStatusTag = (build: JenkinsBuild) => {
    switch (build.result) {
      case 'SUCCESS':
        return <Tag color="green">成功</Tag>
      case 'FAILURE':
        return <Tag color="red">失败</Tag>
      case 'UNSTABLE':
        return <Tag color="orange">不稳定</Tag>
      case 'ABORTED':
        return <Tag color="default">已取消</Tag>
      case null:
        return <Tag color="blue">进行中</Tag>
      default:
        return <Tag color="default">未知</Tag>
    }
  }

  const formatDuration = (duration: number) => {
    if (!duration) return '-'
    const seconds = Math.floor(duration / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`
    } else {
      return `${seconds}s`
    }
  }

  const buildColumns: ColumnsType<JenkinsBuild> = [
    {
      title: '构建号',
      dataIndex: 'number',
      key: 'number',
      width: 100,
      render: (number: number) => `#${number}`,
    },
    {
      title: '状态',
      dataIndex: 'result',
      key: 'result',
      width: 100,
      render: (_, record: JenkinsBuild) => getBuildStatusTag(record),
    },
    {
      title: '开始时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 150,
      render: (timestamp: number) => 
        formatDistanceToNow(new Date(timestamp), {
          addSuffix: true,
          locale: zhCN
        }),
    },
    {
      title: '持续时间',
      dataIndex: 'duration',
      key: 'duration',
      width: 120,
      render: (duration: number) => formatDuration(duration),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record: JenkinsBuild) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            size="small"
            onClick={() => handleViewLogs(record)}
          >
            查看日志
          </Button>
          {record.result === null && (
            <Button
              type="link"
              icon={<StopOutlined />}
              size="small"
              danger
              onClick={() => handleStopBuild(record)}
            >
              停止
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <>
      <Modal
        title={`作业详情 - ${job.name}`}
        open={visible}
        onCancel={onClose}
        width={1000}
        footer={[
          <Button key="close" onClick={onClose}>
            关闭
          </Button>,
        ]}
      >
        <Tabs defaultActiveKey="overview">
          <TabPane tab="概览" key="overview">
            <Card>
              <Descriptions title="作业信息" bordered column={2}>
                <Descriptions.Item label="作业名称">{job.name}</Descriptions.Item>
                <Descriptions.Item label="状态">
                  {job.buildable ? (
                    <Tag color="green">已启用</Tag>
                  ) : (
                    <Tag color="red">已禁用</Tag>
                  )}
                </Descriptions.Item>
                <Descriptions.Item label="作业URL">
                  <Text copyable>{job.url}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="最后构建状态">
                  {job.lastBuild ? (
                    <Space>
                      <span>#{job.lastBuild.number}</span>
                      {getBuildStatusTag({ result: job.lastBuild.result } as JenkinsBuild)}
                    </Space>
                  ) : (
                    '无构建记录'
                  )}
                </Descriptions.Item>
                {job.description && (
                  <Descriptions.Item label="描述" span={2}>
                    <Paragraph>{job.description}</Paragraph>
                  </Descriptions.Item>
                )}
              </Descriptions>
              
              <div style={{ marginTop: 16 }}>
                <Space>
                  <Button
                    type="primary"
                    icon={<PlayCircleOutlined />}
                    onClick={handleBuildJob}
                    disabled={!job.buildable}
                  >
                    立即构建
                  </Button>
                  <Button
                    icon={<ReloadOutlined />}
                    onClick={() => {
                      loadBuilds()
                      onJobUpdate()
                    }}
                  >
                    刷新
                  </Button>
                </Space>
              </div>
            </Card>
          </TabPane>
          
          <TabPane tab="构建历史" key="builds">
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={handleBuildJob}
                  disabled={!job.buildable}
                >
                  新建构建
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={loadBuilds}
                  loading={buildsLoading}
                >
                  刷新
                </Button>
              </Space>
            </div>
            
            <Table
              columns={buildColumns}
              dataSource={builds}
              loading={buildsLoading}
              rowKey="number"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => 
                  `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
              }}
              locale={{
                emptyText: builds.length === 0 && !buildsLoading ? 
                  <Empty description="暂无构建记录" /> : undefined
              }}
            />
          </TabPane>
        </Tabs>
      </Modal>

      <Modal
        title={`构建日志 - #${selectedBuild?.number}`}
        open={logsVisible}
        onCancel={() => {
          setLogsVisible(false)
          setSelectedBuild(null)
          setBuildLogs('')
        }}
        width={1200}
        footer={[
          <Button 
            key="download" 
            icon={<DownloadOutlined />}
            onClick={() => {
              const blob = new Blob([buildLogs], { type: 'text/plain' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `${job.name}-${selectedBuild?.number}-logs.txt`
              document.body.appendChild(a)
              a.click()
              document.body.removeChild(a)
              URL.revokeObjectURL(url)
            }}
          >
            下载日志
          </Button>,
          <Button key="close" onClick={() => setLogsVisible(false)}>
            关闭
          </Button>,
        ]}
      >
        <div style={{ height: 500, overflow: 'auto' }}>
          {logsLoading ? (
            <div style={{ textAlign: 'center', padding: 50 }}>
              <Spin size="large" />
              <div style={{ marginTop: 16 }}>加载日志中...</div>
            </div>
          ) : (
            <pre style={{
              background: '#000',
              color: '#fff',
              padding: 16,
              margin: 0,
              fontSize: 12,
              fontFamily: 'Monaco, Menlo, Consolas, monospace',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word'
            }}>
              {buildLogs || '暂无日志内容'}
            </pre>
          )}
        </div>
      </Modal>
    </>
  )
}

export default JenkinsJobDetail
