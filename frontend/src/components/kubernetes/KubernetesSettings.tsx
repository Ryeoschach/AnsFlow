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
  Divider,
  Alert,
  Row,
  Col,
  Statistic,
  Tabs,
  Descriptions,
  Badge
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
  DatabaseOutlined,
  SyncOutlined,
  EyeOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { apiService } from '../../services/api';
import { KubernetesCluster, KubernetesNamespace } from '../../types';

const { Text } = Typography;
const { TextArea } = Input;
const { TabPane } = Tabs;

const KubernetesSettings: React.FC = () => {
  const [clusters, setClusters] = useState<KubernetesCluster[]>([]);
  const [namespaces, setNamespaces] = useState<KubernetesNamespace[]>([]);
  const [loading, setLoading] = useState(false);
  const [clusterModalVisible, setClusterModalVisible] = useState(false);
  const [namespaceModalVisible, setNamespaceModalVisible] = useState(false);
  const [namespaceDetailModalVisible, setNamespaceDetailModalVisible] = useState(false);
  const [clusterDetailModalVisible, setClusterDetailModalVisible] = useState(false);
  const [editingCluster, setEditingCluster] = useState<KubernetesCluster | null>(null);
  const [editingNamespace, setEditingNamespace] = useState<KubernetesNamespace | null>(null);
  const [selectedNamespace, setSelectedNamespace] = useState<any>(null);
  const [selectedCluster, setSelectedCluster] = useState<KubernetesCluster | null>(null);
  const [namespaceResources, setNamespaceResources] = useState<any>(null);
  const [clusterStats, setClusterStats] = useState<any>(null);
  const [loadingClusterStats, setLoadingClusterStats] = useState(false);
  const [clusterForm] = Form.useForm();
  const [namespaceForm] = Form.useForm();

  useEffect(() => {
    loadClusters();
    loadNamespaces();
  }, []);

  const loadClusters = async () => {
    try {
      setLoading(true);
      const data = await apiService.getKubernetesClusters();
      console.log('Settings页面获取的集群数据:', data);
      console.log('集群数量:', data.length);
      setClusters(data);
    } catch (error: any) {
      console.error('Failed to load clusters:', error);
      if (error.response?.status === 401) {
        message.error('请先登录系统');
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
    
    // 解析认证配置来设置表单字段
    let authType = 'token';
    let authToken = '';
    
    if (cluster.auth_config) {
      if (cluster.auth_config.token) {
        authType = 'token';
        authToken = cluster.auth_config.token;
      } else if (cluster.auth_config.kubeconfig) {
        authType = 'kubeconfig';
        authToken = cluster.auth_config.kubeconfig;
      } else if (cluster.auth_config.client_cert) {
        authType = 'certificate';
        authToken = cluster.auth_config.client_cert;
      }
    }
    
    clusterForm.setFieldsValue({
      ...cluster,
      auth_type: authType,
      auth_token: authToken
    });
    setClusterModalVisible(true);
  };

  const handleDeleteCluster = async (clusterId: number) => {
    try {
      await apiService.deleteKubernetesCluster(clusterId);
      setClusters(clusters.filter(c => c.id !== clusterId));
      setNamespaces(namespaces.filter(ns => ns.cluster !== clusterId));
      message.success('集群删除成功');
    } catch (error: any) {
      console.error('删除集群失败:', error);
      if (error.response?.status === 401) {
        message.error('请先登录系统');
      } else {
        message.error('删除集群失败: ' + (error.response?.data?.message || error.message));
      }
    }
  };

  const handleClusterSubmit = async () => {
    try {
      const values = await clusterForm.validateFields();
      
      // 构造认证配置对象
      const authConfig: Record<string, any> = {};
      if (values.auth_type === 'token') {
        authConfig.token = values.auth_token;
      } else if (values.auth_type === 'kubeconfig') {
        authConfig.kubeconfig = values.auth_token;
      } else if (values.auth_type === 'certificate') {
        authConfig.client_cert = values.auth_token;
        authConfig.client_key = values.auth_token; // 简化处理
      }

      // 准备提交数据
      const submitData = {
        name: values.name,
        description: values.description || '',
        cluster_type: values.cluster_type || 'k8s',
        api_server: values.api_server,
        auth_config: authConfig,
        kubernetes_version: values.kubernetes_version || '',
        default_namespace: values.default_namespace || 'default',
        is_default: false
      };
      
      if (editingCluster) {
        // 更新现有集群
        const updatedCluster = await apiService.updateKubernetesCluster(editingCluster.id, submitData);
        const updatedClusters = clusters.map(c => 
          c.id === editingCluster.id ? updatedCluster : c
        );
        setClusters(updatedClusters);
        message.success('集群更新成功');
      } else {
        // 创建新集群
        const newCluster = await apiService.createKubernetesCluster(submitData);
        setClusters([...clusters, newCluster]);
        message.success('集群添加成功');
      }
      
      setClusterModalVisible(false);
    } catch (error: any) {
      console.error('保存集群失败:', error);
      if (error.response?.status === 401) {
        message.error('请先登录系统');
      } else {
        message.error('保存集群失败: ' + (error.response?.data?.message || error.message));
      }
    }
  };

  const handleTestConnection = async (cluster: KubernetesCluster) => {
    setLoading(true);
    try {
      // 调用真实的连接测试API
      const result = await apiService.validateKubernetesConnection({
        api_server: cluster.api_server,
        auth_config: cluster.auth_config
      });
      
      if (result.valid) {
        // 连接成功，显示成功信息和集群详情
        const clusterInfo = result.cluster_info;
        let successMessage = '连接测试成功: ' + result.message;
        if (clusterInfo) {
          successMessage += ` (版本: ${clusterInfo.version || 'N/A'}, 节点: ${clusterInfo.ready_nodes || 0}/${clusterInfo.total_nodes || 0})`;
        }
        message.success(successMessage);
        
        // 连接成功后，启动集群状态检查任务来更新数据库中的集群状态
        try {
          await apiService.checkKubernetesClusterConnection(cluster.id);
          // 延迟1秒后重新加载集群数据，让异步任务有时间完成
          setTimeout(async () => {
            await loadClusters();
          }, 1000);
        } catch (error) {
          console.warn('启动集群状态检查任务失败:', error);
        }
      } else {
        // 连接失败，显示错误信息
        message.error('连接测试失败: ' + result.message);
      }
    } catch (error: any) {
      console.error('连接测试失败:', error);
      if (error.response?.status === 401) {
        message.error('请先登录系统');
      } else {
        message.error('连接测试失败: ' + (error.response?.data?.message || error.message));
      }
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
      await apiService.deleteKubernetesNamespace(namespaceId);
      setNamespaces(namespaces.filter(ns => ns.id !== namespaceId));
      message.success('命名空间删除成功');
    } catch (error: any) {
      console.error('删除命名空间失败:', error);
      if (error.response?.status === 401) {
        message.error('请先登录系统');
      } else {
        message.error('删除命名空间失败: ' + (error.response?.data?.message || error.message));
      }
    }
  };

  const handleSyncNamespaces = async () => {
    const activeCluster = clusters.find(c => c.status === 'active' || c.status === 'connected');
    if (!activeCluster) {
      message.warning('没有可用的活跃集群，请先连接一个集群');
      return;
    }

    try {
      setLoading(true);
      await apiService.syncKubernetesClusterResources(activeCluster.id);
      message.success('正在从集群同步命名空间，请稍后刷新查看');
      
      // 延迟3秒后重新加载命名空间数据
      setTimeout(async () => {
        await loadNamespaces();
      }, 3000);
    } catch (error: any) {
      console.error('同步命名空间失败:', error);
      if (error.response?.status === 401) {
        message.error('请先登录系统');
      } else {
        message.error('同步命名空间失败: ' + (error.response?.data?.message || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleViewNamespaceDetail = async (namespace: KubernetesNamespace) => {
    try {
      setLoading(true);
      setSelectedNamespace(namespace);
      
      // 获取命名空间的详细资源信息
      const resources = await apiService.getKubernetesNamespaceResources(namespace.id);
      setNamespaceResources(resources);
      setNamespaceDetailModalVisible(true);
    } catch (error: any) {
      console.error('获取命名空间详情失败:', error);
      if (error.response?.status === 401) {
        message.error('请先登录系统');
      } else {
        message.error('获取命名空间详情失败: ' + (error.response?.data?.message || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleViewClusterDetail = async (cluster: KubernetesCluster) => {
    try {
      setLoading(true);
      setSelectedCluster(cluster);
      setClusterDetailModalVisible(true);
      
      // 获取集群统计信息
      setLoadingClusterStats(true);
      try {
        const statsData = await apiService.getKubernetesClusterInfo(cluster.id);
        setClusterStats(statsData);
      } catch (error) {
        console.error('获取集群统计信息失败:', error);
        setClusterStats({
          cluster_id: cluster.id,
          cluster_name: cluster.name,
          connected: false,
          message: '获取统计信息失败',
          cluster_stats: {
            version: '',
            total_nodes: 0,
            ready_nodes: 0,
            total_pods: 0,
            running_pods: 0,
          }
        });
      } finally {
        setLoadingClusterStats(false);
      }
    } catch (error: any) {
      console.error('显示集群详情失败:', error);
      message.error('显示集群详情失败');
    } finally {
      setLoading(false);
    }
  };

  const handleNamespaceSubmit = async () => {
    try {
      const values = await namespaceForm.validateFields();
      
      if (editingNamespace) {
        // 更新现有命名空间
        const updatedNamespace = await apiService.updateKubernetesNamespace(editingNamespace.id, values);
        const updatedNamespaces = namespaces.map(ns => 
          ns.id === editingNamespace.id ? updatedNamespace : ns
        );
        setNamespaces(updatedNamespaces);
        message.success('命名空间更新成功');
      } else {
        // 创建新命名空间
        const newNamespace = await apiService.createKubernetesNamespace(values);
        setNamespaces([...namespaces, newNamespace]);
        message.success('命名空间添加成功');
      }
      
      setNamespaceModalVisible(false);
    } catch (error: any) {
      console.error('保存命名空间失败:', error);
      if (error.response?.status === 401) {
        message.error('请先登录系统');
      } else {
        message.error('保存命名空间失败: ' + (error.response?.data?.message || error.message));
      }
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
          <Button 
            type="link" 
            style={{ padding: 0, fontWeight: 'bold' }}
            onClick={() => handleViewClusterDetail(record)}
          >
            {text}
          </Button>
          <Tag color={getStatusColor(record.status)}>
            {getStatusIcon(record.status)}
            {record.status}
          </Tag>
        </Space>
      )
    },
    {
      title: '端点地址',
      dataIndex: 'api_server',
      key: 'api_server',
      render: (text: string) => (
        <Text code copyable={{ text }}>{text}</Text>
      )
    },
    {
      title: '集群类型',
      dataIndex: 'cluster_type',
      key: 'cluster_type',
      render: (text: string) => text || '-'
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: KubernetesCluster) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewClusterDetail(record)}
            />
          </Tooltip>
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
          <Tooltip title="查看详情">
            <Button
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewNamespaceDetail(record)}
              loading={loading && selectedNamespace?.id === record.id}
            />
          </Tooltip>
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

  const connectedClusters = clusters.filter(c => c.status === 'active' || c.status === 'connected').length;
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
          <Space>
            <Button
              icon={<SyncOutlined />}
              onClick={handleSyncNamespaces}
              loading={loading}
              type="default"
            >
              从集群同步
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAddNamespace}
            >
              添加命名空间
            </Button>
          </Space>
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
            auth_type: 'token',
            cluster_type: 'k8s',
            default_namespace: 'default'
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
                label="API服务器地址"
                name="api_server"
                rules={[{ required: true, message: '请输入API服务器地址' }]}
              >
                <Input placeholder="https://cluster.example.com" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label="集群类型" name="cluster_type">
                <Select placeholder="选择集群类型">
                  <Select.Option value="eks">AWS EKS</Select.Option>
                  <Select.Option value="aks">Azure AKS</Select.Option>
                  <Select.Option value="gke">Google GKE</Select.Option>
                  <Select.Option value="k8s">标准 Kubernetes</Select.Option>
                  <Select.Option value="rke">Rancher RKE</Select.Option>
                  <Select.Option value="k3s">K3s</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={16}>
              <Form.Item label="Kubernetes版本" name="kubernetes_version">
                <Input placeholder="v1.28.3" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item 
                label="认证方式" 
                name="auth_type"
                rules={[{ required: true, message: '请选择认证方式' }]}
              >
                <Select placeholder="选择认证方式">
                  <Select.Option value="token">Token</Select.Option>
                  <Select.Option value="kubeconfig">Kubeconfig</Select.Option>
                  <Select.Option value="certificate">客户端证书</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={16}>
              <Form.Item label="默认命名空间" name="default_namespace">
                <Input placeholder="default" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item 
            label="认证配置" 
            name="auth_token"
            rules={[{ required: true, message: '请输入认证Token' }]}
          >
            <TextArea 
              rows={4} 
              placeholder="请输入 Kubernetes Token 或 Kubeconfig 内容"
            />
          </Form.Item>

          <Form.Item label="描述" name="description">
            <TextArea rows={2} placeholder="集群描述信息" />
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
            name="cluster"
            rules={[{ required: true, message: '请选择所属集群' }]}
          >
            <Select placeholder="选择集群">
              {clusters
                .filter(c => c.status === 'connected' || c.status === 'active')
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

      {/* 命名空间详情模态框 */}
      <Modal
        title={
          <Space>
            <InfoCircleOutlined />
            命名空间详情: {selectedNamespace?.name}
          </Space>
        }
        open={namespaceDetailModalVisible}
        onCancel={() => {
          setNamespaceDetailModalVisible(false);
          setSelectedNamespace(null);
          setNamespaceResources(null);
        }}
        width={1000}
        footer={[
          <Button 
            key="close" 
            onClick={() => {
              setNamespaceDetailModalVisible(false);
              setSelectedNamespace(null);
              setNamespaceResources(null);
            }}
          >
            关闭
          </Button>
        ]}
      >
        {namespaceResources && (
          <Tabs defaultActiveKey="overview">
            <TabPane tab="概览信息" key="overview">
              <Descriptions bordered size="small" column={2}>
                <Descriptions.Item label="命名空间名称">
                  <Text strong>{namespaceResources.namespace.name}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="所属集群">
                  <Tag color="blue">{namespaceResources.namespace.cluster_name}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Badge 
                    status={getStatusColor(namespaceResources.namespace.status) === 'success' ? 'success' : 'warning'} 
                    text={namespaceResources.namespace.status} 
                  />
                </Descriptions.Item>
                <Descriptions.Item label="创建时间">
                  {namespaceResources.namespace.created_at ? 
                    new Date(namespaceResources.namespace.created_at).toLocaleString() : 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="描述" span={2}>
                  {namespaceResources.namespace.description || '无描述'}
                </Descriptions.Item>
              </Descriptions>

              <Divider />

              <Row gutter={16}>
                <Col span={6}>
                  <Card size="small">
                    <Statistic
                      title="部署"
                      value={namespaceResources.deployments?.length || 0}
                      prefix={<ClusterOutlined />}
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card size="small">
                    <Statistic
                      title="服务"
                      value={namespaceResources.services?.length || 0}
                      prefix={<DatabaseOutlined />}
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card size="small">
                    <Statistic
                      title="Pod"
                      value={namespaceResources.pods?.length || 0}
                      prefix={<ClusterOutlined />}
                      valueStyle={{ color: '#722ed1' }}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card size="small">
                    <Statistic
                      title="配置"
                      value={(namespaceResources.configmaps?.length || 0) + (namespaceResources.secrets?.length || 0)}
                      prefix={<DatabaseOutlined />}
                      valueStyle={{ color: '#fa8c16' }}
                    />
                  </Card>
                </Col>
              </Row>
            </TabPane>

            <TabPane tab={`部署 (${namespaceResources.deployments?.length || 0})`} key="deployments">
              <Table
                dataSource={namespaceResources.deployments || []}
                rowKey="id"
                size="small"
                pagination={false}
                columns={[
                  {
                    title: '名称',
                    dataIndex: 'name',
                    key: 'name',
                    render: (text: string) => <Text strong>{text}</Text>
                  },
                  {
                    title: '副本',
                    dataIndex: 'replicas',
                    key: 'replicas',
                    render: (replicas: number, record: any) => (
                      <Tag color={record.ready_replicas === replicas ? 'green' : 'orange'}>
                        {record.ready_replicas || 0}/{replicas || 0}
                      </Tag>
                    )
                  },
                  {
                    title: '状态',
                    dataIndex: 'status',
                    key: 'status',
                    render: (status: string) => (
                      <Tag color={getStatusColor(status)}>{status}</Tag>
                    )
                  },
                  {
                    title: '创建时间',
                    dataIndex: 'created_at',
                    key: 'created_at',
                    render: (time: string) => time ? new Date(time).toLocaleString() : 'N/A'
                  }
                ]}
              />
            </TabPane>

            <TabPane tab={`服务 (${namespaceResources.services?.length || 0})`} key="services">
              <Table
                dataSource={namespaceResources.services || []}
                rowKey="id"
                size="small"
                pagination={false}
                columns={[
                  {
                    title: '名称',
                    dataIndex: 'name',
                    key: 'name',
                    render: (text: string) => <Text strong>{text}</Text>
                  },
                  {
                    title: '类型',
                    dataIndex: 'service_type',
                    key: 'service_type',
                    render: (type: string) => <Tag color="blue">{type}</Tag>
                  },
                  {
                    title: '端口',
                    dataIndex: 'ports',
                    key: 'ports',
                    render: (ports: any) => {
                      if (typeof ports === 'string') {
                        try {
                          ports = JSON.parse(ports);
                        } catch {
                          return ports;
                        }
                      }
                      if (Array.isArray(ports)) {
                        return ports.map((port: any, index: number) => (
                          <Tag key={index}>{port.port || port}</Tag>
                        ));
                      }
                      return 'N/A';
                    }
                  },
                  {
                    title: '创建时间',
                    dataIndex: 'created_at',
                    key: 'created_at',
                    render: (time: string) => time ? new Date(time).toLocaleString() : 'N/A'
                  }
                ]}
              />
            </TabPane>

            <TabPane tab={`Pod (${namespaceResources.pods?.length || 0})`} key="pods">
              <Table
                dataSource={namespaceResources.pods || []}
                rowKey="id"
                size="small"
                pagination={false}
                columns={[
                  {
                    title: '名称',
                    dataIndex: 'name',
                    key: 'name',
                    render: (text: string) => <Text strong>{text}</Text>
                  },
                  {
                    title: '状态',
                    dataIndex: 'status',
                    key: 'status',
                    render: (status: string) => (
                      <Tag color={getStatusColor(status)}>{status}</Tag>
                    )
                  },
                  {
                    title: '重启次数',
                    dataIndex: 'restart_count',
                    key: 'restart_count',
                    render: (count: number) => (
                      <Tag color={count > 0 ? 'orange' : 'green'}>{count || 0}</Tag>
                    )
                  },
                  {
                    title: '节点',
                    dataIndex: 'node_name',
                    key: 'node_name',
                    render: (nodeName: string) => nodeName || 'N/A'
                  },
                  {
                    title: '创建时间',
                    dataIndex: 'created_at',
                    key: 'created_at',
                    render: (time: string) => time ? new Date(time).toLocaleString() : 'N/A'
                  }
                ]}
              />
            </TabPane>

            <TabPane tab={`配置 (${(namespaceResources.configmaps?.length || 0) + (namespaceResources.secrets?.length || 0)})`} key="configs">
              <Card title="ConfigMaps" size="small" style={{ marginBottom: 16 }}>
                <Table
                  dataSource={namespaceResources.configmaps || []}
                  rowKey="id"
                  size="small"
                  pagination={false}
                  columns={[
                    {
                      title: '名称',
                      dataIndex: 'name',
                      key: 'name',
                      render: (text: string) => <Text strong>{text}</Text>
                    },
                    {
                      title: '键数量',
                      dataIndex: 'data',
                      key: 'data',
                      render: (data: any) => {
                        if (typeof data === 'string') {
                          try {
                            data = JSON.parse(data);
                          } catch {
                            return 'N/A';
                          }
                        }
                        return Object.keys(data || {}).length;
                      }
                    },
                    {
                      title: '创建时间',
                      dataIndex: 'created_at',
                      key: 'created_at',
                      render: (time: string) => time ? new Date(time).toLocaleString() : 'N/A'
                    }
                  ]}
                />
              </Card>

              <Card title="Secrets" size="small">
                <Table
                  dataSource={namespaceResources.secrets || []}
                  rowKey="id"
                  size="small"
                  pagination={false}
                  columns={[
                    {
                      title: '名称',
                      dataIndex: 'name',
                      key: 'name',
                      render: (text: string) => <Text strong>{text}</Text>
                    },
                    {
                      title: '类型',
                      dataIndex: 'secret_type',
                      key: 'secret_type',
                      render: (type: string) => <Tag color="purple">{type}</Tag>
                    },
                    {
                      title: '键数量',
                      dataIndex: 'data',
                      key: 'data',
                      render: (data: any) => {
                        if (typeof data === 'string') {
                          try {
                            data = JSON.parse(data);
                          } catch {
                            return 'N/A';
                          }
                        }
                        return Object.keys(data || {}).length;
                      }
                    },
                    {
                      title: '创建时间',
                      dataIndex: 'created_at',
                      key: 'created_at',
                      render: (time: string) => time ? new Date(time).toLocaleString() : 'N/A'
                    }
                  ]}
                />
              </Card>
            </TabPane>
          </Tabs>
        )}
      </Modal>

      {/* 集群详情模态框 */}
      <Modal
        title={
          <Space>
            <ClusterOutlined />
            集群详情: {selectedCluster?.name}
          </Space>
        }
        open={clusterDetailModalVisible}
        onCancel={() => {
          setClusterDetailModalVisible(false);
          setSelectedCluster(null);
          setClusterStats(null);
        }}
        width={800}
        footer={[
          <Button 
            key="close" 
            onClick={() => {
              setClusterDetailModalVisible(false);
              setSelectedCluster(null);
              setClusterStats(null);
            }}
          >
            关闭
          </Button>
        ]}
      >
        {selectedCluster && (
          <Tabs defaultActiveKey="overview">
            <TabPane tab="基本信息" key="overview">
              <Descriptions bordered size="small" column={2}>
                <Descriptions.Item label="集群名称">
                  <Text strong>{selectedCluster.name}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="集群状态">
                  <Badge 
                    status={getStatusColor(selectedCluster.status) === 'success' ? 'success' : 'warning'} 
                    text={selectedCluster.status} 
                  />
                </Descriptions.Item>
                <Descriptions.Item label="API 服务器地址" span={2}>
                  <Text code copyable={{ text: selectedCluster.api_server }}>
                    {selectedCluster.api_server}
                  </Text>
                </Descriptions.Item>
                <Descriptions.Item label="集群类型">
                  <Tag color="blue">{selectedCluster.cluster_type || '未指定'}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="默认集群">
                  {selectedCluster.is_default ? (
                    <Tag color="green">是</Tag>
                  ) : (
                    <Tag color="default">否</Tag>
                  )}
                </Descriptions.Item>
                <Descriptions.Item label="创建时间" span={2}>
                  {selectedCluster.created_at ? 
                    new Date(selectedCluster.created_at).toLocaleString() : 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="更新时间" span={2}>
                  {selectedCluster.updated_at ? 
                    new Date(selectedCluster.updated_at).toLocaleString() : 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="描述" span={2}>
                  {selectedCluster.description || '无描述'}
                </Descriptions.Item>
              </Descriptions>

              <Divider />

              {loadingClusterStats ? (
                <Alert
                  message="正在获取集群资源统计信息..."
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              ) : clusterStats ? (
                <Alert
                  message={`集群资源统计 - ${clusterStats.connected ? '连接正常' : '连接异常'}`}
                  description={clusterStats.message}
                  type={clusterStats.connected ? 'success' : 'error'}
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              ) : (
                <Alert
                  message="集群资源统计"
                  description="点击集群详情时自动获取实时统计信息"
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              )}

              <Row gutter={16}>
                <Col span={12}>
                  <Card size="small">
                    <Statistic
                      title="集群版本"
                      value={clusterStats?.cluster_stats?.version || '获取中...'}
                      prefix={<CheckCircleOutlined />}
                      valueStyle={{ 
                        color: clusterStats?.connected ? '#52c41a' : '#ff4d4f' 
                      }}
                    />
                  </Card>
                </Col>
                <Col span={12}>
                  <Card size="small">
                    <Statistic
                      title="节点状态"
                      value={clusterStats?.cluster_stats ? 
                        `${clusterStats.cluster_stats.ready_nodes}/${clusterStats.cluster_stats.total_nodes}` : 
                        '获取中...'
                      }
                      prefix={<DatabaseOutlined />}
                      valueStyle={{ 
                        color: clusterStats?.connected ? '#52c41a' : '#ff4d4f' 
                      }}
                    />
                  </Card>
                </Col>
              </Row>

              <Row gutter={16} style={{ marginTop: 16 }}>
                <Col span={12}>
                  <Card size="small">
                    <Statistic
                      title="总 Pod 数"
                      value={clusterStats?.cluster_stats?.total_pods || 0}
                      prefix={<CheckCircleOutlined />}
                      valueStyle={{ 
                        color: clusterStats?.connected ? '#1890ff' : '#ff4d4f' 
                      }}
                    />
                  </Card>
                </Col>
                <Col span={12}>
                  <Card size="small">
                    <Statistic
                      title="运行中 Pod"
                      value={clusterStats?.cluster_stats?.running_pods || 0}
                      prefix={<CheckCircleOutlined />}
                      valueStyle={{ 
                        color: clusterStats?.connected ? '#52c41a' : '#ff4d4f' 
                      }}
                    />
                  </Card>
                </Col>
              </Row>

              <Row gutter={16} style={{ marginTop: 16 }}>
                <Col span={12}>
                  <Card size="small">
                    <Statistic
                      title="集群状态"
                      value={selectedCluster.status}
                      prefix={
                        selectedCluster.status === 'connected' || selectedCluster.status === 'active' 
                          ? <CheckCircleOutlined /> 
                          : <ExclamationCircleOutlined />
                      }
                      valueStyle={{ 
                        color: selectedCluster.status === 'connected' || selectedCluster.status === 'active' 
                          ? '#52c41a' 
                          : '#ff4d4f' 
                      }}
                    />
                  </Card>
                </Col>
                <Col span={12}>
                  <Card size="small">
                    <Statistic
                      title="配置状态"
                      value={selectedCluster.auth_config ? '已配置' : '未配置'}
                      prefix={<DatabaseOutlined />}
                      valueStyle={{ 
                        color: selectedCluster.auth_config ? '#52c41a' : '#ff4d4f' 
                      }}
                    />
                  </Card>
                </Col>
              </Row>
            </TabPane>

            <TabPane tab="认证配置" key="auth">
              <Descriptions bordered size="small">
                <Descriptions.Item label="认证方式">
                  {selectedCluster.auth_config?.token ? (
                    <Tag color="green">Token 认证</Tag>
                  ) : selectedCluster.auth_config?.kubeconfig ? (
                    <Tag color="blue">Kubeconfig 认证</Tag>
                  ) : selectedCluster.auth_config?.client_cert ? (
                    <Tag color="purple">证书认证</Tag>
                  ) : (
                    <Tag color="default">未配置</Tag>
                  )}
                </Descriptions.Item>
                <Descriptions.Item label="SSL 验证">
                  {selectedCluster.auth_config?.verify_ssl ? (
                    <Tag color="green">启用</Tag>
                  ) : (
                    <Tag color="orange">禁用</Tag>
                  )}
                </Descriptions.Item>
                <Descriptions.Item label="CA 证书">
                  {selectedCluster.auth_config?.ca_cert ? (
                    <Tag color="green">已配置</Tag>
                  ) : (
                    <Tag color="default">未配置</Tag>
                  )}
                </Descriptions.Item>
                <Descriptions.Item label="配置详情" span={2}>
                  <Text code>
                    {JSON.stringify(
                      Object.keys(selectedCluster.auth_config || {}), 
                      null, 
                      2
                    )}
                  </Text>
                </Descriptions.Item>
              </Descriptions>
            </TabPane>
          </Tabs>
        )}
      </Modal>
    </div>
  );
};

export default KubernetesSettings;
