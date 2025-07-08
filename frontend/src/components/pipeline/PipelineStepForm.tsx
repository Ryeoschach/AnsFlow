import React, { useState } from 'react'
import { 
  Drawer, 
  Form, 
  Input, 
  Select, 
  Space, 
  Button, 
  Divider, 
  Alert, 
  Typography 
} from 'antd'
import { QuestionCircleOutlined } from '@ant-design/icons'
import { PipelineStep, AtomicStep, GitCredential } from '../../types'
import ParameterDocumentation from '../ParameterDocumentation'

const { Option } = Select
const { TextArea } = Input
const { Text } = Typography

interface PipelineStepFormProps {
  visible: boolean
  form: any
  editingStep: (PipelineStep | AtomicStep) | null
  selectedStepType: string
  showParameterDoc: boolean
  gitCredentials: GitCredential[]
  ansiblePlaybooks: any[]
  ansibleInventories: any[]
  ansibleCredentials: any[]
  stepTypes: Array<{ value: string; label: string; description: string }>
  onClose: () => void
  onSubmit: () => void
  onStepTypeChange: (value: string) => void
  onToggleParameterDoc: () => void
  onParameterSelect: (paramKey: string, paramValue: any) => void
}

const PipelineStepForm: React.FC<PipelineStepFormProps> = ({
  visible,
  form,
  editingStep,
  selectedStepType,
  showParameterDoc,
  gitCredentials,
  ansiblePlaybooks,
  ansibleInventories,
  ansibleCredentials,
  stepTypes,
  onClose,
  onSubmit,
  onStepTypeChange,
  onToggleParameterDoc,
  onParameterSelect
}) => {
  return (
    <Drawer
      title={editingStep ? '编辑步骤' : '新建步骤'}
      open={visible}
      onClose={onClose}
      width={500}
      footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={onClose}>关闭</Button>
          <Button type="primary" onClick={onSubmit}>
            {editingStep ? '更新步骤' : '添加步骤'}
          </Button>
        </Space>
      }
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label="步骤名称"
          rules={[{ required: true, message: '请输入步骤名称' }]}
        >
          <Input placeholder="输入步骤名称" />
        </Form.Item>

        <Form.Item
          name="step_type"
          label="步骤类型"
          rules={[{ required: true, message: '请选择步骤类型' }]}
        >
          <Select 
            placeholder="选择步骤类型"
            optionLabelProp="label"
            onChange={onStepTypeChange}
          >
            {stepTypes.map(type => (
              <Option 
                key={type.value} 
                value={type.value}
                label={type.label}
              >
                <div style={{ lineHeight: '1.4', padding: '4px 0' }}>
                  <div style={{ fontWeight: 500, marginBottom: 2 }}>
                    {type.label}
                  </div>
                  <div style={{ 
                    fontSize: 12, 
                    color: '#999',
                    whiteSpace: 'normal',
                    wordBreak: 'break-word',
                    lineHeight: '1.3'
                  }}>
                    {type.description}
                  </div>
                </div>
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="description"
          label="步骤描述"
        >
          <Input placeholder="输入步骤描述（可选）" />
        </Form.Item>

        <Form.Item
          name="order"
          label="执行顺序"
          rules={[{ required: true, message: '请输入执行顺序' }]}
        >
          <Input type="number" placeholder="执行顺序" />
        </Form.Item>

        <Divider>参数配置</Divider>
        
        {/* 参数说明按钮 */}
        {selectedStepType && (
          <Alert
            message={
              <Space>
                <span>需要参数配置帮助？</span>
                <Button 
                  type="link" 
                  size="small" 
                  icon={<QuestionCircleOutlined />}
                  onClick={onToggleParameterDoc}
                >
                  {showParameterDoc ? '隐藏参数说明' : '查看参数说明'}
                </Button>
              </Space>
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {/* 参数说明组件 */}
        {selectedStepType && showParameterDoc && (
          <div style={{ marginBottom: 16 }}>
            <ParameterDocumentation 
              stepType={selectedStepType}
              visible={showParameterDoc}
              onParameterSelect={onParameterSelect}
            />
          </div>
        )}

        {/* Git凭据选择 - 仅在代码拉取步骤显示 */}
        {selectedStepType === 'fetch_code' && (
          <Form.Item
            name="git_credential_id"
            label={
              <Space>
                <span>Git认证凭据</span>
                <Button 
                  type="link" 
                  size="small"
                  onClick={() => {
                    window.open('/settings?module=git-credentials', '_blank')
                  }}
                >
                  管理凭据
                </Button>
              </Space>
            }
            tooltip="选择用于拉取代码的Git认证凭据，如果不选择则使用公开仓库或默认认证"
          >
            <Select 
              placeholder="选择Git凭据（可选）"
              allowClear
              optionLabelProp="label"
              notFoundContent={
                <div style={{ textAlign: 'center', padding: '20px' }}>
                  <Text type="secondary">暂无Git凭据</Text>
                  <br />
                  <Button 
                    type="link" 
                    size="small"
                    onClick={() => {
                      window.open('/settings?module=git-credentials', '_blank')
                    }}
                  >
                    去创建凭据
                  </Button>
                </div>
              }
            >
              {gitCredentials.map(credential => (
                <Select.Option 
                  key={credential.id} 
                  value={credential.id}
                  label={credential.name}
                >
                  <div style={{ lineHeight: '1.4', padding: '4px 0' }}>
                    <div style={{ fontWeight: 500, marginBottom: 2 }}>
                      {credential.name}
                    </div>
                    <div style={{ 
                      fontSize: 12, 
                      color: '#999',
                      whiteSpace: 'normal',
                      wordBreak: 'break-word',
                      lineHeight: '1.3'
                    }}>
                      {credential.platform_display} - {credential.server_url}
                    </div>
                  </div>
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
        )}
        
        {/* Ansible资源选择 - 仅在ansible步骤显示 */}
        {selectedStepType === 'ansible' && (
          <>
            <Form.Item
              name="ansible_playbook_id"
              label={
                <Space>
                  <span>Ansible Playbook</span>
                  <Button 
                    type="link" 
                    size="small"
                    onClick={() => {
                      window.open('/ansible?tab=playbooks', '_blank')
                    }}
                  >
                    管理Playbook
                  </Button>
                </Space>
              }
              tooltip="选择要执行的Ansible Playbook"
              rules={[{ required: true, message: '请选择Ansible Playbook' }]}
            >
              <Select 
                placeholder="选择Ansible Playbook"
                optionLabelProp="label"
                notFoundContent={
                  <div style={{ textAlign: 'center', padding: '20px' }}>
                    <Text type="secondary">暂无Playbook</Text>
                    <br />
                    <Button 
                      type="link" 
                      size="small"
                      onClick={() => {
                        window.open('/ansible?tab=playbooks', '_blank')
                      }}
                    >
                      去创建Playbook
                    </Button>
                  </div>
                }
              >
                {ansiblePlaybooks.map(playbook => (
                  <Select.Option 
                    key={playbook.id} 
                    value={playbook.id}
                    label={playbook.name}
                  >
                    <div style={{ lineHeight: '1.4', padding: '4px 0' }}>
                      <div style={{ fontWeight: 500, marginBottom: 2 }}>
                        {playbook.name}
                      </div>
                      <div style={{ 
                        fontSize: 12, 
                        color: '#999',
                        whiteSpace: 'normal',
                        wordBreak: 'break-word',
                        lineHeight: '1.3'
                      }}>
                        {playbook.description || '无描述'}
                      </div>
                    </div>
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="ansible_inventory_id"
              label={
                <Space>
                  <span>Ansible Inventory</span>
                  <Button 
                    type="link" 
                    size="small"
                    onClick={() => {
                      window.open('/ansible?tab=inventories', '_blank')
                    }}
                  >
                    管理Inventory
                  </Button>
                </Space>
              }
              tooltip="选择目标主机清单（可选）"
            >
              <Select 
                placeholder="选择Ansible Inventory（可选）"
                allowClear
                optionLabelProp="label"
                notFoundContent={
                  <div style={{ textAlign: 'center', padding: '20px' }}>
                    <Text type="secondary">暂无Inventory</Text>
                    <br />
                    <Button 
                      type="link" 
                      size="small"
                      onClick={() => {
                        window.open('/ansible?tab=inventories', '_blank')
                      }}
                    >
                      去创建Inventory
                    </Button>
                  </div>
                }
              >
                {ansibleInventories.map(inventory => (
                  <Select.Option 
                    key={inventory.id} 
                    value={inventory.id}
                    label={inventory.name}
                  >
                    <div style={{ lineHeight: '1.4', padding: '4px 0' }}>
                      <div style={{ fontWeight: 500, marginBottom: 2 }}>
                        {inventory.name}
                      </div>
                      <div style={{ 
                        fontSize: 12, 
                        color: '#999',
                        whiteSpace: 'normal',
                        wordBreak: 'break-word',
                        lineHeight: '1.3'
                      }}>
                        {inventory.description || '无描述'}
                      </div>
                    </div>
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="ansible_credential_id"
              label={
                <Space>
                  <span>Ansible Credential</span>
                  <Button 
                    type="link" 
                    size="small"
                    onClick={() => {
                      window.open('/ansible?tab=credentials', '_blank')
                    }}
                  >
                    管理Credential
                  </Button>
                </Space>
              }
              tooltip="选择SSH认证凭据（可选）"
            >
              <Select 
                placeholder="选择Ansible Credential（可选）"
                allowClear
                optionLabelProp="label"
                notFoundContent={
                  <div style={{ textAlign: 'center', padding: '20px' }}>
                    <Text type="secondary">暂无Credential</Text>
                    <br />
                    <Button 
                      type="link" 
                      size="small"
                      onClick={() => {
                        window.open('/ansible?tab=credentials', '_blank')
                      }}
                    >
                      去创建Credential
                    </Button>
                  </div>
                }
              >
                {ansibleCredentials.map(credential => (
                  <Select.Option 
                    key={credential.id} 
                    value={credential.id}
                    label={credential.name}
                  >
                    <div style={{ lineHeight: '1.4', padding: '4px 0' }}>
                      <div style={{ fontWeight: 500, marginBottom: 2 }}>
                        {credential.name}
                      </div>
                      <div style={{ 
                        fontSize: 12, 
                        color: '#999',
                        whiteSpace: 'normal',
                        wordBreak: 'break-word',
                        lineHeight: '1.3'
                      }}>
                        {credential.username} - {credential.credential_type}
                      </div>
                    </div>
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </>
        )}
        
        <Form.Item
          name="parameters"
          label={
            <Space>
              <span>步骤参数</span>
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                (JSON格式)
              </Typography.Text>
            </Space>
          }
        >
          <TextArea 
            placeholder='输入JSON格式的参数，例如: {"timeout": 300, "retry": 3}'
            rows={6}
          />
        </Form.Item>
      </Form>
    </Drawer>
  )
}

export default PipelineStepForm
