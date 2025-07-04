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
    
    # 新增：CI/CD工具关联
    execution_tool = models.ForeignKey(
        'cicd_integrations.CICDTool', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pipelines',
        help_text="执行此流水线的CI/CD工具"
    )
    
    # 新增：工具特定配置
    tool_job_name = models.CharField(
        max_length=255, 
        blank=True,
        help_text="在CI/CD工具中对应的作业名称"
    )
    
    tool_job_config = models.JSONField(
        default=dict,
        help_text="工具特定的作业配置"
    )
    
    # 新增：执行模式
    EXECUTION_MODES = [
        ('local', 'Local Execution'),      # 本地Celery执行
        ('remote', 'Remote Tool'),         # 远程CI/CD工具执行
        ('hybrid', 'Hybrid'),              # 混合模式
    ]
    execution_mode = models.CharField(
        max_length=20, 
        choices=EXECUTION_MODES, 
        default='local'
    )
    
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
    
    # 步骤类型 - 新增
    STEP_TYPE_CHOICES = [
        ('fetch_code', 'Code Fetch'),
        ('build', 'Build'),
        ('test', 'Test Execution'),
        ('security_scan', 'Security Scan'),
        ('deploy', 'Deployment'),
        ('ansible', 'Ansible Playbook'),
        ('notify', 'Notification'),
        ('custom', 'Custom Step'),
        ('script', 'Script Execution'),
    ]
    
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STEP_STATUS_CHOICES, default='pending')
    
    # 步骤类型 - 新增字段
    step_type = models.CharField(
        max_length=20, 
        choices=STEP_TYPE_CHOICES, 
        default='custom',
        help_text="Type of step to execute"
    )
    
    # Step configuration
    command = models.TextField(blank=True, help_text="Command or script to execute")
    environment_vars = models.JSONField(default=dict, help_text="Environment variables for this step")
    timeout_seconds = models.IntegerField(default=300, help_text="Timeout in seconds")
    
    # Ansible配置 - 新增字段
    ansible_playbook = models.ForeignKey(
        'ansible_integration.AnsiblePlaybook',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pipeline_steps',
        help_text="Ansible playbook to execute (for ansible step type)"
    )
    ansible_inventory = models.ForeignKey(
        'ansible_integration.AnsibleInventory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pipeline_steps',
        help_text="Ansible inventory to use (for ansible step type)"
    )
    ansible_credential = models.ForeignKey(
        'ansible_integration.AnsibleCredential',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pipeline_steps',
        help_text="Ansible credential to use (for ansible step type)"
    )
    ansible_parameters = models.JSONField(
        default=dict,
        help_text="Additional parameters for Ansible execution"
    )
    
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


class PipelineToolMapping(models.Model):
    """流水线与工具作业的映射关系"""
    
    pipeline = models.OneToOneField(
        Pipeline, 
        on_delete=models.CASCADE,
        related_name='tool_mapping'
    )
    
    tool = models.ForeignKey(
        'cicd_integrations.CICDTool',
        on_delete=models.CASCADE,
        related_name='pipeline_mappings'
    )
    
    # 工具特定标识
    external_job_id = models.CharField(
        max_length=255,
        help_text="在外部工具中的作业ID"
    )
    external_job_name = models.CharField(
        max_length=255,
        help_text="在外部工具中的作业名称"
    )
    
    # 同步配置
    auto_sync = models.BooleanField(
        default=True,
        help_text="是否自动同步状态"
    )
    
    last_sync_at = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=50, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Pipeline Tool Mapping"
        verbose_name_plural = "Pipeline Tool Mappings"
        unique_together = ['pipeline', 'tool']
        
    def __str__(self):
        return f"{self.pipeline.name} → {self.tool.name} ({self.external_job_name})"
