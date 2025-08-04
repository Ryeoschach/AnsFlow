"""
Docker执行器使用ExecutionLogger的示例
展示如何在Docker步骤执行中使用公共日志记录模块
"""

from common.execution_logger import ExecutionLogger, ExecutionContext
import subprocess
import logging

logger = logging.getLogger(__name__)


class EnhancedDockerStepExecutor:
    """增强的Docker步骤执行器 - 使用ExecutionLogger"""
    
    def __init__(self, enable_real_execution=True):
        self.enable_real_execution = enable_real_execution
        self.supported_step_types = [
            'docker_build',
            'docker_run', 
            'docker_push',
            'docker_pull'
        ]
    
    def execute_step_with_logging(self, step_execution, step, context=None):
        """
        使用ExecutionLogger执行Docker步骤的示例
        """
        context = context or {}
        
        # 方式1: 使用上下文管理器（推荐）
        with ExecutionContext(step_execution, f"开始执行Docker步骤: {step.name}") as ctx:
            try:
                # 根据步骤类型执行不同的Docker操作
                if step.step_type == 'docker_build':
                    result = self._execute_docker_build_with_logging(step, context)
                elif step.step_type == 'docker_run':
                    result = self._execute_docker_run_with_logging(step, context)
                elif step.step_type == 'docker_push':
                    result = self._execute_docker_push_with_logging(step, context)
                else:
                    raise ValueError(f"不支持的步骤类型: {step.step_type}")
                
                # 设置执行结果
                ctx.set_result({
                    'status': 'success',
                    'output': result.get('output', ''),
                    'stdout': result.get('build_log', ''),
                    'logs': f"Docker步骤执行成功: {result.get('message', '')}",
                })
                
                return result
                
            except Exception as e:
                # 异常会被上下文管理器自动处理
                ExecutionLogger.log_execution_info(
                    step_execution, 
                    f"Docker步骤执行失败: {str(e)}", 
                    level='error'
                )
                raise
    
    def execute_step_manual_logging(self, step_execution, step, context=None):
        """
        手动使用ExecutionLogger的示例
        """
        context = context or {}
        
        # 开始执行
        ExecutionLogger.start_execution(
            step_execution, 
            f"开始执行Docker步骤: {step.name} ({step.step_type})"
        )
        
        try:
            # 记录执行信息
            ExecutionLogger.log_execution_info(
                step_execution, 
                f"Docker步骤参数: {step.ansible_parameters}"
            )
            
            # 执行Docker命令
            if step.step_type == 'docker_build':
                result = self._build_docker_image(step, context)
            elif step.step_type == 'docker_run':
                result = self._run_docker_container(step, context)
            else:
                raise ValueError(f"不支持的步骤类型: {step.step_type}")
            
            # 完成执行
            ExecutionLogger.complete_execution(
                step_execution,
                result={
                    'status': 'success',
                    'stdout': result.get('output', ''),
                    'logs': result.get('build_log', ''),
                    'return_code': 0
                },
                log_message=f"Docker步骤执行成功: {step.name}"
            )
            
            return result
            
        except subprocess.TimeoutExpired as e:
            # 处理超时
            ExecutionLogger.timeout_execution(
                step_execution,
                timeout_message=f"Docker命令执行超时: {str(e)}",
                log_message=f"Docker步骤执行超时: {step.name}"
            )
            raise
            
        except Exception as e:
            # 处理其他异常
            ExecutionLogger.fail_execution(
                step_execution,
                error_message=f"Docker步骤执行失败: {str(e)}",
                log_message=f"Docker步骤执行异常: {step.name}, 错误: {str(e)}"
            )
            raise
    
    def _execute_docker_build_with_logging(self, step, context):
        """Docker构建示例"""
        params = step.ansible_parameters or {}
        image_name = params.get('image', 'unnamed:latest')
        dockerfile_path = params.get('dockerfile', 'Dockerfile')
        build_context = params.get('context', '.')
        
        # 构建Docker命令
        cmd = [
            'docker', 'build',
            '-t', image_name,
            '-f', dockerfile_path,
            build_context
        ]
        
        # 执行命令
        if self.enable_real_execution:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode != 0:
                raise Exception(f"Docker构建失败: {result.stderr}")
            
            return {
                'message': f'镜像 {image_name} 构建成功',
                'output': result.stdout,
                'build_log': result.stdout,
                'image_name': image_name
            }
        else:
            # 模拟模式
            return {
                'message': f'[模拟] 镜像 {image_name} 构建成功',
                'output': f'Successfully built {image_name}',
                'build_log': f'[模拟] 构建日志: {image_name}',
                'image_name': image_name
            }
    
    def _execute_docker_run_with_logging(self, step, context):
        """Docker运行示例"""
        params = step.ansible_parameters or {}
        image_name = params.get('image')
        command = params.get('command')
        
        if not image_name:
            raise ValueError("未指定Docker镜像")
        
        # 构建Docker命令
        cmd = ['docker', 'run', '--rm', image_name]
        if command:
            cmd.extend(command.split())
        
        # 执行命令
        if self.enable_real_execution:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                raise Exception(f"Docker运行失败: {result.stderr}")
            
            return {
                'message': f'容器运行成功',
                'output': result.stdout,
                'exit_code': result.returncode
            }
        else:
            # 模拟模式
            return {
                'message': f'[模拟] 容器运行成功',
                'output': f'[模拟] 运行输出: {image_name}',
                'exit_code': 0
            }
    
    def _execute_docker_push_with_logging(self, step, context):
        """Docker推送示例"""
        params = step.ansible_parameters or {}
        image_name = params.get('image')
        
        if not image_name:
            raise ValueError("未指定Docker镜像")
        
        # 构建Docker命令
        cmd = ['docker', 'push', image_name]
        
        # 执行命令
        if self.enable_real_execution:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode != 0:
                raise Exception(f"Docker推送失败: {result.stderr}")
            
            return {
                'message': f'镜像 {image_name} 推送成功',
                'output': result.stdout,
                'push_log': result.stdout
            }
        else:
            # 模拟模式
            return {
                'message': f'[模拟] 镜像 {image_name} 推送成功',
                'output': f'[模拟] 推送日志: {image_name}',
                'push_log': f'[模拟] 推送成功: {image_name}'
            }


# 使用示例
def example_usage():
    """展示如何使用增强的Docker执行器"""
    
    # 假设的步骤执行对象和步骤对象
    # step_execution = StepExecution.objects.get(id=execution_id)
    # step = step_execution.step
    
    executor = EnhancedDockerStepExecutor(enable_real_execution=False)
    
    # 使用上下文管理器方式（推荐）
    try:
        # result = executor.execute_step_with_logging(step_execution, step)
        # print(f"执行结果: {result}")
        pass
    except Exception as e:
        print(f"执行失败: {e}")
    
    # 使用手动日志记录方式
    try:
        # result = executor.execute_step_manual_logging(step_execution, step)
        # print(f"执行结果: {result}")
        pass
    except Exception as e:
        print(f"执行失败: {e}")


if __name__ == "__main__":
    example_usage()
