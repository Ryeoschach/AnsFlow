import React from 'react'
import { Form, Input, Select, Switch, Space, Button, Divider, Card, Typography, Tag, InputNumber, Radio } from 'antd'
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
  const form = Form.useFormInstance()
  
  const renderK8sDeployConfig = () => {
    // 获取当前的部署类型
    const deployType = form.getFieldValue(['k8s_config', 'deploy_type']) || 'manifest'
    
    return (
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
          label="部署方式"
          name={['k8s_config', 'deploy_type']}
          initialValue="manifest"
          tooltip="选择使用原生 YAML 清单还是 Helm Chart 进行部署"
        >
          <Radio.Group>
            <Radio value="manifest">原生 YAML 清单</Radio>
            <Radio value="helm">Helm Chart</Radio>
          </Radio.Group>
        </Form.Item>
        
        {deployType === 'manifest' && (
          <>
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
          </>
        )}
        
        {deployType === 'helm' && (
          <>
            <Form.Item
              label="Chart 名称"
              name={['k8s_config', 'chart_name']}
              rules={[{ required: true, message: '请输入 Chart 名称' }]}
              tooltip="Helm Chart 的名称，支持变量替换"
            >
              <Input placeholder="例如: nginx, my-app" />
            </Form.Item>
            
            <Form.Item
              label="Chart 仓库"
              name={['k8s_config', 'chart_repo']}
              tooltip="Helm Chart 仓库 URL，留空则使用本地或默认仓库"
            >
              <Input placeholder="例如: https://charts.bitnami.com/bitnami" />
            </Form.Item>
            
            <Form.Item
              label="Chart 版本"
              name={['k8s_config', 'chart_version']}
              tooltip="指定 Chart 版本，留空则使用最新版本"
            >
              <Input placeholder="例如: 1.2.3" />
            </Form.Item>
            
            <Form.Item
              label="Release 名称"
              name={['k8s_config', 'release_name']}
              rules={[{ required: true, message: '请输入 Release 名称' }]}
              tooltip="Helm Release 的名称，支持变量替换"
            >
              <Input placeholder="例如: my-app-release" />
            </Form.Item>
            
            <Form.Item
              label="Values 文件路径"
              name={['k8s_config', 'values_file']}
              tooltip="自定义 values.yaml 文件路径，支持变量替换"
            >
              <Input placeholder="例如: ./helm/values.yaml" />
            </Form.Item>
            
            <Form.Item
              label="自定义 Values"
              name={['k8s_config', 'custom_values']}
              tooltip="直接输入自定义的 values 内容（YAML 格式）"
            >
              <TextArea 
                rows={8} 
                placeholder="输入自定义 Values（YAML 格式）...&#10;例如:&#10;image:&#10;  tag: v1.2.3&#10;replicas: 3"
                style={{ fontFamily: 'monospace' }}
              />
            </Form.Item>
            
            <Divider orientation="left" plain>部署选项</Divider>
            
            <Form.Item
              name={['k8s_config', 'helm_upgrade']}
              valuePropName="checked"
              initialValue={true}
              tooltip="启用时使用 helm upgrade --install，否则使用 helm install"
            >
              <Switch checkedChildren="升级模式" unCheckedChildren="安装模式" />
            </Form.Item>
            
            <Form.Item
              name={['k8s_config', 'helm_wait']}
              valuePropName="checked"
              initialValue={true}
              tooltip="等待所有资源就绪后返回"
            >
              <Switch checkedChildren="等待就绪" unCheckedChildren="不等待" />
            </Form.Item>
            
            <Form.Item
              name={['k8s_config', 'helm_atomic']}
              valuePropName="checked"
              tooltip="失败时自动回滚到上一个版本"
            >
              <Switch checkedChildren="原子性部署" unCheckedChildren="普通部署" />
            </Form.Item>
            
            <Form.Item
              label="超时时间（秒）"
              name={['k8s_config', 'helm_timeout']}
              tooltip="Helm 操作的超时时间，默认 300 秒"
              initialValue={300}
            >
              <InputNumber 
                min={30} 
                max={3600} 
                placeholder="300"
                style={{ width: '100%' }}
              />
            </Form.Item>
          </>
        )}

        <Form.Item
          name={['k8s_config', 'dry_run']}
          valuePropName="checked"
          tooltip="是否执行干运行（仅验证，不实际部署）"
        >
          <Switch checkedChildren="干运行" unCheckedChildren="实际部署" />
        </Form.Item>
      </Card>
    )
  }

  const renderK8sScaleConfig = () => (
    <Card size="small" title="Kubernetes Scale 配置" style={{ marginBottom: 16 }}>
      <Form.Item
        name="k8s_resource_name"
        label="资源名称"
        rules={[{ required: true, message: '请输入资源名称' }]}
        tooltip="要缩放的 Kubernetes 资源名称"
      >
        <Input placeholder="例如: my-app-deployment" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'resource_type']}
        label="资源类型"
        rules={[{ required: true, message: '请选择资源类型' }]}
        initialValue="deployment"
      >
        <Select>
          <Option value="deployment">Deployment</Option>
          <Option value="replicaset">ReplicaSet</Option>
          <Option value="statefulset">StatefulSet</Option>
        </Select>
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'replicas']}
        label="副本数"
        rules={[{ required: true, message: '请输入副本数' }]}
        tooltip="目标副本数量"
      >
        <InputNumber min={0} max={100} placeholder="3" style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'wait_for_rollout']}
        valuePropName="checked"
        initialValue={true}
        tooltip="是否等待缩放完成"
      >
        <Switch checkedChildren="等待缩放完成" unCheckedChildren="不等待" />
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
        initialValue="deployment"
      >
        <Select>
          <Option value="deployment">Deployment</Option>
          <Option value="service">Service</Option>
          <Option value="configmap">ConfigMap</Option>
          <Option value="secret">Secret</Option>
          <Option value="ingress">Ingress</Option>
          <Option value="pod">Pod</Option>
          <Option value="all">所有相关资源</Option>
        </Select>
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'force_delete']}
        valuePropName="checked"
        tooltip="是否强制删除（立即删除，不等待优雅关闭）"
      >
        <Switch checkedChildren="强制删除" unCheckedChildren="优雅删除" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'ignore_not_found']}
        valuePropName="checked"
        initialValue={true}
        tooltip="如果资源不存在是否忽略错误"
      >
        <Switch checkedChildren="忽略不存在" unCheckedChildren="报错" />
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
        name={['k8s_config', 'resource_type']}
        label="资源类型"
        rules={[{ required: true, message: '请选择资源类型' }]}
        initialValue="deployment"
      >
        <Select>
          <Option value="deployment">Deployment</Option>
          <Option value="pod">Pod</Option>
          <Option value="service">Service</Option>
          <Option value="job">Job</Option>
        </Select>
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'condition']}
        label="等待条件"
        rules={[{ required: true, message: '请选择等待条件' }]}
        initialValue="available"
      >
        <Select>
          <Option value="available">Available</Option>
          <Option value="ready">Ready</Option>
          <Option value="complete">Complete</Option>
          <Option value="delete">Delete</Option>
        </Select>
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'timeout']}
        label="超时时间（秒）"
        tooltip="等待的最长时间"
        initialValue={300}
      >
        <InputNumber min={10} max={3600} placeholder="300" style={{ width: '100%' }} />
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
        name={['k8s_config', 'container']}
        label="容器名称"
        tooltip="指定容器名称（可选，默认使用第一个容器）"
      >
        <Input placeholder="例如: app-container" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'command']}
        label="执行命令"
        rules={[{ required: true, message: '请输入要执行的命令' }]}
        tooltip="要在 Pod 中执行的命令"
      >
        <Input placeholder="例如: ls -la" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'stdin']}
        valuePropName="checked"
        tooltip="是否保持 stdin 开放"
      >
        <Switch checkedChildren="保持 stdin" unCheckedChildren="关闭 stdin" />
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
        tooltip="要查看日志的 Pod 名称"
      >
        <Input placeholder="例如: my-app-pod-12345" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'container']}
        label="容器名称"
        tooltip="指定容器名称（可选，默认使用第一个容器）"
      >
        <Input placeholder="例如: app-container" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'follow']}
        valuePropName="checked"
        tooltip="是否跟踪日志输出"
      >
        <Switch checkedChildren="跟踪日志" unCheckedChildren="一次性获取" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'previous']}
        valuePropName="checked"
        tooltip="是否获取前一个容器的日志"
      >
        <Switch checkedChildren="前一个容器" unCheckedChildren="当前容器" />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'since_seconds']}
        label="时间范围（秒）"
        tooltip="只显示指定时间内的日志"
      >
        <InputNumber min={1} placeholder="600" style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item
        name={['k8s_config', 'tail_lines']}
        label="显示行数"
        tooltip="只显示最后几行日志"
      >
        <InputNumber min={1} placeholder="100" style={{ width: '100%' }} />
      </Form.Item>
    </Card>
  )

  const stepInfo = {
    k8s_deploy: {
      title: 'Kubernetes 部署',
      description: '在 Kubernetes 集群中部署应用',
      icon: <CodeOutlined />,
      color: '#326ce5'
    },
    k8s_scale: {
      title: 'Kubernetes 扩缩容',
      description: '调整 Kubernetes 应用的副本数量',
      icon: <InfoCircleOutlined />,
      color: '#52c41a'
    },
    k8s_delete: {
      title: 'Kubernetes 删除',
      description: '删除 Kubernetes 资源',
      icon: <MinusCircleOutlined />,
      color: '#ff4d4f'
    },
    k8s_wait: {
      title: 'Kubernetes 等待',
      description: '等待 Kubernetes 资源达到指定状态',
      icon: <InfoCircleOutlined />,
      color: '#1890ff'
    },
    k8s_exec: {
      title: 'Kubernetes 执行',
      description: '在 Pod 中执行命令',
      icon: <CodeOutlined />,
      color: '#722ed1'
    },
    k8s_logs: {
      title: 'Kubernetes 日志',
      description: '获取 Pod 的日志输出',
      icon: <InfoCircleOutlined />,
      color: '#fa8c16'
    }
  }

  const renderStepConfig = () => {
    switch (stepType) {
      case 'k8s_deploy':
        return renderK8sDeployConfig()
      case 'k8s_scale':
        return renderK8sScaleConfig()
      case 'k8s_delete':
        return renderK8sDeleteConfig()
      case 'k8s_wait':
        return renderK8sWaitConfig()
      case 'k8s_exec':
        return renderK8sExecConfig()
      case 'k8s_logs':
        return renderK8sLogsConfig()
      default:
        return null
    }
  }

  return (
    <div>
      {/* 步骤类型信息 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space align="center">
          {stepInfo[stepType as keyof typeof stepInfo]?.icon}
          <div>
            <Text strong style={{ color: stepInfo[stepType as keyof typeof stepInfo]?.color }}>
              {stepInfo[stepType as keyof typeof stepInfo]?.title}
            </Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {stepInfo[stepType as keyof typeof stepInfo]?.description}
            </Text>
          </div>
        </Space>
      </Card>

      {/* 集群选择 */}
      <Card size="small" title="集群配置" style={{ marginBottom: 16 }}>
        <Form.Item
          name="k8s_cluster_id"
          label="Kubernetes 集群"
          rules={[{ required: true, message: '请选择 Kubernetes 集群' }]}
          tooltip="选择要操作的 Kubernetes 集群"
        >
          <Select
            placeholder="选择集群"
            onChange={onClusterChange}
            dropdownRender={menu => (
              <>
                {menu}
                <Divider style={{ margin: '8px 0' }} />
                <Space style={{ padding: '0 8px 4px' }}>
                  <Button type="text" icon={<PlusOutlined />} onClick={onCreateCluster}>
                    创建新集群
                  </Button>
                </Space>
              </>
            )}
          >
            {k8sClusters.map(cluster => (
              <Option key={cluster.id} value={cluster.id}>
                <Space>
                  <span>{cluster.name}</span>
                  <Tag color={cluster.status === 'connected' ? 'green' : 'red'}>
                    {cluster.status === 'connected' ? '已连接' : '未连接'}
                  </Tag>
                </Space>
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="k8s_namespace"
          label="命名空间"
          rules={[{ required: true, message: '请选择命名空间' }]}
          tooltip="选择要操作的 Kubernetes 命名空间"
        >
          <Select placeholder="选择命名空间">
            {k8sNamespaces.map(namespace => (
              <Option key={namespace.name} value={namespace.name}>
                <Space>
                  <span>{namespace.name}</span>
                  <Tag>{namespace.status}</Tag>
                </Space>
              </Option>
            ))}
          </Select>
        </Form.Item>
      </Card>

      {/* 步骤特定配置 */}
      {renderStepConfig()}

      {/* 环境变量 */}
      <Card size="small" title="环境变量" style={{ marginBottom: 16 }}>
        <Form.List name={['k8s_config', 'env_vars']}>
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name, ...restField }) => (
                <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                  <Form.Item
                    {...restField}
                    name={[name, 'key']}
                    rules={[{ required: true, message: '请输入变量名' }]}
                  >
                    <Input placeholder="变量名" />
                  </Form.Item>
                  <Form.Item
                    {...restField}
                    name={[name, 'value']}
                    rules={[{ required: true, message: '请输入变量值' }]}
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
