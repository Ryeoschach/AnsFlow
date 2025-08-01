import React, { useState } from 'react';
import { Modal, Form, Input, Button, Select, message, Spin, Typography, Space, Alert } from 'antd';
import { EyeInvisibleOutlined, EyeTwoTone, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import apiService from '../services/api';
import { ConnectionTestRequest, ConnectionTestResult } from '../types/ansible';

const { Option } = Select;
const { TextArea } = Input;
const { Text, Paragraph } = Typography;

interface ConnectionTestModalProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess?: (data: ConnectionTestRequest) => void;
}

const ConnectionTestModal: React.FC<ConnectionTestModalProps> = ({ 
  visible, 
  onCancel, 
  onSuccess 
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null);
  const [authMethod, setAuthMethod] = useState<'password' | 'ssh_key'>('password');

  const handleTest = async (values: any) => {
    setLoading(true);
    setTestResult(null);
    
    try {
      const testData: ConnectionTestRequest = {
        ip_address: values.ip_address,
        username: values.username,
        port: values.port || 22,
        connection_type: values.connection_type || 'ssh',
        ...(authMethod === 'password' 
          ? { password: values.password }
          : { ssh_private_key: values.ssh_private_key }
        )
      };

      const result = await apiService.testConnection(testData);
      setTestResult(result);

      if (result.success) {
        message.success('连接测试成功！');
        if (onSuccess) {
          onSuccess(testData);
        }
      } else {
        message.error(`连接测试失败: ${result.message}`);
      }
    } catch (error) {
      message.error('连接测试失败');
      setTestResult({
        success: false,
        message: '网络错误或服务不可用'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    setTestResult(null);
    setAuthMethod('password');
    onCancel();
  };

  return (
    <Modal
      title="SSH连接测试"
      open={visible}
      onCancel={handleCancel}
      width={700}
      footer={[
        <Button key="cancel" onClick={handleCancel}>
          取消
        </Button>,
        <Button 
          key="test" 
          type="primary" 
          loading={loading}
          onClick={() => form.submit()}
        >
          测试连接
        </Button>
      ]}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleTest}
        initialValues={{
          port: 22,
          connection_type: 'ssh'
        }}
      >
        <Alert
          message="连接测试说明"
          description="此功能用于验证SSH连接配置是否正确，测试成功后可以直接创建主机记录。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Form.Item
          label="IP地址"
          name="ip_address"
          rules={[
            { required: true, message: '请输入IP地址' },
            { pattern: /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/, message: '请输入有效的IP地址' }
          ]}
        >
          <Input placeholder="例如: 192.168.1.100" />
        </Form.Item>

        <Space style={{ width: '100%' }} size="large">
          <Form.Item
            label="SSH端口"
            name="port"
            style={{ flex: 1 }}
          >
            <Input type="number" placeholder="默认: 22" />
          </Form.Item>

          <Form.Item
            label="连接类型"
            name="connection_type"
            style={{ flex: 1 }}
          >
            <Select>
              <Option value="ssh">SSH</Option>
              <Option value="local">本地</Option>
            </Select>
          </Form.Item>
        </Space>

        <Form.Item
          label="用户名"
          name="username"
          rules={[{ required: true, message: '请输入用户名' }]}
        >
          <Input placeholder="例如: root, ubuntu, centos" />
        </Form.Item>

        <Form.Item label="认证方式">
          <Select 
            value={authMethod} 
            onChange={(value) => setAuthMethod(value)}
            style={{ width: 200 }}
          >
            <Option value="password">密码认证</Option>
            <Option value="ssh_key">SSH密钥认证</Option>
          </Select>
        </Form.Item>

        {authMethod === 'password' ? (
          <Form.Item
            label="密码"
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              placeholder="请输入SSH密码"
              iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
            />
          </Form.Item>
        ) : (
          <Form.Item
            label="SSH私钥"
            name="ssh_private_key"
            rules={[{ required: true, message: '请输入SSH私钥' }]}
          >
            <TextArea
              rows={8}
              placeholder="请粘贴SSH私钥内容，例如:
-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...
-----END PRIVATE KEY-----"
            />
          </Form.Item>
        )}

        {loading && (
          <div style={{ textAlign: 'center', margin: '20px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">正在测试连接，请稍候...</Text>
            </div>
          </div>
        )}

        {testResult && (
          <Alert
            message={testResult.success ? "连接成功" : "连接失败"}
            description={
              <div>
                <Paragraph>{testResult.message}</Paragraph>
                {testResult.details && (
                  <div>
                    <Text code>返回代码: {testResult.details.return_code}</Text>
                    <br />
                    {testResult.details.stderr && (
                      <div style={{ marginTop: 8 }}>
                        <Text strong>错误输出:</Text>
                        <pre style={{ fontSize: '12px', background: '#f5f5f5', padding: '8px', marginTop: '4px' }}>
                          {testResult.details.stderr}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            }
            type={testResult.success ? "success" : "error"}
            icon={testResult.success ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
            style={{ marginTop: 16 }}
          />
        )}
      </Form>
    </Modal>
  );
};

export default ConnectionTestModal;
