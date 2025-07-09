import React, { useState, useEffect } from 'react'
import {
  Card, Row, Col, Statistic, Progress, Alert, Table, Typography,
  Space, Tag, Button, Tooltip, Badge, Spin, Empty, message
} from 'antd'
import {
  DatabaseOutlined, CloudServerOutlined, MonitorOutlined,
  ThunderboltOutlined, ReloadOutlined, WarningOutlined,
  CheckCircleOutlined, CloseCircleOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import apiService from '../../services/api'
import { SystemMonitoringData, SystemAlert } from '../../types'

const { Text, Title } = Typography

interface ServiceStatus {
  name: string
  status: 'healthy' | 'unhealthy' | 'warning'
  uptime: number
  version: string
  endpoint: string
  last_check: string
  response_time: number
}

const SystemMonitoring: React.FC = () => {
  const [systemData, setSystemData] = useState<SystemMonitoringData | null>(null)
  const [services, setServices] = useState<ServiceStatus[]>([])
  const [alerts, setAlerts] = useState<SystemAlert[]>([])
  const [loading, setLoading] = useState(false)
  const [healthStatus, setHealthStatus] = useState<any>(null)

  useEffect(() => {
    fetchSystemStatus()
    fetchServices()
    fetchAlerts()
    fetchHealthStatus()
    
    // 设置定时器，每30秒刷新一次
    const interval = setInterval(() => {
      fetchSystemStatus()
      fetchHealthStatus()
    }, 30000)
    
    return () => clearInterval(interval)
  }, [])

  const fetchSystemStatus = async () => {
    try {
      setLoading(true)
      const data = await apiService.getSystemMonitoring()
      setSystemData(data)
    } catch (error) {
      console.error('获取系统状态失败:', error)
      message.error('获取系统状态失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchHealthStatus = async () => {
    try {
      const health = await apiService.getSystemHealth()
      setHealthStatus(health)
    } catch (error) {
      console.error('获取健康状态失败:', error)
    }
  }

  const fetchAlerts = async () => {
    try {
      const response = await apiService.getSystemAlerts({ is_active: true })
      setAlerts(response.results)
    } catch (error) {
      console.error('获取系统告警失败:', error)
    }
  }

  const fetchServices = async () => {
    try {
      // Mock services data - 在实际项目中应该替换为真实的 API 调用
      const mockServices: ServiceStatus[] = [
        {
          name: 'Database',
          status: 'healthy',
          uptime: 99.9,
          version: 'PostgreSQL 13.4',
          endpoint: 'localhost:5432',
          last_check: new Date().toISOString(),
          response_time: 12,
        },
        {
          name: 'Redis Cache',
          status: 'healthy',
          uptime: 99.8,
          version: 'Redis 6.2',
          endpoint: 'localhost:6379',
          last_check: new Date().toISOString(),
          response_time: 3,
        },
        {
          name: 'Message Queue',
          status: 'warning',
          uptime: 97.5,
          version: 'RabbitMQ 3.8',
          endpoint: 'localhost:5672',
          last_check: new Date().toISOString(),
          response_time: 45,
        },
      ]
      setServices(mockServices)
    } catch (error) {
      console.error('获取服务状态失败:', error)
    }
  }

  const getProgressColor = (percentage: number) => {
    if (percentage < 50) return '#52c41a'
    if (percentage < 80) return '#faad14'
    return '#ff4d4f'
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success'
      case 'warning':
        return 'warning'
      case 'unhealthy':
        return 'error'
      default:
        return 'default'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14' }} />
      case 'unhealthy':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      default:
        return null
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const serviceColumns = [
    {
      title: '服务名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: ServiceStatus) => (
        <Space>
          {getStatusIcon(record.status)}
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: '可用性',
      dataIndex: 'uptime',
      key: 'uptime',
      render: (uptime: number) => `${uptime}%`,
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
    },
    {
      title: '响应时间',
      dataIndex: 'response_time',
      key: 'response_time',
      render: (time: number) => `${time}ms`,
    },
    {
      title: '最后检查',
      dataIndex: 'last_check',
      key: 'last_check',
      render: (time: string) => dayjs(time).format('HH:mm:ss'),
    },
  ]

  if (loading && !systemData) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={18}>
          <Text strong style={{ fontSize: 16 }}>
            <MonitorOutlined /> 系统监控
          </Text>
          <br />
          <Text type="secondary">实时监控系统状态和服务健康度</Text>
        </Col>
        <Col span={6} style={{ textAlign: 'right' }}>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              fetchSystemStatus()
              fetchServices()
              fetchAlerts()
              fetchHealthStatus()
            }}
          >
            刷新
          </Button>
        </Col>
      </Row>

      {/* 活跃告警 */}
      {alerts.length > 0 && (
        <Alert
          message="系统告警"
          description={
            <div>
              {alerts.slice(0, 3).map(alert => (
                <div key={alert.id}>
                  <Tag color={alert.alert_type === 'error' ? 'error' : alert.alert_type === 'warning' ? 'warning' : 'info'}>
                    {alert.alert_type.toUpperCase()}
                  </Tag>
                  {alert.message}
                  <Text type="secondary" style={{ marginLeft: 8 }}>
                    {dayjs(alert.created_at).format('MM-DD HH:mm')}
                  </Text>
                </div>
              ))}
              {alerts.length > 3 && (
                <Text type="secondary">还有 {alerts.length - 3} 条告警...</Text>
              )}
            </div>
          }
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 系统概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="CPU 使用率"
              value={systemData?.performance_metrics?.cpu_usage || 0}
              precision={1}
              suffix="%"
              prefix={<ThunderboltOutlined />}
            />
            <Progress 
              percent={systemData?.performance_metrics?.cpu_usage || 0} 
              strokeColor={getProgressColor(systemData?.performance_metrics?.cpu_usage || 0)}
              showInfo={false}
              size="small"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="内存使用率"
              value={systemData?.performance_metrics?.memory_usage || 0}
              precision={1}
              suffix="%"
              prefix={<DatabaseOutlined />}
            />
            <Progress 
              percent={systemData?.performance_metrics?.memory_usage || 0} 
              strokeColor={getProgressColor(systemData?.performance_metrics?.memory_usage || 0)}
              showInfo={false}
              size="small"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="磁盘使用率"
              value={systemData?.performance_metrics?.disk_usage || 0}
              precision={1}
              suffix="%"
              prefix={<CloudServerOutlined />}
            />
            <Progress 
              percent={systemData?.performance_metrics?.disk_usage || 0} 
              strokeColor={getProgressColor(systemData?.performance_metrics?.disk_usage || 0)}
              showInfo={false}
              size="small"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={systemData?.application_metrics?.active_users || 0}
              prefix={<MonitorOutlined />}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              活跃流水线: {systemData?.application_metrics?.active_pipelines || 0}
            </Text>
          </Card>
        </Col>
      </Row>

      {/* 网络 I/O */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card title="网络 I/O" size="small">
            <Row>
              <Col span={12}>
                <Statistic
                  title="发送"
                  value={formatBytes(systemData?.performance_metrics?.network_io?.bytes_sent || 0)}
                  valueStyle={{ fontSize: 14 }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="接收"
                  value={formatBytes(systemData?.performance_metrics?.network_io?.bytes_recv || 0)}
                  valueStyle={{ fontSize: 14 }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="数据库状态" size="small">
            <Row>
              <Col span={12}>
                <Statistic
                  title="连接数"
                  value={systemData?.database_metrics?.connection_count || 0}
                  valueStyle={{ fontSize: 14 }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="活跃查询"
                  value={systemData?.database_metrics?.active_queries || 0}
                  valueStyle={{ fontSize: 14 }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* 服务状态 */}
      <Card title="服务状态" style={{ marginBottom: 16 }}>
        <Table
          columns={serviceColumns}
          dataSource={services}
          rowKey="name"
          pagination={false}
          size="small"
        />
      </Card>

      {/* 系统信息 */}
      <Card title="系统信息" size="small">
        <Row gutter={[16, 16]}>
          <Col span={6}>
            <Text strong>主机名:</Text>
            <br />
            <Text>{systemData?.system_info?.hostname || 'Unknown'}</Text>
          </Col>
          <Col span={6}>
            <Text strong>操作系统:</Text>
            <br />
            <Text>{systemData?.system_info?.platform || 'Unknown'}</Text>
          </Col>
          <Col span={6}>
            <Text strong>CPU 核心数:</Text>
            <br />
            <Text>{systemData?.system_info?.cpu_count || 0}</Text>
          </Col>
          <Col span={6}>
            <Text strong>内存总量:</Text>
            <br />
            <Text>{formatBytes(systemData?.system_info?.memory_total || 0)}</Text>
          </Col>
        </Row>
        <Row style={{ marginTop: 16 }}>
          <Col span={24}>
            <Text strong>健康检查:</Text>
            <br />
            {healthStatus?.checks?.map((check: any, index: number) => (
              <Tag key={index} color={check.status === 'pass' ? 'success' : check.status === 'warn' ? 'warning' : 'error'}>
                {check.name}: {check.status}
              </Tag>
            ))}
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default SystemMonitoring
