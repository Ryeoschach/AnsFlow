"""
GitHub Actions CI/CD 适配器实现
"""
import asyncio
import logging
from typing import Dict, Any, List
import httpx
import yaml

from .base import CICDAdapter, PipelineDefinition, ExecutionResult

logger = logging.getLogger(__name__)


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
