import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Space,
  Tag,
  Tooltip,
  message,
  Row,
  Col,
  Statistic,
  Dropdown,
  Popconfirm
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UserOutlined,
  EnvironmentOutlined,
  SettingOutlined,
  EyeOutlined,
  TeamOutlined,
  FolderOutlined,
  MoreOutlined
} from '@ant-design/icons';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import apiService from '../services/api';

const { Option } = Select;
const { TextArea } = Input;

interface Project {
  id: number;
  name: string;
  description: string;
  visibility: 'private' | 'internal' | 'public';
  repository_url: string;
  default_branch: string;
  is_active: boolean;
  settings: Record<string, any>;
  owner: {
    id: number;
    username: string;
    email: string;
  };
  member_count: number;
  pipeline_count: number;
  created_at: string;
  updated_at: string;
}

interface Environment {
  id: number;
  name: string;
  env_type: 'development' | 'testing' | 'staging' | 'production';
  url: string;
  config: Record<string, any>;
  auto_deploy: boolean;
  deploy_branch: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface ProjectMember {
  id: number;
  user: {
    id: number;
    username: string;
    email: string;
  };
  role: 'owner' | 'maintainer' | 'developer' | 'reporter' | 'guest';
  created_at: string;
}

const Projects: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [formVisible, setFormVisible] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [form] = Form.useForm();

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setLoading(true);
    try {
      const data = await apiService.getProjects();
      setProjects(Array.isArray(data) ? data : (data as any)?.results || []);
    } catch (error) {
      console.error('Failed to load projects:', error);
      message.error('加载项目列表失败');
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  const loadProjectDetails = async (projectId: number) => {
    try {
      const [projectDetail, environmentList, memberList] = await Promise.all([
        apiService.getProject(projectId),
        apiService.getProjectEnvironments(projectId),
        apiService.getProjectMembers(projectId)
      ]);
      
      setSelectedProject(projectDetail);
      setEnvironments(environmentList);
      setMembers(memberList);
    } catch (error) {
      console.error('Failed to load project details:', error);
      message.error('加载项目详情失败');
    }
  };

  const handleCreateProject = () => {
    setEditingProject(null);
    form.resetFields();
    form.setFieldsValue({
      visibility: 'private',
      is_active: true,
      default_branch: 'main'
    });
    setFormVisible(true);
  };

  const handleEditProject = (project: Project) => {
    setEditingProject(project);
    form.setFieldsValue({
      name: project.name,
      description: project.description,
      visibility: project.visibility,
      repository_url: project.repository_url,
      default_branch: project.default_branch,
      is_active: project.is_active
    });
    setFormVisible(true);
  };

  const handleViewProject = async (project: Project) => {
    await loadProjectDetails(project.id);
    setDetailVisible(true);
  };

  const handleDeleteProject = async (project: Project) => {
    try {
      await apiService.deleteProject(project.id);
      message.success('项目删除成功');
      loadProjects();
    } catch (error) {
      console.error('Failed to delete project:', error);
      message.error('删除项目失败');
    }
  };

  const handleFormSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingProject) {
        await apiService.updateProject(editingProject.id, values);
        message.success('项目更新成功');
      } else {
        await apiService.createProject(values);
        message.success('项目创建成功');
      }
      
