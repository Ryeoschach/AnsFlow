import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Input,
  Select,
  Tag,
  Modal,
  Popconfirm,
  Tabs,
  Row,
  Col,
  Space,
  Statistic,
  Dropdown,
  Typography,
  Tooltip,
  Alert,
  message,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  MoreOutlined,
  SearchOutlined,
  ApiOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  ClockCircleOutlined,
  LinkOutlined,
  TagsOutlined,
  CloudServerOutlined,
  ImportOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { usePermissions } from '../../hooks/usePermissions';
import { apiService } from '../../services/api';
import {
  APIEndpoint,
  APIStatistics,
  HTTPMethod,
  ServiceType,
} from '../../types';
import dayjs from 'dayjs';

// 子组件导入
import { APIEndpointForm } from './ApiEndpointForm';
import { APITestDialog } from './ApiTestDialog';
import { APIStatisticsPanel } from './ApiStatisticsPanel';
import { ApiImportDialog } from './ApiImportDialog';

const { Option } = Select;
const { TabPane } = Tabs;
const { Title, Text } = Typography;

const methodColors: Record<HTTPMethod, string> = {
  GET: 'green',
  POST: 'blue',
  PUT: 'orange',
  DELETE: 'red',
  PATCH: 'purple',
  HEAD: 'default',
  OPTIONS: 'default',
};

const serviceTypeNames: Record<ServiceType, string> = {
  django: 'Django',
  fastapi: 'FastAPI',
  other: '其他',
};

