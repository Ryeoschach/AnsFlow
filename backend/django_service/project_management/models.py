from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    """Project model for CI/CD platform"""
    
    VISIBILITY_CHOICES = [
        ('private', 'Private'),
        ('internal', 'Internal'),
        ('public', 'Public'),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='private')
    
    # Repository information
    repository_url = models.URLField(blank=True, help_text="Git repository URL")
    default_branch = models.CharField(max_length=100, default='main')
    
    # Project settings
    is_active = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, help_text="Project-specific settings")
    
    # Relationships
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    members = models.ManyToManyField(User, through='ProjectMembership', related_name='projects')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name


class ProjectMembership(models.Model):
    """Project membership with roles"""
    
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('maintainer', 'Maintainer'),
        ('developer', 'Developer'),
        ('reporter', 'Reporter'),
        ('guest', 'Guest'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='developer')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['project', 'user']]
        
    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.role})"


class Environment(models.Model):
    """Deployment environment for projects"""
    
    ENV_TYPES = [
        ('development', 'Development'),
        ('testing', 'Testing'),
        ('staging', 'Staging'),
        ('production', 'Production'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='environments')
    name = models.CharField(max_length=100)
    env_type = models.CharField(max_length=20, choices=ENV_TYPES)
    
    # Environment configuration
    url = models.URLField(blank=True, help_text="Environment URL")
    config = models.JSONField(default=dict, help_text="Environment-specific configuration")
    
    # Deployment settings
    auto_deploy = models.BooleanField(default=False)
    deploy_branch = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['project', 'name']]
        ordering = ['project', 'env_type']
        
    def __str__(self):
        return f"{self.project.name} - {self.name}"
