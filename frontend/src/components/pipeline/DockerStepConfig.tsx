import React from 'react'
import { Form, Input, Select, Switch, Space, Button, Divider, Card, Typography, Tag } from 'antd'
import { PlusOutlined, MinusCircleOutlined, InfoCircleOutlined } from '@ant-design/icons'
import { DockerRegistry } from '../../types'

const { Option } = Select
const { TextArea } = Input
const { Text } = Typography

interface DockerStepConfigProps {
  stepType: string
  dockerRegistries: DockerRegistry[]
  onCreateRegistry?: () => void
}

const DockerStepConfig: React.FC<DockerStepConfigProps> = ({
  stepType,
  dockerRegistries,
  onCreateRegistry
}) => {
  const renderDockerBuildConfig = () => (
    <Card size="small" title="Docker Build 配置" style={{ marginBottom: 16 }}>
      <Form.Item
        name="docker_image"
        label="镜像名称"
        rules={[{ required: true, message: '请输入镜像名称' }]}
        tooltip="Docker 镜像的名称，例如: myapp"
      >
        <Input placeholder="例如: myapp" />
      </Form.Item>

      <Form.Item
        name="docker_tag"
        label="镜像标签"
        initialValue="latest"
        tooltip="Docker 镜像的标签，例如: latest, v1.0.0"
      >
        <Input placeholder="例如: latest, v1.0.0" />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'dockerfile_path']}
        label="Dockerfile 路径"
        tooltip="Dockerfile 的相对路径，默认为根目录的 Dockerfile"
      >
        <Input placeholder="例如: ./Dockerfile 或 docker/Dockerfile" />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'context_path']}
        label="构建上下文"
        tooltip="Docker 构建上下文的路径，默认为当前目录"
      >
        <Input placeholder="例如: . 或 ./app" />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'target_stage']}
        label="目标阶段"
        tooltip="多阶段构建的目标阶段名称"
      >
        <Input placeholder="例如: production" />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'platform']}
        label="目标平台"
        tooltip="构建的目标平台，例如: linux/amd64"
      >
        <Select placeholder="选择目标平台" allowClear>
          <Option value="linux/amd64">linux/amd64</Option>
          <Option value="linux/arm64">linux/arm64</Option>
          <Option value="linux/arm/v7">linux/arm/v7</Option>
          <Option value="windows/amd64">windows/amd64</Option>
        </Select>
      </Form.Item>

      <Form.Item
        name={['docker_config', 'no_cache']}
        valuePropName="checked"
        tooltip="是否禁用缓存构建"
      >
        <Switch checkedChildren="禁用缓存" unCheckedChildren="使用缓存" />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'pull']}
        valuePropName="checked"
        tooltip="是否始终拉取基础镜像的最新版本"
      >
        <Switch checkedChildren="总是拉取" unCheckedChildren="使用本地" />
      </Form.Item>

      <Divider orientation="left">构建参数</Divider>
      
      <Form.List name={['docker_config', 'build_args']}>
        {(fields, { add, remove }) => (
          <>
            {fields.map(({ key, name, ...restField }) => (
              <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                <Form.Item
                  {...restField}
                  name={[name, 'key']}
                  rules={[{ required: true, message: '请输入参数名' }]}
                  style={{ marginBottom: 0 }}
                >
                  <Input placeholder="参数名" />
                </Form.Item>
                <Form.Item
                  {...restField}
                  name={[name, 'value']}
                  rules={[{ required: true, message: '请输入参数值' }]}
                  style={{ marginBottom: 0 }}
                >
                  <Input placeholder="参数值" />
                </Form.Item>
                <MinusCircleOutlined onClick={() => remove(name)} />
              </Space>
            ))}
            <Form.Item>
              <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                添加构建参数
              </Button>
            </Form.Item>
          </>
        )}
      </Form.List>

      <Divider orientation="left">镜像标签</Divider>
      
      <Form.List name={['docker_config', 'labels']}>
        {(fields, { add, remove }) => (
          <>
            {fields.map(({ key, name, ...restField }) => (
              <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                <Form.Item
                  {...restField}
                  name={[name, 'key']}
                  rules={[{ required: true, message: '请输入标签名' }]}
                  style={{ marginBottom: 0 }}
                >
                  <Input placeholder="标签名" />
                </Form.Item>
                <Form.Item
                  {...restField}
                  name={[name, 'value']}
                  rules={[{ required: true, message: '请输入标签值' }]}
                  style={{ marginBottom: 0 }}
                >
                  <Input placeholder="标签值" />
                </Form.Item>
                <MinusCircleOutlined onClick={() => remove(name)} />
              </Space>
            ))}
            <Form.Item>
              <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                添加镜像标签
              </Button>
            </Form.Item>
          </>
        )}
      </Form.List>
    </Card>
  )

  const renderDockerRunConfig = () => (
    <Card size="small" title="Docker Run 配置" style={{ marginBottom: 16 }}>
      <Form.Item
        name="docker_image"
        label="镜像名称"
        rules={[{ required: true, message: '请输入镜像名称' }]}
        tooltip="要运行的 Docker 镜像"
      >
        <Input placeholder="例如: nginx:latest" />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'command']}
        label="运行命令"
        tooltip="容器启动时执行的命令"
      >
        <Input placeholder="例如: /bin/bash -c 'echo hello'" />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'ports']}
        label="端口映射"
        tooltip="格式: 主机端口:容器端口，多个端口用逗号分隔"
      >
        <Input placeholder="例如: 8080:80,8443:443" />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'volumes']}
        label="卷挂载"
        tooltip="格式: 主机路径:容器路径，多个挂载用逗号分隔"
      >
        <Input placeholder="例如: /host/data:/container/data" />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'detach']}
        valuePropName="checked"
        tooltip="是否在后台运行容器"
      >
        <Switch checkedChildren="后台运行" unCheckedChildren="前台运行" />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'remove']}
        valuePropName="checked"
        tooltip="是否在容器退出后自动删除"
      >
        <Switch checkedChildren="自动删除" unCheckedChildren="保留容器" />
      </Form.Item>
    </Card>
  )

  const renderDockerPushPullConfig = () => (
    <Card size="small" title={`Docker ${stepType === 'docker_push' ? 'Push' : 'Pull'} 配置`} style={{ marginBottom: 16 }}>
      <Form.Item
        name="docker_image"
        label="镜像名称"
        rules={[{ required: true, message: '请输入镜像名称' }]}
        tooltip={stepType === 'docker_push' ? '要推送的镜像名称' : '要拉取的镜像名称'}
      >
        <Input placeholder="例如: myregistry.com/myapp:latest" />
      </Form.Item>

      <Form.Item
        name="docker_registry"
        label="Docker 注册表"
        tooltip="选择 Docker 注册表进行认证"
      >
        <Select
          placeholder="选择 Docker 注册表"
          allowClear
          dropdownRender={menu => (
            <div>
              {menu}
              {onCreateRegistry && (
                <>
                  <Divider style={{ margin: '4px 0' }} />
                  <div style={{ padding: '4px 8px', cursor: 'pointer' }} onClick={onCreateRegistry}>
                    <PlusOutlined /> 创建新注册表
                  </div>
                </>
              )}
            </div>
          )}
        >
          {dockerRegistries?.map(registry => (
            <Option key={registry.id} value={registry.id}>
              <div style={{ lineHeight: '1.4', padding: '4px 0' }}>
                <div style={{ fontWeight: 500, marginBottom: 2 }}>
                  {registry.name}
                  {registry.is_default && <Tag color="blue" style={{ marginLeft: 8, fontSize: 11 }}>默认</Tag>}
                </div>
                <div style={{ fontSize: 12, color: '#999' }}>
                  {registry.url}
                </div>
              </div>
            </Option>
          ))}
        </Select>
      </Form.Item>

      {stepType === 'docker_push' && (
        <Form.Item
          name={['docker_config', 'all_tags']}
          valuePropName="checked"
          tooltip="是否推送所有标签"
        >
          <Switch checkedChildren="推送所有标签" unCheckedChildren="仅推送指定标签" />
        </Form.Item>
      )}
    </Card>
  )

  const renderStepTypeInfo = () => {
    const stepInfo = {
      docker_build: {
        title: 'Docker Build',
        description: '构建 Docker 镜像',
        icon: '🔨',
        tips: ['支持多阶段构建', '可配置构建参数和标签', '支持不同平台构建']
      },
      docker_run: {
        title: 'Docker Run',
        description: '运行 Docker 容器',
        icon: '🚀',
        tips: ['支持端口映射和卷挂载', '可配置运行命令', '支持前台/后台运行']
      },
      docker_push: {
        title: 'Docker Push',
        description: '推送 Docker 镜像到注册表',
        icon: '📤',
        tips: ['需要配置注册表认证', '支持推送多个标签', '自动处理镜像标签']
      },
      docker_pull: {
        title: 'Docker Pull',
        description: '从注册表拉取 Docker 镜像',
        icon: '📥',
        tips: ['支持私有注册表', '自动验证镜像完整性', '支持多架构镜像']
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
                <Tag key={index} color="blue" style={{ marginBottom: 4 }}>
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
      
      {stepType === 'docker_build' && renderDockerBuildConfig()}
      {stepType === 'docker_run' && renderDockerRunConfig()}
      {(stepType === 'docker_push' || stepType === 'docker_pull') && renderDockerPushPullConfig()}
      
      <Card size="small" title="通用配置">
        <Form.Item
          name="timeout_seconds"
          label="超时时间"
          tooltip="步骤执行的超时时间（秒）"
          initialValue={300}
        >
          <Input type="number" placeholder="300" suffix="秒" />
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

export default DockerStepConfig
