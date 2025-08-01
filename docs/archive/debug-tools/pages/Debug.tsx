import React from 'react';
import { Card, Typography, Space, Alert, Tabs } from 'antd';
import { BugOutlined } from '@ant-design/icons';
import { InventoryGroupsDebugTool } from '../components/debug/InventoryGroupsDebugTool';
import { SimpleDebugTool } from '../components/debug/SimpleDebugTool';
import { InventoryDynamicDebugTool } from '../components/debug/InventoryDynamicDebugTool';
import InventoryGroupTest from './InventoryGroupTest';

const { Title } = Typography;
const { TabPane } = Tabs;

const DebugPage: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Card>
          <Title level={2}>
            <BugOutlined /> 调试工具页面
          </Title>
          <Alert
            message="调试工具集合"
            description="此页面包含各种调试工具，帮助诊断系统问题"
            type="info"
            showIcon
            style={{ marginBottom: '24px' }}
          />
        </Card>

        <Tabs defaultActiveKey="1" type="card">
          <TabPane tab="简化API调试" key="1">
            <SimpleDebugTool />
          </TabPane>
          <TabPane tab="清单动态管理调试" key="2">
            <InventoryDynamicDebugTool />
          </TabPane>
          <TabPane tab="详细API调试" key="3">
            <InventoryGroupsDebugTool />
          </TabPane>
          <TabPane tab="模态框测试" key="4">
            <InventoryGroupTest />
          </TabPane>
        </Tabs>
      </Space>
    </div>
  );
};

export default DebugPage;
