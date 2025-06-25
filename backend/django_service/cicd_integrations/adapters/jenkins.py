"""
Jenkins CI/CD 适配器实现
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import httpx

from .base import CICDAdapter, PipelineDefinition, ExecutionResult

logger = logging.getLogger(__name__)


class JenkinsAdapter(CICDAdapter):
    """Jenkins 适配器"""
    
    def __init__(self, base_url: str, username: str, token: str, **kwargs):
        super().__init__(base_url, username, token, **kwargs)
        self.auth = (username, token) if username and token else None
        
        # Jenkins 特定配置
        self.crumb_issuer = kwargs.get('crumb_issuer', True)
        self.folder_path = kwargs.get('folder_path', '')
    
    async def _get_crumb(self) -> Optional[Tuple[str, str]]:
        """获取 Jenkins CSRF 保护令牌"""
        if not self.crumb_issuer:
            return None
        
        try:
            response = await self.client.get(
                f"{self.base_url}/crumbIssuer/api/json",
                auth=self.auth
            )
            
            if response.status_code == 200:
                crumb_data = response.json()
                return crumb_data['crumbRequestField'], crumb_data['crumb']
        except Exception as e:
            logger.warning(f"Failed to get Jenkins crumb: {e}")
        
        return None
    
    async def _make_authenticated_request(
        self, 
        method: str, 
        url: str, 
        **kwargs
    ) -> httpx.Response:
        """发送经过认证的请求"""
        headers = kwargs.get('headers', {})
        
        # 添加 CSRF 保护
        crumb = await self._get_crumb()
        if crumb:
            headers[crumb[0]] = crumb[1]
        
        kwargs['headers'] = headers
        kwargs['auth'] = self.auth
        
        return await self.client.request(method, url, **kwargs)
    
    def _convert_atomic_steps_to_jenkinsfile(self, steps: List[Dict[str, Any]]) -> str:
        """将原子步骤转换为 Jenkinsfile"""
        stages = []
        
        for i, step in enumerate(steps):
            step_type = step.get('type', '')
            params = step.get('parameters', {})
            stage_name = params.get('stage', f'Stage {i+1}')
            
            # 根据步骤类型生成不同的 Jenkins 代码
            stage_script = self._generate_stage_script(step_type, params)
            
            stage = f"""
        stage('{stage_name}') {{
            steps {{
                {stage_script}
            }}
        }}"""
            stages.append(stage)
        
        return ''.join(stages)
    
    def _generate_stage_script(self, step_type: str, params: Dict[str, Any]) -> str:
        """根据步骤类型生成 Jenkins 脚本"""
        if step_type == 'git_checkout':
            repo_url = params.get('repository_url', '')
            branch = params.get('branch', 'main')
            if repo_url:
                return f"git url: '{repo_url}', branch: '{branch}'"
            else:
                return "checkout scm"
        
        elif step_type == 'shell_script':
            script = params.get('script', 'echo "No script provided"')
            return f"sh '{script}'"
        
        elif step_type == 'maven_build':
            goals = params.get('goals', 'clean compile')
            return f"sh 'mvn {goals}'"
        
        elif step_type == 'gradle_build':
            tasks = params.get('tasks', 'build')
            return f"sh './gradlew {tasks}'"
        
        elif step_type == 'npm_build':
            script = params.get('script', 'build')
            return f"""
                sh 'npm ci'
                sh 'npm run {script}'"""
        
        elif step_type == 'docker_build':
            dockerfile = params.get('dockerfile', 'Dockerfile')
            tag = params.get('tag', 'latest')
            context = params.get('context', '.')
            return f"sh 'docker build -f {dockerfile} -t {tag} {context}'"
        
        elif step_type == 'kubernetes_deploy':
            namespace = params.get('namespace', 'default')
            manifest_path = params.get('manifest_path', 'k8s/')
            return f"sh 'kubectl apply -f {manifest_path} -n {namespace}'"
        
        elif step_type == 'test_execution':
            test_command = params.get('test_command', 'npm test')
            return f"sh '{test_command}'"
        
        elif step_type == 'security_scan':
            target_url = params.get('target_url', 'http://localhost')
            return f"sh 'docker run -t owasp/zap2docker-stable zap-baseline.py -t {target_url}'"
        
        elif step_type == 'artifact_upload':
            paths = params.get('paths', [])
            if paths:
                archive_paths = ', '.join([f"'{path}'" for path in paths])
                return f"archiveArtifacts artifacts: {archive_paths}, allowEmptyArchive: true"
            else:
                return "echo 'No artifacts to upload'"
        
        elif step_type == 'notification':
            message = params.get('message', 'Pipeline completed')
            webhook_url = params.get('webhook_url', '')
            if webhook_url:
                # 避免在f-string中使用反斜杠
                escaped_message = message.replace('"', '\\"')
                curl_data = '{\\"text\\": \\"' + escaped_message + '\\"}'
                return f"""
                sh 'curl -X POST -H "Content-Type: application/json" -d "{curl_data}" {webhook_url}'"""
            else:
                return f"echo '{message}'"
        
        elif step_type == 'environment_setup':
            # 环境变量在流水线级别设置
            return "echo 'Environment variables configured'"
        
        else:
            # 默认脚本步骤
            command = params.get('command', f'echo "Unknown step type: {step_type}"')
            return f"sh '{command}'"
    
    async def create_pipeline_file(self, pipeline_def: PipelineDefinition, project_path: str = "") -> str:
        """创建 Jenkinsfile 内容"""
        stages_content = self._convert_atomic_steps_to_jenkinsfile(pipeline_def.steps)
        
        # 构建环境变量部分
        env_vars = []
        for key, value in pipeline_def.environment.items():
            env_vars.append(f"        {key} = '{value}'")
        
        env_section = f"""
    environment {{
{chr(10).join(env_vars)}
    }}""" if env_vars else ""
        
        # 构建后置处理部分
        post_section = """
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }"""
        
        jenkinsfile = f"""
