import React, { useState } from 'react';
import {
  Modal,
  Button,
  Upload,
  Steps,
  Table,
  Tag,
  Card,
  Space,
  Typography,
  Alert,
  Progress,
  Checkbox,
  Divider,
  message,
} from 'antd';
import {
  UploadOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ImportOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { APIEndpoint, HTTPMethod, ServiceType } from '../../types';
import { apiService } from '../../services/api';

const { Title, Text, Paragraph } = Typography;
const { Step } = Steps;

interface ApiImportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

interface ImportEndpoint extends Omit<APIEndpoint, 'id' | 'created_at' | 'updated_at'> {
  import_status?: 'pending' | 'success' | 'error' | 'skipped';
  import_error?: string;
  selected?: boolean;
}

export const ApiImportDialog: React.FC<ApiImportDialogProps> = ({
  open,
  onOpenChange,
  onSuccess,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [importData, setImportData] = useState<ImportEndpoint[]>([]);
  const [importing, setImporting] = useState(false);
  const [importProgress, setImportProgress] = useState(0);
  const [importResults, setImportResults] = useState<{
    success: number;
    error: number;
    skipped: number;
  }>({ success: 0, error: 0, skipped: 0 });

  // 预定义的API端点数据
  const getPredefinedEndpoints = (): ImportEndpoint[] => [
    {
      name: '用户列表',
      path: '/api/users/',
      method: 'GET' as HTTPMethod,
      description: '获取系统用户列表',
      service_type: 'django' as ServiceType,
      is_enabled: true,
      auth_required: true,
      rate_limit: 100,
      permissions_required: ['USER_VIEW'],
      is_active: true,
      is_deprecated: false,
      tags: ['用户管理', '基础API'],
      version: '1.0.0',
      deprecated: false,
      selected: true,
      call_count: 0,
      avg_response_time: 0,
    },
    {
      name: '创建用户',
      path: '/api/users/',
      method: 'POST' as HTTPMethod,
      description: '创建新用户账户',
      service_type: 'django' as ServiceType,
      is_enabled: true,
      auth_required: true,
      rate_limit: 50,
      permissions_required: ['USER_CREATE'],
      is_active: true,
      is_deprecated: false,
      tags: ['用户管理', '基础API'],
      version: '1.0.0',
      deprecated: false,
      selected: true,
      call_count: 0,
      avg_response_time: 0,
      request_body_schema: {
        type: 'json',
        description: '用户创建信息',
        required: true,
        content_type: 'application/json',
        schema: {
          type: 'object',
          properties: {
            username: {
              type: 'string',
              description: '用户名',
              required: true,
              minLength: 3,
              maxLength: 50
            },
            email: {
              type: 'string',
              description: '邮箱地址',
              required: true,
              format: 'email'
            },
            password: {
              type: 'string',
              description: '密码',
              required: true,
              minLength: 8
            }
          }
        },
        example: {
          username: 'newuser',
          email: 'user@example.com',
          password: 'securepassword123'
        }
      }
    },
    {
      name: '用户详情',
      path: '/api/users/{id}/',
      method: 'GET' as HTTPMethod,
      description: '获取指定用户的详细信息',
      service_type: 'django' as ServiceType,
      is_enabled: true,
      auth_required: true,
      rate_limit: 200,
      permissions_required: ['USER_VIEW'],
      is_active: true,
      is_deprecated: false,
      tags: ['用户管理', '基础API'],
      version: '1.0.0',
      deprecated: false,
      selected: true,
      call_count: 0,
      avg_response_time: 0,
    },
    {
      name: '更新用户',
      path: '/api/users/{id}/',
      method: 'PUT' as HTTPMethod,
      description: '更新用户信息',
      service_type: 'django' as ServiceType,
      is_enabled: true,
      auth_required: true,
      rate_limit: 50,
      permissions_required: ['USER_EDIT'],
      is_active: true,
      is_deprecated: false,
      tags: ['用户管理', '基础API'],
      version: '1.0.0',
      deprecated: false,
      selected: true,
      call_count: 0,
      avg_response_time: 0,
      request_body_schema: {
        type: 'json',
        description: '用户更新信息',
        required: true,
        content_type: 'application/json',
        schema: {
          type: 'object',
          properties: {
            email: {
              type: 'string',
              description: '邮箱地址',
              format: 'email'
            },
            first_name: {
              type: 'string',
              description: '名'
            },
            last_name: {
              type: 'string',
              description: '姓'
            }
          }
        }
      }
    },
    {
      name: 'API端点列表',
      path: '/api/settings/api-endpoints/',
      method: 'GET' as HTTPMethod,
      description: '获取API端点管理列表',
      service_type: 'django' as ServiceType,
      is_enabled: true,
      auth_required: true,
      rate_limit: 100,
      permissions_required: ['API_ENDPOINT_VIEW'],
      is_active: true,
      is_deprecated: false,
      tags: ['API管理', '设置'],
      version: '1.0.0',
      deprecated: false,
      selected: true,
      call_count: 0,
      avg_response_time: 0,
    },
    {
      name: 'CI/CD 流水线列表',
      path: '/api/pipelines/',
      method: 'GET' as HTTPMethod,
      description: '获取CI/CD流水线列表',
      service_type: 'django' as ServiceType,
      is_enabled: true,
      auth_required: true,
      rate_limit: 100,
      permissions_required: ['PIPELINE_VIEW'],
      is_active: true,
      is_deprecated: false,
      tags: ['CI/CD', '流水线'],
      version: '1.0.0',
      deprecated: false,
      selected: true,
      call_count: 0,
      avg_response_time: 0,
    },
    {
      name: '项目列表',
      path: '/api/projects/',
      method: 'GET' as HTTPMethod,
      description: '获取项目列表',
      service_type: 'django' as ServiceType,
      is_enabled: true,
      auth_required: true,
      rate_limit: 100,
      permissions_required: ['PROJECT_VIEW'],
      is_active: true,
      is_deprecated: false,
      tags: ['项目管理'],
      version: '1.0.0',
      deprecated: false,
      selected: true,
      call_count: 0,
      avg_response_time: 0,
    },
    {
      name: '系统设置',
      path: '/api/settings/global-config/',
      method: 'GET' as HTTPMethod,
      description: '获取系统全局配置',
      service_type: 'django' as ServiceType,
      is_enabled: true,
      auth_required: true,
      rate_limit: 50,
      permissions_required: ['GLOBAL_CONFIG_VIEW'],
      is_active: true,
      is_deprecated: false,
      tags: ['系统管理', '设置'],
      version: '1.0.0',
      deprecated: false,
      selected: true,
      call_count: 0,
      avg_response_time: 0,
    }
  ];

  // 方法颜色映射
  const methodColors: Record<HTTPMethod, string> = {
    GET: 'green',
    POST: 'blue',
    PUT: 'orange',
    DELETE: 'red',
    PATCH: 'purple',
    HEAD: 'default',
    OPTIONS: 'default',
  };

  // 导入状态颜色映射
  const statusColors = {
    pending: 'default',
    success: 'success',
    error: 'error',
    skipped: 'warning',
  };

  // 表格列定义
  const columns: ColumnsType<ImportEndpoint> = [
    {
      title: '选择',
      width: 60,
      render: (_, record, index) => (
        <Checkbox
          checked={record.selected}
          onChange={(e) => {
            const newData = [...importData];
            newData[index].selected = e.target.checked;
            setImportData(newData);
          }}
          disabled={importing}
        />
      ),
    },
    {
      title: '接口名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record) => (
        <div>
          <div style={{ fontWeight: 500 }}>{name}</div>
          {record.description && (
            <div style={{ color: '#666', fontSize: '12px', marginTop: 4 }}>
              {record.description}
            </div>
          )}
        </div>
      ),
    },
    {
      title: '方法',
      dataIndex: 'method',
      key: 'method',
      width: 80,
      render: (method: HTTPMethod) => (
        <Tag color={methodColors[method]}>{method}</Tag>
      ),
    },
    {
      title: '路径',
      dataIndex: 'path',
      key: 'path',
      render: (path: string) => (
        <code style={{ 
          backgroundColor: '#f5f5f5', 
          padding: '2px 4px', 
          borderRadius: '2px',
          fontSize: '12px'
        }}>
          {path}
        </code>
      ),
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => (
        <Space wrap>
          {tags?.map((tag, index) => (
            <Tag key={index}>{tag}</Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '状态',
      key: 'import_status',
      width: 100,
      render: (_, record) => {
        if (!record.import_status || record.import_status === 'pending') {
          return <Tag color="default">待导入</Tag>;
        }
        return (
          <Tag color={statusColors[record.import_status]}>
            {record.import_status === 'success' && '成功'}
            {record.import_status === 'error' && '失败'}
            {record.import_status === 'skipped' && '跳过'}
          </Tag>
        );
      },
    },
  ];

  // 加载预定义端点
  const loadPredefinedEndpoints = () => {
    const endpoints = getPredefinedEndpoints();
    setImportData(endpoints);
    setCurrentStep(1);
    message.success(`加载了 ${endpoints.length} 个预定义API端点`);
  };

  // 处理文件上传
  const handleFileUpload = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const data = JSON.parse(content);
        
        if (data.endpoints && Array.isArray(data.endpoints)) {
          const endpoints = data.endpoints.map((endpoint: any) => ({
            ...endpoint,
            selected: true,
            import_status: 'pending' as const,
          }));
          setImportData(endpoints);
          setCurrentStep(1);
          message.success(`从文件加载了 ${endpoints.length} 个API端点`);
        } else {
          message.error('文件格式不正确，请使用有效的API端点JSON文件');
        }
      } catch (error) {
        message.error('文件解析失败，请检查JSON格式');
      }
    };
    reader.readAsText(file);
    return false; // 阻止默认上传行为
  };

  // 全选/取消全选
  const handleSelectAll = (checked: boolean) => {
    const newData = importData.map(item => ({
      ...item,
      selected: checked
    }));
    setImportData(newData);
  };

  // 开始导入
  const startImport = async () => {
    const selectedEndpoints = importData.filter(item => item.selected);
    
    if (selectedEndpoints.length === 0) {
      message.warning('请至少选择一个API端点进行导入');
      return;
    }

    setImporting(true);
    setImportProgress(0);
    setCurrentStep(2);

    const results = { success: 0, error: 0, skipped: 0 };
    const newData = [...importData];

    for (let i = 0; i < selectedEndpoints.length; i++) {
      const endpoint = selectedEndpoints[i];
      const dataIndex = importData.findIndex(item => 
        item.name === endpoint.name && item.path === endpoint.path && item.method === endpoint.method
      );

      try {
        // 准备发送的数据
        const endpointData = {
          name: endpoint.name,
          path: endpoint.path,
          method: endpoint.method,
          description: endpoint.description,
          service_type: endpoint.service_type,
          is_enabled: endpoint.is_enabled,
          auth_required: endpoint.auth_required,
          rate_limit: endpoint.rate_limit,
          permissions_required: endpoint.permissions_required,
          is_active: endpoint.is_active,
          is_deprecated: endpoint.is_deprecated,
          tags: endpoint.tags,
          request_body_schema: endpoint.request_body_schema,
        };

        await apiService.createAPIEndpoint(endpointData);
        
        newData[dataIndex].import_status = 'success';
        results.success++;
        
        message.success(`✓ ${endpoint.name}`, 1);
      } catch (error: any) {
        if (error.response?.status === 400 && 
            error.response.data?.detail?.includes('already exists')) {
          newData[dataIndex].import_status = 'skipped';
          newData[dataIndex].import_error = '端点已存在';
          results.skipped++;
        } else {
          newData[dataIndex].import_status = 'error';
          newData[dataIndex].import_error = error.message || '导入失败';
          results.error++;
          message.error(`✗ ${endpoint.name}: ${error.message}`, 2);
        }
      }

      // 更新进度
      setImportProgress(((i + 1) / selectedEndpoints.length) * 100);
      setImportData([...newData]);
      
      // 添加短暂延迟避免请求过快
      await new Promise(resolve => setTimeout(resolve, 200));
    }

    setImportResults(results);
    setImporting(false);
    setCurrentStep(3);

    if (results.success > 0) {
      message.success(`导入完成！成功: ${results.success}, 失败: ${results.error}, 跳过: ${results.skipped}`);
      onSuccess?.();
    }
  };

  // 重置对话框
  const resetDialog = () => {
    setCurrentStep(0);
    setImportData([]);
    setImporting(false);
    setImportProgress(0);
    setImportResults({ success: 0, error: 0, skipped: 0 });
  };

  const handleClose = () => {
    resetDialog();
    onOpenChange(false);
  };

  return (
    <Modal
      title={
        <div>
          <ImportOutlined style={{ marginRight: 8 }} />
          API端点批量导入
        </div>
      }
      open={open}
      onCancel={handleClose}
      width={1000}
      footer={null}
      destroyOnClose
    >
      <Steps current={currentStep} style={{ marginBottom: 24 }}>
        <Step title="选择数据源" icon={<FileTextOutlined />} />
        <Step title="配置导入" icon={<ExclamationCircleOutlined />} />
        <Step title="执行导入" icon={<ReloadOutlined />} />
        <Step title="完成" icon={<CheckCircleOutlined />} />
      </Steps>

      {/* 步骤 0: 选择数据源 */}
      {currentStep === 0 && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Title level={4}>选择API端点数据源</Title>
          <Paragraph type="secondary">
            您可以使用预定义的端点模板，或者上传JSON文件来批量导入API端点
          </Paragraph>
          
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Card 
              hoverable 
              style={{ cursor: 'pointer' }}
              onClick={loadPredefinedEndpoints}
            >
              <div style={{ textAlign: 'center' }}>
                <FileTextOutlined style={{ fontSize: '48px', color: '#1890ff', marginBottom: '16px' }} />
                <Title level={5}>使用预定义模板</Title>
                <Text type="secondary">
                  包含用户管理、API管理、CI/CD等常见端点
                </Text>
              </div>
            </Card>

            <Divider>或</Divider>

            <Upload.Dragger
              beforeUpload={handleFileUpload}
              showUploadList={false}
              accept=".json"
            >
              <div style={{ padding: '20px' }}>
                <UploadOutlined style={{ fontSize: '48px', color: '#52c41a' }} />
                <Title level={5} style={{ marginTop: '16px' }}>上传JSON文件</Title>
                <Text type="secondary">
                  支持从导出的API端点JSON文件中导入
                </Text>
              </div>
            </Upload.Dragger>
          </Space>
        </div>
      )}

      {/* 步骤 1: 配置导入 */}
      {currentStep === 1 && (
        <div>
          <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Title level={5} style={{ margin: 0 }}>
                选择要导入的API端点 ({importData.filter(item => item.selected).length}/{importData.length})
              </Title>
              <Text type="secondary">请检查并选择需要导入的API端点</Text>
            </div>
            <Space>
              <Button 
                size="small" 
                onClick={() => handleSelectAll(true)}
              >
                全选
              </Button>
              <Button 
                size="small" 
                onClick={() => handleSelectAll(false)}
              >
                取消全选
              </Button>
            </Space>
          </div>

          <Table
            columns={columns}
            dataSource={importData}
            rowKey={(record) => `${record.method}-${record.path}`}
            pagination={false}
            size="small"
            scroll={{ y: 400 }}
          />

          <div style={{ marginTop: 16, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setCurrentStep(0)}>
                上一步
              </Button>
              <Button 
                type="primary" 
                onClick={startImport}
                disabled={importData.filter(item => item.selected).length === 0}
              >
                开始导入 ({importData.filter(item => item.selected).length} 个)
              </Button>
            </Space>
          </div>
        </div>
      )}

      {/* 步骤 2: 执行导入 */}
      {currentStep === 2 && (
        <div style={{ padding: '20px' }}>
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <Title level={4}>正在导入API端点...</Title>
            <Progress 
              percent={Math.round(importProgress)} 
              status={importing ? 'active' : 'success'}
              style={{ marginBottom: '16px' }}
            />
            <Text type="secondary">
              {importing ? '请稍候，正在导入中...' : '导入完成'}
            </Text>
          </div>

          <Table
            columns={columns.filter(col => col.key !== 'selected')}
            dataSource={importData.filter(item => item.selected)}
            rowKey={(record) => `${record.method}-${record.path}`}
            pagination={false}
            size="small"
            scroll={{ y: 300 }}
          />
        </div>
      )}

      {/* 步骤 3: 完成 */}
      {currentStep === 3 && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <CheckCircleOutlined 
            style={{ fontSize: '64px', color: '#52c41a', marginBottom: '24px' }} 
          />
          <Title level={3}>导入完成！</Title>
          
          <Card style={{ marginTop: '24px', textAlign: 'left' }}>
            <Title level={5}>导入结果统计</Title>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>✅ 成功导入: <strong>{importResults.success}</strong> 个端点</div>
              <div>⏭️ 跳过重复: <strong>{importResults.skipped}</strong> 个端点</div>
              <div>❌ 导入失败: <strong>{importResults.error}</strong> 个端点</div>
            </Space>
          </Card>

          <div style={{ marginTop: '24px' }}>
            <Space>
              <Button onClick={handleClose}>
                关闭
              </Button>
              <Button type="primary" onClick={handleClose}>
                查看API列表
              </Button>
            </Space>
          </div>
        </div>
      )}
    </Modal>
  );
};

export default ApiImportDialog;
