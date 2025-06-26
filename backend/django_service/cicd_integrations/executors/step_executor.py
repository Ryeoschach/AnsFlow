"""
原子步骤执行器
负责单个原子步骤的具体执行逻辑
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from django.utils import timezone
from asgiref.sync import sync_to_async

from ..models import AtomicStep, StepExecution, PipelineExecution
from ..adapters import AdapterFactory, ExecutionResult
from .execution_context import ExecutionContext

logger = logging.getLogger(__name__)

class StepExecutionError(Exception):
    """步骤执行错误"""
    pass

class StepExecutor:
    """原子步骤执行器"""
    
    def __init__(self, context: ExecutionContext):
        self.context = context
        self.adapter = None
    
    async def execute_step(
        self,
        step: AtomicStep,
        tool_config: Dict[str, Any],
        step_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行单个原子步骤
        
        Args:
            step: 原子步骤对象
            tool_config: CI/CD工具配置
            step_parameters: 步骤参数（可覆盖默认参数）
        
        Returns:
            执行结果字典
        """
        step_execution = None
        
        try:
            # 创建步骤执行记录
            step_execution = await self._create_step_execution(step)
            
            # 解析步骤参数
            resolved_parameters = self._resolve_step_parameters(step, step_parameters)
            
            # 检查执行条件
            if not await self._check_conditions(step, resolved_parameters):
                return await self._skip_step(step_execution, "条件不满足")
            
            # 更新状态为运行中
            await self._update_step_status(step_execution, 'running')
            
            logger.info(f"开始执行步骤: {step.name} (ID: {step.id})")
            
            # 根据步骤类型执行
            result = await self._execute_step_by_type(
                step, tool_config, resolved_parameters
            )
            
            # 更新执行结果
            if result.success:
                await self._complete_step_success(step_execution, result)
                logger.info(f"步骤执行成功: {step.name}")
            else:
                await self._complete_step_failure(step_execution, result)
                logger.error(f"步骤执行失败: {step.name} - {result.message}")
            
            # 更新上下文
            step_result = await self._get_step_result(step_execution)
            self.context.set_step_result(step.name, step_result)
            
            return step_result
        
        except Exception as e:
            logger.error(f"步骤执行异常: {step.name} - {str(e)}")
            
            if step_execution:
                await self._complete_step_error(step_execution, str(e))
                step_result = await self._get_step_result(step_execution)
                self.context.set_step_result(step.name, step_result)
                return step_result
            else:
                return {
                    'status': 'failed',
                    'error_message': str(e),
                    'started_at': timezone.now(),
                    'completed_at': timezone.now(),
                }
    
    async def _create_step_execution(self, step: AtomicStep) -> StepExecution:
        """创建步骤执行记录"""
        pipeline_execution = await sync_to_async(PipelineExecution.objects.get)(
            id=self.context.execution_id
        )
        
        # 获取步骤顺序
        existing_count = await sync_to_async(StepExecution.objects.filter)(
            pipeline_execution=pipeline_execution
        ).acount()
        
        step_execution = await sync_to_async(StepExecution.objects.create)(
            pipeline_execution=pipeline_execution,
            atomic_step=step,
            status='pending',
            order=existing_count + 1
        )
        
        return step_execution
    
    def _resolve_step_parameters(
        self, 
        step: AtomicStep, 
        override_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """解析步骤参数"""
        # 合并默认参数和覆盖参数
        parameters = step.parameters.copy()
        if override_parameters:
            parameters.update(override_parameters)
        
        # 使用上下文解析变量
        return self.context.resolve_step_parameters(parameters)
    
    async def _check_conditions(
        self, 
        step: AtomicStep, 
        parameters: Dict[str, Any]
    ) -> bool:
        """检查步骤执行条件"""
        conditions = step.conditions
        if not conditions:
            return True
        
        try:
            # 检查分支条件
            if 'branch' in conditions:
                current_branch = self.context.get_variable('GIT_BRANCH', 'main')
                required_branch = conditions['branch']
                if current_branch != required_branch:
                    logger.info(f"分支条件不满足: 当前 {current_branch}, 需要 {required_branch}")
                    return False
            
            # 检查前置步骤成功条件
            if 'previous_steps_success' in conditions and conditions['previous_steps_success']:
                for step_name, result in self.context.step_results.items():
                    if result['status'] in ['failed', 'error']:
                        logger.info(f"前置步骤失败，跳过执行: {step_name}")
                        return False
            
            # 检查手动审批条件
            if 'manual_approval' in conditions and conditions['manual_approval']:
                # TODO: 实现审批逻辑
                logger.info("需要手动审批，暂时跳过")
                return False
            
            # 检查环境变量条件
            if 'environment' in conditions:
                for env_key, expected_value in conditions['environment'].items():
                    actual_value = self.context.get_environment(env_key)
                    if actual_value != expected_value:
                        logger.info(f"环境变量条件不满足: {env_key}={actual_value}, 期望={expected_value}")
                        return False
            
            # 检查自定义条件表达式
            if 'expression' in conditions:
                # TODO: 实现条件表达式解析
                pass
            
            return True
        
        except Exception as e:
            logger.error(f"检查条件时发生错误: {e}")
            return False
    
    async def _execute_step_by_type(
        self,
        step: AtomicStep,
        tool_config: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> ExecutionResult:
        """根据步骤类型执行步骤"""
        
        if step.step_type == 'fetch_code':
            return await self._execute_fetch_code(parameters)
        elif step.step_type == 'build':
            return await self._execute_build(tool_config, parameters)
        elif step.step_type == 'test':
            return await self._execute_test(tool_config, parameters)
        elif step.step_type == 'security_scan':
            return await self._execute_security_scan(tool_config, parameters)
        elif step.step_type == 'deploy':
            return await self._execute_deploy(tool_config, parameters)
        elif step.step_type == 'notify':
            return await self._execute_notify(parameters)
        elif step.step_type == 'custom':
            return await self._execute_custom(tool_config, parameters)
        else:
            raise StepExecutionError(f"不支持的步骤类型: {step.step_type}")
    
    async def _execute_fetch_code(self, parameters: Dict[str, Any]) -> ExecutionResult:
        """执行代码拉取步骤"""
        try:
            repository_url = parameters.get('repository_url')
            branch = parameters.get('branch', 'main')
            shallow_clone = parameters.get('shallow_clone', True)
            
            # 模拟代码拉取过程
            await asyncio.sleep(1)  # 模拟执行时间
            
            # 设置输出变量
            output = {
                'repository_url': repository_url,
                'branch': branch,
                'commit_sha': 'abc123def456',  # 模拟commit hash
                'workspace_path': '/tmp/workspace'
            }
            
            return ExecutionResult(
                success=True,
                external_id=f"fetch_{self.context.execution_id}",
                message="代码拉取成功",
                logs=f"从 {repository_url} 拉取分支 {branch} 成功",
                artifacts=['source_code']
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                external_id="",
                message=f"代码拉取失败: {str(e)}"
            )
    
    async def _execute_build(
        self, 
        tool_config: Dict[str, Any], 
        parameters: Dict[str, Any]
    ) -> ExecutionResult:
        """执行构建步骤"""
        try:
            build_tool = parameters.get('tool', 'generic')
            command = parameters.get('command', 'build')
            
            # 根据构建工具执行
            if build_tool == 'mvn':
                return await self._execute_maven_build(parameters)
            elif build_tool == 'npm':
                return await self._execute_npm_build(parameters)
            elif build_tool == 'docker':
                return await self._execute_docker_build(parameters)
            else:
                return await self._execute_generic_build(tool_config, parameters)
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                external_id="",
                message=f"构建失败: {str(e)}"
            )
    
    async def _execute_maven_build(self, parameters: Dict[str, Any]) -> ExecutionResult:
        """执行Maven构建"""
        command = parameters.get('command', 'clean compile')
        profiles = parameters.get('profiles', [])
        
        # 模拟Maven构建
        await asyncio.sleep(2)
        
        return ExecutionResult(
            success=True,
            external_id=f"mvn_build_{self.context.execution_id}",
            message="Maven构建成功",
            logs=f"执行命令: mvn {command}",
            artifacts=['target/app.jar']
        )
    
    async def _execute_npm_build(self, parameters: Dict[str, Any]) -> ExecutionResult:
        """执行NPM构建"""
        commands = parameters.get('commands', ['npm install', 'npm run build'])
        
        # 模拟NPM构建
        await asyncio.sleep(1.5)
        
        return ExecutionResult(
            success=True,
            external_id=f"npm_build_{self.context.execution_id}",
            message="NPM构建成功",
            logs=f"执行命令: {', '.join(commands)}",
            artifacts=['dist/']
        )
    
    async def _execute_docker_build(self, parameters: Dict[str, Any]) -> ExecutionResult:
        """执行Docker构建"""
        dockerfile = parameters.get('dockerfile', 'Dockerfile')
        tag = parameters.get('tag', 'latest')
        
        # 模拟Docker构建
        await asyncio.sleep(3)
        
        return ExecutionResult(
            success=True,
            external_id=f"docker_build_{self.context.execution_id}",
            message="Docker镜像构建成功",
            logs=f"构建镜像: {tag}",
            artifacts=[f"image:{tag}"]
        )
    
    async def _execute_test(
        self, 
        tool_config: Dict[str, Any], 
        parameters: Dict[str, Any]
    ) -> ExecutionResult:
        """执行测试步骤"""
        try:
            command = parameters.get('command', 'test')
            coverage = parameters.get('coverage', False)
            
            # 模拟测试执行
            await asyncio.sleep(2)
            
            # 模拟测试结果
            success_rate = 0.95  # 95% 通过率
            
            return ExecutionResult(
                success=True,
                external_id=f"test_{self.context.execution_id}",
                message=f"测试完成，通过率: {success_rate * 100}%",
                logs=f"执行测试命令: {command}",
                artifacts=['test-reports/']
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                external_id="",
                message=f"测试失败: {str(e)}"
            )
    
    async def _execute_security_scan(
        self, 
        tool_config: Dict[str, Any], 
        parameters: Dict[str, Any]
    ) -> ExecutionResult:
        """执行安全扫描步骤"""
        try:
            scan_tool = parameters.get('tool', 'generic')
            
            # 模拟安全扫描
            await asyncio.sleep(1)
            
            return ExecutionResult(
                success=True,
                external_id=f"security_scan_{self.context.execution_id}",
                message="安全扫描完成，未发现高危漏洞",
                logs=f"使用 {scan_tool} 进行安全扫描",
                artifacts=['security-report.json']
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                external_id="",
                message=f"安全扫描失败: {str(e)}"
            )
    
    async def _execute_deploy(
        self, 
        tool_config: Dict[str, Any], 
        parameters: Dict[str, Any]
    ) -> ExecutionResult:
        """执行部署步骤"""
        try:
            environment = parameters.get('environment', 'staging')
            strategy = parameters.get('strategy', 'rolling')
            
            # 模拟部署过程
            await asyncio.sleep(2)
            
            return ExecutionResult(
                success=True,
                external_id=f"deploy_{self.context.execution_id}",
                message=f"部署到 {environment} 环境成功",
                logs=f"使用 {strategy} 策略部署",
                artifacts=[f"deployment-{environment}.yaml"]
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                external_id="",
                message=f"部署失败: {str(e)}"
            )
    
    async def _execute_notify(self, parameters: Dict[str, Any]) -> ExecutionResult:
        """执行通知步骤"""
        try:
            channels = parameters.get('channels', ['email'])
            message = parameters.get('message', '流水线执行完成')
            
            # 模拟发送通知
            await asyncio.sleep(0.5)
            
            return ExecutionResult(
                success=True,
                external_id=f"notify_{self.context.execution_id}",
                message=f"通知发送成功: {', '.join(channels)}",
                logs=f"发送消息: {message}",
                artifacts=[]
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                external_id="",
                message=f"通知发送失败: {str(e)}"
            )
    
    async def _execute_custom(
        self, 
        tool_config: Dict[str, Any], 
        parameters: Dict[str, Any]
    ) -> ExecutionResult:
        """执行自定义步骤"""
        try:
            script = parameters.get('script', '')
            
            # 模拟自定义脚本执行
            await asyncio.sleep(1)
            
            return ExecutionResult(
                success=True,
                external_id=f"custom_{self.context.execution_id}",
                message="自定义步骤执行成功",
                logs=f"执行自定义脚本",
                artifacts=[]
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                external_id="",
                message=f"自定义步骤执行失败: {str(e)}"
            )
    
    async def _execute_generic_build(
        self, 
        tool_config: Dict[str, Any], 
        parameters: Dict[str, Any]
    ) -> ExecutionResult:
        """执行通用构建步骤"""
        try:
            # 使用CI/CD工具适配器执行
            adapter = AdapterFactory.create_adapter(
                tool_config['tool_type'],
                base_url=tool_config.get('base_url', ''),
                username=tool_config.get('username', ''),
                token=tool_config.get('token', ''),
                **tool_config.get('config', {})
            )
            
            # 模拟通过适配器执行
            await asyncio.sleep(1)
            
            return ExecutionResult(
                success=True,
                external_id=f"generic_build_{self.context.execution_id}",
                message="通用构建完成",
                logs="使用外部CI/CD工具构建",
                artifacts=['build_artifacts/']
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                external_id="",
                message=f"通用构建失败: {str(e)}"
            )
    
    async def _skip_step(self, step_execution: StepExecution, reason: str) -> Dict[str, Any]:
        """跳过步骤执行"""
        await self._update_step_status(step_execution, 'skipped', logs=f"跳过原因: {reason}")
        
        return {
            'status': 'skipped',
            'started_at': timezone.now(),
            'completed_at': timezone.now(),
            'logs': f"跳过原因: {reason}",
            'output': {},
            'error_message': '',
            'external_id': '',
        }
    
    async def _update_step_status(
        self, 
        step_execution: StepExecution, 
        status: str,
        logs: str = '',
        external_id: str = ''
    ) -> None:
        """更新步骤状态"""
        step_execution.status = status
        if status == 'running' and not step_execution.started_at:
            step_execution.started_at = timezone.now()
        elif status in ['success', 'failed', 'skipped', 'error']:
            step_execution.completed_at = timezone.now()
        
        if logs:
            step_execution.logs = logs
        if external_id:
            step_execution.external_id = external_id
        
        await sync_to_async(step_execution.save)()
    
    async def _complete_step_success(
        self, 
        step_execution: StepExecution, 
        result: ExecutionResult
    ) -> None:
        """完成步骤执行（成功）"""
        step_execution.status = 'success'
        step_execution.completed_at = timezone.now()
        step_execution.logs = result.logs
        step_execution.external_id = result.external_id
        step_execution.external_url = result.external_url
        
        # 保存输出数据
        if result.artifacts:
            step_execution.output = {
                'artifacts': result.artifacts,
                'external_url': result.external_url
            }
        
        await sync_to_async(step_execution.save)()
    
    async def _complete_step_failure(
        self, 
        step_execution: StepExecution, 
        result: ExecutionResult
    ) -> None:
        """完成步骤执行（失败）"""
        step_execution.status = 'failed'
        step_execution.completed_at = timezone.now()
        step_execution.logs = result.logs
        step_execution.error_message = result.message
        step_execution.external_id = result.external_id
        step_execution.external_url = result.external_url
        
        await sync_to_async(step_execution.save)()
    
    async def _complete_step_error(
        self, 
        step_execution: StepExecution, 
        error_message: str
    ) -> None:
        """完成步骤执行（错误）"""
        step_execution.status = 'failed'
        step_execution.completed_at = timezone.now()
        step_execution.error_message = error_message
        step_execution.logs = f"执行异常: {error_message}"
        
        await sync_to_async(step_execution.save)()
    
    async def _get_step_result(self, step_execution: StepExecution) -> Dict[str, Any]:
        """获取步骤执行结果"""
        # 刷新对象以获取最新数据
        await sync_to_async(step_execution.refresh_from_db)()
        
        return {
            'status': step_execution.status,
            'started_at': step_execution.started_at,
            'completed_at': step_execution.completed_at,
            'logs': step_execution.logs,
            'output': step_execution.output,
            'error_message': step_execution.error_message,
            'external_id': step_execution.external_id,
            'external_url': step_execution.external_url,
        }
