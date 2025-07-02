import React, { useState } from 'react';
import { 
  Card, 
  Collapse, 
  Typography, 
  Tag, 
  Space, 
  Divider, 
  Tooltip, 
  Button,
  Alert,
  Table
} from 'antd';
import { 
  InfoCircleOutlined, 
  DownOutlined, 
  RightOutlined,
  CopyOutlined,
  PlayCircleOutlined
} from '@ant-design/icons';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import pipelineStepsConfig from '../config/pipeline-steps-config.json';

const { Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface ParameterDocumentationProps {
  stepType: string;
  visible?: boolean;
  onParameterSelect?: (paramKey: string, paramValue: any) => void;
}

export const ParameterDocumentation: React.FC<ParameterDocumentationProps> = ({
  stepType,
  visible = true,
  onParameterSelect
}) => {
  const [expandedPanels, setExpandedPanels] = useState<string[]>([]);
  
  const stepConfig = (pipelineStepsConfig as any).pipelineStepsConfig[stepType];
  
  if (!stepConfig || !visible) {
    return null;
  }

  const handlePanelChange = (key: string | string[]) => {
    setExpandedPanels(Array.isArray(key) ? key : [key]);
  };

  const handleParameterExample = (paramKey: string, exampleValue: any) => {
    if (onParameterSelect) {
      onParameterSelect(paramKey, exampleValue);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const renderParameterTable = () => {
    const columns = [
      {
        title: '参数名',
        dataIndex: 'key',
        key: 'key',
        width: 120,
        render: (key: string, record: any) => (
          <Space direction="vertical" size={0}>
            <Text code strong>{key}</Text>
            {record.required && <Tag color="red">必需</Tag>}
            {record.defaultValue && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                默认: {record.defaultValue}
              </Text>
            )}
          </Space>
        )
      },
      {
        title: '类型',
        dataIndex: 'type',
        key: 'type',
        width: 80,
        render: (type: string) => (
          <Tag color="blue">{type}</Tag>
        )
      },
      {
        title: '说明',
        dataIndex: 'description',
        key: 'description',
        render: (description: string, record: any) => (
          <Space direction="vertical" size={4}>
            <Text>{description}</Text>
            {record.placeholder && (
              <Text type="secondary" style={{ fontSize: '12px', fontStyle: 'italic' }}>
                示例: {record.placeholder}
              </Text>
            )}
          </Space>
        )
      },
      {
        title: '操作',
        key: 'actions',
        width: 100,
        render: (_: any, record: any) => (
          <Space>
            <Tooltip title="使用默认值">
              <Button 
                size="small" 
                icon={<PlayCircleOutlined />}
                onClick={() => handleParameterExample(record.key, record.defaultValue || record.placeholder)}
              >
                使用
              </Button>
            </Tooltip>
          </Space>
        )
      }
    ];

    return (
      <Table
        columns={columns}
        dataSource={stepConfig.parameters}
        pagination={false}
        size="small"
        rowKey="key"
      />
    );
  };

  const renderJenkinsExamples = () => {
    if (!stepConfig.jenkinsConversion?.examples) {
      return null;
    }

    return (
      <Space direction="vertical" style={{ width: '100%' }}>
        {stepConfig.jenkinsConversion.examples.map((example: any, index: number) => (
          <Card key={index} size="small" style={{ marginBottom: 8 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>示例 {index + 1}</Text>
              
              <div>
                <Text type="secondary">输入参数:</Text>
                <div style={{ marginTop: 4 }}>
                  <SyntaxHighlighter
                    language="json"
                    style={tomorrow}
                    customStyle={{ 
                      fontSize: '12px', 
                      margin: 0, 
                      padding: '8px',
                      borderRadius: '4px'
                    }}
                  >
                    {JSON.stringify(example.input, null, 2)}
                  </SyntaxHighlighter>
                </div>
              </div>

              <div>
                <Space>
                  <Text type="secondary">Jenkins输出:</Text>
                  <Button 
                    size="small" 
                    icon={<CopyOutlined />}
                    onClick={() => copyToClipboard(example.output)}
                  >
                    复制
                  </Button>
                </Space>
                <div style={{ marginTop: 4 }}>
                  <SyntaxHighlighter
                    language="groovy"
                    style={tomorrow}
                    customStyle={{ 
                      fontSize: '12px', 
                      margin: 0, 
                      padding: '8px',
                      borderRadius: '4px'
                    }}
                  >
                    {example.output}
                  </SyntaxHighlighter>
                </div>
              </div>
            </Space>
          </Card>
        ))}
      </Space>
    );
  };

  const renderConditionalParams = () => {
    const conditionalParams = stepConfig.parameters.filter((p: any) => p.showWhen || p.conditionalDisplay);
    
    if (conditionalParams.length === 0) {
      return null;
    }

    return (
      <Alert
        message="条件参数说明"
        description={
          <ul style={{ margin: 0, paddingLeft: 16 }}>
            {conditionalParams.map((param: any) => (
              <li key={param.key}>
                <Text code>{param.key}</Text> - 
                {param.showWhen && (
                  <Text type="secondary">
                    {` 当 ${Object.keys(param.showWhen)[0]} = "${Object.values(param.showWhen)[0]}" 时显示`}
                  </Text>
                )}
                {param.conditionalDisplay && (
                  <Text type="secondary">
                    {` 根据 ${param.conditionalDisplay.dependsOn} 的值动态调整`}
                  </Text>
                )}
              </li>
            ))}
          </ul>
        }
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
    );
  };

  return (
    <Card 
      title={
        <Space>
          <InfoCircleOutlined />
          <Text strong>{stepConfig.name} - 参数说明</Text>
        </Space>
      }
      extra={
        <Tag color={(pipelineStepsConfig as any).categories[stepConfig.category]?.color}>
          {(pipelineStepsConfig as any).categories[stepConfig.category]?.name}
        </Tag>
      }
      size="small"
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        <Paragraph type="secondary">{stepConfig.description}</Paragraph>
        
        {renderConditionalParams()}

        <Collapse 
          activeKey={expandedPanels}
          onChange={handlePanelChange}
          size="small"
        >
          <Panel 
            header="参数列表" 
            key="parameters"
            extra={<Tag>{stepConfig.parameters.length} 个参数</Tag>}
          >
            {renderParameterTable()}
          </Panel>

          <Panel 
            header="Jenkins转换说明" 
            key="jenkins"
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Paragraph type="secondary">
                {stepConfig.jenkinsConversion?.description}
              </Paragraph>
              
              <Text strong>转换示例:</Text>
              {renderJenkinsExamples()}
            </Space>
          </Panel>

          <Panel 
            header="参数优先级" 
            key="priority"
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Paragraph type="secondary">
                参数按以下优先级生效（数字越小优先级越高）：
              </Paragraph>
              
              <div style={{ marginLeft: 16 }}>
                {stepConfig.parameters
                  .sort((a: any, b: any) => (a.priority || 99) - (b.priority || 99))
                  .map((param: any, index: number) => (
                    <div key={param.key} style={{ marginBottom: 4 }}>
                      <Text>
                        {index + 1}. <Text code>{param.key}</Text> 
                        {param.priority && (
                          <Text type="secondary"> (优先级: {param.priority})</Text>
                        )}
                      </Text>
                    </div>
                  ))
                }
              </div>
              
              <Alert
                message="优先级说明"
                description="command 参数通常具有最高优先级，会覆盖其他所有参数的效果。"
                type="warning"
                showIcon
                style={{ marginTop: 8 }}
              />
            </Space>
          </Panel>
        </Collapse>
      </Space>
    </Card>
  );
};

export default ParameterDocumentation;
