import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Alert,
  Descriptions,
  Timeline,
  Modal,
  Steps,
  Tabs,
  Typography,
  Space,
  Tag,
  Statistic,
  Progress,
  List,
  Tooltip,
  message,
  Divider
} from 'antd';
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  InfoCircleOutlined,
  ToolOutlined,
  CopyOutlined,
  ReloadOutlined,
  RobotOutlined
} from '@ant-design/icons';
import { KubernetesCluster } from '../../types';
import apiService from '../../services/api';

const { Text, Paragraph, Title } = Typography;
const { TabPane } = Tabs;
const { Step } = Steps;

interface TokenStatus {
  status: 'valid' | 'invalid' | 'no_token' | 'warning';
  status_message?: string;  // 新增：状态说明消息
  token_info: {
    has_expiry: boolean;
    expires_at: string | null;
    is_expired: boolean;
    jwt_shows_expired?: boolean;  // 新增：JWT 解析结果
    connection_valid?: boolean;   // 新增：连接验证结果
    auto_refresh_available: boolean;
    last_validated: string;
    error_message: string;
  };
  connection_info: {
    cluster_version?: string;
    total_nodes?: number;
    ready_nodes?: number;
    connection_time: string;
    message: string;
    error?: string;
  };
  recommendations: string[];
}

interface TokenRenewalStrategy {
  current_status: TokenStatus;
  strategies: {
    immediate_actions: Array<{
      action: string;
      title: string;
      description: string;
      urgency: 'high' | 'medium' | 'low';
      commands?: string[];
      steps?: string[];
    }>;
    long_term_solutions: Array<{
      solution: string;
      title: string;
      description: string;
      benefits: string[];
      implementation: string;
    }>;
    automation_options: Array<{
      option: string;
      title: string;
      description: string;
      features: string[];
    }>;
  };
  priority_actions: Array<{
    priority: number;
    action: string;
    reason: string;
  }>;
}

interface KubernetesTokenManagerProps {
  cluster: KubernetesCluster;
  visible: boolean;
  onClose: () => void;
  onTokenUpdated?: () => void;
}

