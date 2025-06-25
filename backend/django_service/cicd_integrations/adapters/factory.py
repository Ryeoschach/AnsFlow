"""
CI/CD Adapter Factory

This module provides a centralized factory for creating CI/CD adapter instances.
The factory handles adapter registration, discovery, and instantiation.
"""

from typing import Dict, Type, Optional
from .base import CICDAdapter
from .jenkins import JenkinsAdapter
from .gitlab_ci import GitLabCIAdapter
from .github_actions import GitHubActionsAdapter


class AdapterFactory:
    """Factory class for creating CI/CD adapter instances."""
    
    # Registry of available adapters
    _adapters: Dict[str, Type[CICDAdapter]] = {
        'jenkins': JenkinsAdapter,
        'gitlab': GitLabCIAdapter,
        'github': GitHubActionsAdapter,
    }
    
    @classmethod
    def create_adapter(cls, platform: str, **kwargs) -> CICDAdapter:
        """
        Create an adapter instance for the specified platform.
        
        Args:
            platform: The CI/CD platform name (jenkins, gitlab, github)
            **kwargs: Additional arguments to pass to the adapter constructor
            
        Returns:
            CICDAdapter: An instance of the appropriate adapter
            
        Raises:
            ValueError: If the platform is not supported
        """
        platform_lower = platform.lower()
        
        if platform_lower not in cls._adapters:
            supported_platforms = ', '.join(cls._adapters.keys())
            raise ValueError(
                f"Unsupported platform '{platform}'. "
                f"Supported platforms: {supported_platforms}"
            )
        
        adapter_class = cls._adapters[platform_lower]
        return adapter_class(**kwargs)
    
    @classmethod
    def register_adapter(cls, platform: str, adapter_class: Type[CICDAdapter]) -> None:
        """
        Register a new adapter class for a platform.
        
        Args:
            platform: The platform name
            adapter_class: The adapter class to register
        """
        if not issubclass(adapter_class, CICDAdapter):
            raise TypeError("Adapter class must inherit from CICDAdapter")
        
        cls._adapters[platform.lower()] = adapter_class
    
    @classmethod
    def get_supported_platforms(cls) -> list:
        """
        Get a list of supported platforms.
        
        Returns:
            list: List of supported platform names
        """
        return list(cls._adapters.keys())
    
    @classmethod
    def is_platform_supported(cls, platform: str) -> bool:
        """
        Check if a platform is supported.
        
        Args:
            platform: The platform name to check
            
        Returns:
            bool: True if the platform is supported, False otherwise
        """
        return platform.lower() in cls._adapters


# Convenience functions for creating specific adapters
def create_jenkins_adapter(**kwargs) -> JenkinsAdapter:
    """Create a Jenkins adapter instance."""
    return AdapterFactory.create_adapter('jenkins', **kwargs)


def create_gitlab_adapter(**kwargs) -> GitLabCIAdapter:
    """Create a GitLab CI adapter instance."""
    return AdapterFactory.create_adapter('gitlab', **kwargs)


def create_github_adapter(**kwargs) -> GitHubActionsAdapter:
    """Create a GitHub Actions adapter instance."""
    return AdapterFactory.create_adapter('github', **kwargs)


def get_adapter_for_platform(platform: str, **kwargs) -> CICDAdapter:
    """
    Get an adapter instance for the specified platform.
    
    This is an alias for AdapterFactory.create_adapter() for convenience.
    
    Args:
        platform: The CI/CD platform name
        **kwargs: Additional arguments to pass to the adapter constructor
        
    Returns:
        CICDAdapter: An instance of the appropriate adapter
    """
    return AdapterFactory.create_adapter(platform, **kwargs)


def get_adapter(platform: str, **kwargs) -> CICDAdapter:
    """
    Factory function to create an adapter instance.
    
    Args:
        platform: The CI/CD platform name
        **kwargs: Additional arguments to pass to the adapter constructor
        
    Returns:
        CICDAdapter: An instance of the appropriate adapter
    """
    return AdapterFactory.create_adapter(platform, **kwargs)
