"""
公共执行日志记录模块
为各种执行器提供统一的日志记录功能
"""
import logging
from typing import Any, Dict, Optional, Union
from django.utils import timezone
from django.db import models
import subprocess

logger = logging.getLogger(__name__)


class ExecutionLogger:
    """执行日志记录器 - 提供统一的执行日志记录功能"""
    
    @staticmethod
    def start_execution(execution: models.Model, log_message: str = None) -> None:
        """
        开始执行，设置状态为running并记录开始时间
        
        Args:
            execution: 执行对象（如AnsibleExecution、StepExecution等）
            log_message: 可选的日志消息
        """
        try:
            execution.status = 'running'
            execution.started_at = timezone.now()
            execution.save()
            
            if log_message:
                logger.info(log_message)
                
        except Exception as e:
            logger.error(f"开始执行记录失败: {str(e)}")
    
    @staticmethod
    def complete_execution(
        execution: models.Model, 
        result: Union[subprocess.CompletedProcess, Dict[str, Any], None] = None,
        status: str = None,
        error_message: str = None,
        timeout_message: str = None,
        custom_logs: str = None,
        log_message: str = None
    ) -> None:
        """
        完成执行，记录执行结果和完成时间
        
        Args:
            execution: 执行对象
            result: subprocess.CompletedProcess对象或包含执行结果的字典
            status: 自定义状态，如果不提供则根据result自动判断
            error_message: 错误消息
            timeout_message: 超时消息
            custom_logs: 自定义日志内容
            log_message: 可选的日志消息
        """
        try:
            # 设置完成时间
            execution.completed_at = timezone.now()
            
            # 处理subprocess.CompletedProcess结果
            if isinstance(result, subprocess.CompletedProcess):
                # 保存标准输出和错误输出
                if hasattr(execution, 'stdout'):
                    execution.stdout = result.stdout
                if hasattr(execution, 'stderr'):
                    execution.stderr = result.stderr
                if hasattr(execution, 'return_code'):
                    execution.return_code = result.returncode
                
                # 合并日志到logs字段（如果存在）
                if hasattr(execution, 'logs'):
                    logs_content = []
                    if result.stdout:
                        logs_content.append(f"STDOUT:\n{result.stdout}")
                    if result.stderr:
                        logs_content.append(f"STDERR:\n{result.stderr}")
                    execution.logs = "\n\n".join(logs_content)
                
                # 根据返回码自动判断状态
                if status is None:
                    status = 'success' if result.returncode == 0 else 'failed'
            
            # 处理字典结果
            elif isinstance(result, dict):
                if hasattr(execution, 'stdout') and 'stdout' in result:
                    execution.stdout = result['stdout']
                if hasattr(execution, 'stderr') and 'stderr' in result:
                    execution.stderr = result['stderr']
                if hasattr(execution, 'return_code') and 'return_code' in result:
                    execution.return_code = result['return_code']
                if hasattr(execution, 'logs') and 'logs' in result:
                    execution.logs = result['logs']
                elif hasattr(execution, 'logs') and 'output' in result:
                    execution.logs = result['output']
                
                # 从字典中获取状态
                if status is None and 'status' in result:
                    status = result['status']
            
            # 处理超时情况
            if timeout_message:
                if hasattr(execution, 'stderr'):
                    execution.stderr = timeout_message
                if hasattr(execution, 'return_code'):
                    execution.return_code = -1
                if hasattr(execution, 'logs'):
                    execution.logs = f"执行超时: {timeout_message}"
                status = 'failed'
            
            # 处理错误情况
            if error_message:
                if hasattr(execution, 'stderr'):
                    execution.stderr = error_message
                if hasattr(execution, 'return_code'):
                    execution.return_code = -1
                if hasattr(execution, 'logs'):
                    execution.logs = f"执行异常: {error_message}"
                status = 'failed'
            
            # 处理自定义日志
            if custom_logs and hasattr(execution, 'logs'):
                execution.logs = custom_logs
            
            # 设置状态
            if status:
                execution.status = status
            elif not hasattr(execution, 'status') or not execution.status:
                execution.status = 'completed'
            
            execution.save()
            
            if log_message:
                if status == 'success':
                    logger.info(log_message)
                else:
                    logger.error(log_message)
                    
        except Exception as e:
            logger.error(f"完成执行记录失败: {str(e)}")
    
    @staticmethod
    def fail_execution(
        execution: models.Model,
        error_message: str,
        return_code: int = -1,
        log_message: str = None
    ) -> None:
        """
        标记执行失败
        
        Args:
            execution: 执行对象
            error_message: 错误消息
            return_code: 返回码，默认-1
            log_message: 可选的日志消息
        """
        ExecutionLogger.complete_execution(
            execution=execution,
            status='failed',
            error_message=error_message,
            log_message=log_message
        )
        
        if hasattr(execution, 'return_code'):
            execution.return_code = return_code
            execution.save()
    
    @staticmethod
    def timeout_execution(
        execution: models.Model,
        timeout_message: str = "执行超时",
        timeout_seconds: int = None,
        log_message: str = None
    ) -> None:
        """
        标记执行超时
        
        Args:
            execution: 执行对象
            timeout_message: 超时消息
            timeout_seconds: 超时时间（秒）
            log_message: 可选的日志消息
        """
        if timeout_seconds:
            timeout_message = f"执行超时（超过{timeout_seconds}秒）"
        
        ExecutionLogger.complete_execution(
            execution=execution,
            status='failed',
            timeout_message=timeout_message,
            log_message=log_message
        )
    
    @staticmethod
    def cancel_execution(
        execution: models.Model,
        cancel_message: str = "执行已取消",
        log_message: str = None
    ) -> None:
        """
        标记执行已取消
        
        Args:
            execution: 执行对象
            cancel_message: 取消消息
            log_message: 可选的日志消息
        """
        try:
            execution.status = 'cancelled'
            execution.completed_at = timezone.now()
            
            if hasattr(execution, 'logs'):
                execution.logs = cancel_message
            if hasattr(execution, 'stderr'):
                execution.stderr = cancel_message
            
            execution.save()
            
            if log_message:
                logger.info(log_message)
                
        except Exception as e:
            logger.error(f"取消执行记录失败: {str(e)}")
    
    @staticmethod
    def update_execution_logs(
        execution: models.Model,
        logs: str,
        append: bool = False
    ) -> None:
        """
        更新执行日志
        
        Args:
            execution: 执行对象
            logs: 日志内容
            append: 是否追加到现有日志
        """
        try:
            if hasattr(execution, 'logs'):
                if append and execution.logs:
                    execution.logs = f"{execution.logs}\n{logs}"
                else:
                    execution.logs = logs
                execution.save()
        except Exception as e:
            logger.error(f"更新执行日志失败: {str(e)}")
    
    @staticmethod
    def log_execution_info(
        execution: models.Model,
        message: str,
        level: str = 'info'
    ) -> None:
        """
        记录执行信息到日志系统
        
        Args:
            execution: 执行对象
            message: 日志消息
            level: 日志级别 ('info', 'warning', 'error')
        """
        try:
            # 获取执行对象的标识信息
            execution_id = getattr(execution, 'id', 'unknown')
            execution_type = execution.__class__.__name__
            
            formatted_message = f"[{execution_type}:{execution_id}] {message}"
            
            if level == 'info':
                logger.info(formatted_message)
            elif level == 'warning':
                logger.warning(formatted_message)
            elif level == 'error':
                logger.error(formatted_message)
            else:
                logger.info(formatted_message)
                
        except Exception as e:
            logger.error(f"记录执行信息失败: {str(e)}")


class ExecutionContext:
    """执行上下文管理器 - 自动处理执行开始和结束"""
    
    def __init__(self, execution: models.Model, start_message: str = None):
        self.execution = execution
        self.start_message = start_message
        self.result = None
        self.error = None
    
    def __enter__(self):
        ExecutionLogger.start_execution(self.execution, self.start_message)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # 有异常发生
            error_message = str(exc_val) if exc_val else "未知异常"
            ExecutionLogger.fail_execution(
                self.execution,
                error_message,
                log_message=f"执行异常: {error_message}"
            )
            return False  # 不抑制异常
        else:
            # 正常完成
            ExecutionLogger.complete_execution(
                self.execution,
                result=self.result,
                log_message="执行完成"
            )
        return False
    
    def set_result(self, result):
        """设置执行结果"""
        self.result = result
