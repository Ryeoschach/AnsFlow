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
  Upload,
  Progress,
  Divider,
  Badge,
  Switch,
  InputNumber,
  Alert
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
  CloudUploadOutlined,
  CloudDownloadOutlined,
  BuildOutlined,
  ContainerOutlined,
  DatabaseOutlined,
  MonitorOutlined,
  SecurityScanOutlined,
  SettingOutlined,
  FileTextOutlined,
  BugOutlined
} from '@ant-design/icons';
import { apiService } from '../services/api';
import type {
  DockerRegistry,
  DockerImage,
  DockerImageList,
  DockerContainer,
  DockerContainerList,
  DockerCompose,
  DockerComposeList,
  DockerContainerStats,
  DockerResourceStats,
  DockerRegistryFormData,
  DockerImageFormData,
  DockerContainerFormData,
  DockerComposeFormData
} from '../types/docker';

const { TabPane } = Tabs;
const { Title, Text } = Typography;
const { TextArea } = Input;

interface DockerPageState {
  registries: DockerRegistry[];
  images: DockerImageList[];
  containers: DockerContainerList[];
  composes: DockerComposeList[];
  systemStats: DockerResourceStats | null;
  loading: {
    registries: boolean;
    images: boolean;
    containers: boolean;
    composes: boolean;
    stats: boolean;
  };
  modals: {
    registry: boolean;
    image: boolean;
    container: boolean;
    compose: boolean;
    logs: boolean;
    stats: boolean;
  };
  selectedItem: any;
  containerLogs: string;
  containerStats: DockerContainerStats | null;
}

