"""
DEPRECATED: This file has been refactored into a modular structure.

The CI/CD adapters have been moved to individual modules for better maintainability:

- Base classes and data structures: cicd_integrations.adapters.base
- Jenkins adapter: cicd_integrations.adapters.jenkins
- GitLab CI adapter: cicd_integrations.adapters.gitlab_ci
- GitHub Actions adapter: cicd_integrations.adapters.github_actions
- Adapter factory: cicd_integrations.adapters.factory

Please update your imports to use the new modular structure. The imports should
remain the same thanks to the __init__.py file:

    from cicd_integrations.adapters import (
        JenkinsAdapter, 
        GitLabCIAdapter, 
        GitHubActionsAdapter,
        AdapterFactory,
        PipelineDefinition,
        ExecutionResult
    )

This file will be removed in a future version.
"""

# Re-export everything from the new modular structure for backward compatibility
from .adapters.base import CICDAdapter, PipelineDefinition, ExecutionResult
from .adapters.jenkins import JenkinsAdapter
from .adapters.gitlab_ci import GitLabCIAdapter
from .adapters.github_actions import GitHubActionsAdapter
from .adapters.factory import AdapterFactory

# Legacy compatibility - keeping old factory name for backward compatibility
CICDAdapterFactory = AdapterFactory

__all__ = [
    'CICDAdapter',
    'PipelineDefinition',
    'ExecutionResult',
    'JenkinsAdapter',
    'GitLabCIAdapter',
    'GitHubActionsAdapter',
    'AdapterFactory',
    'CICDAdapterFactory',  # For backward compatibility
]
