import React, { useState } from 'react';
import { Card, Button, Space, Alert, Typography, Input } from 'antd';
import { BugOutlined } from '@ant-design/icons';
import InventoryGroupModal from '../components/InventoryGroupModal';

const { Title, Text } = Typography;

const InventoryGroupTest: React.FC = () => {
  const [modalVisible, setModalVisible] = useState(false);
  const [inventoryId, setInventoryId] = useState<number>(1);

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Card>
          <Title level={2}>
            <BugOutlined /> 清单主机组模态框测试
          </Title>
          <Alert
            message="测试InventoryGroupModal组件"
            description="此页面用于直接测试清单主机组模态框，帮助诊断'获取清单主机组失败'的问题"
            type="info"
            showIcon
            style={{ marginBottom: '24px' }}
          />

          <Space>
            <Text>清单ID:</Text>
            <Input 
              type="number" 
              value={inventoryId} 
              onChange={(e) => setInventoryId(Number(e.target.value))}
              style={{ width: '120px' }}
            />
            <Button
              type="primary"
              onClick={() => setModalVisible(true)}
            >
              打开清单主机组模态框
            </Button>
          </Space>

          <Alert
            style={{ marginTop: '16px' }}
            message="测试说明"
            description={
              <div>
                <p>1. 设置要测试的清单ID</p>
                <p>2. 点击"打开清单主机组模态框"按钮</p>
                <p>3. 检查浏览器控制台的详细日志</p>
                <p>4. 观察模态框是否正常加载主机组数据</p>
              </div>
            }
            type="warning"
          />
        </Card>

        <InventoryGroupModal
          visible={modalVisible}
          inventory={{ id: inventoryId, name: `测试清单${inventoryId}` } as any}
          onCancel={() => setModalVisible(false)}
          onRefresh={() => {
            console.log('✅ 清单刷新回调被调用');
          }}
        />
      </Space>
    </div>
  );
};

export default InventoryGroupTest;
