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
  Switch,
  Alert,
  Spin,
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
  DatabaseOutlined,
  NodeIndexOutlined,
  ClusterOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import { apiService } from '../services/api';
import { KubernetesCluster, KubernetesNamespace } from '../types';

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

const KubernetesPage: React.FC = () => {
  const [clusters, setClusters] = useState<KubernetesCluster[]>([]);
  const [namespaces, setNamespaces] = useState<KubernetesNamespace[]>([]);
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [clusterModalVisible, setClusterModalVisible] = useState(false);
  const [namespaceModalVisible, setNamespaceModalVisible] = useState(false);
  const [editingCluster, setEditingCluster] = useState<KubernetesCluster | null>(null);
  const [editingNamespace, setEditingNamespace] = useState<KubernetesNamespace | null>(null);
  const [clusterForm] = Form.useForm();
  const [namespaceForm] = Form.useForm();
  const [activeTab, setActiveTab] = useState('clusters');

  useEffect(() => {
    loadClusters();
    loadNamespaces();
  }, []);

  const loadClusters = async () => {
    try {
      setLoading(true);
      const data = await apiService.getKubernetesClusters();
      console.log('API返回的集群数据:', data);
      console.log('集群数量:', data.length);
      setClusters(data);
    } catch (error: any) {
      console.error('Failed to load clusters:', error);
      if (error.response?.status === 401) {
        message.error('请先登录系统');
        // 可以在这里跳转到登录页面
        // window.location.href = '/login';
      } else {
        message.error('加载集群列表失败');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadNamespaces = async () => {
    try {
      const data = await apiService.getKubernetesNamespaces();
      setNamespaces(data);
    } catch (error: any) {
      console.error('Failed to load namespaces:', error);
      if (error.response?.status === 401) {
        message.error('请先登录系统');
      } else {
        message.error('加载命名空间失败');
      }
    }
  };

  const validateConnection = async (values: any) => {
    try {
      setValidating(true);
      const result = await apiService.validateKubernetesConnection(values);
      if (result.valid) {
        message.success(`集群连接验证成功！Kubernetes 版本: ${result.cluster_info?.version || '未知'}`);
        return true;
      } else {
        message.error(`连接验证失败: ${result.message}`);
        return false;
      }
    } catch (error) {
      console.error('Connection validation failed:', error);
      message.error('连接验证失败');
      return false;
    } finally {
      setValidating(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
      case 'active':
        return 'success';
      case 'disconnected':
      case 'inactive':
        return 'warning';
      case 'error':
        return 'error';
      case 'connecting':
        return 'processing';
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
      case 'inactive':
        return <ExclamationCircleOutlined />;
      case 'error':
        return <CloseCircleOutlined />;
      case 'connecting':
        return <LoadingOutlined />;
      default:
        return null;
    }
  };

  // 集群管理函数
  const handleAddCluster = () => {
    setEditingCluster(null);
    clusterForm.resetFields();
    // 设置默认值
    clusterForm.setFieldsValue({
      cluster_type: 'standard',
      auth_config: {
        type: 'token'
      },
      is_default: false
    });
    setClusterModalVisible(true);
  };

  const handleEditCluster = (cluster: KubernetesCluster) => {
    setEditingCluster(cluster);
    clusterForm.setFieldsValue({
      name: cluster.name,
      description: cluster.description,
      cluster_type: cluster.cluster_type,
      api_server: cluster.api_server,
      auth_config: {
        type: cluster.auth_config?.type || 'token',
        ...cluster.auth_config
      },
      is_default: cluster.is_default
    });
    setClusterModalVisible(true);
  };

  const handleDeleteCluster = async (clusterId: number) => {
    try {
      await apiService.deleteKubernetesCluster(clusterId);
      await loadClusters();
      await loadNamespaces();
      message.success('集群删除成功');
    } catch (error) {
      console.error('Failed to delete cluster:', error);
      message.error('删除集群失败');
    }
  };

  const handleClusterSubmit = async () => {
    try {
      const values = await clusterForm.validateFields();
      
      // 验证连接
      const isValid = await validateConnection(values);
      if (!isValid) {
        return;
      }

      if (editingCluster) {
        // 更新集群
        await apiService.updateKubernetesCluster(editingCluster.id, values);
        message.success('集群更新成功');
      } else {
        // 创建新集群
        await apiService.createKubernetesCluster(values);
        message.success('集群创建成功');
      }
      
      setClusterModalVisible(false);
      clusterForm.resetFields();
      await loadClusters();
    } catch (error) {
      console.error('Failed to save cluster:', error);
      message.error(editingCluster ? '更新集群失败' : '创建集群失败');
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
      await apiService.deleteKubernetesNamespace(namespaceId);
      await loadNamespaces();
      message.success('命名空间删除成功');
    } catch (error) {
      console.error('Failed to delete namespace:', error);
      message.error('删除命名空间失败');
    }
  };

  const handleNamespaceSubmit = async () => {
    try {
      const values = await namespaceForm.validateFields();
      
      if (editingNamespace) {
        // 更新命名空间
        await apiService.updateKubernetesNamespace(editingNamespace.id, values);
        message.success('命名空间更新成功');
      } else {
        // 创建新命名空间
        await apiService.createKubernetesNamespace(values);
        message.success('命名空间创建成功');
      }
      
      setNamespaceModalVisible(false);
      namespaceForm.resetFields();
      await loadNamespaces();
    } catch (error) {
      console.error('Failed to save namespace:', error);
      message.error(editingNamespace ? '更新命名空间失败' : '创建命名空间失败');
    }
  };

  // 刷新集群状态
  const handleRefreshCluster = async (clusterId: number) => {
    try {
      await apiService.checkKubernetesClusterConnection(clusterId);
      await loadClusters();
      message.success('集群状态刷新成功');
    } catch (error) {
      console.error('Failed to refresh cluster:', error);
      message.error('刷新集群状态失败');
    }
  };

  // 集群表格列定义
  const clusterColumns = [
    {
      title: '集群名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: KubernetesCluster) => (
        <Space>
          <ClusterOutlined />
          <span>{name}</span>
          {record.is_default && <Tag color="blue">默认</Tag>}
        </Space>
      ),
    },
    {
      title: 'API 服务器',
      dataIndex: 'api_server',
      key: 'api_server',
      render: (url: string) => (
        <Tooltip title={url}>
          <Text code copyable ellipsis style={{ maxWidth: 200 }}>
            {url}
          </Text>
        </Tooltip>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Space>
          {getStatusIcon(status)}
          <Tag color={getStatusColor(status)}>{status}</Tag>
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: KubernetesCluster) => (
        <Space>
          <Tooltip title="刷新状态">
            <Button
              type="text"
              icon={<ReloadOutlined />}
              onClick={() => handleRefreshCluster(record.id)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEditCluster(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除此集群吗？"
            onConfirm={() => handleDeleteCluster(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 命名空间表格列定义
  const namespaceColumns = [
    {
      title: '命名空间名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <Space>
          <DatabaseOutlined />
          <span>{name}</span>
        </Space>
      ),
    },
    {
      title: '所属集群',
      dataIndex: 'cluster_name',
      key: 'cluster_name',
      render: (clusterName: string) => clusterName || '未知',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Space>
          {getStatusIcon(status)}
          <Tag color={getStatusColor(status)}>{status}</Tag>
        </Space>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: KubernetesNamespace) => (
        <Space>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEditNamespace(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除此命名空间吗？"
            onConfirm={() => handleDeleteNamespace(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            <ClusterOutlined style={{ marginRight: '8px' }} />
            Kubernetes 管理
          </Title>
          <Paragraph type="secondary" style={{ margin: '4px 0 0 0' }}>
            管理 Kubernetes 集群和命名空间，支持多种认证方式
          </Paragraph>
        </div>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAddCluster}
          >
            添加集群
          </Button>
        </Space>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总集群数"
              value={clusters.length}
              prefix={<ClusterOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总集群数"
              value={clusters.length}
              prefix={<ClusterOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已连接集群"
              value={clusters.filter(c => c.status === 'active' || c.status === 'connected').length}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="命名空间数"
              value={namespaces.length}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃命名空间"
              value={namespaces.filter(ns => ns.status === 'active').length}
              prefix={<NodeIndexOutlined />}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要内容 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <Tabs.TabPane tab="集群管理" key="clusters">
            <div style={{ marginBottom: '16px' }}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleAddCluster}
              >
                添加集群
              </Button>
            </div>
            <Table
              columns={clusterColumns}
              dataSource={clusters}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 个集群`,
              }}
            />
          </Tabs.TabPane>

          <Tabs.TabPane tab="命名空间管理" key="namespaces">
            <div style={{ marginBottom: '16px' }}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleAddNamespace}
                disabled={clusters.length === 0}
              >
                添加命名空间
              </Button>
              {clusters.length === 0 && (
                <Alert
                  message="请先添加至少一个集群"
                  type="warning"
                  style={{ marginTop: '8px' }}
                />
              )}
            </div>
            <Table
              columns={namespaceColumns}
              dataSource={namespaces}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 个命名空间`,
              }}
            />
          </Tabs.TabPane>
        </Tabs>
      </Card>

      {/* 集群模态框 */}
      <Modal
        title={editingCluster ? '编辑集群' : '添加集群'}
        open={clusterModalVisible}
        onOk={handleClusterSubmit}
        onCancel={() => {
          setClusterModalVisible(false);
          clusterForm.resetFields();
        }}
        width={600}
        confirmLoading={validating}
        okText={validating ? '验证连接中...' : '确定'}
      >
        <Form
          form={clusterForm}
          layout="vertical"
          preserve={false}
        >
          <Form.Item
            name="name"
            label="集群名称"
            rules={[{ required: true, message: '请输入集群名称' }]}
          >
            <Input placeholder="输入集群名称" />
          </Form.Item>

          <Form.Item
            name="api_server"
            label="API 服务器地址"
            rules={[
              { required: true, message: '请输入 API 服务器地址' },
              { type: 'url', message: '请输入有效的 URL' }
            ]}
          >
            <Input placeholder="https://your-k8s-api-server:6443" />
          </Form.Item>

          <Form.Item
            name="cluster_type"
            label="集群类型"
            rules={[{ required: true, message: '请选择集群类型' }]}
            initialValue="standard"
          >
            <Select placeholder="选择集群类型">
              <Select.Option value="standard">标准集群</Select.Option>
              <Select.Option value="development">开发集群</Select.Option>
              <Select.Option value="testing">测试集群</Select.Option>
              <Select.Option value="production">生产集群</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea
              placeholder="输入集群描述"
              rows={3}
            />
          </Form.Item>

          <Form.Item
            name={['auth_config', 'type']}
            label="认证方式"
            rules={[{ required: true, message: '请选择认证方式' }]}
          >
            <Select placeholder="选择认证方式">
              <Select.Option value="token">Bearer Token</Select.Option>
              <Select.Option value="kubeconfig">Kubeconfig 文件</Select.Option>
              <Select.Option value="certificate">客户端证书</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues?.auth_config?.type !== currentValues?.auth_config?.type
            }
          >
            {({ getFieldValue }) => {
              const authType = getFieldValue(['auth_config', 'type']);
              
              if (authType === 'token') {
                return (
                  <Form.Item
                    name={['auth_config', 'token']}
                    label="Bearer Token"
                    rules={[{ required: true, message: '请输入 Bearer Token' }]}
                  >
                    <TextArea
                      placeholder="输入 Bearer Token"
                      rows={3}
                    />
                  </Form.Item>
                );
              }
              
              if (authType === 'kubeconfig') {
                return (
                  <Form.Item
                    name={['auth_config', 'kubeconfig']}
                    label="Kubeconfig 内容"
                    rules={[{ required: true, message: '请输入 Kubeconfig 内容' }]}
                  >
                    <TextArea
                      placeholder="粘贴 kubeconfig 文件内容"
                      rows={6}
                    />
                  </Form.Item>
                );
              }
              
              if (authType === 'certificate') {
                return (
                  <>
                    <Form.Item
                      name={['auth_config', 'client_cert']}
                      label="客户端证书"
                      rules={[{ required: true, message: '请输入客户端证书' }]}
                    >
                      <TextArea
                        placeholder="输入客户端证书内容"
                        rows={4}
                      />
                    </Form.Item>
                    <Form.Item
                      name={['auth_config', 'client_key']}
                      label="客户端密钥"
                      rules={[{ required: true, message: '请输入客户端密钥' }]}
                    >
                      <TextArea
                        placeholder="输入客户端密钥内容"
                        rows={4}
                      />
                    </Form.Item>
                    <Form.Item
                      name={['auth_config', 'ca_cert']}
                      label="CA 证书"
                    >
                      <TextArea
                        placeholder="输入 CA 证书内容（可选）"
                        rows={4}
                      />
                    </Form.Item>
                  </>
                );
              }
              
              return null;
            }}
          </Form.Item>

          <Form.Item
            name="is_default"
            valuePropName="checked"
          >
            <Switch checkedChildren="默认集群" unCheckedChildren="普通集群" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 命名空间模态框 */}
      <Modal
        title={editingNamespace ? '编辑命名空间' : '添加命名空间'}
        open={namespaceModalVisible}
        onOk={handleNamespaceSubmit}
        onCancel={() => {
          setNamespaceModalVisible(false);
          namespaceForm.resetFields();
        }}
        width={500}
      >
        <Form
          form={namespaceForm}
          layout="vertical"
          preserve={false}
        >
          <Form.Item
            name="name"
            label="命名空间名称"
            rules={[
              { required: true, message: '请输入命名空间名称' },
              { pattern: /^[a-z0-9]([-a-z0-9]*[a-z0-9])?$/, message: '名称只能包含小写字母、数字和连字符，且不能以连字符开头或结尾' }
            ]}
          >
            <Input placeholder="输入命名空间名称" />
          </Form.Item>

          <Form.Item
            name="cluster"
            label="所属集群"
            rules={[{ required: true, message: '请选择所属集群' }]}
          >
            <Select
              placeholder="选择集群"
              showSearch
              optionFilterProp="children"
            >
              {clusters
                .filter(cluster => cluster.status === 'active' || cluster.status === 'connected')
                .map(cluster => (
                  <Select.Option key={cluster.id} value={cluster.id}>
                    {cluster.name}
                  </Select.Option>
                ))
              }
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default KubernetesPage;
