import React, { useState, useEffect } from 'react';
import {
  Form,
  Input,
  Select,
  Switch,
  InputNumber,
  Button,
  Space,
  Typography,
  Divider,
  Row,
  Col,
  Card,
  Tag,
  Tabs,
  Collapse,
  message,
} from 'antd';
import {
  PlusOutlined,
  MinusCircleOutlined,
  SaveOutlined,
  CloseOutlined,
  CodeOutlined,
  FileTextOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { 
  APIEndpoint, 
  HTTPMethod, 
  ServiceType, 
  RequestBodySchema, 
  RequestBodyType,
  FieldType,
  FieldSchema 
} from '../../types';
import { apiService } from '../../services/api';

const { TextArea } = Input;
const { Option } = Select;
const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Panel } = Collapse;

// 需要请求体的HTTP方法
const METHODS_WITH_BODY = ['POST', 'PUT', 'PATCH'];

// 请求体类型选项
const REQUEST_BODY_TYPES = [
  { value: 'json', label: 'JSON' },
  { value: 'form-data', label: 'Form Data' },
  { value: 'x-www-form-urlencoded', label: 'URL Encoded' },
  { value: 'raw', label: 'Raw Text' },
  { value: 'binary', label: 'Binary' },
];

// 字段类型选项
const FIELD_TYPES = [
  { value: 'string', label: '字符串' },
  { value: 'number', label: '数字' },
  { value: 'integer', label: '整数' },
  { value: 'boolean', label: '布尔值' },
  { value: 'object', label: '对象' },
  { value: 'array', label: '数组' },
  { value: 'file', label: '文件' },
];

