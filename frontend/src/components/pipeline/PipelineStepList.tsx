import React from 'react'
import { Card, Space, Button, Typography } from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  ThunderboltOutlined,
  BranchesOutlined,
  ShareAltOutlined
} from '@ant-design/icons'
import { PipelineStep, AtomicStep } from '../../types'

const { Text } = Typography

interface PipelineStepListProps {
  steps: (PipelineStep | AtomicStep)[]
  showAdvancedOptions: boolean
  onAddStep: () => void
  onEditStep: (step: PipelineStep | AtomicStep) => void
  onDeleteStep: (stepId: number) => void
  onMoveStep: (stepId: number, direction: 'up' | 'down') => void
  onWorkflowStepEdit: (step: PipelineStep | AtomicStep) => void
  getStepTypeLabel: (stepType: string) => string
  getStepIcon: (stepType: string) => string
  getStepParameters: (step: PipelineStep | AtomicStep) => Record<string, any>
  getStepAnsibleConfig: (step: PipelineStep | AtomicStep) => any
}

const PipelineStepList: React.FC<PipelineStepListProps> = ({
  steps,
  showAdvancedOptions,
  onAddStep,
  onEditStep,
  onDeleteStep,
  onMoveStep,
  onWorkflowStepEdit,
  getStepTypeLabel,
  getStepIcon,
  getStepParameters,
  getStepAnsibleConfig
}) => {
  if (steps.length === 0) {
    return (
      <Card title="流水线步骤配置" size="small">
        <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
          <p>暂无流水线步骤</p>
          <Button type="dashed" icon={<PlusOutlined />} onClick={onAddStep}>
            添加第一个步骤
          </Button>
        </div>
      </Card>
    )
  }

  return (
    <Card title="流水线步骤配置" size="small">
      <div>
        {steps.map((step, index) => (
          <Card
            key={step.id}
            size="small"
            style={{ marginBottom: 16 }}
            title={
              <Space>
                <span>{getStepIcon(step.step_type)}</span>
                <span>步骤 {index + 1}: {step.name}</span>
                <Text type="secondary">({getStepTypeLabel(step.step_type)})</Text>
                {/* 高级功能标签 */}
                {(step as any).condition && (
                  <span style={{ 
                    background: '#1890ff', 
                    color: 'white', 
                    fontSize: '10px', 
                    padding: '2px 6px', 
                    borderRadius: '4px' 
                  }}>
                    <BranchesOutlined /> 条件
                  </span>
                )}
                {(step as any).parallel_group_id && (
                  <span style={{ 
                    background: '#52c41a', 
                    color: 'white', 
                    fontSize: '10px', 
                    padding: '2px 6px', 
                    borderRadius: '4px' 
                  }}>
                    <ShareAltOutlined /> 并行
                  </span>
                )}
                {(step as any).approval_config && (
                  <span style={{ 
                    background: '#fa8c16', 
                    color: 'white', 
                    fontSize: '10px', 
                    padding: '2px 6px', 
                    borderRadius: '4px' 
                  }}>
                    ✋ 审批
                  </span>
                )}
              </Space>
            }
            extra={
              <Space>
                <Button 
                  type="text" 
                  size="small" 
                  icon={<ArrowUpOutlined />}
                  onClick={() => onMoveStep(step.id, 'up')}
                  disabled={index === 0}
                />
                <Button 
                  type="text" 
                  size="small" 
                  icon={<ArrowDownOutlined />}
                  onClick={() => onMoveStep(step.id, 'down')}
                  disabled={index === steps.length - 1}
                />
                <Button 
                  type="text" 
                  size="small" 
                  icon={<EditOutlined />}
                  onClick={() => onEditStep(step)}
                />
                {/* 高级配置按钮 */}
                {showAdvancedOptions && (
                  <Button 
                    type="text" 
                    size="small" 
                    icon={<ThunderboltOutlined />}
                    onClick={() => onWorkflowStepEdit(step)}
                    title="高级配置"
                    style={{ color: '#1890ff' }}
                  />
                )}
                <Button 
                  type="text" 
                  size="small" 
                  icon={<DeleteOutlined />}
                  danger
                  onClick={() => onDeleteStep(step.id)}
                />
              </Space>
            }
          >
            {step.description && (
              <Text type="secondary">{step.description}</Text>
            )}
            
            {/* Ansible步骤特殊显示 */}
            {step.step_type === 'ansible' && (() => {
              const ansibleConfig = getStepAnsibleConfig(step)
              return (
                <div style={{ marginTop: 8 }}>
                  <Text strong>Ansible配置:</Text>
                  <div style={{ marginLeft: 16, marginTop: 4 }}>
                    {ansibleConfig.playbook_id && (
                      <div><Text type="secondary">Playbook ID: </Text>{ansibleConfig.playbook_id}</div>
                    )}
                    {ansibleConfig.inventory_id && (
                      <div><Text type="secondary">Inventory ID: </Text>{ansibleConfig.inventory_id}</div>
                    )}
                    {ansibleConfig.credential_id && (
                      <div><Text type="secondary">Credential ID: </Text>{ansibleConfig.credential_id}</div>
                    )}
                  </div>
                </div>
              )
            })()}
            
            {/* 显示清理后的参数（不包含ansible字段） */}
            {(() => {
              const stepParams = getStepParameters(step)
              const displayParams = { ...stepParams }
              if (step.step_type === 'ansible') {
                delete displayParams.playbook_id
                delete displayParams.inventory_id
                delete displayParams.credential_id
              }
              return Object.keys(displayParams).length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <Text strong>参数: </Text>
                  <Text code>{JSON.stringify(displayParams, null, 2)}</Text>
                </div>
              )
            })()}
          </Card>
        ))}
      </div>
    </Card>
  )
}

export default PipelineStepList
