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
  Drawer,
  Typography,
  Divider,
  Row,
  Col,
  Statistic,
  Avatar,
  Switch,
  Tabs
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  TeamOutlined,
  UserOutlined,
  CrownOutlined,
  SettingOutlined,
  EyeOutlined,
  UserAddOutlined,
  UserDeleteOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { apiService } from '../../services/api'
import { Team, TeamMembership, User } from '../../types'

const { TextArea } = Input
const { Text, Title } = Typography
const { TabPane } = Tabs

interface TeamManagementProps {}

const TeamManagement: React.FC<TeamManagementProps> = () => {
  const [teams, setTeams] = useState<Team[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [memberships, setMemberships] = useState<TeamMembership[]>([])
  const [loading, setLoading] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [memberModalVisible, setMemberModalVisible] = useState(false)
  const [teamDetailVisible, setTeamDetailVisible] = useState(false)
  const [currentTeam, setCurrentTeam] = useState<Team | null>(null)
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [memberForm] = Form.useForm()

  // 加载数据
  const fetchData = async () => {
    setLoading(true)
    try {
      const [teamsResponse, usersResponse] = await Promise.all([
        apiService.getTeams(),
        apiService.getUsers()
      ])
      setTeams(teamsResponse.results || teamsResponse)
      setUsers(usersResponse.results || usersResponse)
    } catch (error) {
      message.error('加载数据失败')
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  // 加载团队成员
  const fetchTeamMembers = async (teamId: number) => {
    try {
      const response = await apiService.getTeamMemberships(teamId)
      setMemberships(response.results || response)
    } catch (error) {
      console.error('Failed to fetch team members:', error)
      message.error('获取团队成员失败')
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  useEffect(() => {
    if (selectedTeamId) {
      fetchTeamMembers(selectedTeamId)
    }
  }, [selectedTeamId])

  // 团队操作
  const handleAddTeam = () => {
    setCurrentTeam(null)
    form.resetFields()
    setEditModalVisible(true)
  }

  const handleEditTeam = (record: Team) => {
    setCurrentTeam(record)
    form.setFieldsValue(record)
    setEditModalVisible(true)
  }

  const handleDeleteTeam = async (id: number) => {
    try {
      await apiService.deleteTeam(id)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      message.error('删除失败')
      console.error('Failed to delete team:', error)
    }
  }

  const handleSubmitTeam = async (values: any) => {
    try {
      if (currentTeam) {
        await apiService.updateTeam(currentTeam.id, values)
        message.success('更新成功')
      } else {
        await apiService.createTeam(values)
        message.success('创建成功')
      }
      
      setEditModalVisible(false)
      fetchData()
    } catch (error) {
      message.error(currentTeam ? '更新失败' : '创建失败')
      console.error('Failed to save team:', error)
    }
  }

  // 成员操作
  const handleAddMember = () => {
    memberForm.resetFields()
    setMemberModalVisible(true)
  }

  const handleSubmitMember = async (values: any) => {
    try {
      if (selectedTeamId) {
        await apiService.addTeamMember(selectedTeamId, {
          user: values.user_id,
          role: values.role
        })
        message.success('成员添加成功')
        fetchTeamMembers(selectedTeamId)
      }
      setMemberModalVisible(false)
    } catch (error) {
      message.error('添加成员失败')
      console.error('Failed to add member:', error)
    }
  }

  const handleRemoveMember = async (teamId: number, userId: number) => {
    try {
      await apiService.removeTeamMember(teamId, userId)
      message.success('成员移除成功')
      fetchTeamMembers(teamId)
    } catch (error) {
      message.error('移除成员失败')
      console.error('Failed to remove member:', error)
    }
  }

  const handleUpdateMemberRole = async (teamId: number, userId: number, role: string) => {
    try {
      await apiService.updateTeamMember(teamId, userId, { role: role as 'admin' | 'member' | 'viewer' })
      message.success('角色更新成功')
      fetchTeamMembers(teamId)
    } catch (error) {
      message.error('角色更新失败')
      console.error('Failed to update member role:', error)
    }
  }

  // 团队表格列
  const teamColumns: ColumnsType<Team> = [
    {
      title: '团队名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <Avatar size="small" icon={<TeamOutlined />} src={record.avatar} />
          <span>{text}</span>
        </Space>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text) => text || '-'
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? '活跃' : '停用'}
        </Tag>
      )
    },
    {
      title: '成员数量',
      dataIndex: 'member_count',
      key: 'member_count',
      render: (count) => count || 0
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleDateString()
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => {
              setCurrentTeam(record)
              setSelectedTeamId(record.id)
              setTeamDetailVisible(true)
            }}
          >
            详情
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEditTeam(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个团队吗？"
            onConfirm={() => handleDeleteTeam(record.id)}
          >
            <Button
              type="link"
              icon={<DeleteOutlined />}
              danger
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  // 成员表格列
  const memberColumns: ColumnsType<TeamMembership> = [
    {
      title: '用户',
      key: 'user',
      render: (_, record) => (
        <Space>
          <Avatar size="small" icon={<UserOutlined />} />
          <div>
            <div>{record.user_info?.username || `用户 ${record.user}`}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.user_info?.email}
            </Text>
          </div>
        </Space>
      )
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role) => {
        const colors = {
          'owner': 'gold',
          'admin': 'red',
          'member': 'blue',
          'viewer': 'default'
        }
        const icons = {
          'owner': <CrownOutlined />,
          'admin': <SettingOutlined />,
          'member': <UserOutlined />,
          'viewer': <EyeOutlined />
        }
        return (
          <Tag color={colors[role as keyof typeof colors]} icon={icons[role as keyof typeof icons]}>
            {role}
          </Tag>
        )
      }
    },
    {
      title: '加入时间',
      dataIndex: 'joined_at',
      key: 'joined_at',
      render: (date) => new Date(date).toLocaleDateString()
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Select
            size="small"
            value={record.role}
            style={{ width: 80 }}
            onChange={(role) => handleUpdateMemberRole(record.team, record.user, role)}
          >
            <Select.Option value="owner">Owner</Select.Option>
            <Select.Option value="admin">Admin</Select.Option>
            <Select.Option value="member">Member</Select.Option>
            <Select.Option value="viewer">Viewer</Select.Option>
          </Select>
          <Popconfirm
            title="确定要移除这个成员吗？"
            onConfirm={() => handleRemoveMember(record.team, record.user)}
          >
            <Button
              type="link"
              icon={<UserDeleteOutlined />}
              danger
              size="small"
            >
              移除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  // 统计数据
  const stats = {
    totalTeams: teams.length,
    activeTeams: teams.filter(t => t.is_active).length,
    totalMembers: memberships.length
  }

  return (
    <div>
      <Title level={4}>团队管理</Title>
      
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic title="团队总数" value={stats.totalTeams} prefix={<TeamOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="活跃团队" value={stats.activeTeams} prefix={<TeamOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="总成员数" value={stats.totalMembers} prefix={<UserOutlined />} />
          </Card>
        </Col>
      </Row>

      <Card
        title="团队列表"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={fetchData}>
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAddTeam}
            >
              新建团队
            </Button>
          </Space>
        }
      >
        <Table
          columns={teamColumns}
          dataSource={teams}
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

      {/* 团队编辑模态框 */}
      <Modal
        title={currentTeam ? '编辑团队' : '新建团队'}
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        width={600}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmitTeam}
        >
          <Form.Item
            label="团队名称"
            name="name"
            rules={[{ required: true, message: '请输入团队名称' }]}
          >
            <Input placeholder="请输入团队名称" />
          </Form.Item>

          <Form.Item
            label="团队描述"
            name="description"
          >
            <TextArea rows={3} placeholder="请输入团队描述" />
          </Form.Item>

          <Form.Item
            label="头像URL"
            name="avatar"
          >
            <Input placeholder="请输入头像URL" />
          </Form.Item>

          <Form.Item
            label="状态"
            name="is_active"
            valuePropName="checked"
          >
            <Switch checkedChildren="活跃" unCheckedChildren="停用" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {currentTeam ? '更新' : '创建'}
              </Button>
              <Button onClick={() => setEditModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 添加成员模态框 */}
      <Modal
        title="添加团队成员"
        open={memberModalVisible}
        onCancel={() => setMemberModalVisible(false)}
        footer={null}
      >
        <Form
          form={memberForm}
          layout="vertical"
          onFinish={handleSubmitMember}
        >
          <Form.Item
            label="选择用户"
            name="user_id"
            rules={[{ required: true, message: '请选择用户' }]}
          >
            <Select
              placeholder="请选择用户"
              showSearch
              filterOption={(input, option) =>
                option?.children?.toString().toLowerCase().includes(input.toLowerCase()) ?? false
              }
            >
              {users.map(user => (
                <Select.Option key={user.id} value={user.id}>
                  {user.username} ({user.email})
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="角色"
            name="role"
            rules={[{ required: true, message: '请选择角色' }]}
            initialValue="member"
          >
            <Select placeholder="请选择角色">
              <Select.Option value="owner">Owner</Select.Option>
              <Select.Option value="admin">Admin</Select.Option>
              <Select.Option value="member">Member</Select.Option>
              <Select.Option value="viewer">Viewer</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                添加
              </Button>
              <Button onClick={() => setMemberModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 团队详情抽屉 */}
      <Drawer
        title="团队详情"
        open={teamDetailVisible}
        onClose={() => setTeamDetailVisible(false)}
        width={800}
      >
        {currentTeam && (
          <div>
            <Row gutter={16}>
              <Col span={24}>
                <Card size="small" title="基本信息">
                  <p><strong>团队名称：</strong>{currentTeam.name}</p>
                  <p><strong>描述：</strong>{currentTeam.description || '暂无描述'}</p>
                  <p><strong>状态：</strong>
                    <Tag color={currentTeam.is_active ? 'green' : 'red'}>
                      {currentTeam.is_active ? '活跃' : '停用'}
                    </Tag>
                  </p>
                  <p><strong>创建时间：</strong>{new Date(currentTeam.created_at).toLocaleString()}</p>
                </Card>
              </Col>
            </Row>
            
            <Divider />
            
            <Card
              size="small"
              title="团队成员"
              extra={
                <Button
                  type="primary"
                  size="small"
                  icon={<UserAddOutlined />}
                  onClick={handleAddMember}
                >
                  添加成员
                </Button>
              }
            >
              <Table
                columns={memberColumns}
                dataSource={memberships}
                rowKey="id"
                size="small"
                pagination={false}
              />
            </Card>
          </div>
        )}
      </Drawer>
    </div>
  )
}

export default TeamManagement
