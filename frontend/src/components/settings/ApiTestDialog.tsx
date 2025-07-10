import React, { useState } from 'react';
import {
  Modal,
  Form,
  Input,
  Button,
  Typography,
  Divider,
  Space,
  Card,
  Row,
  Col,
  Tag,
  Alert,
  Spin,
  Tabs,
  message,
  Collapse,
} from 'antd';
import {
  PlayCircleOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CopyOutlined,
  KeyOutlined,
  LoginOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
} from '@ant-design/icons';
import { APIEndpoint } from '../../types';
import { apiService } from '../../services/api';

const { TextArea } = Input;
const { Text, Title } = Typography;
const { TabPane } = Tabs;
const { Panel } = Collapse;

interface ApiTestDialogProps {
  endpoint: APIEndpoint;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface TestResult {
  success: boolean;
  status_code: number;
  response_time_ms: number;
  response_data: any;
  headers: Record<string, string>;
  error?: string;
}

interface LoginCredentials {
  username: string;
  password: string;
}

export const APITestDialog: React.FC<ApiTestDialogProps> = ({
  endpoint,
  open,
  onOpenChange,
}) => {
  const [form] = Form.useForm();
  const [loginForm] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [loginLoading, setLoginLoading] = useState(false);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [activeTab, setActiveTab] = useState('params');
  const [currentToken, setCurrentToken] = useState<string>('');
  const [showPassword, setShowPassword] = useState(false);

  // 初始化表单默认值
  const initializeForm = () => {
    // 根据端点认证要求和用户token智能设置请求头
    const token = currentToken || localStorage.getItem('access_token') || 'your-token-here';
    
    const defaultHeaders: Record<string, string> = {
      "Content-Type": "application/json"
    };

    // 如果API需要认证，添加Authorization头
    if (endpoint.auth_required) {
      defaultHeaders["Authorization"] = `Bearer ${token}`;
    }

    // 添加常用的自定义头
    defaultHeaders["X-Requested-With"] = "XMLHttpRequest";
    defaultHeaders["Accept"] = "application/json";

    // 根据API方法设置默认参数
    const defaultParams = endpoint.method === 'GET' ? 
      "page=1\nsize=10" : "";

    // 根据API端点的请求体schema设置默认请求体
    let defaultBody = "";
    if (['POST', 'PUT', 'PATCH'].includes(endpoint.method)) {
      if (endpoint.request_body_schema?.example) {
        // 如果有示例，使用示例
        defaultBody = typeof endpoint.request_body_schema.example === 'string' 
          ? endpoint.request_body_schema.example 
          : JSON.stringify(endpoint.request_body_schema.example, null, 2);
      } else {
        // 否则使用通用示例
        defaultBody = JSON.stringify({
          "name": "示例名称",
          "description": "示例描述",
          "data": {
            "field1": "value1",
            "field2": 123,
            "field3": true
          }
        }, null, 2);
      }
    }

    form.setFieldsValue({
      headers: JSON.stringify(defaultHeaders, null, 2),
      params: defaultParams,
      body: defaultBody
    });
  };

  // 当对话框打开时初始化表单
  React.useEffect(() => {
    if (open) {
      const storedToken = localStorage.getItem('access_token');
      if (storedToken) {
        setCurrentToken(storedToken);
      }
      initializeForm();
    }
  }, [open, endpoint, currentToken]);

  // 获取认证token
  const handleLogin = async (values: LoginCredentials) => {
    setLoginLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/token/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(values),
      });