const KubernetesTokenManager: React.FC<KubernetesTokenManagerProps> = ({
  cluster,
  visible,
  onClose,
  onTokenUpdated
}) => {
  const [loading, setLoading] = useState(false);
  const [tokenStatus, setTokenStatus] = useState<TokenStatus | null>(null);
  const [renewalStrategy, setRenewalStrategy] = useState<TokenRenewalStrategy | null>(null);
  const [activeTab, setActiveTab] = useState('status');
  const [guideVisible, setGuideVisible] = useState(false);

  // 加载 Token 状态
  const loadTokenStatus = async () => {
    setLoading(true);
    try {
      const response = await apiService.getKubernetesClusterTokenStatus(cluster.id);
      setTokenStatus(response);
      
      // 总是加载更新策略，为用户提供完整信息
      const strategyResponse = await apiService.getKubernetesClusterTokenRenewalStrategy(cluster.id);
      setRenewalStrategy(strategyResponse);
    } catch (error: any) {
      console.error('加载 Token 状态失败:', error);
      message.error('加载 Token 状态失败: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 立即验证 Token
  const validateTokenNow = async () => {
    setLoading(true);
    try {
      const response = await apiService.validateKubernetesClusterToken(cluster.id);
      message.success('Token 验证完成');
      await loadTokenStatus();
    } catch (error: any) {
      console.error('Token 验证失败:', error);
      message.error('Token 验证失败: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 复制命令到剪贴板
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      message.success('已复制到剪贴板');
    });
  };

  useEffect(() => {
    if (visible) {
      loadTokenStatus();
    }
  }, [visible, cluster.id]);

  // 渲染状态图标
  const renderStatusIcon = (status: string) => {
    switch (status) {
      case 'valid':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'warning':
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      case 'invalid':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'no_token':
        return <InfoCircleOutlined style={{ color: '#1890ff' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#8c8c8c' }} />;
    }
  };

  // 渲染状态概览
  const renderStatusOverview = () => {
    if (!tokenStatus) return null;

    const getStatusColor = (status: string) => {
      switch (status) {
        case 'valid': return '#52c41a';
        case 'warning': return '#faad14';
        case 'invalid': return '#ff4d4f';
        default: return '#8c8c8c';
      }
    };

    const getStatusText = (status: string) => {
      switch (status) {
        case 'valid': return 'Token 有效';
        case 'warning': return 'JWT 已过期但连接有效';
        case 'invalid': return 'Token 无效';
        case 'no_token': return '未配置 Token';
        default: return '未知状态';
      }
    };

    return (
      <Card size="small" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space direction="vertical" size="small">
            <Space>
              {renderStatusIcon(tokenStatus.status)}
              <Title level={4} style={{ margin: 0, color: getStatusColor(tokenStatus.status) }}>
                {getStatusText(tokenStatus.status)}
              </Title>
            </Space>
            {tokenStatus.status_message && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {tokenStatus.status_message}
              </Text>
            )}
          </Space>
          <Space>
            <Button icon={<ReloadOutlined />} onClick={validateTokenNow} loading={loading}>
              立即验证
            </Button>
            <Button icon={<ToolOutlined />} onClick={() => setGuideVisible(true)}>
              更新指南
            </Button>
          </Space>
        </div>

        {tokenStatus.recommendations.length > 0 && (
          <Alert
            style={{ marginTop: 16 }}
            type={tokenStatus.status === 'valid' ? 'info' : 'warning'}
            message="建议"
            description={
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {tokenStatus.recommendations.map((rec, index) => (
                  <li key={index}>{rec}</li>
                ))}
              </ul>
            }
          />
        )}
      </Card>
    );
  };

  // 渲染 Token 详细信息
  const renderTokenDetails = () => {
    if (!tokenStatus) return null;

    const tokenInfo = tokenStatus.token_info;
    const connectionInfo = tokenStatus.connection_info;

    // 计算剩余时间
    let timeToExpiry = null;
    let expiryPercentage = 0;
    if (tokenInfo.expires_at) {
      const expiryDate = new Date(tokenInfo.expires_at);
      const now = new Date();
      timeToExpiry = expiryDate.getTime() - now.getTime();
      
      // 假设 Token 有效期为 1 年，计算使用百分比
      const oneYear = 365 * 24 * 60 * 60 * 1000;
      expiryPercentage = Math.max(0, Math.min(100, (timeToExpiry / oneYear) * 100));
    }

    return (
      <div>
        <Card title="Token 信息" size="small" style={{ marginBottom: 16 }}>
          <Descriptions column={2} size="small">
            <Descriptions.Item label="过期时间">
              {tokenInfo.has_expiry ? (
                <Space direction="vertical" size="small">
                  <Text>{tokenInfo.expires_at ? new Date(tokenInfo.expires_at).toLocaleString() : '未知'}</Text>
                  {timeToExpiry !== null && (
                    <div>
                      {timeToExpiry > 0 ? (
                        <Text type="success">
                          剩余 {Math.floor(timeToExpiry / (1000 * 60 * 60 * 24))} 天
                        </Text>
                      ) : (
                        <Text type="danger">已过期</Text>
                      )}
                      <Progress
                        percent={expiryPercentage}
                        size="small"
                        status={expiryPercentage < 10 ? 'exception' : expiryPercentage < 30 ? 'normal' : 'success'}
                        style={{ marginTop: 4 }}
                      />
                    </div>
                  )}
                </Space>
              ) : (
                <Tag color="blue">永久有效</Tag>
              )}
            </Descriptions.Item>
            
            <Descriptions.Item label="自动刷新">
              <Tag color={tokenInfo.auto_refresh_available ? 'green' : 'default'}>
                {tokenInfo.auto_refresh_available ? '支持' : '不支持'}
              </Tag>
            </Descriptions.Item>
            
            <Descriptions.Item label="最后验证">
              {new Date(tokenInfo.last_validated).toLocaleString()}
            </Descriptions.Item>
            
            <Descriptions.Item label="状态">
              <Space direction="vertical" size="small">
                <div>
                  <Text strong>实际状态: </Text>
                  <Tag color={tokenInfo.connection_valid ? 'green' : 'red'}>
                    {tokenInfo.connection_valid ? '连接有效' : '连接无效'}
                  </Tag>
                </div>
                {tokenInfo.jwt_shows_expired !== undefined && (
                  <div>
                    <Text strong>JWT 状态: </Text>
                    <Tag color={tokenInfo.jwt_shows_expired ? 'orange' : 'green'}>
                      {tokenInfo.jwt_shows_expired ? 'JWT 显示过期' : 'JWT 未过期'}
                    </Tag>
                  </div>
                )}
                {tokenStatus.status === 'warning' && (
                  <Alert
                    type="warning"
                    message="状态说明"
                    description="JWT 显示 Token 已过期，但实际连接仍然有效。这可能是 Kubernetes Service Account Token 的正常行为。"
                    style={{ marginTop: 4, fontSize: '12px' }}
                  />
                )}
              </Space>
            </Descriptions.Item>
          </Descriptions>

          {tokenInfo.error_message && (
            <Alert
              type="error"
              message="错误信息"
              description={tokenInfo.error_message}
              style={{ marginTop: 16 }}
            />
          )}
        </Card>

        <Card title="连接信息" size="small">
          <Descriptions column={2} size="small">
            <Descriptions.Item label="集群版本">
              {connectionInfo.cluster_version || '未知'}
            </Descriptions.Item>
            
            <Descriptions.Item label="节点状态">
              {connectionInfo.ready_nodes !== undefined && connectionInfo.total_nodes !== undefined ? (
                <span>
                  {connectionInfo.ready_nodes}/{connectionInfo.total_nodes} 就绪
                </span>
              ) : (
                '未知'
              )}
            </Descriptions.Item>
            
            <Descriptions.Item label="连接时间">
              {new Date(connectionInfo.connection_time).toLocaleString()}
            </Descriptions.Item>
            
            <Descriptions.Item label="连接状态">
              <Tag color={connectionInfo.error ? 'red' : 'green'}>
                {connectionInfo.message}
              </Tag>
            </Descriptions.Item>
          </Descriptions>

          {connectionInfo.error && (
            <Alert
              type="error"
              message="连接错误"
              description={connectionInfo.error}
              style={{ marginTop: 16 }}
            />
          )}
        </Card>
      </div>
    );
  };

  // 渲染解决方案
  const renderSolutions = () => {
    if (!renewalStrategy) return null;

    return (
      <div>
        {/* 优先行动 */}
        <Card title="优先行动" size="small" style={{ marginBottom: 16 }}>
          <List
            dataSource={renewalStrategy.priority_actions}
            renderItem={(action) => (
              <List.Item>
                <List.Item.Meta
                  avatar={
                    <div style={{
                      width: 24,
                      height: 24,
                      borderRadius: '50%',
                      backgroundColor: action.priority === 1 ? '#ff4d4f' : action.priority === 2 ? '#faad14' : '#52c41a',
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 12,
                      fontWeight: 'bold'
                    }}>
                      {action.priority}
                    </div>
                  }
                  title={action.action}
                  description={action.reason}
                />
              </List.Item>
            )}
          />
        </Card>

        {/* 立即行动建议 */}
        {renewalStrategy.strategies.immediate_actions.length > 0 && (
          <Card title="立即行动建议" size="small" style={{ marginBottom: 16 }}>
            {renewalStrategy.strategies.immediate_actions.map((action, index) => (
              <Card
                key={index}
                type="inner"
                title={
                  <Space>
                    <Tag color={action.urgency === 'high' ? 'red' : action.urgency === 'medium' ? 'orange' : 'green'}>
                      {action.urgency === 'high' ? '紧急' : action.urgency === 'medium' ? '重要' : '一般'}
                    </Tag>
                    {action.title}
                  </Space>
                }
                style={{ marginBottom: 8 }}
              >
                <Paragraph>{action.description}</Paragraph>
                
                {action.commands && (
                  <div>
                    <Text strong>命令:</Text>
                    {action.commands.map((cmd, cmdIndex) => (
                      <div key={cmdIndex} style={{ marginTop: 4 }}>
                        <Text code style={{ background: '#f6f8fa', padding: '2px 4px' }}>
                          {cmd}
                        </Text>
                        <Tooltip title="复制命令">
                          <Button
                            type="text"
                            size="small"
                            icon={<CopyOutlined />}
                            onClick={() => copyToClipboard(cmd)}
                            style={{ marginLeft: 8 }}
                          />
                        </Tooltip>
                      </div>
                    ))}
                  </div>
                )}
                
                {action.steps && (
                  <div style={{ marginTop: 8 }}>
                    <Text strong>步骤:</Text>
                    <ol style={{ marginTop: 4, marginLeft: 16 }}>
                      {action.steps.map((step, stepIndex) => (
                        <li key={stepIndex}>{step}</li>
                      ))}
                    </ol>
                  </div>
                )}
              </Card>
            ))}
          </Card>
        )}

        {/* 长期解决方案 */}
        <Card title="长期解决方案" size="small">
          {renewalStrategy.strategies.long_term_solutions.map((solution, index) => (
            <Card
              key={index}
              type="inner"
              title={solution.title}
              style={{ marginBottom: 8 }}
            >
              <Paragraph>{solution.description}</Paragraph>
              
              <div style={{ marginBottom: 8 }}>
                <Text strong>优势:</Text>
                <ul style={{ marginTop: 4, marginLeft: 16 }}>
                  {solution.benefits.map((benefit, benefitIndex) => (
                    <li key={benefitIndex}>{benefit}</li>
                  ))}
                </ul>
              </div>
              
              <div>
                <Text strong>实施方法:</Text>
                <Text code style={{ display: 'block', marginTop: 4, padding: 8, background: '#f6f8fa' }}>
                  {solution.implementation}
                </Text>
              </div>
            </Card>
          ))}
        </Card>
      </div>
    );
  };

  // 渲染更新指南
  const renderUpdateGuide = () => {
    const steps = [
      {
        title: '连接到集群',
        content: (
          <div>
            <Paragraph>确保您有管理员权限访问 Kubernetes 集群</Paragraph>
            <div>
              <Text code>kubectl cluster-info</Text>
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={() => copyToClipboard('kubectl cluster-info')}
                style={{ marginLeft: 8 }}
              />
            </div>
          </div>
        )
      },
      {
        title: '创建 Service Account',
        content: (
          <div>
            <Paragraph>为 AnsFlow 创建专用的 Service Account</Paragraph>
            <div style={{ marginBottom: 8 }}>
              <Text code>kubectl create serviceaccount ansflow-sa -n default</Text>
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={() => copyToClipboard('kubectl create serviceaccount ansflow-sa -n default')}
                style={{ marginLeft: 8 }}
              />
            </div>
            <div>
              <Text code>kubectl create clusterrolebinding ansflow-binding --clusterrole=cluster-admin --serviceaccount=default:ansflow-sa</Text>
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={() => copyToClipboard('kubectl create clusterrolebinding ansflow-binding --clusterrole=cluster-admin --serviceaccount=default:ansflow-sa')}
                style={{ marginLeft: 8 }}
              />
            </div>
          </div>
        )
      },
      {
        title: '生成 Token',
        content: (
          <div>
            <Paragraph>生成长期有效的 Token</Paragraph>
            <Tabs size="small">
              <TabPane tab="临时 Token (推荐)" key="temp">
                <div>
                  <Text code>kubectl create token ansflow-sa --duration=8760h</Text>
                  <Button
                    type="text"
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() => copyToClipboard('kubectl create token ansflow-sa --duration=8760h')}
                    style={{ marginLeft: 8 }}
                  />
                </div>
                <Alert
                  type="info"
                  message="此方法生成有时间限制的 Token（1年有效期）"
                  style={{ marginTop: 8 }}
                />
              </TabPane>
              
              <TabPane tab="永久 Token" key="permanent">
                <div style={{ marginBottom: 8 }}>
                  <Paragraph>创建 Secret 获取永久 Token:</Paragraph>
                  <pre style={{ background: '#f6f8fa', padding: 12, borderRadius: 4 }}>
{`kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: ansflow-sa-token
  annotations:
    kubernetes.io/service-account.name: ansflow-sa
type: kubernetes.io/service-account-token
EOF`}
                  </pre>
                </div>
                <div>
                  <Text code>{'kubectl get secret ansflow-sa-token -o jsonpath="{.data.token}" | base64 -d'}</Text>
                  <Button
                    type="text"
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() => copyToClipboard('kubectl get secret ansflow-sa-token -o jsonpath="{.data.token}" | base64 -d')}
                    style={{ marginLeft: 8 }}
                  />
                </div>
              </TabPane>
            </Tabs>
          </div>
        )
      },
      {
        title: '更新 AnsFlow 配置',
        content: (
          <div>
            <ol>
              <li>在编辑集群页面中找到认证配置</li>
              <li>选择 "Token 认证" 方式</li>
              <li>粘贴新生成的 Token</li>
              <li>点击"测试连接"验证新 Token</li>
              <li>确认连接成功后保存配置</li>
            </ol>
          </div>
        )
      },
      {
        title: '验证更新结果',
        content: (
          <div>
            <ul>
              <li>在集群列表中查看状态应为"已连接"</li>
              <li>尝试在流水线中使用 Kubernetes 步骤</li>
              <li>检查集群资源同步是否正常</li>
            </ul>
          </div>
        )
      }
    ];

    return (
      <div>
        <Steps direction="vertical" current={-1}>
          {steps.map((step, index) => (
            <Step
              key={index}
              title={step.title}
              description={step.content}
            />
          ))}
        </Steps>
        
        <Divider />
        
        <Card title="常见问题解决" size="small">
          <List
            dataSource={[
              { issue: 'Token 生成失败', solution: '检查 Service Account 是否存在，确认有足够权限' },
              { issue: '连接测试失败', solution: '检查 API Server 地址、Token 格式、网络连通性' },
              { issue: '权限不足错误', solution: '检查 ClusterRoleBinding，确保 Service Account 有足够权限' }
            ]}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  title={<Text strong>{item.issue}</Text>}
                  description={item.solution}
                />
              </List.Item>
            )}
          />
        </Card>
      </div>
    );
  };

  return (
    <>
      <Modal
        title={
          <Space>
            <ToolOutlined />
            Kubernetes Token 管理 - {cluster.name}
          </Space>
        }
        visible={visible}
        onCancel={onClose}
        footer={[
          <Button key="close" onClick={onClose}>
            关闭
          </Button>
        ]}
        width={1000}
        destroyOnClose
      >
        {renderStatusOverview()}
        
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="状态详情" key="status">
            {renderTokenDetails()}
          </TabPane>
          
          {renewalStrategy && (
            <TabPane tab="解决方案" key="solutions">
              {renderSolutions()}
            </TabPane>
          )}
          
          <TabPane tab="自动化选项" key="automation">
            {renewalStrategy?.strategies?.automation_options && renewalStrategy.strategies.automation_options.length > 0 ? (
              <div>
                {renewalStrategy.strategies.automation_options.map((option, index) => (
                  <Card
                    key={index}
                    title={option.title}
                    size="small"
                    style={{ marginBottom: 16 }}
                  >
                    <Paragraph>{option.description}</Paragraph>
                    <div>
                      <Text strong>功能特性:</Text>
                      <ul style={{ marginTop: 4, marginLeft: 16 }}>
                        {option.features?.map((feature, featureIndex) => (
                          <li key={featureIndex}>{feature}</li>
                        ))}
                      </ul>
                    </div>
                    <Button
                      type="primary"
                      size="small"
                      style={{ marginTop: 8 }}
                      onClick={() => message.info('自动化脚本功能开发中')}
                    >
                      复制自动化脚本
                    </Button>
                  </Card>
                ))}
              </div>
            ) : loading ? (
              <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                <RobotOutlined style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: 16 }} />
                <Title level={4} type="secondary">正在加载自动化选项...</Title>
                <Paragraph type="secondary">
                  系统正在分析 Token 状态并生成个性化的自动化建议，请稍候。
                </Paragraph>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                <RobotOutlined style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: 16 }} />
                <Title level={4} type="secondary">暂无自动化选项</Title>
                <Paragraph type="secondary">
                  当前 Token 状态良好，如需自动化管理建议，请点击下方按钮重新加载。
                </Paragraph>
                <Button 
                  type="primary" 
                  loading={loading}
                  onClick={loadTokenStatus}
                >
                  重新加载策略
                </Button>
              </div>
            )}
          </TabPane>
        </Tabs>
      </Modal>

      {/* 更新指南 Modal */}
      <Modal
        title="Token 更新指南"
        visible={guideVisible}
        onCancel={() => setGuideVisible(false)}
        footer={[
          <Button key="close" onClick={() => setGuideVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {renderUpdateGuide()}
      </Modal>
    </>
  );
};

export default KubernetesTokenManager;
