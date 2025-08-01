/**
 * 清单动态管理API调试工具
 * 专门用于诊断动态管理页面的API调用问题
 */

import React, { useState } from 'react';
import { Card, Button, Typography, Space, Input, message, Alert } from 'antd';
import { BugOutlined } from '@ant-design/icons';
import { apiService } from '../../services/api';

const { Title, Text, Paragraph } = Typography;

export const InventoryDynamicDebugTool: React.FC = () => {
  const [inventoryId, setInventoryId] = useState<number>(1);
  const [testing, setTesting] = useState(false);
  const [results, setResults] = useState<any>(null);

  const testInventoryDynamicAPIs = async () => {
    setTesting(true);
    const testResults: any = {
      timestamp: new Date().toISOString(),
      inventoryId,
      tests: {}
    };

    try {
      console.log('🔍 开始测试清单动态管理相关API');

      // 1. 测试获取所有主机
      try {
        console.log('📡 测试获取所有主机...');
        const allHosts = await apiService.getAnsibleHosts();
        testResults.tests.allHosts = {
          success: true,
          count: allHosts.length,
          sample: allHosts.slice(0, 2),
          structure: allHosts.length > 0 ? Object.keys(allHosts[0]) : []
        };
        console.log('✅ 获取所有主机成功:', allHosts.length, '个');
      } catch (error: any) {
        testResults.tests.allHosts = {
          success: false,
          error: error.message,
          details: error.response?.data
        };
        console.error('❌ 获取所有主机失败:', error);
      }

      // 2. 测试获取所有主机组
      try {
        console.log('📡 测试获取所有主机组...');
        const allGroups = await apiService.getAnsibleHostGroups();
        testResults.tests.allGroups = {
          success: true,
          count: allGroups.length,
          sample: allGroups.slice(0, 2),
          structure: allGroups.length > 0 ? Object.keys(allGroups[0]) : []
        };
        console.log('✅ 获取所有主机组成功:', allGroups.length, '个');
      } catch (error: any) {
        testResults.tests.allGroups = {
          success: false,
          error: error.message,
          details: error.response?.data
        };
        console.error('❌ 获取所有主机组失败:', error);
      }

      // 3. 测试获取清单中的主机
      try {
        console.log('📡 测试获取清单中的主机...');
        const inventoryHosts = await apiService.getInventoryHosts(inventoryId);
        testResults.tests.inventoryHosts = {
          success: true,
          count: inventoryHosts.length,
          sample: inventoryHosts.slice(0, 2),
          structure: inventoryHosts.length > 0 ? Object.keys(inventoryHosts[0]) : [],
          dataAnalysis: {
            hasHostField: inventoryHosts.length > 0 ? 'host' in inventoryHosts[0] : false,
            hasHostIdField: inventoryHosts.length > 0 ? 'host_id' in inventoryHosts[0] : false,
            hostStructure: inventoryHosts.length > 0 && inventoryHosts[0].host ? Object.keys(inventoryHosts[0].host) : []
          }
        };
        console.log('✅ 获取清单主机成功:', inventoryHosts.length, '个');
      } catch (error: any) {
        testResults.tests.inventoryHosts = {
          success: false,
          error: error.message,
          details: error.response?.data
        };
        console.error('❌ 获取清单主机失败:', error);
      }

      // 4. 测试获取清单中的主机组
      try {
        console.log('📡 测试获取清单中的主机组...');
        const inventoryGroups = await apiService.getInventoryGroups(inventoryId);
        testResults.tests.inventoryGroups = {
          success: true,
          count: inventoryGroups.length,
          sample: inventoryGroups.slice(0, 2),
          structure: inventoryGroups.length > 0 ? Object.keys(inventoryGroups[0]) : [],
          dataAnalysis: {
            hasGroupField: inventoryGroups.length > 0 ? 'group' in inventoryGroups[0] : false,
            hasGroupIdField: inventoryGroups.length > 0 ? 'group_id' in inventoryGroups[0] : false,
            hasGroupNameField: inventoryGroups.length > 0 ? 'group_name' in inventoryGroups[0] : false
          }
        };
        console.log('✅ 获取清单主机组成功:', inventoryGroups.length, '个');
      } catch (error: any) {
        testResults.tests.inventoryGroups = {
          success: false,
          error: error.message,
          details: error.response?.data
        };
        console.error('❌ 获取清单主机组失败:', error);
      }

      // 5. 数据映射测试
      if (testResults.tests.inventoryHosts?.success && testResults.tests.inventoryGroups?.success) {
        testResults.mappingTest = {
          hostMapping: '测试主机ID映射逻辑',
          groupMapping: '测试主机组ID映射逻辑',
          recommendations: []
        };

        // 主机映射建议
        const hostData = testResults.tests.inventoryHosts.sample[0];
        if (hostData) {
          if (hostData.host?.id) {
            testResults.mappingTest.recommendations.push('主机: 使用 ih.host.id 进行映射 ✅');
          } else if (hostData.host_id) {
            testResults.mappingTest.recommendations.push('主机: 使用 ih.host_id 进行映射 ✅');
          } else {
            testResults.mappingTest.recommendations.push('主机: 未找到合适的ID字段 ❌');
          }
        }

        // 主机组映射建议
        const groupData = testResults.tests.inventoryGroups.sample[0];
        if (groupData) {
          if (groupData.group_id) {
            testResults.mappingTest.recommendations.push('主机组: 使用 ig.group_id 进行映射 ✅');
          } else if (groupData.group) {
            testResults.mappingTest.recommendations.push('主机组: 使用 ig.group 进行映射 ✅');
          } else {
            testResults.mappingTest.recommendations.push('主机组: 未找到合适的ID字段 ❌');
          }
        }
      }

    } catch (error: any) {
      testResults.globalError = {
        message: error.message,
        stack: error.stack
      };
    }

    setResults(testResults);
    setTesting(false);

    // 总结测试结果
    const successCount = Object.values(testResults.tests).filter((test: any) => test.success).length;
    const totalTests = Object.keys(testResults.tests).length;
    
    if (successCount === totalTests) {
      message.success(`所有 ${totalTests} 个API测试通过！`);
    } else {
      message.warning(`${successCount}/${totalTests} 个API测试通过`);
    }
  };

  const renderTestResult = (testName: string, test: any) => {
    if (!test) return null;

    return (
      <Card key={testName} size="small" style={{ marginBottom: '8px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text strong>
            {testName}: {test.success ? '✅ 成功' : '❌ 失败'}
          </Text>
          
          {test.success ? (
            <div>
              <Text type="secondary">数量: {test.count}</Text>
              {test.structure && (
                <div>
                  <Text type="secondary">字段: {test.structure.join(', ')}</Text>
                </div>
              )}
              {test.dataAnalysis && (
                <div>
                  <Text strong>数据分析:</Text>
                  <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
                    {Object.entries(test.dataAnalysis).map(([key, value]) => (
                      <li key={key}>
                        <Text type="secondary">
                          {key}: {typeof value === 'boolean' ? (value ? '是' : '否') : JSON.stringify(value)}
                        </Text>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {test.sample && test.sample.length > 0 && (
                <div>
                  <Text strong>数据样例:</Text>
                  <pre style={{ fontSize: '11px', margin: '4px 0', maxHeight: '120px', overflow: 'auto' }}>
                    {JSON.stringify(test.sample[0], null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div>
              <Text type="danger">错误: {test.error}</Text>
              {test.details && (
                <pre style={{ fontSize: '11px', margin: '4px 0' }}>
                  {JSON.stringify(test.details, null, 2)}
                </pre>
              )}
            </div>
          )}
        </Space>
      </Card>
    );
  };

  return (
    <Card title={<Space><BugOutlined />清单动态管理API调试</Space>} size="small">
      <Space direction="vertical" style={{ width: '100%' }}>
        <Alert
          message="调试说明"
          description="此工具专门测试清单动态管理页面涉及的4个API调用，并分析数据结构映射问题"
          type="info"
          showIcon
        />

        <Space>
          <Text>清单ID:</Text>
          <Input 
            type="number" 
            value={inventoryId} 
            onChange={(e) => setInventoryId(Number(e.target.value))}
            style={{ width: '100px' }}
          />
          <Button
            type="primary"
            onClick={testInventoryDynamicAPIs}
            loading={testing}
          >
            开始测试
          </Button>
        </Space>

        {results && (
          <Card size="small" title="测试结果">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text type="secondary">测试时间: {results.timestamp}</Text>
              
              {Object.entries(results.tests).map(([testName, test]) => 
                renderTestResult(testName, test)
              )}

              {results.mappingTest && (
                <Card size="small" title="数据映射分析">
                  <Space direction="vertical">
                    {results.mappingTest.recommendations.map((rec: string, index: number) => (
                      <Text key={index} type={rec.includes('✅') ? 'success' : 'danger'}>
                        {rec}
                      </Text>
                    ))}
                  </Space>
                </Card>
              )}

              {results.globalError && (
                <Alert
                  message="全局错误"
                  description={results.globalError.message}
                  type="error"
                  showIcon
                />
              )}
            </Space>
          </Card>
        )}
      </Space>
    </Card>
  );
};
