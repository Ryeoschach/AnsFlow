"""
CI/CD 适配器模块

这个模块包含了不同CI/CD平台的适配器实现，采用适配器模式统一接口。

支持的平台:
- Jenkins
- GitLab CI
- GitHub Actions
- CircleCI (计划中)
- Azure DevOps (计划中)
"""

from .base import CICDAdapter, PipelineDefinition, ExecutionResult
from .jenkins import JenkinsAdapter
from .gitlab_ci import GitLabCIAdapter
from .github_actions import GitHubActionsAdapter
from .factory import (
    AdapterFactory,
    create_jenkins_adapter,
    create_gitlab_adapter,
    create_github_adapter,
    get_adapter_for_platform,
    get_adapter
)

# 向后兼容性别名
CICDAdapterFactory = AdapterFactory

__all__ = [
    'CICDAdapter',
    'PipelineDefinition', 
    'ExecutionResult',
    'JenkinsAdapter',
    'GitLabCIAdapter',
    'GitHubActionsAdapter',
    'AdapterFactory',
    'CICDAdapterFactory',  # 向后兼容性
    'create_jenkins_adapter',
    'create_gitlab_adapter',
    'create_github_adapter',
    'get_adapter_for_platform'
]
