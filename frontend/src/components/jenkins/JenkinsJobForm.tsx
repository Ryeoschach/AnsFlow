import React, { useState, useEffect } from 'react'
import { Modal, Form, Input, Button, message, Tabs } from 'antd'
import { Tool, JenkinsJob } from '../../types'
import apiService from '../../services/api'
import { useAppStore } from '../../stores/app'

const { TextArea } = Input
const { TabPane } = Tabs

interface JenkinsJobFormProps {
  tool: Tool
  job?: JenkinsJob | null
  visible: boolean
  onCancel: () => void
  onSuccess: () => void
}

const JenkinsJobForm: React.FC<JenkinsJobFormProps> = ({
  tool,
  job,
  visible,
  onCancel,
  onSuccess
}) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [config, setConfig] = useState('')
  const { addNotification } = useAppStore()

  useEffect(() => {
    if (visible) {
      if (job) {
        form.setFieldsValue({ name: job.name })
        // Load job configuration
        loadJobConfig()
      } else {
        form.resetFields()
        setConfig(getDefaultConfig())
      }
    }
  }, [visible, job, form])

  const loadJobConfig = async () => {
    if (!job) return
    
    try {
      const jobDetail = await apiService.getJenkinsJob(tool.id, job.name)
      setConfig(jobDetail.config || '')
    } catch (error) {
      console.error('Failed to load job config:', error)
      setConfig('')
    }
  }

  const getDefaultConfig = () => {
    return `<?xml version='1.1' encoding='UTF-8'?>
<project>
  <description>通过AnsFlow创建的Jenkins作业</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>echo "Hello World from AnsFlow!"</command>
    </hudson.tasks.Shell>
  </builders>
  <publishers/>
  <buildWrappers/>
</project>`
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)

      if (job) {
        // Update existing job
        await apiService.updateJenkinsJob(tool.id, job.name, config)
        message.success('作业更新成功')
      } else {
        // Create new job
        await apiService.createJenkinsJob(tool.id, values.name, config)
        message.success('作业创建成功')
      }

      addNotification({
        level: 'success',
        title: job ? '作业更新成功' : '作业创建成功',
        message: `Jenkins作业 "${values.name}" ${job ? '已更新' : '已创建'}`
      })

      onSuccess()
    } catch (error) {
      console.error('Failed to save job:', error)
      message.error(job ? '作业更新失败' : '作业创建失败')
    } finally {
      setLoading(false)
    }
  }

  const configTemplates = {
    freestyle: getDefaultConfig(),
    pipeline: `<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.40">
  <description>Pipeline作业</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.92">
    <script>
pipeline {
    agent any
    
    stages {
        stage('Build') {
            steps {
                echo 'Building...'
            }
        }
        stage('Test') {
            steps {
                echo 'Testing...'
            }
        }
        stage('Deploy') {
            steps {
                echo 'Deploying...'
            }
        }
    }
}
    </script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>`,
    maven: `<?xml version='1.1' encoding='UTF-8'?>
<maven2-moduleset plugin="maven-plugin@3.8">
  <description>Maven项目</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <rootModule>
    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
  </rootModule>
  <goals>clean compile test</goals>
  <aggregatorStyleBuild>true</aggregatorStyleBuild>
  <incrementalBuild>false</incrementalBuild>
  <ignoreUpstremChanges>false</ignoreUpstremChanges>
  <ignoreUnsuccessfulUpstreams>false</ignoreUnsuccessfulUpstreams>
  <archivingDisabled>false</archivingDisabled>
  <siteArchivingDisabled>false</siteArchivingDisabled>
  <fingerprintingDisabled>false</fingerprintingDisabled>
  <resolveDependencies>false</resolveDependencies>
  <processPlugins>false</processPlugins>
  <mavenValidationLevel>-1</mavenValidationLevel>
  <runHeadless>false</runHeadless>
  <disableTriggerDownstreamProjects>false</disableTriggerDownstreamProjects>
  <blockTriggerWhenBuilding>true</blockTriggerWhenBuilding>
  <settings class="jenkins.mvn.DefaultSettingsProvider"/>
  <globalSettings class="jenkins.mvn.DefaultGlobalSettingsProvider"/>
  <reporters/>
  <publishers/>
  <buildWrappers/>
</maven2-moduleset>`
  }

  return (
    <Modal
      title={job ? `编辑作业 - ${job.name}` : '新建Jenkins作业'}
      open={visible}
      onCancel={onCancel}
      width={800}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          取消
        </Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleSubmit}>
          {job ? '更新' : '创建'}
        </Button>,
      ]}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label="作业名称"
          rules={[
            { required: true, message: '请输入作业名称' },
            { pattern: /^[a-zA-Z0-9._-]+$/, message: '作业名称只能包含字母、数字、点、下划线和连字符' }
          ]}
        >
          <Input 
            placeholder="输入作业名称"
            disabled={!!job}
          />
        </Form.Item>
      </Form>

      <Tabs defaultActiveKey="config">
        <TabPane tab="作业配置" key="config">
          <div style={{ marginBottom: 8 }}>
            <span style={{ marginRight: 8 }}>快速模板：</span>
            <Button 
              size="small" 
              onClick={() => setConfig(configTemplates.freestyle)}
            >
              自由风格
            </Button>
            <Button 
              size="small" 
              style={{ marginLeft: 8 }}
              onClick={() => setConfig(configTemplates.pipeline)}
            >
              Pipeline
            </Button>
            <Button 
              size="small" 
              style={{ marginLeft: 8 }}
              onClick={() => setConfig(configTemplates.maven)}
            >
              Maven
            </Button>
          </div>
          
          <TextArea
            value={config}
            onChange={(e) => setConfig(e.target.value)}
            placeholder="输入Jenkins作业配置XML..."
            rows={16}
            style={{ fontFamily: 'monospace', fontSize: 12 }}
          />
          
          <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
            提示：这是Jenkins作业的XML配置。您可以使用上面的模板，或者从现有作业中导出配置。
          </div>
        </TabPane>
        
        <TabPane tab="配置说明" key="help">
          <div style={{ fontSize: 14 }}>
            <h4>作业配置说明</h4>
            <ul>
              <li><strong>自由风格项目</strong>：最基本的作业类型，适合简单的构建任务</li>
              <li><strong>Pipeline</strong>：使用Jenkinsfile定义的现代CI/CD流水线</li>
              <li><strong>Maven项目</strong>：专门用于构建Maven项目的作业类型</li>
            </ul>
            
            <h4>常用配置元素</h4>
            <ul>
              <li><code>&lt;description&gt;</code>：作业描述</li>
              <li><code>&lt;scm&gt;</code>：源代码管理配置</li>
              <li><code>&lt;builders&gt;</code>：构建步骤</li>
              <li><code>&lt;publishers&gt;</code>：构建后操作</li>
              <li><code>&lt;triggers&gt;</code>：触发器配置</li>
            </ul>
            
            <h4>注意事项</h4>
            <ul>
              <li>配置必须是有效的XML格式</li>
              <li>创建后可以在Jenkins控制台中进一步配置</li>
              <li>建议先在测试环境中验证配置</li>
            </ul>
          </div>
        </TabPane>
      </Tabs>
    </Modal>
  )
}

export default JenkinsJobForm
