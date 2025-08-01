/**
 * 清单主机组API调试工具
 * 用于诊断"获取清单主机组失败"的问题
 */

import React, { useState } from 'react';
import { Card, Button, Typography, Alert, Space, Table, Input } from 'antd';
import { BugOutlined, ReloadOutlined } from '@ant-design/icons';
import { apiService } from '../../services/api';
import { useAuthStore } from '../../stores/auth';

const { Title, Text } = Typography;

export const InventoryGroupsDebugTool: React.FC = () => {
  const [testResults, setTestResults] = useState<any>(null);
  const [testing, setTesting] = useState(false);
  const [inventoryId, setInventoryId] = useState<number>(1);
  const { isAuthenticated, user } = useAuthStore();

  // 测试获取清单主机组
  const testGetInventoryGroups = async () => {
    setTesting(true);
    const result: any = {
      timestamp: new Date().toISOString(),
      inventoryId,
      authStatus: {
        isAuthenticated,
        user: user ? { id: user.id, username: user.username } : null,
        token: localStorage.getItem('authToken') ? '已存在' : '缺失'
      }
    };

    try {
      console.log('🔍 开始测试清单主机组API');
      console.log('清单ID:', inventoryId);
      console.log('认证状态:', result.authStatus);

      // 1. 直接调用API
      const groups = await apiService.getInventoryGroups(inventoryId);
      console.log('✅ API调用成功:', groups);
      
      result.success = true;
      result.groups = groups;
      result.groupsCount = Array.isArray(groups) ? groups.length : 0;
      
      // 2. 分析数据结构
      if (Array.isArray(groups) && groups.length > 0) {
        const firstGroup = groups[0];
        result.dataStructure = {
          hasGroupId: 'group_id' in firstGroup,
          hasGroup: 'group' in firstGroup,
          hasGroupName: 'group_name' in firstGroup,
          hasIsActive: 'is_active' in firstGroup,
          sampleFields: Object.keys(firstGroup)
        };
        
        result.activeGroups = groups.filter(g => g.is_active);
        result.inactiveGroups = groups.filter(g => !g.is_active);
        
        console.log('📊 数据分析:', result.dataStructure);
      }

    } catch (error: any) {
      console.error('❌ API调用失败:', error);
      
      result.success = false;
      result.error = {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        url: error.config?.url,
        method: error.config?.method,
        headers: error.config?.headers
      };
      
      // 详细错误分析
      if (error.response?.status === 401) {
        result.errorAnalysis = '认证失败 - Token可能已过期或无效';
      } else if (error.response?.status === 403) {
        result.errorAnalysis = '权限不足 - 用户没有访问权限';
      } else if (error.response?.status === 404) {
        result.errorAnalysis = '资源不存在 - 清单ID可能无效或API端点不存在';
      } else if (error.response?.status === 500) {
        result.errorAnalysis = '服务器错误 - 后端处理异常';
      } else if (error.code === 'NETWORK_ERROR') {
        result.errorAnalysis = '网络错误 - 无法连接到服务器';
      } else {
        result.errorAnalysis = '未知错误';
      }
    }

    setTestResults(result);
    setTesting(false);
  };

  // 测试认证状态
  const testAuthentication = async () => {
    try {
      setTesting(true);
      const user = await apiService.getCurrentUser();
      console.log('✅ 认证测试成功:', user);
      setTestResults({
        ...testResults,
        authTest: {
          success: true,
          user
        }
      });
    } catch (error: any) {
      console.error('❌ 认证测试失败:', error);
      setTestResults({
        ...testResults,
        authTest: {
          success: false,
          error: error.message
        }
      });
    } finally {
      setTesting(false);
    }
  };

  // 测试清单列表API
  const testInventoriesAPI = async () => {
    try {
      setTesting(true);
      const inventories = await apiService.getAnsibleInventories();
      console.log('✅ 清单列表API成功:', inventories);
      setTestResults({
        ...testResults,
        inventoriesTest: {
          success: true,
          count: inventories.length,
          inventories: inventories.slice(0, 3) // 只显示前3个
        }
      });
    } catch (error: any) {
      console.error('❌ 清单列表API失败:', error);
      setTestResults({
        ...testResults,
        inventoriesTest: {
          success: false,
          error: error.message
        }
      });
    } finally {
      setTesting(false);
    }
  };

  const columns = [
    {
      title: '字段',
      dataIndex: 'field',
      key: 'field',
    },
    {
      title: '值',
      dataIndex: 'value',
      key: 'value',
      render: (value: any) => {
        if (typeof value === 'object') {
          return <pre>{JSON.stringify(value, null, 2)}</pre>;
        }
        return String(value);
      }
    }
  ];

  return (
    <Card 
      title={
        <Space>
          <BugOutlined />
          <Title level={4} style={{ margin: 0 }}>清单主机组API调试工具</Title>
        </Space>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        <Alert
          message="此工具用于诊断'获取清单主机组失败'的错误"
          description="它会测试API调用、认证状态和数据结构"
          type="info"
          showIcon
        />

        <Card size="small" title="测试控制">
          <Space wrap>
            <Text>清单ID:</Text>
            <Input 
              type="number" 
              value={inventoryId} 
              onChange={(e) => setInventoryId(Number(e.target.value))}
              style={{ width: '100px' }}
            />
            <Button
              type="primary"
              icon={<BugOutlined />}
              onClick={testGetInventoryGroups}
              loading={testing}
            >
              测试主机组API
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={testAuthentication}
              loading={testing}
            >
              测试认证
            </Button>
            <Button
              onClick={testInventoriesAPI}
              loading={testing}
            >
              测试清单列表
            </Button>
          </Space>
        </Card>

        {testResults && (
          <Card size="small" title="测试结果">
            <Space direction="vertical" style={{ width: '100%' }}>
              {/* 基本信息 */}
              <Alert
                message={`API调用${testResults.success ? '成功' : '失败'}`}
                type={testResults.success ? 'success' : 'error'}
                description={
                  <Space direction="vertical">
                    <Text>测试时间: {testResults.timestamp}</Text>
                    <Text>清单ID: {testResults.inventoryId}</Text>
                    <Text>认证状态: {testResults.authStatus.isAuthenticated ? '已认证' : '未认证'}</Text>
                    {testResults.authStatus.user && (
                      <Text>用户: {testResults.authStatus.user.username} (ID: {testResults.authStatus.user.id})</Text>
                    )}
                    <Text>Token: {testResults.authStatus.token}</Text>
                  </Space>
                }
              />

              {/* 成功结果 */}
              {testResults.success && (
                <Card size="small" title="API响应数据">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text strong>主机组数量: {testResults.groupsCount}</Text>
                    <Text>激活主机组: {testResults.activeGroups?.length || 0}</Text>
                    <Text>非激活主机组: {testResults.inactiveGroups?.length || 0}</Text>
                    
                    {testResults.dataStructure && (
                      <div>
                        <Text strong>数据结构分析:</Text>
                        <Table
                          size="small"
                          pagination={false}
                          dataSource={[
                            { field: '包含group_id字段', value: testResults.dataStructure.hasGroupId ? '是' : '否' },
                            { field: '包含group字段', value: testResults.dataStructure.hasGroup ? '是' : '否' },
                            { field: '包含group_name字段', value: testResults.dataStructure.hasGroupName ? '是' : '否' },
                            { field: '包含is_active字段', value: testResults.dataStructure.hasIsActive ? '是' : '否' },
                            { field: '所有字段', value: testResults.dataStructure.sampleFields.join(', ') }
                          ]}
                          columns={columns.slice(0, 2)}
                        />
                      </div>
                    )}

                    {testResults.groups && testResults.groups.length > 0 && (
                      <div>
                        <Text strong>主机组数据样例:</Text>
                        <pre style={{ fontSize: '12px', maxHeight: '200px', overflow: 'auto' }}>
                          {JSON.stringify(testResults.groups.slice(0, 2), null, 2)}
                        </pre>
                      </div>
                    )}
                  </Space>
                </Card>
              )}

              {/* 错误结果 */}
              {!testResults.success && (
                <Card size="small" title="错误详情">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Alert
                      message={testResults.errorAnalysis}
                      type="error"
                    />
                    
                    <Table
                      size="small"
                      pagination={false}
                      dataSource={[
                        { field: '错误消息', value: testResults.error.message },
                        { field: 'HTTP状态码', value: testResults.error.status },
                        { field: '状态文本', value: testResults.error.statusText },
                        { field: 'API路径', value: testResults.error.url },
                        { field: 'HTTP方法', value: testResults.error.method },
                        { field: '响应数据', value: testResults.error.data }
                      ].filter(item => item.value)}
                      columns={columns}
                    />
                  </Space>
                </Card>
              )}

              {/* 认证测试结果 */}
              {testResults.authTest && (
                <Card size="small" title="认证测试">
                  <Alert
                    message={`认证测试${testResults.authTest.success ? '成功' : '失败'}`}
                    type={testResults.authTest.success ? 'success' : 'error'}
                    description={
                      testResults.authTest.success 
                        ? `用户: ${testResults.authTest.user.username}`
                        : testResults.authTest.error
                    }
                  />
                </Card>
              )}

              {/* 清单列表测试结果 */}
              {testResults.inventoriesTest && (
                <Card size="small" title="清单列表测试">
                  <Alert
                    message={`清单列表API${testResults.inventoriesTest.success ? '成功' : '失败'}`}
                    type={testResults.inventoriesTest.success ? 'success' : 'error'}
                    description={
                      testResults.inventoriesTest.success 
                        ? `找到 ${testResults.inventoriesTest.count} 个清单`
                        : testResults.inventoriesTest.error
                    }
                  />
                  {testResults.inventoriesTest.success && testResults.inventoriesTest.inventories.length > 0 && (
                    <pre style={{ fontSize: '12px', maxHeight: '150px', overflow: 'auto' }}>
                      {JSON.stringify(testResults.inventoriesTest.inventories, null, 2)}
                    </pre>
                  )}
                </Card>
              )}
            </Space>
          </Card>
        )}
      </Space>
    </Card>
  );
};
