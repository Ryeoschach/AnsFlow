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
  ReloadOutlined
} from '@ant-design/icons';
import { apiService } from '../services/api';
import type { 
  AnsibleStats, 
  AnsibleInventory, 
  AnsiblePlaybook, 
  AnsibleCredential, 
  AnsibleExecutionList 
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
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState<'inventory' | 'playbook' | 'credential' | 'execute'>('inventory');
  const [editingItem, setEditingItem] = useState<any>(null);
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

  useEffect(() => {
    fetchStats();
    fetchInventories();
    fetchPlaybooks();
    fetchCredentials();
    fetchExecutions();
  }, []);

  // 处理创建/编辑
  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
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

  // 处理删除
  const handleDelete = async (id: number, type: 'inventory' | 'playbook' | 'credential') => {
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

  // 状态标签颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'green';
      case 'failed': return 'red';
      case 'running': return 'blue';
      case 'pending': return 'orange';
      case 'cancelled': return 'gray';
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
                // TODO: 显示日志详情
                message.info('日志查看功能开发中');
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

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Ansible 自动化部署</Title>

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
        </Tabs>
      </Card>

      {/* 模态框 */}
      <Modal
        title={
          modalType === 'inventory' ? (editingItem ? '编辑清单' : '新建清单') :
          modalType === 'playbook' ? (editingItem ? '编辑 Playbook' : '新建 Playbook') :
          modalType === 'credential' ? (editingItem ? '编辑凭据' : '新建凭据') :
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
    </div>
  );
};

export default Ansible;