interface ApiEndpointFormProps {
  endpoint?: APIEndpoint | null;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export const APIEndpointForm: React.FC<ApiEndpointFormProps> = ({
  endpoint,
  onSuccess,
  onCancel,
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('basic');
  const [selectedMethod, setSelectedMethod] = useState<HTTPMethod>('GET');

  useEffect(() => {
    if (endpoint) {
      // 获取请求体schema数据
      const requestBodySchema = endpoint.request_body_schema;
      
      form.setFieldsValue({
        name: endpoint.name,
        path: endpoint.path,
        method: endpoint.method,
        description: endpoint.description || '',
        service_type: endpoint.service_type,
        is_active: endpoint.is_active,
        is_deprecated: endpoint.is_deprecated,
        auth_required: endpoint.auth_required,
        rate_limit: endpoint.rate_limit,
        tags: endpoint.tags || [],
        version: endpoint.version || '1.0.0',
        documentation_url: endpoint.documentation_url || '',
        permissions_required: endpoint.permissions_required || [],
        
        // 请求体配置
        request_body_type: requestBodySchema?.type || 'json',
        request_body_required: requestBodySchema?.required || false,
        request_body_description: requestBodySchema?.description || '',
        request_body_example: requestBodySchema?.example ? JSON.stringify(requestBodySchema.example, null, 2) : '',
      });
      
      setSelectedMethod(endpoint.method);
    } else {
      // 新建API端点时，提供智能默认值
      const defaultExample = JSON.stringify({
        "name": "示例名称",
        "description": "示例描述", 
        "data": {
          "field1": "value1",
          "field2": 123,
          "field3": true
        }
      }, null, 2);

      form.resetFields();
      form.setFieldsValue({
        is_active: true,
        is_deprecated: false,
        auth_required: true,
        rate_limit: 100,
        version: '1.0.0',
        tags: [],
        permissions_required: [],
        request_body_type: 'json',
        request_body_required: false,
        request_body_description: '请求体包含API调用所需的数据',
        request_body_example: defaultExample,
      });
      setSelectedMethod('GET');
    }
  }, [endpoint, form]);

  // 处理HTTP方法变化
  const handleMethodChange = (method: HTTPMethod) => {
    setSelectedMethod(method);
    // 如果切换到不需要请求体的方法，清空请求体相关字段
    if (!METHODS_WITH_BODY.includes(method)) {
      form.setFieldsValue({
        request_body_type: 'json',
        request_body_required: false,
        request_body_description: '',
        request_body_example: '',
      });
    }
  };

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      // 构建请求体schema
      let requestBodySchema: RequestBodySchema | undefined;
      
      if (METHODS_WITH_BODY.includes(values.method) && values.request_body_type) {
        requestBodySchema = {
          type: values.request_body_type,
          description: values.request_body_description,
          required: values.request_body_required,
          content_type: values.request_body_type === 'json' ? 'application/json' : 
                       values.request_body_type === 'form-data' ? 'multipart/form-data' :
                       values.request_body_type === 'x-www-form-urlencoded' ? 'application/x-www-form-urlencoded' :
                       'text/plain',
        };
        
        // 解析示例数据
        if (values.request_body_example) {
          try {
            requestBodySchema.example = JSON.parse(values.request_body_example);
          } catch (error) {
            // 如果不是JSON格式，直接保存为字符串
            requestBodySchema.example = values.request_body_example;
          }
        }
      }

      const data = {
        ...values,
        tags: values.tags || [],
        permissions_required: values.permissions_required || [],
        request_body_schema: requestBodySchema,
        // 移除表单特有字段
        request_body_type: undefined,
        request_body_required: undefined,
        request_body_description: undefined,
        request_body_example: undefined,
      };

      // 清理undefined字段
      Object.keys(data).forEach(key => {
        if (data[key] === undefined) {
          delete data[key];
        }
      });

      if (endpoint) {
        await apiService.updateAPIEndpoint(endpoint.id, data);
        message.success('API端点更新成功');
      } else {
        await apiService.createAPIEndpoint(data);
        message.success('API端点创建成功');
      }

      onSuccess?.();
    } catch (error: any) {
      message.error(
        endpoint 
          ? `更新失败: ${error.message || '未知错误'}` 
          : `创建失败: ${error.message || '未知错误'}`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel?.();
  };

  return (
    <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          is_active: true,
          is_deprecated: false,
          auth_required: true,
          rate_limit: 100,
          version: '1.0.0',
          request_body_type: 'json',
          request_body_required: false,
        }}
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* 基本信息标签页 */}
          <TabPane 
            tab={
              <span>
                <SettingOutlined />
                基本信息
              </span>
            } 
            key="basic"
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="name"
                  label="接口名称"
                  rules={[
                    { required: true, message: '请输入接口名称' },
                    { max: 100, message: '名称长度不能超过100个字符' },
                  ]}
                >
                  <Input placeholder="例如: 获取用户列表" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="path"
                  label="接口路径"
                  rules={[
                    { required: true, message: '请输入接口路径' },
                    { pattern: /^\//, message: '路径必须以/开头' },
                  ]}
                >
                  <Input placeholder="例如: /api/users/" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  name="method"
                  label="HTTP方法"
                  rules={[{ required: true, message: '请选择HTTP方法' }]}
                >
                  <Select placeholder="选择方法" onChange={handleMethodChange}>
                    <Option value="GET">
                      <Tag color="green">GET</Tag>
                    </Option>
                    <Option value="POST">
                      <Tag color="blue">POST</Tag>
                    </Option>
                    <Option value="PUT">
                      <Tag color="orange">PUT</Tag>
                    </Option>
                    <Option value="DELETE">
                      <Tag color="red">DELETE</Tag>
                    </Option>
                    <Option value="PATCH">
                      <Tag color="purple">PATCH</Tag>
                    </Option>
                    <Option value="HEAD">
                      <Tag color="default">HEAD</Tag>
                    </Option>
                    <Option value="OPTIONS">
                      <Tag color="default">OPTIONS</Tag>
                    </Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="service_type"
                  label="服务类型"
                  rules={[{ required: true, message: '请选择服务类型' }]}
                >
                  <Select placeholder="选择服务类型">
                    <Option value="django">Django</Option>
                    <Option value="fastapi">FastAPI</Option>
                    <Option value="other">其他</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="version"
                  label="版本"
                  rules={[{ required: true, message: '请输入版本号' }]}
                >
                  <Input placeholder="例如: 1.0.0" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="description"
              label="描述"
              rules={[{ max: 500, message: '描述长度不能超过500个字符' }]}
            >
              <TextArea 
                rows={3} 
                placeholder="详细描述接口的功能和用途..." 
              />
            </Form.Item>

            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  name="is_active"
                  label="启用状态"
                  valuePropName="checked"
                >
                  <Switch checkedChildren="启用" unCheckedChildren="停用" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="is_deprecated"
                  label="废弃状态"
                  valuePropName="checked"
                >
                  <Switch checkedChildren="已废弃" unCheckedChildren="正常" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="auth_required"
                  label="需要认证"
                  valuePropName="checked"
                >
                  <Switch checkedChildren="需要" unCheckedChildren="不需要" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="rate_limit"
                  label="访问限制(次/分钟)"
                  rules={[
                    { type: 'number', min: 1, message: '限制值必须大于0' },
                  ]}
                >
                  <InputNumber 
                    min={1} 
                    max={10000}
                    style={{ width: '100%' }}
                    placeholder="例如: 100" 
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="documentation_url"
                  label="文档URL"
                  rules={[
                    { type: 'url', message: '请输入有效的URL' },
                  ]}
                >
                  <Input placeholder="例如: https://docs.example.com/api" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="tags"
              label="标签"
              tooltip="用于分类和过滤接口"
            >
              <Select
                mode="tags"
                style={{ width: '100%' }}
                placeholder="输入标签，按回车添加"
                maxTagCount={10}
              />
            </Form.Item>

            <Form.Item
              name="permissions_required"
              label="所需权限"
              tooltip="访问此接口需要的权限列表"
            >
              <Select
                mode="tags"
                style={{ width: '100%' }}
                placeholder="输入权限名称，按回车添加"
                maxTagCount={10}
              />
            </Form.Item>
          </TabPane>

          {/* 请求体配置标签页 */}
          <TabPane 
            tab={
              <span>
                <CodeOutlined />
                请求体配置
              </span>
            } 
            key="request_body"
          >
            {METHODS_WITH_BODY.includes(selectedMethod) ? (
              <>
                <Row gutter={16}>
                  <Col span={8}>
                    <Form.Item
                      name="request_body_type"
                      label="请求体类型"
                    >
                      <Select placeholder="选择请求体类型">
                        {REQUEST_BODY_TYPES.map(type => (
                          <Option key={type.value} value={type.value}>
                            {type.label}
                          </Option>
                        ))}
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item
                      name="request_body_required"
                      label="是否必需"
                      valuePropName="checked"
                    >
                      <Switch checkedChildren="必需" unCheckedChildren="可选" />
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item
                  name="request_body_description"
                  label="请求体描述"
                >
                  <TextArea 
                    rows={2} 
                    placeholder="描述请求体的用途和格式..." 
                  />
                </Form.Item>

                <Form.Item
                  name="request_body_example"
                  label="请求体示例"
                  tooltip="提供JSON格式的示例数据"
                >
                  <TextArea 
                    rows={8} 
                    placeholder={JSON.stringify({
                      "name": "示例名称",
                      "description": "示例描述",
                      "data": {
                        "field1": "value1",
                        "field2": 123,
                        "field3": true
                      }
                    }, null, 2)}
                    style={{ 
                      fontFamily: 'monospace',
                      backgroundColor: '#fafafa',
                      color: '#262626',
                      border: '1px solid #d9d9d9'
                    }}
                  />
                </Form.Item>
              </>
            ) : (
              <div style={{ 
                textAlign: 'center', 
                padding: '40px', 
                color: '#595959',
                background: '#f5f5f5',
                borderRadius: '6px',
                border: '1px solid #d9d9d9'
              }}>
                <CodeOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                <div>
                  <Text type="secondary">
                    {selectedMethod} 方法不需要请求体配置
                  </Text>
                </div>
                <div style={{ marginTop: '8px' }}>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    只有 POST、PUT、PATCH 方法需要配置请求体
                  </Text>
                </div>
              </div>
            )}
          </TabPane>

          {/* 文档信息标签页 */}
          <TabPane 
            tab={
              <span>
                <FileTextOutlined />
                文档信息
              </span>
            } 
            key="documentation"
          >
            <Card 
              style={{ 
                textAlign: 'center', 
                border: '2px dashed #d9d9d9',
                backgroundColor: '#f5f5f5'
              }}
            >
              <div style={{ padding: '40px 20px' }}>
                <FileTextOutlined 
                  style={{ 
                    fontSize: '64px', 
                    color: '#d9d9d9', 
                    marginBottom: '24px' 
                  }} 
                />
                <Title level={4} type="secondary">
                  API文档配置功能开发中
                </Title>
                <Text type="secondary" style={{ fontSize: '14px', lineHeight: '1.6' }}>
                  响应Schema和参数配置功能正在开发中，敬请期待...
                </Text>
                <div style={{ marginTop: '16px' }}>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    🚀 未来版本将支持：
                  </Text>
                  <div style={{ marginTop: '12px' }}>
                    <Space direction="vertical" size="small">
                      <Tag color="blue">📝 完整的OpenAPI 3.0规范支持</Tag>
                      <Tag color="green">🔧 响应Schema可视化配置</Tag>
                      <Tag color="orange">⚙️ 请求参数详细定义</Tag>
                      <Tag color="purple">📚 自动生成API文档</Tag>
                      <Tag color="cyan">🔗 与Swagger UI深度集成</Tag>
                    </Space>
                  </div>
                </div>
                <div style={{ marginTop: '24px' }}>
                  <Text type="secondary" style={{ fontSize: '11px' }}>
                    当前版本专注于请求体配置，文档功能将在后续版本中逐步完善
                  </Text>
                </div>
              </div>
            </Card>
          </TabPane>
        </Tabs>

        {/* 操作按钮 */}
        <Divider />
        <div style={{ textAlign: 'right' }}>
          <Space>
            <Button onClick={handleCancel}>
              <CloseOutlined />
              取消
            </Button>
            <Button type="primary" htmlType="submit" loading={loading}>
              <SaveOutlined />
              {endpoint ? '更新' : '创建'}
            </Button>
          </Space>
        </div>
      </Form>
    </div>
  );
};
