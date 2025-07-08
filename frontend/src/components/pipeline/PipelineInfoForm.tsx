import React from 'react'
import { Drawer, Form, Input, Select, Space, Button } from 'antd'

interface PipelineInfoFormProps {
  visible: boolean
  form: any
  tools: { id: number; name: string; tool_type: string; base_url: string }[]
  onClose: () => void
  onSubmit: () => void
}

const PipelineInfoForm: React.FC<PipelineInfoFormProps> = ({
  visible,
  form,
  tools,
  onClose,
  onSubmit
}) => {
  return (
    <Drawer
      title="编辑流水线信息"
      open={visible}
      onClose={onClose}
      width={500}
      footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={onClose}>取消</Button>
          <Button type="primary" onClick={onSubmit}>
            保存
          </Button>
        </Space>
      }
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label="流水线名称"
          rules={[{ required: true, message: '请输入流水线名称' }]}
        >
          <Input placeholder="输入流水线名称" />
        </Form.Item>

        <Form.Item
          name="description"
          label="描述"
        >
          <Input.TextArea 
            placeholder="输入流水线描述（可选）" 
            rows={3} 
          />
        </Form.Item>

        <Form.Item
          name="execution_mode"
          label="执行模式"
          tooltip="本地执行：使用本地Celery执行；远程工具：在CI/CD工具中执行；混合模式：部分本地、部分远程执行"
        >
          <Select placeholder="选择执行模式">
            <Select.Option value="local">本地执行</Select.Option>
            <Select.Option value="remote">远程工具</Select.Option>
            <Select.Option value="hybrid">混合模式</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="execution_tool"
          label="执行工具"
          tooltip="选择用于远程或混合模式执行的CI/CD工具"
        >
          <Select 
            placeholder="选择CI/CD工具（可选）" 
            allowClear
          >
            {tools.map((tool: any) => (
              <Select.Option 
                key={tool.id} 
                value={tool.id}
              >
                {tool.name} ({tool.tool_type})
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="tool_job_name"
          label="工具作业名称"
          tooltip="在CI/CD工具中的作业名称"
        >
          <Input placeholder="输入工具中的作业名称（可选）" />
        </Form.Item>

        <Form.Item
          name="is_active"
          label="状态"
        >
          <Select>
            <Select.Option value={true}>活跃</Select.Option>
            <Select.Option value={false}>停用</Select.Option>
          </Select>
        </Form.Item>
      </Form>
    </Drawer>
  )
}

export default PipelineInfoForm
