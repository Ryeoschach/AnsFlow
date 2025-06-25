"""
CI/CD 工具适配器基类和具体实现
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import httpx
import asyncio
import json
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class PipelineDefinition:
    """统一的流水线定义"""
    name: str
    steps: List[Dict[str, Any]]
    triggers: Dict[str, Any]
    environment: Dict[str, str]
    artifacts: List[str] = None
    timeout: int = 3600  # 默认1小时超时

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    external_id: str
    external_url: str = ""
    message: str = ""
    logs: str = ""
    artifacts: List[str] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []


class CICDAdapter(ABC):
    """CI/CD 工具适配器基类"""
    
    def __init__(self, base_url: str, username: str = "", token: str = "", **kwargs):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.token = token
        self.config = kwargs
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @abstractmethod
    async def create_pipeline(self, definition: PipelineDefinition) -> str:
        """创建流水线，返回流水线ID"""
        pass
    
    @abstractmethod
    async def trigger_pipeline(self, pipeline_id: str, params: Dict[str, Any]) -> ExecutionResult:
        """触发流水线执行"""
        pass
    
    @abstractmethod
    async def get_pipeline_status(self, execution_id: str) -> Dict[str, Any]:
        """获取流水线状态"""
        pass
    
    @abstractmethod
    async def cancel_pipeline(self, execution_id: str) -> bool:
        """取消流水线执行"""
        pass
    
    @abstractmethod
    async def get_logs(self, execution_id: str) -> str:
        """获取执行日志"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass


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
    
    def _convert_to_jenkinsfile(self, definition: PipelineDefinition) -> str:
        """将统一定义转换为 Jenkinsfile"""
        stages = []
        
        for i, step in enumerate(definition.steps):
            stage_name = step.get('name', f'Stage {i+1}')
            step_type = step.get('type', 'custom')
            
            # 根据步骤类型生成不同的 Jenkins 代码
            stage_script = self._generate_stage_script(step_type, step)
            
            stage = f"""
        stage('{stage_name}') {{
            steps {{
                {stage_script}
            }}
        }}"""
            stages.append(stage)
        
        # 构建环境变量部分
        env_vars = []
        for key, value in definition.environment.items():
            env_vars.append(f"        {key} = '{value}'")
        
        env_section = f"""
    environment {{
{chr(10).join(env_vars)}
    }}""" if env_vars else ""
        
        # 构建后置处理部分
        post_section = """
    post {
        always {
            // 清理工作空间
            cleanWs()
        }
        success {
            // 成功时的操作
            echo 'Pipeline completed successfully!'
        }
        failure {
            // 失败时的操作
            echo 'Pipeline failed!'
        }
    }"""
        
        jenkinsfile = f"""
pipeline {{
    agent any
    
    options {{
        timeout(time: {definition.timeout // 60}, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }}{env_section}
    
    stages {{{(''.join(stages))
    }}}{post_section}
}}"""
        
        return jenkinsfile.strip()
    
    def _generate_stage_script(self, step_type: str, step_data: Dict[str, Any]) -> str:
        """根据步骤类型生成 Jenkins 脚本"""
        params = step_data.get('parameters', {})
        
        if step_type == 'fetch_code':
            repo_url = params.get('repository_url', '')
            branch = params.get('branch', 'main')
            return f"""
                checkout scm
                // 或者指定具体的仓库
                // git url: '{repo_url}', branch: '{branch}'"""
        
        elif step_type == 'build':
            build_tool = params.get('tool', 'make')
            command = params.get('command', 'build')
            return f"""
                sh '{build_tool} {command}'"""
        
        elif step_type == 'test':
            test_command = params.get('command', 'make test')
            coverage = params.get('coverage', False)
            script = f"sh '{test_command}'"
            if coverage:
                script += """
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'coverage',
                    reportFiles: 'index.html',
                    reportName: 'Coverage Report'
                ])"""
            return script
        
        elif step_type == 'deploy':
            deploy_command = params.get('command', '')
            environment = params.get('environment', 'staging')
            return f"""
                sh '{deploy_command}'
                echo 'Deployed to {environment}'"""
        
        elif step_type == 'security_scan':
            scan_tool = params.get('tool', 'sonarqube')
            if scan_tool == 'sonarqube':
                return """
                withSonarQubeEnv('SonarQube') {
                    sh 'mvn sonar:sonar'
                }"""
            else:
                return f"sh '{params.get('command', 'security-scan')}'"
        
        elif step_type == 'notify':
            return f"""
                echo 'Notification: {params.get('message', 'Step completed')}'"""
        
        else:  # custom
            commands = params.get('commands', [])
            if isinstance(commands, list):
                return '\n                '.join([f"sh '{cmd}'" for cmd in commands])
            else:
                return f"sh '{commands}'"
    
    async def create_pipeline(self, definition: PipelineDefinition) -> str:
        """在 Jenkins 中创建流水线任务"""
        job_name = definition.name.replace(' ', '-').lower()
        
        # 生成 Jenkinsfile
        jenkinsfile = self._convert_to_jenkinsfile(definition)
        
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
                # Job 不存在，创建新的
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
    
    async def trigger_pipeline(self, pipeline_id: str, params: Dict[str, Any]) -> ExecutionResult:
        """触发 Jenkins 任务执行"""
        try:
            # 构建参数
            build_params = []
            for key, value in params.items():
                build_params.append(f"{key}={value}")
            
            # 触发构建
            if build_params:
                url = f"{self.base_url}/job/{pipeline_id}/buildWithParameters"
                data = '&'.join(build_params)
            else:
                url = f"{self.base_url}/job/{pipeline_id}/build"
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
                    # 等待构建开始，获取构建编号
                    build_number = await self._get_build_number_from_queue(queue_url)
                    external_url = f"{self.base_url}/job/{pipeline_id}/{build_number}/"
                    
                    return ExecutionResult(
                        success=True,
                        external_id=f"{pipeline_id}#{build_number}",
                        external_url=external_url,
                        message="Build triggered successfully"
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
                    executable = queue_data.get('executable')
                    if executable:
                        return str(executable['number'])
                
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


class GitLabCIAdapter(CICDAdapter):
    """GitLab CI 适配器"""
    
    def __init__(self, base_url: str, token: str, project_id: str = "", **kwargs):
        super().__init__(base_url, token=token, **kwargs)
        self.project_id = project_id
        self.headers = {
            'PRIVATE-TOKEN': token,
            'Content-Type': 'application/json'
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)
    
    def _convert_atomic_steps_to_gitlab_ci(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """将原子步骤转换为 GitLab CI 配置"""
        gitlab_ci = {
            'stages': [],
            'variables': {},
            'before_script': []
        }
        
        # 收集所有阶段
        stages_seen = set()
        jobs = {}
        
        for i, step in enumerate(steps):
            step_type = step.get('type', '')
            params = step.get('parameters', {})
            stage_name = params.get('stage', f'stage_{i+1}')
            
            if stage_name not in stages_seen:
                gitlab_ci['stages'].append(stage_name)
                stages_seen.add(stage_name)
            
            job_name = f"{step_type}_{i+1}"
            job_config = {
                'stage': stage_name,
                'script': []
            }
            
            # 根据步骤类型生成脚本
            if step_type == 'git_checkout':
                # GitLab CI 自动处理 git checkout
                job_config['script'] = ['echo "Git checkout handled automatically"']
                if params.get('branch'):
                    job_config['only'] = {'refs': [params['branch']]}
            
            elif step_type == 'shell_script':
                job_config['script'] = [params.get('script', 'echo "No script provided"')]
            
            elif step_type == 'maven_build':
                job_config['image'] = 'maven:3.8.4-openjdk-11'
                job_config['script'] = [
                    f"mvn {params.get('goals', 'clean compile')}"
                ]
                job_config['cache'] = {
                    'paths': ['.m2/repository/']
                }
            
            elif step_type == 'gradle_build':
                job_config['image'] = 'gradle:7.4.2-jdk11'
                job_config['script'] = [
                    f"gradle {params.get('tasks', 'build')}"
                ]
                job_config['cache'] = {
                    'paths': ['.gradle/']
                }
            
            elif step_type == 'npm_build':
                job_config['image'] = 'node:16'
                job_config['script'] = [
                    'npm ci',
                    f"npm run {params.get('script', 'build')}"
                ]
                job_config['cache'] = {
                    'paths': ['node_modules/']
                }
            
            elif step_type == 'docker_build':
                job_config['image'] = 'docker:20.10.16'
                job_config['services'] = ['docker:20.10.16-dind']
                dockerfile = params.get('dockerfile', 'Dockerfile')
                tag = params.get('tag', 'latest')
                context = params.get('context', '.')
                job_config['script'] = [
                    f"docker build -f {dockerfile} -t {tag} {context}"
                ]
                job_config['variables'] = {
                    'DOCKER_DRIVER': 'overlay2',
                    'DOCKER_TLS_CERTDIR': '/certs'
                }
            
            elif step_type == 'kubernetes_deploy':
                job_config['image'] = 'bitnami/kubectl:latest'
                namespace = params.get('namespace', 'default')
                manifest_path = params.get('manifest_path', 'k8s/')
                job_config['script'] = [
                    f"kubectl apply -f {manifest_path} -n {namespace}"
                ]
            
            elif step_type == 'test_execution':
                test_command = params.get('test_command', 'npm test')
                job_config['script'] = [test_command]
                job_config['artifacts'] = {
                    'reports': {
                        'junit': params.get('report_path', 'test-results.xml')
                    },
                    'when': 'always'
                }
            
            elif step_type == 'security_scan':
                job_config['image'] = 'owasp/zap2docker-stable'
                target_url = params.get('target_url', 'http://localhost')
                job_config['script'] = [
                    f"zap-baseline.py -t {target_url}"
                ]
                job_config['allow_failure'] = True
            
            elif step_type == 'artifact_upload':
                paths = params.get('paths', [])
                job_config['artifacts'] = {
                    'paths': paths,
                    'expire_in': params.get('retention', '1 week')
                }
                job_config['script'] = ['echo "Artifacts configured"']
            
            elif step_type == 'notification':
                # GitLab CI 可以通过 webhook 或集成发送通知
                message = params.get('message', 'Pipeline completed')
                job_config['script'] = [f'echo "{message}"']
                if params.get('webhook_url'):
                    job_config['script'].append(
                        f"curl -X POST -H 'Content-Type: application/json' "
                        f"-d '{{\"text\": \"{message}\"}}' {params['webhook_url']}"
                    )
            
            elif step_type == 'environment_setup':
                variables = params.get('variables', {})
                for key, value in variables.items():
                    gitlab_ci['variables'][key] = value
                job_config['script'] = ['echo "Environment variables set"']
            
            else:
                # 默认脚本步骤
                job_config['script'] = [params.get('command', 'echo "Unknown step type"')]
            
            # 添加依赖关系
            if params.get('depends_on'):
                job_config['needs'] = params['depends_on']
            
            # 添加条件执行
            if params.get('when'):
                job_config['when'] = params['when']
            
            # 添加环境变量
            if params.get('environment_variables'):
                if 'variables' not in job_config:
                    job_config['variables'] = {}
                job_config['variables'].update(params['environment_variables'])
            
            jobs[job_name] = job_config
        
        # 合并作业到 GitLab CI 配置
        gitlab_ci.update(jobs)
        
        return gitlab_ci
    
    async def create_pipeline_file(self, pipeline_def: PipelineDefinition, project_path: str = "") -> str:
        """创建 .gitlab-ci.yml 文件内容"""
        gitlab_ci = self._convert_atomic_steps_to_gitlab_ci(pipeline_def.steps)
        
        # 添加全局配置
        if pipeline_def.environment:
            gitlab_ci['variables'].update(pipeline_def.environment)
        
        # 添加触发器配置
        if pipeline_def.triggers:
            if pipeline_def.triggers.get('schedule'):
                # GitLab CI 使用 pipeline schedules，这里只是注释
                gitlab_ci['# schedule'] = pipeline_def.triggers['schedule']
            
            if pipeline_def.triggers.get('webhook'):
                gitlab_ci['workflow'] = {
                    'rules': [
                        {'if': '$CI_PIPELINE_SOURCE == "web"'},
                        {'if': '$CI_PIPELINE_SOURCE == "api"'}
                    ]
                }
        
        # 设置超时
        if pipeline_def.timeout != 3600:
            gitlab_ci['default'] = {
                'timeout': f"{pipeline_def.timeout // 60}m"
            }
        
        import yaml
        return yaml.dump(gitlab_ci, default_flow_style=False, allow_unicode=True)
    
    async def trigger_pipeline(self, pipeline_def: PipelineDefinition, project_path: str = "") -> ExecutionResult:
        """触发 GitLab CI 流水线"""
        try:
            project_id = self.project_id or project_path
            if not project_id:
                return ExecutionResult(
                    success=False,
                    external_id="",
                    message="Project ID is required for GitLab CI"
                )
            
            # 创建流水线
            url = f"{self.base_url}/api/v4/projects/{project_id}/pipeline"
            
            payload = {
                'ref': 'main',  # 默认分支
                'variables': []
            }
            
            # 添加环境变量
            for key, value in pipeline_def.environment.items():
                payload['variables'].append({
                    'key': key,
                    'value': value
                })
            
            # 从触发器中获取分支信息
            if pipeline_def.triggers.get('branch'):
                payload['ref'] = pipeline_def.triggers['branch']
            
            response = await self.client.post(url, json=payload)
            
            if response.status_code == 201:
                pipeline_data = response.json()
                pipeline_id = pipeline_data['id']
                
                return ExecutionResult(
                    success=True,
                    external_id=str(pipeline_id),
                    external_url=pipeline_data.get('web_url', ''),
                    message=f"GitLab CI pipeline {pipeline_id} triggered successfully"
                )
            else:
                return ExecutionResult(
                    success=False,
                    external_id="",
                    message=f"Failed to trigger pipeline: HTTP {response.status_code} - {response.text}"
                )
        
        except Exception as e:
            logger.error(f"Error triggering GitLab CI pipeline: {e}")
            return ExecutionResult(
                success=False,
                external_id="",
                message=f"Error triggering pipeline: {str(e)}"
            )
    
    async def get_pipeline_status(self, execution_id: str) -> Dict[str, Any]:
        """获取 GitLab CI 流水线状态"""
        try:
            project_id = self.project_id
            if not project_id:
                return {
                    'status': 'error',
                    'external_id': execution_id,
                    'error': 'Project ID not configured'
                }
            
            url = f"{self.base_url}/api/v4/projects/{project_id}/pipelines/{execution_id}"
            response = await self.client.get(url)
            
            if response.status_code == 200:
                pipeline_data = response.json()
                
                # 映射 GitLab CI 状态到统一状态
                gitlab_status = pipeline_data.get('status')
                status_mapping = {
                    'created': 'pending',
                    'waiting_for_resource': 'pending',
                    'preparing': 'pending',
                    'pending': 'pending',
                    'running': 'running',
                    'success': 'success',
                    'failed': 'failed',
                    'canceled': 'cancelled',
                    'skipped': 'cancelled',
                    'manual': 'pending'
                }
                
                status = status_mapping.get(gitlab_status, 'unknown')
                
                return {
                    'status': status,
                    'external_id': execution_id,
                    'external_url': pipeline_data.get('web_url', ''),
                    'started_at': pipeline_data.get('created_at'),
                    'finished_at': pipeline_data.get('finished_at'),
                    'duration': pipeline_data.get('duration'),
                    'result': gitlab_status,
                    'ref': pipeline_data.get('ref'),
                    'sha': pipeline_data.get('sha'),
                    'raw_data': pipeline_data
                }
            else:
                return {
                    'status': 'unknown',
                    'external_id': execution_id,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
        
        except Exception as e:
            logger.error(f"Error getting GitLab CI pipeline status: {e}")
            return {
                'status': 'error',
                'external_id': execution_id,
                'error': str(e)
            }
    
    async def cancel_pipeline(self, execution_id: str) -> bool:
        """取消 GitLab CI 流水线"""
        try:
            project_id = self.project_id
            if not project_id:
                return False
            
            url = f"{self.base_url}/api/v4/projects/{project_id}/pipelines/{execution_id}/cancel"
            response = await self.client.post(url)
            
            return response.status_code in [200, 201]
        
        except Exception as e:
            logger.error(f"Error cancelling GitLab CI pipeline: {e}")
            return False
    
    async def get_logs(self, execution_id: str) -> str:
        """获取 GitLab CI 流水线日志"""
        try:
            project_id = self.project_id
            if not project_id:
                return "Project ID not configured"
            
            # 获取流水线的所有作业
            jobs_url = f"{self.base_url}/api/v4/projects/{project_id}/pipelines/{execution_id}/jobs"
            jobs_response = await self.client.get(jobs_url)
            
            if jobs_response.status_code != 200:
                return f"Failed to get jobs: HTTP {jobs_response.status_code}"
            
            jobs = jobs_response.json()
            all_logs = []
            
            for job in jobs:
                job_id = job['id']
                job_name = job['name']
                
                # 获取每个作业的日志
                trace_url = f"{self.base_url}/api/v4/projects/{project_id}/jobs/{job_id}/trace"
                trace_response = await self.client.get(trace_url)
                
                if trace_response.status_code == 200:
                    job_logs = trace_response.text
                    all_logs.append(f"=== Job: {job_name} ===\n{job_logs}\n")
                else:
                    all_logs.append(f"=== Job: {job_name} ===\nFailed to get logs\n")
            
            return "\n".join(all_logs)
        
        except Exception as e:
            logger.error(f"Error getting GitLab CI logs: {e}")
            return f"Error getting logs: {str(e)}"
    
    async def health_check(self) -> bool:
        """GitLab CI 健康检查"""
        try:
            # 检查 GitLab API 是否可访问
            response = await self.client.get(f"{self.base_url}/api/v4/version")
            if response.status_code != 200:
                return False
            
            # 如果配置了项目ID，检查项目是否可访问
            if self.project_id:
                project_response = await self.client.get(f"{self.base_url}/api/v4/projects/{self.project_id}")
                return project_response.status_code == 200
            
            return True
        except Exception as e:
            logger.error(f"GitLab CI health check failed: {e}")
            return False


class GitHubActionsAdapter(CICDAdapter):
    """GitHub Actions 适配器"""
    
    def __init__(self, base_url: str, token: str, owner: str = "", repo: str = "", **kwargs):
        super().__init__(base_url, token=token, **kwargs)
        self.owner = owner
        self.repo = repo
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
            'Content-Type': 'application/json'
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)
    
    def _convert_atomic_steps_to_github_actions(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """将原子步骤转换为 GitHub Actions 工作流配置"""
        workflow = {
            'name': 'AnsFlow Pipeline',
            'on': {
                'push': {'branches': ['main']},
                'pull_request': {'branches': ['main']},
                'workflow_dispatch': {}
            },
            'jobs': {}
        }
        
        # 按阶段分组步骤
        stages = {}
        for i, step in enumerate(steps):
            step_type = step.get('type', '')
            params = step.get('parameters', {})
            stage_name = params.get('stage', f'stage_{i+1}')
            
            if stage_name not in stages:
                stages[stage_name] = []
            
            stages[stage_name].append((step_type, params, i))
        
        # 为每个阶段创建作业
        for stage_name, stage_steps in stages.items():
            job_name = f"{stage_name}_job"
            job_config = {
                'runs-on': 'ubuntu-latest',
                'steps': []
            }
            
            # 添加默认的 checkout 步骤
            job_config['steps'].append({
                'name': 'Checkout code',
                'uses': 'actions/checkout@v4'
            })
            
            # 转换阶段中的每个步骤
            for step_type, params, step_index in stage_steps:
                step_name = f"{step_type}_{step_index+1}"
                
                if step_type == 'git_checkout':
                    # GitHub Actions 自动处理 checkout
                    if params.get('branch') and params['branch'] != 'main':
                        job_config['steps'][-1]['with'] = {
                            'ref': params['branch']
                        }
                
                elif step_type == 'shell_script':
                    job_config['steps'].append({
                        'name': step_name,
                        'run': params.get('script', 'echo "No script provided"')
                    })
                
                elif step_type == 'maven_build':
                    job_config['steps'].extend([
                        {
                            'name': 'Set up JDK',
                            'uses': 'actions/setup-java@v3',
                            'with': {
                                'java-version': '11',
                                'distribution': 'temurin'
                            }
                        },
                        {
                            'name': f'Cache Maven dependencies',
                            'uses': 'actions/cache@v3',
                            'with': {
                                'path': '~/.m2',
                                'key': "${{ runner.os }}-m2-${{ hashFiles('**/pom.xml') }}"
                            }
                        },
                        {
                            'name': step_name,
                            'run': f"mvn {params.get('goals', 'clean compile')}"
                        }
                    ])
                
                elif step_type == 'gradle_build':
                    job_config['steps'].extend([
                        {
                            'name': 'Set up JDK',
                            'uses': 'actions/setup-java@v3',
                            'with': {
                                'java-version': '11',
                                'distribution': 'temurin'
                            }
                        },
                        {
                            'name': 'Setup Gradle',
                            'uses': 'gradle/gradle-build-action@v2'
                        },
                        {
                            'name': step_name,
                            'run': f"./gradlew {params.get('tasks', 'build')}"
                        }
                    ])
                
                elif step_type == 'npm_build':
                    node_version = params.get('node_version', '18')
                    job_config['steps'].extend([
                        {
                            'name': 'Setup Node.js',
                            'uses': 'actions/setup-node@v3',
                            'with': {
                                'node-version': node_version,
                                'cache': 'npm'
                            }
                        },
                        {
                            'name': 'Install dependencies',
                            'run': 'npm ci'
                        },
                        {
                            'name': step_name,
                            'run': f"npm run {params.get('script', 'build')}"
                        }
                    ])
                
                elif step_type == 'docker_build':
                    dockerfile = params.get('dockerfile', 'Dockerfile')
                    tag = params.get('tag', 'latest')
                    context = params.get('context', '.')
                    job_config['steps'].append({
                        'name': step_name,
                        'run': f"docker build -f {dockerfile} -t {tag} {context}"
                    })
                
                elif step_type == 'kubernetes_deploy':
                    namespace = params.get('namespace', 'default')
                    manifest_path = params.get('manifest_path', 'k8s/')
                    job_config['steps'].extend([
                        {
                            'name': 'Setup kubectl',
                            'uses': 'azure/setup-kubectl@v3'
                        },
                        {
                            'name': step_name,
                            'run': f"kubectl apply -f {manifest_path} -n {namespace}"
                        }
                    ])
                
                elif step_type == 'test_execution':
                    test_command = params.get('test_command', 'npm test')
                    job_config['steps'].append({
                        'name': step_name,
                        'run': test_command
                    })
                    
                    # 添加测试报告上传
                    if params.get('report_path'):
                        job_config['steps'].append({
                            'name': f'Upload test results',
                            'uses': 'actions/upload-artifact@v3',
                            'with': {
                                'name': 'test-results',
                                'path': params['report_path']
                            },
                            'if': 'always()'
                        })
                
                elif step_type == 'security_scan':
                    target_url = params.get('target_url', 'http://localhost')
                    job_config['steps'].append({
                        'name': step_name,
                        'run': f"docker run -t owasp/zap2docker-stable zap-baseline.py -t {target_url}",
                        'continue-on-error': True
                    })
                
                elif step_type == 'artifact_upload':
                    paths = params.get('paths', [])
                    if paths:
                        job_config['steps'].append({
                            'name': step_name,
                            'uses': 'actions/upload-artifact@v3',
                            'with': {
                                'name': 'build-artifacts',
                                'path': '\n'.join(paths),
                                'retention-days': self._parse_retention_days(params.get('retention', '7'))
                            }
                        })
                
                elif step_type == 'notification':
                    message = params.get('message', 'Pipeline completed')
                    if params.get('webhook_url'):
                        job_config['steps'].append({
                            'name': step_name,
                            'run': f"curl -X POST -H 'Content-Type: application/json' -d '{{\"text\": \"{message}\"}}' {params['webhook_url']}"
                        })
                    else:
                        job_config['steps'].append({
                            'name': step_name,
                            'run': f'echo "{message}"'
                        })
                
                elif step_type == 'environment_setup':
                    variables = params.get('variables', {})
                    if variables:
                        if 'env' not in job_config:
                            job_config['env'] = {}
                        job_config['env'].update(variables)
                
                else:
                    # 默认脚本步骤
                    job_config['steps'].append({
                        'name': step_name,
                        'run': params.get('command', f'echo "Unknown step type: {step_type}"')
                    })
            
            workflow['jobs'][job_name] = job_config
        
        return workflow
    
    def _parse_retention_days(self, retention: str) -> int:
        """解析保留期限为天数"""
        if 'day' in retention:
            return int(retention.split()[0])
        elif 'week' in retention:
            return int(retention.split()[0]) * 7
        elif 'month' in retention:
            return int(retention.split()[0]) * 30
        else:
            return 7  # 默认7天
    
    async def create_pipeline_file(self, pipeline_def: PipelineDefinition, project_path: str = "") -> str:
        """创建 GitHub Actions 工作流文件内容"""
        workflow = self._convert_atomic_steps_to_github_actions(pipeline_def.steps)
        
        # 设置工作流名称
        workflow['name'] = pipeline_def.name
        
        # 添加环境变量
        if pipeline_def.environment:
            workflow['env'] = pipeline_def.environment
        
        # 配置触发器
        if pipeline_def.triggers:
            on_config = {}
            
            if pipeline_def.triggers.get('branch'):
                on_config['push'] = {'branches': [pipeline_def.triggers['branch']]}
                on_config['pull_request'] = {'branches': [pipeline_def.triggers['branch']]}
            
            if pipeline_def.triggers.get('schedule'):
                on_config['schedule'] = [{'cron': pipeline_def.triggers['schedule']}]
            
            if pipeline_def.triggers.get('webhook') or pipeline_def.triggers.get('manual'):
                on_config['workflow_dispatch'] = {}
            
            if on_config:
                workflow['on'] = on_config
        
        import yaml
        return yaml.dump(workflow, default_flow_style=False, allow_unicode=True)
    
    async def trigger_pipeline(self, pipeline_def: PipelineDefinition, project_path: str = "") -> ExecutionResult:
        """触发 GitHub Actions 工作流"""
        try:
            repo_path = project_path or f"{self.owner}/{self.repo}"
            if '/' not in repo_path:
                return ExecutionResult(
                    success=False,
                    external_id="",
                    message="Repository path must be in format 'owner/repo'"
                )
            
            owner, repo = repo_path.split('/', 1)
            
            # 触发 workflow_dispatch 事件
            url = f"{self.base_url}/repos/{owner}/{repo}/actions/workflows/.github/workflows/ansflow.yml/dispatches"
            
            payload = {
                'ref': 'main',  # 默认分支
                'inputs': {}
            }
            
            # 添加环境变量作为输入
            for key, value in pipeline_def.environment.items():
                payload['inputs'][key] = str(value)
            
            # 从触发器中获取分支信息
            if pipeline_def.triggers.get('branch'):
                payload['ref'] = pipeline_def.triggers['branch']
            
            response = await self.client.post(url, json=payload)
            
            if response.status_code == 204:
                # GitHub Actions 不返回运行ID，需要查询最新的运行
                await asyncio.sleep(2)  # 等待工作流启动
                
                runs_url = f"{self.base_url}/repos/{owner}/{repo}/actions/runs"
                runs_response = await self.client.get(runs_url, params={'per_page': 1})
                
                if runs_response.status_code == 200:
                    runs_data = runs_response.json()
                    if runs_data['workflow_runs']:
                        run = runs_data['workflow_runs'][0]
                        return ExecutionResult(
                            success=True,
                            external_id=str(run['id']),
                            external_url=run['html_url'],
                            message=f"GitHub Actions workflow triggered successfully"
                        )
                
                return ExecutionResult(
                    success=True,
                    external_id="unknown",
                    message="Workflow triggered but run ID not available"
                )
            else:
                return ExecutionResult(
                    success=False,
                    external_id="",
                    message=f"Failed to trigger workflow: HTTP {response.status_code} - {response.text}"
                )
        
        except Exception as e:
            logger.error(f"Error triggering GitHub Actions workflow: {e}")
            return ExecutionResult(
                success=False,
                external_id="",
                message=f"Error triggering workflow: {str(e)}"
            )
    
    async def get_pipeline_status(self, execution_id: str) -> Dict[str, Any]:
        """获取 GitHub Actions 工作流状态"""
        try:
            repo_path = f"{self.owner}/{self.repo}"
            url = f"{self.base_url}/repos/{repo_path}/actions/runs/{execution_id}"
            response = await self.client.get(url)
            
            if response.status_code == 200:
                run_data = response.json()
                
                # 映射 GitHub Actions 状态到统一状态
                github_status = run_data.get('status')
                github_conclusion = run_data.get('conclusion')
                
                if github_status == 'completed':
                    if github_conclusion == 'success':
                        status = 'success'
                    elif github_conclusion == 'failure':
                        status = 'failed'
                    elif github_conclusion == 'cancelled':
                        status = 'cancelled'
                    else:
                        status = 'failed'
                elif github_status in ['queued', 'waiting']:
                    status = 'pending'
                elif github_status == 'in_progress':
                    status = 'running'
                else:
                    status = 'unknown'
                
                return {
                    'status': status,
                    'external_id': execution_id,
                    'external_url': run_data.get('html_url', ''),
                    'started_at': run_data.get('run_started_at'),
                    'finished_at': run_data.get('updated_at') if github_status == 'completed' else None,
                    'duration': None,  # GitHub 不直接提供持续时间
                    'result': github_conclusion,
                    'workflow_status': github_status,
                    'head_branch': run_data.get('head_branch'),
                    'head_sha': run_data.get('head_sha'),
                    'raw_data': run_data
                }
            else:
                return {
                    'status': 'unknown',
                    'external_id': execution_id,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
        
        except Exception as e:
            logger.error(f"Error getting GitHub Actions run status: {e}")
            return {
                'status': 'error',
                'external_id': execution_id,
                'error': str(e)
            }
    
    async def cancel_pipeline(self, execution_id: str) -> bool:
        """取消 GitHub Actions 工作流运行"""
        try:
            repo_path = f"{self.owner}/{self.repo}"
            url = f"{self.base_url}/repos/{repo_path}/actions/runs/{execution_id}/cancel"
            response = await self.client.post(url)
            
            return response.status_code in [202]
        
        except Exception as e:
            logger.error(f"Error cancelling GitHub Actions run: {e}")
            return False
    
    async def get_logs(self, execution_id: str) -> str:
        """获取 GitHub Actions 工作流日志"""
        try:
            repo_path = f"{self.owner}/{self.repo}"
            
            # 获取工作流运行的作业
            jobs_url = f"{self.base_url}/repos/{repo_path}/actions/runs/{execution_id}/jobs"
            jobs_response = await self.client.get(jobs_url)
            
            if jobs_response.status_code != 200:
                return f"Failed to get jobs: HTTP {jobs_response.status_code}"
            
            jobs = jobs_response.json().get('jobs', [])
            all_logs = []
            
            for job in jobs:
                job_id = job['id']
                job_name = job['name']
                
                # 获取每个作业的日志
                logs_url = f"{self.base_url}/repos/{repo_path}/actions/jobs/{job_id}/logs"
                logs_response = await self.client.get(logs_url)
                
                if logs_response.status_code == 200:
                    job_logs = logs_response.text
                    all_logs.append(f"=== Job: {job_name} ===\n{job_logs}\n")
                else:
                    all_logs.append(f"=== Job: {job_name} ===\nFailed to get logs\n")
            
            return "\n".join(all_logs)
        
        except Exception as e:
            logger.error(f"Error getting GitHub Actions logs: {e}")
            return f"Error getting logs: {str(e)}"
    
    async def health_check(self) -> bool:
        """GitHub Actions 健康检查"""
        try:
            # 检查 GitHub API 是否可访问
            response = await self.client.get(f"{self.base_url}/user")
            if response.status_code != 200:
                return False
            
            # 如果配置了仓库，检查仓库是否可访问
            if self.owner and self.repo:
                repo_response = await self.client.get(f"{self.base_url}/repos/{self.owner}/{self.repo}")
                return repo_response.status_code == 200
            
            return True
        except Exception as e:
            logger.error(f"GitHub Actions health check failed: {e}")
            return False


class CICDAdapterFactory:
    """CI/CD 适配器工厂"""
    
    _adapters = {
        'jenkins': JenkinsAdapter,
        'gitlab_ci': GitLabCIAdapter,
        'github_actions': GitHubActionsAdapter,
        # 后续添加其他工具适配器
        # 'circleci': CircleCIAdapter,
        # 'azure_devops': AzureDevOpsAdapter,
    }
    
    @classmethod
    def create_adapter(cls, tool_type: str, **config) -> CICDAdapter:
        """根据工具类型创建适配器"""
        adapter_class = cls._adapters.get(tool_type)
        if not adapter_class:
            raise ValueError(f"Unsupported CI/CD tool: {tool_type}")
        
        return adapter_class(**config)
    
    @classmethod
    def register_adapter(cls, tool_type: str, adapter_class: type):
        """注册新的适配器"""
        cls._adapters[tool_type] = adapter_class
    
    @classmethod
    def get_supported_tools(cls) -> List[str]:
        """获取支持的工具列表"""
        return list(cls._adapters.keys())