export const ApiManagement: React.FC = () => {
  const [endpoints, setEndpoints] = useState<APIEndpoint[]>([]);
  const [statistics, setStatistics] = useState<APIStatistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedServiceType, setSelectedServiceType] = useState<ServiceType | 'all'>('all');
  const [selectedEndpoint, setSelectedEndpoint] = useState<APIEndpoint | null>(null);
  const [isFormModalVisible, setIsFormModalVisible] = useState(false);
  const [isTestModalVisible, setIsTestModalVisible] = useState(false);
  const [isImportModalVisible, setIsImportModalVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('endpoints');

  const {
    canViewAPIEndpoints,
    canEditAPIEndpoints,
    canDeleteAPIEndpoints,
    canTestAPIEndpoints,
    canDiscoverAPIEndpoints,
    loading: permissionLoading,
    userInfo,
    hasPermission,
    isAdmin,
    isSuperAdmin,
  } = usePermissions();



  // 加载API端点列表
  const loadEndpoints = async () => {
    if (!canViewAPIEndpoints()) {
      message.error('您没有查看API端点的权限');
      return;
    }

    setLoading(true);
    try {
      const data = await apiService.getAPIEndpoints();
      setEndpoints(Array.isArray(data) ? data : data.results || []);
    } catch (error) {
      message.error('无法加载API端点列表');
      console.error('Load endpoints error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 加载统计数据
  const loadStatistics = async () => {
    try {
      // 计算请求体相关统计
      const endpointsWithRequestBody = endpoints.filter(e => 
        ['POST', 'PUT', 'PATCH'].includes(e.method) && e.request_body_schema
      );
      
      const requestBodyTypeBreakdown = {
        json: endpointsWithRequestBody.filter(e => e.request_body_schema?.type === 'json').length,
        'form-data': endpointsWithRequestBody.filter(e => e.request_body_schema?.type === 'form-data').length,
        'x-www-form-urlencoded': endpointsWithRequestBody.filter(e => e.request_body_schema?.type === 'x-www-form-urlencoded').length,
        raw: endpointsWithRequestBody.filter(e => e.request_body_schema?.type === 'raw').length,
        binary: endpointsWithRequestBody.filter(e => e.request_body_schema?.type === 'binary').length,
      };

      // 暂时使用模拟数据
      const mockStats: APIStatistics = {
        total_endpoints: endpoints.length,
        active_endpoints: endpoints.filter(e => e.is_active).length,
        deprecated_endpoints: endpoints.filter(e => e.is_deprecated).length,
        service_type_breakdown: {
          django: endpoints.filter(e => e.service_type === 'django').length,
          fastapi: endpoints.filter(e => e.service_type === 'fastapi').length,
          other: endpoints.filter(e => e.service_type === 'other').length,
        },
        method_breakdown: {
          GET: endpoints.filter(e => e.method === 'GET').length,
          POST: endpoints.filter(e => e.method === 'POST').length,
          PUT: endpoints.filter(e => e.method === 'PUT').length,
          DELETE: endpoints.filter(e => e.method === 'DELETE').length,
          PATCH: endpoints.filter(e => e.method === 'PATCH').length,
          HEAD: endpoints.filter(e => e.method === 'HEAD').length,
          OPTIONS: endpoints.filter(e => e.method === 'OPTIONS').length,
        },
        avg_response_time: 120,
        total_calls: 15420,
        calls_today: 234,
        top_endpoints: endpoints.slice(0, 5).map(e => ({
          id: e.id,
          name: e.name,
          path: e.path,
          call_count: e.call_count,
          avg_response_time: e.avg_response_time,
        })),
      };
      
      // 将请求体统计信息记录在控制台，供后续扩展使用
      console.log('Request Body Statistics:', {
        endpoints_with_request_body: endpointsWithRequestBody.length,
        request_body_type_breakdown: requestBodyTypeBreakdown,
      });
      
      setStatistics(mockStats);
    } catch (error) {
      console.error('Failed to load statistics:', error);
    }
  };

  // 自动发现API端点
  const handleAutoDiscover = async () => {
    if (!canDiscoverAPIEndpoints) {
      message.error('您没有自动发现API端点的权限');
      return;
    }

    setLoading(true);
    try {
      // 暂时模拟发现结果
      message.success('发现 3 个新端点，更新 2 个端点');
      await loadEndpoints();
      await loadStatistics();
    } catch (error) {
      message.error('无法自动发现API端点');
    } finally {
      setLoading(false);
    }
  };

  // 删除API端点
  const handleDelete = async (endpoint: APIEndpoint) => {
    if (!canDeleteAPIEndpoints) {
      message.error('您没有删除API端点的权限');
      return;
    }

    try {
      await apiService.deleteAPIEndpoint(endpoint.id);
      message.success(`API端点 ${endpoint.path} 已删除`);
      await loadEndpoints();
      await loadStatistics();
    } catch (error) {
      message.error('无法删除API端点');
    }
  };

  // 测试API端点
  const handleTest = (endpoint: APIEndpoint) => {
    if (!canTestAPIEndpoints()) {
      message.error('您没有测试API端点的权限');
      return;
    }

    setSelectedEndpoint(endpoint);
    setIsTestModalVisible(true);
  };

  // 编辑API端点
  const handleEdit = (endpoint: APIEndpoint) => {
    if (!canEditAPIEndpoints) {
      message.error('您没有编辑API端点的权限');
      return;
    }

    setSelectedEndpoint(endpoint);
    setIsFormModalVisible(true);
  };

  // 创建新API端点
  const handleCreate = () => {
    if (!canEditAPIEndpoints) {
      message.error('您没有创建API端点的权限');
      return;
    }

    setSelectedEndpoint(null);
    setIsFormModalVisible(true);
  };

  // 过滤端点
  const filteredEndpoints = endpoints.filter((endpoint) => {
    const matchesSearch = !searchTerm || 
      endpoint.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
      endpoint.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      endpoint.description?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesServiceType = selectedServiceType === 'all' || 
      endpoint.service_type === selectedServiceType;
    
    return matchesSearch && matchesServiceType;
  });

  // 表格列定义
  const columns: ColumnsType<APIEndpoint> = [
    {
      title: '接口名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: APIEndpoint) => (
        <div>
          <div style={{ fontWeight: 500 }}>{name}</div>
          {record.description && (
            <div style={{ color: '#666', fontSize: '12px', marginTop: 4 }}>
              {record.description}
            </div>
          )}
          {record.tags && record.tags.length > 0 && (
            <div style={{ marginTop: 8 }}>
              {record.tags.map((tag, index) => (
                <Tag key={index} icon={<TagsOutlined />} color="default">
                  {tag}
                </Tag>
              ))}
            </div>
          )}
        </div>
      ),
    },
    {
      title: '路径',
      dataIndex: 'path',
      key: 'path',
      render: (path: string) => (
        <code style={{ 
          backgroundColor: '#f5f5f5', 
          padding: '4px 8px', 
          borderRadius: '4px',
          fontSize: '12px'
        }}>
          {path}
        </code>
      ),
    },
    {
      title: '方法',
      dataIndex: 'method',
      key: 'method',
      render: (method: HTTPMethod) => (
        <Tag color={methodColors[method]}>{method}</Tag>
      ),
    },
    {
      title: '请求体',
      key: 'request_body',
      render: (_, record: APIEndpoint) => {
        const hasRequestBody = ['POST', 'PUT', 'PATCH'].includes(record.method);
        if (!hasRequestBody || !record.request_body_schema) {
          return <span style={{ color: '#999' }}>-</span>;
        }

        const { type, description, required, example, schema } = record.request_body_schema;
        
        // 从schema.properties中提取字段信息
        const fields = schema?.properties ? Object.entries(schema.properties) : [];
        
        // 构建tooltip内容
        const tooltipContent = (
          <div style={{ maxWidth: 300 }}>
            <div style={{ marginBottom: 8 }}>
              <strong>类型:</strong> {type}
            </div>
            {description && (
              <div style={{ marginBottom: 8 }}>
                <strong>描述:</strong> {description}
              </div>
            )}
            {required !== undefined && (
              <div style={{ marginBottom: 8 }}>
                <strong>必需:</strong> {required ? '是' : '否'}
              </div>
            )}
            {fields && fields.length > 0 && (
              <div style={{ marginBottom: 8 }}>
                <strong>字段:</strong>
                <div style={{ marginTop: 4 }}>
                  {fields.slice(0, 3).map(([fieldName, fieldSchema], index) => (
                    <div key={index} style={{ fontSize: '12px', color: '#595959' }}>
                      • {fieldName} ({fieldSchema.type}){fieldSchema.required ? '*' : ''}
                    </div>
                  ))}
                  {fields.length > 3 && (
                    <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                      还有 {fields.length - 3} 个字段...
                    </div>
                  )}
                </div>
              </div>
            )}
            {example && (
              <div>
                <strong>示例:</strong>
                <pre style={{ 
                  fontSize: '11px', 
                  backgroundColor: '#f5f5f5',
                  color: '#262626',
                  padding: '4px',
                  borderRadius: '2px',
                  marginTop: '4px',
                  maxHeight: '100px',
                  overflow: 'auto',
                  border: '1px solid #d9d9d9'
                }}>
                  {typeof example === 'string' ? example : JSON.stringify(example, null, 2)}
                </pre>
              </div>
            )}
          </div>
        );

        return (
          <Tooltip title={tooltipContent} placement="topLeft">
            <div style={{ fontSize: '12px', cursor: 'pointer' }}>
              <div>
                <Tag color="cyan">{type}</Tag>
                {required && <Tag color="red">必需</Tag>}
              </div>
              {description && (
                <div style={{ color: '#595959', marginTop: 4, maxWidth: 180 }}>
                  {description.length > 40 ? `${description.substring(0, 40)}...` : description}
                </div>
              )}
              {fields && fields.length > 0 && (
                <div style={{ color: '#8c8c8c', marginTop: 2, fontSize: '11px' }}>
                  {fields.length} 个字段
                </div>
              )}
            </div>
          </Tooltip>
        );
      },
    },
    {
      title: '服务类型',
      dataIndex: 'service_type',
      key: 'service_type',
      render: (serviceType: ServiceType) => (
        <Tag icon={<CloudServerOutlined />} color="blue">
          {serviceTypeNames[serviceType]}
        </Tag>
      ),
    },
    {
      title: '状态',
      key: 'status',
      render: (_, record: APIEndpoint) => (
        <Space direction="vertical" size="small">
          <Tag color={record.is_active ? 'green' : 'default'}>
            {record.is_active ? '活跃' : '停用'}
          </Tag>
          {record.is_deprecated && (
            <Tag color="red">已废弃</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (updatedAt: string) => (
        <div style={{ display: 'flex', alignItems: 'center', color: '#666' }}>
          <ClockCircleOutlined style={{ marginRight: 4 }} />
          {dayjs(updatedAt).format('YYYY-MM-DD HH:mm')}
        </div>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: APIEndpoint) => {
        const items = [
          canTestAPIEndpoints() && {
            key: 'test',
            icon: <PlayCircleOutlined />,
            label: '测试接口',
            onClick: () => handleTest(record),
          },
          canEditAPIEndpoints() && {
            key: 'edit',
            icon: <EditOutlined />,
            label: '编辑',
            onClick: () => handleEdit(record),
          },
          record.documentation_url && {
            key: 'docs',
            icon: <LinkOutlined />,
            label: (
              <a 
                href={record.documentation_url} 
                target="_blank" 
                rel="noopener noreferrer"
              >
                查看文档
              </a>
            ),
          },
          canDeleteAPIEndpoints() && {
            key: 'delete',
            icon: <DeleteOutlined />,
            label: (
              <Popconfirm
                title="确定要删除此接口吗？"
                description="此操作无法撤销"
                onConfirm={() => handleDelete(record)}
                okText="确定"
                cancelText="取消"
              >
                <span style={{ color: '#ff4d4f' }}>删除</span>
              </Popconfirm>
            ),
          },
        ].filter(Boolean) as any[];

        return (
          <Dropdown 
            menu={{ items }} 
            trigger={['click']}
          >
            <Button icon={<MoreOutlined />} />
          </Dropdown>
        );
      },
    },
  ];

  useEffect(() => {
    loadEndpoints();
  }, []);

  useEffect(() => {
    if (endpoints.length > 0) {
      loadStatistics();
    }
  }, [endpoints]);

  if (!canViewAPIEndpoints) {
    return (
      <Card>
        <div style={{ textAlign: 'center', color: '#666', padding: '32px 0' }}>
          您没有查看API端点的权限
        </div>
      </Card>
    );
  }  return (
    <div style={{ marginBottom: 24 }}>
      {/* 页头 */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'flex-start',
        marginBottom: 24 
      }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>API接口管理</Title>
          <Text type="secondary">管理系统中的所有API端点</Text>
        </div>
        <Space>
          {canDiscoverAPIEndpoints() && (
            <Button 
              icon={<ReloadOutlined />}
              onClick={handleAutoDiscover} 
              loading={loading}
            >
              自动发现
            </Button>
          )}
          {canEditAPIEndpoints() && (
            <Button 
              icon={<ImportOutlined />}
              onClick={() => setIsImportModalVisible(true)}
            >
              批量导入
            </Button>
          )}
          {canEditAPIEndpoints() && (
            <Button 
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              新增接口
            </Button>
          )}
        </Space>
      </div>

      {/* 标签页 */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="接口列表" key="endpoints">
          {/* 搜索和过滤 */}
          <Card style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col flex="auto">
                <Input
                  placeholder="搜索接口名称、路径或描述..."
                  prefix={<SearchOutlined />}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  allowClear
                />
              </Col>
              <Col>
                <Select
                  value={selectedServiceType}
                  onChange={setSelectedServiceType}
                  style={{ width: 150 }}
                >
                  <Option value="all">所有服务</Option>
                  <Option value="django">Django</Option>
                  <Option value="fastapi">FastAPI</Option>
                  <Option value="other">其他</Option>
                </Select>
              </Col>
            </Row>
          </Card>

          {/* 接口表格 */}
          <Card>
            <Table
              columns={columns}
              dataSource={filteredEndpoints}
              rowKey="id"
              loading={loading}
              pagination={{
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => 
                  `第 ${range[0]}-${range[1]} 条/共 ${total} 条`,
              }}
            />
          </Card>
        </TabPane>

        <TabPane tab="统计信息" key="statistics">
          {/* 模拟数据提示 */}
          <Alert
            message="数据说明"
            description="当前统计数据包含部分模拟信息（如调用次数、响应时间等）。真实的API监控和统计功能正在开发中。"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
            closable
          />
          
          {statistics && (
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="总端点数"
                    value={statistics.total_endpoints}
                    prefix={<ApiOutlined />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="活跃端点"
                    value={statistics.active_endpoints}
                    valueStyle={{ color: '#3f8600' }}
                    prefix={<ExperimentOutlined />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="今日调用"
                    value={statistics.calls_today}
                    prefix={<BarChartOutlined />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="平均响应时间"
                    value={statistics.avg_response_time}
                    suffix="ms"
                    prefix={<ClockCircleOutlined />}
                  />
                </Card>
              </Col>
            </Row>
          )}
        </TabPane>
      </Tabs>

      {/* 表单模态框 */}
      <Modal
        title={selectedEndpoint ? '编辑API端点' : '新增API端点'}
        open={isFormModalVisible}
        onCancel={() => setIsFormModalVisible(false)}
        footer={null}
        width={900}
        destroyOnClose
      >
        <APIEndpointForm
          endpoint={selectedEndpoint}
          onSuccess={async () => {
            setIsFormModalVisible(false);
            setSelectedEndpoint(null);
            await loadEndpoints();
            await loadStatistics();
          }}
          onCancel={() => setIsFormModalVisible(false)}
        />
      </Modal>

      {/* 测试模态框 */}
      {selectedEndpoint && (
        <APITestDialog
          endpoint={selectedEndpoint}
          open={isTestModalVisible}
          onOpenChange={setIsTestModalVisible}
        />
      )}

      {/* 批量导入模态框 */}
      <ApiImportDialog
        open={isImportModalVisible}
        onOpenChange={setIsImportModalVisible}
        onSuccess={async () => {
          await loadEndpoints();
          await loadStatistics();
        }}
      />
    </div>
  );
};
