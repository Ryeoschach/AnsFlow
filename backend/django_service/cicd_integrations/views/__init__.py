"""
CI/CD 集成视图模块

将原来庞大的views.py文件拆分为多个模块以提高代码可维护性：
- tools.py: CI/CD工具管理视图
- jenkins.py: Jenkins特定功能视图  
- executions.py: 流水线执行管理视图
- steps.py: 原子步骤管理视图
"""

from .tools import CICDToolViewSet
from .jenkins import JenkinsManagementMixin
from .executions import PipelineExecutionViewSet
from .steps import AtomicStepViewSet
from .git_credentials import GitCredentialViewSet

__all__ = [
    'CICDToolViewSet',
    'JenkinsManagementMixin', 
    'PipelineExecutionViewSet',
    'AtomicStepViewSet',
    'GitCredentialViewSet',
]