      if (response.ok) {
        const data = await response.json();
        const token = data.access;
        
        if (token) {
          setCurrentToken(token);
          localStorage.setItem('access_token', token);
          message.success('Token获取成功！已自动更新请求头');
          
          // 重新初始化表单以更新请求头
          initializeForm();
          
          // 清空登录表单
          loginForm.resetFields();
        } else {
          message.error('Token获取失败：响应中未找到access token');
        }
      } else {
        const errorData = await response.json();
        message.error(`登录失败: ${errorData.detail || '用户名或密码错误'}`);
      }
    } catch (error: any) {
      message.error(`请求失败: ${error.message}`);
    } finally {
      setLoginLoading(false);
    }
  };

  // 清除token
  const handleClearToken = () => {
    setCurrentToken('');
    localStorage.removeItem('access_token');
    message.info('Token已清除');
    initializeForm();
  };

  const handleTest = async (values: any) => {
    setLoading(true);
    setTestResult(null);

    try {
      // 解析请求参数
      let parsedParams: Record<string, string> = {};
      if (values.params) {
        // 支持 key=value 格式，每行一个
        const lines = values.params.split('\n').filter((line: string) => line.trim());
        for (const line of lines) {
          const [key, ...valueParts] = line.split('=');
          if (key && valueParts.length > 0) {
            parsedParams[key.trim()] = valueParts.join('=').trim();
          }
        }
      }

      // 解析JSON数据
      let parsedBody = null;
      if (values.body) {
        try {
          parsedBody = JSON.parse(values.body);
        } catch (error) {
          message.error('请求体JSON格式错误');
          setLoading(false);
          return;
        }
      }

      let parsedHeaders = {};
      if (values.headers) {
        try {
          parsedHeaders = JSON.parse(values.headers);
        } catch (error) {
          message.error('请求头JSON格式错误');
          setLoading(false);
          return;
        }
      }

      const testData = {
        params: parsedParams,
        body: parsedBody,
        headers: parsedHeaders,
      };

      // 调用真实的API测试接口
      const startTime = Date.now();
      
      const result = await apiService.testAPIEndpoint(endpoint.id, testData);
      
      const endTime = Date.now();
      
      // 如果后端没有返回响应时间，使用前端计算的时间
      const responseTime = result.response_time_ms || (endTime - startTime);
      
      const testResult: TestResult = {
        success: result.success,
        status_code: result.status_code || 0,
        response_time_ms: responseTime,
        response_data: result.response_data,
        headers: result.headers || {},
        error: result.error,
      };

      setTestResult(testResult);
      
      if (testResult.success) {
        message.success('API测试成功');
      } else {
        message.warning('API测试完成，但返回了错误状态');
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || error.message || '测试失败';
      setTestResult({
        success: false,
        status_code: error.response?.status || 0,
        response_time_ms: 0,
        response_data: error.response?.data || null,
        headers: {},
        error: errorMessage,
      });
      message.error(`API测试失败: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      message.success('已复制到剪贴板');
    });
  };

  const formatResponseTime = (ms: number) => {
    if (ms < 1000) {
      return `${ms}ms`;
    }
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getStatusColor = (code: number) => {
    if (code >= 200 && code < 300) return 'success';
    if (code >= 400 && code < 500) return 'warning';
    if (code >= 500) return 'error';
    return 'default';
  };

  return (
    <Modal
      title={
        <div>
          <PlayCircleOutlined style={{ marginRight: 8 }} />
          测试API端点: {endpoint.name}
        </div>
      }
      open={open}
      onCancel={() => onOpenChange(false)}
      width={900}
      footer={null}
      destroyOnClose
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Tag color="blue">{endpoint.method}</Tag>
          <Text code>{endpoint.path}</Text>
        </Space>
        {endpoint.description && (
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">{endpoint.description}</Text>
          </div>
        )}
      </div>

      <Form form={form} layout="vertical" onFinish={handleTest}>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="认证管理" key="auth">
            <Alert
              type="info"
              message="Token认证"
              description="如果API需要认证，请先获取有效的token。获取后会自动更新请求头中的Authorization字段。"
              style={{ marginBottom: 16 }}
            />
            
            <Row gutter={16}>
              <Col span={12}>
                <Card size="small" title="当前Token状态">
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>当前Token: </Text>
                    {currentToken ? (
                      <div>
                        <Text code style={{ 
                          display: 'block', 
                          marginTop: 4,
                          wordBreak: 'break-all',
                          backgroundColor: '#f0f0f0',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '12px'
                        }}>
                          {currentToken.length > 50 ? 
                            `${currentToken.substring(0, 20)}...${currentToken.substring(currentToken.length - 20)}` :
                            currentToken
                          }
                        </Text>
                        <div style={{ marginTop: 8 }}>
                          <Button 
                            size="small" 
                            onClick={() => {
                              navigator.clipboard.writeText(currentToken);
                              message.success('Token已复制到剪贴板');
                            }}
                            icon={<CopyOutlined />}
                          >
                            复制Token
                          </Button>
                          <Button 
                            size="small" 
                            onClick={handleClearToken}
                            style={{ marginLeft: 8 }}
                            danger
                          >
                            清除Token
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <Text type="secondary">未设置Token</Text>
                    )}
                  </div>
                </Card>
              </Col>
              
              <Col span={12}>
                <Card size="small" title="获取新Token">
                  <Form
                    form={loginForm}
                    layout="vertical"
                    onFinish={handleLogin}
                    size="small"
                    onSubmitCapture={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                    }}
                  >
                    <Form.Item
                      name="username"
                      label="用户名"
                      rules={[{ required: true, message: '请输入用户名' }]}
                    >
                      <Input placeholder="请输入用户名" />
                    </Form.Item>
                    
                    <Form.Item
                      name="password"
                      label="密码"
                      rules={[{ required: true, message: '请输入密码' }]}
                    >
                      <Input.Password 
                        placeholder="请输入密码"
                        iconRender={(visible) => (visible ? <EyeOutlined /> : <EyeInvisibleOutlined />)}
                      />
                    </Form.Item>
                    
                    <Form.Item style={{ marginBottom: 0 }}>
                      <Button
                        type="primary"
                        onClick={() => {
                          loginForm.validateFields().then(values => {
                            handleLogin(values);
                          }).catch(err => {
                            console.log('Validation failed:', err);
                          });
                        }}
                        loading={loginLoading}
                        icon={<LoginOutlined />}
                        block
                      >
                        {loginLoading ? '获取中...' : '获取Token'}
                      </Button>
                    </Form.Item>
                  </Form>
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="请求参数" key="params">
            <Form.Item
              name="params"
              label="查询参数"
              tooltip="URL查询参数，如: page=1&size=10"
            >
              <TextArea
                rows={4}
                placeholder="请输入查询参数，每行一个，格式: key=value"
                style={{
                  fontFamily: 'monospace',
                  backgroundColor: '#fafafa',
                  color: '#262626'
                }}
              />
            </Form.Item>
          </TabPane>

          <TabPane tab="请求体" key="body">
            <Form.Item
              name="body"
              label="请求体 (JSON)"
              tooltip="POST、PUT、PATCH请求的请求体数据"
            >
              <TextArea
                rows={8}
                placeholder="请求体为空或参考预填充内容"
                style={{
                  fontFamily: 'monospace',
                  backgroundColor: '#fafafa',
                  color: '#262626'
                }}
              />
            </Form.Item>
          </TabPane>

          <TabPane tab="请求头" key="headers">
            <Form.Item
              name="headers"
              label="请求头 (JSON)"
              tooltip="自定义请求头，JSON格式。预填充了常用请求头，可直接修改使用"
            >
              <TextArea
                rows={6}
                placeholder="请求头为空或参考预填充内容"
                style={{
                  fontFamily: 'monospace',
                  backgroundColor: '#fafafa',
                  color: '#262626'
                }}
              />
            </Form.Item>
          </TabPane>
        </Tabs>

        <Divider />

        <div style={{ textAlign: 'center', marginBottom: 16 }}>
          <Space size="middle">
            <Button
              onClick={initializeForm}
              style={{ marginRight: 8 }}
            >
              重置为默认值
            </Button>
            {currentToken && (
              <Button
                onClick={() => {
                  // 更新请求头中的Authorization
                  const currentHeaders = form.getFieldValue('headers');
                  let headers: Record<string, string> = {};
                  try {
                    headers = currentHeaders ? JSON.parse(currentHeaders) : {};
                  } catch (error) {
                    headers = {};
                  }
                  headers['Authorization'] = `Bearer ${currentToken}`;
                  form.setFieldValue('headers', JSON.stringify(headers, null, 2));
                  message.success('已更新请求头中的Token');
                }}
                icon={<KeyOutlined />}
              >
                更新Token到请求头
              </Button>
            )}
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              size="large"
              icon={<PlayCircleOutlined />}
            >
              {loading ? '测试中...' : '开始测试'}
            </Button>
          </Space>
        </div>
      </Form>

      {/* 测试结果 */}
      {testResult && (
        <Card
          title="测试结果"
          style={{ marginTop: 16 }}
          extra={
            <Button
              icon={<CopyOutlined />}
              onClick={() => copyToClipboard(JSON.stringify(testResult, null, 2))}
            >
              复制结果
            </Button>
          }
        >
          {/* 状态概览 */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card size="small">
                <div style={{ textAlign: 'center' }}>
                  {testResult.success ? (
                    <CheckCircleOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                  ) : (
                    <ExclamationCircleOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />
                  )}
                  <div style={{ marginTop: 8 }}>
                    <Text strong>{testResult.success ? '成功' : '失败'}</Text>
                  </div>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <div style={{ textAlign: 'center' }}>
                  <Tag color={getStatusColor(testResult.status_code)} style={{ fontSize: 14 }}>
                    {testResult.status_code}
                  </Tag>
                  <div style={{ marginTop: 8 }}>
                    <Text type="secondary">状态码</Text>
                  </div>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <div style={{ textAlign: 'center' }}>
                  <ClockCircleOutlined style={{ fontSize: 18, color: '#1890ff' }} />
                  <div style={{ marginTop: 8 }}>
                    <Text strong>{formatResponseTime(testResult.response_time_ms)}</Text>
                  </div>
                  <div>
                    <Text type="secondary">响应时间</Text>
                  </div>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <div style={{ textAlign: 'center' }}>
                  <Text strong style={{ fontSize: 18 }}>
                    {testResult.response_data ? Object.keys(testResult.response_data).length : 0}
                  </Text>
                  <div style={{ marginTop: 8 }}>
                    <Text type="secondary">返回字段</Text>
                  </div>
                </div>
              </Card>
            </Col>
          </Row>

          {/* 错误信息 */}
          {testResult.error && (
            <Alert
              type="error"
              message="请求失败"
              description={testResult.error}
              style={{ marginBottom: 16 }}
            />
          )}

          {/* 响应详情 */}
          <Tabs>
            <TabPane tab="响应数据" key="response">
              <div style={{ 
                backgroundColor: '#f5f5f5', 
                color: '#262626',
                padding: 16, 
                borderRadius: 6,
                maxHeight: 300,
                overflow: 'auto',
                border: '1px solid #d9d9d9'
              }}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                  {typeof testResult.response_data === 'string' 
                    ? testResult.response_data 
                    : JSON.stringify(testResult.response_data, null, 2)}
                </pre>
              </div>
            </TabPane>
            <TabPane tab="响应头" key="headers">
              <div style={{ 
                backgroundColor: '#f5f5f5',
                color: '#262626', 
                padding: 16, 
                borderRadius: 6,
                maxHeight: 300,
                overflow: 'auto',
                border: '1px solid #d9d9d9'
              }}>
                <pre style={{ margin: 0, fontFamily: 'monospace' }}>
                  {JSON.stringify(testResult.headers, null, 2)}
                </pre>
              </div>
            </TabPane>
          </Tabs>
        </Card>
      )}
    </Modal>
  );
};
