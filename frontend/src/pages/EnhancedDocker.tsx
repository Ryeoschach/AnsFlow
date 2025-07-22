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
  Typography,
  Switch,
  Radio,
  Alert,
  Empty,
  Tooltip,
  Badge
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  PlusOutlined,
  CloudOutlined,
  DesktopOutlined,
  ContainerOutlined,
  DatabaseOutlined,
  SettingOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { apiService } from '../services/api';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

// Docker资源显示模式
type DockerViewMode = 'managed' | 'local' | 'hybrid';

interface DockerPageState {
  viewMode: DockerViewMode;
  managedResources: {
    registries: any[];
    images: any[];
    containers: any[];
    compose: any[];
  };
  localResources: {
    images: any[];
    containers: any[];
    info: any;
  };
  loading: {
    managed: boolean;
    local: boolean;
  };
  systemInfo: any;
}

const DockerManagement: React.FC = () => {
  const [state, setState] = useState<DockerPageState>({
    viewMode: 'managed',
    managedResources: {
      registries: [],
      images: [],
      containers: [],
      compose: []
    },
    localResources: {
      images: [],
      containers: [],
      info: null
    },
    loading: {
      managed: false,
      local: false
    },
    systemInfo: null
  });

  // 加载管理的资源
  const loadManagedResources = async () => {
    setState(prev => ({ ...prev, loading: { ...prev.loading, managed: true } }));
    try {
      const [registries, images, containers, compose] = await Promise.all([
        apiService.getDockerRegistries(),
        apiService.getDockerImages(),
        apiService.getDockerContainers(),
        apiService.getDockerComposes()
      ]);

      setState(prev => ({
        ...prev,
        managedResources: {
          registries: registries.results || [],
          images: images.results || [],
          containers: containers.results || [],
          compose: compose.results || []
        }
      }));
    } catch (error) {
      message.error('加载管理资源失败');
      console.error('Load managed resources error:', error);
    } finally {
      setState(prev => ({ ...prev, loading: { ...prev.loading, managed: false } }));
    }
  };

  // 加载本地Docker资源
  const loadLocalResources = async () => {
    setState(prev => ({ ...prev, loading: { ...prev.loading, local: true } }));
    try {
      // 暂时使用现有API，后续需要添加本地资源API
      const [localImages, localContainers, dockerInfo] = await Promise.all([
        Promise.resolve([]), // 待实现：apiService.getLocalDockerImages()
        Promise.resolve([]), // 待实现：apiService.getLocalDockerContainers()
        Promise.resolve(null) // 待实现：apiService.getDockerSystemInfo()
      ]);

      setState(prev => ({
        ...prev,
        localResources: {
          images: localImages || [],
          containers: localContainers || [],
          info: dockerInfo
        }
      }));
    } catch (error) {
      message.error('加载本地资源失败');
      console.error('Load local resources error:', error);
    } finally {
      setState(prev => ({ ...prev, loading: { ...prev.loading, local: false } }));
    }
  };

  // 模式切换处理
  const handleViewModeChange = (mode: DockerViewMode) => {
    setState(prev => ({ ...prev, viewMode: mode }));
    
    if (mode === 'local' || mode === 'hybrid') {
      loadLocalResources();
    }
    if (mode === 'managed' || mode === 'hybrid') {
      loadManagedResources();
    }
  };

  // 初始化加载
  useEffect(() => {
    loadManagedResources();
  }, []);

  // 渲染模式切换器
  const renderModeSwitch = () => (
    <Card size="small" style={{ marginBottom: 16 }}>
      <Row justify="space-between" align="middle">
        <Col>
          <Text strong>显示模式：</Text>
        </Col>
        <Col>
          <Radio.Group
            value={state.viewMode}
            onChange={(e) => handleViewModeChange(e.target.value)}
            size="small"
          >
            <Radio.Button value="managed">
              <CloudOutlined /> 托管资源
            </Radio.Button>
            <Radio.Button value="local">
              <DesktopOutlined /> 本地资源
            </Radio.Button>
            <Radio.Button value="hybrid">
              <SettingOutlined /> 混合视图
            </Radio.Button>
          </Radio.Group>
        </Col>
      </Row>
      
      {/* 模式说明 */}
      <div style={{ marginTop: 8 }}>
        {state.viewMode === 'managed' && (
          <Alert
            message="显示 AnsFlow 系统管理的 Docker 资源（仓库配置、管理的镜像和容器）"
            type="info"
            showIcon
          />
        )}
        {state.viewMode === 'local' && (
          <Alert
            message="显示本地 Docker 守护进程中的实际镜像和容器"
            type="success"
            showIcon
          />
        )}
        {state.viewMode === 'hybrid' && (
          <Alert
            message="同时显示托管资源和本地资源，便于对比和管理"
            type="warning"
            showIcon
          />
        )}
      </div>
    </Card>
  );

  // 渲染统计信息
  const renderStatistics = () => {
    const managedStats = {
      registries: state.managedResources.registries.length,
      images: state.managedResources.images.length,
      containers: state.managedResources.containers.length,
      running: state.managedResources.containers.filter(c => c.status === 'running').length
    };

    const localStats = {
      images: state.localResources.images.length,
      containers: state.localResources.containers.length,
      running: state.localResources.containers.filter(c => c.status === 'running').length
    };

    return (
      <Row gutter={16} style={{ marginBottom: 24 }}>
        {(state.viewMode === 'managed' || state.viewMode === 'hybrid') && (
          <>
            <Col span={state.viewMode === 'hybrid' ? 3 : 6}>
              <Card>
                <Statistic
                  title="托管仓库"
                  value={managedStats.registries}
                  prefix={<CloudOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col span={state.viewMode === 'hybrid' ? 3 : 6}>
              <Card>
                <Statistic
                  title="托管镜像"
                  value={managedStats.images}
                  prefix={<DatabaseOutlined />}
                />
              </Card>
            </Col>
            <Col span={state.viewMode === 'hybrid' ? 3 : 6}>
              <Card>
                <Statistic
                  title="托管容器"
                  value={managedStats.containers}
                  prefix={<ContainerOutlined />}
                />
              </Card>
            </Col>
          </>
        )}
        
        {(state.viewMode === 'local' || state.viewMode === 'hybrid') && (
          <>
            <Col span={state.viewMode === 'hybrid' ? 3 : 8}>
              <Card>
                <Statistic
                  title="本地镜像"
                  value={localStats.images}
                  prefix={<DatabaseOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col span={state.viewMode === 'hybrid' ? 3 : 8}>
              <Card>
                <Statistic
                  title="本地容器"
                  value={localStats.containers}
                  prefix={<ContainerOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col span={state.viewMode === 'hybrid' ? 3 : 8}>
              <Card>
                <Statistic
                  title="运行中"
                  value={localStats.running}
                  prefix={<PlayCircleOutlined />}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Card>
            </Col>
          </>
        )}
      </Row>
    );
  };

  // 渲染空状态
  const renderEmptyState = (type: 'registries' | 'images' | 'containers' | 'compose', isLocal: boolean = false) => {
    const resourceType = isLocal ? '本地' : '托管';
    const descriptions: Record<string, string> = {
      registries: `暂无${resourceType}仓库配置`,
      images: `暂无${resourceType}镜像`,
      containers: `暂无${resourceType}容器`,
      compose: `暂无${resourceType}Compose文件`
    };

    const actions: Record<string, React.ReactNode[]> = {
      registries: [
        <Button key="add" type="primary" icon={<PlusOutlined />}>
          添加仓库
        </Button>
      ],
      images: [
        <Button key="pull" type="primary" icon={<CloudOutlined />}>
          拉取镜像
        </Button>,
        <Button key="build" icon={<SettingOutlined />}>
          构建镜像
        </Button>
      ],
      containers: [
        <Button key="create" type="primary" icon={<PlusOutlined />}>
          创建容器
        </Button>
      ],
      compose: [
        <Button key="add" type="primary" icon={<PlusOutlined />}>
          添加Compose
        </Button>
      ]
    };

    return (
      <Empty
        description={descriptions[type]}
        style={{ margin: '40px 0' }}
      >
        {!isLocal && actions[type]}
      </Empty>
    );
  };

  // 镜像列表列定义
  const getImageColumns = (isLocal: boolean = false) => [
    {
      title: '镜像名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: any) => (
        <Space>
          <Text strong>{text}</Text>
          {isLocal && <Tag color="green">本地</Tag>}
          {!isLocal && <Tag color="blue">托管</Tag>}
        </Space>
      )
    },
    {
      title: '标签',
      dataIndex: 'tag',
      key: 'tag',
      render: (tag: string) => <Tag>{tag || 'latest'}</Tag>
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      render: (size: number) => size ? `${(size / 1024 / 1024).toFixed(2)} MB` : '-'
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => date ? new Date(date).toLocaleString() : '-'
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: any) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />}>
            详情
          </Button>
          {!isLocal && (
            <>
              <Button size="small" icon={<EditOutlined />}>
                编辑
              </Button>
              <Button size="small" danger icon={<DeleteOutlined />}>
                删除
              </Button>
            </>
          )}
        </Space>
      )
    }
  ];

  // 容器列表列定义
  const getContainerColumns = (isLocal: boolean = false) => [
    {
      title: '容器名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: any) => (
        <Space>
          <Text strong>{text}</Text>
          {isLocal && <Tag color="green">本地</Tag>}
          {!isLocal && <Tag color="blue">托管</Tag>}
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig: Record<string, { color: string; text: string }> = {
          running: { color: 'green', text: '运行中' },
          stopped: { color: 'red', text: '已停止' },
          paused: { color: 'orange', text: '已暂停' },
          exited: { color: 'gray', text: '已退出' }
        };
        const config = statusConfig[status] || { color: 'default', text: status };
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '镜像',
      dataIndex: 'image',
      key: 'image',
      render: (image: string) => <Text code>{image}</Text>
    },
    {
      title: '端口',
      dataIndex: 'ports',
      key: 'ports',
      render: (ports: any[]) => (
        <Space>
          {ports?.map((port, index) => (
            <Tag key={index}>{port}</Tag>
          )) || '-'}
        </Space>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: any) => (
        <Space>
          {record.status === 'running' ? (
            <Button size="small" icon={<PauseCircleOutlined />}>
              暂停
            </Button>
          ) : (
            <Button size="small" icon={<PlayCircleOutlined />}>
              启动
            </Button>
          )}
          <Button size="small" icon={<StopOutlined />}>
            停止
          </Button>
          <Button size="small" icon={<EyeOutlined />}>
            日志
          </Button>
          {!isLocal && (
            <Button size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          )}
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Docker 管理</Title>
      
      {/* 模式切换器 */}
      {renderModeSwitch()}
      
      {/* 统计信息 */}
      {renderStatistics()}

      <Tabs defaultActiveKey="images" type="card">
        {/* 镜像管理 */}
        <TabPane
          tab={
            <span>
              <DatabaseOutlined />
              镜像管理
              <Badge
                count={
                  state.viewMode === 'managed' ? state.managedResources.images.length :
                  state.viewMode === 'local' ? state.localResources.images.length :
                  state.managedResources.images.length + state.localResources.images.length
                }
                style={{ marginLeft: 8 }}
              />
            </span>
          }
          key="images"
        >
          {state.viewMode === 'managed' && (
            <Card title="托管镜像" style={{ marginBottom: 16 }}>
              {state.managedResources.images.length > 0 ? (
                <Table
                  columns={getImageColumns(false)}
                  dataSource={state.managedResources.images}
                  rowKey="id"
                  loading={state.loading.managed}
                  pagination={{ pageSize: 10 }}
                />
              ) : (
                renderEmptyState('images', false)
              )}
            </Card>
          )}

          {state.viewMode === 'local' && (
            <Card title="本地镜像" style={{ marginBottom: 16 }}>
              {state.localResources.images.length > 0 ? (
                <Table
                  columns={getImageColumns(true)}
                  dataSource={state.localResources.images}
                  rowKey="id"
                  loading={state.loading.local}
                  pagination={{ pageSize: 10 }}
                />
              ) : (
                renderEmptyState('images', true)
              )}
            </Card>
          )}

          {state.viewMode === 'hybrid' && (
            <>
              <Card title="托管镜像" style={{ marginBottom: 16 }}>
                {state.managedResources.images.length > 0 ? (
                  <Table
                    columns={getImageColumns(false)}
                    dataSource={state.managedResources.images}
                    rowKey="id"
                    loading={state.loading.managed}
                    pagination={{ pageSize: 5 }}
                  />
                ) : (
                  renderEmptyState('images', false)
                )}
              </Card>
              
              <Card title="本地镜像">
                {state.localResources.images.length > 0 ? (
                  <Table
                    columns={getImageColumns(true)}
                    dataSource={state.localResources.images}
                    rowKey="id"
                    loading={state.loading.local}
                    pagination={{ pageSize: 5 }}
                  />
                ) : (
                  renderEmptyState('images', true)
                )}
              </Card>
            </>
          )}
        </TabPane>

        {/* 容器管理 */}
        <TabPane
          tab={
            <span>
              <ContainerOutlined />
              容器管理
              <Badge
                count={
                  state.viewMode === 'managed' ? state.managedResources.containers.length :
                  state.viewMode === 'local' ? state.localResources.containers.length :
                  state.managedResources.containers.length + state.localResources.containers.length
                }
                style={{ marginLeft: 8 }}
              />
            </span>
          }
          key="containers"
        >
          {state.viewMode === 'managed' && (
            <Card title="托管容器" style={{ marginBottom: 16 }}>
              {state.managedResources.containers.length > 0 ? (
                <Table
                  columns={getContainerColumns(false)}
                  dataSource={state.managedResources.containers}
                  rowKey="id"
                  loading={state.loading.managed}
                  pagination={{ pageSize: 10 }}
                />
              ) : (
                renderEmptyState('containers', false)
              )}
            </Card>
          )}

          {state.viewMode === 'local' && (
            <Card title="本地容器" style={{ marginBottom: 16 }}>
              {state.localResources.containers.length > 0 ? (
                <Table
                  columns={getContainerColumns(true)}
                  dataSource={state.localResources.containers}
                  rowKey="id"
                  loading={state.loading.local}
                  pagination={{ pageSize: 10 }}
                />
              ) : (
                renderEmptyState('containers', true)
              )}
            </Card>
          )}

          {state.viewMode === 'hybrid' && (
            <>
              <Card title="托管容器" style={{ marginBottom: 16 }}>
                {state.managedResources.containers.length > 0 ? (
                  <Table
                    columns={getContainerColumns(false)}
                    dataSource={state.managedResources.containers}
                    rowKey="id"
                    loading={state.loading.managed}
                    pagination={{ pageSize: 5 }}
                  />
                ) : (
                  renderEmptyState('containers', false)
                )}
              </Card>
              
              <Card title="本地容器">
                {state.localResources.containers.length > 0 ? (
                  <Table
                    columns={getContainerColumns(true)}
                    dataSource={state.localResources.containers}
                    rowKey="id"
                    loading={state.loading.local}
                    pagination={{ pageSize: 5 }}
                  />
                ) : (
                  renderEmptyState('containers', true)
                )}
              </Card>
            </>
          )}
        </TabPane>

        {/* 仓库管理 */}
        <TabPane
          tab={
            <span>
              <CloudOutlined />
              仓库管理
              <Badge count={state.managedResources.registries.length} style={{ marginLeft: 8 }} />
            </span>
          }
          key="registries"
        >
          <Card title="Docker 仓库配置">
            {state.managedResources.registries.length > 0 ? (
              <Table
                columns={[
                  {
                    title: '仓库名称',
                    dataIndex: 'name',
                    key: 'name',
                    render: (text: string, record: any) => (
                      <Space>
                        <Text strong>{text}</Text>
                        {record.is_default && <Tag color="gold">默认</Tag>}
                      </Space>
                    )
                  },
                  {
                    title: '类型',
                    dataIndex: 'registry_type',
                    key: 'registry_type',
                    render: (type: string) => <Tag>{type}</Tag>
                  },
                  {
                    title: '地址',
                    dataIndex: 'url',
                    key: 'url',
                    render: (url: string) => <Text code>{url}</Text>
                  },
                  {
                    title: '状态',
                    dataIndex: 'status',
                    key: 'status',
                    render: (status: string) => (
                      <Tag color={status === 'active' ? 'green' : 'red'}>
                        {status === 'active' ? '活跃' : '非活跃'}
                      </Tag>
                    )
                  },
                  {
                    title: '操作',
                    key: 'actions',
                    render: () => (
                      <Space>
                        <Button size="small" icon={<EditOutlined />}>编辑</Button>
                        <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
                      </Space>
                    )
                  }
                ]}
                dataSource={state.managedResources.registries}
                rowKey="id"
                loading={state.loading.managed}
                pagination={{ pageSize: 10 }}
              />
            ) : (
              renderEmptyState('registries', false)
            )}
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default DockerManagement;
