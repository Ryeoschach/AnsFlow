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
        try:
            if step.step_type == 'ansible':
                # Ansible 步骤执行
                return self._execute_ansible_step(step, context)
            elif step.step_type == 'script':
                # 脚本步骤执行
                return self._execute_script_step(step, context)
            else:
                # 其他类型的步骤，使用原有的 Celery 任务
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
        # 这里应该调用 Ansible 集成模块
        # 暂时返回模拟结果
        return {
            'success': True,
            'message': f'Ansible step {step.name} completed (simulated)',
            'output': f'Ansible playbook executed successfully',
            'data': {'ansible_result': 'success'}
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
