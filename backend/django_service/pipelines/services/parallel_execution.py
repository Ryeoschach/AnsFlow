"""
并行执行服务
负责处理流水线中的并行组执行逻辑，支持本地和远程并行执行
"""
import logging
import asyncio
import time
import json
import statistics
import hashlib
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from ..models import Pipeline, PipelineRun, ParallelGroup
from cicd_integrations.models import AtomicStep, StepExecution, PipelineExecution
from pipelines.services.local_executor import LocalPipelineExecutor
# from cicd_integrations.executors.remote_executor import RemoteStepExecutor  # 暂时禁用

# 可选依赖
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

logger = logging.getLogger(__name__)


class ParallelExecutionService:
    """并行执行服务"""
    
    def __init__(self):
        self.local_executor = LocalPipelineExecutor()
        # self.remote_executor = RemoteStepExecutor()  # 暂时禁用
        self.remote_executor = None
        self.max_parallel_workers = 10  # 最大并行工作线程数
    
    def analyze_pipeline_execution_plan(self, pipeline: Pipeline) -> Dict[str, Any]:
        """
        分析流水线的执行计划，识别并行组和依赖关系
        
        Returns:
            执行计划，包含步骤分组、依赖关系和执行顺序
        """
        steps = list(pipeline.atomic_steps.all().order_by('order'))
        parallel_groups = {}
        sequential_steps = []
        execution_plan = {
            'stages': [],  # 执行阶段列表
            'parallel_groups': {},
            'dependencies': {},
            'total_stages': 0
        }
        
        # 收集并行组信息
        for step in steps:
            if hasattr(step, 'parallel_group') and step.parallel_group:
                group_id = step.parallel_group
                if group_id not in parallel_groups:
                    parallel_groups[group_id] = {
                        'id': group_id,
                        'name': f"并行组-{group_id[:8]}",
                        'steps': [],
                        'sync_policy': 'wait_all',  # 默认等待所有步骤完成
                        'timeout_seconds': None,
                        'min_order': float('inf'),
                        'max_order': 0
                    }
                
                parallel_groups[group_id]['steps'].append(step)
                parallel_groups[group_id]['min_order'] = min(parallel_groups[group_id]['min_order'], step.order)
                parallel_groups[group_id]['max_order'] = max(parallel_groups[group_id]['max_order'], step.order)
                logger.info(f"Added step {step.name} to parallel group {group_id} with order {step.order}")
            else:
                sequential_steps.append(step)
                logger.info(f"Added step {step.name} to sequential execution with order {step.order}")
        
        logger.info(f"Found {len(parallel_groups)} parallel groups and {len(sequential_steps)} sequential steps")
        
        # 创建执行阶段
        # 按照 order 字段排序，将并行组和单独步骤安排到不同的阶段
        all_items = []
        
        # 添加单独步骤
        for step in sequential_steps:
            all_items.append({
                'type': 'step',
                'order': step.order,
                'item': step,
                'parallel': False
            })
        
        # 添加并行组（使用最小order作为组的order）
        for group_id, group_info in parallel_groups.items():
            all_items.append({
                'type': 'parallel_group',
                'order': group_info['min_order'],
                'item': group_info,
                'parallel': True
            })
        
        # 按order排序
        all_items.sort(key=lambda x: x['order'])
        
        # 构建执行阶段
        stage_number = 0
        for item in all_items:
            stage = {
                'stage_number': stage_number,
                'type': item['type'],
                'parallel': item['parallel'],
                'items': []
            }
            
            if item['type'] == 'step':
                stage['items'] = [item['item']]
            else:  # parallel_group
                stage['items'] = item['item']['steps']
                stage['group_info'] = item['item']
            
            execution_plan['stages'].append(stage)
            stage_number += 1
        
        execution_plan['total_stages'] = stage_number
        execution_plan['parallel_groups'] = parallel_groups
        
        logger.info(f"Pipeline {pipeline.id} execution plan: {stage_number} stages, {len(parallel_groups)} parallel groups")
        return execution_plan
    
    def execute_pipeline_with_parallel_support(self, 
                                              pipeline: Pipeline, 
                                              pipeline_run: PipelineRun, 
                                              execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据执行计划执行流水线，支持并行组
        """
        logger.info(f"Starting pipeline {pipeline.id} execution with parallel support")
        
        try:
            # 创建流水线执行记录
            pipeline_execution = self._create_pipeline_execution(pipeline, pipeline_run)
            
            # 按阶段执行
            for stage in execution_plan['stages']:
                stage_result = self._execute_stage(
                    stage, 
                    pipeline, 
                    pipeline_execution, 
                    execution_plan
                )
                
                if not stage_result['success']:
                    logger.error(f"Stage {stage['stage_number']} failed: {stage_result['message']}")
                    return {
                        'success': False,
                        'message': f"Pipeline failed at stage {stage['stage_number']}: {stage_result['message']}",
                        'failed_stage': stage['stage_number']
                    }
            
            # 所有阶段完成
            pipeline_execution.status = 'success'
            pipeline_execution.completed_at = timezone.now()
            pipeline_execution.save()
            
            return {
                'success': True,
                'message': 'Pipeline completed successfully',
                'execution_id': pipeline_execution.id
            }
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            if 'pipeline_execution' in locals():
                pipeline_execution.status = 'failed'
                pipeline_execution.completed_at = timezone.now()
                pipeline_execution.save()
            
            return {
                'success': False,
                'message': f'Pipeline execution failed: {str(e)}'
            }
    
    def _execute_stage(self, 
                      stage: Dict[str, Any], 
                      pipeline: Pipeline, 
                      pipeline_execution,
                      execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个阶段（可能包含并行步骤）
        """
        stage_number = stage['stage_number']
        is_parallel = stage['parallel']
        steps = stage['items']
        
        logger.info(f"开始执行阶段 {stage_number}: {'并行' if is_parallel else '串行'} 执行，包含 {len(steps)} 个步骤")
        
        if is_parallel:
            group_info = stage.get('group_info', {})
            logger.info(f"  - 并行组ID: {group_info.get('id', 'N/A')}")
            logger.info(f"  - 同步策略: {group_info.get('sync_policy', 'wait_all')}")
            return self._execute_parallel_stage(stage, pipeline, pipeline_execution)
        else:
            return self._execute_sequential_stage(stage, pipeline, pipeline_execution)
    
    def _execute_parallel_stage(self, 
                               stage: Dict[str, Any], 
                               pipeline: Pipeline, 
                               pipeline_execution) -> Dict[str, Any]:
        """
        执行并行阶段
        """
        steps = stage['items']
        group_info = stage.get('group_info', {})
        sync_policy = group_info.get('sync_policy', 'wait_all')
        timeout_seconds = group_info.get('timeout_seconds')
        
        logger.info(f"Executing parallel stage with {len(steps)} steps, sync_policy: {sync_policy}")
        
        # 根据执行模式选择并行执行策略
        if pipeline.execution_mode == 'local':
            return self._execute_parallel_local(steps, pipeline_execution, sync_policy, timeout_seconds)
        elif pipeline.execution_mode == 'remote':
            return self._execute_parallel_remote(steps, pipeline, pipeline_execution, sync_policy)
        else:  # hybrid
            return self._execute_parallel_hybrid(steps, pipeline, pipeline_execution, sync_policy)
    
    def _execute_parallel_local(self, 
                               steps: List[AtomicStep], 
                               pipeline_execution,
                               sync_policy: str = 'wait_all',
                               timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        本地并行执行（使用线程池）
        """
        logger.info(f"开始本地并行执行 {len(steps)} 个步骤，同步策略: {sync_policy}")
        
        # 打印步骤信息
        for step in steps:
            logger.info(f"  - 步骤: {step.name}, 顺序: {step.order}, 类型: {step.step_type}")
        
        step_executions = []
        for step in steps:
            step_execution = StepExecution.objects.create(
                pipeline_execution=pipeline_execution,
                atomic_step=step,
                status='pending',
                order=step.order
            )
            step_executions.append(step_execution)
        
        # 使用线程池执行并行步骤
        results = []
        logger.info(f"创建线程池，最大工作线程数: {min(len(steps), self.max_parallel_workers)}")
        
        with ThreadPoolExecutor(max_workers=min(len(steps), self.max_parallel_workers)) as executor:
            # 提交所有任务
            future_to_step = {
                executor.submit(self._execute_step_local, step_execution): step_execution
                for step_execution in step_executions
            }
            
            logger.info(f"已提交 {len(future_to_step)} 个并行任务到线程池")
            
            # 等待结果
            completed_count = 0
            failed_count = 0
            
            try:
                for future in as_completed(future_to_step, timeout=timeout_seconds):
                    step_execution = future_to_step[future]
                    try:
                        result = future.result()
                        results.append(result)
                        
                        if result['success']:
                            completed_count += 1
                            step_execution.status = 'success'
                            logger.info(f"步骤 {step_execution.atomic_step.name} 执行成功")
                        else:
                            failed_count += 1
                            step_execution.status = 'failed'
                            step_execution.error_message = result.get('error', 'Unknown error')
                            logger.error(f"步骤 {step_execution.atomic_step.name} 执行失败: {result.get('error', 'Unknown error')}")
                        
                        step_execution.completed_at = timezone.now()
                        step_execution.save()
                        
                        # 根据同步策略决定是否提前退出
                        if sync_policy == 'fail_fast' and failed_count > 0:
                            logger.info("Fail-fast策略触发，取消剩余任务")
                            break
                        elif sync_policy == 'wait_any' and completed_count > 0:
                            logger.info("Wait-any策略满足，取消剩余任务")
                            break
                            
                    except Exception as e:
                        logger.error(f"步骤执行异常: {e}")
                        step_execution.status = 'failed'
                        step_execution.error_message = str(e)
                        step_execution.completed_at = timezone.now()
                        step_execution.save()
                        failed_count += 1
            
            except asyncio.TimeoutError:
                logger.error(f"并行执行超时，超时时间: {timeout_seconds} 秒")
                return {
                    'success': False,
                    'message': f'并行执行超时，超时时间: {timeout_seconds} 秒'
                }
        
        # 评估整体结果
        total_steps = len(steps)
        success = self._evaluate_parallel_result(sync_policy, completed_count, failed_count, total_steps)
        
        logger.info(f"并行执行完成: {completed_count} 成功, {failed_count} 失败, 总体结果: {'成功' if success else '失败'}")
        
        return {
            'success': success,
            'message': f'并行执行完成: {completed_count} 成功, {failed_count} 失败',
            'completed_count': completed_count,
            'failed_count': failed_count,
            'sync_policy': sync_policy
        }
    
    def _execute_parallel_remote(self, 
                                steps: List[AtomicStep], 
                                pipeline: Pipeline,
                                pipeline_execution,
                                sync_policy: str = 'wait_all') -> Dict[str, Any]:
        """
        远程并行执行（转换为目标CI/CD工具的并行语法）
        """
        tool = pipeline.execution_tool
        if not tool:
            return {
                'success': False,
                'message': 'No execution tool configured for remote parallel execution'
            }
        
        if tool.tool_type == 'jenkins':
            return self._execute_parallel_jenkins(steps, pipeline, pipeline_execution, sync_policy)
        elif tool.tool_type == 'gitlab_ci':
            return self._execute_parallel_gitlab(steps, pipeline, pipeline_execution, sync_policy)
        elif tool.tool_type == 'github_actions':
            return self._execute_parallel_github(steps, pipeline, pipeline_execution, sync_policy)
        else:
            return {
                'success': False,
                'message': f'Parallel execution not supported for tool type: {tool.tool_type}'
            }
    
    def _execute_parallel_jenkins(self, 
                                 steps: List[AtomicStep], 
                                 pipeline: Pipeline,
                                 pipeline_execution,
                                 sync_policy: str) -> Dict[str, Any]:
        """
        转换为Jenkins并行执行语法
        """
        logger.info(f"Converting {len(steps)} steps to Jenkins parallel syntax")
        
        # 生成Jenkins Pipeline并行代码
        parallel_code = self._generate_jenkins_parallel_code(steps, sync_policy)
        
        # 更新Jenkins作业配置
        tool = pipeline.execution_tool
        jenkins_service = self._get_jenkins_service(tool)
        
        try:
            # 执行Jenkins作业
            build_result = jenkins_service.trigger_parallel_build(
                job_name=pipeline.tool_job_name,
                parallel_code=parallel_code,
                parameters=pipeline_execution.parameters
            )
            
            # 创建步骤执行记录
            for step in steps:
                StepExecution.objects.create(
                    pipeline_execution=pipeline_execution,
                    atomic_step=step,
                    external_id=build_result.get('build_number'),
                    status='running',
                    order=step.order
                )
            
            return {
                'success': True,
                'message': 'Jenkins parallel execution started',
                'build_number': build_result.get('build_number'),
                'jenkins_url': build_result.get('url')
            }
            
        except Exception as e:
            logger.error(f"Jenkins parallel execution failed: {e}")
            return {
                'success': False,
                'message': f'Jenkins parallel execution failed: {str(e)}'
            }
    
    def _generate_jenkins_parallel_code(self, steps: List[AtomicStep], sync_policy: str) -> str:
        """
        生成Jenkins Pipeline的并行执行代码
        """
        parallel_blocks = []
        
        for step in steps:
            step_name = step.name.replace(' ', '_').replace('-', '_')
            step_code = f'''
            "{step_name}": {{
                node {{
                    stage("{step.name}") {{
                        try {{
                            {self._convert_step_to_jenkins_code(step)}
                        }} catch (Exception e) {{
                            currentBuild.result = 'FAILURE'
                            throw e
                        }}
                    }}
                }}
            }}'''
            parallel_blocks.append(step_code)
        
        # 根据同步策略添加失败处理
        fail_fast = "true" if sync_policy == "fail_fast" else "false"
        
        jenkins_code = f'''
        pipeline {{
            agent any
            stages {{
                stage('Parallel Execution') {{
                    steps {{
                        script {{
                            parallel(
                                failFast: {fail_fast},
                                {','.join(parallel_blocks)}
                            )
                        }}
                    }}
                }}
            }}
        }}
        '''
        
        return jenkins_code
    
    def _convert_step_to_jenkins_code(self, step: AtomicStep) -> str:
        """
        将步骤转换为Jenkins执行代码
        """
        if step.step_type == 'shell':
            return f'sh """{step.config.get("command", "")}"""'
        elif step.step_type == 'python':
            script = step.config.get("script", "")
            return f'sh """python3 -c \'{script}\' """'
        elif step.step_type == 'docker':
            image = step.config.get('image', 'ubuntu:latest')
            command = step.config.get('command', 'echo "Hello World"')
            return f'sh """docker run --rm {image} {command}"""'
        else:
            return f'echo "Executing step: {step.name}"'
    
    def _execute_sequential_stage(self, 
                                 stage: Dict[str, Any], 
                                 pipeline: Pipeline, 
                                 pipeline_execution) -> Dict[str, Any]:
        """
        执行顺序阶段
        """
        steps = stage['items']
        logger.info(f"Executing sequential stage with {len(steps)} steps")
        
        for step in steps:
            step_execution = StepExecution.objects.create(
                pipeline_execution=pipeline_execution,
                atomic_step=step,
                status='running',
                order=step.order
            )
            
            try:
                result = self._execute_step_local(step_execution)
                
                if result['success']:
                    step_execution.status = 'success'
                else:
                    step_execution.status = 'failed'
                    step_execution.error_message = result.get('error', 'Unknown error')
                    step_execution.completed_at = timezone.now()
                    step_execution.save()
                    
                    return {
                        'success': False,
                        'message': f'Step {step.name} failed: {result.get("error", "Unknown error")}',
                        'failed_step': step.name
                    }
                
                step_execution.completed_at = timezone.now()
                step_execution.save()
                
            except Exception as e:
                logger.error(f"Step execution error: {e}")
                step_execution.status = 'failed'
                step_execution.error_message = str(e)
                step_execution.completed_at = timezone.now()
                step_execution.save()
                
                return {
                    'success': False,
                    'message': f'Step {step.name} failed: {str(e)}',
                    'failed_step': step.name
                }
        
        return {
            'success': True,
            'message': f'Sequential stage completed with {len(steps)} steps'
        }
    
    def _execute_step_local(self, step_execution) -> Dict[str, Any]:
        """
        本地执行单个步骤
        """
        try:
            step = step_execution.atomic_step
            logger.info(f"开始本地执行步骤: {step.name}")
            
            # 更新状态
            step_execution.status = 'running'
            step_execution.started_at = timezone.now()
            step_execution.save()
            
            # 执行步骤
            result = self.local_executor.execute_step(step)
            
            # 保存输出
            step_execution.logs = result.get('output', '')
            step_execution.output = result.get('result', {})
            
            logger.info(f"步骤 {step.name} 执行完成，结果: {'成功' if result['success'] else '失败'}")
            
            return result
            
        except Exception as e:
            logger.error(f"本地步骤执行失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _evaluate_parallel_result(self, sync_policy: str, completed: int, failed: int, total: int) -> bool:
        """
        根据同步策略评估并行执行结果
        """
        if sync_policy == 'wait_all':
            return failed == 0  # 所有步骤都必须成功
        elif sync_policy == 'wait_any':
            return completed > 0  # 至少一个步骤成功
        elif sync_policy == 'fail_fast':
            return failed == 0  # 没有失败的步骤
        else:
            return completed > failed  # 默认：成功多于失败
    
    def _create_pipeline_execution(self, pipeline: Pipeline, pipeline_run: PipelineRun):
        """
        创建流水线执行记录
        """
        from cicd_integrations.models import PipelineExecution
        
        return PipelineExecution.objects.create(
            pipeline=pipeline,
            status='running',
            trigger_type='manual',
            definition=pipeline.config,
            parameters=pipeline_run.trigger_data,
            started_at=timezone.now()
        )
    
    def _get_jenkins_service(self, tool):
        """
        获取Jenkins服务实例
        """
        # 这里应该返回Jenkins服务实例
        # 暂时返回模拟对象
        class MockJenkinsService:
            def trigger_parallel_build(self, job_name, parallel_code, parameters):
                return {
                    'build_number': 123,
                    'url': f'http://jenkins.example.com/job/{job_name}/123/'
                }
        
        return MockJenkinsService()
    
    def _execute_parallel_gitlab(self, 
                                steps: List[AtomicStep], 
                                pipeline: Pipeline,
                                pipeline_execution,
                                sync_policy: str) -> Dict[str, Any]:
        """
        转换为GitLab CI并行执行语法
        """
        logger.info(f"Converting {len(steps)} steps to GitLab CI parallel syntax")
        
        # 生成GitLab CI YAML配置
        gitlab_config = self._generate_gitlab_parallel_config(steps, sync_policy)
        
        # 更新GitLab项目配置
        tool = pipeline.execution_tool
        gitlab_service = self._get_gitlab_service(tool)
        
        try:
            # 触发GitLab Pipeline
            pipeline_result = gitlab_service.trigger_parallel_pipeline(
                project_id=pipeline.tool_project_id,
                gitlab_config=gitlab_config,
                variables=pipeline_execution.parameters,
                ref=pipeline.tool_branch or 'main'
            )
            
            # 创建步骤执行记录
            for step in steps:
                StepExecution.objects.create(
                    pipeline_execution=pipeline_execution,
                    atomic_step=step,
                    external_id=pipeline_result.get('pipeline_id'),
                    status='running',
                    order=step.order
                )
            
            return {
                'success': True,
                'message': 'GitLab CI parallel execution started',
                'pipeline_id': pipeline_result.get('pipeline_id'),
                'gitlab_url': pipeline_result.get('web_url')
            }
            
        except Exception as e:
            logger.error(f"GitLab CI parallel execution failed: {e}")
            return {
                'success': False,
                'message': f'GitLab CI parallel execution failed: {str(e)}'
            }
    
    def _execute_parallel_github(self, 
                                steps: List[AtomicStep], 
                                pipeline: Pipeline,
                                pipeline_execution,
                                sync_policy: str) -> Dict[str, Any]:
        """
        转换为GitHub Actions并行执行语法
        """
        logger.info(f"Converting {len(steps)} steps to GitHub Actions parallel syntax")
        
        # 生成GitHub Actions workflow配置
        workflow_config = self._generate_github_parallel_workflow(steps, sync_policy)
        
        # 更新GitHub仓库workflow
        tool = pipeline.execution_tool
        github_service = self._get_github_service(tool)
        
        try:
            # 触发GitHub Actions workflow
            workflow_result = github_service.trigger_parallel_workflow(
                owner=pipeline.tool_owner,
                repo=pipeline.tool_repo,
                workflow_config=workflow_config,
                inputs=pipeline_execution.parameters,
                ref=pipeline.tool_branch or 'main'
            )
            
            # 创建步骤执行记录
            for step in steps:
                StepExecution.objects.create(
                    pipeline_execution=pipeline_execution,
                    atomic_step=step,
                    external_id=workflow_result.get('run_id'),
                    status='running',
                    order=step.order
                )
            
            return {
                'success': True,
                'message': 'GitHub Actions parallel execution started',
                'run_id': workflow_result.get('run_id'),
                'github_url': workflow_result.get('html_url')
            }
            
        except Exception as e:
            logger.error(f"GitHub Actions parallel execution failed: {e}")
            return {
                'success': False,
                'message': f'GitHub Actions parallel execution failed: {str(e)}'
            }

    def _execute_parallel_hybrid(self, 
                               steps: List[AtomicStep], 
                               pipeline: Pipeline,
                               pipeline_execution,
                               sync_policy: str) -> Dict[str, Any]:
        """
        混合模式并行执行：智能分配本地和远程执行
        """
        logger.info(f"Hybrid parallel execution of {len(steps)} steps")
        
        # 分析步骤，决定执行位置
        local_steps = []
        remote_steps = []
        
        for step in steps:
            if self._should_execute_locally_in_parallel(step):
                local_steps.append(step)
            else:
                remote_steps.append(step)
        
        logger.info(f"Hybrid allocation: {len(local_steps)} local, {len(remote_steps)} remote")
        
        # 并行执行本地和远程步骤
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        results = []
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            
            # 提交本地并行任务
            if local_steps:
                local_future = executor.submit(
                    self._execute_parallel_local,
                    local_steps, pipeline_execution, sync_policy
                )
                futures.append(('local', local_future))
            
            # 提交远程并行任务
            if remote_steps:
                remote_future = executor.submit(
                    self._execute_parallel_remote,
                    remote_steps, pipeline, pipeline_execution, sync_policy
                )
                futures.append(('remote', remote_future))
            
            # 等待所有任务完成
            for task_type, future in futures:
                try:
                    result = future.result()
                    result['task_type'] = task_type
                    results.append(result)
                except Exception as e:
                    logger.error(f"Hybrid {task_type} execution failed: {e}")
                    results.append({
                        'success': False,
                        'message': f'{task_type} execution failed: {str(e)}',
                        'task_type': task_type
                    })
        
        # 评估混合执行结果
        total_success = all(r.get('success', False) for r in results)
        
        return {
            'success': total_success,
            'message': f'Hybrid parallel execution completed',
            'results': results,
            'local_steps_count': len(local_steps),
            'remote_steps_count': len(remote_steps)
        }

    def _generate_gitlab_parallel_config(self, steps: List[AtomicStep], sync_policy: str) -> str:
        """
        生成GitLab CI的并行执行配置
        """
        jobs = {}
        
        # 生成并行作业
        for step in steps:
            job_name = step.name.replace(' ', '_').replace('-', '_').lower()
            
            job_config = {
                'stage': 'parallel_execution',
                'script': self._convert_step_to_gitlab_script(step),
                'parallel': 1,  # 标记为并行作业
            }
            
            # 根据步骤类型添加特殊配置
            if step.step_type == 'docker':
                job_config['image'] = step.config.get('image', 'ubuntu:latest')
            
            # 添加失败策略
            if sync_policy == 'fail_fast':
                job_config['allow_failure'] = False
            elif sync_policy == 'wait_any':
                job_config['allow_failure'] = True
            
            jobs[job_name] = job_config
        
        # 构建完整的GitLab CI配置
        gitlab_config = {
            'stages': ['parallel_execution'],
            **jobs
        }
        
        try:
            import yaml
            return yaml.dump(gitlab_config, default_flow_style=False)
        except ImportError:
            logger.warning("PyYAML not installed, returning JSON format")
            import json
            return json.dumps(gitlab_config, indent=2)
    
    def _generate_github_parallel_workflow(self, steps: List[AtomicStep], sync_policy: str) -> str:
        """
        生成GitHub Actions的并行workflow配置
        """
        jobs = {}
        
        # 生成并行作业
        for step in steps:
            job_name = step.name.replace(' ', '_').replace('-', '_').lower()
            
            job_config = {
                'runs-on': 'ubuntu-latest',
                'steps': [
                    {
                        'name': 'Checkout code',
                        'uses': 'actions/checkout@v3'
                    },
                    {
                        'name': step.name,
                        'run': self._convert_step_to_github_script(step)
                    }
                ]
            }
            
            # 根据步骤类型添加特殊配置
            if step.step_type == 'docker':
                job_config['container'] = step.config.get('image', 'ubuntu:latest')
            
            # 添加失败策略
            if sync_policy != 'fail_fast':
                job_config['continue-on-error'] = True
            
            jobs[job_name] = job_config
        
        # 构建完整的GitHub Actions workflow
        workflow_config = {
            'name': 'Parallel Execution Workflow',
            'on': {
                'workflow_dispatch': {
                    'inputs': {}
                }
            },
            'jobs': jobs
        }
        
        try:
            import yaml
            return yaml.dump(workflow_config, default_flow_style=False)
        except ImportError:
            logger.warning("PyYAML not installed, returning JSON format")
            import json
            return json.dumps(workflow_config, indent=2)
    
    def _convert_step_to_gitlab_script(self, step: AtomicStep) -> List[str]:
        """
        将步骤转换为GitLab CI脚本
        """
        if step.step_type == 'shell':
            return [step.config.get("command", "echo 'No command specified'")]
        elif step.step_type == 'python':
            script = step.config.get("script", "print('Hello World')")
            return [f'python3 -c "{script}"']
        elif step.step_type == 'docker':
            command = step.config.get('command', 'echo "Hello World"')
            return [command]
        else:
            return [f'echo "Executing step: {step.name}"']
    
    def _convert_step_to_github_script(self, step: AtomicStep) -> str:
        """
        将步骤转换为GitHub Actions脚本
        """
        if step.step_type == 'shell':
            return step.config.get("command", "echo 'No command specified'")
        elif step.step_type == 'python':
            script = step.config.get("script", "print('Hello World')")
            return f'python3 -c "{script}"'
        elif step.step_type == 'docker':
            command = step.config.get('command', 'echo "Hello World"')
            return command
        else:
            return f'echo "Executing step: {step.name}"'
    
    def _should_execute_locally_in_parallel(self, step: AtomicStep) -> bool:
        """
        判断步骤是否应该在本地并行执行（混合模式下）
        """
        # 本地执行优先的步骤类型
        local_preferred_types = ['python', 'shell', 'file_operation']
        
        # 远程执行优先的步骤类型
        remote_preferred_types = ['docker', 'kubernetes', 'terraform']
        
        if step.step_type in local_preferred_types:
            return True
        elif step.step_type in remote_preferred_types:
            return False
        else:
            # 默认策略：简单步骤本地执行，复杂步骤远程执行
            config_complexity = len(str(step.config))
            return config_complexity < 500  # 配置简单的本地执行
    
    def _get_gitlab_service(self, tool):
        """
        获取GitLab服务实例
        """
        # 这里应该返回GitLab服务实例
        # 暂时返回模拟对象
        class MockGitLabService:
            def trigger_parallel_pipeline(self, project_id, gitlab_config, variables, ref):
                return {
                    'pipeline_id': 12345,
                    'web_url': f'https://gitlab.example.com/project/{project_id}/-/pipelines/12345'
                }
        
        return MockGitLabService()
    
    def _get_github_service(self, tool):
        """
        获取GitHub服务实例
        """
        # 这里应该返回GitHub服务实例
        # 暂时返回模拟对象
        class MockGitHubService:
            def trigger_parallel_workflow(self, owner, repo, workflow_config, inputs, ref):
                return {
                    'run_id': 67890,
                    'html_url': f'https://github.com/{owner}/{repo}/actions/runs/67890'
                }
        
        return MockGitHubService()

    def analyze_parallel_groups(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从步骤列表分析并行组
        
        Args:
            steps: 步骤列表，每个步骤包含 name, step_type, order, parallel_group 等字段
            
        Returns:
            并行组列表，每个组包含 name, order, steps 字段
        """
        logger.info(f"analyze_parallel_groups 开始分析，收到 {len(steps)} 个步骤")
        for i, step in enumerate(steps):
            logger.info(f"步骤 {i}: name={step.get('name')}, parallel_group={step.get('parallel_group')}, order={step.get('order')}")
            
        if not steps:
            return []
        
        # 首先检查是否有步骤明确指定了parallel_group
        explicit_groups = {}
        remaining_steps = []
        
        for step in steps:
            parallel_group = step.get('parallel_group')
            if parallel_group:
                # 有明确指定的并行组
                logger.info(f"发现并行组步骤: {step.get('name')} -> {parallel_group}")
                if parallel_group not in explicit_groups:
                    explicit_groups[parallel_group] = {
                        'id': parallel_group,
                        'name': f'parallel_group_{parallel_group}',
                        'steps': [],
                        'order': step.get('order', 0),
                        'parallel': True,
                        'sync_policy': 'wait_all'
                    }
                explicit_groups[parallel_group]['steps'].append(step)
                # 更新order为最小值
                explicit_groups[parallel_group]['order'] = min(
                    explicit_groups[parallel_group]['order'], 
                    step.get('order', 0)
                )
            else:
                logger.info(f"顺序步骤: {step.get('name')} (无parallel_group)")
                remaining_steps.append(step)
        
        # 如果没有明确的并行组，则按order分组（相同order的步骤可以并行执行）
        parallel_groups = list(explicit_groups.values())
        logger.info(f"找到明确的并行组: {len(parallel_groups)} 个")
        
        if not parallel_groups and remaining_steps:
            # 按order分组，相同order的步骤可以并行执行
            order_groups = {}
            
            for step in remaining_steps:
                order = step.get('order', 0)
                if order not in order_groups:
                    order_groups[order] = []
                order_groups[order].append(step)
            
            # 检查每个order组，如果包含多个步骤，则创建并行组
            for order, group_steps in order_groups.items():
                if len(group_steps) > 1:
                    # 创建并行组
                    parallel_group = {
                        'id': f'auto_parallel_order_{order}',
                        'name': f'parallel_group_order_{order}',
                        'order': order,
                        'steps': group_steps,
                        'parallel': True,
                        'sync_policy': 'wait_all'  # 默认等待所有步骤完成
                    }
                    parallel_groups.append(parallel_group)
        
        logger.info(f"分析到 {len(parallel_groups)} 个并行组，总步骤数 {len(steps)}")
        for group in parallel_groups:
            logger.info(f"并行组 {group['name']}: {len(group['steps'])} 个步骤, order={group['order']}")
        
        return parallel_groups
    
    def execute_pipeline_with_performance_optimization(self, 
                                                     pipeline: Pipeline, 
                                                     pipeline_run: PipelineRun, 
                                                     execution_plan: Dict[str, Any],
                                                     optimization_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行流水线，包含性能优化策略
        
        Args:
            pipeline: 流水线对象
            pipeline_run: 流水线运行实例
            execution_plan: 执行计划
            optimization_config: 优化配置
                - batch_size: 批处理大小
                - adaptive_workers: 是否启用自适应工作线程
                - memory_threshold_mb: 内存阈值(MB)
                - enable_caching: 是否启用缓存
                - priority_scheduling: 是否启用优先级调度
        """
        if optimization_config is None:
            optimization_config = {
                'batch_size': 5,
                'adaptive_workers': True,
                'memory_threshold_mb': 1024,
                'enable_caching': True,
                'priority_scheduling': True
            }
        
        logger.info(f"Starting optimized pipeline {pipeline.id} execution")
        logger.info(f"Optimization config: {optimization_config}")
        
        # 性能监控
        start_time = timezone.now()
        performance_metrics = {
            'start_time': start_time,
            'stages_completed': 0,
            'parallel_groups_executed': 0,
            'total_steps_executed': 0,
            'memory_peaks': [],
            'execution_times': []
        }
        
        try:
            # 创建流水线执行记录
            pipeline_execution = self._create_pipeline_execution(pipeline, pipeline_run)
            
            # 自适应工作线程池配置
            if optimization_config.get('adaptive_workers', True):
                optimal_workers = self._calculate_optimal_workers(execution_plan)
                self.max_parallel_workers = optimal_workers
                logger.info(f"Adaptive workers: using {optimal_workers} threads")
            
            # 资源池初始化
            resource_pool = self._initialize_resource_pool(optimization_config)
            
            # 按阶段执行，支持批处理
            stages = execution_plan['stages']
            batch_size = optimization_config.get('batch_size', 5)
            
            # 将大型并行组分批处理
            optimized_stages = self._optimize_stage_batching(stages, batch_size)
            
            for stage_batch in optimized_stages:
                batch_start_time = timezone.now()
                
                # 内存检查
                if self._check_memory_threshold(optimization_config.get('memory_threshold_mb', 1024)):
                    logger.warning("Memory threshold exceeded, triggering garbage collection")
                    self._perform_memory_cleanup()
                
                # 执行批次
                batch_result = self._execute_stage_batch(
                    stage_batch, 
                    pipeline, 
                    pipeline_execution,
                    resource_pool,
                    optimization_config
                )
                
                if not batch_result['success']:
                    logger.error(f"Stage batch failed: {batch_result['message']}")
                    return {
                        'success': False,
                        'message': f"Pipeline failed: {batch_result['message']}",
                        'performance_metrics': performance_metrics
                    }
                
                # 更新性能指标
                batch_end_time = timezone.now()
                performance_metrics['stages_completed'] += len(stage_batch)
                performance_metrics['execution_times'].append(
                    (batch_end_time - batch_start_time).total_seconds()
                )
                
                # 记录内存使用
                memory_usage = self._get_current_memory_usage()
                performance_metrics['memory_peaks'].append(memory_usage)
            
            # 流水线完成
            end_time = timezone.now()
            total_execution_time = (end_time - start_time).total_seconds()
            
            pipeline_execution.status = 'success'
            pipeline_execution.completed_at = end_time
            pipeline_execution.save()
            
            # 更新最终性能指标
            performance_metrics.update({
                'end_time': end_time,
                'total_execution_time': total_execution_time,
                'avg_stage_time': statistics.mean(performance_metrics['execution_times']) if performance_metrics['execution_times'] else 0,
                'peak_memory_mb': max(performance_metrics['memory_peaks']) if performance_metrics['memory_peaks'] else 0
            })
            
            logger.info(f"Optimized pipeline completed in {total_execution_time:.2f}s")
            
            return {
                'success': True,
                'message': 'Pipeline completed successfully with performance optimization',
                'execution_id': pipeline_execution.id,
                'performance_metrics': performance_metrics
            }
            
        except Exception as e:
            logger.error(f"Optimized pipeline execution failed: {e}")
            if 'pipeline_execution' in locals():
                pipeline_execution.status = 'failed'
                pipeline_execution.completed_at = timezone.now()
                pipeline_execution.save()
            
            return {
                'success': False,
                'message': f'Optimized pipeline execution failed: {str(e)}',
                'performance_metrics': performance_metrics
            }
    
    def _calculate_optimal_workers(self, execution_plan: Dict[str, Any]) -> int:
        """计算最优工作线程数"""
        if PSUTIL_AVAILABLE:
            cpu_count = psutil.cpu_count()
        else:
            cpu_count = 4  # 默认值
        
        # 分析并行组的复杂度
        total_parallel_steps = 0
        max_group_size = 0
        
        for stage in execution_plan['stages']:
            if stage['parallel']:
                group_size = len(stage['items'])
                total_parallel_steps += group_size
                max_group_size = max(max_group_size, group_size)
        
        # 自适应算法
        if total_parallel_steps == 0:
            return min(4, cpu_count)  # 顺序执行，少量线程即可
        
        # 基于CPU核心数和并行步骤数计算
        optimal_workers = min(
            cpu_count * 2,  # 不超过CPU核心数的2倍
            max_group_size + 2,  # 基于最大并行组大小
            total_parallel_steps,  # 不超过总并行步骤数
            20  # 硬限制
        )
        
        return max(2, optimal_workers)  # 至少2个线程
    
    def _initialize_resource_pool(self, optimization_config: Dict[str, Any]) -> Dict[str, Any]:
        """初始化资源池"""
        return {
            'step_cache': {} if optimization_config.get('enable_caching', True) else None,
            'execution_history': [],
            'resource_locks': {},
            'priority_queue': [] if optimization_config.get('priority_scheduling', True) else None
        }
    
    def _optimize_stage_batching(self, stages: List[Dict[str, Any]], batch_size: int) -> List[List[Dict[str, Any]]]:
        """优化阶段批处理，将大型并行组分批"""
        optimized_batches = []
        current_batch = []
        
        for stage in stages:
            if stage['parallel'] and len(stage['items']) > batch_size:
                # 大型并行组分批处理
                if current_batch:
                    optimized_batches.append(current_batch)
                    current_batch = []
                
                # 将大型并行组拆分为多个小批次
                items = stage['items']
                for i in range(0, len(items), batch_size):
                    batch_items = items[i:i + batch_size]
                    sub_stage = {
                        **stage,
                        'items': batch_items,
                        'original_group_size': len(items),
                        'batch_index': i // batch_size,
                        'is_sub_batch': True
                    }
                    optimized_batches.append([sub_stage])
            else:
                current_batch.append(stage)
                
                # 如果当前批次已满，开始新批次
                if len(current_batch) >= batch_size:
                    optimized_batches.append(current_batch)
                    current_batch = []
        
        # 处理最后一个批次
        if current_batch:
            optimized_batches.append(current_batch)
        
        return optimized_batches
    
    def _execute_stage_batch(self, 
                           stage_batch: List[Dict[str, Any]], 
                           pipeline: Pipeline, 
                           pipeline_execution,
                           resource_pool: Dict[str, Any],
                           optimization_config: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段批次"""
        try:
            for stage in stage_batch:
                stage_result = self._execute_stage_optimized(
                    stage, 
                    pipeline, 
                    pipeline_execution,
                    resource_pool,
                    optimization_config
                )
                
                if not stage_result['success']:
                    return stage_result
            
            return {'success': True, 'message': 'Stage batch completed successfully'}
            
        except Exception as e:
            logger.error(f"Stage batch execution failed: {e}")
            return {'success': False, 'message': f'Stage batch failed: {str(e)}'}
    
    def _execute_stage_optimized(self, 
                               stage: Dict[str, Any], 
                               pipeline: Pipeline, 
                               pipeline_execution,
                               resource_pool: Dict[str, Any],
                               optimization_config: Dict[str, Any]) -> Dict[str, Any]:
        """执行优化的阶段"""
        if stage['parallel']:
            return self._execute_parallel_stage_optimized(
                stage, pipeline, pipeline_execution, resource_pool, optimization_config
            )
        else:
            return self._execute_sequential_stage_optimized(
                stage, pipeline, pipeline_execution, resource_pool, optimization_config
            )
    
    def _execute_parallel_stage_optimized(self, 
                                        stage: Dict[str, Any], 
                                        pipeline: Pipeline, 
                                        pipeline_execution,
                                        resource_pool: Dict[str, Any],
                                        optimization_config: Dict[str, Any]) -> Dict[str, Any]:
        """执行优化的并行阶段"""
        steps = stage['items']
        group_info = stage.get('group_info', {})
        
        logger.info(f"Executing optimized parallel stage with {len(steps)} steps")
        
        # 优先级调度
        if optimization_config.get('priority_scheduling', True):
            steps = self._sort_steps_by_priority(steps)
        
        # 使用优化的线程池
        with ThreadPoolExecutor(max_workers=self.max_parallel_workers) as executor:
            # 提交所有步骤
            futures = {}
            for step in steps:
                # 检查缓存
                if self._check_step_cache(step, resource_pool):
                    continue
                
                future = executor.submit(
                    self._execute_step_with_monitoring, 
                    step, 
                    pipeline, 
                    pipeline_execution,
                    resource_pool
                )
                futures[future] = step
            
            # 收集结果
            successful_steps = 0
            failed_steps = []
            
            for future in as_completed(futures, timeout=group_info.get('timeout_seconds', 300)):
                step = futures[future]
                try:
                    result = future.result()
                    if result['success']:
                        successful_steps += 1
                        # 更新缓存
                        self._update_step_cache(step, result, resource_pool)
                    else:
                        failed_steps.append((step, result['message']))
                        
                except Exception as e:
                    logger.error(f"Step {step.get('name', 'unknown')} failed: {e}")
                    failed_steps.append((step, str(e)))
            
            # 根据同步策略判断成功
            sync_policy = group_info.get('sync_policy', 'wait_all')
            if sync_policy == 'wait_all' and failed_steps:
                return {
                    'success': False,
                    'message': f'Parallel stage failed: {len(failed_steps)} steps failed'
                }
            elif sync_policy == 'wait_any' and successful_steps == 0:
                return {
                    'success': False,
                    'message': 'Parallel stage failed: no steps succeeded'
                }
            
            return {
                'success': True,
                'message': f'Parallel stage completed: {successful_steps} succeeded, {len(failed_steps)} failed'
            }
    
    def _execute_sequential_stage_optimized(self, 
                                          stage: Dict[str, Any], 
                                          pipeline: Pipeline, 
                                          pipeline_execution,
                                          resource_pool: Dict[str, Any],
                                          optimization_config: Dict[str, Any]) -> Dict[str, Any]:
        """执行优化的顺序阶段"""
        steps = stage['items']
        
        for step in steps:
            # 检查缓存
            if self._check_step_cache(step, resource_pool):
                continue
            
            result = self._execute_step_with_monitoring(
                step, 
                pipeline, 
                pipeline_execution,
                resource_pool
            )
            
            if not result['success']:
                return {
                    'success': False,
                    'message': f'Sequential step failed: {result["message"]}'
                }
            
            # 更新缓存
            self._update_step_cache(step, result, resource_pool)
        
        return {'success': True, 'message': 'Sequential stage completed'}
    
    def _execute_step_with_monitoring(self, 
                                    step: Any, 
                                    pipeline: Pipeline, 
                                    pipeline_execution,
                                    resource_pool: Dict[str, Any]) -> Dict[str, Any]:
        """执行步骤并监控性能"""
        step_start_time = time.time()
        
        try:
            # 执行步骤（这里应该调用实际的步骤执行逻辑）
            result = self.local_executor.execute_step(step, {})
            
            # 记录执行时间
            execution_time = time.time() - step_start_time
            resource_pool['execution_history'].append({
                'step_id': getattr(step, 'id', 'unknown'),
                'execution_time': execution_time,
                'success': result.get('success', False),
                'timestamp': timezone.now()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Step monitoring failed: {e}")
            return {'success': False, 'message': str(e)}
    
    def _sort_steps_by_priority(self, steps: List[Any]) -> List[Any]:
        """根据优先级排序步骤"""
        def get_priority(step):
            # 基于预估执行时间和依赖关系计算优先级
            estimated_time = getattr(step, 'estimated_duration', 0) or 0
            dependencies_count = len(getattr(step, 'dependencies', []))
            
            # 短作业优先 + 依赖关系考虑
            return estimated_time + dependencies_count * 10
        
        return sorted(steps, key=get_priority)
    
    def _check_step_cache(self, step: Any, resource_pool: Dict[str, Any]) -> bool:
        """检查步骤缓存"""
        if not resource_pool.get('step_cache'):
            return False
        
        step_id = getattr(step, 'id', None)
        if not step_id:
            return False
        
        # 简单的缓存策略：基于步骤ID和参数hash
        step_hash = self._calculate_step_hash(step)
        return step_hash in resource_pool['step_cache']
    
    def _update_step_cache(self, step: Any, result: Dict[str, Any], resource_pool: Dict[str, Any]):
        """更新步骤缓存"""
        if not resource_pool.get('step_cache'):
            return
        
        step_hash = self._calculate_step_hash(step)
        resource_pool['step_cache'][step_hash] = {
            'result': result,
            'timestamp': timezone.now(),
            'step_name': getattr(step, 'name', 'unknown')
        }
        
        # 限制缓存大小
        if len(resource_pool['step_cache']) > 1000:
            # 移除最旧的条目
            oldest_key = min(
                resource_pool['step_cache'].keys(),
                key=lambda k: resource_pool['step_cache'][k]['timestamp']
            )
            del resource_pool['step_cache'][oldest_key]
    
    def _calculate_step_hash(self, step: Any) -> str:
        """计算步骤hash"""
        import hashlib
        
        step_data = {
            'id': getattr(step, 'id', ''),
            'name': getattr(step, 'name', ''),
            'type': getattr(step, 'type', ''),
            'parameters': getattr(step, 'parameters', {})
        }
        
        step_str = json.dumps(step_data, sort_keys=True)
        return hashlib.md5(step_str.encode()).hexdigest()
    
    def _check_memory_threshold(self, threshold_mb: int) -> bool:
        """检查内存使用是否超过阈值"""
        if not PSUTIL_AVAILABLE:
            return False
            
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            return memory_mb > threshold_mb
        except Exception:
            return False
    
    def _perform_memory_cleanup(self):
        """执行内存清理"""
        gc.collect()
        logger.info("Memory cleanup performed")
    
    def _get_current_memory_usage(self) -> float:
        """获取当前内存使用量(MB)"""
        if not PSUTIL_AVAILABLE:
            return 0.0
            
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0

    def analyze_pipeline_step_execution_plan(self, pipeline: Pipeline) -> Dict[str, Any]:
        """
        分析流水线的PipelineStep执行计划，识别并行组和依赖关系
        
        Returns:
            执行计划，包含步骤分组、依赖关系和执行顺序
        """
        steps = list(pipeline.steps.all().order_by('order'))
        parallel_groups = {}
        sequential_steps = []
        execution_plan = {
            'stages': [],  # 执行阶段列表
            'parallel_groups': {},
            'dependencies': {},
            'total_stages': 0
        }
        
        # 收集并行组信息
        for step in steps:
            if hasattr(step, 'parallel_group') and step.parallel_group:
                group_id = step.parallel_group
                if group_id not in parallel_groups:
                    parallel_groups[group_id] = {
                        'id': group_id,
                        'name': f"并行组-{group_id[:8]}",
                        'steps': [],
                        'sync_policy': 'wait_all',  # 默认等待所有步骤完成
                        'timeout_seconds': None,
                        'min_order': float('inf'),
                        'max_order': 0
                    }
                
                parallel_groups[group_id]['steps'].append(step)
                parallel_groups[group_id]['min_order'] = min(parallel_groups[group_id]['min_order'], step.order)
                parallel_groups[group_id]['max_order'] = max(parallel_groups[group_id]['max_order'], step.order)
                logger.info(f"Added PipelineStep {step.name} to parallel group {group_id} with order {step.order}")
            else:
                sequential_steps.append(step)
                logger.info(f"Added PipelineStep {step.name} to sequential execution with order {step.order}")
        
        logger.info(f"Found {len(parallel_groups)} parallel groups and {len(sequential_steps)} sequential steps")
        
        # 创建执行阶段
        # 按照 order 字段排序，将并行组和单独步骤安排到不同的阶段
        all_items = []
        
        # 添加单独步骤
        for step in sequential_steps:
            all_items.append({
                'type': 'step',
                'order': step.order,
                'item': step,
                'parallel': False
            })
        
        # 添加并行组（使用最小order作为组的order）
        for group_id, group_info in parallel_groups.items():
            all_items.append({
                'type': 'parallel_group',
                'order': group_info['min_order'],
                'item': group_info,
                'parallel': True
            })
        
        # 按order排序
        all_items.sort(key=lambda x: x['order'])
        
        # 构建执行阶段
        stage_number = 0
        for item in all_items:
            stage = {
                'stage_number': stage_number,
                'type': item['type'],
                'parallel': item['parallel'],
                'items': []
            }
            
            if item['type'] == 'step':
                stage['items'] = [item['item']]
            else:  # parallel_group
                stage['items'] = item['item']['steps']
                stage['group_info'] = item['item']
            
            execution_plan['stages'].append(stage)
            stage_number += 1
        
        execution_plan['total_stages'] = stage_number
        execution_plan['parallel_groups'] = parallel_groups
        
        logger.info(f"Pipeline {pipeline.id} PipelineStep execution plan: {stage_number} stages, {len(parallel_groups)} parallel groups")
        return execution_plan

    def execute_pipeline_step_with_parallel_support(self, 
                                                    pipeline: Pipeline, 
                                                    pipeline_run, 
                                                    execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据执行计划执行流水线的PipelineStep，支持并行组
        """
        logger.info(f"Starting PipelineStep execution for pipeline {pipeline.id} with parallel support")
        
        try:
            # 按阶段执行
            for stage in execution_plan['stages']:
                stage_result = self._execute_pipeline_step_stage(
                    stage, 
                    pipeline, 
                    pipeline_run, 
                    execution_plan
                )
                
                if not stage_result['success']:
                    logger.error(f"PipelineStep stage {stage['stage_number']} failed: {stage_result['message']}")
                    return {
                        'success': False,
                        'message': f"Pipeline failed at stage {stage['stage_number']}: {stage_result['message']}",
                        'failed_stage': stage['stage_number']
                    }
            
            # 所有阶段完成
            return {
                'success': True,
                'message': 'Pipeline PipelineStep execution completed successfully',
                'execution_type': 'pipeline_step'
            }
            
        except Exception as e:
            logger.error(f"PipelineStep execution failed: {e}")
            return {
                'success': False,
                'message': f'PipelineStep execution failed: {str(e)}'
            }

    def _execute_pipeline_step_stage(self, 
                                    stage: Dict[str, Any], 
                                    pipeline: Pipeline, 
                                    pipeline_run,
                                    execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个PipelineStep阶段（可能包含并行步骤）
        """
        stage_number = stage['stage_number']
        is_parallel = stage['parallel']
        steps = stage['items']
        
        logger.info(f"开始执行PipelineStep阶段 {stage_number}: {'并行' if is_parallel else '串行'} 执行，包含 {len(steps)} 个步骤")
        
        if is_parallel:
            # 并行执行
            return self._execute_parallel_pipeline_steps(steps, stage.get('group_info', {}), pipeline_run)
        else:
            # 串行执行
            return self._execute_sequential_pipeline_steps(steps, pipeline_run)

    def _execute_parallel_pipeline_steps(self, steps: List, group_info: Dict[str, Any], pipeline_execution) -> Dict[str, Any]:
        """
        并行执行多个PipelineStep
        """
        import subprocess
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        logger.info(f"开始本地并行执行 {len(steps)} 个PipelineStep，同步策略: {group_info.get('sync_policy', 'wait_all')}")
        
        # 创建线程池
        max_workers = min(len(steps), self.max_parallel_workers)
        logger.info(f"创建线程池，最大工作线程数: {max_workers}")
        
        def execute_single_pipeline_step(step):
            """执行单个PipelineStep"""
            logger.info(f"开始本地执行PipelineStep: {step.name}")
            
            try:
                # 首先创建StepExecution记录
                from cicd_integrations.models import StepExecution
                
                step_execution = StepExecution.objects.create(
                    pipeline_execution=pipeline_execution,
                    pipeline_step=step,
                    status='running',
                    order=step.order,
                    started_at=timezone.now()
                )
                
                # 更新步骤状态
                step.status = 'running'
                step.started_at = timezone.now()
                step.save()
                
                # 执行命令
                if step.command:
                    process = subprocess.run(
                        step.command, 
                        shell=True, 
                        capture_output=True, 
                        text=True,
                        timeout=step.timeout_seconds
                    )
                    
                    if process.returncode == 0:
                        step.status = 'success'
                        step.output_log = process.stdout
                        step_execution.status = 'success'
                        step_execution.logs = process.stdout
                        step_execution.output = {'returncode': 0, 'stdout': process.stdout}
                        logger.info(f"PipelineStep {step.name} 执行完成，结果: 成功")
                    else:
                        step.status = 'failed'
                        step.error_log = process.stderr
                        step_execution.status = 'failed'
                        step_execution.logs = process.stderr
                        step_execution.error_message = process.stderr
                        step_execution.output = {'returncode': process.returncode, 'stderr': process.stderr}
                        logger.error(f"PipelineStep {step.name} 执行失败: {process.stderr}")
                else:
                    step.status = 'success'
                    step.output_log = "No command to execute"
                    step_execution.status = 'success'
                    step_execution.logs = "No command to execute"
                    step_execution.output = {'message': 'No command to execute'}
                    logger.info(f"PipelineStep {step.name} 没有命令，直接完成")
                
                step.completed_at = timezone.now()
                step.save()
                
                step_execution.completed_at = timezone.now()
                step_execution.save()
                
                return {
                    'success': step.status == 'success',
                    'step_name': step.name,
                    'output': step.output_log,
                    'error': step.error_log if step.status == 'failed' else None
                }
                
            except Exception as e:
                logger.error(f"PipelineStep {step.name} 执行异常: {e}")
                step.status = 'failed'
                step.error_log = str(e)
                step.completed_at = timezone.now()
                step.save()
                
                # 更新StepExecution记录
                if 'step_execution' in locals():
                    step_execution.status = 'failed'
                    step_execution.error_message = str(e)
                    step_execution.logs = str(e)
                    step_execution.completed_at = timezone.now()
                    step_execution.save()
                
                return {
                    'success': False,
                    'step_name': step.name,
                    'error': str(e)
                }
        
        # 并行执行步骤
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            futures = []
            for step in steps:
                future = executor.submit(execute_single_pipeline_step, step)
                futures.append(future)
                logger.info(f"  - PipelineStep: {step.name}, 顺序: {step.order}, 类型: {step.step_type}")
            
            logger.info(f"已提交 {len(futures)} 个并行任务到线程池")
            
            # 等待所有任务完成
            results = []
            success_count = 0
            failed_count = 0
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                
                if result['success']:
                    success_count += 1
                    logger.info(f"PipelineStep {result['step_name']} 执行成功")
                else:
                    failed_count += 1
                    logger.error(f"PipelineStep {result['step_name']} 执行失败: {result.get('error', '')}")
        
        # 根据同步策略判断整体结果
        sync_policy = group_info.get('sync_policy', 'wait_all')
        overall_success = (success_count > 0) if sync_policy == 'wait_any' else (failed_count == 0)
        
        logger.info(f"并行执行完成: {success_count} 成功, {failed_count} 失败, 总体结果: {'成功' if overall_success else '失败'}")
        
        return {
            'success': overall_success,
            'message': f'Parallel execution completed: {success_count} success, {failed_count} failed',
            'results': results,
            'sync_policy': sync_policy
        }

    def _execute_sequential_pipeline_steps(self, steps: List, pipeline_execution) -> Dict[str, Any]:
        """
        串行执行多个PipelineStep
        """
        import subprocess
        
        logger.info(f"Executing sequential stage with {len(steps)} steps")
        
        for step in steps:
            logger.info(f"开始本地执行PipelineStep: {step.name}")
            
            try:
                # 创建StepExecution记录
                from cicd_integrations.models import StepExecution
                
                step_execution = StepExecution.objects.create(
                    pipeline_execution=pipeline_execution,
                    pipeline_step=step,
                    status='running',
                    order=step.order,
                    started_at=timezone.now()
                )
                
                # 更新步骤状态
                step.status = 'running'
                step.started_at = timezone.now()
                step.save()
                
                # 执行命令
                if step.command:
                    process = subprocess.run(
                        step.command, 
                        shell=True, 
                        capture_output=True, 
                        text=True,
                        timeout=step.timeout_seconds
                    )
                    
                    if process.returncode == 0:
                        step.status = 'success'
                        step.output_log = process.stdout
                        step_execution.status = 'success'
                        step_execution.logs = process.stdout
                        step_execution.output = {'returncode': 0, 'stdout': process.stdout}
                        logger.info(f"PipelineStep {step.name} 执行完成，结果: 成功")
                    else:
                        step.status = 'failed'
                        step.error_log = process.stderr
                        step_execution.status = 'failed'
                        step_execution.logs = process.stderr
                        step_execution.error_message = process.stderr
                        step_execution.output = {'returncode': process.returncode, 'stderr': process.stderr}
                        logger.error(f"PipelineStep {step.name} 执行失败: {process.stderr}")
                        
                        step.completed_at = timezone.now()
                        step.save()
                        
                        step_execution.completed_at = timezone.now()
                        step_execution.save()
                        
                        return {
                            'success': False,
                            'message': f'PipelineStep {step.name} failed',
                            'error': process.stderr
                        }
                else:
                    step.status = 'success'
                    step.output_log = "No command to execute"
                    step_execution.status = 'success'
                    step_execution.logs = "No command to execute"
                    step_execution.output = {'message': 'No command to execute'}
                    logger.info(f"PipelineStep {step.name} 没有命令，直接完成")
                
                step.completed_at = timezone.now()
                step.save()
                
                step_execution.completed_at = timezone.now()
                step_execution.save()
                
            except Exception as e:
                logger.error(f"PipelineStep {step.name} 执行异常: {e}")
                step.status = 'failed'
                step.error_log = str(e)
                step.completed_at = timezone.now()
                step.save()
                
                # 更新StepExecution记录
                if 'step_execution' in locals():
                    step_execution.status = 'failed'
                    step_execution.error_message = str(e)
                    step_execution.logs = str(e)
                    step_execution.completed_at = timezone.now()
                    step_execution.save()
                
                return {
                    'success': False,
                    'message': f'PipelineStep {step.name} failed with exception',
                    'error': str(e)
                }
        
        return {
            'success': True,
            'message': 'Sequential execution completed successfully'
        }

# 全局服务实例
parallel_execution_service = ParallelExecutionService()
