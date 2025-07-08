import React from 'react'
import { Space, Button } from 'antd'
import {
  PlusOutlined,
  SaveOutlined,
  SettingOutlined,
  EyeOutlined,
  ThunderboltOutlined,
  ShareAltOutlined,
  BarChartOutlined,
  ReloadOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'

interface PipelineToolbarProps {
  showAdvancedOptions: boolean
  showValidationPanel: boolean
  onClose: () => void
  onEditPipelineInfo: () => void
  onPreviewPipeline: () => void
  onAdvancedOptionsToggle: () => void
  onParallelGroupManager: () => void
  onWorkflowAnalyzer: () => void
  onExecutionRecovery: () => void
  onToggleValidationPanel: () => void
  onAddStep: () => void
  onSavePipeline: () => void
}

const PipelineToolbar: React.FC<PipelineToolbarProps> = ({
  showAdvancedOptions,
  showValidationPanel,
  onClose,
  onEditPipelineInfo,
  onPreviewPipeline,
  onAdvancedOptionsToggle,
  onParallelGroupManager,
  onWorkflowAnalyzer,
  onExecutionRecovery,
  onToggleValidationPanel,
  onAddStep,
  onSavePipeline
}) => {
  return (
    <Space>
      <Button onClick={onClose}>取消</Button>
      <Button icon={<SettingOutlined />} onClick={onEditPipelineInfo}>
        编辑信息
      </Button>
      <Button icon={<EyeOutlined />} onClick={onPreviewPipeline}>
        预览Pipeline
      </Button>
      {/* 高级工作流功能按钮 */}
      <Button 
        icon={<ThunderboltOutlined />} 
        type={showAdvancedOptions ? "primary" : "default"}
        onClick={onAdvancedOptionsToggle}
      >
        高级功能
      </Button>
      <Button icon={<ShareAltOutlined />} onClick={onParallelGroupManager}>
        并行组管理
      </Button>
      <Button icon={<BarChartOutlined />} onClick={onWorkflowAnalyzer}>
        工作流分析
      </Button>
      <Button icon={<ReloadOutlined />} onClick={onExecutionRecovery}>
        执行恢复
      </Button>
      <Button icon={<CheckCircleOutlined />} onClick={onToggleValidationPanel}>
        {showValidationPanel ? '隐藏验证' : '工作流验证'}
      </Button>
      <Button icon={<PlusOutlined />} onClick={onAddStep}>
        添加步骤
      </Button>
      <Button type="primary" icon={<SaveOutlined />} onClick={onSavePipeline}>
        保存流水线
      </Button>
    </Space>
  )
}

export default PipelineToolbar
