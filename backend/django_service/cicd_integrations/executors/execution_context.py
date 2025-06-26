"""
执行上下文管理器
管理流水线执行过程中的共享状态、变量和环境
"""
import json
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from django.utils import timezone

@dataclass
class ExecutionContext:
    """流水线执行上下文"""
    
    # 基本信息
    execution_id: int
    pipeline_name: str
    trigger_type: str
    triggered_by: Optional[str] = None
    
    # 执行状态
    status: str = 'pending'
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 变量和参数
    variables: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    
    # 步骤执行记录
    step_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    step_outputs: Dict[str, Any] = field(default_factory=dict)
    
    # 并发控制
    _locks: Dict[str, asyncio.Lock] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        if self.started_at is None and self.status == 'running':
            self.started_at = timezone.now()
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """获取变量值"""
        return self.variables.get(key, default)
    
    def set_variable(self, key: str, value: Any) -> None:
        """设置变量值"""
        self.variables[key] = value
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取参数值"""
        return self.parameters.get(key, default)
    
    def set_parameter(self, key: str, value: Any) -> None:
        """设置参数值"""
        self.parameters[key] = value
    
    def get_environment(self, key: str, default: str = '') -> str:
        """获取环境变量"""
        return self.environment.get(key, default)
    
    def set_environment(self, key: str, value: str) -> None:
        """设置环境变量"""
        self.environment[key] = value
    
    def resolve_variables(self, text: str) -> str:
        """解析变量替换"""
        if not isinstance(text, str):
            return text
        
        # 替换环境变量 ${VAR_NAME}
        import re
        pattern = r'\$\{([^}]+)\}'
        
        def replacer(match):
            var_name = match.group(1)
            
            # 优先级: 参数 > 变量 > 环境变量
            if var_name in self.parameters:
                return str(self.parameters[var_name])
            elif var_name in self.variables:
                return str(self.variables[var_name])
            elif var_name in self.environment:
                return str(self.environment[var_name])
            else:
                # 返回原始文本，避免替换失败
                return match.group(0)
        
        return re.sub(pattern, replacer, text)
    
    def resolve_step_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """解析步骤参数中的变量"""
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str):
                resolved[key] = self.resolve_variables(value)
            elif isinstance(value, dict):
                resolved[key] = self.resolve_step_parameters(value)
            elif isinstance(value, list):
                resolved[key] = [
                    self.resolve_variables(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                resolved[key] = value
        
        return resolved
    
    def set_step_result(self, step_name: str, result: Dict[str, Any]) -> None:
        """设置步骤执行结果"""
        self.step_results[step_name] = {
            'status': result.get('status'),
            'started_at': result.get('started_at'),
            'completed_at': result.get('completed_at'),
            'logs': result.get('logs', ''),
            'error_message': result.get('error_message', ''),
            'output': result.get('output', {}),
            'external_id': result.get('external_id', ''),
        }
        
        # 保存步骤输出供后续步骤使用
        if 'output' in result:
            self.step_outputs[step_name] = result['output']
    
    def get_step_result(self, step_name: str) -> Optional[Dict[str, Any]]:
        """获取步骤执行结果"""
        return self.step_results.get(step_name)
    
    def get_step_output(self, step_name: str, key: str = None) -> Any:
        """获取步骤输出"""
        if step_name not in self.step_outputs:
            return None
        
        if key is None:
            return self.step_outputs[step_name]
        
        return self.step_outputs[step_name].get(key)
    
    def is_step_successful(self, step_name: str) -> bool:
        """检查步骤是否执行成功"""
        result = self.get_step_result(step_name)
        return result and result.get('status') == 'success'
    
    def is_step_failed(self, step_name: str) -> bool:
        """检查步骤是否执行失败"""
        result = self.get_step_result(step_name)
        return result and result.get('status') in ['failed', 'error']
    
    def is_step_completed(self, step_name: str) -> bool:
        """检查步骤是否已完成（无论成功或失败）"""
        result = self.get_step_result(step_name)
        return result and result.get('status') in ['success', 'failed', 'error', 'skipped']
    
    async def get_lock(self, resource_name: str) -> asyncio.Lock:
        """获取资源锁"""
        if resource_name not in self._locks:
            self._locks[resource_name] = asyncio.Lock()
        return self._locks[resource_name]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'execution_id': self.execution_id,
            'pipeline_name': self.pipeline_name,
            'trigger_type': self.trigger_type,
            'triggered_by': self.triggered_by,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'variables': self.variables,
            'parameters': self.parameters,
            'environment': self.environment,
            'step_results': self.step_results,
            'step_outputs': self.step_outputs,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionContext':
        """从字典创建实例"""
        context = cls(
            execution_id=data['execution_id'],
            pipeline_name=data['pipeline_name'],
            trigger_type=data['trigger_type'],
            triggered_by=data.get('triggered_by'),
            status=data.get('status', 'pending'),
            variables=data.get('variables', {}),
            parameters=data.get('parameters', {}),
            environment=data.get('environment', {}),
            step_results=data.get('step_results', {}),
            step_outputs=data.get('step_outputs', {}),
        )
        
        # 解析时间字段
        if data.get('started_at'):
            from dateutil.parser import parse
            context.started_at = parse(data['started_at'])
        
        if data.get('completed_at'):
            from dateutil.parser import parse
            context.completed_at = parse(data['completed_at'])
        
        return context
