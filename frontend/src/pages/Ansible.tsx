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
  Tooltip
} from 'antd';
import {
  PlayCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  PlaySquareOutlined,
  StopOutlined,
  ReloadOutlined,
  HistoryOutlined,
  UploadOutlined,
  UserOutlined,
  SyncOutlined
} from '@ant-design/icons';
import { apiService } from '../services/api';
import { authUtils } from '../utils/auth';
import { InventoryDataSyncFixer } from '../utils/inventoryDataSyncFixer';
import ConnectionTestModal from '../components/ConnectionTestModal';
import HostFactsModal from '../components/HostFactsModal';
import InventoryHostModal from '../components/InventoryHostModal';
import ExecutionLogsModal from '../components/ExecutionLogsModal';
import HostGroupModal from '../components/HostGroupModal';
import InventoryGroupModal from '../components/InventoryGroupModal';
import InventoryDynamicGeneratorModal from '../components/InventoryDynamicGeneratorModal';
import type { 
  AnsibleStats, 
  AnsibleInventory, 
  AnsiblePlaybook, 
  AnsibleCredential, 
  AnsibleExecutionList,
  AnsibleHost,
  AnsibleHostGroup,
  AnsibleInventoryVersion,
  AnsiblePlaybookVersion,
  FileUploadResponse,
  ConnectionTestRequest
} from '../types';

const { TabPane } = Tabs;
const { TextArea } = Input;
const { Title, Text } = Typography;

