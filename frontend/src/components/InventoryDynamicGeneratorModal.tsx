import React, { useState, useEffect } from 'react';
import {
  Modal,
  Tabs,
  Transfer,
  Button,
  Space,
  message,
  Typography,
  Card,
  Tag,
  Divider
} from 'antd';
import { 
  UserOutlined, 
  TeamOutlined, 
  EyeOutlined, 
  SaveOutlined 
} from '@ant-design/icons';
import { apiService } from '../services/api';
import { AnsibleInventory, AnsibleHost, AnsibleHostGroup } from '../types/ansible';

const { TabPane } = Tabs;
const { Text, Paragraph } = Typography;

interface InventoryDynamicGeneratorModalProps {
  visible: boolean;
  onClose: () => void;
  inventory: AnsibleInventory | null;
  onSuccess: () => void;
}

interface TransferItem {
  key: string;
  title: string;
  description: string;
  type: 'host' | 'group';
  disabled?: boolean;
}

interface GeneratedInventory {
  content: string;
  format_type: string;
  hosts_count: number;
  groups_count: number;
  summary: string;
}

const InventoryDynamicGeneratorModal: React.FC<InventoryDynamicGeneratorModalProps> = ({
  visible,
  onClose,
  inventory,
  onSuccess
}) => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('hosts');
  
  // 主机相关状态
  const [allHosts, setAllHosts] = useState<AnsibleHost[]>([]);
  const [selectedHostKeys, setSelectedHostKeys] = useState<React.Key[]>([]);
  const [hostTargetKeys, setHostTargetKeys] = useState<React.Key[]>([]);
  
  // 主机组相关状态
  const [allGroups, setAllGroups] = useState<AnsibleHostGroup[]>([]);
  const [selectedGroupKeys, setSelectedGroupKeys] = useState<React.Key[]>([]);
  const [groupTargetKeys, setGroupTargetKeys] = useState<React.Key[]>([]);
  
  // 预览相关状态
  const [generatedInventory, setGeneratedInventory] = useState<GeneratedInventory | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // 获取所有主机
  const fetchHosts = async () => {
    try {
      console.log('🔍 开始获取主机列表');
      const hosts = await apiService.getAnsibleHosts();
      console.log('✅ 主机列表获取成功:', hosts.length, '个主机');
      setAllHosts(hosts);
      
      // 获取已经在清单中的主机
      if (inventory) {
        console.log('🔍 获取清单中的主机，清单ID:', inventory.id);
        const inventoryHosts = await apiService.getInventoryHosts(inventory.id);
        console.log('✅ 清单主机获取成功:', inventoryHosts);
        
        // 修复数据映射 - 使用正确的字段名
        const existingHostIds = inventoryHosts.map(ih => {
          // 根据后端返回的数据结构调整
          const hostId = ih.host?.id || ih.host_id;
          return hostId ? hostId.toString() : null;
        }).filter((id): id is string => id !== null);
        
        console.log('📊 已存在的主机IDs:', existingHostIds);
        setHostTargetKeys(existingHostIds);
      }
    } catch (error: any) {
      console.error('❌ 获取主机列表失败:', error);
      console.error('错误详情:', {
        message: error.message,
        status: error.response?.status,
        data: error.response?.data
      });
      message.error('获取主机列表失败');
    }
  };

  // 获取所有主机组
  const fetchGroups = async () => {
    try {
      console.log('🔍 开始获取主机组列表');
      const groups = await apiService.getAnsibleHostGroups();
      console.log('✅ 主机组列表获取成功:', groups.length, '个主机组');
      setAllGroups(groups);
      
      // 获取已经在清单中的主机组
      if (inventory) {
        console.log('🔍 获取清单中的主机组，清单ID:', inventory.id);
        const inventoryGroups = await apiService.getInventoryGroups(inventory.id);
        console.log('✅ 清单主机组获取成功:', inventoryGroups);
        
        // 修复数据映射 - 使用正确的字段名
        const existingGroupIds = inventoryGroups.map(ig => {
          // 根据后端返回的数据结构调整 - 使用 group_id 字段
          const groupId = ig.group_id || ig.group;
          return groupId ? groupId.toString() : null;
        }).filter((id): id is string => id !== null);
        
        console.log('📊 已存在的主机组IDs:', existingGroupIds);
        setGroupTargetKeys(existingGroupIds);
      }
    } catch (error: any) {
      console.error('❌ 获取主机组列表失败:', error);
      console.error('错误详情:', {
        message: error.message,
        status: error.response?.status,
        data: error.response?.data
      });
      message.error('获取主机组列表失败');
    }
  };

  useEffect(() => {
    if (visible && inventory) {
      fetchHosts();
      fetchGroups();
    }
  }, [visible, inventory]);

  // 生成Transfer组件的数据源
  const hostDataSource: TransferItem[] = allHosts.map(host => ({
    key: host.id.toString(),
    title: host.hostname,
    description: `${host.ip_address}:${host.port} (${host.username})`,
    type: 'host'
  }));

  const groupDataSource: TransferItem[] = allGroups.map(group => ({
    key: group.id.toString(),
    title: group.name,
    description: group.description || '无描述',
    type: 'group'
  }));

  // 处理主机选择变化
  const handleHostChange = (targetKeys: React.Key[], direction: string, moveKeys: React.Key[]) => {
    setHostTargetKeys(targetKeys);
  };

  const handleHostSelectChange = (sourceSelectedKeys: React.Key[], targetSelectedKeys: React.Key[]) => {
    setSelectedHostKeys([...sourceSelectedKeys, ...targetSelectedKeys]);
  };

  // 处理主机组选择变化
  const handleGroupChange = (targetKeys: React.Key[], direction: string, moveKeys: React.Key[]) => {
    setGroupTargetKeys(targetKeys);
  };

  const handleGroupSelectChange = (sourceSelectedKeys: React.Key[], targetSelectedKeys: React.Key[]) => {
    setSelectedGroupKeys([...sourceSelectedKeys, ...targetSelectedKeys]);
  };

  // 预览生成的清单
  const handlePreview = async () => {
    if (!inventory) return;

    setPreviewLoading(true);
    try {
      const result = await apiService.generateInventory(inventory.id);
      setGeneratedInventory(result);
    } catch (error) {
      message.error('生成清单预览失败');
    } finally {
      setPreviewLoading(false);
    }
  };

  // 保存配置
  const handleSave = async () => {
    if (!inventory) return;

    setLoading(true);
    try {
      // 获取当前选中的主机和组
      const selectedHostIds = hostTargetKeys.map(key => typeof key === 'string' ? parseInt(key) : key as number);
      const selectedGroupIds = groupTargetKeys.map(key => typeof key === 'string' ? parseInt(key) : key as number);

      // 获取已存在的主机和组
      const [currentHosts, currentGroups] = await Promise.all([
        apiService.getInventoryHosts(inventory.id),
        apiService.getInventoryGroups(inventory.id)
      ]);

      const currentHostIds = currentHosts.map(h => h.host.id);
      const currentGroupIds = currentGroups.map(g => g.group);

      // 计算需要添加和移除的主机
      const hostsToAdd = selectedHostIds.filter(id => !currentHostIds.includes(id));
      const hostsToRemove = currentHostIds.filter(id => !selectedHostIds.includes(id));

      // 计算需要添加和移除的主机组
      const groupsToAdd = selectedGroupIds.filter(id => !currentGroupIds.includes(id));
      const groupsToRemove = currentGroupIds.filter(id => !selectedGroupIds.includes(id));

      // 执行操作
      const operations = [];

      if (hostsToAdd.length > 0) {
        operations.push(
          apiService.addHostsToInventory(inventory.id, {
            host_ids: hostsToAdd,
            inventory_names: hostsToAdd.map(id => {
              const host = allHosts.find(h => h.id === id);
              return host ? host.hostname : `host-${id}`;
            }),
            host_variables: hostsToAdd.map(() => ({})),
            is_active: true
          })
        );
      }

      if (hostsToRemove.length > 0) {
        operations.push(
          apiService.removeHostsFromInventory(inventory.id, hostsToRemove)
        );
      }

      if (groupsToAdd.length > 0) {
        operations.push(
          apiService.addGroupsToInventory(inventory.id, {
            group_ids: groupsToAdd
          })
        );
      }

      if (groupsToRemove.length > 0) {
        operations.push(
          apiService.removeGroupsFromInventory(inventory.id, {
            group_ids: groupsToRemove
          })
        );
      }

      await Promise.all(operations);

      message.success('清单配置保存成功');
      onSuccess();
      onClose();
    } catch (error) {
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  const renderTransfer = (
    dataSource: TransferItem[],
    targetKeys: React.Key[],
    selectedKeys: React.Key[],
    onChange: (targetKeys: React.Key[], direction: string, moveKeys: React.Key[]) => void,
    onSelectChange: (sourceSelectedKeys: React.Key[], targetSelectedKeys: React.Key[]) => void,
    type: 'host' | 'group'
  ) => (
    <Transfer
      dataSource={dataSource}
      titles={[
        type === 'host' ? '可用主机' : '可用主机组',
        type === 'host' ? '清单中的主机' : '清单中的主机组'
      ]}
      targetKeys={targetKeys}
      selectedKeys={selectedKeys}
      onChange={onChange}
      onSelectChange={onSelectChange}
      render={item => (
        <div>
          <div style={{ fontWeight: 'bold' }}>
            {type === 'host' ? <UserOutlined /> : <TeamOutlined />} {item.title}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {item.description}
          </div>
        </div>
      )}
      listStyle={{
        width: 300,
        height: 400,
      }}
      showSearch
    />
  );

  return (
    <Modal
      title="动态清单管理"
      open={visible}
      onCancel={onClose}
      width={900}
      footer={[
        <Button key="preview" icon={<EyeOutlined />} onClick={handlePreview} loading={previewLoading}>
          预览清单
        </Button>,
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button key="save" type="primary" icon={<SaveOutlined />} onClick={handleSave} loading={loading}>
          保存配置
        </Button>,
      ]}
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab={<span><UserOutlined />主机管理</span>} key="hosts">
          <div style={{ marginBottom: 16 }}>
            <Text type="secondary">
              选择要添加到清单 "{inventory?.name}" 中的主机。左侧显示所有可用主机，右侧显示已添加的主机。
            </Text>
          </div>
          {renderTransfer(
            hostDataSource,
            hostTargetKeys,
            selectedHostKeys,
            handleHostChange,
            handleHostSelectChange,
            'host'
          )}
          <div style={{ marginTop: 16 }}>
            <Tag color="blue">已选择 {hostTargetKeys.length} 个主机</Tag>
          </div>
        </TabPane>

        <TabPane tab={<span><TeamOutlined />主机组管理</span>} key="groups">
          <div style={{ marginBottom: 16 }}>
            <Text type="secondary">
              选择要添加到清单 "{inventory?.name}" 中的主机组。主机组中的主机会自动包含在清单中。
            </Text>
          </div>
          {renderTransfer(
            groupDataSource,
            groupTargetKeys,
            selectedGroupKeys,
            handleGroupChange,
            handleGroupSelectChange,
            'group'
          )}
          <div style={{ marginTop: 16 }}>
            <Tag color="purple">已选择 {groupTargetKeys.length} 个主机组</Tag>
          </div>
        </TabPane>

        <TabPane tab={<span><EyeOutlined />清单预览</span>} key="preview">
          <div style={{ marginBottom: 16 }}>
            <Space>
              <Button 
                type="primary" 
                icon={<EyeOutlined />} 
                onClick={handlePreview}
                loading={previewLoading}
              >
                刷新预览
              </Button>
              {generatedInventory && (
                <Tag color="green">{generatedInventory.summary}</Tag>
              )}
            </Space>
          </div>

          {generatedInventory && (
            <Card>
              <div style={{ marginBottom: 16 }}>
                <Space>
                  <Tag>格式: {generatedInventory.format_type.toUpperCase()}</Tag>
                  <Tag color="blue">{generatedInventory.hosts_count} 个主机</Tag>
                  <Tag color="purple">{generatedInventory.groups_count} 个主机组</Tag>
                </Space>
              </div>
              <Divider />
              <div style={{ backgroundColor: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                  {generatedInventory.content}
                </pre>
              </div>
            </Card>
          )}

          {!generatedInventory && (
            <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
              点击"刷新预览"按钮查看生成的清单内容
            </div>
          )}
        </TabPane>
      </Tabs>
    </Modal>
  );
};

export default InventoryDynamicGeneratorModal;
