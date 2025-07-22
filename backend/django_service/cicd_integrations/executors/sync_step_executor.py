"""
同步步骤执行器
专为Celery任务设计的同步版本，避免异步调用问题
"""
import logging
import subprocess
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from django.utils import timezone
from django.db import transaction

from ..models import AtomicStep, StepExecution
from .execution_context import ExecutionContext

logger = logging.getLogger(__name__)

class SyncStepExecutor:
    """同步步骤执行器"""
    
    def __init__(self, context: ExecutionContext):
        self.context = context
        self.default_timeout = 1800  # 30分钟默认超时
    
    def execute_step(
        self,
        atomic_step: AtomicStep,
        tool_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行原子步骤（同步版本）
        
        Args:
            atomic_step: 原子步骤对象
            tool_config: CI/CD工具配置
        
        Returns:
            执行结果
        """
        start_time = timezone.now()
        step_execution = None
        
        try:
            # 创建步骤执行记录
            step_execution = self._create_step_execution(atomic_step)
            
            # 更新步骤状态为运行中
            self._update_step_status(step_execution, 'running')
            
            logger.info(f"开始执行原子步骤: {self._get_step_name(atomic_step)} (ID: {atomic_step.id})")
            
            # 准备执行环境
            execution_env = self._prepare_execution_environment(atomic_step, tool_config)
            
            # 根据步骤类型执行
            result = self._execute_by_type(atomic_step, execution_env, tool_config)
            
            # 更新步骤状态
            final_status = 'success' if result.get('success', False) else 'failed'
            self._update_step_status(step_execution, final_status, result)
            
            # 构建返回结果
            execution_result = {
                'status': final_status,
                'start_time': start_time.isoformat(),
                'end_time': timezone.now().isoformat(),
                'execution_time': (timezone.now() - start_time).total_seconds(),
                'output': result.get('output', ''),
                'error_message': result.get('error_message'),
                'artifacts': result.get('artifacts', []),
                'metadata': result.get('metadata', {})
            }
            
            logger.info(f"原子步骤执行完成: {self._get_step_name(atomic_step)} - {final_status}")
            
            return execution_result
        
        except Exception as e:
            logger.error(f"原子步骤执行异常: {self._get_step_name(atomic_step)} - {str(e)}", exc_info=True)
            
            # 更新步骤状态为失败
            if step_execution:
                self._update_step_status(step_execution, 'failed', {'error_message': str(e)})
            
            return {
                'status': 'failed',
                'start_time': start_time.isoformat(),
                'end_time': timezone.now().isoformat(),
                'execution_time': (timezone.now() - start_time).total_seconds(),
                'error_message': str(e),
                'output': '',
                'artifacts': [],
                'metadata': {}
            }
    
    def _create_step_execution(self, step) -> StepExecution:
        """创建步骤执行记录"""
        try:
            # 获取流水线执行记录
            from ..models import PipelineExecution
            pipeline_execution = PipelineExecution.objects.get(id=self.context.execution_id)
            
            # 检查step是AtomicStep还是PipelineStep
            from ..models import AtomicStep
            from pipelines.models import PipelineStep
            
            order = getattr(step, 'order', 0)
            
            # 检查是否已存在相同order的执行记录
            existing_execution = StepExecution.objects.filter(
                pipeline_execution=pipeline_execution,
                order=order
            ).first()
            
            if existing_execution:
                logger.warning(f"步骤执行记录已存在，复用: {existing_execution.id}")
                return existing_execution
            
            # 根据step类型创建StepExecution
            if isinstance(step, AtomicStep):
                step_execution = StepExecution.objects.create(
                    pipeline_execution=pipeline_execution,
                    atomic_step=step,
                    status='pending',
                    order=order,
                    started_at=timezone.now()
                )
            elif isinstance(step, PipelineStep):
                step_execution = StepExecution.objects.create(
                    pipeline_execution=pipeline_execution,
                    pipeline_step=step,
                    status='pending',
                    order=order,
                    started_at=timezone.now()
                )
            else:
                # 兼容性：如果是其他类型，尝试使用PipelineStep
                try:
                    pipeline_step = PipelineStep.objects.get(id=step.id)
                    step_execution = StepExecution.objects.create(
                        pipeline_execution=pipeline_execution,
                        pipeline_step=pipeline_step,
                        status='pending',
                        order=order,
                        started_at=timezone.now()
                    )
                except PipelineStep.DoesNotExist:
                    raise ValueError(f"无法识别的步骤类型: {type(step)}")
            
            logger.info(f"创建步骤执行记录: {step_execution.id}")
            return step_execution
            
        except Exception as e:
            logger.error(f"创建步骤执行记录失败: {str(e)}")
            raise
    
    def _update_step_status(
        self,
        step_execution: StepExecution,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ):
        """更新步骤执行状态"""
        try:
            with transaction.atomic():
                step_execution.status = status
                step_execution.updated_at = timezone.now()
                
                if status == 'running':
                    step_execution.started_at = timezone.now()
                elif status in ['success', 'failed']:
                    step_execution.completed_at = timezone.now()
                
                if result:
                    step_execution.output = result
                    step_execution.logs = result.get('output', '')
                    step_execution.error_message = result.get('error_message', '') or ''
                
                step_execution.save()
                
        except Exception as e:
            logger.error(f"更新步骤状态失败: {str(e)}")
    
    def _prepare_execution_environment(
        self,
        atomic_step: AtomicStep,
        tool_config: Dict[str, Any]
    ) -> Dict[str, str]:
        """准备执行环境"""
        # 基础环境变量
        env = dict(os.environ)
        env.update(self.context.environment)
        
        # 添加步骤特定的环境变量
        env.update({
            'STEP_ID': str(atomic_step.id),
            'STEP_NAME': self._get_step_name(atomic_step),
            'STEP_TYPE': self._get_step_type(atomic_step),
        })
        
        # 添加步骤配置中的环境变量
        step_config = self._get_step_config(atomic_step)
        if step_config and 'environment' in step_config:
            step_env = step_config['environment']
            if isinstance(step_env, dict):
                env.update(step_env)
            else:
                logger.warning(f"步骤 {self._get_step_name(atomic_step)} 的环境变量配置格式错误，应为字典格式")
        
        return env
    
    def _execute_by_type(
        self,
        atomic_step,
        execution_env: Dict[str, str],
        tool_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """根据步骤类型执行"""
        step_type = self._get_step_type(atomic_step)
        
        if step_type == 'fetch_code':
            return self._execute_fetch_code(atomic_step, execution_env)
        elif step_type == 'build':
            return self._execute_build(atomic_step, execution_env)
        elif step_type == 'test':
            return self._execute_test(atomic_step, execution_env)
        elif step_type == 'security_scan':
            return self._execute_security_scan(atomic_step, execution_env)
        elif step_type == 'deploy':
            return self._execute_deploy(atomic_step, execution_env)
        elif step_type == 'notify':
            return self._execute_notify(atomic_step, execution_env)
        elif step_type == 'custom':
            return self._execute_custom(atomic_step, execution_env)
        elif step_type in ['docker_build', 'docker_run', 'docker_push', 'docker_pull']:
            return self._execute_docker_step(atomic_step, execution_env)
        else:
            return self._execute_mock(atomic_step, execution_env)
    
    def _execute_fetch_code(
        self,
        atomic_step: AtomicStep,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行代码拉取步骤"""
        try:
            config = atomic_step.config or {}
            repository_url = config.get('repository_url', 'https://github.com/example/repo.git')
            branch = config.get('branch', 'main')
            target_dir = config.get('target_dir', '/tmp/code')
            
            # 模拟代码拉取
            commands = [
                f'mkdir -p {target_dir}',
                f'cd {target_dir} && git init',
                f'cd {target_dir} && (git remote get-url origin || git remote add origin {repository_url})',
                f'cd {target_dir} && echo "模拟代码拉取完成" > README.md'
            ]
            
            output = []
            for cmd in commands:
                result = self._run_command(cmd, execution_env)
                output.append(f"$ {cmd}\n{result['output']}")
                # 对于git remote操作，即使返回非0也可能是正常的
                if not result['success'] and 'git remote' not in cmd:
                    return {
                        'success': False,
                        'error_message': result['error_message'],
                        'output': '\n'.join(output)
                    }
            
            return {
                'success': True,
                'output': '\n'.join(output),
                'metadata': {
                    'repository_url': repository_url,
                    'branch': branch,
                    'target_dir': target_dir
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'output': ''
            }
    
    def _execute_build(
        self,
        atomic_step: AtomicStep,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行构建步骤"""
        try:
            config = atomic_step.config or {}
            build_command = config.get('build_command', 'echo "执行构建操作"')
            
            result = self._run_command(build_command, execution_env)
            
            return {
                'success': result['success'],
                'output': result['output'],
                'error_message': result.get('error_message'),
                'artifacts': ['build_artifact.tar.gz'] if result['success'] else [],
                'metadata': {
                    'build_command': build_command
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'output': ''
            }
    
    def _execute_test(
        self,
        atomic_step: AtomicStep,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行测试步骤"""
        try:
            config = atomic_step.config or {}
            test_command = config.get('test_command', 'echo "执行测试用例"')
            
            result = self._run_command(test_command, execution_env)
            
            return {
                'success': result['success'],
                'output': result['output'],
                'error_message': result.get('error_message'),
                'artifacts': ['test_report.xml'] if result['success'] else [],
                'metadata': {
                    'test_command': test_command,
                    'test_type': config.get('test_type', 'unit')
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'output': ''
            }
    
    def _execute_security_scan(
        self,
        atomic_step: AtomicStep,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行安全扫描步骤"""
        try:
            config = atomic_step.config or {}
            scan_command = config.get('scan_command', 'echo "执行安全扫描"')
            
            result = self._run_command(scan_command, execution_env)
            
            return {
                'success': result['success'],
                'output': result['output'],
                'error_message': result.get('error_message'),
                'artifacts': ['security_report.json'] if result['success'] else [],
                'metadata': {
                    'scan_command': scan_command,
                    'scan_type': config.get('scan_type', 'static')
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'output': ''
            }
    
    def _execute_deploy(
        self,
        atomic_step: AtomicStep,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行部署步骤"""
        try:
            config = atomic_step.config or {}
            deploy_command = config.get('deploy_command', 'echo "执行部署操作"')
            
            result = self._run_command(deploy_command, execution_env)
            
            return {
                'success': result['success'],
                'output': result['output'],
                'error_message': result.get('error_message'),
                'metadata': {
                    'deploy_command': deploy_command,
                    'environment': config.get('environment', 'production')
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'output': ''
            }
    
    def _execute_notify(
        self,
        atomic_step: AtomicStep,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行通知步骤"""
        try:
            config = atomic_step.config or {}
            message = config.get('message', '流水线执行完成')
            notify_type = config.get('type', 'email')
            
            # 模拟通知发送
            output = f"发送{notify_type}通知: {message}"
            
            return {
                'success': True,
                'output': output,
                'metadata': {
                    'message': message,
                    'notify_type': notify_type
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'output': ''
            }
    
    def _execute_custom(
        self,
        atomic_step,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行自定义步骤"""
        try:
            # 获取执行脚本，兼容AtomicStep和PipelineStep
            script = self._get_step_command(atomic_step)
            if not script:
                config = self._get_step_config(atomic_step)
                script = config.get('script', 'echo "执行自定义脚本"')
            
            result = self._run_command(script, execution_env)
            
            # 生成详细的日志信息
            log_content = f"执行命令: {script}\n"
            if result.get('success'):
                log_content += f"命令执行成功\n"
                if result.get('output'):
                    log_content += f"输出:\n{result['output']}"
            else:
                log_content += f"命令执行失败\n"
                if result.get('error_message'):
                    log_content += f"错误信息: {result['error_message']}\n"
                if result.get('error_output'):
                    log_content += f"错误输出: {result['error_output']}\n"
            
            return {
                'success': result['success'],
                'output': log_content,  # 使用详细的日志内容
                'error_message': result.get('error_message'),
                'metadata': {
                    'script': script,
                    'return_code': result.get('return_code', 0)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'output': f'步骤执行异常: {str(e)}'
            }
    
    def _execute_mock(
        self,
        atomic_step: AtomicStep,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行模拟步骤"""
        import time
        import random
        
        # 模拟执行时间
        execution_time = random.uniform(1, 5)
        time.sleep(execution_time)
        
        # 90% 成功率
        success = random.random() > 0.1
        
        if success:
            output = f"模拟步骤 {self._get_step_name(atomic_step)} 执行成功"
            return {
                'success': True,
                'output': output,
                'metadata': {
                    'execution_time': execution_time,
                    'step_type': self._get_step_type(atomic_step)
                }
            }
        else:
            return {
                'success': False,
                'error_message': f"模拟步骤 {self._get_step_name(atomic_step)} 执行失败",
                'output': '',
                'metadata': {
                    'execution_time': execution_time
                }
            }
    
    def _run_command(
        self,
        command: str,
        execution_env: Dict[str, str],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """运行命令"""
        try:
            if timeout is None:
                timeout = self.default_timeout
            
            logger.info(f"执行命令: {command}")
            
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                env=execution_env,
                timeout=timeout
            )
            
            result = {
                'success': process.returncode == 0,
                'output': process.stdout,
                'return_code': process.returncode
            }
            
            if process.stderr:
                result['error_output'] = process.stderr
                if not result['success']:
                    result['error_message'] = process.stderr
            
            return result
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error_message': f'命令执行超时 ({timeout}秒)',
                'output': '',
                'return_code': -1
            }
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'output': '',
                'return_code': -1
            }
    
    def _get_step_name(self, step):
        """获取步骤名称，兼容AtomicStep和PipelineStep"""
        return getattr(step, 'name', f'Step {getattr(step, "id", "unknown")}')
    
    def _get_step_config(self, step):
        """获取步骤配置，兼容AtomicStep和PipelineStep"""
        from ..models import AtomicStep
        from pipelines.models import PipelineStep
        
        if isinstance(step, AtomicStep):
            return getattr(step, 'config', {})
        elif isinstance(step, PipelineStep):
            return getattr(step, 'environment_vars', {})
        else:
            return {}
    
    def _get_step_type(self, step):
        """获取步骤类型，兼容AtomicStep和PipelineStep"""
        return getattr(step, 'step_type', 'custom')
    
    def _get_step_parameters(self, step):
        """获取步骤参数，兼容AtomicStep和PipelineStep"""
        from ..models import AtomicStep
        from pipelines.models import PipelineStep
        
        if isinstance(step, AtomicStep):
            return getattr(step, 'parameters', {})
        elif isinstance(step, PipelineStep):
            return getattr(step, 'ansible_parameters', {})
        else:
            return {}
    
    def _get_step_command(self, step):
        """获取步骤命令，兼容AtomicStep和PipelineStep"""
        from pipelines.models import PipelineStep
        
        if isinstance(step, PipelineStep):
            # 首先尝试从command字段获取
            command = getattr(step, 'command', '')
            if command:
                return command
            
            # 如果command字段为空，尝试从parameters中获取
            parameters = self._get_step_parameters(step)
            if parameters and 'command' in parameters:
                return parameters['command']
            
            # 如果都没有，返回空字符串
            return ''
        else:
            # AtomicStep没有command字段，返回空字符串
            return ''
    
    def _get_step_timeout(self, step):
        """获取步骤超时时间，兼容AtomicStep和PipelineStep"""
        from ..models import AtomicStep
        from pipelines.models import PipelineStep
        
        if isinstance(step, AtomicStep):
            return getattr(step, 'timeout', 600)
        elif isinstance(step, PipelineStep):
            return getattr(step, 'timeout_seconds', 300)
        else:
            return 600
    
    def _get_step_ansible_config(self, step):
        """获取步骤的Ansible配置，兼容AtomicStep和PipelineStep"""
        return {
            'playbook': getattr(step, 'ansible_playbook', None),
            'inventory': getattr(step, 'ansible_inventory', None),
            'credential': getattr(step, 'ansible_credential', None),
            'extra_vars': getattr(step, 'ansible_extra_vars', {}),
            'vault_password': getattr(step, 'ansible_vault_password', None)
        }
    
    def _execute_docker_step(
        self,
        atomic_step,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行 Docker 相关步骤"""
        try:
            step_type = self._get_step_type(atomic_step)
            logger.info(f"执行 Docker 步骤: {step_type}")
            
            # 导入 Docker 执行器
            try:
                from pipelines.services.docker_executor import DockerStepExecutor
                docker_executor = DockerStepExecutor()
                
                # 检查是否可以执行该步骤类型
                if not docker_executor.can_execute(step_type):
                    raise ValueError(f"Docker 执行器不支持步骤类型: {step_type}")
                
                # 执行 Docker 步骤
                result = docker_executor.execute_step(atomic_step, execution_env)
                
                return {
                    'success': result.get('success', False),
                    'output': result.get('output', ''),
                    'error_message': result.get('error') if not result.get('success') else None,
                    'metadata': result.get('data', {})
                }
                
            except ImportError as e:
                logger.error(f"Docker 执行器不可用: {e}")
                # 如果 Docker 执行器不可用，执行基本的模拟命令
                return self._execute_docker_fallback(atomic_step, execution_env)
                
        except Exception as e:
            logger.error(f"Docker 步骤执行失败: {e}")
            return {
                'success': False,
                'error_message': str(e),
                'output': ''
            }
    
    def _execute_docker_fallback(
        self,
        atomic_step,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """Docker 步骤的回退执行方法"""
        step_type = self._get_step_type(atomic_step)
        
        # 获取 Docker 配置
        docker_image = getattr(atomic_step, 'docker_image', 'nginx:latest')
        docker_tag = getattr(atomic_step, 'docker_tag', 'latest')
        full_image = f"{docker_image}:{docker_tag}" if not docker_image.endswith(docker_tag) else docker_image
        
        # 根据步骤类型生成相应的 Docker 命令
        if step_type == 'docker_build':
            command = f"echo '构建 Docker 镜像: {full_image}' && docker build -t {full_image} ."
        elif step_type == 'docker_run':
            command = f"echo '运行 Docker 容器: {full_image}' && docker run --rm {full_image} echo 'Container executed successfully'"
        elif step_type == 'docker_push':
            command = f"echo '推送 Docker 镜像: {full_image}' && docker push {full_image}"
        elif step_type == 'docker_pull':
            command = f"echo '拉取 Docker 镜像: {full_image}' && docker pull {full_image}"
        else:
            command = f"echo '执行 Docker 操作: {step_type}'"
        
        logger.info(f"执行命令: {command}")
        
        # 执行命令
        result = self._run_command(command, execution_env)
        
        return {
            'success': result['success'],
            'output': result['output'],
            'error_message': result.get('error_message'),
            'metadata': {
                'docker_image': docker_image,
                'docker_tag': docker_tag,
                'step_type': step_type
            }
        }
