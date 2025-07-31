import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Space,
  Popconfirm,
  message,
  Tag,
  Tooltip,
  Card,
  Row,
  Col,
  Statistic,
  Drawer,
  List,
  Badge,
  Typography,
  Divider
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  ApiOutlined,
  SettingOutlined,
  StarOutlined,
  StarFilled,
  FolderOutlined,
  AppstoreOutlined,
  EyeOutlined,
  EyeInvisibleOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { DockerRegistry, DockerRegistryFormData, DockerRegistryType, DockerRegistryProject, DockerRegistryProjectFormData } from '../../types/docker';
import dockerRegistryProjectService from '../../services/dockerRegistryProjectService';

const { Option } = Select;
const { TextArea } = Input;
const { Text, Title } = Typography;

interface DockerRegistriesProps {}

const DockerRegistries: React.FC<DockerRegistriesProps> = () => {
  const [registries, setRegistries] = useState<DockerRegistry[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRegistry, setEditingRegistry] = useState<DockerRegistry | null>(null);
  const [form] = Form.useForm();
  const [testingConnection, setTestingConnection] = useState<number | null>(null);

  // 项目管理相关状态
  const [projectDrawerVisible, setProjectDrawerVisible] = useState(false);
  const [selectedRegistry, setSelectedRegistry] = useState<DockerRegistry | null>(null);
  const [registryProjects, setRegistryProjects] = useState<DockerRegistryProject[]>([]);
  const [projectModalVisible, setProjectModalVisible] = useState(false);
  const [editingProject, setEditingProject] = useState<DockerRegistryProject | null>(null);
  const [projectForm] = Form.useForm();
  const [loadingProjects, setLoadingProjects] = useState(false);

  // 获取注册表列表
  const fetchRegistries = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/docker/registries/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        const registriesData = data.results || data;
        
        // 为每个注册表获取项目数量
        const registriesWithProjectCount = await Promise.all(
          registriesData.map(async (registry: DockerRegistry) => {
            try {
              const projects = await dockerRegistryProjectService.getRegistryProjects(registry.id);
              return {
                ...registry,
                project_count: projects.length
              };
            } catch (error) {
              console.warn(`Failed to get project count for registry ${registry.id}:`, error);
              return {
                ...registry,
                project_count: 0
              };
            }
          })
        );
        
        setRegistries(registriesWithProjectCount);
      }
    } catch (error) {
      message.error('获取注册表列表失败');
      console.error('Error fetching registries:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRegistries();
  }, []);

  // 打开新增/编辑模态框
  const handleOpenModal = (registry?: DockerRegistry) => {
    setEditingRegistry(registry || null);
    setModalVisible(true);
    if (registry) {
      form.setFieldsValue({
        name: registry.name,
        url: registry.url,
        registry_type: registry.registry_type,
        username: registry.username,
        description: registry.description,
        is_default: registry.is_default
      });
    } else {
      form.resetFields();
    }
  };

  // 关闭模态框
  const handleCloseModal = () => {
    setModalVisible(false);
    setEditingRegistry(null);
    form.resetFields();
  };

  // 保存注册表
  const handleSaveRegistry = async (values: DockerRegistryFormData) => {
    try {
      const url = editingRegistry 
        ? `/api/v1/docker/registries/${editingRegistry.id}/`
        : '/api/v1/docker/registries/';
      const method = editingRegistry ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify(values)
      });

      if (response.ok) {
        message.success(editingRegistry ? '注册表更新成功' : '注册表创建成功');
        handleCloseModal();
        fetchRegistries();
      } else {
        const errorData = await response.json();
        message.error(errorData.message || '操作失败');
      }
    } catch (error) {
      message.error('网络错误，请重试');
      console.error('Error saving registry:', error);
    }
  };

  // 删除注册表
  const handleDeleteRegistry = async (registryId: number) => {
    try {
      const response = await fetch(`/api/v1/docker/registries/${registryId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (response.ok) {
        message.success('注册表删除成功');
        fetchRegistries();
      } else {
        message.error('删除失败');
      }
    } catch (error) {
      message.error('网络错误，请重试');
      console.error('Error deleting registry:', error);
    }
  };

  // 测试连接
  const handleTestConnection = async (registry: DockerRegistry) => {
    setTestingConnection(registry.id);
    try {
      const response = await fetch(`/api/v1/docker/registries/${registry.id}/test_connection/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      const result = await response.json();
      if (result.success) {
        message.success('连接测试成功');
      } else {
        message.error(`连接测试失败: ${result.message}`);
      }
      fetchRegistries(); // 刷新状态
    } catch (error) {
      message.error('测试连接失败');
      console.error('Error testing connection:', error);
    } finally {
      setTestingConnection(null);
    }
  };

  // ===== 项目管理相关函数 =====
  
  // 打开项目管理抽屉
  const handleOpenProjectDrawer = async (registry: DockerRegistry) => {
    setSelectedRegistry(registry);
    setProjectDrawerVisible(true);
    await fetchRegistryProjects(registry.id);
  };

  // 获取注册表的项目列表
  const fetchRegistryProjects = async (registryId: number) => {
    setLoadingProjects(true);
    try {
      const projects = await dockerRegistryProjectService.getRegistryProjects(registryId);
      setRegistryProjects(projects);
    } catch (error) {
      message.error('获取项目列表失败');
      console.error('Error fetching projects:', error);
    } finally {
      setLoadingProjects(false);
    }
  };

  // 打开项目模态框
  const handleOpenProjectModal = (project?: DockerRegistryProject) => {
    setEditingProject(project || null);
    setProjectModalVisible(true);
    if (project) {
      projectForm.setFieldsValue({
        name: project.name,
        description: project.description,
        visibility: project.config?.visibility || 'private',
        tags: project.config?.tags || [],
        is_default: project.is_default
      });
    } else {
      projectForm.resetFields();
      projectForm.setFieldsValue({
        registry: selectedRegistry?.id,
        visibility: 'private',
        tags: []
      });
    }
  };

  // 关闭项目模态框
  const handleCloseProjectModal = () => {
    setProjectModalVisible(false);
    setEditingProject(null);
    projectForm.resetFields();
  };

  // 更新特定注册表的项目数量
  const updateRegistryProjectCount = async (registryId: number) => {
    try {
      const projects = await dockerRegistryProjectService.getRegistryProjects(registryId);
      setRegistries(prevRegistries => 
        prevRegistries.map(registry => 
          registry.id === registryId 
            ? { ...registry, project_count: projects.length }
            : registry
        )
      );
    } catch (error) {
      console.warn(`Failed to update project count for registry ${registryId}:`, error);
    }
  };

  // 保存项目
  const handleSaveProject = async (values: DockerRegistryProjectFormData) => {
    try {
      if (!selectedRegistry) return;

      const projectData = {
        ...values,
        registry: selectedRegistry.id,
        config: {
          visibility: values.visibility || 'private',
          tags: values.tags || [],
          auto_build: true
        }
      };

      if (editingProject) {
        await dockerRegistryProjectService.updateProject(editingProject.id, projectData);
        message.success('项目更新成功');
      } else {
        await dockerRegistryProjectService.createProject(projectData);
        message.success('项目创建成功');
      }

      handleCloseProjectModal();
      await fetchRegistryProjects(selectedRegistry.id);
      await updateRegistryProjectCount(selectedRegistry.id); // 只更新当前注册表的项目计数
    } catch (error) {
      message.error(editingProject ? '项目更新失败' : '项目创建失败');
      console.error('Error saving project:', error);
    }
  };

  // 删除项目
  const handleDeleteProject = async (projectId: number) => {
    try {
      await dockerRegistryProjectService.deleteProject(projectId);
      message.success('项目删除成功');
      if (selectedRegistry) {
        await fetchRegistryProjects(selectedRegistry.id);
        await updateRegistryProjectCount(selectedRegistry.id); // 只更新当前注册表的项目计数
      }
    } catch (error) {
      message.error('项目删除失败');
      console.error('Error deleting project:', error);
    }
  };

  // 设置默认注册表
  const handleSetDefault = async (registry: DockerRegistry) => {
    try {
      const response = await fetch(`/api/v1/docker/registries/${registry.id}/set_default/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (response.ok) {
        message.success('默认注册表设置成功');
        fetchRegistries();
      } else {
        message.error('设置失败');
      }
    } catch (error) {
      message.error('网络错误，请重试');
      console.error('Error setting default:', error);
    }
  };

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'inactive':
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ExclamationCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  // 获取注册表类型标签颜色
  const getRegistryTypeColor = (type: DockerRegistryType) => {
    const colors = {
      dockerhub: 'blue',
      private: 'green',
      harbor: 'purple',
      ecr: 'orange',
      gcr: 'cyan',
      acr: 'magenta'
    };
    return colors[type] || 'default';
  };

  const columns: ColumnsType<DockerRegistry> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <span style={{ fontWeight: 500 }}>{text}</span>
          {record.is_default && (
            <Tooltip title="默认注册表">
              <StarFilled style={{ color: '#faad14' }} />
            </Tooltip>
          )}
        </Space>
      )
    },
    {
      title: '类型',
      dataIndex: 'registry_type',
      key: 'registry_type',
      render: (type) => (
        <Tag color={getRegistryTypeColor(type)}>
          {type.toUpperCase()}
        </Tag>
      )
    },
    {
      title: '地址',
      dataIndex: 'url',
      key: 'url',
      ellipsis: true
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status, record) => (
        <Tooltip title={record.check_message || status}>
          <Space>
            {getStatusIcon(status)}
            <span>{
              status === 'active' ? '正常' :
              status === 'inactive' ? '未激活' : '错误'
            }</span>
          </Space>
        </Tooltip>
      )
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (text) => text || '-'
    },
    {
      title: '项目数',
      dataIndex: 'project_count',
      key: 'project_count',
      render: (count) => count || 0
    },
    {
      title: '最后检查',
      dataIndex: 'last_check',
      key: 'last_check',
      render: (date) => date ? new Date(date).toLocaleString() : '-'
    },
    {
      title: '操作',
      key: 'actions',
      width: 300,
      render: (_, record) => (
        <Space>
          <Tooltip title="管理项目">
            <Button
              type="link"
              icon={<FolderOutlined />}
              onClick={() => handleOpenProjectDrawer(record)}
            >
              项目({record.project_count || 0})
            </Button>
          </Tooltip>
          <Tooltip title="测试连接">
            <Button
              type="link"
              icon={<ApiOutlined />}
              loading={testingConnection === record.id}
              onClick={() => handleTestConnection(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleOpenModal(record)}
            />
          </Tooltip>
          {!record.is_default && (
            <Tooltip title="设为默认">
              <Button
                type="link"
                icon={<StarOutlined />}
                onClick={() => handleSetDefault(record)}
              />
            </Tooltip>
          )}
          <Popconfirm
            title="确定要删除这个注册表吗？"
            description="删除后将无法恢复，且相关的流水线步骤可能受到影响。"
            onConfirm={() => handleDeleteRegistry(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="link"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  // 统计数据
  const stats = {
    total: registries.length,
    active: registries.filter(r => r.status === 'active').length,
    default: registries.filter(r => r.is_default).length
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总注册表数"
              value={stats.total}
              prefix={<SettingOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃注册表"
              value={stats.active}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="默认注册表"
              value={stats.default}
              prefix={<StarFilled style={{ color: '#faad14' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 操作栏 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>Docker 注册表管理</h2>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => handleOpenModal()}
        >
          添加注册表
        </Button>
      </div>

      {/* 注册表列表 */}
      <Table
        columns={columns}
        dataSource={registries}
        rowKey="id"
        loading={loading}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 个注册表`
        }}
      />

      {/* 新增/编辑模态框 */}
      <Modal
        title={editingRegistry ? '编辑注册表' : '添加注册表'}
        open={modalVisible}
        onCancel={handleCloseModal}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveRegistry}
        >
          <Form.Item
            name="name"
            label="注册表名称"
            rules={[
              { required: true, message: '请输入注册表名称' },
              { max: 100, message: '名称不能超过100个字符' }
            ]}
          >
            <Input placeholder="请输入注册表名称" />
          </Form.Item>

          <Form.Item
            name="registry_type"
            label="注册表类型"
            rules={[{ required: true, message: '请选择注册表类型' }]}
          >
            <Select placeholder="请选择注册表类型">
              <Option value="dockerhub">Docker Hub</Option>
              <Option value="private">私有仓库</Option>
              <Option value="harbor">Harbor</Option>
              <Option value="ecr">AWS ECR</Option>
              <Option value="gcr">Google GCR</Option>
              <Option value="acr">Azure ACR</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="url"
            label="注册表地址"
            rules={[
              { required: true, message: '请输入注册表地址' },
              { type: 'url', message: '请输入有效的URL' }
            ]}
          >
            <Input placeholder="https://registry.example.com" />
          </Form.Item>

          <Form.Item
            name="username"
            label="用户名"
          >
            <Input placeholder="请输入用户名（可选）" />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
          >
            <Input.Password placeholder="请输入密码（可选）" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea
              rows={3}
              placeholder="请输入注册表描述"
              maxLength={500}
            />
          </Form.Item>

          <Form.Item
            name="is_default"
            label="设为默认注册表"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={handleCloseModal}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {editingRegistry ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 项目管理抽屉 */}
      <Drawer
        title={
          <Space>
            <FolderOutlined />
            <span>{selectedRegistry?.name} - 项目管理</span>
            <Badge count={registryProjects.length} showZero color="#1890ff" />
          </Space>
        }
        placement="right"
        width={800}
        open={projectDrawerVisible}
        onClose={() => setProjectDrawerVisible(false)}
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => handleOpenProjectModal()}
          >
            添加项目
          </Button>
        }
      >
        <List
          loading={loadingProjects}
          dataSource={registryProjects}
          renderItem={(project) => (
            <List.Item
              actions={[
                <Button
                  key="edit"
                  type="link"
                  icon={<EditOutlined />}
                  onClick={() => handleOpenProjectModal(project)}
                >
                  编辑
                </Button>,
                <Popconfirm
                  key="delete"
                  title="确定要删除这个项目吗？"
                  description="删除后将无法恢复。"
                  onConfirm={() => handleDeleteProject(project.id)}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button type="link" danger icon={<DeleteOutlined />}>
                    删除
                  </Button>
                </Popconfirm>
              ]}
            >
              <List.Item.Meta
                avatar={<AppstoreOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                title={
                  <Space>
                    <Text strong>{project.name}</Text>
                    {project.is_default && (
                      <Tag color="gold">
                        <StarFilled /> 默认
                      </Tag>
                    )}
                    <Tag color={project.config?.visibility === 'public' ? 'green' : 'orange'}>
                      {project.config?.visibility === 'public' ? (
                        <><EyeOutlined /> 公开</>
                      ) : (
                        <><EyeInvisibleOutlined /> 私有</>
                      )}
                    </Tag>
                  </Space>
                }
                description={
                  <div>
                    <Text type="secondary">{project.description || '暂无描述'}</Text>
                    <div style={{ marginTop: 8 }}>
                      <Text type="secondary">镜像数量: {project.image_count}</Text>
                      <Divider type="vertical" />
                      <Text type="secondary">更新时间: {new Date(project.last_updated).toLocaleString()}</Text>
                    </div>
                    {project.config?.tags && project.config.tags.length > 0 && (
                      <div style={{ marginTop: 8 }}>
                        {project.config.tags.map((tag: string) => (
                          <Tag key={tag} style={{ fontSize: '12px' }}>{tag}</Tag>
                        ))}
                      </div>
                    )}
                  </div>
                }
              />
            </List.Item>
          )}
          locale={{ emptyText: '暂无项目，点击添加项目开始创建' }}
        />
      </Drawer>

      {/* 项目编辑模态框 */}
      <Modal
        title={editingProject ? '编辑项目' : '创建项目'}
        open={projectModalVisible}
        onCancel={handleCloseProjectModal}
        footer={null}
        width={600}
      >
        <Form
          form={projectForm}
          layout="vertical"
          onFinish={handleSaveProject}
        >
          <Form.Item
            name="name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input placeholder="请输入项目名称，如：my-web-app" />
          </Form.Item>

          <Form.Item
            name="description"
            label="项目描述"
          >
            <TextArea
              rows={3}
              placeholder="请输入项目描述"
              maxLength={500}
            />
          </Form.Item>

          <Form.Item
            name="visibility"
            label="可见性"
            initialValue="private"
          >
            <Select>
              <Option value="public">
                <Space>
                  <EyeOutlined />
                  公开 - 任何人都可以拉取镜像
                </Space>
              </Option>
              <Option value="private">
                <Space>
                  <EyeInvisibleOutlined />
                  私有 - 需要认证才能访问
                </Space>
              </Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="tags"
            label="标签"
          >
            <Select
              mode="tags"
              placeholder="输入标签，按回车添加"
              tokenSeparators={[',']}
            />
          </Form.Item>

          <Form.Item
            name="is_default"
            label="设为默认项目"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={handleCloseProjectModal}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {editingProject ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DockerRegistries;
