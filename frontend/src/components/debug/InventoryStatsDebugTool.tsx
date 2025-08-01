/**
 * 主机组移除后统计数据同步测试工具
 * 用于诊断和修复主机组移除后统计数据不更新的问题
 */

import React, { useState } from 'react';
import { Card, Button, Typography, Alert, Space, Descriptions, Table } from 'antd';
import { BugOutlined, ReloadOutlined, SyncOutlined } from '@ant-design/icons';
import { apiService } from '../../services/api';

const { Title, Text } = Typography;

interface InventoryStatistics {
  id: number;
  name: string;
  groups_count: number;
  active_groups_count: number;
  hosts_count: number;
  active_hosts_count: number;
}

interface TestResult {
  timestamp: string;
  inventoryId: number;
  beforeRemoval: InventoryStatistics;
  afterRemoval: InventoryStatistics;
  actualGroups: any[];
  isConsistent: boolean;
  issues: string[];
}

export const InventoryStatsDebugTool: React.FC = () => {
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [testing, setTesting] = useState(false);
  const [selectedInventoryId, setSelectedInventoryId] = useState<number>(1);

  // 获取清单统计数据
  const getInventoryStats = async (inventoryId: number): Promise<InventoryStatistics> => {
    const inventory = await apiService.getAnsibleInventory(inventoryId);
    return {
      id: inventory.id,
      name: inventory.name,
      groups_count: inventory.groups_count || 0,
      active_groups_count: inventory.active_groups_count || 0,
      hosts_count: inventory.hosts_count || 0,
      active_hosts_count: inventory.active_hosts_count || 0
    };
  };

  // 获取实际的主机组数据
  const getActualGroups = async (inventoryId: number): Promise<any[]> => {
    try {
      const groups = await apiService.getInventoryGroups(inventoryId);
      return Array.isArray(groups) ? groups : [];
    } catch (error) {
      console.error('获取实际主机组数据失败:', error);
      return [];
    }
  };

  // 验证数据一致性
  const validateConsistency = (stats: InventoryStatistics, actualGroups: any[]): { isConsistent: boolean; issues: string[] } => {
    const issues: string[] = [];
    let isConsistent = true;

    const actualGroupsCount = actualGroups.length;
    const activeGroupsCount = actualGroups.filter(g => g.is_active).length;

    if (stats.groups_count !== actualGroupsCount) {
      issues.push(`主机组总数不匹配: 统计数据显示 ${stats.groups_count}，实际为 ${actualGroupsCount}`);
      isConsistent = false;
    }

    if (stats.active_groups_count !== activeGroupsCount) {
      issues.push(`激活主机组数不匹配: 统计数据显示 ${stats.active_groups_count}，实际为 ${activeGroupsCount}`);
      isConsistent = false;
    }

    return { isConsistent, issues };
  };

  // 测试主机组移除后的统计数据同步
  const testGroupRemovalSync = async () => {
    setTesting(true);
    
    try {
      // 1. 获取移除前的统计数据
      const beforeStats = await getInventoryStats(selectedInventoryId);
      const beforeGroups = await getActualGroups(selectedInventoryId);
      
      console.log('移除前统计:', beforeStats);
      console.log('移除前实际主机组:', beforeGroups);
      
      // 验证移除前的数据一致性
      const beforeValidation = validateConsistency(beforeStats, beforeGroups);
      
      if (!beforeValidation.isConsistent) {
        console.warn('移除前数据就存在不一致:', beforeValidation.issues);
      }
      
      // 2. 如果有主机组，移除第一个
      if (beforeGroups.length > 0) {
        const groupToRemove = beforeGroups[0];
        console.log('准备移除主机组:', groupToRemove);
        
        try {
          await apiService.removeGroupsFromInventory(selectedInventoryId, {
            group_ids: [groupToRemove.group]
          });
          console.log('主机组移除成功');
          
          // 等待一段时间确保数据同步
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          // 3. 获取移除后的统计数据
          const afterStats = await getInventoryStats(selectedInventoryId);
          const afterGroups = await getActualGroups(selectedInventoryId);
          
          console.log('移除后统计:', afterStats);
          console.log('移除后实际主机组:', afterGroups);
          
          // 4. 验证移除后的数据一致性
          const afterValidation = validateConsistency(afterStats, afterGroups);
          
          // 5. 生成测试结果
          const testResult: TestResult = {
            timestamp: new Date().toISOString(),
            inventoryId: selectedInventoryId,
            beforeRemoval: beforeStats,
            afterRemoval: afterStats,
            actualGroups: afterGroups,
            isConsistent: afterValidation.isConsistent,
            issues: afterValidation.issues
          };
          
          setTestResults(prev => [testResult, ...prev]);
          
          if (afterValidation.isConsistent) {
            console.log('✅ 数据同步正常');
          } else {
            console.error('❌ 数据同步异常:', afterValidation.issues);
          }
          
        } catch (removeError) {
          console.error('主机组移除失败:', removeError);
        }
        
      } else {
        console.log('该清单没有主机组可移除');
      }
      
    } catch (error) {
      console.error('测试过程中发生错误:', error);
    } finally {
      setTesting(false);
    }
  };

  // 强制刷新清单数据
  const forceRefreshInventory = async () => {
    try {
      setTesting(true);
      
      // 重新获取清单数据
      const inventory = await apiService.getAnsibleInventory(selectedInventoryId);
      
      console.log('强制刷新后的清单数据:', inventory);
      
      const actualGroups = await getActualGroups(selectedInventoryId);
      const inventoryStats: InventoryStatistics = {
        id: inventory.id,
        name: inventory.name,
        groups_count: inventory.groups_count || 0,
        active_groups_count: inventory.active_groups_count || 0,
        hosts_count: inventory.hosts_count || 0,
        active_hosts_count: inventory.active_hosts_count || 0
      };
      
      const validation = validateConsistency(inventoryStats, actualGroups);
      
      if (validation.isConsistent) {
        console.log('✅ 强制刷新后数据一致');
      } else {
        console.error('❌ 强制刷新后数据仍不一致:', validation.issues);
      }
      
    } catch (error) {
      console.error('强制刷新失败:', error);
    } finally {
      setTesting(false);
    }
  };

  const columns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '清单ID',
      dataIndex: 'inventoryId',
      key: 'inventoryId',
    },
    {
      title: '移除前统计',
      key: 'before',
      render: (record: TestResult) => (
        <Space direction="vertical" size="small">
          <Text>主机组: {record.beforeRemoval.groups_count}</Text>
          <Text>激活组: {record.beforeRemoval.active_groups_count}</Text>
        </Space>
      ),
    },
    {
      title: '移除后统计',
      key: 'after',
      render: (record: TestResult) => (
        <Space direction="vertical" size="small">
          <Text>主机组: {record.afterRemoval.groups_count}</Text>
          <Text>激活组: {record.afterRemoval.active_groups_count}</Text>
        </Space>
      ),
    },
    {
      title: '实际数量',
      key: 'actual',
      render: (record: TestResult) => (
        <Space direction="vertical" size="small">
          <Text>实际组: {record.actualGroups.length}</Text>
          <Text>激活组: {record.actualGroups.filter(g => g.is_active).length}</Text>
        </Space>
      ),
    },
    {
      title: '一致性',
      key: 'consistency',
      render: (record: TestResult) => (
        <Space direction="vertical" size="small">
          <Text type={record.isConsistent ? 'success' : 'danger'}>
            {record.isConsistent ? '✅ 一致' : '❌ 不一致'}
          </Text>
          {record.issues.length > 0 && (
            <Text type="warning" style={{ fontSize: '12px' }}>
              {record.issues.join('; ')}
            </Text>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Card 
      title={
        <Space>
          <BugOutlined />
          <Title level={4} style={{ margin: 0 }}>主机组统计数据同步调试工具</Title>
        </Space>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        <Alert
          message="此工具用于诊断主机组移除后统计数据不更新的问题"
          description="它会测试移除主机组前后的统计数据，并验证数据一致性"
          type="info"
          showIcon
        />

        <Card size="small" title="测试控制">
          <Space wrap>
            <Text>测试清单ID:</Text>
            <input 
              type="number" 
              value={selectedInventoryId} 
              onChange={(e) => setSelectedInventoryId(Number(e.target.value))}
              style={{ width: '100px', padding: '4px' }}
            />
            <Button
              type="primary"
              icon={<BugOutlined />}
              onClick={testGroupRemovalSync}
              loading={testing}
            >
              测试主机组移除同步
            </Button>
            <Button
              icon={<SyncOutlined />}
              onClick={forceRefreshInventory}
              loading={testing}
            >
              强制刷新清单数据
            </Button>
          </Space>
        </Card>

        {testResults.length > 0 && (
          <Card size="small" title="测试结果">
            <Table
              dataSource={testResults}
              columns={columns}
              size="small"
              pagination={false}
              rowKey="timestamp"
            />
          </Card>
        )}
      </Space>
    </Card>
  );
};
