import React, { useState, useEffect } from 'react'
import { Space, Button, Dropdown, Menu } from 'antd'
import {
  PlusOutlined,
  SaveOutlined,
  SettingOutlined,
  EyeOutlined,
  ThunderboltOutlined,
  ShareAltOutlined,
  BarChartOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  MoreOutlined
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
  const [screenWidth, setScreenWidth] = useState(typeof window !== 'undefined' ? window.innerWidth : 1200)

  useEffect(() => {
    const handleResize = () => {
      setScreenWidth(window.innerWidth)
    }
    
    if (typeof window !== 'undefined') {
      window.addEventListener('resize', handleResize)
      return () => window.removeEventListener('resize', handleResize)
    }
  }, [])

  // 判断屏幕大小
  const isMobile = screenWidth < 768
  const isTablet = screenWidth >= 768 && screenWidth < 1024
  const isSmallDesktop = screenWidth >= 1024 && screenWidth < 1440

  // 高级功能菜单项
  const advancedMenuItems = [
    {
      key: 'advanced',
      label: '高级功能',
      icon: <ThunderboltOutlined />,
      onClick: onAdvancedOptionsToggle
    },
    {
      key: 'parallel',
      label: '并行组管理',
      icon: <ShareAltOutlined />,
      onClick: onParallelGroupManager
    },
    {
      key: 'analyzer',
      label: '工作流分析',
      icon: <BarChartOutlined />,
      onClick: onWorkflowAnalyzer
    },
    {
      key: 'recovery',
      label: '执行恢复',
      icon: <ReloadOutlined />,
      onClick: onExecutionRecovery
    },
    {
      key: 'validation',
      label: showValidationPanel ? '隐藏验证' : '工作流验证',
      icon: <CheckCircleOutlined />,
      onClick: onToggleValidationPanel
    }
  ]

  if (isMobile) {
    // 移动端：只显示最核心的按钮，其他放到更多菜单
    return (
      <Space size="small">
        <Button size="small" onClick={onClose}>取消</Button>
        <Button size="small" icon={<PlusOutlined />} onClick={onAddStep}>
          添加
        </Button>
        <Dropdown 
          menu={{ 
            items: [
              {
                key: 'edit',
                label: '编辑信息',
                icon: <SettingOutlined />,
                onClick: onEditPipelineInfo
              },
              {
                key: 'preview',
                label: '预览Pipeline',
                icon: <EyeOutlined />,
                onClick: onPreviewPipeline
              },
              ...advancedMenuItems
            ]
          }}
          trigger={['click']}
          placement="bottomRight"
        >
          <Button size="small" icon={<MoreOutlined />}>
            更多
          </Button>
        </Dropdown>
        <Button size="small" type="primary" icon={<SaveOutlined />} onClick={onSavePipeline}>
          保存
        </Button>
      </Space>
    )
  } else if (isTablet) {
    // 平板端：显示主要按钮，高级功能合并到菜单
    return (
      <Space size="small">
        <Button size="small" onClick={onClose}>取消</Button>
        <Button size="small" icon={<SettingOutlined />} onClick={onEditPipelineInfo}>
          编辑信息
        </Button>
        <Button size="small" icon={<EyeOutlined />} onClick={onPreviewPipeline}>
          预览
        </Button>
        <Dropdown 
          menu={{ items: advancedMenuItems }}
          trigger={['click']}
          placement="bottomRight"
        >
          <Button size="small" icon={<MoreOutlined />}>
            高级功能
          </Button>
        </Dropdown>
        <Button size="small" icon={<PlusOutlined />} onClick={onAddStep}>
          添加步骤
        </Button>
        <Button size="small" type="primary" icon={<SaveOutlined />} onClick={onSavePipeline}>
          保存流水线
        </Button>
      </Space>
    )
  } else {
    // 桌面端：显示所有按钮
    return (
      <Space size="small">
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
}

export default PipelineToolbar