const Ansible: React.FC = () => {
  const [stats, setStats] = useState<AnsibleStats | null>(null);
  const [inventories, setInventories] = useState<AnsibleInventory[]>([]);
  const [playbooks, setPlaybooks] = useState<AnsiblePlaybook[]>([]);
  const [credentials, setCredentials] = useState<AnsibleCredential[]>([]);
  const [executions, setExecutions] = useState<AnsibleExecutionList[]>([]);
  const [hosts, setHosts] = useState<AnsibleHost[]>([]);
  const [hostGroups, setHostGroups] = useState<AnsibleHostGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [connectionTestVisible, setConnectionTestVisible] = useState(false);
  const [factsModalVisible, setFactsModalVisible] = useState(false);
  const [selectedHost, setSelectedHost] = useState<AnsibleHost | null>(null);
  const [modalType, setModalType] = useState<'inventory' | 'playbook' | 'credential' | 'execute' | 'host' | 'hostgroup' | 'upload' | 'versions'>('inventory');
  const [editingItem, setEditingItem] = useState<any>(null);
  const [tempAuthData, setTempAuthData] = useState<ConnectionTestRequest | null>(null);
  const [versionsVisible, setVersionsVisible] = useState(false);
  const [versionsList, setVersionsList] = useState<any[]>([]);
  const [versionType, setVersionType] = useState<'inventory' | 'playbook'>('inventory');
  const [inventoryHostModalVisible, setInventoryHostModalVisible] = useState(false);
  const [selectedInventory, setSelectedInventory] = useState<AnsibleInventory | null>(null);
  const [executionLogsModalVisible, setExecutionLogsModalVisible] = useState(false);
  const [selectedExecution, setSelectedExecution] = useState<AnsibleExecutionList | null>(null);
  const [hostGroupModalVisible, setHostGroupModalVisible] = useState(false);
  const [selectedHostGroup, setSelectedHostGroup] = useState<AnsibleHostGroup | null>(null);
  const [inventoryGroupModalVisible, setInventoryGroupModalVisible] = useState(false);
  const [inventoryDynamicModalVisible, setInventoryDynamicModalVisible] = useState(false);
  const [form] = Form.useForm();

  // 获取统计数据
  const fetchStats = async () => {
    try {
      const data = await apiService.getAnsibleStats();
      setStats(data);
    } catch (error) {
      console.error('获取统计数据失败:', error);
    }
  };

  // 获取清单列表
  const fetchInventories = async () => {
    try {
      setLoading(true);
      const data = await apiService.getAnsibleInventories();
      setInventories(data);
    } catch (error) {
      message.error('获取清单列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取Playbook列表
  const fetchPlaybooks = async () => {
    try {
      setLoading(true);
      const data = await apiService.getAnsiblePlaybooks();
      setPlaybooks(data);
    } catch (error) {
      message.error('获取Playbook列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取凭据列表
  const fetchCredentials = async () => {
    try {
      setLoading(true);
      const data = await apiService.getAnsibleCredentials();
      setCredentials(data);
    } catch (error) {
      message.error('获取凭据列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取执行记录
  const fetchExecutions = async () => {
    try {
      setLoading(true);
      const data = await apiService.getAnsibleExecutions();
      setExecutions(data);
    } catch (error) {
      message.error('获取执行记录失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取主机列表
  const fetchHosts = async () => {
    try {
      setLoading(true);
      const data = await apiService.getAnsibleHosts();
      setHosts(data);
    } catch (error) {
      message.error('获取主机列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取主机组列表
  const fetchHostGroups = async () => {
    try {
      setLoading(true);
      const data = await apiService.getAnsibleHostGroups();
      setHostGroups(data);
    } catch (error) {
      message.error('获取主机组列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchInventories();
    fetchPlaybooks();
    fetchCredentials();
    fetchExecutions();
    fetchHosts();
    fetchHostGroups();
  }, []);

  // 加载演示数据
  const handleLoadDemoData = async () => {
    try {
      setLoading(true);
      // 这里可以调用后端API来加载演示数据
      // 目前我们直接刷新数据
      await Promise.all([
        fetchInventories(),
        fetchPlaybooks(),
        fetchCredentials(),
        fetchExecutions(),
        fetchHosts(),
        fetchHostGroups()
      ]);
      message.success('演示数据加载成功！请查看各个标签页的内容。');
    } catch (error) {
      message.error('加载演示数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理创建/编辑
  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      // 处理文件上传
      if (modalType === 'upload') {
        const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
        const file = fileInput?.files?.[0];
        if (!file) {
          message.error('请选择文件');
          return;
        }
        
        await handleFileUpload(values.upload_type, file, values.name, values.description);
        return;
      }
      
      if (editingItem) {
        // 编辑
        switch (modalType) {
          case 'inventory':
            await apiService.updateAnsibleInventory(editingItem.id, values);
            fetchInventories();
            break;
          case 'playbook':
            await apiService.updateAnsiblePlaybook(editingItem.id, values);
            fetchPlaybooks();
            break;
          case 'credential':
            await apiService.updateAnsibleCredential(editingItem.id, values);
            fetchCredentials();
            break;
          case 'host':
            await apiService.updateAnsibleHost(editingItem.id, values);
            fetchHosts();
            break;
          case 'hostgroup':
            await apiService.updateAnsibleHostGroup(editingItem.id, values);
            fetchHostGroups();
            break;
        }
        message.success('更新成功');
      } else {
        // 创建
        switch (modalType) {
          case 'inventory':
            await apiService.createAnsibleInventory(values);
            fetchInventories();
            break;
          case 'playbook':
            await apiService.createAnsiblePlaybook(values);
            fetchPlaybooks();
            break;
          case 'credential':
            await apiService.createAnsibleCredential(values);
            fetchCredentials();
            break;
          case 'host':
            // 如果有临时认证数据，将其包含在主机创建请求中
            const hostData = tempAuthData ? {
              ...values,
              temp_password: tempAuthData.password,
              temp_ssh_key: tempAuthData.ssh_private_key
            } : values;
            await apiService.createAnsibleHost(hostData);
            // 清除临时认证数据
            setTempAuthData(null);
            fetchHosts();
            break;
          case 'hostgroup':
            await apiService.createAnsibleHostGroup(values);
            fetchHostGroups();
            break;
        }
        message.success('创建成功');
      }
      
      setModalVisible(false);
      form.resetFields();
      setEditingItem(null);
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 修复清单统计数据
  const handleFixInventoryStats = async (inventoryId: number) => {
    try {
      setLoading(true);
      const success = await InventoryDataSyncFixer.forceRefreshInventoryStats(inventoryId);
      
      if (success) {
        message.success('统计数据已同步');
        fetchInventories(); // 重新获取清单列表
      } else {
        message.warning('检测到统计数据不一致，正在尝试修复...');
        // 强制刷新一次
        setTimeout(() => {
          fetchInventories();
        }, 1000);
      }
    } catch (error) {
      message.error('修复统计数据失败');
    } finally {
      setLoading(false);
    }
  };
  const handleDelete = async (id: number, type: 'inventory' | 'playbook' | 'credential' | 'host' | 'hostgroup') => {
    try {
      switch (type) {
        case 'inventory':
          await apiService.deleteAnsibleInventory(id);
          fetchInventories();
          break;
        case 'playbook':
          await apiService.deleteAnsiblePlaybook(id);
          fetchPlaybooks();
          break;
        case 'credential':
          await apiService.deleteAnsibleCredential(id);
          fetchCredentials();
          break;
        case 'host':
          await apiService.deleteAnsibleHost(id);
          fetchHosts();
          break;
        case 'hostgroup':
          await apiService.deleteAnsibleHostGroup(id);
          fetchHostGroups();
          break;
      }
      message.success('删除成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 执行Playbook
  const handleExecute = async (values: any) => {
    try {
      const result = await apiService.executeAnsiblePlaybook(values.playbook_id, {
        inventory_id: values.inventory_id,
        credential_id: values.credential_id,
        parameters: values.parameters || {}
      });
      message.success(`Playbook执行已启动: ${result.execution_id}`);
      setModalVisible(false);
      form.resetFields();
      fetchExecutions();
    } catch (error) {
      message.error('执行失败');
    }
  };

  // 取消执行
  const handleCancel = async (id: number) => {
    try {
      await apiService.cancelAnsibleExecution(id);
      message.success('执行已取消');
      fetchExecutions();
    } catch (error) {
      message.error('取消失败');
    }
  };

  // 主机连通性检查
  const handleCheckConnectivity = async (hostId: number) => {
    try {
      const result = await apiService.checkHostConnectivity(hostId);
      if (result.success) {
        message.success(`主机 ${result.hostname} 连接成功`);
      } else {
        message.error(`主机 ${result.hostname} 连接失败: ${result.message}`);
      }
      fetchHosts(); // 刷新主机状态
    } catch (error) {
      message.error('检查连通性失败');
    }
  };

  // 收集主机Facts
  const handleGatherFacts = async (hostId: number) => {
    try {
      const result = await apiService.gatherHostFacts(hostId);
      if (result.success) {
        message.success('主机 Facts 收集成功');
      } else {
        message.error(`主机 Facts 收集失败: ${result.message}`);
      }
      fetchHosts(); // 刷新主机信息
    } catch (error) {
      message.error('收集Facts失败');
    }
  };

  // 查看主机Facts详情
  const handleViewFacts = (host: AnsibleHost) => {
    setSelectedHost(host);
    setFactsModalVisible(true);
  };

  // 连接测试成功后的处理
  const handleConnectionTestSuccess = (testData: ConnectionTestRequest) => {
    // 保存连接测试的认证信息以便主机创建时使用
    setTempAuthData(testData);
    
    // 将测试数据填充到主机创建表单中
    setModalType('host');
    setModalVisible(true);
    setConnectionTestVisible(false);
    
    // 预填充表单数据
    form.setFieldsValue({
      hostname: `host-${testData.ip_address.replace(/\./g, '-')}`,
      ip_address: testData.ip_address,
      port: testData.port,
      username: testData.username,
      connection_type: testData.connection_type,
      // 认证信息将在创建时从tempAuthData中获取
    });
    
    message.success('连接测试成功！已为您预填充主机信息，点击确定即可创建主机。');
  };

  // 文件上传处理
  const handleFileUpload = async (uploadType: 'inventory' | 'playbook', file: File, name: string, description?: string) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', name);
      if (description) {
        formData.append('description', description);
      }

      let result: FileUploadResponse;
      if (uploadType === 'inventory') {
        result = await apiService.uploadInventoryFile(formData);
        fetchInventories();
      } else {
        result = await apiService.uploadPlaybookFile(formData);
        fetchPlaybooks();
      }
      
      message.success(result.message);
      setModalVisible(false);
      form.resetFields();
    } catch (error) {
      message.error('文件上传失败');
    }
  };

  // 版本管理相关函数
  const handleViewVersions = async (id: number, type: 'inventory' | 'playbook') => {
    try {
      setLoading(true);
      let versions: any[];
      if (type === 'inventory') {
        versions = await apiService.getInventoryVersions(id);
      } else {
        versions = await apiService.getPlaybookVersions(id);
      }
      setVersionsList(versions);
      setVersionType(type);
      setEditingItem({ id });
      setVersionsVisible(true);
    } catch (error) {
      message.error('获取版本历史失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVersion = async (values: any) => {
    try {
      if (versionType === 'inventory') {
        await apiService.createInventoryVersion(editingItem.id, values);
        message.success('Inventory 版本创建成功');
        fetchInventories();
      } else {
        await apiService.createPlaybookVersion(editingItem.id, values);
        message.success('Playbook 版本创建成功');
        fetchPlaybooks();
      }
      handleViewVersions(editingItem.id, versionType); // 刷新版本列表
    } catch (error) {
      message.error('版本创建失败');
    }
  };

  const handleRestoreVersion = async (versionId: number) => {
    try {
      if (versionType === 'inventory') {
        await apiService.restoreInventoryVersion(editingItem.id, versionId);
        message.success('Inventory 版本恢复成功');
        fetchInventories();
      } else {
        await apiService.restorePlaybookVersion(editingItem.id, versionId);
        message.success('Playbook 版本恢复成功');
        fetchPlaybooks();
      }
    } catch (error) {
      message.error('版本恢复失败');
    }
  };

  // 状态标签颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'green';
      case 'failed': return 'red';
      case 'running': return 'blue';
      case 'pending': return 'orange';
      case 'cancelled': return 'gray';
      // 主机状态颜色
      case 'active': return 'green';
      case 'inactive': return 'orange';
      case 'unknown': return 'gray';
      default: return 'default';
    }
  };

  // 清单表格列
  const inventoryColumns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '格式',
      dataIndex: 'format_type',
      key: 'format_type',
      render: (format: string) => <Tag>{format.toUpperCase()}</Tag>
    },
    {
      title: '关联资源',
      key: 'resources_info',
      render: (record: AnsibleInventory) => (
        <Space wrap>
          <Tag color="blue">
            {record.hosts_count || 0} 个主机
          </Tag>
          {record.active_hosts_count !== undefined && (
            <Tag color="green">
              {record.active_hosts_count} 个激活
            </Tag>
          )}
          <Tag color="purple">
            {record.groups_count || 0} 个主机组
          </Tag>
          {record.active_groups_count !== undefined && (
            <Tag color="cyan">
              {record.active_groups_count} 个激活组
            </Tag>
          )}
        </Space>
      )
    },
    {
      title: '创建者',
      dataIndex: 'created_by_username',
      key: 'created_by_username',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString()
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: AnsibleInventory) => (
        <Space>
          <Tooltip title="管理主机">
            <Button 
              size="small" 
              type="default"
              onClick={() => {
                setSelectedInventory(record);
                setInventoryHostModalVisible(true);
              }}
            >
              主机
            </Button>
          </Tooltip>
          <Tooltip title="管理主机组">
            <Button 
              size="small" 
              type="default"
              onClick={() => {
                setSelectedInventory(record);
                setInventoryGroupModalVisible(true);
              }}
            >
              主机组
            </Button>
          </Tooltip>
          <Tooltip title="动态管理">
            <Button 
              size="small" 
              type="primary"
              onClick={() => {
                setSelectedInventory(record);
                setInventoryDynamicModalVisible(true);
              }}
            >
              动态管理
            </Button>
          </Tooltip>
          <Tooltip title="修复统计数据">
            <Button 
              size="small" 
              icon={<SyncOutlined />}
              onClick={() => handleFixInventoryStats(record.id)}
            >
              同步
            </Button>
          </Tooltip>
          <Tooltip title="编辑">
            <Button 
              size="small" 
              icon={<EditOutlined />}
              onClick={() => {
                setEditingItem(record);
                setModalType('inventory');
                setModalVisible(true);
                form.setFieldsValue(record);
              }}
            />
          </Tooltip>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id, 'inventory')}>
            <Button size="small" icon={<DeleteOutlined />} danger />
          </Popconfirm>
          <Tooltip title="版本管理">
            <Button 
              size="small" 
              icon={<HistoryOutlined />}
              onClick={() => handleViewVersions(record.id, 'inventory')}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  // Playbook表格列
  const playbookColumns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => category && <Tag>{category}</Tag>
    },
    {
      title: '模板',
      dataIndex: 'is_template',
      key: 'is_template',
      render: (isTemplate: boolean) => (
        <Tag color={isTemplate ? 'blue' : 'default'}>
          {isTemplate ? '模板' : '普通'}
        </Tag>
      )
    },
    {
      title: '创建者',
      dataIndex: 'created_by_username',
      key: 'created_by_username',
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: AnsiblePlaybook) => (
        <Space>
          <Tooltip title="执行">
            <Button 
              size="small" 
              icon={<PlaySquareOutlined />}
              type="primary"
              onClick={() => {
                setEditingItem(record);
                setModalType('execute');
                setModalVisible(true);
                form.setFieldValue('playbook_id', record.id);
              }}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button 
              size="small" 
              icon={<EditOutlined />}
              onClick={() => {
                setEditingItem(record);
                setModalType('playbook');
                setModalVisible(true);
                form.setFieldsValue(record);
              }}
            />
          </Tooltip>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id, 'playbook')}>
            <Button size="small" icon={<DeleteOutlined />} danger />
          </Popconfirm>
          <Tooltip title="版本管理">
            <Button 
              size="small" 
              icon={<HistoryOutlined />}
              onClick={() => handleViewVersions(record.id, 'playbook')}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  // 凭据表格列
  const credentialColumns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '类型',
      dataIndex: 'credential_type_display',
      key: 'credential_type_display',
      render: (type: string) => <Tag>{type}</Tag>
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '创建者',
      dataIndex: 'created_by_username',
      key: 'created_by_username',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString()
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: AnsibleCredential) => (
        <Space>
          <Tooltip title="编辑">
            <Button 
              size="small" 
              icon={<EditOutlined />}
              onClick={() => {
                setEditingItem(record);
                setModalType('credential');
                setModalVisible(true);
                form.setFieldsValue(record);
              }}
            />
          </Tooltip>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id, 'credential')}>
            <Button size="small" icon={<DeleteOutlined />} danger />
          </Popconfirm>
        </Space>
      )
    }
  ];

  // 执行记录表格列
  const executionColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: 'Playbook',
      dataIndex: 'playbook_name',
      key: 'playbook_name',
    },
    {
      title: '清单',
      dataIndex: 'inventory_name',
      key: 'inventory_name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string, record: AnsibleExecutionList) => (
        <Tag color={getStatusColor(status)}>
          {record.status_display}
        </Tag>
      )
    },
    {
      title: '执行时长',
      dataIndex: 'duration',
      key: 'duration',
      render: (duration: number | null) => 
        duration ? `${duration.toFixed(2)}s` : '-'
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (date: string | null) => 
        date ? new Date(date).toLocaleString() : '-'
    },
    {
      title: '执行者',
      dataIndex: 'created_by_username',
      key: 'created_by_username',
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: AnsibleExecutionList) => (
        <Space>
          <Tooltip title="查看日志">
            <Button 
              size="small" 
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedExecution(record);
                setExecutionLogsModalVisible(true);
              }}
            />
          </Tooltip>
          {(record.status === 'running' || record.status === 'pending') && (
            <Tooltip title="取消执行">
              <Popconfirm title="确认取消执行？" onConfirm={() => handleCancel(record.id)}>
                <Button size="small" icon={<StopOutlined />} danger />
              </Popconfirm>
            </Tooltip>
          )}
        </Space>
      )
    }
  ];

  // 主机表格列
  const hostColumns = [
    {
      title: '主机名',
      dataIndex: 'hostname',
      key: 'hostname',
    },
    {
      title: 'IP地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
    },
    {
      title: '端口',
      dataIndex: 'port',
      key: 'port',
      width: 80,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '认证方式',
      dataIndex: 'credential',
      key: 'credential',
      render: (credentialId: number | null, record: AnsibleHost) => {
        if (credentialId) {
          const credential = credentials.find(c => c.id === credentialId);
          return credential ? (
            <Tag color="blue">{credential.name}</Tag>
          ) : (
            <Tag color="orange">凭据未找到</Tag>
          );
        } else if (record.temp_password || record.temp_ssh_key) {
          return <Tag color="gray">临时认证</Tag>;
        } else {
          return <Tag color="red">未配置</Tag>;
        }
      }
    },
    {
      title: '所属组',
      dataIndex: 'groups',
      key: 'groups',
      render: (groups: AnsibleHostGroup[]) => (
        <Space wrap>
          {groups && groups.length > 0 ? (
            groups.map(group => (
              <Tag 
                key={group.id} 
                color="purple"
                style={{ cursor: 'pointer' }}
                onClick={() => {
                  setSelectedHostGroup(group);
                  setHostGroupModalVisible(true);
                }}
              >
                {group.name}
              </Tag>
            ))
          ) : (
            <Tag color="default">未分组</Tag>
          )}
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {status === 'active' ? '活跃' : status === 'failed' ? '失败' : status === 'inactive' ? '非活跃' : '未知'}
        </Tag>
      )
    },
    {
      title: '系统信息',
      dataIndex: 'os_distribution',
      key: 'os_distribution',
      render: (distribution: string, record: AnsibleHost) => 
        distribution ? `${distribution} ${record.os_version}` : '未知'
    },
    {
      title: '最后检查',
      dataIndex: 'last_check',
      key: 'last_check',
      render: (date: string) => date ? new Date(date).toLocaleString() : '未检查'
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: AnsibleHost) => (
        <Space>
          <Tooltip title="检查连通性">
            <Button 
              size="small" 
              icon={<ReloadOutlined />}
              onClick={() => handleCheckConnectivity(record.id)}
            />
          </Tooltip>
          <Tooltip title="收集Facts">
            <Button 
              size="small" 
              icon={<EyeOutlined />}
              onClick={() => handleGatherFacts(record.id)}
            />
          </Tooltip>
          <Tooltip title="查看Facts详情">
            <Button 
              size="small" 
              type="primary"
              ghost
              onClick={() => handleViewFacts(record)}
              disabled={!record.ansible_facts || Object.keys(record.ansible_facts).length === 0}
            >
              详情
            </Button>
          </Tooltip>
          <Tooltip title="编辑">
            <Button 
              size="small" 
              icon={<EditOutlined />}
              onClick={() => {
                setEditingItem(record);
                setModalType('host');
                setModalVisible(true);
                form.setFieldsValue(record);
              }}
            />
          </Tooltip>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id, 'host')}>
            <Button size="small" icon={<DeleteOutlined />} danger />
          </Popconfirm>
        </Space>
      )
    }
  ];

  // 主机组表格列
  const hostGroupColumns = [
    {
      title: '组名',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '父组',
      dataIndex: 'parent_name',
      key: 'parent_name',
      render: (parentName: string) => parentName || '-'
    },
    {
      title: '主机数量',
      dataIndex: 'hosts_count',
      key: 'hosts_count',
      render: (count: number) => <Tag>{count}</Tag>
    },
    {
      title: '创建者',
      dataIndex: 'created_by_username',
      key: 'created_by_username',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString()
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: AnsibleHostGroup) => (
        <Space>
          <Tooltip title="管理主机">
            <Button 
              size="small" 
              type="primary"
              icon={<UserOutlined />}
              onClick={() => {
                setSelectedHostGroup(record);
                setHostGroupModalVisible(true);
              }}
            >
              主机
            </Button>
          </Tooltip>
          <Tooltip title="编辑">
            <Button 
              size="small" 
              icon={<EditOutlined />}
              onClick={() => {
                setEditingItem(record);
                setModalType('hostgroup');
                setModalVisible(true);
                form.setFieldsValue(record);
              }}
            />
          </Tooltip>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id, 'hostgroup')}>
            <Button size="small" icon={<DeleteOutlined />} danger />
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <Title level={2}>Ansible 自动化部署</Title>
        <Space>
          <Button 
            type="dashed" 
            onClick={() => {
              authUtils.setTestToken();
              message.success('测试身份验证已设置');
            }}
          >
            设置测试身份验证
          </Button>
          <Button 
            type="dashed" 
            icon={<PlayCircleOutlined />}
            onClick={handleLoadDemoData}
            loading={loading}
          >
            加载演示数据
          </Button>
        </Space>
      </div>

      {/* 统计卡片 */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总执行次数"
                value={stats.total_executions}
                prefix={<PlayCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="成功执行"
                value={stats.successful_executions}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="失败执行"
                value={stats.failed_executions}
                prefix={<ExclamationCircleOutlined />}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="成功率"
                value={stats.success_rate}
                precision={1}
                suffix="%"
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: stats.success_rate >= 80 ? '#3f8600' : '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 标签页 */}
      <Card>
        <Tabs defaultActiveKey="executions">
          <TabPane tab="执行历史" key="executions">
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setModalType('execute');
                    setModalVisible(true);
                    setEditingItem(null);
                    form.resetFields();
                  }}
                >
                  执行 Playbook
                </Button>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={fetchExecutions}
                >
                  刷新
                </Button>
              </Space>
            </div>
            <Table
              columns={executionColumns}
              dataSource={executions}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />
          </TabPane>

          <TabPane tab="Playbook 管理" key="playbooks">
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setModalType('playbook');
                    setModalVisible(true);
                    setEditingItem(null);
                    form.resetFields();
                  }}
                >
                  新建 Playbook
                </Button>
                <Button 
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setModalType('upload');
                    setModalVisible(true);
                    setEditingItem(null);
                    form.resetFields();
                    form.setFieldValue('upload_type', 'playbook');
                  }}
                >
                  上传文件
                </Button>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={fetchPlaybooks}
                >
                  刷新
                </Button>
              </Space>
            </div>
            <Table
              columns={playbookColumns}
              dataSource={playbooks}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />
          </TabPane>

          <TabPane tab="主机清单" key="inventories">
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setModalType('inventory');
                    setModalVisible(true);
                    setEditingItem(null);
                    form.resetFields();
                  }}
                >
                  新建清单
                </Button>
                <Button 
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setModalType('upload');
                    setModalVisible(true);
                    setEditingItem(null);
                    form.resetFields();
                    form.setFieldValue('upload_type', 'inventory');
                  }}
                >
                  上传文件
                </Button>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={fetchInventories}
                >
                  刷新
                </Button>
              </Space>
            </div>
            <Table
              columns={inventoryColumns}
              dataSource={inventories}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />
          </TabPane>

          <TabPane tab="认证凭据" key="credentials">
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setModalType('credential');
                    setModalVisible(true);
                    setEditingItem(null);
                    form.resetFields();
                  }}
                >
                  新建凭据
                </Button>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={fetchCredentials}
                >
                  刷新
                </Button>
              </Space>
            </div>
            <Table
              columns={credentialColumns}
              dataSource={credentials}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />
          </TabPane>

          <TabPane tab="主机管理" key="hosts">
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setModalType('host');
                    setModalVisible(true);
                    setEditingItem(null);
                    form.resetFields();
                    // 设置主机默认值
                    form.setFieldsValue({
                      port: 22,
                      connection_type: 'ssh',
                      become_method: 'sudo'
                    });
                  }}
                >
                  新建主机
                </Button>
                <Button 
                  icon={<CheckCircleOutlined />}
                  onClick={() => setConnectionTestVisible(true)}
                >
                  连接测试
                </Button>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={fetchHosts}
                >
                  刷新
                </Button>
              </Space>
            </div>
            <Table
              columns={hostColumns}
              dataSource={hosts}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />
          </TabPane>

          <TabPane tab="主机组管理" key="hostgroups">
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setModalType('hostgroup');
                    setModalVisible(true);
                    setEditingItem(null);
                    form.resetFields();
                  }}
                >
                  新建主机组
                </Button>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={fetchHostGroups}
                >
                  刷新
                </Button>
              </Space>
            </div>
            <Table
              columns={hostGroupColumns}
              dataSource={hostGroups}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 模态框 */}
      <Modal
        title={
          modalType === 'inventory' ? (editingItem ? '编辑清单' : '新建清单') :
          modalType === 'playbook' ? (editingItem ? '编辑 Playbook' : '新建 Playbook') :
          modalType === 'credential' ? (editingItem ? '编辑凭据' : '新建凭据') :
          modalType === 'host' ? (editingItem ? '编辑主机' : '新建主机') :
          modalType === 'hostgroup' ? (editingItem ? '编辑主机组' : '新建主机组') :
          modalType === 'upload' ? '上传文件' :
          '执行 Playbook'
        }
        open={modalVisible}
        onOk={modalType === 'execute' ? () => form.submit() : handleModalOk}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setEditingItem(null);
        }}
        width={modalType === 'playbook' ? 800 : 600}
        okText={modalType === 'execute' ? '执行' : '确定'}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={modalType === 'execute' ? handleExecute : undefined}
        >
          {modalType === 'inventory' && (
            <>
              <Form.Item name="name" label="名称" rules={[{ required: true }]}>
                <Input placeholder="请输入清单名称" />
              </Form.Item>
              <Form.Item name="description" label="描述">
                <Input placeholder="请输入清单描述" />
              </Form.Item>
              <Form.Item name="format_type" label="格式" rules={[{ required: true }]}>
                <Select placeholder="请选择格式">
                  <Select.Option value="ini">INI</Select.Option>
                  <Select.Option value="yaml">YAML</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="content" label="内容" rules={[{ required: true }]}>
                <TextArea 
                  rows={10} 
                  placeholder="请输入清单内容"
                />
              </Form.Item>
            </>
          )}

          {modalType === 'playbook' && (
            <>
              <Form.Item name="name" label="名称" rules={[{ required: true }]}>
                <Input placeholder="请输入 Playbook 名称" />
              </Form.Item>
              <Form.Item name="description" label="描述">
                <Input placeholder="请输入 Playbook 描述" />
              </Form.Item>
              <Form.Item name="version" label="版本">
                <Input placeholder="请输入版本号" defaultValue="1.0" />
              </Form.Item>
              <Form.Item name="category" label="分类">
                <Input placeholder="请输入分类" />
              </Form.Item>
              <Form.Item name="is_template" label="类型" valuePropName="checked">
                <Select placeholder="请选择类型">
                  <Select.Option value={false}>普通 Playbook</Select.Option>
                  <Select.Option value={true}>模板</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="content" label="内容" rules={[{ required: true }]}>
                <TextArea 
                  rows={15} 
                  placeholder="请输入 Playbook YAML 内容"
                />
              </Form.Item>
            </>
          )}

          {modalType === 'credential' && (
            <>
              <Form.Item name="name" label="名称" rules={[{ required: true }]}>
                <Input placeholder="请输入凭据名称" />
              </Form.Item>
              <Form.Item name="credential_type" label="类型" rules={[{ required: true }]}>
                <Select placeholder="请选择凭据类型">
                  <Select.Option value="ssh_key">SSH 密钥</Select.Option>
                  <Select.Option value="password">用户名密码</Select.Option>
                  <Select.Option value="vault">Ansible Vault</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="username" label="用户名">
                <Input placeholder="请输入用户名" />
              </Form.Item>
              <Form.Item name="password_input" label="密码">
                <Input.Password placeholder="请输入密码" />
              </Form.Item>
              <Form.Item name="ssh_private_key_input" label="SSH 私钥">
                <TextArea rows={8} placeholder="请输入 SSH 私钥" />
              </Form.Item>
            </>
          )}

          {modalType === 'host' && (
            <>
              <Form.Item name="hostname" label="主机名" rules={[{ required: true }]}>
                <Input placeholder="请输入主机名" />
              </Form.Item>
              <Form.Item name="ip_address" label="IP地址" rules={[{ required: true, type: 'string' }]}>
                <Input placeholder="请输入IP地址" />
              </Form.Item>
              <Form.Item name="port" label="SSH端口" rules={[{ required: true, message: '请输入SSH端口' }]}>
                <Input type="number" placeholder="22" />
              </Form.Item>
              <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
                <Input placeholder="请输入用户名" />
              </Form.Item>
              <Form.Item name="connection_type" label="连接类型">
                <Select placeholder="请选择连接类型">
                  <Select.Option value="ssh">SSH</Select.Option>
                  <Select.Option value="winrm">WinRM</Select.Option>
                  <Select.Option value="local">本地</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="become_method" label="提权方式">
                <Select placeholder="请选择提权方式">
                  <Select.Option value="sudo">sudo</Select.Option>
                  <Select.Option value="su">su</Select.Option>
                  <Select.Option value="pbrun">pbrun</Select.Option>
                  <Select.Option value="pfexec">pfexec</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="credential" label="认证凭据">
                <Select placeholder="请选择已有凭据或留空手动输入认证信息" allowClear>
                  {credentials.map(cred => (
                    <Select.Option key={cred.id} value={cred.id}>
                      {cred.name} ({cred.credential_type_display})
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
              <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
                如果选择了认证凭据，将使用凭据中的认证信息；如果未选择，请在下方手动输入认证信息
              </Text>
              <Form.Item name="temp_password" label="临时密码（仅当未选择凭据时使用）">
                <Input.Password placeholder="请输入密码" />
              </Form.Item>
              <Form.Item name="temp_ssh_key" label="临时SSH私钥（仅当未选择凭据时使用）">
                <TextArea rows={4} placeholder="请输入SSH私钥内容" />
              </Form.Item>
              <Form.Item name="tags" label="主机标签">
                <TextArea 
                  rows={3} 
                  placeholder="请输入JSON格式的标签（可选），如：{&quot;env&quot;: &quot;production&quot;, &quot;type&quot;: &quot;web&quot;}"
                />
              </Form.Item>
            </>
          )}

          {modalType === 'hostgroup' && (
            <>
              <Form.Item name="name" label="组名" rules={[{ required: true }]}>
                <Input placeholder="请输入主机组名称" />
              </Form.Item>
              <Form.Item name="description" label="描述">
                <Input placeholder="请输入主机组描述" />
              </Form.Item>
              <Form.Item name="parent" label="父组">
                <Select placeholder="请选择父组（可选）" allowClear>
                  {hostGroups.map(group => (
                    <Select.Option key={group.id} value={group.id}>
                      {group.name}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item name="variables" label="组变量">
                <TextArea 
                  rows={5} 
                  placeholder="请输入JSON格式的组变量（可选），如：{&quot;env&quot;: &quot;production&quot;, &quot;db_host&quot;: &quot;localhost&quot;}"
                />
              </Form.Item>
            </>
          )}

          {modalType === 'upload' && (
            <>
              <Form.Item name="upload_type" label="上传类型" rules={[{ required: true }]}>
                <Select placeholder="请选择文件类型">
                  <Select.Option value="inventory">Inventory 清单文件</Select.Option>
                  <Select.Option value="playbook">Playbook 文件</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="name" label="名称" rules={[{ required: true }]}>
                <Input placeholder="请输入名称" />
              </Form.Item>
              <Form.Item name="description" label="描述">
                <Input placeholder="请输入描述" />
              </Form.Item>
              <Form.Item name="file" label="文件" rules={[{ required: true }]}>
                <Input type="file" accept=".yml,.yaml,.ini,.txt" />
              </Form.Item>
            </>
          )}

          {modalType === 'execute' && (
            <>
              <Form.Item name="playbook_id" label="Playbook" rules={[{ required: true }]}>
                <Select placeholder="请选择 Playbook">
                  {playbooks.map(pb => (
                    <Select.Option key={pb.id} value={pb.id}>
                      {pb.name}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item name="inventory_id" label="主机清单" rules={[{ required: true }]}>
                <Select placeholder="请选择主机清单">
                  {inventories.map(inv => (
                    <Select.Option key={inv.id} value={inv.id}>
                      {inv.name}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item name="credential_id" label="认证凭据" rules={[{ required: true }]}>
                <Select placeholder="请选择认证凭据">
                  {credentials.map(cred => (
                    <Select.Option key={cred.id} value={cred.id}>
                      {cred.name} ({cred.credential_type_display})
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item name="parameters" label="执行参数">
                <TextArea 
                  rows={4} 
                  placeholder="请输入 JSON 格式的执行参数（可选）"
                />
              </Form.Item>
            </>
          )}
        </Form>
      </Modal>

      {/* 版本管理模态框 */}
      <Modal
        title={`${versionType === 'inventory' ? 'Inventory' : 'Playbook'} 版本历史`}
        open={versionsVisible}
        onCancel={() => {
          setVersionsVisible(false);
          setVersionsList([]);
          setEditingItem(null);
        }}
        width={800}
        footer={[
          <Button key="close" onClick={() => setVersionsVisible(false)}>
            关闭
          </Button>,
          <Button 
            key="create" 
            type="primary" 
            onClick={() => {
              Modal.confirm({
                title: '创建新版本',
                content: (
                  <Form 
                    onFinish={handleCreateVersion}
                    layout="vertical"
                  >
                    <Form.Item name="version" label="版本号" rules={[{ required: true }]}>
                      <Input placeholder="如: v1.1.0" />
                    </Form.Item>
                    <Form.Item name="changelog" label="变更说明">
                      <TextArea rows={3} placeholder="请输入版本变更说明" />
                    </Form.Item>
                    {versionType === 'playbook' && (
                      <Form.Item name="is_release" valuePropName="checked">
                        <input type="checkbox" /> 标记为发布版本
                      </Form.Item>
                    )}
                  </Form>
                ),
                onOk: () => {
                  const form = document.querySelector('form');
                  if (form) {
                    const formData = new FormData(form);
                    const values = Object.fromEntries(formData.entries());
                    handleCreateVersion(values);
                  }
                }
              });
            }}
          >
            创建版本
          </Button>
        ]}
      >
        <Table
          columns={[
            {
              title: '版本号',
              dataIndex: 'version',
              key: 'version',
            },
            {
              title: '变更说明',
              dataIndex: 'changelog',
              key: 'changelog',
              ellipsis: true,
            },
            {
              title: '校验和',
              dataIndex: 'checksum',
              key: 'checksum',
              width: 120,
              render: (checksum: string) => checksum.substring(0, 8) + '...'
            },
            ...(versionType === 'playbook' ? [{
              title: '发布版本',
              dataIndex: 'is_release',
              key: 'is_release',
              render: (isRelease: boolean) => (
                <Tag color={isRelease ? 'green' : 'default'}>
                  {isRelease ? '是' : '否'}
                </Tag>
              )
            }] : []),
            {
              title: '创建者',
              dataIndex: 'created_by_username',
              key: 'created_by_username',
            },
            {
              title: '创建时间',
              dataIndex: 'created_at',
              key: 'created_at',
              render: (date: string) => new Date(date).toLocaleString()
            },
            {
              title: '操作',
              key: 'actions',
              render: (record: any) => (
                <Space>
                  <Popconfirm 
                    title="确认恢复到此版本？" 
                    onConfirm={() => handleRestoreVersion(record.id)}
                  >
                    <Button size="small" type="primary">
                      恢复
                    </Button>
                  </Popconfirm>
                  <Button 
                    size="small"
                    onClick={() => {
                      Modal.info({
                        title: '版本内容',
                        content: (
                          <pre style={{ maxHeight: '400px', overflow: 'auto' }}>
                            {record.content}
                          </pre>
                        ),
                        width: 800
                      });
                    }}
                  >
                    查看内容
                  </Button>
                </Space>
              )
            }
          ]}
          dataSource={versionsList}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Modal>

      {/* 连接测试模态框 */}
      <ConnectionTestModal
        visible={connectionTestVisible}
        onCancel={() => setConnectionTestVisible(false)}
        onSuccess={handleConnectionTestSuccess}
      />

      {/* 主机Facts详情模态框 */}
      <HostFactsModal
        visible={factsModalVisible}
        host={selectedHost}
        onCancel={() => {
          setFactsModalVisible(false);
          setSelectedHost(null);
        }}
      />

      {/* 主机管理弹窗 */}
      <InventoryHostModal
        visible={inventoryHostModalVisible}
        inventory={selectedInventory}
        onCancel={() => {
          setInventoryHostModalVisible(false);
          setSelectedInventory(null);
        }}
        onRefresh={() => {
          fetchInventories(); // 刷新主机清单列表
        }}
      />

      {/* 执行日志弹窗 */}
      <ExecutionLogsModal
        visible={executionLogsModalVisible}
        execution={selectedExecution}
        onCancel={() => {
          setExecutionLogsModalVisible(false);
          setSelectedExecution(null);
        }}
      />

      {/* 主机组管理弹窗 */}
      <HostGroupModal
        visible={hostGroupModalVisible}
        hostGroup={selectedHostGroup}
        onCancel={() => {
          setHostGroupModalVisible(false);
          setSelectedHostGroup(null);
        }}
        onRefresh={() => {
          fetchHostGroups(); // 刷新主机组列表
          fetchHosts(); // 刷新主机列表以更新组关联信息
        }}
      />

      {/* 清单主机组管理弹窗 */}
      <InventoryGroupModal
        visible={inventoryGroupModalVisible}
        inventory={selectedInventory}
        onCancel={() => {
          setInventoryGroupModalVisible(false);
          setSelectedInventory(null);
        }}
        onRefresh={() => {
          fetchInventories(); // 刷新清单列表以更新计数
        }}
      />

      {/* 清单动态管理弹窗 */}
      <InventoryDynamicGeneratorModal
        visible={inventoryDynamicModalVisible}
        inventory={selectedInventory}
        onClose={() => {
          setInventoryDynamicModalVisible(false);
          setSelectedInventory(null);
        }}
        onSuccess={() => {
          fetchInventories(); // 刷新清单列表以更新计数
          fetchHosts(); // 刷新主机列表
          fetchHostGroups(); // 刷新主机组列表
        }}
      />
    </div>
  );
};

export default Ansible;
