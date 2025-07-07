import React, { useState, useEffect } from 'react'
import { Modal, Card, Typography, Alert, Spin, Button, Space, Tabs, Descriptions, Switch, Tooltip } from 'antd'
import { 
  EyeOutlined, 
  CodeOutlined, 
  SettingOutlined,
  PlayCircleOutlined,
  ClockCircleOutlined,
  TagOutlined,
  EditOutlined,
  DatabaseOutlined 
} from '@ant-design/icons'
import { AtomicStep, Pipeline } from '../../types'
import apiService from '../../services/api'

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs

interface PipelinePreviewProps {
  visible: boolean
  pipeline: Pipeline
  steps: AtomicStep[]
  onClose: () => void
  onExecute?: (pipeline: Pipeline) => void
}

interface GeneratedPipeline {
  content?: string  // 主要内容字段，后端优先返回此字段
  jenkinsfile?: string
  gitlab_ci?: string
  github_actions?: string
  workflow_summary: {
    total_steps: number
    estimated_duration: string
    step_types: string[]
    triggers: string[]
    preview_mode?: boolean
    data_source?: string
  }
  supported_tools?: string[]
  current_tool?: string
}

const PipelinePreview: React.FC<PipelinePreviewProps> = ({
  visible,
  pipeline,
  steps,
  onClose,
  onExecute
}) => {
  const [loading, setLoading] = useState(false)
  const [generatedPipeline, setGeneratedPipeline] = useState<GeneratedPipeline | null>(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [previewMode, setPreviewMode] = useState(true) // true: 预览编辑内容, false: 预览数据库内容

  useEffect(() => {
    if (visible) {
      generatePipelinePreview()
    }
  }, [visible, steps, previewMode])

  const generatePipelinePreview = async () => {
    setLoading(true)
    try {
      // 根据预览模式决定使用哪些步骤数据
      const stepsToUse = previewMode ? steps : []
      
      // 调试日志
      console.log('Pipeline Preview 请求参数:', {
        pipeline_id: pipeline.id,
        preview_mode: previewMode,
        steps_count: stepsToUse.length,
        steps_with_ansible: stepsToUse.filter(s => s.step_type === 'ansible').map(s => ({
          name: s.name,
          parameters: s.parameters
        }))
      })
      
      const requestBody = {
        pipeline_id: pipeline.id,
        steps: stepsToUse.map(step => ({
          name: step.name,
          step_type: step.step_type,
          parameters: step.parameters || {},
          order: step.order,
          description: step.description || ''
        })),
        execution_mode: pipeline.execution_mode || 'local',
        execution_tool: pipeline.execution_tool,
        preview_mode: previewMode,  // 传递预览模式参数
        ci_tool_type: 'jenkins', // 默认Jenkins，后续可以根据execution_tool动态设置
        // 确保传递必要的环境变量和配置
        environment: pipeline.config?.environment || {},
        timeout: pipeline.config?.timeout || 3600
      }
      
      const response = await fetch('/api/v1/cicd/pipelines/preview/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
        },
        body: JSON.stringify(requestBody)
      })

      if (response.ok) {
        const data = await response.json()
        console.log('Pipeline Preview 响应数据:', {
          data_source: data.workflow_summary?.data_source,
          preview_mode: data.workflow_summary?.preview_mode,
          content_length: data.content?.length || data.jenkinsfile?.length || 0,
          has_ansible_commands: (data.content || data.jenkinsfile || '').includes('ansible-playbook')
        })
        setGeneratedPipeline(data)
      } else {
        const errorText = await response.text()
        console.error('API响应错误:', errorText)
        throw new Error(`API调用失败: ${response.status}`)
      }
    } catch (error) {
      console.error('生成Pipeline预览失败:', error)
      // 如果API失败，生成模拟数据
      generateMockPreview()
    } finally {
      setLoading(false)
    }
  }

  const generateMockPreview = () => {
    const stepTypes = [...new Set(steps.map(s => s.step_type))]
    const estimatedMinutes = steps.length * 2 // 假设每个步骤2分钟
    
    const mockJenkinsfile = generateMockJenkinsfile()
    
    setGeneratedPipeline({
      jenkinsfile: mockJenkinsfile,
      workflow_summary: {
        total_steps: steps.length,
        estimated_duration: `${estimatedMinutes}分钟`,
        step_types: stepTypes,
        triggers: pipeline.config?.triggers ? Object.keys(pipeline.config.triggers) : ['manual']
      }
    })
  }

  const generateMockJenkinsfile = () => {
    const stages = steps.map(step => {
      let command = 'echo "执行步骤"'
      
      switch (step.step_type) {
        case 'ansible':
          const playbook = step.parameters?.playbook_path || 'playbook.yml'
          const inventory = step.parameters?.inventory_path || 'hosts'
          command = `ansible-playbook -i ${inventory} ${playbook}`
          break
        case 'shell_script':
          command = step.parameters?.script || 'echo "Shell脚本"'
          break
        case 'docker_build':
          const tag = step.parameters?.tag || 'latest'
          command = `docker build -t myapp:${tag} .`
          break
        case 'test':
          command = step.parameters?.test_command || 'npm test'
          break
        default:
          command = step.parameters?.command || `echo "执行${step.step_type}步骤"`
      }

      return `        stage('${step.name}') {
            steps {
                sh '${command}'
            }
        }`
    }).join('\n')

    return `pipeline {
    agent any
    
    options {
        timeout(time: 60, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    
    environment {
        APP_ENV = '${pipeline.config?.environment?.APP_ENV || 'development'}'
    }
    
    stages {
${stages}
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline 执行成功!'
        }
        failure {
            echo 'Pipeline 执行失败!'
        }
    }
}`
  }

  const handleExecutePipeline = () => {
    if (onExecute) {
      onExecute(pipeline)
    }
    onClose()
  }

  const renderOverview = () => (
    <div>
      {/* 数据来源和模式切换 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <Text strong>数据来源: </Text>
            <Text type={previewMode ? 'warning' : 'success'}>
              {previewMode ? '当前编辑内容' : '数据库已保存内容'}
            </Text>
            {generatedPipeline?.workflow_summary.data_source && (
              <Text type="secondary" style={{ marginLeft: 8 }}>
                ({generatedPipeline.workflow_summary.data_source})
              </Text>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Tooltip title={previewMode ? '切换到数据库模式（与实际执行一致）' : '切换到编辑模式（预览当前编辑内容）'}>
              <Space>
                <EditOutlined style={{ color: previewMode ? '#1890ff' : '#999' }} />
                <Switch 
                  checked={!previewMode}
                  onChange={(checked) => setPreviewMode(!checked)}
                  size="small"
                />
                <DatabaseOutlined style={{ color: !previewMode ? '#52c41a' : '#999' }} />
              </Space>
            </Tooltip>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {previewMode ? '编辑预览' : '实际内容'}
            </Text>
          </div>
        </div>

        {!previewMode && (
          <Alert
            message="当前显示的是数据库中已保存的流水线内容"
            description="这与实际执行时使用的内容完全一致。如需预览编辑中的内容，请切换到编辑预览模式。"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {previewMode && (
          <Alert
            message="当前显示的是编辑器中的临时内容"
            description="如需确保与实际执行一致，请先保存流水线，然后切换到实际内容模式。"
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        <Descriptions column={2} size="small">
          <Descriptions.Item label="流水线名称">{pipeline.name}</Descriptions.Item>
          <Descriptions.Item label="执行模式">{pipeline.execution_mode || 'local'}</Descriptions.Item>
          <Descriptions.Item label="总步骤数">{generatedPipeline?.workflow_summary.total_steps}</Descriptions.Item>
          <Descriptions.Item label="预计耗时">{generatedPipeline?.workflow_summary.estimated_duration}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="步骤概览" size="small" style={{ marginBottom: 16 }}>
        {steps.map((step, index) => (
          <div key={step.id || index} style={{ 
            padding: '8px 12px', 
            border: '1px solid #f0f0f0', 
            borderRadius: '6px',
            marginBottom: '8px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <Space>
              <Text strong>{index + 1}.</Text>
              <Text>{step.name}</Text>
            </Space>
            <Space>
              <TagOutlined />
              <Text type="secondary">{step.step_type}</Text>
            </Space>
          </div>
        ))}
      </Card>

      <Card title="步骤类型分布" size="small">
        <Space wrap>
          {generatedPipeline?.workflow_summary.step_types.map(type => (
            <Button key={type} size="small" type="dashed">
              {type}
            </Button>
          ))}
        </Space>
      </Card>
    </div>
  )

  const renderJenkinsfile = () => {
    // 优先使用content字段，如果没有则使用jenkinsfile字段
    const content = generatedPipeline?.content || generatedPipeline?.jenkinsfile || '暂无内容'
    
    return (
      <div>
        <Alert 
          message="Jenkins Pipeline 预览" 
          description={
            <div>
              以下是根据您的流水线配置生成的 Jenkinsfile 内容
              {generatedPipeline?.workflow_summary.data_source && (
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary">
                    数据来源: {generatedPipeline.workflow_summary.data_source === 'frontend' ? '前端编辑内容' : '数据库已保存内容'}
                  </Text>
                </div>
              )}
            </div>
          }
          type="info" 
          style={{ marginBottom: 16 }}
        />
        <pre style={{
          backgroundColor: '#f6f8fa',
          padding: '16px',
          borderRadius: '6px',
          overflow: 'auto',
          maxHeight: '400px',
          fontSize: '13px',
          lineHeight: '1.4',
          border: '1px solid #e1e4e8'
        }}>
          {content}
        </pre>
      </div>
    )
  }

  const renderGitLabCI = () => (
    <div>
      <Alert 
        message="GitLab CI/CD 配置预览" 
        description="以下是根据您的流水线配置生成的 .gitlab-ci.yml 内容"
        type="info" 
        style={{ marginBottom: 16 }}
      />
      <pre style={{
        backgroundColor: '#f6f8fa',
        padding: '16px',
        borderRadius: '6px',
        overflow: 'auto',
        maxHeight: '400px',
        fontSize: '13px',
        lineHeight: '1.4',
        border: '1px solid #e1e4e8'
      }}>
        {generatedPipeline?.gitlab_ci || '暂无 GitLab CI 配置'}
      </pre>
    </div>
  )

  const renderGitHubActions = () => (
    <div>
      <Alert 
        message="GitHub Actions 工作流预览" 
        description="以下是根据您的流水线配置生成的 GitHub Actions 工作流内容"
        type="info" 
        style={{ marginBottom: 16 }}
      />
      <pre style={{
        backgroundColor: '#f6f8fa',
        padding: '16px',
        borderRadius: '6px',
        overflow: 'auto',
        maxHeight: '400px',
        fontSize: '13px',
        lineHeight: '1.4',
        border: '1px solid #e1e4e8'
      }}>
        {generatedPipeline?.github_actions || '暂无 GitHub Actions 配置'}
      </pre>
    </div>
  )

  const renderStepDetails = () => (
    <div>
      {steps.map((step, index) => (
        <Card key={step.id || index} size="small" style={{ marginBottom: 12 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text strong>{index + 1}. {step.name}</Text>
              <Text type="secondary">{step.step_type}</Text>
            </div>
            {step.description && (
              <Text type="secondary">{step.description}</Text>
            )}
            {Object.keys(step.parameters || {}).length > 0 && (
              <div>
                <Text strong>参数:</Text>
                <pre style={{ 
                  backgroundColor: '#f9f9f9', 
                  padding: '8px', 
                  borderRadius: '4px',
                  fontSize: '12px',
                  marginTop: '4px'
                }}>
                  {JSON.stringify(step.parameters, null, 2)}
                </pre>
              </div>
            )}
          </Space>
        </Card>
      ))}
    </div>
  )

  return (
    <Modal
      title={
        <Space>
          <EyeOutlined />
          Pipeline 预览 - {pipeline.name}
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={900}
      footer={
        <Space>
          <Button onClick={onClose}>关闭</Button>
          {onExecute && (
            <Button 
              type="primary" 
              icon={<PlayCircleOutlined />}
              onClick={handleExecutePipeline}
            >
              执行流水线
            </Button>
          )}
        </Space>
      }
    >
      <Spin spinning={loading}>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane 
            tab={
              <span>
                <SettingOutlined />
                概览
              </span>
            } 
            key="overview"
          >
            {generatedPipeline && renderOverview()}
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                <CodeOutlined />
                Jenkins
              </span>
            } 
            key="jenkinsfile"
          >
            {generatedPipeline && renderJenkinsfile()}
          </TabPane>
          
          {generatedPipeline?.gitlab_ci && (
            <TabPane 
              tab={
                <span>
                  <CodeOutlined />
                  GitLab CI
                </span>
              } 
              key="gitlab"
            >
              {renderGitLabCI()}
            </TabPane>
          )}
          
          {generatedPipeline?.github_actions && (
            <TabPane 
              tab={
                <span>
                  <CodeOutlined />
                  GitHub Actions
                </span>
              } 
              key="github"
            >
              {renderGitHubActions()}
            </TabPane>
          )}
          
          <TabPane 
            tab={
              <span>
                <ClockCircleOutlined />
                步骤详情
              </span>
            } 
            key="steps"
          >
            {renderStepDetails()}
          </TabPane>
        </Tabs>
      </Spin>
    </Modal>
  )
}

export default PipelinePreview
