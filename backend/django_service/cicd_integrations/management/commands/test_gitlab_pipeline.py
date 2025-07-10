"""
测试 GitLab CI 流水线执行的管理命令
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import asyncio
import os
import time
from cicd_integrations.models import CICDTool, AtomicStep, PipelineExecution
from cicd_integrations.services import UnifiedCICDEngine
from cicd_integrations.adapters import PipelineDefinition


class Command(BaseCommand):
    help = '测试 GitLab CI 流水线执行'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tool-id',
            type=int,
            help='要使用的 GitLab CI 工具 ID'
        )
        parser.add_argument(
            '--project-id',
            type=str,
            default=os.getenv('GITLAB_PROJECT_ID', ''),
            help='GitLab 项目 ID'
        )
        parser.add_argument(
            '--branch',
            type=str,
            default='main',
            help='要构建的分支 (默认: main)'
        )
        parser.add_argument(
            '--steps',
            type=str,
            nargs='+',
            default=['git_checkout', 'shell_script', 'test_execution'],
            help='要执行的原子步骤类型列表'
        )
        parser.add_argument(
            '--monitor',
            action='store_true',
            help='监控流水线执行状态直到完成'
        )

    def handle(self, *args, **options):
        tool_id = options['tool_id']
        project_id = options['project_id']
        branch = options['branch']
        step_types = options['steps']
        monitor = options['monitor']
        
        if not project_id:
            self.stdout.write(
                self.style.ERROR('GitLab project ID is required. Use --project-id or set GITLAB_PROJECT_ID environment variable.')
            )
            return
        
        # 获取 GitLab CI 工具
        if tool_id:
            try:
                tool = CICDTool.objects.get(id=tool_id, tool_type='gitlab_ci')
            except CICDTool.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'GitLab CI tool with ID {tool_id} not found'))
                return
        else:
            # 查找第一个可用的 GitLab CI 工具
            tool = CICDTool.objects.filter(tool_type='gitlab_ci', status__in=['active', 'authenticated']).first()
            if not tool:
                self.stdout.write(self.style.ERROR('No active GitLab CI tool found. Please register one first.'))
                return
        
        self.stdout.write(f'使用 GitLab CI 工具: {tool.name} (ID: {tool.id})')
        self.stdout.write(f'项目 ID: {project_id}')
        self.stdout.write(f'分支: {branch}')
        self.stdout.write(f'步骤类型: {", ".join(step_types)}')
        
        # 运行异步测试
        asyncio.run(self._test_pipeline_execution(tool, project_id, branch, step_types, monitor))

    async def _test_pipeline_execution(self, tool: CICDTool, project_id: str, branch: str, step_types: list, monitor: bool):
        """异步测试流水线执行"""
        try:
            # 1. 准备原子步骤
            self.stdout.write('\n1. 准备原子步骤...')
            atomic_steps = []
            
            for step_type in step_types:
                step = AtomicStep.objects.filter(step_type=step_type, visibility='public').first()
                if step:
                    atomic_steps.append(step)
                    self.stdout.write(f'  ✓ 找到步骤: {step.name} ({step.step_type})')
                else:
                    self.stdout.write(f'  ⚠ 未找到步骤类型: {step_type}，使用默认配置')
                    # 创建默认步骤配置
                    default_params = self._get_default_step_params(step_type, project_id, branch)
                    atomic_steps.append({
                        'type': step_type,
                        'parameters': default_params
                    })
            
            if not atomic_steps:
                self.stdout.write(self.style.ERROR('没有可用的原子步骤'))
                return
            
            # 2. 创建流水线定义
            self.stdout.write('\n2. 创建流水线定义...')
            
            # 准备步骤列表
            pipeline_steps = []
            for i, step in enumerate(atomic_steps):
                if isinstance(step, AtomicStep):
                    # 数据库中的步骤
                    step_config = {
                        'type': step.step_type,
                        'parameters': step.default_parameters.copy()
                    }
                    # 为特定步骤添加项目相关参数
                    if step.step_type == 'git_checkout':
                        step_config['parameters']['branch'] = branch
                    elif step.step_type == 'shell_script':
                        step_config['parameters']['script'] = 'echo "Hello from GitLab CI Pipeline!"'
                        step_config['parameters']['stage'] = 'build'
                    elif step.step_type == 'test_execution':
                        step_config['parameters']['test_command'] = 'echo "Running tests..."'
                        step_config['parameters']['stage'] = 'test'
                else:
                    # 默认配置的步骤
                    step_config = step
                
                pipeline_steps.append(step_config)
            
            pipeline_def = PipelineDefinition(
                name=f'test-pipeline-{int(time.time())}',
                steps=pipeline_steps,
                triggers={
                    'branch': branch,
                    'manual': True
                },
                environment={
                    'CI_PROJECT_ID': project_id,
                    'TEST_ENV': 'true',
                    'PIPELINE_SOURCE': 'ansflow'
                }
            )
            
            self.stdout.write(f'  ✓ 流水线定义创建完成，包含 {len(pipeline_steps)} 个步骤')
            
            # 3. 使用统一引擎执行流水线
            self.stdout.write('\n3. 执行流水线...')
            engine = UnifiedCICDEngine()
            
            # 更新工具配置以包含项目ID
            tool_config = tool.configuration.copy()
            tool_config['project_id'] = project_id
            
            execution = await engine.execute_pipeline(
                tool_id=tool.id,
                pipeline_definition=pipeline_def,
                project_path=project_id,
                tool_config=tool_config
            )
            
            if execution:
                self.stdout.write(self.style.SUCCESS(f'  ✓ 流水线已提交执行'))
                self.stdout.write(f'  执行 ID: {execution.id}')
                self.stdout.write(f'  外部 ID: {execution.external_id}')
                if execution.external_url:
                    self.stdout.write(f'  GitLab URL: {execution.external_url}')
                
                # 4. 监控执行状态（如果启用）
                if monitor:
                    self.stdout.write('\n4. 监控流水线执行状态...')
                    await self._monitor_execution(engine, execution)
                else:
                    self.stdout.write('\n4. 跳过状态监控（使用 --monitor 启用）')
                    self.stdout.write(f'  可以使用以下命令查看状态:')
                    self.stdout.write(f'  python manage.py shell -c "')
                    self.stdout.write(f'  from cicd_integrations.models import PipelineExecution;')
                    self.stdout.write(f'  print(PipelineExecution.objects.get(id={execution.id}).status)"')
            else:
                self.stdout.write(self.style.ERROR('  ✗ 流水线执行失败'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'流水线执行测试失败: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())

    async def _monitor_execution(self, engine: UnifiedCICDEngine, execution: PipelineExecution):
        """监控流水线执行状态"""
        max_wait_time = 300  # 最多等待5分钟
        check_interval = 10  # 每10秒检查一次
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            try:
                # 刷新执行状态
                await engine.update_execution_status(execution.id)
                execution.refresh_from_db()
                
                self.stdout.write(f'  [{elapsed_time:3d}s] 状态: {execution.status}')
                
                if execution.status in ['success', 'failed', 'cancelled']:
                    # 获取最终日志
                    logs = await engine.get_execution_logs(execution.id)
                    if logs:
                        self.stdout.write('\n最终日志:')
                        self.stdout.write('-' * 50)
                        # 只显示最后20行
                        log_lines = logs.split('\n')
                        if len(log_lines) > 20:
                            self.stdout.write('... (省略前面的日志)')
                            log_lines = log_lines[-20:]
                        for line in log_lines:
                            self.stdout.write(f'  {line}')
                        self.stdout.write('-' * 50)
                    
                    if execution.status == 'success':
                        self.stdout.write(self.style.SUCCESS('\n✓ 流水线执行成功！'))
                    elif execution.status == 'failed':
                        self.stdout.write(self.style.ERROR('\n✗ 流水线执行失败！'))
                    else:
                        self.stdout.write(self.style.WARNING(f'\n⚠ 流水线已{execution.status}'))
                    break
                
                await asyncio.sleep(check_interval)
                elapsed_time += check_interval
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  监控出错: {e}'))
                break
        
        if elapsed_time >= max_wait_time:
            self.stdout.write(self.style.WARNING(f'\n⏰ 监控超时（{max_wait_time}秒），流水线可能仍在执行'))

    def _get_default_step_params(self, step_type: str, project_id: str, branch: str) -> dict:
        """获取步骤类型的默认参数"""
        default_params = {
            'git_checkout': {
                'repository': f'project_{project_id}',
                'branch': branch,
                'stage': 'checkout'
            },
            'shell_script': {
                'script': 'echo "Hello from shell script"',
                'stage': 'build'
            },
            'maven_build': {
                'goals': 'clean compile test',
                'stage': 'build'
            },
            'gradle_build': {
                'tasks': 'clean build test',
                'stage': 'build'
            },
            'npm_build': {
                'script': 'build',
                'stage': 'build'
            },
            'docker_build': {
                'dockerfile': 'Dockerfile',
                'tag': 'latest',
                'context': '.',
                'stage': 'build'
            },
            'test_execution': {
                'test_command': 'echo "Running tests"',
                'stage': 'test'
            },
            'security_scan': {
                'target_url': 'http://localhost',
                'stage': 'security'
            },
            'kubernetes_deploy': {
                'namespace': 'default',
                'manifest_path': 'k8s/',
                'stage': 'deploy'
            },
            'artifact_upload': {
                'paths': ['build/'],
                'retention': '1 week',
                'stage': 'archive'
            },
            'notification': {
                'message': f'Pipeline completed for project {project_id}',
                'stage': 'notify'
            },
            'environment_setup': {
                'variables': {
                    'PROJECT_ID': project_id,
                    'BRANCH': branch
                },
                'stage': 'setup'
            }
        }
        
        return default_params.get(step_type, {
            'command': f'echo "Unknown step type: {step_type}"',
            'stage': 'unknown'
        })
