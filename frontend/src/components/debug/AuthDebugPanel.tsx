import React, { useState } from 'react';
import { Card, Button, Typography, Alert, Space, Descriptions, Tag, Collapse } from 'antd';
import { BugOutlined, ReloadOutlined, KeyOutlined } from '@ant-design/icons';
import { useAuthStore } from '../../stores/auth';
import { tokenManager } from '../../utils/tokenManager';
import { authenticatedApiService } from '../../services/authenticatedApiService';
import { ansibleApiService } from '../../services/ansibleApiService';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

export const AuthDebugPanel: React.FC = () => {
  const { user, isAuthenticated, getAuthDebugInfo, checkAuth } = useAuthStore();
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  // 测试认证状态
  const testAuthentication = async () => {
    setTesting(true);
    const result: any = {
      timestamp: new Date().toISOString(),
      tests: {}
    };

    try {
      // 1. Token管理器状态
      result.tests.tokenManager = tokenManager.getTokenInfo();

      // 2. API服务状态
      result.tests.apiService = authenticatedApiService.getAuthDebugInfo();

      // 3. Zustand状态
      result.tests.zustandAuth = getAuthDebugInfo();

      // 4. 验证API访问
      try {
        result.tests.apiAccess = await authenticatedApiService.validateAuth();
        if (result.tests.apiAccess) {
          result.tests.currentUser = await authenticatedApiService.getCurrentUser();
        }
      } catch (error: any) {
        result.tests.apiAccess = false;
        result.tests.apiError = error.message;
      }

      // 5. 测试Ansible API
      try {
        result.tests.ansibleApi = await ansibleApiService.getAvailableGroups();
        result.tests.ansibleApiSuccess = true;
      } catch (error: any) {
        result.tests.ansibleApiSuccess = false;
        result.tests.ansibleApiError = error.message;
      }

      setTestResult(result);
    } catch (error: any) {
      result.tests.error = error.message;
      setTestResult(result);
    } finally {
      setTesting(false);
    }
  };

  // 测试主机组移除
  const testGroupRemoval = async () => {
    try {
      setTesting(true);
      
      // 使用测试数据
      const testInventoryId = 1;
      const testGroupIds = [1];
      
      await ansibleApiService.testRemoveGroups(testInventoryId, testGroupIds);
      
      setTestResult({
        ...testResult,
        groupRemovalTest: {
          success: true,
          message: '主机组移除测试成功'
        }
      });
    } catch (error: any) {
      setTestResult({
        ...testResult,
        groupRemovalTest: {
          success: false,
          error: error.message
        }
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <Card 
      title={
        <Space>
          <BugOutlined />
          <Title level={4} style={{ margin: 0 }}>认证调试面板</Title>
        </Space>
      }
      extra={
        <Space>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={checkAuth}
            size="small"
          >
            刷新认证状态
          </Button>
          <Button 
            type="primary" 
            icon={<KeyOutlined />}
            onClick={testAuthentication}
            loading={testing}
            size="small"
          >
            运行认证测试
          </Button>
        </Space>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        {/* 基本认证状态 */}
        <Alert
          message="认证状态概览"
          description={
            <Descriptions size="small" column={2}>
              <Descriptions.Item label="登录状态">
                <Tag color={isAuthenticated ? 'green' : 'red'}>
                  {isAuthenticated ? '已登录' : '未登录'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="用户信息">
                {user ? `${user.username} (ID: ${user.id})` : '无'}
              </Descriptions.Item>
              <Descriptions.Item label="Token">
                <Tag color={tokenManager.getTokenInfo().hasAccessToken ? 'green' : 'red'}>
                  {tokenManager.getTokenInfo().hasAccessToken ? '存在' : '缺失'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Token过期">
                <Tag color={tokenManager.getTokenInfo().isExpired ? 'red' : 'green'}>
                  {tokenManager.getTokenInfo().isExpired ? '已过期' : '有效'}
                </Tag>
              </Descriptions.Item>
            </Descriptions>
          }
          type={isAuthenticated ? 'success' : 'error'}
        />

        {/* 测试结果 */}
        {testResult && (
          <Collapse>
            <Panel header="详细测试结果" key="1">
              <Space direction="vertical" style={{ width: '100%' }}>
                {/* Token管理器状态 */}
                <Card size="small" title="Token管理器状态">
                  <Paragraph>
                    <pre>{JSON.stringify(testResult.tests.tokenManager, null, 2)}</pre>
                  </Paragraph>
                </Card>

                {/* API服务状态 */}
                <Card size="small" title="API服务状态">
                  <Paragraph>
                    <pre>{JSON.stringify(testResult.tests.apiService, null, 2)}</pre>
                  </Paragraph>
                </Card>

                {/* Zustand状态 */}
                <Card size="small" title="Zustand认证状态">
                  <Paragraph>
                    <pre>{JSON.stringify(testResult.tests.zustandAuth, null, 2)}</pre>
                  </Paragraph>
                </Card>

                {/* API访问测试 */}
                <Card size="small" title="API访问测试">
                  <Space direction="vertical">
                    <Text>
                      访问状态: <Tag color={testResult.tests.apiAccess ? 'green' : 'red'}>
                        {testResult.tests.apiAccess ? '成功' : '失败'}
                      </Tag>
                    </Text>
                    {testResult.tests.apiError && (
                      <Alert message="API错误" description={testResult.tests.apiError} type="error" />
                    )}
                    {testResult.tests.currentUser && (
                      <Paragraph>
                        <Text strong>当前用户:</Text>
                        <pre>{JSON.stringify(testResult.tests.currentUser, null, 2)}</pre>
                      </Paragraph>
                    )}
                  </Space>
                </Card>

                {/* Ansible API测试 */}
                <Card size="small" title="Ansible API测试">
                  <Space direction="vertical">
                    <Text>
                      访问状态: <Tag color={testResult.tests.ansibleApiSuccess ? 'green' : 'red'}>
                        {testResult.tests.ansibleApiSuccess ? '成功' : '失败'}
                      </Tag>
                    </Text>
                    {testResult.tests.ansibleApiError && (
                      <Alert 
                        message="Ansible API错误" 
                        description={testResult.tests.ansibleApiError} 
                        type="error" 
                      />
                    )}
                  </Space>
                </Card>

                {/* 主机组移除测试 */}
                {testResult.groupRemovalTest && (
                  <Card size="small" title="主机组移除测试">
                    <Space direction="vertical">
                      <Text>
                        测试状态: <Tag color={testResult.groupRemovalTest.success ? 'green' : 'red'}>
                          {testResult.groupRemovalTest.success ? '成功' : '失败'}
                        </Tag>
                      </Text>
                      {testResult.groupRemovalTest.error && (
                        <Alert 
                          message="移除测试错误" 
                          description={testResult.groupRemovalTest.error} 
                          type="error" 
                        />
                      )}
                      {testResult.groupRemovalTest.message && (
                        <Alert 
                          message={testResult.groupRemovalTest.message} 
                          type="success" 
                        />
                      )}
                    </Space>
                  </Card>
                )}
              </Space>
            </Panel>
          </Collapse>
        )}

        {/* 快速操作 */}
        <Card size="small" title="快速操作">
          <Space wrap>
            <Button onClick={testGroupRemoval} loading={testing}>
              测试主机组移除
            </Button>
            <Button onClick={() => tokenManager.clearTokens()}>
              清理Token
            </Button>
            <Button onClick={() => console.log('Token信息:', tokenManager.getTokenInfo())}>
              输出Token信息到控制台
            </Button>
          </Space>
        </Card>
      </Space>
    </Card>
  );
};
