import React, { useState, useEffect } from 'react';
import { Modal, Spin, Tabs, Typography, Alert, Tag, Space, Button } from 'antd';
import { ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import { apiService } from '../services/api';
import type { ExecutionLogsResponse, AnsibleExecutionList } from '../types';

const { TabPane } = Tabs;
const { Text, Paragraph } = Typography;

interface ExecutionLogsModalProps {
  visible: boolean;
  execution: AnsibleExecutionList | null;
  onCancel: () => void;
}

const ExecutionLogsModal: React.FC<ExecutionLogsModalProps> = ({
  visible,
  execution,
  onCancel,
}) => {
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<ExecutionLogsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 获取执行日志
  const fetchLogs = async () => {
    if (!execution) return;
    
    try {
      setLoading(true);
      setError(null);
      const logsData = await apiService.getAnsibleExecutionLogs(execution.id);
      setLogs(logsData);
    } catch (err) {
      setError('获取执行日志失败');
      console.error('获取执行日志失败:', err);
    } finally {
      setLoading(false);
    }
  };

  // 下载日志
  const downloadLogs = () => {
    if (!logs || !execution) return;
    
    const logContent = `
=== Ansible Playbook 执行日志 ===
执行ID: ${logs.execution_id}
Playbook: ${execution.playbook_name}
清单: ${execution.inventory_name}
状态: ${execution.status_display}
开始时间: ${logs.started_at || '未知'}
完成时间: ${logs.completed_at || '未知'}
执行时长: ${logs.duration ? `${logs.duration.toFixed(2)}s` : '未知'}
返回码: ${logs.return_code ?? '未知'}

=== 标准输出 (STDOUT) ===
${logs.stdout || '无输出'}

=== 标准错误 (STDERR) ===
${logs.stderr || '无错误输出'}
    `.trim();

    const blob = new Blob([logContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ansible-execution-${logs.execution_id}-logs.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'green';
      case 'failed': return 'red';
      case 'running': return 'blue';
      case 'pending': return 'orange';
      case 'cancelled': return 'gray';
      default: return 'default';
    }
  };

  // 当模态框显示时加载日志
  useEffect(() => {
    if (visible && execution) {
      fetchLogs();
    }
  }, [visible, execution]);

  // 自动刷新正在运行的执行
  useEffect(() => {
    if (!visible || !execution || execution.status !== 'running') return;

    const interval = setInterval(() => {
      fetchLogs();
    }, 5000); // 每5秒刷新一次

    return () => clearInterval(interval);
  }, [visible, execution]);

  return (
    <Modal
      title={
        <Space>
          <span>执行日志</span>
          {execution && (
            <Tag color={getStatusColor(execution.status)}>
              {execution.status_display}
            </Tag>
          )}
        </Space>
      }
      open={visible}
      onCancel={onCancel}
      width={1000}
      footer={[
        <Button key="refresh" icon={<ReloadOutlined />} onClick={fetchLogs}>
          刷新
        </Button>,
        <Button 
          key="download" 
          icon={<DownloadOutlined />} 
          onClick={downloadLogs}
          disabled={!logs}
        >
          下载日志
        </Button>,
        <Button key="close" onClick={onCancel}>
          关闭
        </Button>,
      ]}
    >
      {loading && (
        <div style={{ textAlign: 'center', padding: '50px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>加载执行日志中...</div>
        </div>
      )}

      {error && (
        <Alert
          type="error"
          message="加载失败"
          description={error}
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {logs && !loading && (
        <div>
          {/* 执行信息概览 */}
          <div style={{ marginBottom: 24, padding: '16px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <Text strong>执行ID:</Text>
                <Text code>{logs.execution_id}</Text>
              </Space>
              <Space>
                <Text strong>Playbook:</Text>
                <Text>{execution?.playbook_name}</Text>
              </Space>
              <Space>
                <Text strong>清单:</Text>
                <Text>{execution?.inventory_name}</Text>
              </Space>
              <Space>
                <Text strong>状态:</Text>
                <Tag color={getStatusColor(logs.status)}>
                  {execution?.status_display}
                </Tag>
              </Space>
              <Space>
                <Text strong>开始时间:</Text>
                <Text>{logs.started_at ? new Date(logs.started_at).toLocaleString() : '未开始'}</Text>
              </Space>
              <Space>
                <Text strong>完成时间:</Text>
                <Text>{logs.completed_at ? new Date(logs.completed_at).toLocaleString() : '未完成'}</Text>
              </Space>
              <Space>
                <Text strong>执行时长:</Text>
                <Text>{logs.duration ? `${logs.duration.toFixed(2)}s` : '未知'}</Text>
              </Space>
              <Space>
                <Text strong>返回码:</Text>
                <Text code style={{ color: logs.return_code === 0 ? 'green' : 'red' }}>
                  {logs.return_code ?? '未知'}
                </Text>
              </Space>
            </Space>
          </div>

          {/* 日志内容 */}
          <Tabs defaultActiveKey="stdout">
            <TabPane tab="标准输出 (STDOUT)" key="stdout">
              <div style={{ 
                backgroundColor: '#1f1f1f', 
                color: '#fff', 
                padding: '16px', 
                borderRadius: '6px',
                maxHeight: '400px',
                overflow: 'auto',
                fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                fontSize: '12px',
                lineHeight: '1.4'
              }}>
                {logs.stdout ? (
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {logs.stdout}
                  </pre>
                ) : (
                  <Text type="secondary">无标准输出</Text>
                )}
              </div>
            </TabPane>

            <TabPane tab="标准错误 (STDERR)" key="stderr">
              <div style={{ 
                backgroundColor: '#1f1f1f', 
                color: '#fff', 
                padding: '16px', 
                borderRadius: '6px',
                maxHeight: '400px',
                overflow: 'auto',
                fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                fontSize: '12px',
                lineHeight: '1.4'
              }}>
                {logs.stderr ? (
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', color: '#ff6b6b' }}>
                    {logs.stderr}
                  </pre>
                ) : (
                  <Text type="secondary">无错误输出</Text>
                )}
              </div>
            </TabPane>
          </Tabs>

          {/* 正在运行提示 */}
          {execution?.status === 'running' && (
            <Alert
              type="info"
              message="执行进行中"
              description="日志将每5秒自动刷新。您也可以手动点击刷新按钮获取最新日志。"
              showIcon
              style={{ marginTop: 16 }}
            />
          )}
        </div>
      )}
    </Modal>
  );
};

export default ExecutionLogsModal;