const Docker: React.FC = () => {
  const [state, setState] = useState<DockerPageState>({
    registries: [],
    images: [],
    containers: [],
    composes: [],
    systemStats: null,
    loading: {
      registries: false,
      images: false,
      containers: false,
      composes: false,
      stats: false
    },
    modals: {
      registry: false,
      image: false,
      container: false,
      compose: false,
      logs: false,
      stats: false
    },
    selectedItem: null,
    containerLogs: '',
    containerStats: null
  });

  const [registryForm] = Form.useForm();
  const [imageForm] = Form.useForm();
  const [containerForm] = Form.useForm();
  const [composeForm] = Form.useForm();

  // 数据加载函数
  const loadRegistries = async () => {
    setState(prev => ({ ...prev, loading: { ...prev.loading, registries: true } }));
    try {
      const data = await apiService.getDockerRegistries();
      setState(prev => ({ ...prev, registries: data.results || [] }));
    } catch (error) {
      message.error('加载仓库列表失败');
    } finally {
      setState(prev => ({ ...prev, loading: { ...prev.loading, registries: false } }));
    }
  };

  const loadImages = async () => {
    setState(prev => ({ ...prev, loading: { ...prev.loading, images: true } }));
    try {
      const data = await apiService.getDockerImages();
      setState(prev => ({ ...prev, images: data.results || [] }));
    } catch (error) {
      message.error('加载镜像列表失败');
    } finally {
      setState(prev => ({ ...prev, loading: { ...prev.loading, images: false } }));
    }
  };

  const loadContainers = async () => {
    setState(prev => ({ ...prev, loading: { ...prev.loading, containers: true } }));
    try {
      const data = await apiService.getDockerContainers();
      setState(prev => ({ ...prev, containers: data.results || [] }));
    } catch (error) {
      message.error('加载容器列表失败');
    } finally {
      setState(prev => ({ ...prev, loading: { ...prev.loading, containers: false } }));
    }
  };

  const loadComposes = async () => {
    setState(prev => ({ ...prev, loading: { ...prev.loading, composes: true } }));
    try {
      const data = await apiService.getDockerComposes();
      setState(prev => ({ ...prev, composes: data.results || [] }));
    } catch (error) {
      message.error('加载Compose列表失败');
    } finally {
      setState(prev => ({ ...prev, loading: { ...prev.loading, composes: false } }));
    }
  };

  const loadSystemStats = async () => {
    setState(prev => ({ ...prev, loading: { ...prev.loading, stats: true } }));
    try {
      const data = await apiService.getDockerSystemStats();
      setState(prev => ({ ...prev, systemStats: data }));
    } catch (error) {
      message.error('加载系统状态失败');
    } finally {
      setState(prev => ({ ...prev, loading: { ...prev.loading, stats: false } }));
    }
  };

  useEffect(() => {
    loadRegistries();
    loadImages();
    loadContainers();
    loadComposes();
    loadSystemStats();
  }, []);

  // 状态标签渲染
  const renderStatusTag = (status: string) => {
    const statusConfig: Record<string, { color: string; text: string }> = {
      active: { color: 'green', text: '活跃' },
      inactive: { color: 'red', text: '不活跃' },
      running: { color: 'green', text: '运行中' },
      stopped: { color: 'red', text: '已停止' },
      paused: { color: 'orange', text: '已暂停' },
      exited: { color: 'gray', text: '已退出' },
      created: { color: 'blue', text: '已创建' },
      error: { color: 'red', text: '错误' }
    };
    
    const config = statusConfig[status] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // Docker Registry 相关操作
  const handleCreateRegistry = async (values: DockerRegistryFormData) => {
    try {
      await apiService.createDockerRegistry(values);
      message.success('仓库创建成功');
      loadRegistries();
      setState(prev => ({ ...prev, modals: { ...prev.modals, registry: false } }));
      registryForm.resetFields();
    } catch (error) {
      message.error('仓库创建失败');
    }
  };

  const handleDeleteRegistry = async (id: number) => {
    try {
      await apiService.deleteDockerRegistry(id);
      message.success('仓库删除成功');
      loadRegistries();
    } catch (error) {
      message.error('仓库删除失败');
    }
  };

  const handleTestRegistry = async (id: number) => {
    try {
      const result = await apiService.testDockerRegistry(id);
      if (result.status === 'success') {
        message.success('仓库连接测试成功');
      } else {
        message.error(`仓库连接测试失败: ${result.message}`);
      }
    } catch (error) {
      message.error('仓库连接测试失败');
    }
  };

  // Docker Image 相关操作
  const handleCreateImage = async (values: DockerImageFormData) => {
    try {
      await apiService.createDockerImage(values);
      message.success('镜像创建成功');
      loadImages();
      setState(prev => ({ ...prev, modals: { ...prev.modals, image: false } }));
      imageForm.resetFields();
    } catch (error) {
      message.error('镜像创建失败');
    }
  };

  const handleBuildImage = async (id: number) => {
    try {
      const result = await apiService.buildDockerImage(id, {});
      if (result.status === 'success') {
        message.success('镜像构建任务已启动');
      } else {
        message.error(`镜像构建失败: ${result.message}`);
      }
    } catch (error) {
      message.error('镜像构建失败');
    }
  };

  const handlePushImage = async (id: number) => {
    try {
      const result = await apiService.pushDockerImage(id, {});
      if (result.status === 'success') {
        message.success('镜像推送任务已启动');
      } else {
        message.error(`镜像推送失败: ${result.message}`);
      }
    } catch (error) {
      message.error('镜像推送失败');
    }
  };

  const handlePullImage = async (id: number) => {
    try {
      const result = await apiService.pullDockerImage(id);
      if (result.status === 'success') {
        message.success('镜像拉取任务已启动');
      } else {
        message.error(`镜像拉取失败: ${result.message}`);
      }
    } catch (error) {
      message.error('镜像拉取失败');
    }
  };

  // Docker Container 相关操作
  const handleCreateContainer = async (values: DockerContainerFormData) => {
    try {
      await apiService.createDockerContainer(values);
      message.success('容器创建成功');
      loadContainers();
      setState(prev => ({ ...prev, modals: { ...prev.modals, container: false } }));
      containerForm.resetFields();
    } catch (error) {
      message.error('容器创建失败');
    }
  };

  const handleStartContainer = async (id: number) => {
    try {
      const result = await apiService.startDockerContainer(id);
      if (result.status === 'success') {
        message.success('容器启动成功');
        loadContainers();
      } else {
        message.error(`容器启动失败: ${result.message}`);
      }
    } catch (error) {
      message.error('容器启动失败');
    }
  };

  const handleStopContainer = async (id: number) => {
    try {
      const result = await apiService.stopDockerContainer(id);
      if (result.status === 'success') {
        message.success('容器停止成功');
        loadContainers();
      } else {
        message.error(`容器停止失败: ${result.message}`);
      }
    } catch (error) {
      message.error('容器停止失败');
    }
  };

  const handleRestartContainer = async (id: number) => {
    try {
      const result = await apiService.restartDockerContainer(id);
      if (result.status === 'success') {
        message.success('容器重启成功');
        loadContainers();
      } else {
        message.error(`容器重启失败: ${result.message}`);
      }
    } catch (error) {
      message.error('容器重启失败');
    }
  };

  const handleViewContainerLogs = async (container: DockerContainer) => {
    try {
      const result = await apiService.getDockerContainerLogs(container.id, { tail: '100' });
      setState(prev => ({
        ...prev,
        selectedItem: container,
        containerLogs: result.logs,
        modals: { ...prev.modals, logs: true }
      }));
    } catch (error) {
      message.error('获取容器日志失败');
    }
  };

  const handleViewContainerStats = async (container: DockerContainer) => {
    try {
      const stats = await apiService.getDockerContainerStats(container.id);
      setState(prev => ({
        ...prev,
        selectedItem: container,
        containerStats: stats,
        modals: { ...prev.modals, stats: true }
      }));
    } catch (error) {
      message.error('获取容器统计失败');
    }
  };

  // Docker Compose 相关操作
  const handleCreateCompose = async (values: DockerComposeFormData) => {
    try {
      await apiService.createDockerCompose(values);
      message.success('Compose项目创建成功');
      loadComposes();
      setState(prev => ({ ...prev, modals: { ...prev.modals, compose: false } }));
      composeForm.resetFields();
    } catch (error) {
      message.error('Compose项目创建失败');
    }
  };

  const handleStartCompose = async (id: number) => {
    try {
      const result = await apiService.startDockerCompose(id);
      if (result.status === 'success') {
        message.success('Compose项目启动成功');
        loadComposes();
      } else {
        message.error(`Compose项目启动失败: ${result.message}`);
      }
    } catch (error) {
      message.error('Compose项目启动失败');
    }
  };

  const handleStopCompose = async (id: number) => {
    try {
      const result = await apiService.stopDockerCompose(id);
      if (result.status === 'success') {
        message.success('Compose项目停止成功');
        loadComposes();
      } else {
        message.error(`Compose项目停止失败: ${result.message}`);
      }
    } catch (error) {
      message.error('Compose项目停止失败');
    }
  };

  // 表格列定义
  const registryColumns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
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
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => renderStatusTag(status)
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: DockerRegistry) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<BugOutlined />}
            onClick={() => handleTestRegistry(record.id)}
          >
            测试
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => {
              setState(prev => ({ ...prev, selectedItem: record, modals: { ...prev.modals, registry: true } }));
              registryForm.setFieldsValue(record);
            }}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除这个仓库吗？"
            onConfirm={() => handleDeleteRegistry(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  const imageColumns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '标签',
      dataIndex: 'tag',
      key: 'tag',
      render: (tag: string) => <Tag color="blue">{tag}</Tag>
    },
    {
      title: '仓库',
      dataIndex: 'registry_name',
      key: 'registry_name',
    },
    {
      title: '大小',
      dataIndex: 'image_size',
      key: 'image_size',
      render: (size: number) => size ? `${(size / 1024 / 1024).toFixed(2)} MB` : '-'
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => renderStatusTag(status)
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: DockerImage) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<BuildOutlined />}
            onClick={() => handleBuildImage(record.id)}
          >
            构建
          </Button>
          <Button
            size="small"
            icon={<CloudUploadOutlined />}
            onClick={() => handlePushImage(record.id)}
          >
            推送
          </Button>
          <Button
            size="small"
            icon={<CloudDownloadOutlined />}
            onClick={() => handlePullImage(record.id)}
          >
            拉取
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => {
              setState(prev => ({ ...prev, selectedItem: record, modals: { ...prev.modals, image: true } }));
              imageForm.setFieldsValue(record);
            }}
          >
            编辑
          </Button>
        </Space>
      )
    }
  ];

  const containerColumns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '镜像',
      dataIndex: 'image_name',
      key: 'image_name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => renderStatusTag(status)
    },
    {
      title: '启动时间',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (time: string) => time ? new Date(time).toLocaleString() : '-'
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: DockerContainer) => (
        <Space>
          {record.status === 'running' ? (
            <>
              <Button
                size="small"
                icon={<StopOutlined />}
                onClick={() => handleStopContainer(record.id)}
              >
                停止
              </Button>
              <Button
                size="small"
                icon={<PauseCircleOutlined />}
                onClick={() => handleRestartContainer(record.id)}
              >
                重启
              </Button>
            </>
          ) : (
            <Button
              type="primary"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleStartContainer(record.id)}
            >
              启动
            </Button>
          )}
          <Button
            size="small"
            icon={<FileTextOutlined />}
            onClick={() => handleViewContainerLogs(record)}
          >
            日志
          </Button>
          <Button
            size="small"
            icon={<MonitorOutlined />}
            onClick={() => handleViewContainerStats(record)}
          >
            监控
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => {
              setState(prev => ({ ...prev, selectedItem: record, modals: { ...prev.modals, container: true } }));
              containerForm.setFieldsValue(record);
            }}
          >
            编辑
          </Button>
        </Space>
      )
    }
  ];

  const composeColumns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '项目目录',
      dataIndex: 'project_path',
      key: 'project_path',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => renderStatusTag(status)
    },
    {
      title: '服务数量',
      dataIndex: 'services_count',
      key: 'services_count',
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: DockerCompose) => (
        <Space>
          {record.status === 'running' ? (
            <Button
              size="small"
              icon={<StopOutlined />}
              onClick={() => handleStopCompose(record.id)}
            >
              停止
            </Button>
          ) : (
            <Button
              type="primary"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleStartCompose(record.id)}
            >
              启动
            </Button>
          )}
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => {
              setState(prev => ({ ...prev, selectedItem: record, modals: { ...prev.modals, compose: true } }));
              composeForm.setFieldsValue(record);
            }}
          >
            编辑
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Docker 管理</Title>
      
      {/* 系统统计 */}
      {state.systemStats && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="容器总数"
                value={state.systemStats.total_containers}
                prefix={<ContainerOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="镜像总数"
                value={state.systemStats.total_images}
                prefix={<DatabaseOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="运行中容器"
                value={state.systemStats.running_containers}
                prefix={<PlayCircleOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="仓库总数"
                value={state.systemStats.total_registries}
                prefix={<DatabaseOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Tabs defaultActiveKey="containers" type="card">
        {/* 容器管理 */}
        <TabPane
          tab={
            <span>
              <ContainerOutlined />
              容器管理
            </span>
          }
          key="containers"
        >
          <Card
            title="容器列表"
            extra={
              <Space>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setState(prev => ({ ...prev, selectedItem: null, modals: { ...prev.modals, container: true } }));
                    containerForm.resetFields();
                  }}
                >
                  创建容器
                </Button>
                <Button icon={<ReloadOutlined />} onClick={loadContainers}>
                  刷新
                </Button>
              </Space>
            }
          >
            <Table
              columns={containerColumns}
              dataSource={state.containers}
              rowKey="id"
              loading={state.loading.containers}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>

        {/* 镜像管理 */}
        <TabPane
          tab={
            <span>
              <DatabaseOutlined />
              镜像管理
            </span>
          }
          key="images"
        >
          <Card
            title="镜像列表"
            extra={
              <Space>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setState(prev => ({ ...prev, selectedItem: null, modals: { ...prev.modals, image: true } }));
                    imageForm.resetFields();
                  }}
                >
                  添加镜像
                </Button>
                <Button icon={<ReloadOutlined />} onClick={loadImages}>
                  刷新
                </Button>
              </Space>
            }
          >
            <Table
              columns={imageColumns}
              dataSource={state.images}
              rowKey="id"
              loading={state.loading.images}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>

        {/* Compose管理 */}
        <TabPane
          tab={
            <span>
              <SettingOutlined />
              Compose管理
            </span>
          }
          key="compose"
        >
          <Card
            title="Compose项目列表"
            extra={
              <Space>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setState(prev => ({ ...prev, selectedItem: null, modals: { ...prev.modals, compose: true } }));
                    composeForm.resetFields();
                  }}
                >
                  创建项目
                </Button>
                <Button icon={<ReloadOutlined />} onClick={loadComposes}>
                  刷新
                </Button>
              </Space>
            }
          >
            <Table
              columns={composeColumns}
              dataSource={state.composes}
              rowKey="id"
              loading={state.loading.composes}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>

        {/* 仓库管理 */}
        <TabPane
          tab={
            <span>
              <CloudDownloadOutlined />
              仓库管理
            </span>
          }
          key="registries"
        >
          <Card
            title="仓库列表"
            extra={
              <Space>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setState(prev => ({ ...prev, selectedItem: null, modals: { ...prev.modals, registry: true } }));
                    registryForm.resetFields();
                  }}
                >
                  添加仓库
                </Button>
                <Button icon={<ReloadOutlined />} onClick={loadRegistries}>
                  刷新
                </Button>
              </Space>
            }
          >
            <Table
              columns={registryColumns}
              dataSource={state.registries}
              rowKey="id"
              loading={state.loading.registries}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* 仓库创建/编辑模态框 */}
      <Modal
        title={state.selectedItem ? '编辑仓库' : '添加仓库'}
        open={state.modals.registry}
        onCancel={() => setState(prev => ({ ...prev, modals: { ...prev.modals, registry: false } }))}
        footer={null}
        width={600}
      >
        <Form
          form={registryForm}
          layout="vertical"
          onFinish={handleCreateRegistry}
        >
          <Form.Item
            name="name"
            label="仓库名称"
            rules={[{ required: true, message: '请输入仓库名称' }]}
          >
            <Input placeholder="请输入仓库名称" />
          </Form.Item>
          <Form.Item
            name="registry_type"
            label="仓库类型"
            rules={[{ required: true, message: '请选择仓库类型' }]}
          >
            <Select placeholder="请选择仓库类型">
              <Select.Option value="dockerhub">Docker Hub</Select.Option>
              <Select.Option value="private">私有仓库</Select.Option>
              <Select.Option value="harbor">Harbor</Select.Option>
              <Select.Option value="ecr">AWS ECR</Select.Option>
              <Select.Option value="gcr">Google GCR</Select.Option>
              <Select.Option value="acr">Azure ACR</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="url"
            label="仓库地址"
            rules={[{ required: true, message: '请输入仓库地址' }]}
          >
            <Input placeholder="请输入仓库地址" />
          </Form.Item>
          <Form.Item name="username" label="用户名">
            <Input placeholder="请输入用户名" />
          </Form.Item>
          <Form.Item name="password" label="密码">
            <Input.Password placeholder="请输入密码" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {state.selectedItem ? '更新' : '创建'}
              </Button>
              <Button onClick={() => setState(prev => ({ ...prev, modals: { ...prev.modals, registry: false } }))}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 镜像创建/编辑模态框 */}
      <Modal
        title={state.selectedItem ? '编辑镜像' : '添加镜像'}
        open={state.modals.image}
        onCancel={() => setState(prev => ({ ...prev, modals: { ...prev.modals, image: false } }))}
        footer={null}
        width={600}
      >
        <Form
          form={imageForm}
          layout="vertical"
          onFinish={handleCreateImage}
        >
          <Form.Item
            name="name"
            label="镜像名称"
            rules={[{ required: true, message: '请输入镜像名称' }]}
          >
            <Input placeholder="请输入镜像名称" />
          </Form.Item>
          <Form.Item
            name="tag"
            label="镜像标签"
            rules={[{ required: true, message: '请输入镜像标签' }]}
          >
            <Input placeholder="请输入镜像标签，如：latest" />
          </Form.Item>
          <Form.Item
            name="registry"
            label="所属仓库"
          >
            <Select placeholder="请选择仓库">
              {state.registries.map(registry => (
                <Select.Option key={registry.id} value={registry.id}>
                  {registry.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="dockerfile_content" label="Dockerfile内容">
            <TextArea rows={10} placeholder="请输入Dockerfile内容" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {state.selectedItem ? '更新' : '创建'}
              </Button>
              <Button onClick={() => setState(prev => ({ ...prev, modals: { ...prev.modals, image: false } }))}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 容器创建/编辑模态框 */}
      <Modal
        title={state.selectedItem ? '编辑容器' : '创建容器'}
        open={state.modals.container}
        onCancel={() => setState(prev => ({ ...prev, modals: { ...prev.modals, container: false } }))}
        footer={null}
        width={800}
      >
        <Form
          form={containerForm}
          layout="vertical"
          onFinish={handleCreateContainer}
        >
          <Form.Item
            name="name"
            label="容器名称"
            rules={[{ required: true, message: '请输入容器名称' }]}
          >
            <Input placeholder="请输入容器名称" />
          </Form.Item>
          <Form.Item
            name="image"
            label="使用镜像"
            rules={[{ required: true, message: '请选择镜像' }]}
          >
            <Select placeholder="请选择镜像">
              {state.images.map(image => (
                <Select.Option key={image.id} value={image.id}>
                  {image.name}:{image.tag}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="command" label="启动命令">
            <Input placeholder="请输入启动命令" />
          </Form.Item>
          <Form.Item name="environment_vars" label="环境变量">
            <TextArea rows={4} placeholder="请输入环境变量，格式：KEY=VALUE，每行一个" />
          </Form.Item>
          <Form.Item name="port_mappings" label="端口映射">
            <TextArea rows={3} placeholder="请输入端口映射，格式：主机端口:容器端口，每行一个" />
          </Form.Item>
          <Form.Item name="volume_mappings" label="数据卷映射">
            <TextArea rows={3} placeholder="请输入数据卷映射，格式：主机路径:容器路径，每行一个" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {state.selectedItem ? '更新' : '创建'}
              </Button>
              <Button onClick={() => setState(prev => ({ ...prev, modals: { ...prev.modals, container: false } }))}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Compose创建/编辑模态框 */}
      <Modal
        title={state.selectedItem ? '编辑Compose项目' : '创建Compose项目'}
        open={state.modals.compose}
        onCancel={() => setState(prev => ({ ...prev, modals: { ...prev.modals, compose: false } }))}
        footer={null}
        width={800}
      >
        <Form
          form={composeForm}
          layout="vertical"
          onFinish={handleCreateCompose}
        >
          <Form.Item
            name="name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input placeholder="请输入项目名称" />
          </Form.Item>
          <Form.Item
            name="project_path"
            label="项目路径"
            rules={[{ required: true, message: '请输入项目路径' }]}
          >
            <Input placeholder="请输入项目路径" />
          </Form.Item>
          <Form.Item
            name="compose_content"
            label="docker-compose.yml内容"
            rules={[{ required: true, message: '请输入docker-compose.yml内容' }]}
          >
            <TextArea rows={15} placeholder="请输入docker-compose.yml内容" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {state.selectedItem ? '更新' : '创建'}
              </Button>
              <Button onClick={() => setState(prev => ({ ...prev, modals: { ...prev.modals, compose: false } }))}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 容器日志模态框 */}
      <Modal
        title={`容器日志 - ${state.selectedItem?.name}`}
        open={state.modals.logs}
        onCancel={() => setState(prev => ({ ...prev, modals: { ...prev.modals, logs: false } }))}
        footer={null}
        width={1000}
      >
        <div style={{ height: '500px', overflow: 'auto', backgroundColor: '#f5f5f5', padding: '16px', fontFamily: 'monospace' }}>
          <pre>{state.containerLogs}</pre>
        </div>
      </Modal>

      {/* 容器监控模态框 */}
      <Modal
        title={`容器监控 - ${state.selectedItem?.name}`}
        open={state.modals.stats}
        onCancel={() => setState(prev => ({ ...prev, modals: { ...prev.modals, stats: false } }))}
        footer={null}
        width={800}
      >
        {state.containerStats && (
          <div>
            <Row gutter={16}>
              <Col span={12}>
                <Card title="CPU使用率">
                  <Progress
                    type="circle"
                    percent={state.containerStats.cpu_usage_percent}
                    format={(percent) => `${percent}%`}
                  />
                </Card>
              </Col>
              <Col span={12}>
                <Card title="内存使用率">
                  <Progress
                    type="circle"
                    percent={state.containerStats.memory_percent}
                    format={(percent) => `${percent}%`}
                  />
                </Card>
              </Col>
            </Row>
            <Divider />
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="内存使用"
                  value={state.containerStats.memory_usage}
                  suffix="MB"
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="内存限制"
                  value={state.containerStats.memory_limit}
                  suffix="MB"
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="网络接收"
                  value={Math.round(state.containerStats.network_rx_bytes / 1024)}
                  suffix="KB"
                />
              </Col>
            </Row>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Docker;
