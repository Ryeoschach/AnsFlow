import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Progress,
  Select,
  DatePicker,
  Button,
  Space,
  Tooltip,
  Typography,
  Spin,
  Alert
} from 'antd';
import {
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  SyncOutlined,
  ReloadOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined
} from '@ant-design/icons';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  TimeScale
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import 'chartjs-adapter-date-fns';
import { formatDistanceToNow, format, parseISO, subDays, startOfDay, endOfDay } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import apiService from '../services/api';

// 注册 Chart.js 组件
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend,
  TimeScale
);

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Title: AntTitle, Text } = Typography;

interface ExecutionStats {
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  running_executions: number;
  success_rate: number;
  avg_duration: number;
  total_duration: number;
}

interface ExecutionTrend {
  date: string;
  total: number;
  successful: number;
  failed: number;
  success_rate: number;
  avg_duration: number;
}

interface PipelineStats {
  pipeline_id: number;
  pipeline_name: string;
  total_executions: number;
  success_rate: number;
  avg_duration: number;
  last_execution: string;
  status: string;
}

interface RecentExecution {
  id: number;
  pipeline_name: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  duration: number | null;
  triggered_by: string;
}

const Analytics: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<ExecutionStats | null>(null);
  const [trends, setTrends] = useState<ExecutionTrend[]>([]);
  const [pipelineStats, setPipelineStats] = useState<PipelineStats[]>([]);
  const [recentExecutions, setRecentExecutions] = useState<RecentExecution[]>([]);
  const [timeRange, setTimeRange] = useState<string>('7d');
  const [dateRange, setDateRange] = useState<[any, any] | null>(null);

  useEffect(() => {
    loadAnalyticsData();
  }, [timeRange, dateRange]);

  const loadAnalyticsData = async () => {
    setLoading(true);
    try {
      // 模拟数据加载，因为后端API可能还没有实现
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 生成模拟数据
      const mockStats: ExecutionStats = {
        total_executions: 156,
        successful_executions: 132,
        failed_executions: 18,
        running_executions: 6,
        success_rate: 84.6,
        avg_duration: 480, // 8分钟
        total_duration: 74880 // 总时长
      };

      const mockTrends: ExecutionTrend[] = Array.from({ length: 7 }, (_, i) => {
        const date = format(subDays(new Date(), 6 - i), 'yyyy-MM-dd');
        const total = Math.floor(Math.random() * 30) + 10;
        const successful = Math.floor(total * (0.7 + Math.random() * 0.2));
        const failed = total - successful;
        return {
          date,
          total,
          successful,
          failed,
          success_rate: Math.round((successful / total) * 100),
          avg_duration: Math.floor(Math.random() * 600) + 300
        };
      });

      const mockPipelineStats: PipelineStats[] = [
        {
          pipeline_id: 1,
          pipeline_name: '前端构建部署',
          total_executions: 45,
          success_rate: 91.1,
          avg_duration: 420,
          last_execution: new Date().toISOString(),
          status: 'success'
        },
        {
          pipeline_id: 2,
          pipeline_name: '后端API测试',
          total_executions: 38,
          success_rate: 78.9,
          avg_duration: 680,
          last_execution: subDays(new Date(), 1).toISOString(),
          status: 'failed'
        },
        {
          pipeline_id: 3,
          pipeline_name: '数据库迁移',
          total_executions: 12,
          success_rate: 100,
          avg_duration: 180,
          last_execution: subDays(new Date(), 2).toISOString(),
          status: 'success'
        }
      ];

      const mockRecentExecutions: RecentExecution[] = [
        {
          id: 1,
          pipeline_name: '前端构建部署',
          status: 'success',
          started_at: subDays(new Date(), 0.1).toISOString(),
          completed_at: new Date().toISOString(),
          duration: 420,
          triggered_by: 'admin'
        },
        {
          id: 2,
          pipeline_name: '后端API测试',
          status: 'running',
          started_at: subDays(new Date(), 0.2).toISOString(),
          completed_at: null,
          duration: null,
          triggered_by: 'developer'
        }
      ];

      setStats(mockStats);
      setTrends(mockTrends);
      setPipelineStats(mockPipelineStats);
      setRecentExecutions(mockRecentExecutions);
    } catch (error) {
      console.error('Failed to load analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'success';
      case 'running': return 'processing';
      case 'failed': return 'error';
      case 'pending': return 'default';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'success': return '成功';
      case 'running': return '运行中';
      case 'failed': return '失败';
      case 'pending': return '等待中';
      default: return status;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircleOutlined />;
      case 'running': return <SyncOutlined spin />;
      case 'failed': return <ExclamationCircleOutlined />;
      case 'pending': return <ClockCircleOutlined />;
      default: return null;
    }
  };

  // 成功率趋势图配置
  const successRateChartData = {
    labels: trends.map(t => format(parseISO(t.date), 'MM/dd', { locale: zhCN })),
    datasets: [
      {
        label: '成功率 (%)',
        data: trends.map(t => t.success_rate),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  };

  // 执行量趋势图配置
  const executionTrendChartData = {
    labels: trends.map(t => format(parseISO(t.date), 'MM/dd', { locale: zhCN })),
    datasets: [
      {
        label: '成功',
        data: trends.map(t => t.successful),
        backgroundColor: 'rgba(34, 197, 94, 0.8)',
        borderRadius: 4,
      },
      {
        label: '失败',
        data: trends.map(t => t.failed),
        backgroundColor: 'rgba(239, 68, 68, 0.8)',
        borderRadius: 4,
      },
    ],
  };

  // 状态分布饼图配置
  const statusDistributionData = stats ? {
    labels: ['成功', '失败', '运行中'],
    datasets: [
      {
        data: [stats.successful_executions, stats.failed_executions, stats.running_executions],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(59, 130, 246, 0.8)',
        ],
        borderWidth: 2,
        borderColor: '#ffffff',
      },
    ],
  } : null;

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  const successRateOptions = {
    ...chartOptions,
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: function(value: any) {
            return value + '%';
          }
        }
      },
    },
  };

  const pipelineColumns = [
    {
      title: '流水线',
      dataIndex: 'pipeline_name',
      key: 'pipeline_name',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '执行次数',
      dataIndex: 'total_executions',
      key: 'total_executions',
      sorter: (a: PipelineStats, b: PipelineStats) => a.total_executions - b.total_executions,
      render: (count: number) => (
        <Tooltip title="总执行次数">
          <Tag color="blue">{count}</Tag>
        </Tooltip>
      ),
    },
    {
      title: '成功率',
      dataIndex: 'success_rate',
      key: 'success_rate',
      render: (rate: number) => (
        <div style={{ width: 120 }}>
          <Progress 
            percent={rate} 
            size="small" 
            strokeColor={rate >= 80 ? '#52c41a' : rate >= 60 ? '#faad14' : '#ff4d4f'}
            format={percent => `${percent}%`}
          />
        </div>
      ),
      sorter: (a: PipelineStats, b: PipelineStats) => a.success_rate - b.success_rate,
    },
    {
      title: '平均耗时',
      dataIndex: 'avg_duration',
      key: 'avg_duration',
      render: (duration: number) => {
        const minutes = Math.floor(duration / 60);
        const seconds = duration % 60;
        return (
          <Tooltip title={`${duration}秒`}>
            <span>{minutes}分{seconds}秒</span>
          </Tooltip>
        );
      },
      sorter: (a: PipelineStats, b: PipelineStats) => a.avg_duration - b.avg_duration,
    },
    {
      title: '最近执行',
      dataIndex: 'last_execution',
      key: 'last_execution',
      render: (date: string) => (
        <Tooltip title={format(parseISO(date), 'yyyy-MM-dd HH:mm:ss')}>
          {formatDistanceToNow(parseISO(date), { 
            addSuffix: true, 
            locale: zhCN 
          })}
        </Tooltip>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
          {getStatusText(status)}
        </Tag>
      ),
    },
  ];

  const recentExecutionsColumns = [
    {
      title: '流水线',
      dataIndex: 'pipeline_name',
      key: 'pipeline_name',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
          {getStatusText(status)}
        </Tag>
      ),
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (date: string) => format(parseISO(date), 'MM-dd HH:mm'),
    },
    {
      title: '耗时',
      dataIndex: 'duration',
      key: 'duration',
      render: (duration: number | null) => 
        duration ? `${Math.floor(duration / 60)}分${duration % 60}秒` : '运行中',
    },
    {
      title: '触发者',
      dataIndex: 'triggered_by',
      key: 'triggered_by',
      render: (user: string) => <Tag>{user}</Tag>,
    },
  ];

  // 计算趋势指标
  const getTrendIndicator = (current: number, previous: number) => {
    if (previous === 0) return { trend: 'neutral', percentage: 0 };
    const percentage = ((current - previous) / previous) * 100;
    const trend = percentage > 0 ? 'up' : percentage < 0 ? 'down' : 'neutral';
    return { trend, percentage: Math.abs(percentage) };
  };

  const currentSuccessRate = trends.length > 0 ? trends[trends.length - 1].success_rate : 0;
  const previousSuccessRate = trends.length > 1 ? trends[trends.length - 2].success_rate : 0;
  const successRateTrend = getTrendIndicator(currentSuccessRate, previousSuccessRate);

  const currentTotal = trends.length > 0 ? trends[trends.length - 1].total : 0;
  const previousTotal = trends.length > 1 ? trends[trends.length - 2].total : 0;
  const executionTrend = getTrendIndicator(currentTotal, previousTotal);

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <AntTitle level={2} style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
              <BarChartOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              数据分析仪表板
            </AntTitle>
            <Text type="secondary">流水线执行数据分析与性能监控</Text>
          </Col>
          <Col>
            <Space>
              <Select
                value={timeRange}
                onChange={setTimeRange}
                style={{ width: 120 }}
              >
                <Option value="1d">最近1天</Option>
                <Option value="7d">最近7天</Option>
                <Option value="30d">最近30天</Option>
                <Option value="90d">最近90天</Option>
                <Option value="custom">自定义</Option>
              </Select>
              
              {timeRange === 'custom' && (
                <RangePicker
                  value={dateRange}
                  onChange={setDateRange}
                  style={{ width: 240 }}
                />
              )}
              
              <Button 
                type="primary" 
                icon={<ReloadOutlined />}
                onClick={loadAnalyticsData}
                loading={loading}
              >
                刷新数据
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 100 }}>
          <Spin size="large" />
        </div>
      ) : (
        <>
          {/* 核心指标卡片 */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="总执行次数"
                  value={stats?.total_executions || 0}
                  prefix={<BarChartOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                  suffix={
                    executionTrend.trend !== 'neutral' && (
                      <span style={{ fontSize: 12, color: executionTrend.trend === 'up' ? '#3f8600' : '#cf1322' }}>
                        {executionTrend.trend === 'up' ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                        {executionTrend.percentage.toFixed(1)}%
                      </span>
                    )
                  }
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="成功率"
                  value={stats?.success_rate || 0}
                  precision={1}
                  suffix="%"
                  prefix={<TrophyOutlined />}
                  valueStyle={{ 
                    color: (stats?.success_rate || 0) >= 80 ? '#3f8600' : 
                           (stats?.success_rate || 0) >= 60 ? '#faad14' : '#cf1322'
                  }}
                />
                {successRateTrend.trend !== 'neutral' && (
                  <div style={{ 
                    fontSize: 12, 
                    color: successRateTrend.trend === 'up' ? '#3f8600' : '#cf1322',
                    marginTop: 4
                  }}>
                    {successRateTrend.trend === 'up' ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                    {successRateTrend.percentage.toFixed(1)}% vs 昨日
                  </div>
                )}
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="平均耗时"
                  value={stats?.avg_duration ? Math.floor(stats.avg_duration / 60) : 0}
                  suffix="分钟"
                  prefix={<ClockCircleOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
                <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                  总耗时: {stats?.total_duration ? Math.floor(stats.total_duration / 3600) : 0}小时
                </div>
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="运行中"
                  value={stats?.running_executions || 0}
                  prefix={<SyncOutlined />}
                  valueStyle={{ color: '#fa8c16' }}
                />
                <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                  失败: {stats?.failed_executions || 0} 次
                </div>
              </Card>
            </Col>
          </Row>

          {/* 图表区域 */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} lg={16}>
              <Card 
                title={
                  <span>
                    <LineChartOutlined style={{ marginRight: 8 }} />
                    执行趋势分析
                  </span>
                } 
                extra={<Text type="secondary">最近7天执行情况</Text>}
              >
                {trends.length > 0 ? (
                  <Bar data={executionTrendChartData} options={chartOptions} height={80} />
                ) : (
                  <div style={{ textAlign: 'center', padding: 60 }}>
                    <BarChartOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
                    <div style={{ marginTop: 16 }}>
                      <Text type="secondary">暂无执行数据</Text>
                    </div>
                  </div>
                )}
              </Card>
            </Col>
            <Col xs={24} lg={8}>
              <Card 
                title={
                  <span>
                    <PieChartOutlined style={{ marginRight: 8 }} />
                    状态分布
                  </span>
                }
                extra={<Text type="secondary">执行状态占比</Text>}
              >
                {statusDistributionData ? (
                  <Doughnut 
                    data={statusDistributionData} 
                    options={{
                      responsive: true,
                      plugins: {
                        legend: {
                          position: 'bottom' as const,
                        },
                      },
                    }}
                    height={200}
                  />
                ) : (
                  <div style={{ textAlign: 'center', padding: 60 }}>
                    <PieChartOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
                    <div style={{ marginTop: 16 }}>
                      <Text type="secondary">暂无状态数据</Text>
                    </div>
                  </div>
                )}
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col span={24}>
              <Card 
                title={
                  <span>
                    <LineChartOutlined style={{ marginRight: 8 }} />
                    成功率趋势
                  </span>
                }
                extra={<Text type="secondary">质量趋势监控</Text>}
              >
                {trends.length > 0 ? (
                  <Line data={successRateChartData} options={successRateOptions} height={60} />
                ) : (
                  <div style={{ textAlign: 'center', padding: 40 }}>
                    <LineChartOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
                    <div style={{ marginTop: 16 }}>
                      <Text type="secondary">暂无趋势数据</Text>
                    </div>
                  </div>
                )}
              </Card>
            </Col>
          </Row>

          {/* 数据表格区域 */}
          <Row gutter={[16, 16]}>
            <Col xs={24} xl={14}>
              <Card title={
                <span>
                  <BarChartOutlined style={{ marginRight: 8 }} />
                  流水线性能统计
                </span>
              }>
                <Table
                  columns={pipelineColumns}
                  dataSource={pipelineStats}
                  rowKey="pipeline_id"
                  size="small"
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: false,
                    showQuickJumper: true,
                    showTotal: (total) => `共 ${total} 条记录`,
                  }}
                  loading={loading}
                />
              </Card>
            </Col>
            <Col xs={24} xl={10}>
              <Card title={
                <span>
                  <ClockCircleOutlined style={{ marginRight: 8 }} />
                  最近执行记录
                </span>
              }>
                <Table
                  columns={recentExecutionsColumns}
                  dataSource={recentExecutions}
                  rowKey="id"
                  size="small"
                  pagination={false}
                  loading={loading}
                />
                {recentExecutions.length === 0 && !loading && (
                  <div style={{ textAlign: 'center', padding: 40 }}>
                    <ClockCircleOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
                    <div style={{ marginTop: 16 }}>
                      <Text type="secondary">暂无最近执行记录</Text>
                    </div>
                  </div>
                )}
              </Card>
            </Col>
          </Row>

          {/* 提示信息 */}
          <Row style={{ marginTop: 24 }}>
            <Col span={24}>
              <Alert
                message="数据说明"
                description="当前显示的是模拟数据，实际部署时将连接真实的执行数据。图表会根据选择的时间范围动态更新，支持实时监控和历史分析。"
                type="info"
                showIcon
                closable
              />
            </Col>
          </Row>
        </>
      )}
    </div>
  );
};

export default Analytics;
