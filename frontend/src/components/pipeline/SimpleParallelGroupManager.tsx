import React from 'react'
import { Modal, Button, Alert } from 'antd'
import { ClusterOutlined } from '@ant-design/icons'

interface SimpleParallelGroupManagerProps {
  visible: boolean
  onClose: () => void
}

const SimpleParallelGroupManager: React.FC<SimpleParallelGroupManagerProps> = ({
  visible,
  onClose
}) => {
  return (
    <Modal
      title="并行组管理（简化版）"
      open={visible}
      onCancel={onClose}
      width={600}
      footer={[
        <Button key="close" onClick={onClose}>
          关闭
        </Button>
      ]}
    >
      <Alert
        message="测试组件"
        description="这是一个简化版的并行组管理器，用于测试组件渲染。"
        type="success"
        showIcon
      />
    </Modal>
  )
}

export default SimpleParallelGroupManager
