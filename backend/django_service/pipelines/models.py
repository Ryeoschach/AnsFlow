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
        # Docker 步骤类型
        ('docker_build', 'Docker Build'),
        ('docker_run', 'Docker Run'),
        ('docker_push', 'Docker Push'),
        ('docker_pull', 'Docker Pull'),
        # Kubernetes 步骤类型
        ('k8s_deploy', 'Kubernetes Deploy'),
        ('k8s_scale', 'Kubernetes Scale'),
        ('k8s_delete', 'Kubernetes Delete'),
        ('k8s_wait', 'Kubernetes Wait'),
        ('k8s_exec', 'Kubernetes Exec'),
        ('k8s_logs', 'Kubernetes Logs'),
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
    
    # Docker 配置 - 新增字段
    docker_image = models.CharField(
        max_length=255,
        blank=True,
        help_text="Docker image name for docker step types"
    )
    docker_tag = models.CharField(
        max_length=100,
        blank=True,
        help_text="Docker image tag"
    )
    docker_registry = models.ForeignKey(
        'docker_integration.DockerRegistry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pipeline_steps',
        help_text="Docker registry for push/pull operations"
    )
    docker_config = models.JSONField(
        default=dict,
        help_text="Docker-specific configuration (dockerfile path, build args, etc.)"
    )
    
    # Kubernetes 配置 - 新增字段
    k8s_cluster = models.ForeignKey(
        'kubernetes_integration.KubernetesCluster',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pipeline_steps',
        help_text="Kubernetes cluster for k8s step types"
    )
    k8s_namespace = models.CharField(
        max_length=100,
        blank=True,
        help_text="Kubernetes namespace"
    )
    k8s_resource_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Kubernetes resource name (deployment, service, etc.)"
    )
    k8s_config = models.JSONField(
        default=dict,
        help_text="Kubernetes-specific configuration (deployment spec, wait conditions, etc.)"
    )
    
    # Step execution order
    order = models.PositiveIntegerField(default=0)
    
    # 高级工作流功能字段
    # 依赖关系
    dependencies = models.JSONField(default=list, help_text="List of step IDs this step depends on")
    
    # 并行执行组
    parallel_group = models.CharField(max_length=100, blank=True, help_text="Parallel execution group name")
    
    # 条件执行
    conditions = models.JSONField(default=list, help_text="Execution conditions")
    
    # 审批配置
    approval_required = models.BooleanField(default=False, help_text="Whether this step requires approval")
    approval_users = models.JSONField(default=list, help_text="List of usernames who can approve")
    approval_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('timeout', 'Timeout'),
        ],
        blank=True,
        help_text="Approval status"
    )
    approved_by = models.CharField(max_length=100, blank=True, help_text="Username of approver")
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # 重试策略
    retry_policy = models.JSONField(default=dict, help_text="Retry configuration")
    
    # 通知配置
    notification_config = models.JSONField(default=dict, help_text="Notification configuration")
    
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


class ParallelGroup(models.Model):
    """并行执行组模型"""
    
    SYNC_POLICY_CHOICES = [
        ('wait_all', 'Wait All'),
        ('wait_any', 'Wait Any'),
        ('fail_fast', 'Fail Fast'),
    ]
    
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='parallel_groups')
    sync_policy = models.CharField(max_length=20, choices=SYNC_POLICY_CHOICES, default='wait_all')
    timeout_seconds = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Parallel Group"
        verbose_name_plural = "Parallel Groups"
        
    def __str__(self):
        return f"{self.pipeline.name} - {self.name}"


class ApprovalRequest(models.Model):
    """审批请求模型"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('timeout', 'Timeout'),
    ]
    
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='approval_requests')
    step = models.ForeignKey(PipelineStep, on_delete=models.CASCADE, related_name='approval_requests')
    execution_id = models.CharField(max_length=100, help_text="Pipeline execution ID")
    
    requester_username = models.CharField(max_length=100, help_text="Username of the requester")
    approvers = models.JSONField(default=list, help_text="List of approved usernames")
    required_approvals = models.IntegerField(default=1)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approval_message = models.TextField(blank=True)
    timeout_hours = models.IntegerField(null=True, blank=True)
    auto_approve_on_timeout = models.BooleanField(default=False)
    
    approved_by = models.CharField(max_length=100, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    response_comment = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Approval Request"
        verbose_name_plural = "Approval Requests"
        
    def __str__(self):
        return f"Approval for {self.step.name} - {self.status}"


class WorkflowExecution(models.Model):
    """工作流执行记录模型"""
    
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='workflow_executions')
    execution_id = models.CharField(max_length=100, unique=True)
    
    status = models.CharField(max_length=20, choices=Pipeline.STATUS_CHOICES, default='pending')
    trigger_data = models.JSONField(default=dict)
    context_variables = models.JSONField(default=dict, help_text="Workflow context variables")
    step_results = models.JSONField(default=dict, help_text="Results from each step")
    
    current_step = models.ForeignKey(PipelineStep, on_delete=models.SET_NULL, null=True, blank=True)
    failed_steps = models.JSONField(default=list, help_text="List of failed step IDs")
    pending_approvals = models.JSONField(default=list, help_text="List of step IDs waiting for approval")
    
    recovery_point = models.IntegerField(null=True, blank=True, help_text="Step ID to resume from")
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Workflow Execution"
        verbose_name_plural = "Workflow Executions"
        
    def __str__(self):
        return f"{self.pipeline.name} - {self.execution_id}"


class StepExecutionHistory(models.Model):
    """步骤执行历史模型"""
    
    workflow_execution = models.ForeignKey(WorkflowExecution, on_delete=models.CASCADE, related_name='step_histories')
    step = models.ForeignKey(PipelineStep, on_delete=models.CASCADE)
    
    status = models.CharField(max_length=20, choices=PipelineStep.STEP_STATUS_CHOICES, default='pending')
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=0)
    
    logs = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    output_data = models.JSONField(default=dict)
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Step Execution History"
        verbose_name_plural = "Step Execution Histories"
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.step.name} - {self.status}"
