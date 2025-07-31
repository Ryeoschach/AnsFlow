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
  Card,
  Row,
  Col,
  Statistic,
  Tooltip,
  Badge
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  AppstoreOutlined,
  EyeOutlined,
  LockOutlined,
  TagsOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { DockerRegistryProject, DockerRegistryProjectFormData, DockerRegistry } from '../../types/docker';

const { Option } = Select;
const { TextArea } = Input;

interface DockerProjectsProps {}

const DockerProjects: React.FC<DockerProjectsProps> = () => {
  const [projects, setProjects] = useState<DockerRegistryProject[]>([]);
  const [registries, setRegistries] = useState<DockerRegistry[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingProject, setEditingProject] = useState<DockerRegistryProject | null>(null);
  const [selectedRegistry, setSelectedRegistry] = useState<number | null>(null);
  const [form] = Form.useForm();

  // 获取注册表列表
  const fetchRegistries = async () => {
    try {
      const response = await fetch('/api/v1/docker/registries/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setRegistries(data.results || data);
      }
    } catch (error) {
      console.error('Error fetching registries:', error);
    }
  };

  // 获取项目列表
  const fetchProjects = async () => {
    setLoading(true);
    try {
      const url = selectedRegistry 
        ? `/api/v1/docker/registries/${selectedRegistry}/projects/`
        : '/api/v1/docker/registries/projects/';
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setProjects(Array.isArray(data) ? data : data.results || []);
      }
    } catch (error) {
      message.error('获取项目列表失败');
      console.error('Error fetching projects:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRegistries();
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [selectedRegistry]);

  // 打开新增/编辑模态框
  const handleOpenModal = (project?: DockerRegistryProject) => {
    setEditingProject(project || null);
    setModalVisible(true);
    if (project) {
      form.setFieldsValue({
        name: project.name,
        registry: project.registry,
        description: project.description,
        is_default: project.is_default,
        visibility: project.visibility,
        tags: project.tags
      });
    } else {
      form.resetFields();
      if (selectedRegistry) {
        form.setFieldValue('registry', selectedRegistry);
      }
    }
  };

  // 关闭模态框
  const handleCloseModal = () => {
    setModalVisible(false);
    setEditingProject(null);
    form.resetFields();
  };

  // 保存项目
  const handleSaveProject = async (values: DockerRegistryProjectFormData) => {
    try {
      const url = editingProject 
        ? `/api/v1/docker/registry-projects/${editingProject.id}/`
        : '/api/v1/docker/registry-projects/';
      const method = editingProject ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify(values)
      });

      if (response.ok) {
        message.success(editingProject ? '项目更新成功' : '项目创建成功');
        handleCloseModal();
        fetchProjects();
      } else {
        const errorData = await response.json();
        message.error(errorData.message || '操作失败');
      }
    } catch (error) {
      message.error('网络错误，请重试');
      console.error('Error saving project:', error);
    }
  };

  // 删除项目
  const handleDeleteProject = async (projectId: number) => {
    try {
      const response = await fetch(`/api/v1/docker/registry-projects/${projectId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (response.ok) {
        message.success('项目删除成功');
        fetchProjects();
      } else {
        message.error('删除失败');
      }
    } catch (error) {
      message.error('网络错误，请重试');
      console.error('Error deleting project:', error);
    }
  };

  const columns: ColumnsType<DockerRegistryProject> = [
    {
      title: '项目名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <span style={{ fontWeight: 500 }}>{text}</span>
          {record.is_default && (
            <Tag color="gold">默认</Tag>
          )}
        </Space>
      )
    },
    {
      title: '所属注册表',
      dataIndex: 'registry_name',
      key: 'registry_name',
      render: (text, record) => {
        const registry = registries.find(r => r.id === record.registry);
        return registry ? registry.name : text || `ID: ${record.registry}`;
      }
    },
    {
      title: '可见性',
      dataIndex: 'visibility',
      key: 'visibility',
      render: (visibility) => (
        <Tag color={visibility === 'public' ? 'green' : 'orange'} icon={visibility === 'public' ? <EyeOutlined /> : <LockOutlined />}>
          {visibility === 'public' ? '公开' : '私有'}
        </Tag>
      )
    },
    {
      title: '镜像数量',
      dataIndex: 'image_count',
      key: 'image_count',
      render: (count) => (
        <Badge count={count} showZero color="#1890ff" />
      )
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags) => (
        <Space wrap>
          {tags && tags.length > 0 ? (
            tags.slice(0, 3).map((tag: string, index: number) => (
              <Tag key={index} icon={<TagsOutlined />} color="blue">
                {tag}
              </Tag>
            ))
          ) : (
            <span style={{ color: '#999' }}>无标签</span>
          )}
          {tags && tags.length > 3 && (
            <Tag>+{tags.length - 3}</Tag>
          )}
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
      title: '最后更新',
      dataIndex: 'last_updated',
      key: 'last_updated',
      render: (date) => new Date(date).toLocaleString()
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space>
          <Tooltip title="编辑">
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleOpenModal(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个项目吗？"
            description="删除后将无法恢复。"
            onConfirm={() => handleDeleteProject(record.id)}
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
    total: projects.length,
    public: projects.filter(p => p.visibility === 'public').length,
    private: projects.filter(p => p.visibility === 'private').length,
    totalImages: projects.reduce((sum, p) => sum + (p.image_count || 0), 0)
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总项目数"
              value={stats.total}
              prefix={<AppstoreOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="公开项目"
              value={stats.public}
              prefix={<EyeOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="私有项目"
              value={stats.private}
              prefix={<LockOutlined style={{ color: '#faad14' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总镜像数"
              value={stats.totalImages}
              prefix={<AppstoreOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 操作栏 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <h2 style={{ margin: 0 }}>Docker 项目管理</h2>
          <Select
            placeholder="选择注册表过滤"
            style={{ width: 200 }}
            allowClear
            value={selectedRegistry}
            onChange={setSelectedRegistry}
          >
            {registries.map(registry => (
              <Option key={registry.id} value={registry.id}>
                {registry.name}
              </Option>
            ))}
          </Select>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => handleOpenModal()}
        >
          创建项目
        </Button>
      </div>

      {/* 项目列表 */}
      <Table
        columns={columns}
        dataSource={projects}
        rowKey="id"
        loading={loading}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 个项目`
        }}
      />

      {/* 新增/编辑模态框 */}
      <Modal
        title={editingProject ? '编辑项目' : '创建项目'}
        open={modalVisible}
        onCancel={handleCloseModal}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveProject}
        >
          <Form.Item
            name="name"
            label="项目名称"
            rules={[
              { required: true, message: '请输入项目名称' },
              { max: 100, message: '名称不能超过100个字符' },
              { pattern: /^[a-zA-Z0-9._-]+$/, message: '项目名称只能包含字母、数字、点、下划线和连字符' }
            ]}
          >
            <Input placeholder="请输入项目名称" />
          </Form.Item>

          <Form.Item
            name="registry"
            label="所属注册表"
            rules={[{ required: true, message: '请选择注册表' }]}
          >
            <Select placeholder="请选择注册表">
              {registries.map(registry => (
                <Option key={registry.id} value={registry.id}>
                  {registry.name} ({registry.registry_type})
                </Option>
              ))}
            </Select>
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
              <Option value="public">公开</Option>
              <Option value="private">私有</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="tags"
            label="标签"
          >
            <Select
              mode="tags"
              placeholder="输入标签，按回车添加"
              style={{ width: '100%' }}
            >
            </Select>
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
              <Button onClick={handleCloseModal}>
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

export default DockerProjects;
