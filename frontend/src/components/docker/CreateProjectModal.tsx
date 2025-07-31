import React, { useState } from 'react';
import {
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Button,
  Space,
  message
} from 'antd';
import { DockerRegistryProjectFormData, DockerRegistry, DockerRegistryList } from '../../types/docker';
import DockerRegistryProjectService from '../../services/dockerRegistryProjectService';

const { Option } = Select;
const { TextArea } = Input;

interface CreateProjectModalProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: (project: any) => void;
  registries: (DockerRegistry | DockerRegistryList)[];
  preselectedRegistryId?: number;
}

const CreateProjectModal: React.FC<CreateProjectModalProps> = ({
  visible,
  onCancel,
  onSuccess,
  registries,
  preselectedRegistryId
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: DockerRegistryProjectFormData) => {
    setLoading(true);
    try {
      const project = await DockerRegistryProjectService.createProject(values);
      message.success('项目创建成功');
      form.resetFields();
      onSuccess(project);
    } catch (error) {
      message.error(`创建失败: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  return (
    <Modal
      title="创建新项目"
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={500}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          registry: preselectedRegistryId,
          visibility: 'private',
          is_default: false
        }}
      >
        <Form.Item
          name="name"
          label="项目名称"
          rules={[
            { required: true, message: '请输入项目名称' },
            { max: 100, message: '名称不能超过100个字符' },
            { pattern: /^[a-zA-Z0-9._-]+$/, message: '项目名称只能包含字母、数字、点、下划线和连字符' }
          ]}
        >
          <Input placeholder="请输入项目名称，如: myapp" />
        </Form.Item>

        <Form.Item
          name="registry"
          label="所属注册表"
          rules={[{ required: true, message: '请选择注册表' }]}
        >
          <Select placeholder="请选择注册表">
            {registries.map(registry => (
              <Option key={registry.id} value={registry.id}>
                {registry.name} ({(registry as DockerRegistry).registry_type || 'unknown'})
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="description"
          label="项目描述"
        >
          <TextArea
            rows={3}
            placeholder="请输入项目描述（可选）"
            maxLength={500}
          />
        </Form.Item>

        <Form.Item
          name="visibility"
          label="可见性"
          initialValue="private"
        >
          <Select>
            <Option value="public">公开</Option>
            <Option value="private">私有</Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="tags"
          label="标签"
        >
          <Select
            mode="tags"
            placeholder="输入标签，按回车添加"
            style={{ width: '100%' }}
          >
          </Select>
        </Form.Item>

        <Form.Item
          name="is_default"
          label="设为默认项目"
          valuePropName="checked"
        >
          <Switch />
        </Form.Item>

        <Form.Item style={{ marginBottom: 0 }}>
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button onClick={handleCancel}>
              取消
            </Button>
            <Button type="primary" htmlType="submit" loading={loading}>
              创建
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default CreateProjectModal;