pipeline {{
    agent any
    
    options {{
        timeout(time: {pipeline_def.timeout // 60}, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }}{env_section}
    
    stages {{{stages_content}
    }}{post_section}
}}"""
        
        return jenkinsfile.strip()
    
    async def create_pipeline(self, definition: PipelineDefinition) -> str:
        """在 Jenkins 中创建流水线任务"""
        job_name = definition.name.replace(' ', '-').lower()
        
        # 生成 Jenkinsfile
        jenkinsfile = await self.create_pipeline_file(definition)
        
        # Jenkins Job 配置 XML
        job_config = f"""<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.40">
  <actions/>
  <description>Generated by AnsFlow CI/CD Platform</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers/>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.92">
    <script>{jenkinsfile}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>"""
        
        # 创建或更新 Job
        url = f"{self.base_url}/job/{job_name}/config.xml"
        
        try:
            # 先检查 Job 是否存在
            check_response = await self.client.get(url, auth=self.auth)
            
            if check_response.status_code == 404:
                # Job 不存在，创建新 Job
                create_url = f"{self.base_url}/createItem?name={job_name}"
                response = await self._make_authenticated_request(
                    'POST',
                    create_url,
                    content=job_config,
                    headers={'Content-Type': 'application/xml'}
                )
            else:
                # Job 存在，更新配置
                response = await self._make_authenticated_request(
                    'POST',
                    url,
                    content=job_config,
                    headers={'Content-Type': 'application/xml'}
                )
            
            if response.status_code in [200, 201]:
                logger.info(f"Jenkins job '{job_name}' created/updated successfully")
                return job_name
            else:
                raise Exception(f"Failed to create Jenkins job: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"Error creating Jenkins job: {e}")
            raise
    
    async def trigger_pipeline(self, pipeline_def: PipelineDefinition, project_path: str = "") -> ExecutionResult:
        """触发 Jenkins 流水线执行"""
        try:
            # 首先创建或更新流水线
            job_name = await self.create_pipeline(pipeline_def)
            
            # 构建参数
            build_params = []
            for key, value in pipeline_def.environment.items():
                build_params.append(f"{key}={value}")
            
            # 触发构建
            if build_params:
                url = f"{self.base_url}/job/{job_name}/buildWithParameters"
                data = '&'.join(build_params)
            else:
                url = f"{self.base_url}/job/{job_name}/build"
                data = ''
            
            response = await self._make_authenticated_request(
                'POST',
                url,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code in [200, 201]:
                # 获取构建编号
                queue_url = response.headers.get('Location')
                if queue_url:
                    build_number = await self._get_build_number_from_queue(queue_url)
                    external_id = f"{job_name}#{build_number}"
                    external_url = f"{self.base_url}/job/{job_name}/{build_number}/"
                else:
                    external_id = f"{job_name}#latest"
                    external_url = f"{self.base_url}/job/{job_name}/"
                
                return ExecutionResult(
                    success=True,
                    external_id=external_id,
                    external_url=external_url,
                    message=f"Jenkins job '{job_name}' triggered successfully"
                )
            
            return ExecutionResult(
                success=False,
                external_id="",
                message=f"Failed to trigger build: {response.status_code}"
            )
        
        except Exception as e:
            logger.error(f"Error triggering Jenkins build: {e}")
            return ExecutionResult(
                success=False,
                external_id="",
                message=str(e)
            )
    
    async def _get_build_number_from_queue(self, queue_url: str) -> str:
        """从队列URL获取构建编号"""
        try:
            # 等待构建从队列中开始
            for _ in range(30):  # 最多等待30秒
                response = await self.client.get(f"{queue_url}api/json", auth=self.auth)
                if response.status_code == 200:
                    queue_data = response.json()
                    if 'executable' in queue_data and queue_data['executable']:
                        return str(queue_data['executable']['number'])
                
                await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"Failed to get build number from queue: {e}")
        
        return "latest"
    
    async def get_pipeline_status(self, execution_id: str) -> Dict[str, Any]:
        """获取 Jenkins 构建状态"""
        try:
            # 解析执行ID (格式: job_name#build_number)
            if '#' in execution_id:
                job_name, build_number = execution_id.split('#', 1)
            else:
                job_name = execution_id
                build_number = 'lastBuild'
            
            url = f"{self.base_url}/job/{job_name}/{build_number}/api/json"
            response = await self.client.get(url, auth=self.auth)
            
            if response.status_code == 200:
                build_data = response.json()
                
                # 映射 Jenkins 状态到统一状态
                jenkins_result = build_data.get('result')
                building = build_data.get('building', False)
                
                if building:
                    status = 'running'
                elif jenkins_result == 'SUCCESS':
                    status = 'success'
                elif jenkins_result == 'FAILURE':
                    status = 'failed'
                elif jenkins_result == 'ABORTED':
                    status = 'cancelled'
                elif jenkins_result is None:
                    status = 'pending'
                else:
                    status = 'failed'
                
                return {
                    'status': status,
                    'external_id': execution_id,
                    'external_url': build_data.get('url', ''),
                    'started_at': datetime.fromtimestamp(build_data.get('timestamp', 0) / 1000).isoformat() if build_data.get('timestamp') else None,
                    'duration': build_data.get('duration', 0) / 1000 if build_data.get('duration') else None,
                    'result': jenkins_result,
                    'building': building,
                    'raw_data': build_data
                }
            else:
                return {
                    'status': 'unknown',
                    'external_id': execution_id,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
        
        except Exception as e:
            logger.error(f"Error getting Jenkins build status: {e}")
            return {
                'status': 'error',
                'external_id': execution_id,
                'error': str(e)
            }
    
    async def cancel_pipeline(self, execution_id: str) -> bool:
        """取消 Jenkins 构建"""
        try:
            if '#' in execution_id:
                job_name, build_number = execution_id.split('#', 1)
            else:
                return False
            
            url = f"{self.base_url}/job/{job_name}/{build_number}/stop"
            response = await self._make_authenticated_request('POST', url)
            
            return response.status_code in [200, 302]
        
        except Exception as e:
            logger.error(f"Error cancelling Jenkins build: {e}")
            return False
    
    async def get_logs(self, execution_id: str) -> str:
        """获取 Jenkins 构建日志"""
        try:
            if '#' in execution_id:
                job_name, build_number = execution_id.split('#', 1)
            else:
                job_name = execution_id
                build_number = 'lastBuild'
            
            url = f"{self.base_url}/job/{job_name}/{build_number}/consoleText"
            response = await self.client.get(url, auth=self.auth)
            
            if response.status_code == 200:
                return response.text
            else:
                return f"Failed to get logs: HTTP {response.status_code}"
        
        except Exception as e:
            logger.error(f"Error getting Jenkins logs: {e}")
            return f"Error getting logs: {str(e)}"
    
    async def health_check(self) -> bool:
        """Jenkins 健康检查"""
        try:
            response = await self.client.get(f"{self.base_url}/api/json", auth=self.auth)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Jenkins health check failed: {e}")
            return False