      setFormVisible(false);
      loadProjects();
    } catch (error) {
      console.error('Failed to save project:', error);
      message.error(editingProject ? '更新项目失败' : '创建项目失败');
    }
  };

  const getVisibilityColor = (visibility: string) => {
    switch (visibility) {
      case 'public': return 'green';
      case 'internal': return 'blue';
      case 'private': return 'red';
      default: return 'default';
    }
  };

  const getVisibilityText = (visibility: string) => {
    switch (visibility) {
      case 'public': return '公开';
      case 'internal': return '内部';
      case 'private': return '私有';
      default: return visibility;
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'owner': return 'gold';
      case 'maintainer': return 'blue';
      case 'developer': return 'green';
      case 'reporter': return 'orange';
      case 'guest': return 'default';
      default: return 'default';
    }
  };

  const getRoleText = (role: string) => {
    switch (role) {
      case 'owner': return '拥有者';
      case 'maintainer': return '维护者';
      case 'developer': return '开发者';
      case 'reporter': return '报告者';
      case 'guest': return '访客';
      default: return role;
    }
  };

  const getEnvTypeColor = (envType: string) => {
    switch (envType) {
      case 'production': return 'red';
      case 'staging': return 'orange';
      case 'testing': return 'blue';
      case 'development': return 'green';
      default: return 'default';
    }
  };

  const getEnvTypeText = (envType: string) => {
    switch (envType) {
      case 'production': return '生产环境';
      case 'staging': return '预发布环境';
      case 'testing': return '测试环境';
      case 'development': return '开发环境';
      default: return envType;
    }
  };

  const columns = [
    {
      title: '项目名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Project) => (
        <Space>
          <FolderOutlined />
          <span style={{ fontWeight: 500 }}>{text}</span>
          {!record.is_active && <Tag color="default">已停用</Tag>}
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: '可见性',
      dataIndex: 'visibility',
      key: 'visibility',
      render: (visibility: string) => (
        <Tag color={getVisibilityColor(visibility)}>
          {getVisibilityText(visibility)}
        </Tag>
      ),
    },
    {
      title: '拥有者',
      key: 'owner',
      render: (_: any, record: Project) => (
        <Space>
          <UserOutlined />
          <span>{record.owner.username}</span>
        </Space>
      ),
    },
    {
      title: '成员数',
      dataIndex: 'member_count',
      key: 'member_count',
      render: (count: number) => (
        <Space>
          <TeamOutlined />
          <span>{count}</span>
        </Space>
      ),
    },
    {
      title: '流水线数',
      dataIndex: 'pipeline_count',
      key: 'pipeline_count',
      render: (count: number) => count || 0,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (created_at: string) => (
        <span style={{ color: '#666' }}>
          {formatDistanceToNow(new Date(created_at), {
            addSuffix: true,
            locale: zhCN
          })}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: Project) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewProject(record)}
            />
          </Tooltip>
          <Tooltip title="编辑项目">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEditProject(record)}
            />
          </Tooltip>
          <Dropdown
            menu={{
              items: [
                {
                  key: 'manage-members',
                  icon: <TeamOutlined />,
                  label: '管理成员',
                  onClick: () => {
                    // TODO: 实现成员管理
                    message.info('成员管理功能开发中...');
                  },
                },
                {
                  key: 'manage-environments',
                  icon: <EnvironmentOutlined />,
                  label: '管理环境',
                  onClick: () => {
                    // TODO: 实现环境管理
                    message.info('环境管理功能开发中...');
                  },
                },
                {
                  key: 'settings',
                  icon: <SettingOutlined />,
                  label: '项目设置',
                  onClick: () => {
                    // TODO: 实现项目设置
                    message.info('项目设置功能开发中...');
                  },
                },
                {
                  type: 'divider' as const,
                },
                {
                  key: 'delete',
                  icon: <DeleteOutlined />,
                  label: '删除项目',
                  danger: true,
                  onClick: () => {
                    Modal.confirm({
                      title: '确认删除项目？',
                      content: '删除后将无法恢复，相关流水线和数据也会被删除。',
                      okText: '确认删除',
                      cancelText: '取消',
                      okType: 'danger',
                      onOk: () => handleDeleteProject(record),
                    });
                  },
                },
              ],
            }}
            trigger={['click']}
          >
            <Button type="text" size="small" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总项目数"
              value={projects.length}
              prefix={<FolderOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃项目"
              value={projects.filter(p => p.is_active).length}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总流水线数"
              value={projects.reduce((sum, p) => sum + p.pipeline_count, 0)}
              prefix={<SettingOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总成员数"
              value={projects.reduce((sum, p) => sum + p.member_count, 0)}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 项目列表 */}
      <Card
        title="项目列表"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreateProject}
          >
            新建项目
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={projects}
          rowKey="id"
          loading={loading}
          pagination={{
            total: projects.length,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个项目`,
          }}
        />
      </Card>

      {/* 创建/编辑表单 */}
      <Modal
        title={editingProject ? '编辑项目' : '新建项目'}
        open={formVisible}
        onCancel={() => setFormVisible(false)}
        onOk={handleFormSubmit}
        okText={editingProject ? '更新' : '创建'}
        cancelText="取消"
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input placeholder="输入项目名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="项目描述"
          >
            <TextArea
              placeholder="输入项目描述（可选）"
              rows={3}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="visibility"
                label="可见性"
                rules={[{ required: true, message: '请选择可见性' }]}
              >
                <Select placeholder="选择可见性">
                  <Option value="private">私有</Option>
                  <Option value="internal">内部</Option>
                  <Option value="public">公开</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="is_active"
                label="状态"
              >
                <Select>
                  <Option value={true}>活跃</Option>
                  <Option value={false}>停用</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="repository_url"
            label="仓库地址"
          >
            <Input placeholder="输入Git仓库地址（可选）" />
          </Form.Item>

          <Form.Item
            name="default_branch"
            label="默认分支"
          >
            <Input placeholder="默认分支名称" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 项目详情抽屉 */}
      <Modal
        title="项目详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={800}
      >
        {selectedProject && (
          <div>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <Card size="small" title="基本信息">
                  <p><strong>项目名称:</strong> {selectedProject.name}</p>
                  <p><strong>描述:</strong> {selectedProject.description || '-'}</p>
                  <p><strong>可见性:</strong> 
                    <Tag color={getVisibilityColor(selectedProject.visibility)} style={{ marginLeft: 8 }}>
                      {getVisibilityText(selectedProject.visibility)}
                    </Tag>
                  </p>
                  <p><strong>拥有者:</strong> {selectedProject.owner.username}</p>
                  <p><strong>状态:</strong> 
                    <Tag color={selectedProject.is_active ? 'green' : 'default'} style={{ marginLeft: 8 }}>
                      {selectedProject.is_active ? '活跃' : '停用'}
                    </Tag>
                  </p>
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" title="统计信息">
                  <p><strong>成员数量:</strong> {selectedProject.member_count}</p>
                  <p><strong>流水线数量:</strong> {selectedProject.pipeline_count}</p>
                  <p><strong>创建时间:</strong> {new Date(selectedProject.created_at).toLocaleString()}</p>
                  <p><strong>更新时间:</strong> {new Date(selectedProject.updated_at).toLocaleString()}</p>
                </Card>
              </Col>
            </Row>

            {/* 环境列表 */}
            <Card size="small" title="环境配置" style={{ marginBottom: 16 }}>
              {environments.length > 0 ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {environments.map(env => (
                    <Tag
                      key={env.id}
                      color={getEnvTypeColor(env.env_type)}
                      style={{ margin: 4 }}
                    >
                      {env.name} ({getEnvTypeText(env.env_type)})
                    </Tag>
                  ))}
                </div>
              ) : (
                <p style={{ color: '#999', textAlign: 'center', padding: 20 }}>
                  暂无环境配置
                </p>
              )}
            </Card>

            {/* 成员列表 */}
            <Card size="small" title="项目成员">
              {members.length > 0 ? (
                <div>
                  {members.map(member => (
                    <div key={member.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                      <Space>
                        <UserOutlined />
                        <span>{member.user.username}</span>
                        <span style={{ color: '#666' }}>({member.user.email})</span>
                      </Space>
                      <Tag color={getRoleColor(member.role)}>
                        {getRoleText(member.role)}
                      </Tag>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: '#999', textAlign: 'center', padding: 20 }}>
                  暂无项目成员
                </p>
              )}
            </Card>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Projects;
