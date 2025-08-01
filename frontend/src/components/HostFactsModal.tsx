import React from 'react';
import { 
  Modal, 
  Descriptions, 
  Tabs, 
  Tag, 
  Typography, 
  Card, 
  Row, 
  Col,
  Statistic,
  Table,
  Empty
} from 'antd';
import {
  DesktopOutlined,
  HddOutlined,
  DatabaseOutlined,
  GlobalOutlined,
  SettingOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import type { AnsibleHost } from '../types';

const { TabPane } = Tabs;
const { Text, Title } = Typography;

interface HostFactsModalProps {
  visible: boolean;
  host: AnsibleHost | null;
  onCancel: () => void;
}

const HostFactsModal: React.FC<HostFactsModalProps> = ({
  visible,
  host,
  onCancel
}) => {
  if (!host || !host.ansible_facts || Object.keys(host.ansible_facts).length === 0) {
    return (
      <Modal
        title="主机 Facts 详情"
        open={visible}
        onCancel={onCancel}
        footer={null}
        width={800}
      >
        <Empty 
          description="暂无 Facts 数据，请先收集主机信息"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Modal>
    );
  }

  const facts = host.ansible_facts;

  // 系统信息
  const getSystemInfo = () => ({
    hostname: facts.ansible_hostname || facts.ansible_fqdn || '未知',
    architecture: facts.ansible_architecture || '未知',
    system: facts.ansible_system || '未知',
    kernel: facts.ansible_kernel || '未知',
    distribution: facts.ansible_distribution || '未知',
    distribution_version: facts.ansible_distribution_version || '未知',
    machine: facts.ansible_machine || '未知',
    product_name: facts.ansible_product_name || '未知',
    virtualization_type: facts.ansible_virtualization_type || '未知'
  });

  // 内存信息
  const getMemoryInfo = () => ({
    total: facts.ansible_memtotal_mb ? `${facts.ansible_memtotal_mb} MB` : '未知',
    free: facts.ansible_memfree_mb ? `${facts.ansible_memfree_mb} MB` : '未知',
    used: facts.ansible_memtotal_mb && facts.ansible_memfree_mb 
      ? `${facts.ansible_memtotal_mb - facts.ansible_memfree_mb} MB` 
      : '未知',
    swap_total: facts.ansible_swaptotal_mb ? `${facts.ansible_swaptotal_mb} MB` : '0 MB',
    swap_free: facts.ansible_swapfree_mb ? `${facts.ansible_swapfree_mb} MB` : '0 MB'
  });

  // CPU信息
  const getCpuInfo = () => ({
    processor_count: facts.ansible_processor_count || '未知',
    processor_cores: facts.ansible_processor_cores || '未知',
    processor_threads_per_core: facts.ansible_processor_threads_per_core || '未知',
    processor_vcpus: facts.ansible_processor_vcpus || '未知',
    processors: facts.ansible_processor || []
  });

  // 网络接口信息
  const getNetworkInterfaces = () => {
    const interfaces = facts.ansible_interfaces || [];
    return interfaces.map((interfaceName: string) => {
      const interfaceData = facts[`ansible_${interfaceName}`];
      if (!interfaceData) return null;

      return {
        name: interfaceName,
        active: interfaceData.active || false,
        type: interfaceData.type || '未知',
        macaddress: interfaceData.macaddress || '未知',
        mtu: interfaceData.mtu || '未知',
        ipv4: interfaceData.ipv4 ? {
          address: interfaceData.ipv4.address,
          netmask: interfaceData.ipv4.netmask,
          network: interfaceData.ipv4.network
        } : null,
        ipv6: interfaceData.ipv6 || []
      };
    }).filter(Boolean);
  };

  // 磁盘设备信息
  const getDiskDevices = () => {
    const devices = facts.ansible_devices || {};
    return Object.entries(devices).map(([name, device]: [string, any]) => ({
      name,
      model: device.model || '未知',
      size: device.size || '未知',
      type: device.rotational === '0' ? 'SSD' : device.rotational === '1' ? 'HDD' : '未知',
      vendor: device.vendor || '未知',
      removable: device.removable === '1' ? '是' : '否'
    }));
  };

  // 挂载点信息
  const getMounts = () => {
    const mounts = facts.ansible_mounts || [];
    return mounts.map((mount: any) => ({
      device: mount.device,
      mount: mount.mount,
      fstype: mount.fstype,
      size_total: mount.size_total ? `${(mount.size_total / 1024 / 1024 / 1024).toFixed(2)} GB` : '未知',
      size_available: mount.size_available ? `${(mount.size_available / 1024 / 1024 / 1024).toFixed(2)} GB` : '未知',
      options: mount.options
    }));
  };

  const systemInfo = getSystemInfo();
  const memoryInfo = getMemoryInfo();
  const cpuInfo = getCpuInfo();
  const networkInterfaces = getNetworkInterfaces();
  const diskDevices = getDiskDevices();
  const mounts = getMounts();

  // 网络接口表格列
  const interfaceColumns = [
    { title: '接口名称', dataIndex: 'name', key: 'name' },
    { 
      title: '状态', 
      dataIndex: 'active', 
      key: 'active',
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? '活跃' : '非活跃'}
        </Tag>
      )
    },
    { title: '类型', dataIndex: 'type', key: 'type' },
    { title: 'MAC地址', dataIndex: 'macaddress', key: 'macaddress' },
    { title: 'MTU', dataIndex: 'mtu', key: 'mtu' },
    { 
      title: 'IPv4地址', 
      dataIndex: 'ipv4', 
      key: 'ipv4',
      render: (ipv4: any) => ipv4 ? `${ipv4.address}/${ipv4.netmask}` : '-'
    }
  ];

  // 磁盘设备表格列
  const diskColumns = [
    { title: '设备名称', dataIndex: 'name', key: 'name' },
    { title: '型号', dataIndex: 'model', key: 'model' },
    { title: '大小', dataIndex: 'size', key: 'size' },
    { title: '类型', dataIndex: 'type', key: 'type' },
    { title: '厂商', dataIndex: 'vendor', key: 'vendor' },
    { title: '可移动', dataIndex: 'removable', key: 'removable' }
  ];

  // 挂载点表格列
  const mountColumns = [
    { title: '设备', dataIndex: 'device', key: 'device' },
    { title: '挂载点', dataIndex: 'mount', key: 'mount' },
    { title: '文件系统', dataIndex: 'fstype', key: 'fstype' },
    { title: '总大小', dataIndex: 'size_total', key: 'size_total' },
    { title: '可用空间', dataIndex: 'size_available', key: 'size_available' }
  ];

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <DesktopOutlined style={{ marginRight: 8 }} />
          主机 Facts 详情 - {host.hostname} ({host.ip_address})
        </div>
      }
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={1200}
      style={{ top: 20 }}
    >
      <Tabs defaultActiveKey="system">
        <TabPane tab={
          <span>
            <InfoCircleOutlined />
            系统信息
          </span>
        } key="system">
          <Card>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="主机名">{systemInfo.hostname}</Descriptions.Item>
              <Descriptions.Item label="架构">{systemInfo.architecture}</Descriptions.Item>
              <Descriptions.Item label="操作系统">{systemInfo.system}</Descriptions.Item>
              <Descriptions.Item label="内核版本">{systemInfo.kernel}</Descriptions.Item>
              <Descriptions.Item label="发行版">{systemInfo.distribution}</Descriptions.Item>
              <Descriptions.Item label="发行版版本">{systemInfo.distribution_version}</Descriptions.Item>
              <Descriptions.Item label="机器类型">{systemInfo.machine}</Descriptions.Item>
              <Descriptions.Item label="产品名称">{systemInfo.product_name}</Descriptions.Item>
              <Descriptions.Item label="虚拟化类型" span={2}>
                <Tag color={systemInfo.virtualization_type !== '未知' ? 'blue' : 'default'}>
                  {systemInfo.virtualization_type}
                </Tag>
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </TabPane>

        <TabPane tab={
          <span>
            <DatabaseOutlined />
            内存信息
          </span>
        } key="memory">
          <Row gutter={16}>
            <Col span={8}>
              <Card>
                <Statistic
                  title="总内存"
                  value={memoryInfo.total}
                  prefix={<DatabaseOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="空闲内存"
                  value={memoryInfo.free}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="已用内存"
                  value={memoryInfo.used}
                  valueStyle={{ color: '#cf1322' }}
                />
              </Card>
            </Col>
          </Row>
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={12}>
              <Card title="交换分区">
                <Descriptions size="small">
                  <Descriptions.Item label="总大小">{memoryInfo.swap_total}</Descriptions.Item>
                  <Descriptions.Item label="空闲大小">{memoryInfo.swap_free}</Descriptions.Item>
                </Descriptions>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab={
          <span>
            <SettingOutlined />
            CPU信息
          </span>
        } key="cpu">
          <Row gutter={16}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="CPU数量"
                  value={cpuInfo.processor_count}
                  prefix={<SettingOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="核心数"
                  value={cpuInfo.processor_cores}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="每核心线程数"
                  value={cpuInfo.processor_threads_per_core}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="虚拟CPU数"
                  value={cpuInfo.processor_vcpus}
                />
              </Card>
            </Col>
          </Row>
          {cpuInfo.processors && cpuInfo.processors.length > 0 && (
            <Card title="处理器详情" style={{ marginTop: 16 }}>
              {cpuInfo.processors.map((processor: any, index: number) => (
                <Text key={index} code style={{ display: 'block', marginBottom: 4 }}>
                  CPU {index}: {typeof processor === 'string' ? processor : JSON.stringify(processor)}
                </Text>
              ))}
            </Card>
          )}
        </TabPane>

        <TabPane tab={
          <span>
            <GlobalOutlined />
            网络接口
          </span>
        } key="network">
          <Table
            columns={interfaceColumns}
            dataSource={networkInterfaces}
            rowKey="name"
            pagination={false}
            size="small"
          />
        </TabPane>

        <TabPane tab={
          <span>
            <HddOutlined />
            存储设备
          </span>
        } key="storage">
          <Tabs type="card">
            <TabPane tab="磁盘设备" key="disks">
              <Table
                columns={diskColumns}
                dataSource={diskDevices}
                rowKey="name"
                pagination={false}
                size="small"
              />
            </TabPane>
            <TabPane tab="挂载点" key="mounts">
              <Table
                columns={mountColumns}
                dataSource={mounts}
                rowKey="mount"
                pagination={false}
                size="small"
              />
            </TabPane>
          </Tabs>
        </TabPane>

        <TabPane tab="原始数据" key="raw">
          <Card>
            <pre style={{ 
              maxHeight: '600px', 
              overflow: 'auto', 
              background: '#f5f5f5', 
              padding: '16px',
              borderRadius: '4px',
              fontSize: '12px'
            }}>
              {JSON.stringify(facts, null, 2)}
            </pre>
          </Card>
        </TabPane>
      </Tabs>
    </Modal>
  );
};

export default HostFactsModal;
