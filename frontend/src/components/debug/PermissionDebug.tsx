import React from 'react';
import { Card, Typography, Tag, Space, Alert } from 'antd';
import { usePermissions } from '../../hooks/usePermissions';
import { useAuthStore } from '../../stores/auth';

const { Title, Text, Paragraph } = Typography;

export const PermissionDebug: React.FC = () => {
  const { user, isAuthenticated } = useAuthStore();
  const { 
    userInfo, 
    loading, 
    hasPermission, 
    canViewAPIEndpoints,
    canEditAPIEndpoints,
    canDeleteAPIEndpoints,
    canTestAPIEndpoints,
    canDiscoverAPIEndpoints,
    isAdmin,
    isSuperAdmin 
  } = usePermissions();

  if (loading) {
    return <Alert message="权限加载中..." type="info" />;
  }

  return (
    <Card title="权限调试信息" style={{ margin: '16px 0' }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <div>
          <Title level={5}>认证状态</Title>
          <Text>是否已认证: <Tag color={isAuthenticated ? 'green' : 'red'}>{isAuthenticated ? '是' : '否'}</Tag></Text>
        </div>

        <div>
          <Title level={5}>原始用户信息</Title>
          <Paragraph>
            <pre>{JSON.stringify(user, null, 2)}</pre>
          </Paragraph>
        </div>

        <div>
          <Title level={5}>权限用户信息</Title>
          <Paragraph>
            <pre>{JSON.stringify(userInfo, null, 2)}</pre>
          </Paragraph>
        </div>

        <div>
          <Title level={5}>管理员状态</Title>
          <Space>
            <Text>是否管理员: <Tag color={isAdmin() ? 'green' : 'red'}>{isAdmin() ? '是' : '否'}</Tag></Text>
            <Text>是否超级管理员: <Tag color={isSuperAdmin() ? 'green' : 'red'}>{isSuperAdmin() ? '是' : '否'}</Tag></Text>
          </Space>
        </div>

        <div>
          <Title level={5}>API端点权限</Title>
          <Space wrap>
            <Text>查看: <Tag color={canViewAPIEndpoints() ? 'green' : 'red'}>{canViewAPIEndpoints() ? '✓' : '✗'}</Tag></Text>
            <Text>编辑: <Tag color={canEditAPIEndpoints() ? 'green' : 'red'}>{canEditAPIEndpoints() ? '✓' : '✗'}</Tag></Text>
            <Text>删除: <Tag color={canDeleteAPIEndpoints() ? 'green' : 'red'}>{canDeleteAPIEndpoints() ? '✓' : '✗'}</Tag></Text>
            <Text>测试: <Tag color={canTestAPIEndpoints() ? 'green' : 'red'}>{canTestAPIEndpoints() ? '✓' : '✗'}</Tag></Text>
            <Text>发现: <Tag color={canDiscoverAPIEndpoints() ? 'green' : 'red'}>{canDiscoverAPIEndpoints() ? '✓' : '✗'}</Tag></Text>
          </Space>
        </div>
      </Space>
    </Card>
  );
};
