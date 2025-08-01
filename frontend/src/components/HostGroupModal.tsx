import React, { useState, useEffect } from 'react';
import {
  Modal,
  Table,
  Button,
  Space,
  Tag,
  message,
  Popconfirm,
  Transfer,
  Tabs,
  Typography,
  Card,
  Row,
  Col,
  Statistic,
  Tooltip,
  Input,
  Form
} from 'antd';
import {
  PlusOutlined,
  MinusOutlined,
  ReloadOutlined,
  UserOutlined,
  SettingOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { apiService } from '../services/api';
import type { AnsibleHostGroup, AnsibleHost } from '../types';

const { TabPane } = Tabs;
const { Title, Text } = Typography;
const { TextArea } = Input;

interface HostGroupModalProps {
  visible: boolean;
  hostGroup: AnsibleHostGroup | null;
  onCancel: () => void;
  onRefresh?: () => void;
}

const HostGroupModal: React.FC<HostGroupModalProps> = ({
  visible,
  hostGroup,
  onCancel,
  onRefresh
}) => {
  const [loading, setLoading] = useState(false);
  const [groupHosts, setGroupHosts] = useState<AnsibleHost[]>([]);
  const [availableHosts, setAvailableHosts] = useState<AnsibleHost[]>([]);
  const [selectedHostIds, setSelectedHostIds] = useState<number[]>([]);
  const [addHostsVisible, setAddHostsVisible] = useState(false);
  const [hostVariablesVisible, setHostVariablesVisible] = useState(false);
  const [selectedHostForVariables, setSelectedHostForVariables] = useState<AnsibleHost | null>(null);
  const [variablesForm] = Form.useForm();

  // 获取主机组内的主机
  const fetchGroupHosts = async () => {
    if (!hostGroup) return;
    
    try {
      setLoading(true);
      const data = await apiService.getHostGroupHosts(hostGroup.id);
      setGroupHosts(data);
    } catch (error) {
      message.error('获取主机组内主机失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取所有可用主机
  const fetchAvailableHosts = async () => {
    if (!hostGroup) return;
    
    try {
      const allHosts = await apiService.getAnsibleHosts();
      const currentHostIds = groupHosts.map(host => host.id);
      const available = allHosts.filter(host => !currentHostIds.includes(host.id));
      setAvailableHosts(available);
    } catch (error) {
      message.error('获取可用主机失败');
    }
  };

  // 添加主机到组
  const handleAddHosts = async () => {
    if (!hostGroup || selectedHostIds.length === 0) return;

    try {
      await apiService.addHostsToGroup(hostGroup.id, {
        host_ids: selectedHostIds
      });
      message.success(`成功添加 ${selectedHostIds.length} 个主机到组`);
      setSelectedHostIds([]);
      setAddHostsVisible(false);
      fetchGroupHosts();
      onRefresh?.();
    } catch (error) {
      message.error('添加主机失败');
    }
  };

  // 移除主机
  const handleRemoveHost = async (hostId: number) => {
    if (!hostGroup) return;

    try {
      await apiService.removeHostFromGroup(hostGroup.id, hostId);
      message.success('成功移除主机');
      fetchGroupHosts();
      onRefresh?.();
    } catch (error) {
      message.error('移除主机失败');
    }
  };

  // 批量移除主机
  const handleBatchRemove = async (hostIds: number[]) => {
    if (!hostGroup || hostIds.length === 0) return;

    try {
      await apiService.removeHostsFromGroup(hostGroup.id, {
        host_ids: hostIds
      });
      message.success(`成功移除 ${hostIds.length} 个主机`);
      fetchGroupHosts();
      onRefresh?.();
    } catch (error) {
      message.error('批量移除主机失败');
    }
  };

  // 设置主机变量
  const handleSetHostVariables = async (host: AnsibleHost) => {
    setSelectedHostForVariables(host);
    // 这里可以获取主机在组中的变量
    try {
      // 假设有获取主机组成员变量的API
      const membershipData = await apiService.getHostGroupMembership(hostGroup!.id, host.id);
      variablesForm.setFieldsValue({
        variables: JSON.stringify(membershipData.variables || {}, null, 2)
      });
    } catch (error) {
      // 如果没有现有变量，设置为空对象
      variablesForm.setFieldsValue({
        variables: JSON.stringify({}, null, 2)
      });
    }
    setHostVariablesVisible(true);
  };

  // 保存主机变量
  const handleSaveHostVariables = async () => {
    if (!hostGroup || !selectedHostForVariables) return;

    try {
      const values = await variablesForm.validateFields();
      let variables = {};
      try {
        variables = JSON.parse(values.variables);
      } catch (e) {
        message.error('变量格式不正确，请输入有效的JSON');
        return;
      }

      await apiService.updateHostGroupMembership(hostGroup.id, selectedHostForVariables.id, {
        variables
      });
      message.success('主机变量设置成功');
      setHostVariablesVisible(false);
      setSelectedHostForVariables(null);
      variablesForm.resetFields();
    } catch (error) {
      message.error('设置主机变量失败');
    }
  };

  useEffect(() => {
    if (visible && hostGroup) {
      fetchGroupHosts();
    }
  }, [visible, hostGroup]);

  useEffect(() => {
    if (addHostsVisible) {
      fetchAvailableHosts();
    }
  }, [addHostsVisible, groupHosts]);

  // 状态标签颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'inactive': return 'orange';
      case 'failed': return 'red';
      case 'unknown': return 'gray';
      default: return 'default';
    }
  };

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
      title: '操作',
      key: 'actions',
      render: (record: AnsibleHost) => (
        <Space>
          <Tooltip title="设置主机变量">
            <Button 
              size="small" 
              icon={<SettingOutlined />}
              onClick={() => handleSetHostVariables(record)}
            />
          </Tooltip>
          <Popconfirm 
            title="确认从组中移除该主机？" 
            onConfirm={() => handleRemoveHost(record.id)}
          >
            <Button size="small" icon={<MinusOutlined />} danger />
          </Popconfirm>
        </Space>
      )
    }
  ];

  // Transfer数据源
  const transferDataSource = availableHosts.map(host => ({
    key: host.id.toString(),
    title: `${host.hostname} (${host.ip_address})`,
    description: host.status === 'active' ? '活跃' : '非活跃',
    disabled: host.status !== 'active'
  }));

  const transferTargetKeys = selectedHostIds.map(id => id.toString());

  return (
    <>
      <Modal
        title={`主机组管理 - ${hostGroup?.name || ''}`}
        open={visible}
        onCancel={onCancel}
        width={1200}
        footer={[
          <Button key="close" onClick={onCancel}>
            关闭
          </Button>
        ]}
      >
        {hostGroup && (
          <div>
            {/* 主机组信息卡片 */}
            <Card style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic
                    title="组名"
                    value={hostGroup.name}
                    prefix={<UserOutlined />}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="主机数量"
                    value={hostGroup.hosts_count || 0}
                    prefix={<EyeOutlined />}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="父组"
                    value={hostGroup.parent_name || '无'}
                  />
                </Col>
              </Row>
              {hostGroup.description && (
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary">描述：{hostGroup.description}</Text>
                </div>
              )}
            </Card>

            <Tabs defaultActiveKey="hosts">
              <TabPane tab={`主机列表 (${groupHosts.length})`} key="hosts">
                <div style={{ marginBottom: 16 }}>
                  <Space>
                    <Button 
                      type="primary" 
                      icon={<PlusOutlined />}
                      onClick={() => setAddHostsVisible(true)}
                    >
                      添加主机
                    </Button>
                    <Button 
                      icon={<ReloadOutlined />}
                      onClick={fetchGroupHosts}
                    >
                      刷新
                    </Button>
                    <Button 
                      danger
                      onClick={() => {
                        const selectedRows = Table.prototype.getSelectedRowKeys?.() || [];
                        if (selectedRows.length > 0) {
                          handleBatchRemove(selectedRows as number[]);
                        } else {
                          message.warning('请先选择要移除的主机');
                        }
                      }}
                    >
                      批量移除
                    </Button>
                  </Space>
                </div>
                <Table
                  columns={hostColumns}
                  dataSource={groupHosts}
                  rowKey="id"
                  loading={loading}
                  pagination={{ pageSize: 10 }}
                  rowSelection={{
                    type: 'checkbox',
                  }}
                />
              </TabPane>

              <TabPane tab="组变量" key="variables">
                <Card>
                  <Title level={4}>组级别变量</Title>
                  <pre style={{ 
                    background: '#f5f5f5', 
                    padding: '12px', 
                    borderRadius: '4px',
                    overflow: 'auto',
                    maxHeight: '300px'
                  }}>
                    {JSON.stringify(hostGroup.variables || {}, null, 2)}
                  </pre>
                  <Text type="secondary">
                    这些变量将应用于组内所有主机。可以在主机组编辑页面修改这些变量。
                  </Text>
                </Card>
              </TabPane>

              <TabPane tab="层级结构" key="hierarchy">
                <Card>
                  <Title level={4}>组织结构</Title>
                  <div style={{ padding: '16px 0' }}>
                    {hostGroup.parent_name && (
                      <div style={{ marginBottom: 12 }}>
                        <Text strong>父组：</Text>
                        <Tag color="blue">{hostGroup.parent_name}</Tag>
                      </div>
                    )}
                    <div style={{ marginBottom: 12 }}>
                      <Text strong>当前组：</Text>
                      <Tag color="green">{hostGroup.name}</Tag>
                    </div>
                    {hostGroup.children && hostGroup.children.length > 0 && (
                      <div>
                        <Text strong>子组：</Text>
                        <div style={{ marginTop: 8 }}>
                          {hostGroup.children.map(child => (
                            <Tag key={child.id} color="orange" style={{ marginBottom: 4 }}>
                              {child.name}
                            </Tag>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </Card>
              </TabPane>
            </Tabs>
          </div>
        )}
      </Modal>

      {/* 添加主机模态框 */}
      <Modal
        title="添加主机到组"
        open={addHostsVisible}
        onOk={handleAddHosts}
        onCancel={() => {
          setAddHostsVisible(false);
          setSelectedHostIds([]);
        }}
        width={800}
        okText="添加选中主机"
        okButtonProps={{ disabled: selectedHostIds.length === 0 }}
      >
        <div style={{ marginBottom: 16 }}>
          <Text>选择要添加到组 <Tag>{hostGroup?.name}</Tag> 的主机：</Text>
        </div>
        <Transfer
          dataSource={transferDataSource}
          targetKeys={transferTargetKeys}
          onChange={(targetKeys) => {
            setSelectedHostIds(targetKeys.map(key => parseInt(key.toString())));
          }}
          render={item => item.title}
          titles={['可用主机', '选中主机']}
          listStyle={{
            width: 350,
            height: 400,
          }}
          showSearch
          filterOption={(inputValue, option) =>
            option.title.toLowerCase().indexOf(inputValue.toLowerCase()) > -1
          }
        />
      </Modal>

      {/* 主机变量设置模态框 */}
      <Modal
        title={`设置主机变量 - ${selectedHostForVariables?.hostname}`}
        open={hostVariablesVisible}
        onOk={handleSaveHostVariables}
        onCancel={() => {
          setHostVariablesVisible(false);
          setSelectedHostForVariables(null);
          variablesForm.resetFields();
        }}
        width={600}
        okText="保存变量"
      >
        <Form form={variablesForm} layout="vertical">
          <Form.Item 
            name="variables" 
            label="主机在组中的变量（JSON格式）"
            rules={[
              {
                validator: (_, value) => {
                  if (!value) return Promise.resolve();
                  try {
                    JSON.parse(value);
                    return Promise.resolve();
                  } catch (e) {
                    return Promise.reject(new Error('请输入有效的JSON格式'));
                  }
                }
              }
            ]}
          >
            <TextArea 
              rows={12} 
              placeholder='{"key": "value", "env": "production"}'
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>
          <Text type="secondary">
            这些变量仅对该主机在此组中生效，会覆盖组级别的同名变量。
          </Text>
        </Form>
      </Modal>
    </>
  );
};

export default HostGroupModal;
