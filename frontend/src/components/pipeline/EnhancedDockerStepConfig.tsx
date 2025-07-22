import React, { useEffect, useState } from 'react'
import { 
  Form, 
  Input, 
  Select, 
  Switch, 
  Space, 
  Button, 
  Divider, 
  Card, 
  Typography, 
  Tag, 
  Alert,
  Tooltip,
  AutoComplete,
  Modal,
  message
} from 'antd'
import { 
  PlusOutlined, 
  MinusCircleOutlined, 
  InfoCircleOutlined,
  LinkOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ExperimentOutlined
} from '@ant-design/icons'
import { DockerRegistry } from '../../types/docker'
import useDockerStepConfig from '../../hooks/useDockerStepConfig'

const { Option } = Select
const { TextArea } = Input
const { Text } = Typography

interface EnhancedDockerStepConfigProps {
  stepType: string
  onRegistryChange?: (registryId: number) => void
  form?: any
  initialValues?: any
}

const EnhancedDockerStepConfig: React.FC<EnhancedDockerStepConfigProps> = ({
  stepType,
  onRegistryChange,
  form,
  initialValues
}) => {
  const {
    registries,
    loading,
    error,
    createRegistry,
    testRegistry,
    setDefaultRegistry,
    getInitialFormValues,
    validateStepConfig,
    generateFullImageName,
    getImageSuggestions,
    clearError
  } = useDockerStepConfig()

  const [selectedRegistry, setSelectedRegistry] = useState<any>(null)
  const [showRegistryModal, setShowRegistryModal] = useState(false)

  useEffect(() => {
    // 设置表单初始值
    if (form && initialValues) {
      const mergedValues = getInitialFormValues(stepType, initialValues)
      form.setFieldsValue(mergedValues)
    }
  }, [form, initialValues, stepType, getInitialFormValues])

  useEffect(() => {
    // 监听注册表变化
    const registryId = form?.getFieldValue('docker_registry')
    if (registryId) {
      const registry = registries.find((r: any) => r.id === registryId)
      setSelectedRegistry(registry || null)
    }
  }, [registries, form])

  const handleRegistryChange = (registryId: number) => {
    const registry = registries.find((r: any) => r.id === registryId)
    setSelectedRegistry(registry || null)
    
    if (onRegistryChange) {
      onRegistryChange(registryId)
    }
  }

  const handleCreateRegistry = () => {
    setShowRegistryModal(true)
  }

  const handleTestRegistry = async (registryId: number) => {
    try {
      const result = await testRegistry(registryId)
      if (result.success) {
        message.success('注册表连接测试成功')
      } else {
        message.error(`注册表连接测试失败: ${result.message}`)
      }
    } catch (err) {
      message.error('测试注册表连接失败')
    }
  }

  const imageSuggestions = getImageSuggestions(selectedRegistry?.id || null)

  const renderRegistryInfo = () => {
    if (!selectedRegistry) return null

    return (
      <Alert
        message={
          <Space>
            <LinkOutlined />
            <span>已选择注册表: {selectedRegistry.name}</span>
            <Tag color={selectedRegistry.status === 'active' ? 'green' : 'orange'}>
              {selectedRegistry.status === 'active' ? '可用' : '不可用'}
            </Tag>
            {selectedRegistry.is_default && <Tag color="blue">默认</Tag>}
          </Space>
        }
        description={
          <div>
            <div>地址: {selectedRegistry.url}</div>
            <div>类型: {selectedRegistry.registry_type}</div>
            {selectedRegistry.description && <div>描述: {selectedRegistry.description}</div>}
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
    )
  }

  const handleImageNameChange = (value: string) => {
    if (!form) return
    
    console.log('🔍 handleImageNameChange called with:', value)
    
    // 检查是否包含标签（冒号分隔）
    if (value && value.includes(':')) {
      const parts = value.split(':')
      if (parts.length === 2) {
        const [imageName, tag] = parts
        console.log('📦 Extracting - Image:', imageName, 'Tag:', tag)
        
        // 更新镜像名称部分（不包含标签）
        form.setFieldValue('docker_image', imageName)
        // 自动设置标签
        form.setFieldValue('docker_tag', tag)
        
        // 强制表单重新渲染
        form.validateFields(['docker_image', 'docker_tag'])
        
        console.log('✅ Updated form values - Image:', imageName, 'Tag:', tag)
        return
      }
    }
    
    // 如果没有标签，直接设置镜像名称
    console.log('📝 Setting image without tag:', value)
    form.setFieldValue('docker_image', value)
    // 如果没有标签，确保使用默认标签
    if (!form.getFieldValue('docker_tag')) {
      form.setFieldValue('docker_tag', 'latest')
    }
  }

  const renderDockerBuildConfig = () => (
    <Card size="small" title="Docker Build 配置" style={{ marginBottom: 16 }}>
      <Form.Item
        name="docker_image"
        label="镜像名称"
        rules={[
          { required: true, message: '请输入镜像名称' },
          { pattern: /^[a-z0-9]+([-._][a-z0-9]+)*$/, message: '镜像名称格式不正确' }
        ]}
        tooltip="Docker 镜像的名称，例如: myapp 或 myapp:tag（会自动提取标签）"
      >
        <AutoComplete
          placeholder="例如: myapp 或 myapp:latest"
          options={imageSuggestions.map((img: string) => ({ value: img }))}
          filterOption={(inputValue, option) =>
            String(option?.value || '').toLowerCase().includes(inputValue.toLowerCase())
          }
          onChange={handleImageNameChange}
        />
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
        initialValue="Dockerfile"
      >
        <Input placeholder="例如: ./Dockerfile 或 docker/Dockerfile" />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'context_path']}
        label="构建上下文"
        tooltip="Docker 构建上下文的路径，默认为当前目录"
        initialValue="."
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
        initialValue="linux/amd64"
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
        initialValue={true}
        tooltip="构建前是否拉取最新的基础镜像"
      >
        <Switch checkedChildren="拉取最新" unCheckedChildren="使用本地" />
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
    </Card>
  )

  const renderDockerRunConfig = () => (
    <Card size="small" title="Docker Run 配置" style={{ marginBottom: 16 }}>
      <Form.Item
        name="docker_image"
        label="镜像名称"
        rules={[
          { required: true, message: '请输入镜像名称' },
          { pattern: /^[a-z0-9]+([-._\/][a-z0-9]+)*$/, message: '镜像名称格式不正确' }
        ]}
        tooltip="要运行的 Docker 镜像，支持 image:tag 格式（会自动提取标签）"
      >
        <AutoComplete
          placeholder="例如: nginx:latest"
          options={imageSuggestions.map((img: string) => ({ value: img }))}
          filterOption={(inputValue, option) =>
            String(option?.value || '').toLowerCase().includes(inputValue.toLowerCase())
          }
          onChange={handleImageNameChange}
        />
      </Form.Item>

      <Form.Item
        name="docker_tag"
        label="镜像标签"
        initialValue="latest"
        tooltip="Docker 镜像的标签"
      >
        <Input placeholder="例如: latest, v1.0.0" />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'container_name']}
        label="容器名称"
        tooltip="自定义容器名称"
      >
        <Input placeholder="例如: my-container" />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'command']}
        label="运行命令"
        tooltip="容器启动时执行的命令"
      >
        <Input placeholder="例如: /bin/bash -c 'echo hello'" />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'working_dir']}
        label="工作目录"
        tooltip="容器内的工作目录"
      >
        <Input placeholder="例如: /app" />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'detach']}
        valuePropName="checked"
        initialValue={true}
        tooltip="是否在后台运行容器"
      >
        <Switch checkedChildren="后台运行" unCheckedChildren="前台运行" />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'remove']}
        valuePropName="checked"
        initialValue={true}
        tooltip="容器停止后是否自动删除"
      >
        <Switch checkedChildren="自动删除" unCheckedChildren="保留容器" />
      </Form.Item>

      <Divider orientation="left">端口映射</Divider>
      
      <Form.List name={['docker_config', 'ports']}>
        {(fields, { add, remove }) => (
          <>
            {fields.map(({ key, name, ...restField }) => (
              <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                <Form.Item
                  {...restField}
                  name={[name, 'host']}
                  rules={[{ required: true, message: '请输入宿主机端口' }]}
                  style={{ marginBottom: 0 }}
                >
                  <Input placeholder="宿主机端口" />
                </Form.Item>
                <span>:</span>
                <Form.Item
                  {...restField}
                  name={[name, 'container']}
                  rules={[{ required: true, message: '请输入容器端口' }]}
                  style={{ marginBottom: 0 }}
                >
                  <Input placeholder="容器端口" />
                </Form.Item>
                <MinusCircleOutlined onClick={() => remove(name)} />
              </Space>
            ))}
            <Form.Item>
              <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                添加端口映射
              </Button>
            </Form.Item>
          </>
        )}
      </Form.List>

      <Divider orientation="left">卷挂载</Divider>
      
      <Form.List name={['docker_config', 'volumes']}>
        {(fields, { add, remove }) => (
          <>
            {fields.map(({ key, name, ...restField }) => (
              <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                <Form.Item
                  {...restField}
                  name={[name, 'host']}
                  rules={[{ required: true, message: '请输入宿主机路径' }]}
                  style={{ marginBottom: 0, flex: 1 }}
                >
                  <Input placeholder="宿主机路径" />
                </Form.Item>
                <span>:</span>
                <Form.Item
                  {...restField}
                  name={[name, 'container']}
                  rules={[{ required: true, message: '请输入容器路径' }]}
                  style={{ marginBottom: 0, flex: 1 }}
                >
                  <Input placeholder="容器路径" />
                </Form.Item>
                <Form.Item
                  {...restField}
                  name={[name, 'mode']}
                  initialValue="rw"
                  style={{ marginBottom: 0 }}
                >
                  <Select style={{ width: 60 }}>
                    <Option value="rw">rw</Option>
                    <Option value="ro">ro</Option>
                  </Select>
                </Form.Item>
                <MinusCircleOutlined onClick={() => remove(name)} />
              </Space>
            ))}
            <Form.Item>
              <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                添加卷挂载
              </Button>
            </Form.Item>
          </>
        )}
      </Form.List>
    </Card>
  )

  const renderDockerPushPullConfig = () => (
    <Card size="small" title={`Docker ${stepType === 'docker_push' ? 'Push' : 'Pull'} 配置`} style={{ marginBottom: 16 }}>
      <Form.Item
        name="docker_image"
        label="镜像名称"
        rules={[
          { required: true, message: '请输入镜像名称' },
          { pattern: /^[a-z0-9]+([-._\/][a-z0-9]+)*$/, message: '镜像名称格式不正确' }
        ]}
        tooltip={`要${stepType === 'docker_push' ? '推送' : '拉取'}的 Docker 镜像名称，支持 image:tag 格式（会自动提取标签）`}
      >
        <AutoComplete
          placeholder={stepType === 'docker_push' ? "例如: myapp:latest" : "例如: nginx:alpine, registry.example.com/myapp:v1.0"}
          options={imageSuggestions.map((img: string) => ({ value: img }))}
          filterOption={(inputValue, option) =>
            String(option?.value || '').toLowerCase().includes(inputValue.toLowerCase())
          }
          onChange={handleImageNameChange}
        />
      </Form.Item>

      <Form.Item
        name="docker_tag"
        label="镜像标签"
        initialValue="latest"
        tooltip={`要${stepType === 'docker_push' ? '推送' : '拉取'}的镜像标签`}
      >
        <Input placeholder="例如: latest, v1.0.0" />
      </Form.Item>

      <Form.Item
        name="docker_registry"
        label={stepType === 'docker_push' ? '目标注册表' : '源注册表'}
        rules={stepType === 'docker_push' ? [{ required: true, message: '请选择目标注册表' }] : []}
        tooltip={`选择要${stepType === 'docker_push' ? '推送到' : '从中拉取'}的 Docker 注册表${stepType === 'docker_pull' ? '（可选）' : ''}`}
      >
        <Select 
          placeholder={`选择注册表${stepType === 'docker_pull' ? '（可选）' : ''}`}
          allowClear
          showSearch
          onChange={handleRegistryChange}
          filterOption={(input, option) =>
            (option?.children as any)?.props?.children?.[0]?.props?.children?.toLowerCase().includes(input.toLowerCase()) ?? false
          }
          dropdownRender={menu => (
            <div>
              {menu}
              <Divider style={{ margin: '8px 0' }} />
              <Space style={{ padding: '0 8px 4px' }}>
                <Button type="text" icon={<PlusOutlined />} onClick={handleCreateRegistry}>
                  添加新注册表
                </Button>
              </Space>
            </div>
          )}
        >
          {registries.map((registry: any) => (
            <Option key={registry.id} value={registry.id}>
              <Space>
                <span>{registry.name}</span>
                {registry.is_default && <Tag color="blue">默认</Tag>}
                <Tag color={registry.status === 'active' ? 'green' : 'orange'}>
                  {registry.status === 'active' ? '可用' : '不可用'}
                </Tag>
              </Space>
            </Option>
          ))}
        </Select>
      </Form.Item>

      {renderRegistryInfo()}

      <Form.Item
        name={['docker_config', 'all_tags']}
        valuePropName="checked"
        tooltip={`是否${stepType === 'docker_push' ? '推送' : '拉取'}镜像的所有标签`}
      >
        <Switch 
          checkedChildren={`${stepType === 'docker_push' ? '推送' : '拉取'}所有标签`} 
          unCheckedChildren={`仅${stepType === 'docker_push' ? '推送' : '拉取'}指定标签`} 
        />
      </Form.Item>

      <Form.Item
        name={['docker_config', 'platform']}
        label="目标平台"
        tooltip={`${stepType === 'docker_push' ? '推送' : '拉取'}特定平台的镜像`}
      >
        <Select placeholder="选择目标平台" allowClear>
          <Option value="linux/amd64">linux/amd64</Option>
          <Option value="linux/arm64">linux/arm64</Option>
          <Option value="linux/arm/v7">linux/arm/v7</Option>
          <Option value="windows/amd64">windows/amd64</Option>
        </Select>
      </Form.Item>
    </Card>
  )

  const renderStepTypeInfo = () => {
    const stepInfo = {
      docker_build: {
        title: 'Docker Build',
        description: '构建 Docker 镜像',
        icon: '🔨',
        tips: ['支持多阶段构建', '可配置构建参数和标签', '支持不同平台构建'],
        requiresRegistry: false
      },
      docker_run: {
        title: 'Docker Run',
        description: '运行 Docker 容器',
        icon: '🚀',
        tips: ['支持端口映射和卷挂载', '可配置运行命令', '支持前台/后台运行'],
        requiresRegistry: false
      },
      docker_push: {
        title: 'Docker Push',
        description: '推送 Docker 镜像到注册表',
        icon: '📤',
        tips: ['需要配置注册表认证', '支持推送多个标签', '自动处理镜像标签'],
        requiresRegistry: true
      },
      docker_pull: {
        title: 'Docker Pull',
        description: '从注册表拉取 Docker 镜像',
        icon: '📥',
        tips: ['支持私有注册表', '自动验证镜像完整性', '支持多架构镜像'],
        requiresRegistry: false
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
            {info.requiresRegistry && (
              <Tag color="orange" style={{ marginLeft: 8 }}>
                <ExclamationCircleOutlined /> 需要注册表
              </Tag>
            )}
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
      {error && (
        <Alert
          message="错误"
          description={error}
          type="error"
          closable
          onClose={clearError}
          style={{ marginBottom: 16 }}
        />
      )}
      
      {renderStepTypeInfo()}
      
      {stepType === 'docker_build' && renderDockerBuildConfig()}
      {stepType === 'docker_run' && renderDockerRunConfig()}
      {(stepType === 'docker_push' || stepType === 'docker_pull') && renderDockerPushPullConfig()}
      
      <Card size="small" title="通用配置">
        <Form.Item
          name="timeout_seconds"
          label="超时时间"
          tooltip="步骤执行的超时时间（秒）"
          initialValue={stepType === 'docker_build' ? 1800 : stepType === 'docker_run' ? 3600 : 1800}
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

      {/* 创建注册表模态框 */}
      <Modal
        title="添加 Docker 注册表"
        open={showRegistryModal}
        onCancel={() => setShowRegistryModal(false)}
        footer={null}
        width={600}
      >
        <CreateRegistryForm
          onSuccess={() => {
            setShowRegistryModal(false)
            message.success('注册表创建成功')
          }}
          onCancel={() => setShowRegistryModal(false)}
          createRegistry={createRegistry}
        />
      </Modal>
    </div>
  )
}

export default EnhancedDockerStepConfig

// 创建注册表表单组件
const CreateRegistryForm: React.FC<{
  onSuccess: () => void
  onCancel: () => void
  createRegistry: (data: any) => Promise<any>
}> = ({ onSuccess, onCancel, createRegistry }) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      await createRegistry(values)
      onSuccess()
      form.resetFields()
    } catch (error) {
      message.error('创建注册表失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
    >
      <Form.Item
        name="name"
        label="注册表名称"
        rules={[{ required: true, message: '请输入注册表名称' }]}
      >
        <Input placeholder="例如: 公司私有仓库" />
      </Form.Item>

      <Form.Item
        name="url"
        label="注册表地址"
        rules={[
          { required: true, message: '请输入注册表地址' },
          { type: 'url', message: '请输入有效的URL地址' }
        ]}
      >
        <Input placeholder="例如: https://registry.example.com" />
      </Form.Item>

      <Form.Item
        name="registry_type"
        label="注册表类型"
        rules={[{ required: true, message: '请选择注册表类型' }]}
        initialValue="private"
      >
        <Select>
          <Option value="dockerhub">Docker Hub</Option>
          <Option value="private">私有注册表</Option>
          <Option value="harbor">Harbor</Option>
          <Option value="ecr">AWS ECR</Option>
          <Option value="gcr">Google GCR</Option>
          <Option value="acr">Azure ACR</Option>
        </Select>
      </Form.Item>

      <Form.Item
        name="username"
        label="用户名"
      >
        <Input placeholder="注册表登录用户名" />
      </Form.Item>

      <Form.Item
        name="password"
        label="密码"
      >
        <Input.Password placeholder="注册表登录密码" />
      </Form.Item>

      <Form.Item
        name="description"
        label="描述"
      >
        <TextArea rows={3} placeholder="注册表描述信息" />
      </Form.Item>

      <Form.Item
        name="is_default"
        valuePropName="checked"
      >
        <Switch checkedChildren="设为默认" unCheckedChildren="普通注册表" />
      </Form.Item>

      <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
        <Space>
          <Button onClick={onCancel}>
            取消
          </Button>
          <Button type="primary" htmlType="submit" loading={loading}>
            创建
          </Button>
        </Space>
      </Form.Item>
    </Form>
  )
}
