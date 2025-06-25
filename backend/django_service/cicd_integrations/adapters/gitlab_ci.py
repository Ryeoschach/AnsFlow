"""
GitLab CI/CD 适配器实现
"""
import asyncio
import logging
from typing import Dict, Any, List
import httpx
import yaml

from .base import CICDAdapter, PipelineDefinition, ExecutionResult

logger = logging.getLogger(__name__)


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
