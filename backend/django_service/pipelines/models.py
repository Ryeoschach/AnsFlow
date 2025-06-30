from django.db import models
from django.contrib.auth.models import User


class Pipeline(models.Model):
    """CI/CD Pipeline model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=255, help_text="Pipeline name")
    description = models.TextField(blank=True, help_text="Pipeline description")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=True, help_text="Whether the pipeline is active")
    
    # Configuration
    config = models.JSONField(default=dict, help_text="Pipeline configuration in JSON format")
    
    # Relationships
    project = models.ForeignKey('project_management.Project', on_delete=models.CASCADE, related_name='pipelines')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_pipelines')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Pipeline"
        verbose_name_plural = "Pipelines"
        
    def __str__(self):
        return f"{self.name} ({self.status})"


class PipelineStep(models.Model):
    """Individual step in a pipeline"""
    
    STEP_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STEP_STATUS_CHOICES, default='pending')
    
    # Step configuration
    command = models.TextField(help_text="Command or script to execute")
    environment_vars = models.JSONField(default=dict, help_text="Environment variables for this step")
    timeout_seconds = models.IntegerField(default=300, help_text="Timeout in seconds")
    
    # Step execution order
    order = models.PositiveIntegerField(default=0)
    
    # Execution results
    output_log = models.TextField(blank=True, help_text="Step execution output")
    error_log = models.TextField(blank=True, help_text="Step execution errors")
    exit_code = models.IntegerField(null=True, blank=True)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['order']
        unique_together = [['pipeline', 'order']]
        
    def __str__(self):
        return f"{self.pipeline.name} - {self.name}"


class PipelineRun(models.Model):
    """A specific execution/run of a pipeline"""
    
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='runs')
    run_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Pipeline.STATUS_CHOICES, default='pending')
    
    # Trigger information
    triggered_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='triggered_pipeline_runs')
    trigger_type = models.CharField(max_length=50, help_text="manual, webhook, schedule, etc.")
    trigger_data = models.JSONField(default=dict, help_text="Additional trigger information")
    
    # Execution metadata
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Results
    artifacts = models.JSONField(default=list, help_text="List of generated artifacts")
    
    class Meta:
        ordering = ['-run_number']
        unique_together = [['pipeline', 'run_number']]
        
    def __str__(self):
        return f"{self.pipeline.name} - Run #{self.run_number}"
