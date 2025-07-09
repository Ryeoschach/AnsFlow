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
  Divider,
  Alert,
  Row,
  Col,
  Statistic
} from 'antd';
import {
  ClusterOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  LinkOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  DatabaseOutlined
} from '@ant-design/icons';

const { Text } = Typography;
const { TextArea } = Input;

interface KubernetesCluster {
  id: number;
  name: string;
  endpoint: string;
  description?: string;
  provider?: string;
  version?: string;
  status: 'connected' | 'disconnected' | 'error';
  config_type: 'kubeconfig' | 'token' | 'certificate';
  tls_verify: boolean;
  created_at: string;
}

interface KubernetesNamespace {
  id: number;
  name: string;
  cluster_id: number;
  cluster_name: string;
  description?: string;
  status: 'active' | 'terminating';
  created_at: string;
}

const KubernetesSettings: React.FC = () => {
  const [clusters, setClusters] = useState<KubernetesCluster[]>([]);
  const [namespaces, setNamespaces] = useState<KubernetesNamespace[]>([]);
  const [loading, setLoading] = useState(false);
  const [clusterModalVisible, setClusterModalVisible] = useState(false);
  const [namespaceModalVisible, setNamespaceModalVisible] = useState(false);
  const [editingCluster, setEditingCluster] = useState<KubernetesCluster | null>(null);
  const [editingNamespace, setEditingNamespace] = useState<KubernetesNamespace | null>(null);
  const [clusterForm] = Form.useForm();
  const [namespaceForm] = Form.useForm();

  useEffect(() => {
    loadMockData();
  }, []);

  const loadMockData = () => {
    const mockClusters: KubernetesCluster[] = [
      {
        id: 1,
        name: '开发集群',
        endpoint: 'https://dev-k8s.example.com',
        description: '开发环境 Kubernetes 集群',
        provider: 'AWS EKS',
        version: 'v1.28.3',
        status: 'connected',
        created_at: '2024-01-15T10:00:00Z',
        config_type: 'kubeconfig',
        tls_verify: true
      },
      {
        id: 2,
        name: '生产集群',
        endpoint: 'https://prod-k8s.example.com',
        description: '生产环境 Kubernetes 集群',
        provider: 'Azure AKS',
        version: 'v1.28.5',
        status: 'connected',
        created_at: '2024-01-10T08:00:00Z',
        config_type: 'token',
        tls_verify: true
      }
    ];

    const mockNamespaces: KubernetesNamespace[] = [
      {
        id: 1,
        name: 'default',
        cluster_id: 1,
        cluster_name: '开发集群',
        description: '默认命名空间',
        status: 'active',
        created_at: '2024-01-15T10:00:00Z'
      },
      {
        id: 2,
        name: 'development',
        cluster_id: 1,
        cluster_name: '开发集群',
        description: '开发环境命名空间',
        status: 'active',
        created_at: '2024-01-15T10:30:00Z'
      },
      {
        id: 3,
        name: 'production',
        cluster_id: 2,
        cluster_name: '生产集群',
        description: '生产环境命名空间',
        status: 'active',
        created_at: '2024-01-10T08:30:00Z'
      }
    ];

    setClusters(mockClusters);
    setNamespaces(mockNamespaces);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
      case 'active':
        return 'success';
      case 'disconnected':
      case 'terminating':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
      case 'active':
        return <CheckCircleOutlined />;
      case 'disconnected':
        return <ExclamationCircleOutlined />;
      case 'error':
        return <CloseCircleOutlined />;
      default:
        return null;
    }
  };

  const handleAddCluster = () => {
    setEditingCluster(null);
    clusterForm.resetFields();
    setClusterModalVisible(true);
  };

  const handleEditCluster = (cluster: KubernetesCluster) => {
    setEditingCluster(cluster);
    clusterForm.setFieldsValue(cluster);
    setClusterModalVisible(true);
  };

  const handleDeleteCluster = async (clusterId: number) => {
    try {
      setClusters(clusters.filter(c => c.id !== clusterId));
      setNamespaces(namespaces.filter(ns => ns.cluster_id !== clusterId));
      message.success('集群删除成功');
    } catch (error) {
      message.error('删除集群失败');
    }
  };

  const handleClusterSubmit = async () => {
    try {
      const values = await clusterForm.validateFields();
      
      if (editingCluster) {
        const updatedClusters = clusters.map(c => 
          c.id === editingCluster.id 
            ? { ...c, ...values }
            : c
        );
        setClusters(updatedClusters);
        message.success('集群更新成功');
      } else {
        const newCluster: KubernetesCluster = {
          id: Date.now(),
          ...values,
          status: 'disconnected',
          created_at: new Date().toISOString()
        };
        setClusters([...clusters, newCluster]);
        message.success('集群添加成功');
      }
      
      setClusterModalVisible(false);
    } catch (error) {
      message.error('保存集群失败');
    }
  };

  const handleTestConnection = async (cluster: KubernetesCluster) => {
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const updatedClusters = clusters.map(c => 
        c.id === cluster.id 
          ? { ...c, status: 'connected' as const }
          : c
      );
      setClusters(updatedClusters);
      message.success('连接测试成功');
    } catch (error) {
      message.error('连接测试失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAddNamespace = () => {
    setEditingNamespace(null);
    namespaceForm.resetFields();
    setNamespaceModalVisible(true);
  };

  const handleEditNamespace = (namespace: KubernetesNamespace) => {
    setEditingNamespace(namespace);
    namespaceForm.setFieldsValue(namespace);
    setNamespaceModalVisible(true);
  };

  const handleDeleteNamespace = async (namespaceId: number) => {
    try {
      setNamespaces(namespaces.filter(ns => ns.id !== namespaceId));
      message.success('命名空间删除成功');
    } catch (error) {
      message.error('删除命名空间失败');
    }
  };

  const handleNamespaceSubmit = async () => {
    try {
      const values = await namespaceForm.validateFields();
      
      if (editingNamespace) {
        const updatedNamespaces = namespaces.map(ns => 
          ns.id === editingNamespace.id 
            ? { ...ns, ...values }
            : ns
        );
        setNamespaces(updatedNamespaces);
        message.success('命名空间更新成功');
      } else {
        const selectedCluster = clusters.find(c => c.id === values.cluster_id);
        const newNamespace: KubernetesNamespace = {
          id: Date.now(),
          ...values,
          cluster_name: selectedCluster?.name || '',
          status: 'active',
          created_at: new Date().toISOString()
        };
        setNamespaces([...namespaces, newNamespace]);
        message.success('命名空间添加成功');
      }
      
      setNamespaceModalVisible(false);
    } catch (error) {
      message.error('保存命名空间失败');
    }
  };

  const clusterColumns = [
    {
      title: '集群名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: KubernetesCluster) => (
        <Space>
          <ClusterOutlined />
          <strong>{text}</strong>
          <Tag color={getStatusColor(record.status)}>
            {getStatusIcon(record.status)}
            {record.status}
          </Tag>
        </Space>
      )
    },
    {
      title: '端点地址',
      dataIndex: 'endpoint',
      key: 'endpoint',
      render: (text: string) => (
        <Text code copyable={{ text }}>{text}</Text>
      )
    },
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
      render: (text: string) => text || '-'
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: KubernetesCluster) => (
        <Space>
          <Tooltip title="测试连接">
            <Button
              size="small"
              icon={<LinkOutlined />}
              onClick={() => handleTestConnection(record)}
              loading={loading}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEditCluster(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这个集群吗？"
              onConfirm={() => handleDeleteCluster(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      )
    }
  ];

  const namespaceColumns = [
    {
      title: '命名空间',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: KubernetesNamespace) => (
        <Space>
          <DatabaseOutlined />
          <strong>{text}</strong>
          <Tag color={getStatusColor(record.status)}>{record.status}</Tag>
        </Space>
      )
    },
    {
      title: '所属集群',
      dataIndex: 'cluster_name',
      key: 'cluster_name',
      render: (text: string) => (
        <Tag color="blue">{text}</Tag>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      render: (text: string) => text || '-'
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: KubernetesNamespace) => (
        <Space>
          <Tooltip title="编辑">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEditNamespace(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这个命名空间吗？"
              onConfirm={() => handleDeleteNamespace(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      )
    }
  ];

  const connectedClusters = clusters.filter(c => c.status === 'connected').length;
  const activeNamespaces = namespaces.filter(ns => ns.status === 'active').length;

  return (
    <div>
      <Alert
        message="Kubernetes 集群配置"
        description="管理 Kubernetes 集群连接和命名空间配置，这些配置将用于流水线中的 K8s 步骤。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card>
            <Statistic
              title="已连接集群"
              value={connectedClusters}
              suffix={`/ ${clusters.length}`}
              valueStyle={{ color: '#3f8600' }}
              prefix={<ClusterOutlined />}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Statistic
              title="活跃命名空间"
              value={activeNamespaces}
              valueStyle={{ color: '#722ed1' }}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="Kubernetes 集群"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAddCluster}
          >
            添加集群
          </Button>
        }
        style={{ marginBottom: 16 }}
      >
        <Table
          columns={clusterColumns}
          dataSource={clusters}
          rowKey="id"
          size="small"
          pagination={false}
        />
      </Card>

      <Card
        title="命名空间"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAddNamespace}
          >
            添加命名空间
          </Button>
        }
      >
        <Table
          columns={namespaceColumns}
          dataSource={namespaces}
          rowKey="id"
          size="small"
          pagination={false}
        />
      </Card>

      {/* 集群配置模态框 */}
      <Modal
        title={editingCluster ? '编辑集群' : '添加集群'}
        open={clusterModalVisible}
        onOk={handleClusterSubmit}
        onCancel={() => setClusterModalVisible(false)}
        width={720}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={clusterForm}
          layout="vertical"
          initialValues={{
            config_type: 'kubeconfig',
            tls_verify: true
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="集群名称"
                name="name"
                rules={[{ required: true, message: '请输入集群名称' }]}
              >
                <Input placeholder="输入集群名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="端点地址"
                name="endpoint"
                rules={[{ required: true, message: '请输入端点地址' }]}
              >
                <Input placeholder="https://cluster.example.com" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label="提供商" name="provider">
                <Select placeholder="选择提供商">
                  <Select.Option value="AWS EKS">AWS EKS</Select.Option>
                  <Select.Option value="Azure AKS">Azure AKS</Select.Option>
                  <Select.Option value="Google GKE">Google GKE</Select.Option>
                  <Select.Option value="Self-managed">自建集群</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="版本" name="version">
                <Input placeholder="v1.28.3" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="认证方式" name="config_type">
                <Select>
                  <Select.Option value="kubeconfig">Kubeconfig</Select.Option>
                  <Select.Option value="token">Token</Select.Option>
                  <Select.Option value="certificate">证书</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="描述" name="description">
            <TextArea rows={2} placeholder="集群描述信息" />
          </Form.Item>

          <Form.Item label="启用 TLS 验证" name="tls_verify" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      {/* 命名空间配置模态框 */}
      <Modal
        title={editingNamespace ? '编辑命名空间' : '添加命名空间'}
        open={namespaceModalVisible}
        onOk={handleNamespaceSubmit}
        onCancel={() => setNamespaceModalVisible(false)}
        okText="保存"
        cancelText="取消"
      >
        <Form form={namespaceForm} layout="vertical">
          <Form.Item
            label="命名空间名称"
            name="name"
            rules={[{ required: true, message: '请输入命名空间名称' }]}
          >
            <Input placeholder="输入命名空间名称" />
          </Form.Item>

          <Form.Item
            label="所属集群"
            name="cluster_id"
            rules={[{ required: true, message: '请选择所属集群' }]}
          >
            <Select placeholder="选择集群">
              {clusters
                .filter(c => c.status === 'connected')
                .map(cluster => (
                  <Select.Option key={cluster.id} value={cluster.id}>
                    {cluster.name}
                  </Select.Option>
                ))
              }
            </Select>
          </Form.Item>

          <Form.Item label="描述" name="description">
            <TextArea rows={3} placeholder="命名空间描述信息" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default KubernetesSettings;
