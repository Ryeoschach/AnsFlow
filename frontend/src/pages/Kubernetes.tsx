import React, { useState, useEffect } from 'react';
import {
  Card,
  Tabs,
  Row,
  Col,
  Statistic,
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
  Progress,
  Divider,
  Badge,
  Switch,
  InputNumber,
  Alert,
  Upload,
  Descriptions,
  Timeline,
  List
} from 'antd';
import {
  CloudServerOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  MonitorOutlined,
  SettingOutlined,
  EyeOutlined,
  DatabaseOutlined,
  NodeIndexOutlined,
  ClusterOutlined,
  ContainerOutlined,
  FileTextOutlined,
  LinkOutlined,
  DisconnectOutlined,
  SafetyCertificateOutlined,
  ApiOutlined
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;

// 类型定义
interface KubernetesCluster {
  id: number;
  name: string;
  endpoint: string;
  description?: string;
  region?: string;
  provider?: string;
  version?: string;
  status: 'connected' | 'disconnected' | 'error';
  node_count?: number;
  created_at: string;
  updated_at: string;
  config_type: 'kubeconfig' | 'token' | 'certificate';
  tls_verify: boolean;
  ca_cert?: string;
  client_cert?: string;
  client_key?: string;
  token?: string;
  username?: string;
  password?: string;
}

interface KubernetesNamespace {
  id: number;
  name: string;
  cluster_id: number;
  cluster_name: string;
  description?: string;
  status: 'active' | 'terminating';
  resource_quota?: any;
  created_at: string;
}

interface KubernetesResource {
  id: number;
  cluster_id: number;
  namespace: string;
  kind: string;
  name: string;
  status: string;
  created_at: string;
}

const KubernetesPage: React.FC = () => {
  const [clusters, setClusters] = useState<KubernetesCluster[]>([]);
  const [namespaces, setNamespaces] = useState<KubernetesNamespace[]>([]);
  const [resources, setResources] = useState<KubernetesResource[]>([]);
  const [loading, setLoading] = useState(false);
  const [clusterModalVisible, setClusterModalVisible] = useState(false);
  const [namespaceModalVisible, setNamespaceModalVisible] = useState(false);
  const [editingCluster, setEditingCluster] = useState<KubernetesCluster | null>(null);
  const [editingNamespace, setEditingNamespace] = useState<KubernetesNamespace | null>(null);
  const [clusterForm] = Form.useForm();
  const [namespaceForm] = Form.useForm();
  const [activeTab, setActiveTab] = useState('clusters');

  // 模拟数据
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
        region: 'us-west-1',
        provider: 'AWS EKS',
        version: 'v1.28.3',
        status: 'connected',
        node_count: 3,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-20T15:30:00Z',
        config_type: 'kubeconfig',
        tls_verify: true
      },
      {
        id: 2,
        name: '生产集群',
        endpoint: 'https://prod-k8s.example.com',
        description: '生产环境 Kubernetes 集群',
        region: 'us-east-1',
        provider: 'Azure AKS',
        version: 'v1.28.5',
        status: 'connected',
        node_count: 8,
        created_at: '2024-01-10T08:00:00Z',
        updated_at: '2024-01-20T12:15:00Z',
        config_type: 'token',
        tls_verify: true
      },
      {
        id: 3,
        name: '测试集群',
        endpoint: 'https://test-k8s.example.com',
        description: '测试环境 Kubernetes 集群',
        region: 'us-central-1',
        provider: 'Google GKE',
        version: 'v1.27.8',
        status: 'error',
        node_count: 2,
        created_at: '2024-01-05T14:00:00Z',
        updated_at: '2024-01-18T09:45:00Z',
        config_type: 'certificate',
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
      },
      {
        id: 4,
        name: 'monitoring',
        cluster_id: 2,
        cluster_name: '生产集群',
        description: '监控服务命名空间',
        status: 'active',
        created_at: '2024-01-10T09:00:00Z'
      }
    ];

    const mockResources: KubernetesResource[] = [
      {
        id: 1,
        cluster_id: 1,
        namespace: 'development',
        kind: 'Deployment',
        name: 'web-app',
        status: 'Running',
        created_at: '2024-01-16T10:00:00Z'
      },
      {
        id: 2,
        cluster_id: 1,
        namespace: 'development',
        kind: 'Service',
        name: 'web-app-service',
        status: 'Active',
        created_at: '2024-01-16T10:05:00Z'
      },
      {
        id: 3,
        cluster_id: 2,
        namespace: 'production',
        kind: 'Deployment',
        name: 'api-server',
        status: 'Running',
        created_at: '2024-01-11T14:00:00Z'
      }
    ];

    setClusters(mockClusters);
    setNamespaces(mockNamespaces);
    setResources(mockResources);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
      case 'active':
      case 'Running':
      case 'Active':
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

  // 集群管理函数
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
        // 更新集群
        const updatedClusters = clusters.map(c => 
          c.id === editingCluster.id 
            ? { ...c, ...values, updated_at: new Date().toISOString() }
            : c
        );
        setClusters(updatedClusters);
        message.success('集群更新成功');
      } else {
        // 添加新集群
        const newCluster: KubernetesCluster = {
          id: Date.now(),
          ...values,
          status: 'disconnected',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
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
      // 模拟连接测试
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const updatedClusters = clusters.map(c => 
        c.id === cluster.id 
          ? { ...c, status: 'connected' as const, updated_at: new Date().toISOString() }
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

  // 命名空间管理函数
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
        // 更新命名空间
        const updatedNamespaces = namespaces.map(ns => 
          ns.id === editingNamespace.id 
            ? { ...ns, ...values }
            : ns
        );
        setNamespaces(updatedNamespaces);
        message.success('命名空间更新成功');
      } else {
        // 添加新命名空间
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

  // 集群表格列定义
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
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      render: (text: string) => (
        <Tag color="blue">{text || '-'}</Tag>
      )
    },
    {
      title: '节点数',
      dataIndex: 'node_count',
      key: 'node_count',
      render: (count: number) => (
        <Badge count={count} color="green" />
      )
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
      render: (_text: any, record: KubernetesCluster) => (
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

  // 命名空间表格列定义
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
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleString()
    },
    {
      title: '操作',
      key: 'actions',
      render: (_text: any, record: KubernetesNamespace) => (
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

  // 资源表格列定义
  const resourceColumns = [
    {
      title: '资源类型',
      dataIndex: 'kind',
      key: 'kind',
      render: (text: string) => (
        <Tag color="purple">{text}</Tag>
      )
    },
    {
      title: '资源名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => (
        <Space>
          <ContainerOutlined />
          <strong>{text}</strong>
        </Space>
      )
    },
    {
      title: '命名空间',
      dataIndex: 'namespace',
      key: 'namespace'
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (text: string) => (
        <Tag color={getStatusColor(text)}>{text}</Tag>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleString()
    }
  ];

  // 统计数据
  const connectedClusters = clusters.filter(c => c.status === 'connected').length;
  const totalNodes = clusters.reduce((sum, c) => sum + (c.node_count || 0), 0);
  const activeNamespaces = namespaces.filter(ns => ns.status === 'active').length;
  const totalResources = resources.length;

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <CloudServerOutlined /> Kubernetes 管理
      </Title>
      <Paragraph type="secondary">
        管理 Kubernetes 集群、命名空间和资源配置
      </Paragraph>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
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
        <Col span={6}>
          <Card>
            <Statistic
              title="总节点数"
              value={totalNodes}
              valueStyle={{ color: '#1890ff' }}
              prefix={<NodeIndexOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃命名空间"
              value={activeNamespaces}
              valueStyle={{ color: '#722ed1' }}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总资源数"
              value={totalResources}
              valueStyle={{ color: '#eb2f96' }}
              prefix={<ContainerOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="集群管理" key="clusters">
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
          >
            <Table
              columns={clusterColumns}
              dataSource={clusters}
              rowKey="id"
              size="small"
            />
          </Card>
        </TabPane>

        <TabPane tab="命名空间" key="namespaces">
          <Card
            title="命名空间管理"
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
            />
          </Card>
        </TabPane>

        <TabPane tab="资源监控" key="resources">
          <Card title="集群资源">
            <Table
              columns={resourceColumns}
              dataSource={resources}
              rowKey="id"
              size="small"
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* 添加/编辑集群模态框 */}
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
              <Form.Item label="区域" name="region">
                <Input placeholder="us-west-1" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="版本" name="version">
                <Input placeholder="v1.28.3" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="描述" name="description">
            <TextArea rows={2} placeholder="集群描述信息" />
          </Form.Item>

          <Divider>认证配置</Divider>

          <Form.Item label="认证方式" name="config_type">
            <Select>
              <Select.Option value="kubeconfig">Kubeconfig 文件</Select.Option>
              <Select.Option value="token">Token 认证</Select.Option>
              <Select.Option value="certificate">证书认证</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item label="启用 TLS 验证" name="tls_verify" valuePropName="checked">
            <Switch />
          </Form.Item>

          <Form.Item shouldUpdate={(prevValues, currentValues) => 
            prevValues.config_type !== currentValues.config_type
          }>
            {({ getFieldValue }) => {
              const configType = getFieldValue('config_type');
              
              if (configType === 'token') {
                return (
                  <Form.Item label="Token" name="token">
                    <TextArea rows={3} placeholder="输入访问令牌" />
                  </Form.Item>
                );
              }
              
              if (configType === 'certificate') {
                return (
                  <>
                    <Form.Item label="CA 证书" name="ca_cert">
                      <TextArea rows={3} placeholder="CA 证书内容" />
                    </Form.Item>
                    <Form.Item label="客户端证书" name="client_cert">
                      <TextArea rows={3} placeholder="客户端证书内容" />
                    </Form.Item>
                    <Form.Item label="客户端密钥" name="client_key">
                      <TextArea rows={3} placeholder="客户端密钥内容" />
                    </Form.Item>
                  </>
                );
              }
              
              return null;
            }}
          </Form.Item>
        </Form>
      </Modal>

      {/* 添加/编辑命名空间模态框 */}
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

export default KubernetesPage;
