import React, { useState, useEffect } from 'react'
import {
  Card, Table, Space, Input, Select, DatePicker, Tag,
  Typography, Row, Col, Button, Tooltip, Badge, Modal, message
} from 'antd'
import {
  AuditOutlined, SearchOutlined, DownloadOutlined,
  InfoCircleOutlined, ExclamationCircleOutlined, CheckCircleOutlined
} from '@ant-design/icons'
import { RangePickerProps } from 'antd/es/date-picker'
import dayjs from 'dayjs'
import apiService from '../../services/api'
import { AuditLog } from '../../types'

const { Text } = Typography
const { RangePicker } = DatePicker
const { Option } = Select

const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    search: '',
    action: '',
    result: '',
    dateRange: null as [dayjs.Dayjs, dayjs.Dayjs] | null,
  })
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  })
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null)

  useEffect(() => {
    fetchLogs()
  }, [filters])

  const fetchLogs = async (page: number = 1, pageSize: number = 10) => {
    try {
      setLoading(true)
      const params: any = {
        page,
        page_size: pageSize,
      }
      
      if (filters.search) {
        params.search = filters.search
      }
      if (filters.action) {
        params.action = filters.action
      }
      if (filters.dateRange) {
        params.start_date = filters.dateRange[0].format('YYYY-MM-DD')
        params.end_date = filters.dateRange[1].format('YYYY-MM-DD')
      }

      const response = await apiService.getAuditLogs(params)
      setLogs(response.results)
      setPagination({
        current: page,
        pageSize,
        total: response.count,
      })
    } catch (error) {
      console.error('Failed to fetch audit logs:', error)
      message.error('获取审计日志失败')
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async () => {
    try {
      const params: any = {}
      
      if (filters.search) {
        params.search = filters.search
      }
      if (filters.action) {
        params.action = filters.action
      }
      if (filters.dateRange) {
        params.start_date = filters.dateRange[0].format('YYYY-MM-DD')
        params.end_date = filters.dateRange[1].format('YYYY-MM-DD')
      }

      const blob = await apiService.exportAuditLogs({ ...params, format: 'excel' })
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `audit_logs_${dayjs().format('YYYY-MM-DD')}.xlsx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      message.success('导出成功')
    } catch (error) {
      console.error('Export failed:', error)
      message.error('导出失败')
    }
  }

  const showLogDetail = (log: AuditLog) => {
    setSelectedLog(log)
    setDetailModalVisible(true)
  }

  const getResultIcon = (result: string) => {
    switch (result) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'failure':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'warning':
        return <InfoCircleOutlined style={{ color: '#faad14' }} />
      default:
        return null
    }
  }

  const getResultColor = (result: string) => {
    switch (result) {
      case 'success':
        return 'success'
      case 'failure':
        return 'error'
      case 'warning':
        return 'warning'
      default:
        return 'default'
    }
  }

  const columns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
      sorter: true,
      width: 180,
    },
    {
      title: '用户',
      dataIndex: 'user',
      key: 'user',
      width: 120,
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      width: 150,
      render: (action: string) => (
        <Tag color="blue">{action.replace(/_/g, ' ')}</Tag>
      ),
    },
    {
      title: '资源',
      key: 'resource',
      width: 150,
      render: (log: AuditLog) => (
        <Space direction="vertical" size={0}>
          <Text strong>{log.resource_type}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            ID: {log.resource_id}
          </Text>
        </Space>
      ),
    },
    {
      title: '结果',
      dataIndex: 'result',
      key: 'result',
      width: 100,
      render: (result: string | undefined) => {
        if (!result) return <Tag color="default">未知</Tag>
        return (
          <Space>
            {getResultIcon(result)}
            <Tag color={getResultColor(result)}>
              {result.toUpperCase()}
            </Tag>
          </Space>
        )
      },
    },
    {
      title: 'IP地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 120,
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (log: AuditLog) => (
        <Button
          type="link"
          size="small"
          icon={<InfoCircleOutlined />}
          onClick={() => showLogDetail(log)}
        >
          详情
        </Button>
      ),
    },
  ]

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={18}>
          <Text strong style={{ fontSize: 16 }}>
            <AuditOutlined /> 审计日志
          </Text>
          <br />
          <Text type="secondary">查看系统操作日志和访问记录</Text>
        </Col>
        <Col span={6} style={{ textAlign: 'right' }}>
          <Button
            icon={<DownloadOutlined />}
            onClick={handleExport}
          >
            导出日志
          </Button>
        </Col>
      </Row>

      <Card>
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Input
              placeholder="搜索操作或资源"
              prefix={<SearchOutlined />}
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="操作类型"
              style={{ width: '100%' }}
              value={filters.action || undefined}
              onChange={(value) => setFilters({ ...filters, action: value })}
              allowClear
            >
              <Option value="CREATE">创建</Option>
              <Option value="UPDATE">更新</Option>
              <Option value="DELETE">删除</Option>
              <Option value="LOGIN">登录</Option>
              <Option value="LOGOUT">登出</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="结果状态"
              style={{ width: '100%' }}
              value={filters.result || undefined}
              onChange={(value) => setFilters({ ...filters, result: value })}
              allowClear
            >
              <Option value="success">成功</Option>
              <Option value="failure">失败</Option>
              <Option value="warning">警告</Option>
            </Select>
          </Col>
          <Col span={6}>
            <RangePicker
              style={{ width: '100%' }}
              value={filters.dateRange}
              onChange={(dates) => setFilters({ ...filters, dateRange: dates as [dayjs.Dayjs, dayjs.Dayjs] | null })}
              showTime
            />
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
            onChange: (page, pageSize) => {
              fetchLogs(page, pageSize)
            },
          }}
          scroll={{ y: 400 }}
        />
      </Card>

      <Modal
        title="审计日志详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={600}
      >
        {selectedLog && (
          <div>
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Text strong>操作时间:</Text>
              </Col>
              <Col span={16}>
                <Text>{dayjs(selectedLog.timestamp).format('YYYY-MM-DD HH:mm:ss')}</Text>
              </Col>
            </Row>
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Text strong>操作用户:</Text>
              </Col>
              <Col span={16}>
                <Text>{selectedLog.user}</Text>
              </Col>
            </Row>
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Text strong>操作类型:</Text>
              </Col>
              <Col span={16}>
                <Tag color="blue">{selectedLog.action.replace(/_/g, ' ')}</Tag>
              </Col>
            </Row>
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Text strong>资源类型:</Text>
              </Col>
              <Col span={16}>
                <Text>{selectedLog.resource_type}</Text>
              </Col>
            </Row>
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Text strong>资源ID:</Text>
              </Col>
              <Col span={16}>
                <Text>{selectedLog.resource_id}</Text>
              </Col>
            </Row>
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Text strong>操作结果:</Text>
              </Col>
              <Col span={16}>
                {selectedLog.result ? (
                  <Space>
                    {getResultIcon(selectedLog.result)}
                    <Tag color={getResultColor(selectedLog.result)}>
                      {selectedLog.result.toUpperCase()}
                    </Tag>
                  </Space>
                ) : (
                  <Tag color="default">未知</Tag>
                )}
              </Col>
            </Row>
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Text strong>IP地址:</Text>
              </Col>
              <Col span={16}>
                <Text>{selectedLog.ip_address}</Text>
              </Col>
            </Row>
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Text strong>用户代理:</Text>
              </Col>
              <Col span={16}>
                <Tooltip title={selectedLog.user_agent}>
                  <Text ellipsis style={{ maxWidth: 300 }}>
                    {selectedLog.user_agent}
                  </Text>
                </Tooltip>
              </Col>
            </Row>
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Text strong>详细信息:</Text>
              </Col>
              <Col span={16}>
                <pre style={{ fontSize: 12, background: '#f5f5f5', padding: 8 }}>
                  {JSON.stringify(selectedLog.details, null, 2)}
                </pre>
              </Col>
            </Row>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default AuditLogs
