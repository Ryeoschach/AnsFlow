import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Typography,
  Tooltip,
  Switch,
  Alert,
  Row,
  Col,
  Statistic
} from 'antd';
import {
  CloudUploadOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  LinkOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  SafetyCertificateOutlined
} from '@ant-design/icons';

const { Text } = Typography;
const { TextArea } = Input;
const { Password } = Input;

interface DockerRegistry {
  id: number;
  name: string;
  url: string;
  username: string;
  description?: string;
  registry_type: 'dockerhub' | 'aws_ecr' | 'azure_acr' | 'google_gcr' | 'harbor' | 'private';
  status: 'active' | 'inactive' | 'error';
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

const DockerRegistrySettings: React.FC = () => {
  const [registries, setRegistries] = useState<DockerRegistry[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRegistry, setEditingRegistry] = useState<DockerRegistry | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadMockData();
  }, []);

  const loadMockData = () => {
    const mockRegistries: DockerRegistry[] = [
      {
        id: 1,
        name: 'Docker Hub',
        url: 'https://registry-1.docker.io',
        username: 'myuser',
        description: '官方 Docker Hub 镜像仓库',
        registry_type: 'dockerhub',
        status: 'active',
        is_default: true,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-20T15:30:00Z'
      },
      {
        id: 2,
        name: '阿里云容器镜像',
        url: 'registry.cn-hangzhou.aliyuncs.com',
        username: 'aliyun_user',
        description: '阿里云 ACR 容器镜像服务',
        registry_type: 'private',
        status: 'active',
        is_default: false,
        created_at: '2024-01-10T08:00:00Z',
        updated_at: '2024-01-18T12:15:00Z'
      },
      {
        id: 3,
        name: 'AWS ECR',
        url: '123456789012.dkr.ecr.us-west-2.amazonaws.com',
        username: 'aws_user',
        description: 'AWS Elastic Container Registry',
        registry_type: 'aws_ecr',
        status: 'inactive',
        is_default: false,
        created_at: '2024-01-05T14:00:00Z',
        updated_at: '2024-01-15T09:45:00Z'
      }
    ];

    setRegistries(mockRegistries);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircleOutlined />;
      case 'inactive':
        return <ExclamationCircleOutlined />;
      case 'error':
        return <CloseCircleOutlined />;
      default:
        return null;
    }
  };

  const getRegistryTypeLabel = (type: string) => {
    const typeMap: Record<string, string> = {
      dockerhub: 'Docker Hub',
      aws_ecr: 'AWS ECR',
      azure_acr: 'Azure ACR',
      google_gcr: 'Google GCR',
      harbor: 'Harbor',
      private: '私有仓库'
    };
    return typeMap[type] || type;
  };

  const handleAdd = () => {
    setEditingRegistry(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (registry: DockerRegistry) => {
    setEditingRegistry(registry);
    form.setFieldsValue({
      ...registry,
      password: '' // 不显示密码
    });
    setModalVisible(true);
  };

  const handleDelete = async (registryId: number) => {
    try {
      setRegistries(registries.filter(r => r.id !== registryId));
      message.success('注册表删除成功');
    } catch (error) {
      message.error('删除注册表失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingRegistry) {
        const updatedRegistries = registries.map(r => 
          r.id === editingRegistry.id 
            ? { ...r, ...values, updated_at: new Date().toISOString() }
            : r
        );
        setRegistries(updatedRegistries);
        message.success('注册表更新成功');
      } else {
        const newRegistry: DockerRegistry = {
          id: Date.now(),
          ...values,
          status: 'inactive',
          is_default: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        setRegistries([...registries, newRegistry]);
        message.success('注册表添加成功');
      }
      
      setModalVisible(false);
    } catch (error) {
      message.error('保存注册表失败');
    }
  };

  const handleTestConnection = async (registry: DockerRegistry) => {
    setLoading(true);
    try {
      // 模拟连接测试
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const updatedRegistries = registries.map(r => 
        r.id === registry.id 
          ? { ...r, status: 'active' as const, updated_at: new Date().toISOString() }
          : r
      );
      setRegistries(updatedRegistries);
      message.success('连接测试成功');
    } catch (error) {
      message.error('连接测试失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSetDefault = async (registryId: number) => {
    try {
      const updatedRegistries = registries.map(r => ({
        ...r,
        is_default: r.id === registryId,
        updated_at: r.id === registryId ? new Date().toISOString() : r.updated_at
      }));
      setRegistries(updatedRegistries);
      message.success('默认注册表设置成功');
    } catch (error) {
      message.error('设置默认注册表失败');
    }
  };

  const columns = [
    {
      title: '注册表名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: DockerRegistry) => (
        <Space>
          <CloudUploadOutlined />
          <strong>{text}</strong>
          {record.is_default && <Tag color="gold">默认</Tag>}
          <Tag color={getStatusColor(record.status)}>
            {getStatusIcon(record.status)}
            {record.status}
          </Tag>
        </Space>
      )
    },
    {
      title: '类型',
      dataIndex: 'registry_type',
      key: 'registry_type',
      render: (type: string) => (
        <Tag color="blue">{getRegistryTypeLabel(type)}</Tag>
      )
    },
    {
      title: '注册表地址',
      dataIndex: 'url',
      key: 'url',
      render: (text: string) => (
        <Text code copyable={{ text }}>{text}</Text>
      )
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username'
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      render: (text: string) => text || '-'
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleString()
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: DockerRegistry) => (
        <Space>
          <Tooltip title="测试连接">
            <Button
              size="small"
              icon={<LinkOutlined />}
              onClick={() => handleTestConnection(record)}
              loading={loading}
            />
          </Tooltip>
          {!record.is_default && (
            <Tooltip title="设为默认">
              <Button
                size="small"
                icon={<SafetyCertificateOutlined />}
                onClick={() => handleSetDefault(record.id)}
              />
            </Tooltip>
          )}
          <Tooltip title="编辑">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这个注册表吗？"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
                disabled={record.is_default}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      )
    }
  ];

  const activeRegistries = registries.filter(r => r.status === 'active').length;
  const defaultRegistry = registries.find(r => r.is_default);

  return (
    <div>
      <Alert
        message="Docker 注册表配置"
        description="管理 Docker 镜像仓库配置，这些配置将用于流水线中的 Docker 步骤。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="活跃注册表"
              value={activeRegistries}
              suffix={`/ ${registries.length}`}
              valueStyle={{ color: '#3f8600' }}
              prefix={<CloudUploadOutlined />}
            />
          </Card>
        </Col>
        <Col span={16}>
          <Card>
            <Statistic
              title="默认注册表"
              value={defaultRegistry?.name || '未设置'}
              valueStyle={{ color: '#1890ff' }}
              prefix={<SafetyCertificateOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="Docker 注册表"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            添加注册表
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={registries}
          rowKey="id"
          size="small"
          pagination={false}
        />
      </Card>

      {/* 注册表配置模态框 */}
      <Modal
        title={editingRegistry ? '编辑注册表' : '添加注册表'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            registry_type: 'private'
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="注册表名称"
                name="name"
                rules={[{ required: true, message: '请输入注册表名称' }]}
              >
                <Input placeholder="输入注册表名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="注册表类型"
                name="registry_type"
                rules={[{ required: true, message: '请选择注册表类型' }]}
              >
                <Select placeholder="选择注册表类型">
                  <Select.Option value="dockerhub">Docker Hub</Select.Option>
                  <Select.Option value="aws_ecr">AWS ECR</Select.Option>
                  <Select.Option value="azure_acr">Azure ACR</Select.Option>
                  <Select.Option value="google_gcr">Google GCR</Select.Option>
                  <Select.Option value="harbor">Harbor</Select.Option>
                  <Select.Option value="private">私有仓库</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="注册表地址"
            name="url"
            rules={[{ required: true, message: '请输入注册表地址' }]}
          >
            <Input placeholder="https://registry.example.com" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="用户名"
                name="username"
                rules={[{ required: true, message: '请输入用户名' }]}
              >
                <Input placeholder="输入用户名" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="密码"
                name="password"
                rules={[{ required: !editingRegistry, message: '请输入密码' }]}
              >
                <Password placeholder="输入密码" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="项目名称"
                name="project_name"
                tooltip="Harbor等私有仓库的项目名称，如果为空则直接使用镜像名"
              >
                <Input placeholder="项目名称（可选）" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="描述" name="description">
            <TextArea rows={3} placeholder="注册表描述信息" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DockerRegistrySettings;
