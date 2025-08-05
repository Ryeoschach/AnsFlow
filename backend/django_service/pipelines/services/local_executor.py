"""
本地Celery执行器 - 在AnsFlow服务器上执行原子步骤
支持传统步骤、Docker步骤和Kubernetes步骤
"""
import logging
from typing import Dict, Any
from django.utils import timezone
from celery import group, chain

from ..models import Pipeline, PipelineRun
from cicd_integrations.models import AtomicStep
from ..tasks import execute_atomic_step_task
from .docker_executor import DockerStepExecutor
from .kubernetes_executor import KubernetesStepExecutor
from common.execution_logger import ExecutionLogger

logger = logging.getLogger(__name__)


class LocalPipelineExecutor:
    """本地Celery执行器 - 支持传统步骤、Docker步骤和Kubernetes步骤"""
    
    def __init__(self):
        self.docker_executor = DockerStepExecutor()
        self.k8s_executor = KubernetesStepExecutor()
    
    def execute(self, pipeline: Pipeline, pipeline_run: PipelineRun, 
               parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        在本地使用Celery执行流水线中的原子步骤
        
        Args:
            pipeline: 流水线对象
            pipeline_run: 流水线运行记录
            parameters: 执行参数
            
        Returns:
            执行结果字典
        """
        logger.info(f"开始本地执行流水线: {pipeline.name}")
        
        try:
            # 获取流水线的步骤，按order排序
            steps = pipeline.steps.filter(is_active=True).order_by('order')
            
            if not steps.exists():
                pipeline_run.status = 'success'
                pipeline_run.completed_at = timezone.now()
                pipeline_run.save()
                
                return {
                    'message': '流水线没有配置步骤，直接完成',
                    'steps_executed': 0
                }
            
            # 更新流水线运行状态
            pipeline_run.status = 'running'
            pipeline_run.save()
            
            # 执行步骤
            context = parameters or {}
            step_results = []
            
            for step in steps:
                try:
                    # 检查步骤是否需要审批
                    if step.approval_required and step.approval_status != 'approved':
                        step.status = 'pending_approval'
                        step.save()
                        continue
                    
                    # 更新步骤状态
                    step.status = 'running'
                    step.started_at = timezone.now()
                    step.save()
                    
                    # 根据步骤类型选择执行器
                    result = self._execute_step(step, context)
                    
                    if result['success']:
                        step.status = 'success'
                        step.output_log = result.get('output', '')
                        # 更新上下文
                        context.update(result.get('data', {}))
                    else:
                        step.status = 'failed'
                        step.error_log = result.get('error', '')
                        
                        # 如果步骤失败且没有配置继续执行，则停止整个流水线
                        if not step.retry_policy.get('continue_on_failure', False):
                            break
                    
                    step.completed_at = timezone.now()
                    step.save()
                    
                    step_results.append(result)
                    
                except Exception as e:
                    logger.error(f"Step {step.name} execution failed: {e}")
                    step.status = 'failed'
                    step.error_log = str(e)
                    step.completed_at = timezone.now()
                    step.save()
                    
                    step_results.append({
                        'success': False,
                        'step_id': step.id,
                        'error': str(e)
                    })
                    
                    if not step.retry_policy.get('continue_on_failure', False):
                        break
            
            # 更新流水线运行状态
            failed_steps = [r for r in step_results if not r['success']]
            if failed_steps:
                pipeline_run.status = 'failed'
            else:
                pipeline_run.status = 'success'
            
            pipeline_run.completed_at = timezone.now()
            pipeline_run.save()
            
            return {
                'message': f'流水线执行完成，共执行{len(step_results)}个步骤',
                'steps_executed': len(step_results),
                'failed_steps': len(failed_steps),
                'execution_mode': 'local',
                'step_results': step_results
            }
            
        except Exception as e:
            logger.error(f"本地执行失败: {e}")
            pipeline_run.status = 'failed'
            pipeline_run.completed_at = timezone.now()
            pipeline_run.save()
            
            return {
                'message': f'本地执行失败: {str(e)}',
                'error': str(e)
            }
    
    def execute_step(self, step, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行单个步骤，用于并行执行服务调用
        """
        context = context or {}
        return self._execute_step(step, context)
    
    def _execute_step(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """根据步骤类型选择合适的执行器"""
        
        # Docker 步骤
        if self.docker_executor.can_execute(step.step_type):
            return self.docker_executor.execute_step(step, context)
        
        # Kubernetes 步骤
        elif self.k8s_executor.can_execute(step.step_type):
            return self.k8s_executor.execute_step(step, context)
        
        # 传统步骤（Ansible、脚本等）
        else:
            return self._execute_traditional_step(step, context)
    
    def _execute_traditional_step(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行传统步骤（原有逻辑）"""
        import os
        
        # 打印当前工作目录信息  
        working_directory = context.get('working_directory', os.getcwd())
        logger.info(f"📁 [traditional] 当前工作目录: {working_directory}")
        logger.info(f"📁 [traditional] 目录内容: {os.listdir(working_directory) if os.path.exists(working_directory) else '目录不存在'}")
        
        try:
            if step.step_type == 'fetch_code':
                # 代码获取步骤执行
                return self._execute_fetch_code_step(step, context)
            elif step.step_type == 'ansible':
                # Ansible 步骤执行
                return self._execute_ansible_step(step, context)
            elif step.step_type == 'script':
                # 脚本步骤执行
                return self._execute_script_step(step, context)
            elif step.step_type == 'custom':
                # 🔥 问题2修复：custom类型步骤直接执行shell命令，不使用Celery
                return self._execute_shell_command_step(step, context)
            else:
                # 其他类型的步骤，使用原有的 Celery 任务
                logger.info(f"🚀 [traditional] 启动Celery任务执行步骤: {step.name} (类型: {step.step_type})")
                task_result = execute_atomic_step_task.delay(
                    step_id=step.id,
                    parameters=context
                )
                
                return {
                    'success': True,
                    'message': f'Step {step.name} started',
                    'task_id': task_result.id,
                    'output': f'Celery task started: {task_result.id}',
                    'data': {}
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': '',
                'data': {}
            }
    
    def _execute_ansible_step(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Ansible 步骤"""
        try:
            from ansible_integration.models import AnsibleExecution
            from ansible_integration.tasks import execute_ansible_playbook
            
            logger.info(f"开始执行Ansible步骤: {step.name}")
            
            # 从步骤参数中获取ansible配置
            ansible_parameters = getattr(step, 'ansible_parameters', {}) or {}
            ansible_playbook = getattr(step, 'ansible_playbook', None)
            ansible_inventory = getattr(step, 'ansible_inventory', None) 
            ansible_credential = getattr(step, 'ansible_credential', None)
            
            # 记录步骤配置信息
            logger.info(f"Ansible步骤配置: playbook={ansible_playbook}, inventory={ansible_inventory}, credential={ansible_credential}")
            logger.info(f"Ansible参数: {ansible_parameters}")
            
            # 如果没有直接字段，尝试从parameters中获取ID
            if not ansible_playbook and ansible_parameters.get('playbook_id'):
                from ansible_integration.models import AnsiblePlaybook
                try:
                    ansible_playbook = AnsiblePlaybook.objects.get(id=ansible_parameters['playbook_id'])
                    logger.info(f"通过playbook_id {ansible_parameters['playbook_id']} 找到playbook: {ansible_playbook.name}")
                except AnsiblePlaybook.DoesNotExist:
                    logger.error(f"Ansible Playbook ID {ansible_parameters['playbook_id']} 不存在")
                    
            if not ansible_inventory and ansible_parameters.get('inventory_id'):
                from ansible_integration.models import AnsibleInventory
                try:
                    ansible_inventory = AnsibleInventory.objects.get(id=ansible_parameters['inventory_id'])
                    logger.info(f"通过inventory_id {ansible_parameters['inventory_id']} 找到inventory: {ansible_inventory.name}")
                except AnsibleInventory.DoesNotExist:
                    logger.error(f"Ansible Inventory ID {ansible_parameters['inventory_id']} 不存在")
                    
            if not ansible_credential and ansible_parameters.get('credential_id'):
                from ansible_integration.models import AnsibleCredential
                try:
                    ansible_credential = AnsibleCredential.objects.get(id=ansible_parameters['credential_id'])
                    logger.info(f"通过credential_id {ansible_parameters['credential_id']} 找到credential: {ansible_credential.name}")
                except AnsibleCredential.DoesNotExist:
                    logger.error(f"Ansible Credential ID {ansible_parameters['credential_id']} 不存在")
            
            if not ansible_playbook or not ansible_inventory:
                error_msg = f"Ansible步骤 {step.name} 缺少必要配置: playbook={ansible_playbook}, inventory={ansible_inventory}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'message': error_msg,
                    'output': '',
                    'error': error_msg
                }
            
            # 创建AnsibleExecution记录
            execution = AnsibleExecution.objects.create(
                playbook=ansible_playbook,
                inventory=ansible_inventory,
                credential=ansible_credential,
                parameters=ansible_parameters,
                status='pending',
                created_by_id=1  # TODO: 从context中获取用户ID
            )
            
            logger.info(f"创建AnsibleExecution记录: {execution.id}")
            logger.info(f"  - Playbook: {ansible_playbook.name}")
            logger.info(f"  - Inventory: {ansible_inventory.name}")
            logger.info(f"  - Credential: {ansible_credential.name if ansible_credential else 'None'}")
            
            # 使用ExecutionLogger记录开始执行
            ExecutionLogger.start_execution(
                execution,
                f"流水线步骤 {step.name} 开始执行Ansible playbook: {ansible_playbook.name}"
            )
            
            # 同步执行ansible任务（而不是异步）
            task_result = execute_ansible_playbook(execution.id)
            
            # 重新获取execution对象，查看最新状态
            execution.refresh_from_db()
            
            logger.info(f"Ansible执行完成: status={execution.status}, return_code={getattr(execution, 'return_code', None)}")
            
            if execution.status == 'success':
                ExecutionLogger.log_execution_info(
                    execution,
                    f"流水线步骤 {step.name} 中的Ansible执行成功完成"
                )
                return {
                    'success': True,
                    'message': f'Ansible步骤 {step.name} 执行成功',
                    'output': execution.stdout or 'Ansible playbook executed successfully',
                    'data': {
                        'ansible_execution_id': execution.id,
                        'return_code': getattr(execution, 'return_code', 0),
                        'status': execution.status
                    }
                }
            else:
                ExecutionLogger.log_execution_info(
                    execution,
                    f"流水线步骤 {step.name} 中的Ansible执行失败: {execution.error_message or 'Unknown error'}",
                    level='error'
                )
                return {
                    'success': False,
                    'message': f'Ansible步骤 {step.name} 执行失败',
                    'output': execution.stdout or '',
                    'error': execution.stderr or execution.error_message or 'Ansible execution failed',
                    'data': {
                        'ansible_execution_id': execution.id,
                        'return_code': getattr(execution, 'return_code', 1),
                        'status': execution.status
                    }
                }
                
        except Exception as e:
            error_msg = f"Ansible步骤执行异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'message': error_msg,
                'output': '',
                'error': error_msg
            }
    
    def _execute_script_step(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行脚本步骤"""
        import subprocess
        import os
        
        try:
            # 设置环境变量
            env = os.environ.copy()
            env.update(step.environment_vars)
            env.update({k: str(v) for k, v in context.items()})
            
            # 执行命令
            result = subprocess.run(
                step.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=step.timeout_seconds,
                env=env
            )
            
            return {
                'success': result.returncode == 0,
                'message': f'Script executed with exit code {result.returncode}',
                'output': result.stdout + result.stderr,
                'data': {'exit_code': result.returncode}
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Script execution timed out after {step.timeout_seconds} seconds',
                'output': '',
                'data': {}
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': '',
                'data': {}
            }
            return group(tasks)
    
    def _has_dependencies(self, atomic_steps):
        """检查步骤是否有依赖关系"""
        for step in atomic_steps:
            if step.dependencies.exists():
                return True
        return False
    
    def execute_single_step(self, step: AtomicStep, pipeline_run: PipelineRun,
                           parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行单个原子步骤（用于混合模式）
        
        Args:
            step: 原子步骤
            pipeline_run: 流水线运行记录
            parameters: 执行参数
            
        Returns:
            执行结果
        """
        logger.info(f"本地执行单个步骤: {step.name}")
        
        try:
            # 执行步骤
            result = execute_atomic_step_task.delay(
                step_id=step.id,
                pipeline_run_id=pipeline_run.id,
                parameters=parameters or {}
            )
            
            return {
                'success': True,
                'task_id': result.id,
                'step_name': step.name,
                'execution_type': 'local'
            }
            
        except Exception as e:
            logger.error(f"单步本地执行失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'step_name': step.name
            }

    def _execute_shell_command_step(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行Shell命令步骤 (custom类型)"""
        import subprocess
        import os
        
        try:
            working_directory = context.get('working_directory', os.getcwd())
            
            # 打印当前工作目录信息
            logger.info(f"📁 [shell_command] 当前工作目录: {working_directory}")
            logger.info(f"📁 [shell_command] 目录内容: {os.listdir(working_directory) if os.path.exists(working_directory) else '目录不存在'}")
            
            # 获取要执行的命令
            command = step.command
            
            if not command:
                return {
                    'success': False,
                    'error': 'No command specified in command field',
                    'output': '',
                    'data': {}
                }
            
            logger.info(f"🚀 [shell_command] 执行命令: {command}")
            
            # 处理cd命令 - 这是一个特殊情况，因为cd不会改变Python进程的工作目录
            if command.startswith('cd '):
                target_dir = command[3:].strip()
                # 如果是相对路径，基于当前工作目录
                if not os.path.isabs(target_dir):
                    target_dir = os.path.join(working_directory, target_dir)
                logger.info(f"🔄 [shell_command] 尝试切换到目录: {target_dir}")
                # 检查目标目录是否存在
                if os.path.exists(target_dir) and os.path.isdir(target_dir):
                    logger.info(f"✅ [shell_command] 成功切换工作目录到: {target_dir}")
                    return {
                        'success': True,
                        'message': f'Changed working directory to: {target_dir}',
                        'output': f'Directory changed to: {target_dir}',
                        'data': {
                            'working_directory': target_dir,
                            'previous_directory': working_directory
                        }
                    }
                else:
                    logger.error(f"❌ [shell_command] 目标目录不存在: {target_dir}")
                    return {
                        'success': False,
                        'error': f'Directory not found: {target_dir}',
                        'output': '',
                        'data': {
                            'working_directory': working_directory
                        }
                    }
            # 执行其他shell命令
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=working_directory,
                timeout=step.timeout_seconds
            )
            # 执行后打印目录状态
            logger.info(f"📁 [shell_command] 执行后目录内容: {os.listdir(working_directory) if os.path.exists(working_directory) else '目录不存在'}")
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'Shell command completed: {step.name}',
                    'output': result.stdout,
                    'data': {
                        'exit_code': result.returncode,
                        'working_directory': working_directory
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f'Command failed with exit code {result.returncode}: {result.stderr}',
                    'output': result.stdout,
                    'data': {
                        'exit_code': result.returncode,
                        'working_directory': working_directory
                    }
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Command timeout after {step.timeout_seconds} seconds',
                'output': '',
                'data': {}
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': '',
                'data': {}
            }

    def _execute_fetch_code_step(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行代码拉取步骤"""
        import subprocess
        import os
        
        try:
            working_directory = context.get('working_directory', os.getcwd())
            
            # 打印当前工作目录信息
            logger.info(f"📁 [fetch_code] 当前工作目录: {working_directory}")
            logger.info(f"📁 [fetch_code] 目录内容: {os.listdir(working_directory) if os.path.exists(working_directory) else '目录不存在'}")
            
            # 从step.command中获取git命令（fetch_code类型主要使用command字段）
            git_command = step.command
            
            if not git_command:
                return {
                    'success': False,
                    'error': 'No git command specified in command field',
                    'output': '',
                    'data': {}
                }
            
            logger.info(f"🚀 [fetch_code] 执行命令: {git_command}")
            
            # 执行git命令
            result = subprocess.run(
                git_command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=working_directory,
                timeout=step.timeout_seconds
            )
            
            # 执行后打印目录状态
            logger.info(f"📁 [fetch_code] 执行后目录内容: {os.listdir(working_directory) if os.path.exists(working_directory) else '目录不存在'}")
            
            if result.returncode == 0:
                # 检查是否有新的代码目录被创建
                after_dirs = [d for d in os.listdir(working_directory) if os.path.isdir(os.path.join(working_directory, d))]
                
                return {
                    'success': True,
                    'message': f'Code fetch completed: {step.name}',
                    'output': result.stdout,
                    'data': {
                        'working_directory': working_directory,
                        'created_directories': after_dirs
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f'Git command failed: {result.stderr}',
                    'output': result.stdout,
                    'data': {}
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Command timeout after {step.timeout_seconds} seconds',
                'output': '',
                'data': {}
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': '',
                'data': {}
            }
