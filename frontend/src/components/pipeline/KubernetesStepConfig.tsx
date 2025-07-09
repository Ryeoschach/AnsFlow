import React from 'react'
import { Form, Input, Select, Switch, Space, Button, Divider, Card, Typography, Tag, InputNumber } from 'antd'
import { PlusOutlined, MinusCircleOutlined, InfoCircleOutlined, CodeOutlined } from '@ant-design/icons'
import { KubernetesCluster, KubernetesNamespace } from '../../types'

const { Option } = Select
const { TextArea } = Input
const { Text } = Typography

interface KubernetesStepConfigProps {
  stepType: string
  k8sClusters: KubernetesCluster[]
  k8sNamespaces: KubernetesNamespace[]
  onCreateCluster?: () => void
  onClusterChange?: (clusterId: number) => void
}

const KubernetesStepConfig: React.FC<KubernetesStepConfigProps> = ({
  stepType,
  k8sClusters,
  k8sNamespaces,
  onCreateCluster,
  onClusterChange
}) => {
  const renderK8sDeployConfig = () => (
    <Card size="small" title="Kubernetes Deploy 配置" style={{ marginBottom: 16 }}>
      <Form.Item
        name="k8s_resource_name"
        label="资源名称"
        rules={[{ required: true, message: '请输入资源名称' }]}
        tooltip="Kubernetes 资源的名称，例如: my-app-deployment"
      >
        <Input placeholder="例如: my-app-deployment" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'manifest_path']}
        label="Manifest 文件路径"
        tooltip="Kubernetes YAML 文件的路径"
      >
        <Input placeholder="例如: k8s/deployment.yaml" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'manifest_content']}
        label="Manifest 内容"
        tooltip="直接输入 Kubernetes YAML 内容（优先级高于文件路径）"
      >
        <TextArea
          rows={8}
          placeholder="apiVersion: apps/v1&#10;kind: Deployment&#10;metadata:&#10;  name: my-app"
          style={{ fontFamily: 'monospace' }}
        />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'wait_for_rollout']}
        valuePropName="checked"
        initialValue={true}
        tooltip="是否等待部署完成"
      >
        <Switch checkedChildren="等待部署完成" unCheckedChildren="不等待" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'rollback_on_failure']}
        valuePropName="checked"
        tooltip="失败时是否自动回滚"
      >
        <Switch checkedChildren="失败时回滚" unCheckedChildren="失败不回滚" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'dry_run']}
        valuePropName="checked"
        tooltip="是否执行干运行（仅验证，不实际部署）"
      >
        <Switch checkedChildren="干运行" unCheckedChildren="实际部署" />
      </Form.Item>
    </Card>
  )

  const renderK8sScaleConfig = () => (
    <Card size="small" title="Kubernetes Scale 配置" style={{ marginBottom: 16 }}>
      <Form.Item
        name="k8s_resource_name"
        label="Deployment 名称"
        rules={[{ required: true, message: '请输入 Deployment 名称' }]}
        tooltip="要扩缩容的 Deployment 名称"
      >
        <Input placeholder="例如: my-app-deployment" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'replicas']}
        label="副本数量"
        rules={[{ required: true, message: '请输入副本数量' }]}
        tooltip="目标副本数量"
      >
        <InputNumber min={0} max={100} placeholder="例如: 3" style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'wait_for_rollout']}
        valuePropName="checked"
        initialValue={true}
        tooltip="是否等待扩缩容完成"
      >
        <Switch checkedChildren="等待完成" unCheckedChildren="不等待" />
      </Form.Item>
    </Card>
  )

  const renderK8sDeleteConfig = () => (
    <Card size="small" title="Kubernetes Delete 配置" style={{ marginBottom: 16 }}>
      <Form.Item
        name="k8s_resource_name"
        label="资源名称"
        rules={[{ required: true, message: '请输入资源名称' }]}
        tooltip="要删除的 Kubernetes 资源名称"
      >
        <Input placeholder="例如: my-app-deployment" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'resource_type']}
        label="资源类型"
        rules={[{ required: true, message: '请选择资源类型' }]}
        tooltip="Kubernetes 资源类型"
      >
        <Select placeholder="选择资源类型">
          <Option value="deployment">Deployment</Option>
          <Option value="service">Service</Option>
          <Option value="configmap">ConfigMap</Option>
          <Option value="secret">Secret</Option>
          <Option value="ingress">Ingress</Option>
          <Option value="pod">Pod</Option>
          <Option value="job">Job</Option>
          <Option value="cronjob">CronJob</Option>
        </Select>
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'force']}
        valuePropName="checked"
        tooltip="是否强制删除（忽略优雅终止）"
      >
        <Switch checkedChildren="强制删除" unCheckedChildren="优雅删除" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'grace_period']}
        label="优雅终止时间"
        tooltip="优雅终止的等待时间（秒）"
      >
        <InputNumber min={0} max={3600} placeholder="30" suffix="秒" style={{ width: '100%' }} />
      </Form.Item>
    </Card>
  )

  const renderK8sWaitConfig = () => (
    <Card size="small" title="Kubernetes Wait 配置" style={{ marginBottom: 16 }}>
      <Form.Item
        name="k8s_resource_name"
        label="资源名称"
        rules={[{ required: true, message: '请输入资源名称' }]}
        tooltip="要等待的 Kubernetes 资源名称"
      >
        <Input placeholder="例如: my-app-deployment" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'condition']}
        label="等待条件"
        rules={[{ required: true, message: '请选择等待条件' }]}
        tooltip="等待的条件类型"
      >
        <Select placeholder="选择等待条件">
          <Option value="Available">Available</Option>
          <Option value="Ready">Ready</Option>
          <Option value="Complete">Complete</Option>
          <Option value="Failed">Failed</Option>
          <Option value="Progressing">Progressing</Option>
        </Select>
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'timeout']}
        label="超时时间"
        initialValue={300}
        tooltip="等待的超时时间（秒）"
      >
        <InputNumber min={1} max={3600} suffix="秒" style={{ width: '100%' }} />
      </Form.Item>
    </Card>
  )

  const renderK8sExecConfig = () => (
    <Card size="small" title="Kubernetes Exec 配置" style={{ marginBottom: 16 }}>
      <Form.Item
        name="k8s_resource_name"
        label="Pod 名称"
        rules={[{ required: true, message: '请输入 Pod 名称' }]}
        tooltip="要执行命令的 Pod 名称"
      >
        <Input placeholder="例如: my-app-pod-12345" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'container_name']}
        label="容器名称"
        tooltip="Pod 中的容器名称（如果 Pod 有多个容器）"
      >
        <Input placeholder="例如: my-app-container" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'command']}
        label="执行命令"
        rules={[{ required: true, message: '请输入要执行的命令' }]}
        tooltip="要在容器中执行的命令"
      >
        <Input placeholder="例如: /bin/bash -c 'echo hello'" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'stdin']}
        valuePropName="checked"
        tooltip="是否启用标准输入"
      >
        <Switch checkedChildren="启用 stdin" unCheckedChildren="禁用 stdin" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'tty']}
        valuePropName="checked"
        tooltip="是否分配 TTY"
      >
        <Switch checkedChildren="分配 TTY" unCheckedChildren="不分配 TTY" />
      </Form.Item>
    </Card>
  )

  const renderK8sLogsConfig = () => (
    <Card size="small" title="Kubernetes Logs 配置" style={{ marginBottom: 16 }}>
      <Form.Item
        name="k8s_resource_name"
        label="Pod 名称"
        rules={[{ required: true, message: '请输入 Pod 名称' }]}
        tooltip="要获取日志的 Pod 名称"
      >
        <Input placeholder="例如: my-app-pod-12345" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'container_name']}
        label="容器名称"
        tooltip="Pod 中的容器名称（如果 Pod 有多个容器）"
      >
        <Input placeholder="例如: my-app-container" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'follow']}
        valuePropName="checked"
        tooltip="是否持续跟踪日志"
      >
        <Switch checkedChildren="跟踪日志" unCheckedChildren="获取一次" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'tail_lines']}
        label="日志行数"
        tooltip="获取最近的日志行数"
      >
        <InputNumber min={1} max={10000} placeholder="100" suffix="行" style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'since_seconds']}
        label="时间范围"
        tooltip="获取最近多少秒的日志"
      >
        <InputNumber min={1} max={86400} placeholder="3600" suffix="秒" style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'previous']}
        valuePropName="checked"
        tooltip="是否获取上一个容器实例的日志"
      >
        <Switch checkedChildren="上一个容器" unCheckedChildren="当前容器" />
      </Form.Item>
    </Card>
  )

  const renderStepTypeInfo = () => {
    const stepInfo = {
      k8s_deploy: {
        title: 'Kubernetes Deploy',
        description: '部署应用到 Kubernetes 集群',
        icon: '🚀',
        tips: ['支持 YAML 文件和直接内容', '可等待部署完成', '支持失败回滚']
      },
      k8s_scale: {
        title: 'Kubernetes Scale',
        description: '扩缩容 Kubernetes 部署',
        icon: '📈',
        tips: ['支持 Deployment 扩缩容', '可等待扩缩容完成', '支持零副本部署']
      },
      k8s_delete: {
        title: 'Kubernetes Delete',
        description: '删除 Kubernetes 资源',
        icon: '🗑️',
        tips: ['支持多种资源类型', '可强制删除', '支持优雅终止']
      },
      k8s_wait: {
        title: 'Kubernetes Wait',
        description: '等待 Kubernetes 资源状态',
        icon: '⏳',
        tips: ['支持多种等待条件', '可配置超时时间', '用于状态同步']
      },
      k8s_exec: {
        title: 'Kubernetes Exec',
        description: '在 Pod 中执行命令',
        icon: '💻',
        tips: ['支持多容器 Pod', '可分配 TTY', '支持交互式命令']
      },
      k8s_logs: {
        title: 'Kubernetes Logs',
        description: '获取 Pod 日志',
        icon: '📋',
        tips: ['支持实时跟踪', '可限制日志行数', '支持历史日志']
      }
    }

    const info = stepInfo[stepType as keyof typeof stepInfo]
    if (!info) return null

    return (
      <Card size="small" style={{ marginBottom: 16, backgroundColor: '#f6f8fa' }}>
        <Space>
          <span style={{ fontSize: 20 }}>{info.icon}</span>
          <div>
            <Text strong>{info.title}</Text>
            <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
              {info.description}
            </div>
            <div style={{ marginTop: 8 }}>
              {info.tips.map((tip, index) => (
                <Tag key={index} color="green" style={{ marginBottom: 4 }}>
                  <InfoCircleOutlined style={{ marginRight: 4 }} />
                  {tip}
                </Tag>
              ))}
            </div>
          </div>
        </Space>
      </Card>
    )
  }

  return (
    <div>
      {renderStepTypeInfo()}
      
      {/* Kubernetes 集群和命名空间选择 */}
      <Card size="small" title="集群配置" style={{ marginBottom: 16 }}>
        <Form.Item
          name="k8s_cluster"
          label="Kubernetes 集群"
          rules={[{ required: true, message: '请选择 Kubernetes 集群' }]}
          tooltip="选择要操作的 Kubernetes 集群"
        >
          <Select
            placeholder="选择 Kubernetes 集群"
            onChange={onClusterChange}
            dropdownRender={menu => (
              <div>
                {menu}
                {onCreateCluster && (
                  <>
                    <Divider style={{ margin: '4px 0' }} />
                    <div style={{ padding: '4px 8px', cursor: 'pointer' }} onClick={onCreateCluster}>
                      <PlusOutlined /> 创建新集群
                    </div>
                  </>
                )}
              </div>
            )}
          >
            {k8sClusters?.map(cluster => (
              <Option key={cluster.id} value={cluster.id}>
                <div style={{ lineHeight: '1.4', padding: '4px 0' }}>
                  <div style={{ fontWeight: 500, marginBottom: 2 }}>
                    {cluster.name}
                    {cluster.status === 'connected' && <Tag color="green" style={{ marginLeft: 8, fontSize: 11 }}>已连接</Tag>}
                    {cluster.status === 'disconnected' && <Tag color="orange" style={{ marginLeft: 8, fontSize: 11 }}>未连接</Tag>}
                    {cluster.status === 'error' && <Tag color="red" style={{ marginLeft: 8, fontSize: 11 }}>错误</Tag>}
                  </div>
                  <div style={{ fontSize: 12, color: '#999' }}>
                    {cluster.api_server}
                  </div>
                </div>
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="k8s_namespace"
          label="Kubernetes 命名空间"
          rules={[{ required: true, message: '请输入命名空间' }]}
          tooltip="Kubernetes 命名空间，默认为 default"
        >
          <Select
            placeholder="选择或输入命名空间"
            showSearch
            allowClear
            optionFilterProp="children"
          >
            <Option value="default">default</Option>
            <Option value="kube-system">kube-system</Option>
            <Option value="kube-public">kube-public</Option>
            {k8sNamespaces?.map(ns => (
              <Option key={ns.id} value={ns.name}>
                <div style={{ lineHeight: '1.4', padding: '2px 0' }}>
                  <span style={{ fontWeight: 500 }}>{ns.name}</span>
                  {ns.status === 'active' && <Tag color="green" style={{ marginLeft: 8, fontSize: 11 }}>活跃</Tag>}
                  {ns.status === 'terminating' && <Tag color="orange" style={{ marginLeft: 8, fontSize: 11 }}>终止中</Tag>}
                </div>
              </Option>
            ))}
          </Select>
        </Form.Item>
      </Card>
      
      {/* 根据步骤类型渲染不同的配置界面 */}
      {stepType === 'k8s_deploy' && renderK8sDeployConfig()}
      {stepType === 'k8s_scale' && renderK8sScaleConfig()}
      {stepType === 'k8s_delete' && renderK8sDeleteConfig()}
      {stepType === 'k8s_wait' && renderK8sWaitConfig()}
      {stepType === 'k8s_exec' && renderK8sExecConfig()}
      {stepType === 'k8s_logs' && renderK8sLogsConfig()}
      
      <Card size="small" title="通用配置">
        <Form.Item
          name="timeout_seconds"
          label="超时时间"
          tooltip="步骤执行的超时时间（秒）"
          initialValue={300}
        >
          <InputNumber min={1} max={3600} suffix="秒" style={{ width: '100%' }} />
        </Form.Item>

        <Divider orientation="left">环境变量</Divider>
        
        <Form.List name="environment_vars">
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name, ...restField }) => (
                <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                  <Form.Item
                    {...restField}
                    name={[name, 'key']}
                    rules={[{ required: true, message: '请输入变量名' }]}
                    style={{ marginBottom: 0 }}
                  >
                    <Input placeholder="变量名" />
                  </Form.Item>
                  <Form.Item
                    {...restField}
                    name={[name, 'value']}
                    rules={[{ required: true, message: '请输入变量值' }]}
                    style={{ marginBottom: 0 }}
                  >
                    <Input placeholder="变量值" />
                  </Form.Item>
                  <MinusCircleOutlined onClick={() => remove(name)} />
                </Space>
              ))}
              <Form.Item>
                <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                  添加环境变量
                </Button>
              </Form.Item>
            </>
          )}
        </Form.List>
      </Card>
    </div>
  )
}

export default KubernetesStepConfig
