import React, { useState, useEffect } from 'react';
import {
  Modal,
  Table,
  Button,
  Space,
  Tag,
  Select,
  message,
  Popconfirm,
  Input,
  Row,
  Col,
  Divider,
  Typography,
  Card
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  SyncOutlined,
  FileTextOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { apiService } from '../services/api';
import type { AnsibleInventory, AnsibleHost } from '../types';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface InventoryHostModalProps {
  visible: boolean;
  inventory: AnsibleInventory | null;
  onCancel: () => void;
  onRefresh?: () => void;
}

interface InventoryHost {
  id: number;
  inventory: number;
  host: number;
  inventory_name: string;
  host_variables: any;
  is_active: boolean;
  inventory_name_display: string;
  host_hostname: string;
  host_ip_address: string;
  host_status: string;
  created_at: string;
  updated_at: string;
}

const InventoryHostModal: React.FC<InventoryHostModalProps> = ({
  visible,
  inventory,
  onCancel,
  onRefresh
}) => {
  const [loading, setLoading] = useState(false);
  const [inventoryHosts, setInventoryHosts] = useState<InventoryHost[]>([]);
  const [availableHosts, setAvailableHosts] = useState<AnsibleHost[]>([]);
  const [selectedHostIds, setSelectedHostIds] = useState<number[]>([]);
  const [addHostsVisible, setAddHostsVisible] = useState(false);
  const [dynamicInventoryVisible, setDynamicInventoryVisible] = useState(false);
  const [dynamicContent, setDynamicContent] = useState('');
  const [dynamicFormat, setDynamicFormat] = useState<'ini' | 'yaml'>('ini');

  // 获取清单关联的主机
  const fetchInventoryHosts = async () => {
    if (!inventory) return;
    
    try {
      setLoading(true);
      const data = await apiService.getInventoryHosts(inventory.id);
      setInventoryHosts(data);
    } catch (error) {
      message.error('获取关联主机失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取所有可用主机
  const fetchAvailableHosts = async () => {
    if (!inventory) return;
    
    try {
      const allHosts = await apiService.getAnsibleHosts();
      const currentHostIds = inventoryHosts.map(ih => ih.host);
      const available = allHosts.filter(host => !currentHostIds.includes(host.id));
      setAvailableHosts(available);
    } catch (error) {
      message.error('获取可用主机失败');
    }
  };

  // 添加主机到清单
  const handleAddHosts = async () => {
    if (!inventory || selectedHostIds.length === 0) return;

    try {
      await apiService.addHostsToInventory(inventory.id, {
        host_ids: selectedHostIds,
        is_active: true
      });
      message.success(`成功添加 ${selectedHostIds.length} 个主机到清单`);
      setSelectedHostIds([]);
      setAddHostsVisible(false);
      fetchInventoryHosts();
      onRefresh?.();
    } catch (error) {
      message.error('添加主机失败');
    }
  };

  // 移除主机
  const handleRemoveHost = async (hostId: number) => {
    if (!inventory) return;

    try {
      await apiService.removeHostsFromInventory(inventory.id, [hostId]);
      message.success('主机已从清单中移除');
      fetchInventoryHosts();
      onRefresh?.();
    } catch (error) {
      message.error('移除主机失败');
    }
  };

  // 生成动态清单
  const handleGenerateDynamicInventory = async () => {
    if (!inventory) return;

    try {
      setLoading(true);
      const result = await apiService.generateDynamicInventory(inventory.id, dynamicFormat);
      setDynamicContent(result.content);
      setDynamicInventoryVisible(true);
      message.success(`生成 ${result.format_type.toUpperCase()} 格式清单成功（${result.hosts_count} 个主机）`);
    } catch (error) {
      message.error('生成动态清单失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible && inventory) {
      fetchInventoryHosts();
    }
  }, [visible, inventory]);

  useEffect(() => {
    if (addHostsVisible) {
      fetchAvailableHosts();
    }
  }, [addHostsVisible, inventoryHosts]);

  // 关联主机表格列
  const columns = [
    {
      title: '清单名称',
      dataIndex: 'inventory_name',
      key: 'inventory_name',
    },
    {
      title: '主机名',
      dataIndex: 'host_hostname',
      key: 'host_hostname',
    },
    {
      title: 'IP地址',
      dataIndex: 'host_ip_address',
      key: 'host_ip_address',
    },
    {
      title: '主机状态',
      dataIndex: 'host_status',
      key: 'host_status',
      render: (status: string) => {
        const color = status === 'active' ? 'green' : 
                     status === 'failed' ? 'red' : 
                     status === 'inactive' ? 'orange' : 'gray';
        const text = status === 'active' ? '活跃' : 
                     status === 'failed' ? '失败' : 
                     status === 'inactive' ? '非活跃' : '未知';
        return <Tag color={color}>{text}</Tag>;
      }
    },
    {
      title: '激活状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'gray'}>
          {isActive ? '激活' : '未激活'}
        </Tag>
      )
    },
    {
      title: '主机变量',
      dataIndex: 'host_variables',
      key: 'host_variables',
      render: (variables: any) => {
        const varCount = Object.keys(variables || {}).length;
        return varCount > 0 ? (
          <Tag color="blue">{varCount} 个变量</Tag>
        ) : (
          <Text disabled>无变量</Text>
        );
      }
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: InventoryHost) => (
        <Space>
          <Popconfirm
            title="确认移除该主机？"
            onConfirm={() => handleRemoveHost(record.host)}
          >
            <Button size="small" icon={<DeleteOutlined />} danger />
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <>
      <Modal
        title={`清单主机管理 - ${inventory?.name}`}
        open={visible}
        onCancel={onCancel}
        width={1200}
        footer={[
          <Button key="close" onClick={onCancel}>
            关闭
          </Button>
        ]}
      >
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col flex="auto">
            <Space>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setAddHostsVisible(true)}
              >
                添加主机
              </Button>
              <Button
                icon={<FileTextOutlined />}
                onClick={handleGenerateDynamicInventory}
                loading={loading}
              >
                生成动态清单
              </Button>
              <Select
                value={dynamicFormat}
                onChange={setDynamicFormat}
                style={{ width: 100 }}
              >
                <Select.Option value="ini">INI</Select.Option>
                <Select.Option value="yaml">YAML</Select.Option>
              </Select>
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchInventoryHosts}
                loading={loading}
              >
                刷新
              </Button>
            </Space>
          </Col>
          <Col>
            <Text strong>
              关联主机: {inventoryHosts.length} 个
            </Text>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={inventoryHosts}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          size="small"
        />
      </Modal>

      {/* 添加主机模态框 */}
      <Modal
        title="添加主机到清单"
        open={addHostsVisible}
        onOk={handleAddHosts}
        onCancel={() => {
          setAddHostsVisible(false);
          setSelectedHostIds([]);
        }}
        okText="添加"
        cancelText="取消"
        okButtonProps={{ disabled: selectedHostIds.length === 0 }}
      >
        <div style={{ marginBottom: 16 }}>
          <Text>选择要添加到清单的主机：</Text>
        </div>
        <Select
          mode="multiple"
          placeholder="请选择主机"
          style={{ width: '100%' }}
          value={selectedHostIds}
          onChange={setSelectedHostIds}
          showSearch
          filterOption={(input, option) =>
            String(option?.children)?.toLowerCase().includes(input.toLowerCase())
          }
        >
          {availableHosts.map(host => (
            <Select.Option key={host.id} value={host.id}>
              {host.hostname} ({host.ip_address})
            </Select.Option>
          ))}
        </Select>
        <div style={{ marginTop: 8 }}>
          <Text type="secondary">
            可用主机: {availableHosts.length} 个
          </Text>
        </div>
      </Modal>

      {/* 动态清单内容模态框 */}
      <Modal
        title={`动态清单内容 (${dynamicFormat.toUpperCase()})`}
        open={dynamicInventoryVisible}
        onCancel={() => setDynamicInventoryVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setDynamicInventoryVisible(false)}>
            关闭
          </Button>,
          <Button
            key="copy"
            type="primary"
            onClick={() => {
              navigator.clipboard.writeText(dynamicContent);
              message.success('已复制到剪贴板');
            }}
          >
            复制内容
          </Button>
        ]}
      >
        <Card>
          <TextArea
            value={dynamicContent}
            rows={20}
            readOnly
            style={{ fontFamily: 'monospace' }}
          />
        </Card>
      </Modal>
    </>
  );
};

export default InventoryHostModal;
