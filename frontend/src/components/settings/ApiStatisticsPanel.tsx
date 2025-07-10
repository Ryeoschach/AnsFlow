import React from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Table,
  Tag,
  Typography,
  Space,
  Divider,
} from 'antd';
import {
  ApiOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  RiseOutlined,
  CloudServerOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { APIStatistics, HTTPMethod, ServiceType } from '../../types';

const { Title, Text } = Typography;

interface ApiStatisticsPanelProps {
  statistics: APIStatistics;
}

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

export const APIStatisticsPanel: React.FC<ApiStatisticsPanelProps> = ({
  statistics,
}) => {
  // 热门端点表格列定义
  const topEndpointsColumns: ColumnsType<typeof statistics.top_endpoints[0]> = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_, __, index) => (
        <div style={{ textAlign: 'center' }}>
          {index === 0 && <TrophyOutlined style={{ color: '#faad14' }} />}
          {index === 1 && <TrophyOutlined style={{ color: '#d9d9d9' }} />}
          {index === 2 && <TrophyOutlined style={{ color: '#d48806' }} />}
          {index > 2 && <span>{index + 1}</span>}
        </div>
      ),
    },
    {
      title: '接口名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: '路径',
      dataIndex: 'path',
      key: 'path',
      render: (path: string) => (
        <code style={{ 
          backgroundColor: '#f5f5f5', 
          padding: '2px 6px', 
          borderRadius: '4px',
          fontSize: '12px'
        }}>
          {path}
        </code>
      ),
    },
    {
      title: '调用次数',
      dataIndex: 'call_count',
      key: 'call_count',
      sorter: (a, b) => a.call_count - b.call_count,
      render: (count: number) => (
        <Text strong>{count.toLocaleString()}</Text>
      ),
    },
    {
      title: '平均响应时间',
      dataIndex: 'avg_response_time',
      key: 'avg_response_time',
      sorter: (a, b) => a.avg_response_time - b.avg_response_time,
      render: (time: number) => (
        <Space>
          <ClockCircleOutlined />
          <Text>{time}ms</Text>
        </Space>
      ),
    },
  ];

  // 计算活跃率
  const activeRate = statistics.total_endpoints > 0 
    ? (statistics.active_endpoints / statistics.total_endpoints) * 100 
    : 0;

  // 计算废弃率
  const deprecatedRate = statistics.total_endpoints > 0 
    ? (statistics.deprecated_endpoints / statistics.total_endpoints) * 100 
    : 0;

  return (
    <div>
      {/* 总体统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总端点数"
              value={statistics.total_endpoints}
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃端点"
              value={statistics.active_endpoints}
              suffix={`/ ${statistics.total_endpoints}`}
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <Progress 
              percent={activeRate} 
              size="small" 
              status="active"
              style={{ marginTop: 8 }}
              showInfo={false}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="今日调用"
              value={statistics.calls_today}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">
                <RiseOutlined style={{ color: '#52c41a', marginRight: 4 }} />
                总调用: {statistics.total_calls.toLocaleString()}
              </Text>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均响应时间"
              value={statistics.avg_response_time}
              suffix="ms"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ 
                color: statistics.avg_response_time > 500 ? '#ff4d4f' : '#52c41a' 
              }}
            />
            <div style={{ marginTop: 8 }}>
              <Progress 
                percent={Math.min((statistics.avg_response_time / 1000) * 100, 100)}
                size="small"
                status={statistics.avg_response_time > 500 ? 'exception' : 'success'}
                showInfo={false}
              />
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* HTTP方法分布 */}
        <Col span={12}>
          <Card 
            title={
              <Space>
                <BarChartOutlined />
                HTTP方法分布
              </Space>
            }
            size="small"
          >
            <div style={{ minHeight: 200 }}>
              {Object.entries(statistics.method_breakdown).map(([method, count]) => (
                <div key={method} style={{ marginBottom: 12 }}>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: 4
                  }}>
                    <Space>
                      <Tag color={methodColors[method as HTTPMethod]}>{method}</Tag>
                      <Text>{count}</Text>
                    </Space>
                    <Text type="secondary">
                      {statistics.total_endpoints > 0 
                        ? ((count / statistics.total_endpoints) * 100).toFixed(1)
                        : 0}%
                    </Text>
                  </div>
                  <Progress 
                    percent={statistics.total_endpoints > 0 
                      ? (count / statistics.total_endpoints) * 100 
                      : 0} 
                    size="small"
                    showInfo={false}
                    strokeColor={
                      method === 'GET' ? '#52c41a' :
                      method === 'POST' ? '#1890ff' :
                      method === 'PUT' ? '#fa8c16' :
                      method === 'DELETE' ? '#ff4d4f' :
                      '#722ed1'
                    }
                  />
                </div>
              ))}
            </div>
          </Card>
        </Col>

        {/* 服务类型分布 */}
        <Col span={12}>
          <Card 
            title={
              <Space>
                <CloudServerOutlined />
                服务类型分布
              </Space>
            }
            size="small"
          >
            <div style={{ minHeight: 200 }}>
              {Object.entries(statistics.service_type_breakdown).map(([type, count]) => (
                <div key={type} style={{ marginBottom: 16 }}>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: 8
                  }}>
                    <Space>
                      <Tag color="blue">{serviceTypeNames[type as ServiceType]}</Tag>
                      <Text strong>{count}</Text>
                    </Space>
                    <Text type="secondary">
                      {statistics.total_endpoints > 0 
                        ? ((count / statistics.total_endpoints) * 100).toFixed(1)
                        : 0}%
                    </Text>
                  </div>
                  <Progress 
                    percent={statistics.total_endpoints > 0 
                      ? (count / statistics.total_endpoints) * 100 
                      : 0}
                    size="small"
                    showInfo={false}
                    strokeColor="#1890ff"
                  />
                </div>
              ))}
              
              <Divider />
              
              {/* 状态统计 */}
              <div style={{ marginTop: 16 }}>
                <Title level={5}>状态分布</Title>
                <div style={{ marginBottom: 12 }}>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: 4
                  }}>
                    <Space>
                      <Tag color="green">活跃</Tag>
                      <Text>{statistics.active_endpoints}</Text>
                    </Space>
                    <Text type="secondary">{activeRate.toFixed(1)}%</Text>
                  </div>
                  <Progress 
                    percent={activeRate}
                    size="small"
                    showInfo={false}
                    strokeColor="#52c41a"
                  />
                </div>
                
                <div>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: 4
                  }}>
                    <Space>
                      <Tag color="red">已废弃</Tag>
                      <Text>{statistics.deprecated_endpoints}</Text>
                    </Space>
                    <Text type="secondary">{deprecatedRate.toFixed(1)}%</Text>
                  </div>
                  <Progress 
                    percent={deprecatedRate}
                    size="small"
                    showInfo={false}
                    strokeColor="#ff4d4f"
                  />
                </div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 热门端点排行 */}
      {statistics.top_endpoints.length > 0 && (
        <Card 
          title={
            <Space>
              <TrophyOutlined />
              热门端点排行
            </Space>
          }
          style={{ marginTop: 16 }}
          size="small"
        >
          <Table
            columns={topEndpointsColumns}
            dataSource={statistics.top_endpoints}
            rowKey="id"
            pagination={false}
            size="small"
          />
        </Card>
      )}
    </div>
  );
};
