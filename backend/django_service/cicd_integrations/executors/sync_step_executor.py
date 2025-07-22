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
        step_obj,  # 可以是AtomicStep或PipelineStep
        tool_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行步骤（同步版本）
        
        Args:
            step_obj: 步骤对象（AtomicStep或PipelineStep）
            tool_config: CI/CD工具配置
        
        Returns:
            执行结果
        """
        start_time = timezone.now()
        step_execution = None
        
        try:
            # 创建步骤执行记录
            step_execution = self._create_step_execution(step_obj)
            
            # 更新步骤状态为运行中
            self._update_step_status(step_execution, 'running')
            
            logger.info(f"开始执行原子步骤: {self._get_step_name(step_obj)} (ID: {step_obj.id})")
            
            # 准备执行环境
            execution_env = self._prepare_execution_environment(step_obj, tool_config)
            
            # 根据步骤类型执行
            result = self._execute_by_type(step_obj, execution_env, tool_config)
            
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
            
            logger.info(f"原子步骤执行完成: {self._get_step_name(step_obj)} - {final_status}")
            
            return execution_result
        
        except Exception as e:
            logger.error(f"原子步骤执行异常: {self._get_step_name(step_obj)} - {str(e)}", exc_info=True)
            
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

    def _get_step_config(self, step_obj) -> Dict[str, Any]:
        """获取步骤配置，兼容AtomicStep和PipelineStep"""
        try:
            from ..models import AtomicStep
            from pipelines.models import PipelineStep
            
            if isinstance(step_obj, AtomicStep):
                # AtomicStep有config字段
                return step_obj.config or {}
            elif isinstance(step_obj, PipelineStep):
                # PipelineStep需要根据步骤类型返回相应的配置
                config = {}
                
                # 基础配置
                if step_obj.command:
                    config['command'] = step_obj.command
                if step_obj.environment_vars:
                    config['environment'] = step_obj.environment_vars
                
                # 根据步骤类型添加特定配置
                if step_obj.step_type.startswith('docker_'):
                    config.update(step_obj.docker_config or {})
                    if step_obj.docker_image:
                        config['image'] = step_obj.docker_image
                        if step_obj.docker_tag:
                            config['image'] += f":{step_obj.docker_tag}"
                elif step_obj.step_type.startswith('k8s_'):
                    config.update(step_obj.k8s_config or {})
                    if step_obj.k8s_namespace:
                        config['namespace'] = step_obj.k8s_namespace
                    if step_obj.k8s_resource_name:
                        config['resource_name'] = step_obj.k8s_resource_name
                elif step_obj.step_type == 'ansible':
                    if step_obj.ansible_playbook:
                        config['playbook_id'] = step_obj.ansible_playbook.id
                    if step_obj.ansible_inventory:
                        config['inventory_id'] = step_obj.ansible_inventory.id
                    if step_obj.ansible_credential:
                        config['credential_id'] = step_obj.ansible_credential.id
                    config.update(step_obj.ansible_parameters or {})
                elif step_obj.step_type == 'fetch_code':
                    # 为代码拉取步骤配置，但不提供默认的仓库URL
                    config.setdefault('branch', 'main')
                    if not config.get('repository_url'):
                        logger.warning("代码拉取步骤缺少repository_url配置")
                
                # 合并步骤对象的config属性（如果存在）
                if hasattr(step_obj, 'config') and step_obj.config:
                    config.update(step_obj.config)
                
                return config
            else:
                logger.warning(f"未知的步骤类型: {type(step_obj)}")
                # 尝试直接获取config属性（用于测试或其他情况）
                if hasattr(step_obj, 'config') and step_obj.config:
                    config = step_obj.config.copy()
                    # 如果有command属性，添加到配置中
                    if hasattr(step_obj, 'command') and step_obj.command:
                        config['command'] = step_obj.command
                    return config
                elif hasattr(step_obj, 'command') and step_obj.command:
                    # 如果只有command属性
                    return {'command': step_obj.command}
                else:
                    return {}
        except Exception as e:
            logger.error(f"获取步骤配置失败: {str(e)}")
            return {}

    def _get_step_name(self, step_obj) -> str:
        """获取步骤名称"""
        return getattr(step_obj, 'name', f'Step {step_obj.id}')

    def _get_step_type(self, step_obj) -> str:
        """获取步骤类型"""
        return getattr(step_obj, 'step_type', 'custom')
    
    def _prepare_execution_environment(
        self,
        step_obj,
        tool_config: Dict[str, Any]
    ) -> Dict[str, str]:
        """准备执行环境"""
        # 基础环境变量
        env = dict(os.environ)
        env.update(self.context.environment)
        
        # 添加步骤特定的环境变量
        env.update({
            'STEP_ID': str(step_obj.id),
            'STEP_NAME': self._get_step_name(step_obj),
            'STEP_TYPE': self._get_step_type(step_obj),
        })
        
        # 添加步骤配置中的环境变量
        step_config = self._get_step_config(step_obj)
        if step_config and 'environment' in step_config:
            step_env = step_config['environment']
            if isinstance(step_env, dict):
                env.update(step_env)
            else:
                logger.warning(f"步骤 {self._get_step_name(step_obj)} 的环境变量配置格式错误，应为字典格式")
        
        return env
    
    def _execute_by_type(
        self,
        step_obj,
        execution_env: Dict[str, str],
        tool_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """根据步骤类型执行"""
        step_type = self._get_step_type(step_obj)
        
        if step_type == 'fetch_code':
            return self._execute_fetch_code(step_obj, execution_env)
        elif step_type == 'build':
            return self._execute_build(step_obj, execution_env)
        elif step_type == 'test':
            return self._execute_test(step_obj, execution_env)
        elif step_type == 'security_scan':
            return self._execute_security_scan(step_obj, execution_env)
        elif step_type == 'deploy':
            return self._execute_deploy(step_obj, execution_env)
        elif step_type == 'notify':
            return self._execute_notify(step_obj, execution_env)
        elif step_type == 'custom':
            return self._execute_custom(step_obj, execution_env)
        elif step_type in ['docker_build', 'docker_run', 'docker_push', 'docker_pull']:
            return self._execute_docker_step(step_obj, execution_env)
        else:
            # 对于不支持的步骤类型，返回错误而不是模拟执行
            return {
                'success': False,
                'error_message': f'不支持的步骤类型: {step_type}',
                'output': f'请检查步骤配置，当前步骤类型 "{step_type}" 尚未实现'
            }
    
    def _execute_fetch_code(
        self,
        step_obj,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行代码拉取步骤"""
        try:
            config = self._get_step_config(step_obj)
            
            # 优先使用command字段，如果没有则使用repository_url
            custom_command = config.get('command')
            repository_url = config.get('repository_url')
            branch = config.get('branch', 'main')
            git_credential_id = config.get('git_credential_id')
            
            # 处理Git凭据认证
            git_env = execution_env.copy()
            if git_credential_id:
                try:
                    git_env = self._setup_git_credentials(git_credential_id, git_env)
                    logger.info(f"已设置Git凭据认证，凭据ID: {git_credential_id}")
                except Exception as e:
                    logger.warning(f"设置Git凭据失败: {e}，将尝试使用默认认证")
            
            # 直接使用工作空间根目录作为目标目录，不创建额外的code子目录
            workspace_path = self.context.get_workspace_path()
            target_dir = workspace_path
            
            # 切换到工作目录
            original_cwd = os.getcwd()
            self.context.change_directory()
            
            try:
                if custom_command:
                    # 如果指定了自定义命令，直接在工作空间根目录执行
                    logger.info(f"使用自定义代码拉取命令: {custom_command}")
                    
                    commands = [
                        custom_command
                    ]
                    
                    # 如果自定义命令中包含git clone，尝试切换分支
                    if 'git clone' in custom_command and branch != 'main':
                        commands.append(f'git checkout {branch}')
                        
                elif repository_url:
                    # 如果没有自定义命令但有repository_url，使用标准的git clone
                    logger.info(f"使用标准代码拉取: {repository_url}")
                    
                    commands = [
                        f'git clone {repository_url} .',
                        f'git checkout {branch}'
                    ]
                else:
                    # 既没有自定义命令也没有repository_url
                    return {
                        'success': False,
                        'error_message': '代码拉取配置缺失，请在步骤配置中指定 command 或 repository_url',
                        'output': '示例配置：\n1. 使用自定义命令: {"command": "git clone ssh://git@example.com:2424/repo.git"}\n2. 使用仓库URL: {"repository_url": "https://github.com/user/repo.git"}'
                    }
                
                output = []
                for cmd in commands:
                    result = self._run_command(cmd, git_env)  # 使用带凭据的环境变量
                    output.append(f"$ {cmd}\n{result['output']}")
                    if not result['success']:
                        # 如果是Git认证相关错误，提供更详细的错误信息
                        error_msg = result.get('error_message', '')
                        if 'authentication failed' in error_msg.lower() or 'access denied' in error_msg.lower():
                            error_msg += f"\n提示：请检查Git凭据配置(ID: {git_credential_id})是否正确"
                        return {
                            'success': False,
                            'error_message': error_msg,
                            'output': '\n'.join(output)
                        }
                
                # 检测Git clone后是否创建了新的目录
                self._detect_and_handle_git_clone_directory(custom_command or f'git clone {repository_url}', workspace_path)
                
                return {
                    'success': True,
                    'output': '\n'.join(output),
                    'metadata': {
                        'repository_url': repository_url or '自定义命令',
                        'branch': branch,
                        'target_dir': target_dir,
                        'workspace_path': workspace_path,
                        'git_credential_id': git_credential_id,
                        'custom_command': custom_command
                    }
                }
                
            finally:
                # 注释：不再恢复原始工作目录，保持目录状态的连续性
                # 保持在 ExecutionContext 中跟踪的当前目录，以便下一个步骤继续使用
                # 清理Git凭据临时文件
                if git_credential_id:
                    self._cleanup_git_credentials(git_env)
            
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'output': ''
            }
    
    def _execute_build(
        self,
        step_obj,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行构建步骤"""
        try:
            config = self._get_step_config(step_obj) or {}
            build_command = config.get('build_command', 'echo "执行构建操作"')
            
            # 切换到工作目录进行构建
            workspace_path = self.context.get_workspace_path()
            original_cwd = os.getcwd()
            
            # 如果存在代码目录，切换到代码目录进行构建
            code_dir = os.path.join(workspace_path, 'code')
            if os.path.exists(code_dir):
                build_dir = code_dir
            else:
                build_dir = workspace_path
            
            try:
                self.context.change_directory(os.path.relpath(build_dir, workspace_path))
                
                # 添加工作目录信息到构建命令
                enhanced_command = f"echo 'Building in: {build_dir}' && {build_command}"
                
                result = self._run_command(enhanced_command, execution_env)
                
                return {
                    'success': result['success'],
                    'output': result['output'],
                    'error_message': result.get('error_message'),
                    'artifacts': ['build_artifact.tar.gz'] if result['success'] else [],
                    'metadata': {
                        'build_command': build_command,
                        'build_directory': build_dir,
                        'workspace_path': workspace_path
                    }
                }
                
            finally:
                # 注释：不再恢复原始工作目录，保持目录状态的连续性
                # 保持在 ExecutionContext 中跟踪的当前目录，以便下一个步骤继续使用
                pass
            
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'output': ''
            }
    
    def _execute_test(
        self,
        step_obj,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行测试步骤"""
        try:
            config = self._get_step_config(step_obj) or {}
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
        step_obj,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行安全扫描步骤"""
        try:
            config = self._get_step_config(step_obj) or {}
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
        step_obj,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行部署步骤"""
        try:
            config = self._get_step_config(step_obj) or {}
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
        step_obj,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行通知步骤"""
        try:
            config = self._get_step_config(step_obj) or {}
            message = config.get('message', '流水线执行完成')
            notify_type = config.get('type', 'email')
            notify_command = config.get('notify_command')
            
            if notify_command:
                # 执行自定义通知命令
                result = self._run_command(notify_command, execution_env)
                return {
                    'success': result['success'],
                    'output': result['output'],
                    'error_message': result.get('error_message'),
                    'metadata': {
                        'message': message,
                        'notify_type': notify_type,
                        'notify_command': notify_command
                    }
                }
            else:
                # 如果没有配置通知命令，返回错误
                return {
                    'success': False,
                    'error_message': '通知步骤未配置notify_command，请指定具体的通知命令',
                    'output': f'通知类型: {notify_type}, 消息: {message}'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'output': ''
            }
    
    def _execute_custom(
        self,
        step_obj,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行自定义步骤"""
        try:
            # 获取执行脚本，兼容AtomicStep和PipelineStep
            script = self._get_step_command(step_obj)
            if not script:
                config = self._get_step_config(step_obj)
                script = config.get('script', 'echo "执行自定义脚本"')
            
            # 切换到工作目录执行命令
            workspace_path = self.context.get_workspace_path()
            original_cwd = os.getcwd()
            
            # 对于自定义步骤，从工作空间根目录开始执行，保持命令的直观性
            # 这样用户可以使用 "cd code/test" 这样的相对路径
            workspace_path = self.context.get_workspace_path()
            
            # 在脚本前添加工作目录信息 - 修复pwd显示
            enhanced_script = f"echo 'Executing in workspace: {workspace_path}' && echo \"Current directory: $(pwd)\" && {script}"
            
            result = self._run_command_from_workspace_root(enhanced_script, execution_env)
            
            # 生成详细的日志信息
            log_content = f"=== 步骤执行详情 ===\n"
            log_content += f"工作目录: {workspace_path}\n"
            log_content += f"执行前目录: {workspace_path}\n"  # 自定义步骤总是从根目录开始
            log_content += f"原始命令: {script}\n"
            log_content += f"完整命令: {enhanced_script}\n"
            log_content += f"返回码: {result.get('return_code', 'N/A')}\n"
            log_content += f"执行后目录: {result.get('working_directory', 'N/A')}\n"
            
            if result.get('success'):
                log_content += f"执行状态: ✅ 成功\n"
                if result.get('output'):
                    log_content += f"\n=== 命令输出 ===\n{result['output']}\n"
            else:
                log_content += f"执行状态: ❌ 失败\n"
                if result.get('error_message'):
                    log_content += f"\n=== 错误信息 ===\n{result['error_message']}\n"
                if result.get('error_output'):
                    log_content += f"\n=== 错误输出 ===\n{result['error_output']}\n"
            
            log_content += f"=== 步骤执行完成 ===\n"
            
            return {
                'success': result['success'],
                'output': log_content,  # 使用详细的日志内容
                'error_message': result.get('error_message'),
                'metadata': {
                    'script': script,
                    'workspace_path': workspace_path,
                    'return_code': result.get('return_code', 0)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'output': f'步骤执行异常: {str(e)}'
            }
    
    def _run_command_from_workspace_root(
        self,
        command: str,
        execution_env: Dict[str, str],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """从工作空间根目录运行命令，不继承之前步骤的目录状态"""
        try:
            if timeout is None:
                timeout = self.default_timeout
            
            # 使用工作空间根目录
            workspace_root = self.context.get_workspace_path()
            
            # 确保工作目录存在
            if not os.path.exists(workspace_root):
                logger.warning(f"工作空间根目录不存在: {workspace_root}")
                return {
                    'success': False,
                    'error_message': f'工作空间根目录不存在: {workspace_root}',
                    'output': '',
                    'return_code': -1,
                    'working_directory': workspace_root
                }
            
            # 构造完整命令，从工作空间根目录执行
            debug_commands = [
                f"echo 'Executing in workspace: {workspace_root}'",
                f"echo \"Current directory: $(pwd)\"",
                command
            ]
            full_command = " && ".join(debug_commands)
            full_command = f"cd '{workspace_root}' && {full_command}"
            
            logger.info(f"从工作空间根目录 {workspace_root} 执行命令: {command}")
            
            process = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                env=execution_env,
                timeout=timeout
            )
            
            # 检测目录变化并更新共享状态
            if process.returncode == 0:
                self._detect_directory_change(command, workspace_root)
            
            # 构建详细的执行结果
            result = {
                'success': process.returncode == 0,
                'output': process.stdout,
                'return_code': process.returncode,
                'working_directory': self.context.get_current_directory(),
                'execution_details': {
                    'original_command': command,
                    'full_command': full_command,
                    'execution_directory': workspace_root,
                    'final_directory': self.context.get_current_directory(),
                    'stdout': process.stdout,
                    'stderr': process.stderr if process.stderr else None,
                    'execution_time': None
                }
            }
            
            if process.stderr:
                result['error_output'] = process.stderr
                if not result['success']:
                    result['error_message'] = process.stderr
            
            # 记录详细的执行信息
            logger.info(f"命令执行完成: 返回码={process.returncode}, 最终目录={self.context.get_current_directory()}")
            
            return result
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error_message': f'命令执行超时 ({timeout}秒)',
                'output': '',
                'return_code': -1,
                'working_directory': self.context.get_workspace_path()
            }
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'output': '',
                'return_code': -1,
                'working_directory': self.context.get_workspace_path()
            }

    def _run_command(
        self,
        command: str,
        execution_env: Dict[str, str],
        timeout: Optional[int] = None,
        update_working_dir: bool = True
    ) -> Dict[str, Any]:
        """运行命令，支持工作目录延续"""
        try:
            if timeout is None:
                timeout = self.default_timeout
            
            # 获取当前工作目录 - 这里获取的是共享状态中的目录
            current_dir = self.context.get_current_directory()
            
            # 确保工作目录存在，如果不存在则尝试恢复
            if not os.path.exists(current_dir):
                logger.warning(f"工作目录不存在，尝试恢复: {current_dir}")
                try:
                    self.context.change_directory()
                    current_dir = self.context.get_current_directory()
                    logger.info(f"工作目录已恢复: {current_dir}")
                except Exception as recovery_error:
                    logger.error(f"工作目录恢复失败: {recovery_error}")
                    return {
                        'success': False,
                        'error_message': f'工作目录不存在且无法恢复: {current_dir}',
                        'output': '',
                        'return_code': -1,
                        'working_directory': current_dir
                    }
            
            # 添加执行前目录信息到日志
            logger.info(f"执行前目录: {current_dir}")
            logger.info(f"在目录 {current_dir} 执行命令: {command}")
            
            # 构造完整命令，包含目录切换和调试信息
            debug_commands = [
                f"echo 'Executing in workspace: {self.context.get_workspace_path()}'",
                f"echo \"Current directory: $(pwd)\"",
                command
            ]
            full_command = " && ".join(debug_commands)
            
            # 使用 cd && 确保在正确的目录中执行命令
            full_command = f"cd '{current_dir}' && {full_command}"
            
            process = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                env=execution_env,
                timeout=timeout
            )
            
            # 检测目录变化
            if update_working_dir and process.returncode == 0:
                self._detect_directory_change(command, current_dir)
            
            # 构建详细的执行结果
            result = {
                'success': process.returncode == 0,
                'output': process.stdout,
                'return_code': process.returncode,
                'working_directory': self.context.get_current_directory(),
                'execution_details': {
                    'original_command': command,
                    'full_command': full_command,
                    'execution_directory': current_dir,
                    'final_directory': self.context.get_current_directory(),
                    'stdout': process.stdout,
                    'stderr': process.stderr if process.stderr else None,
                    'execution_time': None  # 可以在未来添加执行时间记录
                }
            }
            
            if process.stderr:
                result['error_output'] = process.stderr
                if not result['success']:
                    result['error_message'] = process.stderr
            
            # 记录详细的执行信息
            logger.info(f"命令执行完成: 返回码={process.returncode}, 最终目录={self.context.get_current_directory()}")
            
            return result
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error_message': f'命令执行超时 ({timeout}秒)',
                'output': '',
                'return_code': -1,
                'working_directory': self.context.get_current_directory()
            }
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'output': '',
                'return_code': -1,
                'working_directory': self.context.get_current_directory()
            }
    
    def _detect_and_handle_git_clone_directory(self, git_command: str, workspace_path: str) -> None:
        """
        检测Git clone命令创建的目录并自动切换到该目录
        
        Args:
            git_command: Git命令字符串
            workspace_path: 工作空间路径
        """
        import re
        import urllib.parse
        
        # 添加强制调试输出
        print(f"🔍 [DEBUG] 开始检测Git clone目录...")
        print(f"🔍 [DEBUG] Git命令: {git_command}")
        print(f"🔍 [DEBUG] 工作空间: {workspace_path}")
        
        if 'git clone' not in git_command:
            print(f"🔍 [DEBUG] 命令中不包含git clone，跳过检测")
            return
        
        try:
            # 提取仓库URL
            # 支持多种格式：
            # git clone https://github.com/user/repo.git
            # git clone ssh://git@gitlab.com:2424/user/repo.git
            # git clone git@github.com:user/repo.git
            clone_patterns = [
                r'git\s+clone\s+([^\s]+\.git)(?:\s+([^\s]+))?',  # 匹配 .git 结尾的URL，可选目标目录
                r'git\s+clone\s+([^\s]+)(?:\s+([^\s]+))?'       # 匹配任意URL，可选目标目录
            ]
            
            repo_url = None
            target_directory = None
            
            for pattern in clone_patterns:
                match = re.search(pattern, git_command)
                if match:
                    repo_url = match.group(1)
                    target_directory = match.group(2) if len(match.groups()) > 1 else None
                    break
            
            print(f"🔍 [DEBUG] 提取的仓库URL: {repo_url}")
            print(f"🔍 [DEBUG] 目标目录: {target_directory}")
            
            if not repo_url:
                print(f"🔍 [DEBUG] 无法从Git命令中提取仓库URL: {git_command}")
                logger.warning(f"无法从Git命令中提取仓库URL: {git_command}")
                return
            
            # 如果指定了目标目录，使用指定的目录
            if target_directory and target_directory != '.':
                cloned_dir = target_directory
            else:
                # 从URL中提取仓库名作为目录名
                # 处理各种URL格式
                if repo_url.startswith('ssh://'):
                    # ssh://git@gitlab.com:2424/user/repo.git -> repo
                    parsed = urllib.parse.urlparse(repo_url)
                    path_parts = parsed.path.strip('/').split('/')
                    repo_name = path_parts[-1] if path_parts else 'repo'
                elif '@' in repo_url and ':' in repo_url and not '://' in repo_url:
                    # git@github.com:user/repo.git -> repo
                    repo_name = repo_url.split(':')[-1].split('/')[-1]
                else:
                    # https://github.com/user/repo.git -> repo
                    repo_name = repo_url.split('/')[-1]
                
                # 移除.git后缀
                if repo_name.endswith('.git'):
                    repo_name = repo_name[:-4]
                
                cloned_dir = repo_name
            
            print(f"🔍 [DEBUG] 预期的克隆目录名: {cloned_dir}")
            
            # 检查克隆的目录是否存在
            cloned_path = os.path.join(workspace_path, cloned_dir)
            print(f"🔍 [DEBUG] 检查路径: {cloned_path}")
            print(f"🔍 [DEBUG] 路径存在: {os.path.exists(cloned_path)}")
            print(f"🔍 [DEBUG] 是目录: {os.path.isdir(cloned_path) if os.path.exists(cloned_path) else False}")
            
            if os.path.exists(cloned_path) and os.path.isdir(cloned_path):
                # 自动切换到克隆的目录
                self.context.set_current_directory(cloned_path)
                print(f"✅ [DEBUG] 检测到Git clone创建了目录 '{cloned_dir}'，自动切换工作目录到: {cloned_path}")
                logger.info(f"🔄 检测到Git clone创建了目录 '{cloned_dir}'，自动切换工作目录到: {cloned_path}")
                
                # 验证这确实是一个Git仓库
                git_dir = os.path.join(cloned_path, '.git')
                if os.path.exists(git_dir):
                    print(f"✅ [DEBUG] 确认 '{cloned_dir}' 是有效的Git仓库")
                    logger.info(f"✅ 确认 '{cloned_dir}' 是有效的Git仓库")
                else:
                    print(f"⚠️ [DEBUG] 目录 '{cloned_dir}' 存在但可能不是Git仓库")
                    logger.warning(f"⚠️ 目录 '{cloned_dir}' 存在但可能不是Git仓库")
            else:
                print(f"❌ [DEBUG] Git clone命令执行后未发现预期的目录: {cloned_path}")
                logger.info(f"📁 Git clone命令执行后未发现预期的目录: {cloned_path}")
                
                # 列出工作空间当前的内容进行调试
                try:
                    items = os.listdir(workspace_path)
                    print(f"🔍 [DEBUG] 工作空间当前内容: {items}")
                except Exception as e:
                    print(f"🔍 [DEBUG] 无法列出工作空间内容: {e}")
                
        except Exception as e:
            print(f"❌ [DEBUG] 检测Git clone目录时发生错误: {e}")
            logger.warning(f"检测Git clone目录时发生错误: {e}")

    def _detect_directory_change(self, command: str, previous_dir: str) -> None:
        """检测命令是否改变了工作目录"""
        import re
        
        # 检测cd命令
        cd_patterns = [
            r'\bcd\s+([^\s;&|]+)',  # cd path
            r'\bcd\s*$',  # cd (切换到HOME)
        ]
        
        for pattern in cd_patterns:
            match = re.search(pattern, command)
            if match:
                if len(match.groups()) == 0:
                    # cd命令没有参数，切换到HOME目录或工作目录根
                    target_dir = self.context.get_workspace_path()
                else:
                    target_dir = match.group(1).strip('\'"')
                
                if target_dir.startswith('/'):
                    # 绝对路径
                    new_dir = target_dir
                elif target_dir == '..':
                    # 上级目录
                    new_dir = os.path.dirname(previous_dir)
                elif target_dir == '.':
                    # 当前目录，无变化
                    return
                elif target_dir == '~':
                    # HOME目录，这里使用工作目录根
                    new_dir = self.context.get_workspace_path()
                else:
                    # 相对路径
                    new_dir = os.path.join(previous_dir, target_dir)
                
                # 标准化路径
                new_dir = os.path.abspath(new_dir)
                
                # 更新工作目录状态
                self.context.set_current_directory(new_dir)
                logger.info(f"检测到目录变化，工作目录已更新: {new_dir}")
                break

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
            # 对于PipelineStep，主要从ansible_parameters中获取配置
            config = {}
            
            # 从ansible_parameters获取主要配置（包含command等）
            ansible_params = getattr(step, 'ansible_parameters', {})
            if ansible_params:
                config.update(ansible_params)
            
            # 添加环境变量
            env_vars = getattr(step, 'environment_vars', {})
            if env_vars:
                config['environment'] = env_vars
            
            # 添加其他字段
            if hasattr(step, 'command') and step.command:
                config['command'] = step.command
                
            return config
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
        step_obj,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行 Docker 相关步骤"""
        try:
            step_type = self._get_step_type(step_obj)
            logger.info(f"执行 Docker 步骤: {step_type}")
            
            # 导入 Docker 执行器
            try:
                from pipelines.services.docker_executor import DockerStepExecutor
                docker_executor = DockerStepExecutor()
                
                # 检查是否可以执行该步骤类型
                if not docker_executor.can_execute(step_type):
                    raise ValueError(f"Docker 执行器不支持步骤类型: {step_type}")
                
                # 准备上下文，包含当前工作目录信息
                docker_context = {
                    'working_directory': self.context.get_current_directory(),
                    'workspace_path': self.context.get_workspace_path(),
                    'execution_env': execution_env
                }
                
                logger.info(f"[DEBUG] 传递给Docker执行器的工作目录: {docker_context['working_directory']}")
                
                # 执行 Docker 步骤
                result = docker_executor.execute_step(step_obj, docker_context)
                
                return {
                    'success': result.get('success', False),
                    'output': result.get('output', ''),
                    'error_message': result.get('error') if not result.get('success') else None,
                    'metadata': result.get('data', {})
                }
                
            except ImportError as e:
                logger.error(f"Docker 执行器不可用: {e}")
                # 如果 Docker 执行器不可用，执行基本的Docker命令
                return self._execute_docker_fallback(step_obj, execution_env)
                
        except Exception as e:
            logger.error(f"Docker 步骤执行失败: {e}")
            return {
                'success': False,
                'error_message': str(e),
                'output': ''
            }
    
    def _execute_docker_fallback(
        self,
        step_obj,
        execution_env: Dict[str, str]
    ) -> Dict[str, Any]:
        """Docker 步骤的真实执行方法"""
        step_type = self._get_step_type(step_obj)
        
        # 获取 Docker 配置
        docker_image = getattr(step_obj, 'docker_image', 'nginx:latest')
        docker_tag = getattr(step_obj, 'docker_tag', 'latest')
        full_image = f"{docker_image}:{docker_tag}" if not docker_image.endswith(docker_tag) else docker_image
        
        # 获取当前工作目录（由Git clone检测自动设置）
        workspace_path = self.context.get_workspace_path()
        current_working_dir = self.context.get_current_directory()
        
        # 使用当前工作目录作为构建上下文，而不是硬编码的 'code' 目录
        # 这样可以正确处理Git clone自动切换的目录
        build_context = current_working_dir if current_working_dir else workspace_path
        
        print(f"[DEBUG] Docker步骤使用构建上下文: {build_context}")
        print(f"[DEBUG] 当前工作目录: {current_working_dir}")
        print(f"[DEBUG] workspace路径: {workspace_path}")
        
        commands = []
        
        # 根据步骤类型生成相应的真实命令
        if step_type == 'docker_build':
            # 检查Dockerfile是否存在
            dockerfile_path = os.path.join(build_context, 'Dockerfile')
            if not os.path.exists(dockerfile_path):
                return {
                    'success': False,
                    'error_message': f'Dockerfile不存在于路径: {dockerfile_path}，请确保代码检出步骤包含Dockerfile文件',
                    'output': f'检查路径: {dockerfile_path}'
                }
            
            commands = [
                f"echo '🏗️ 开始构建Docker镜像: {full_image}'",
                f"docker build -t {full_image} .",
                f"echo '✅ Docker镜像构建完成: {full_image}'"
            ]
            
        elif step_type == 'docker_run':
            commands = [
                f"echo '🚀 运行Docker容器: {full_image}'",
                f"docker run --rm {full_image}",
                f"echo '✅ 容器执行完成'"
            ]
            
        elif step_type == 'docker_push':
            commands = [
                f"echo '� 推送Docker镜像: {full_image}'",
                f"docker push {full_image}",
                f"echo '✅ 镜像推送完成'"
            ]
            
        elif step_type == 'docker_pull':
            commands = [
                f"echo '📥 拉取Docker镜像: {full_image}'",
                f"docker pull {full_image}",
                f"echo '✅ 镜像拉取完成'"
            ]
            
        elif step_type == 'docker_push':
            commands = [
                f"echo '📤 准备推送Docker镜像: {full_image}'",
                f"echo '🔐 验证镜像仓库权限'",
                f"echo '⬆️ 上传镜像层'",
                f"echo '✅ 镜像推送完成'",
                f"echo '🌐 镜像已发布到仓库'",
                f"echo '💾 模拟推送成功，未实际执行docker push命令'"
            ]
            
        elif step_type == 'docker_pull':
            commands = [
                f"echo '📥 准备拉取Docker镜像: {full_image}'",
                f"echo '🔍 查找镜像源'",
                f"echo '⬇️ 下载镜像层'",
                f"echo '✅ 镜像拉取完成'",
                f"echo '📦 镜像已就绪'",
                f"echo '💾 模拟拉取成功，未实际执行docker pull命令'"
            ]
            
        else:
            commands = [
                f"echo '🐳 执行Docker操作: {step_type}'",
                f"echo '⚙️ 配置Docker环境'",
                f"echo '✅ Docker操作完成'",
                f"echo '💾 模拟执行成功'"
            ]
        
        # 执行所有命令
        all_output = []
        try:
            for cmd in commands:
                logger.info(f"执行模拟命令: {cmd}")
                result = self._run_command(cmd, execution_env)
                all_output.append(result['output'])
                if not result['success']:
                    return {
                        'success': False,
                        'output': '\n'.join(all_output),
                        'error_message': result.get('error_message', '模拟命令执行失败'),
                        'metadata': {
                            'docker_image': docker_image,
                            'docker_tag': docker_tag,
                            'step_type': step_type,
                            'simulation': True
                        }
                    }
            
            return {
                'success': True,
                'output': '\n'.join(all_output),
                'error_message': None,
                'metadata': {
                    'docker_image': docker_image,
                    'docker_tag': docker_tag,
                    'step_type': step_type,
                    'simulation': True,
                    'workspace_path': workspace_path
                }
            }
            
        except Exception as e:
            logger.error(f"Docker模拟执行失败: {e}")
            return {
                'success': False,
                'output': '\n'.join(all_output),
                'error_message': f"Docker模拟执行失败: {str(e)}",
                'metadata': {
                    'docker_image': docker_image,
                    'docker_tag': docker_tag,
                    'step_type': step_type,
                    'simulation': True
                }
            }

    def _setup_git_credentials(self, git_credential_id: int, env: Dict[str, str]) -> Dict[str, str]:
        """设置Git凭据环境变量"""
        try:
            # 导入Git凭据模型
            from cicd_integrations.models import GitCredential
            
            # 获取Git凭据
            credential = GitCredential.objects.get(id=git_credential_id)
            
            # 根据认证类型设置环境变量
            if credential.credential_type == 'username_password':
                password = credential.decrypt_password()
                if credential.username and password:
                    env['GIT_USERNAME'] = credential.username
                    env['GIT_PASSWORD'] = password
                    env['GIT_TERMINAL_PROMPT'] = '0'
                    env['GIT_ASKPASS'] = 'echo'
                    logger.info("已设置用户名密码认证")
                    
            elif credential.credential_type == 'access_token':
                token = credential.decrypt_password()
                if token:
                    # 对于access token，通常用作密码
                    env['GIT_USERNAME'] = credential.username or 'token'
                    env['GIT_PASSWORD'] = token
                    env['GIT_TERMINAL_PROMPT'] = '0'
                    env['GIT_ASKPASS'] = 'echo'
                    logger.info("已设置访问令牌认证")
                    
            elif credential.credential_type == 'ssh_key':
                private_key = credential.decrypt_ssh_key()
                if private_key:
                    # SSH密钥需要写入临时文件
                    import tempfile
                    temp_key_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.key')
                    temp_key_file.write(private_key)
                    temp_key_file.close()
                    
                    # 设置文件权限
                    os.chmod(temp_key_file.name, 0o600)
                    
                    # 设置SSH环境变量
                    env['GIT_SSH_COMMAND'] = f'ssh -i {temp_key_file.name} -o StrictHostKeyChecking=no'
                    env['SSH_PRIVATE_KEY_FILE'] = temp_key_file.name  # 记录文件路径以便后续清理
                    logger.info("已设置SSH密钥认证")
                    
            # 通用Git设置
            env['GIT_TERMINAL_PROMPT'] = '0'
            
            # 对于自签名证书或开发环境，忽略SSL验证
            server_url = getattr(credential, 'server_url', '')
            if '127.0.0.1' in server_url or 'localhost' in server_url or not server_url.startswith('https://'):
                env['GIT_SSL_NO_VERIFY'] = 'true'
            
            return env
            
        except Exception as e:
            logger.error(f"设置Git凭据失败: {e}")
            raise e

    def _cleanup_git_credentials(self, env: Dict[str, str]):
        """清理Git凭据相关的临时文件"""
        try:
            ssh_key_file = env.get('SSH_PRIVATE_KEY_FILE')
            if ssh_key_file and os.path.exists(ssh_key_file):
                os.unlink(ssh_key_file)
                logger.info(f"已清理SSH密钥临时文件: {ssh_key_file}")
        except Exception as e:
            logger.warning(f"清理Git凭据临时文件失败: {e}")
