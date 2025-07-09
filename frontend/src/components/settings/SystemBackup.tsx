import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  message,
  Space,
  Tag,
  Popconfirm,
  Typography,
  Row,
  Col,
  Statistic,
  Progress,
  Upload,
  Alert,
  DatePicker,
  Switch
} from 'antd'
import {
  PlusOutlined,
  DownloadOutlined,
  DeleteOutlined,
  ReloadOutlined,
  CloudUploadOutlined,
  DatabaseOutlined,
  FileZipOutlined,
  HistoryOutlined,
  ScheduleOutlined,
  UploadOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { apiService } from '../../services/api'
import { BackupRecord, BackupSchedule } from '../../types'

const { TextArea } = Input
const { Text, Title } = Typography
const { RangePicker } = DatePicker

interface SystemBackupProps {}

const SystemBackup: React.FC<SystemBackupProps> = () => {
  const [backupRecords, setBackupRecords] = useState<BackupRecord[]>([])
  const [backupSchedules, setBackupSchedules] = useState<BackupSchedule[]>([])
  const [loading, setLoading] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [scheduleModalVisible, setScheduleModalVisible] = useState(false)
  const [currentRecord, setCurrentRecord] = useState<BackupRecord | null>(null)
  const [currentSchedule, setCurrentSchedule] = useState<BackupSchedule | null>(null)
  const [form] = Form.useForm()
  const [scheduleForm] = Form.useForm()

  // 加载备份记录
  const fetchBackupRecords = async () => {
    setLoading(true)
    try {
      const response = await apiService.getBackupRecords()
      setBackupRecords(response.results || response)
    } catch (error) {
      message.error('加载备份记录失败')
      console.error('Failed to fetch backup records:', error)
    } finally {
      setLoading(false)
    }
  }

  // 加载备份计划
  const fetchBackupSchedules = async () => {
    try {
      const response = await apiService.getBackupSchedules()
      setBackupSchedules(response.results || response)
    } catch (error) {
      message.error('加载备份计划失败')
      console.error('Failed to fetch backup schedules:', error)
    }
  }

  useEffect(() => {
    fetchBackupRecords()
    fetchBackupSchedules()
  }, [])

  // 创建备份
  const handleCreateBackup = async (values: any) => {
    try {
      await apiService.createBackup(values)
      message.success('备份创建成功')
      setCreateModalVisible(false)
      form.resetFields()
      fetchBackupRecords()
    } catch (error) {
      message.error('创建备份失败')
      console.error('Failed to create backup:', error)
    }
  }

  // 下载备份
  const handleDownload = async (record: BackupRecord) => {
    try {
      const blob = await apiService.downloadBackup(record.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = record.filename || `backup_${record.id}.zip`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      message.success('下载开始')
    } catch (error) {
      message.error('下载失败')
      console.error('Failed to download backup:', error)
    }
  }

  // 删除备份
  const handleDelete = async (id: number) => {
    try {
      await apiService.deleteBackupRecord(id)
      message.success('删除成功')
      fetchBackupRecords()
    } catch (error) {
      message.error('删除失败')
      console.error('Failed to delete backup:', error)
    }
  }

  // 创建备份计划
  const handleCreateSchedule = async (values: any) => {
    try {
      await apiService.createBackupSchedule(values)
      message.success('备份计划创建成功')
      setScheduleModalVisible(false)
      scheduleForm.resetFields()
      fetchBackupSchedules()
    } catch (error) {
      message.error('创建备份计划失败')
      console.error('Failed to create backup schedule:', error)
    }
  }

  // 删除备份计划
  const handleDeleteSchedule = async (id: number) => {
    try {
      await apiService.deleteBackupSchedule(id)
      message.success('删除成功')
      fetchBackupSchedules()
    } catch (error) {
      message.error('删除失败')
      console.error('Failed to delete backup schedule:', error)
    }
  }

  // 备份记录表格列
  const backupColumns: ColumnsType<BackupRecord> = [
    {
      title: '备份名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '类型',
      dataIndex: 'backup_type',
      key: 'backup_type',
      render: (type) => {
        const typeMap = {
          'full': { color: 'blue', text: '完整备份' },
          'incremental': { color: 'green', text: '增量备份' },
          'differential': { color: 'orange', text: '差异备份' }
        }
        const config = typeMap[type as keyof typeof typeMap] || { color: 'default', text: type }
        return <Tag color={config.color}>{config.text}</Tag>
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const statusMap = {
          'pending': { color: 'processing', text: '等待中' },
          'running': { color: 'processing', text: '进行中' },
          'completed': { color: 'success', text: '已完成' },
          'failed': { color: 'error', text: '失败' }
        }
        const config = statusMap[status as keyof typeof statusMap] || { color: 'default', text: status }
        return <Tag color={config.color}>{config.text}</Tag>
      }
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (size) => size ? `${(size / 1024 / 1024).toFixed(2)} MB` : '--'
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress) => {
        if (progress === undefined || progress === null) return '--'
        return <Progress percent={progress} size="small" />
      }
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleString()
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          {record.status === 'completed' && (
            <Button
              type="link"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(record)}
              size="small"
            >
              下载
            </Button>
          )}
          <Popconfirm
            title="确定要删除这个备份吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="删除"
            cancelText="取消"
          >
            <Button
              type="link"
              icon={<DeleteOutlined />}
              danger
              size="small"
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  // 备份计划表格列
  const scheduleColumns: ColumnsType<BackupSchedule> = [
    {
      title: '计划名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Cron 表达式',
      dataIndex: 'cron_expression',
      key: 'cron_expression',
      render: (cron) => <Text code>{cron}</Text>
    },
    {
      title: '备份类型',
      dataIndex: 'backup_type',
      key: 'backup_type',
      render: (type) => {
        const typeMap = {
          'full': { color: 'blue', text: '完整备份' },
          'incremental': { color: 'green', text: '增量备份' },
          'differential': { color: 'orange', text: '差异备份' }
        }
        const config = typeMap[type as keyof typeof typeMap] || { color: 'default', text: type }
        return <Tag color={config.color}>{config.text}</Tag>
      }
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (_, record) => (
        <Tag color={(record.status === 'active' || record.is_active) ? 'green' : 'red'}>
          {(record.status === 'active' || record.is_active) ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '下次执行',
      dataIndex: 'next_run_at',
      key: 'next_run_at',
      render: (time, record) => {
        const nextTime = time || record.next_run_time
        return nextTime ? new Date(nextTime).toLocaleString() : '--'
      }
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Popconfirm
            title="确定要删除这个备份计划吗？"
            onConfirm={() => handleDeleteSchedule(record.id)}
            okText="删除"
            cancelText="取消"
          >
            <Button
              type="link"
              icon={<DeleteOutlined />}
              danger
              size="small"
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  // 统计数据
  const stats = {
    totalBackups: backupRecords.length,
    completedBackups: backupRecords.filter(r => r.status === 'completed').length,
    totalSize: backupRecords
      .filter(r => r.file_size)
      .reduce((sum, r) => sum + (r.file_size || 0), 0),
    activeSchedules: backupSchedules.filter(s => s.status === 'active' || s.is_active).length
  }

  return (
    <div>
      <Title level={4}>系统备份</Title>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总备份数"
              value={stats.totalBackups}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已完成"
              value={stats.completedBackups}
              prefix={<FileZipOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总大小"
              value={`${(stats.totalSize / 1024 / 1024).toFixed(2)} MB`}
              prefix={<CloudUploadOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃计划"
              value={stats.activeSchedules}
              prefix={<ScheduleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 备份记录表格 */}
      <Card
        title="备份记录"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={fetchBackupRecords}>
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setCreateModalVisible(true)}
            >
              创建备份
            </Button>
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        <Table
          columns={backupColumns}
          dataSource={backupRecords}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>

      {/* 备份计划表格 */}
      <Card
        title="备份计划"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={fetchBackupSchedules}>
              刷新
            </Button>
            <Button
              type="primary"
              icon={<ScheduleOutlined />}
              onClick={() => setScheduleModalVisible(true)}
            >
              创建计划
            </Button>
          </Space>
        }
      >
        <Table
          columns={scheduleColumns}
          dataSource={backupSchedules}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>

      {/* 创建备份模态框 */}
      <Modal
        title="创建备份"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        width={600}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateBackup}
        >
          <Form.Item
            label="备份名称"
            name="name"
            rules={[{ required: true, message: '请输入备份名称' }]}
          >
            <Input placeholder="输入备份名称" />
          </Form.Item>

          <Form.Item
            label="备份类型"
            name="backup_type"
            rules={[{ required: true, message: '请选择备份类型' }]}
          >
            <Select placeholder="选择备份类型">
              <Select.Option value="full">完整备份</Select.Option>
              <Select.Option value="incremental">增量备份</Select.Option>
              <Select.Option value="differential">差异备份</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="备份描述"
            name="description"
          >
            <TextArea
              rows={3}
              placeholder="输入备份描述（可选）"
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建备份
              </Button>
              <Button onClick={() => setCreateModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 创建备份计划模态框 */}
      <Modal
        title="创建备份计划"
        open={scheduleModalVisible}
        onCancel={() => setScheduleModalVisible(false)}
        width={600}
        footer={null}
      >
        <Form
          form={scheduleForm}
          layout="vertical"
          onFinish={handleCreateSchedule}
        >
          <Form.Item
            label="计划名称"
            name="name"
            rules={[{ required: true, message: '请输入计划名称' }]}
          >
            <Input placeholder="输入计划名称" />
          </Form.Item>

          <Form.Item
            label="Cron 表达式"
            name="cron_expression"
            rules={[{ required: true, message: '请输入 Cron 表达式' }]}
            help="例如：0 2 * * * (每天凌晨2点执行)"
          >
            <Input placeholder="0 2 * * *" />
          </Form.Item>

          <Form.Item
            label="备份类型"
            name="backup_type"
            rules={[{ required: true, message: '请选择备份类型' }]}
          >
            <Select placeholder="选择备份类型">
              <Select.Option value="full">完整备份</Select.Option>
              <Select.Option value="incremental">增量备份</Select.Option>
              <Select.Option value="differential">差异备份</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="启用状态"
            name="is_active"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            label="保留天数"
            name="retention_days"
            rules={[{ required: true, message: '请输入保留天数' }]}
          >
            <Input type="number" placeholder="30" />
          </Form.Item>

          <Form.Item
            label="计划描述"
            name="description"
          >
            <TextArea
              rows={3}
              placeholder="输入计划描述（可选）"
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建计划
              </Button>
              <Button onClick={() => setScheduleModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default SystemBackup
