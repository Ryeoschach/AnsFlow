"""
CI/CD 适配器基类和通用数据结构
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import httpx
import logging

logger = logging.getLogger(__name__)


@dataclass
class PipelineDefinition:
    """统一的流水线定义"""
    name: str
    steps: List[Dict[str, Any]]
    triggers: Dict[str, Any]
    environment: Dict[str, str]
    artifacts: List[str] = None
    timeout: int = 3600  # 默认1小时超时

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    external_id: str
    external_url: str = ""
    message: str = ""
    logs: str = ""
    artifacts: List[str] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []


class CICDAdapter(ABC):
    """CI/CD 工具适配器基类"""
    
    def __init__(self, base_url: str, username: str = "", token: str = "", **kwargs):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.token = token
        self.config = kwargs
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @abstractmethod
    async def create_pipeline_file(self, pipeline_def: PipelineDefinition, project_path: str = "") -> str:
        """创建流水线配置文件内容"""
        pass
    
    @abstractmethod
    async def trigger_pipeline(self, pipeline_def: PipelineDefinition, project_path: str = "") -> ExecutionResult:
        """触发流水线执行"""
        pass
    
    @abstractmethod
    async def get_pipeline_status(self, execution_id: str) -> Dict[str, Any]:
        """获取流水线状态"""
        pass
    
    @abstractmethod
    async def cancel_pipeline(self, execution_id: str) -> bool:
        """取消流水线执行"""
        pass
    
    @abstractmethod
    async def get_logs(self, execution_id: str) -> str:
        """获取流水线日志"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
