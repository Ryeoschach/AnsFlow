import React, { useState, useEffect } from 'react';
import {
  Modal,
  Tabs,
  Table,
  Button,
  Space,
  Tag,
  Transfer,
  message,
  Form,
  Input,
  Switch,
  Typography,
  Tooltip,
  Popconfirm
} from 'antd';
import {
  PlusOutlined,
  MinusOutlined,
  EditOutlined,
  DeleteOutlined,
  TeamOutlined
} from '@ant-design/icons';
import { apiService } from '../services/api';
import { ansibleApiService } from '../services/ansibleApiService';
import { useAuthStore } from '../stores/auth';
import type { AnsibleInventory, AnsibleHostGroup, InventoryGroup } from '../types';

const { TabPane } = Tabs;
const { TextArea } = Input;
const { Text } = Typography;

interface InventoryGroupModalProps {
  visible: boolean;
  inventory: AnsibleInventory | null;
  onCancel: () => void;
  onRefresh: () => void;
}

interface TransferItem {
  key: string;
  title: string;
  description?: string;
  disabled?: boolean;
}

const InventoryGroupModal: React.FC<InventoryGroupModalProps> = ({
  visible,
  inventory,
  onCancel,
  onRefresh
}) => {
  const { isAuthenticated, getAuthDebugInfo } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [allGroups, setAllGroups] = useState<AnsibleHostGroup[]>([]);
  const [inventoryGroups, setInventoryGroups] = useState<InventoryGroup[]>([]);
  const [selectedGroups, setSelectedGroups] = useState<string[]>([]);
  const [targetKeys, setTargetKeys] = useState<string[]>([]);
  const [editingGroup, setEditingGroup] = useState<InventoryGroup | null>(null);
  const [groupEditVisible, setGroupEditVisible] = useState(false);
  const [form] = Form.useForm();

  // 获取所有主机组
  const fetchAllGroups = async () => {
    try {
      const groups = await apiService.getAnsibleHostGroups();
      setAllGroups(groups);
    } catch (error) {
      message.error('获取主机组列表失败');
    }
  };

  // 获取清单中的主机组
  const fetchInventoryGroups = async () => {
    if (!inventory) return;
    
    try {
      setLoading(true);
      console.log('正在获取清单主机组，清单ID:', inventory.id);
      
      const groups = await apiService.getInventoryGroups(inventory.id);
      console.log('获取到的主机组数据:', groups);
      
      setInventoryGroups(groups);
      
      // 设置 Transfer 组件的目标键
      const activeGroupIds = groups
        .filter(g => g.is_active)
        .map(g => (g.group_id || g.group).toString());
      console.log('设置的目标键:', activeGroupIds);
      setTargetKeys(activeGroupIds);
      
    } catch (error: any) {
      console.error('获取清单主机组失败，详细错误:', error);
      console.error('错误响应:', error.response);
      
      let errorMessage = '获取清单主机组失败';
      
      if (error.response?.status === 401) {
        errorMessage = '认证失败，请重新登录';
      } else if (error.response?.status === 403) {
        errorMessage = '权限不足，无法访问主机组数据';
      } else if (error.response?.status === 404) {
        errorMessage = '指定的清单不存在';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = `获取清单主机组失败: ${error.message}`;
      }
      
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible && inventory) {
      fetchAllGroups();
      fetchInventoryGroups();
    }
  }, [visible, inventory]);

  // 处理主机组转移
  const handleTransferChange = async (newTargetKeys: React.Key[]) => {
    if (!inventory) return;

    // 检查认证状态
    if (!isAuthenticated) {
      message.error('未登录，请先登录');
      return;
    }

    const targetKeysStr = newTargetKeys.map(key => key.toString());
    const currentKeys = new Set(targetKeys);
    const newKeysSet = new Set(targetKeysStr);
    
    // 找出要添加和移除的主机组
    const toAdd = targetKeysStr.filter(key => !currentKeys.has(key));
    const toRemove = targetKeys.filter(key => !newKeysSet.has(key));

    try {
      setLoading(true);

      // 添加主机组
      if (toAdd.length > 0) {
        console.log('添加主机组:', toAdd);
        await ansibleApiService.addGroupsToInventory(
          inventory.id, 
          toAdd.map(id => parseInt(id))
        );
        console.log('主机组添加成功');
      }

      // 移除主机组
      if (toRemove.length > 0) {
        console.log('移除主机组:', toRemove);
        const result = await ansibleApiService.removeGroupsFromInventory(
          inventory.id,
          toRemove.map(id => parseInt(id))
        );
        console.log('主机组移除成功:', result);
        
        // 如果后端返回了最新统计数据，可以在这里处理
        if (result.current_stats) {
          console.log('最新统计数据:', result.current_stats);
        }
      }

      setTargetKeys(targetKeysStr);
      
      // 立即刷新本地数据
      await fetchInventoryGroups();
      
      // 刷新父组件的清单列表（触发统计数据更新）
      onRefresh();
      
      // 短暂延迟后再次刷新，确保数据同步
      setTimeout(() => {
        onRefresh();
      }, 500);
      
      message.success(`主机组管理操作完成`);
    } catch (error: any) {
      console.error('主机组操作失败:', error);
      
      // 获取认证调试信息
      const authInfo = getAuthDebugInfo();
      console.error('认证调试信息:', authInfo);
      
      let errorMessage = '主机组操作失败';
      
      if (error.message.includes('认证失败')) {
        errorMessage = '身份验证失败，请重新登录';
      } else if (error.message.includes('权限不足')) {
        errorMessage = '权限不足，无法执行此操作';
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 编辑主机组配置
  const handleEditGroup = (group: InventoryGroup) => {
    setEditingGroup(group);
    form.setFieldsValue({
      inventory_name: group.inventory_name,
      group_variables: JSON.stringify(group.group_variables, null, 2),
      is_active: group.is_active
    });
    setGroupEditVisible(true);
  };

  // 保存主机组配置
  const handleSaveGroupConfig = async () => {
    if (!editingGroup) return;

    try {
      const values = await form.validateFields();
      let variables = {};

      try {
        variables = JSON.parse(values.group_variables || '{}');
      } catch (e) {
        message.error('组变量格式不正确，请输入有效的JSON');
        return;
      }

      // 这里需要调用更新 InventoryGroup 的 API
      // 暂时使用批量更新API
      await apiService.batchAddInventoryGroups({
        inventory_id: inventory!.id,
        group_ids: [editingGroup.group],
        inventory_names: [values.inventory_name],
        group_variables: [variables],
        is_active: values.is_active
      });

      await fetchInventoryGroups();
      setGroupEditVisible(false);
      setEditingGroup(null);
      form.resetFields();
      message.success('主机组配置更新成功');
    } catch (error) {
      message.error('更新主机组配置失败');
    }
  };

  // 移除单个主机组
  const handleRemoveGroup = async (groupId: number) => {
    if (!inventory) return;

    try {
      console.log('正在移除单个主机组:', groupId);
      await apiService.removeGroupsFromInventory(inventory.id, { group_ids: [groupId] });
      await fetchInventoryGroups();
      
      // 更新 targetKeys
      setTargetKeys(prev => prev.filter(key => key !== groupId.toString()));
      
      onRefresh();
      message.success('主机组已移除');
    } catch (error: any) {
      console.error('移除主机组失败:', error);
      let errorMessage = '移除主机组失败';
      
      if (error.response?.status === 401) {
        errorMessage = '身份验证失败，请重新登录';
      } else if (error.response?.status === 403) {
        errorMessage = '权限不足，无法执行此操作';
      } else if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      message.error(errorMessage);
    }
  };

  // 准备 Transfer 数据源
  const transferDataSource: TransferItem[] = allGroups.map(group => ({
    key: group.id.toString(),
    title: group.name,
    description: group.description || `${group.hosts_count || 0} 个主机`
  }));

  // 清单中主机组表格列
  const groupColumns = [
    {
      title: '组名',
      dataIndex: 'group_name',
      key: 'group_name',
      render: (name: string, record: InventoryGroup) => (
        <Space>
          <TeamOutlined />
          <span>{name}</span>
          {record.inventory_name !== name && (
            <Text type="secondary">({record.inventory_name})</Text>
          )}
        </Space>
      )
    },
    {
      title: '描述',
      dataIndex: 'group_description',
      key: 'group_description',
      ellipsis: true
    },
    {
      title: '主机数量',
      dataIndex: 'hosts_count',
      key: 'hosts_count',
      render: (count: number) => <Tag color="blue">{count || 0}</Tag>
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? '激活' : '禁用'}
        </Tag>
      )
    },
    {
      title: '变量数',
      dataIndex: 'group_variables',
      key: 'group_variables',
      render: (variables: Record<string, any>) => (
        <Tag>{Object.keys(variables || {}).length}</Tag>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: InventoryGroup) => (
        <Space>
          <Tooltip title="编辑配置">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEditGroup(record)}
            />
          </Tooltip>
          <Tooltip title="移除">
            <Popconfirm
              title="确认移除此主机组？"
              onConfirm={() => handleRemoveGroup(record.group)}
            >
              <Button
                size="small"
                icon={<MinusOutlined />}
                danger
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <>
      <Modal
        title={`管理清单主机组 - ${inventory?.name}`}
        open={visible}
        onCancel={onCancel}
        width={1000}
        footer={[
          <Button key="close" onClick={onCancel}>
            关闭
          </Button>
        ]}
        loading={loading}
      >
        <Tabs defaultActiveKey="groups">
          <TabPane tab="主机组列表" key="groups">
            <Table
              columns={groupColumns}
              dataSource={inventoryGroups}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
              size="small"
            />
          </TabPane>

          <TabPane tab="管理主机组" key="add">
            <div style={{ marginBottom: 16 }}>
              <Text type="secondary">
                管理清单中的主机组。左侧为可用主机组，右侧为已添加的主机组。
              </Text>
              <br />
              <Text type="secondary">
                • 双击项目或使用箭头按钮在两侧之间移动
              </Text>
              <br />
              <Text type="secondary">
                • 选中项目后点击箭头按钮进行批量操作
              </Text>
            </div>
            <Transfer
              dataSource={transferDataSource}
              targetKeys={targetKeys}
              selectedKeys={selectedGroups}
              onChange={handleTransferChange}
              onSelectChange={(sourceSelectedKeys, targetSelectedKeys) => {
                const allSelected = [
                  ...sourceSelectedKeys.map(key => key.toString()), 
                  ...targetSelectedKeys.map(key => key.toString())
                ];
                setSelectedGroups(allSelected);
              }}
              render={item => `${item.title} - ${item.description}`}
              titles={['可用主机组', '清单中的主机组']}
              operations={['添加到清单', '从清单移除']}
              style={{ marginBottom: 16 }}
              showSearch
              filterOption={(inputValue, option) =>
                option.title.toLowerCase().indexOf(inputValue.toLowerCase()) > -1
              }
            />
            <div style={{ marginTop: 16, padding: '8px', backgroundColor: '#f6f6f6', borderRadius: '4px' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                💡 操作提示：选中要操作的主机组，然后点击中间的箭头按钮进行添加或移除操作
              </Text>
            </div>
          </TabPane>
        </Tabs>
      </Modal>

      {/* 主机组配置编辑模态框 */}
      <Modal
        title="编辑主机组配置"
        open={groupEditVisible}
        onOk={handleSaveGroupConfig}
        onCancel={() => {
          setGroupEditVisible(false);
          setEditingGroup(null);
          form.resetFields();
        }}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="inventory_name"
            label="在清单中的名称"
            rules={[{ required: true, message: '请输入组名称' }]}
          >
            <Input placeholder="请输入在清单中显示的组名称" />
          </Form.Item>

          <Form.Item name="group_variables" label="组变量">
            <TextArea
              rows={8}
              placeholder="请输入JSON格式的组变量，如：{&quot;env&quot;: &quot;production&quot;}"
            />
          </Form.Item>

          <Form.Item name="is_active" label="是否激活" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default InventoryGroupModal;
