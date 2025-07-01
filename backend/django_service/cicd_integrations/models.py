"""
CI/CD 工具集成数据模型
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator
import json


class CICDTool(models.Model):
    """CI/CD 工具配置模型"""
    
    TOOL_TYPES = [
        ('jenkins', 'Jenkins'),
        ('gitlab_ci', 'GitLab CI'),
        ('circleci', 'CircleCI'),
        ('github_actions', 'GitHub Actions'),
        ('azure_devops', 'Azure DevOps'),
        ('custom', 'Custom Tool'),
    ]
    
    STATUSES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
    ]
    
    name = models.CharField(max_length=255, help_text="工具实例名称")
    tool_type = models.CharField(max_length=50, choices=TOOL_TYPES, help_text="工具类型")
    base_url = models.URLField(help_text="工具服务器基础URL")
    description = models.TextField(blank=True, help_text="工具描述")
    
    # 认证配置
    username = models.CharField(max_length=255, blank=True, help_text="用户名")
    token = models.CharField(max_length=500, help_text="API令牌或密码")
    
    # 配置和元数据
    config = models.JSONField(default=dict, help_text="工具特定配置")
    metadata = models.JSONField(default=dict, help_text="额外的元数据")
    
    # 状态
    status = models.CharField(max_length=20, choices=STATUSES, default='active')
    last_health_check = models.DateTimeField(null=True, blank=True)
    
    # 关系
    project = models.ForeignKey('project_management.Project', on_delete=models.CASCADE, 
                               related_name='cicd_tools', help_text="关联项目")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, 
                                  related_name='created_tools')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "CI/CD Tool"
        verbose_name_plural = "CI/CD Tools"
        unique_together = ['project', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_tool_type_display()})"


class AtomicStep(models.Model):
    """原子化步骤定义"""
    
    STEP_TYPES = [
        ('fetch_code', 'Fetch Code'),
        ('build', 'Build'),
        ('test', 'Test'),
        ('security_scan', 'Security Scan'),
        ('deploy', 'Deploy'),
        ('notify', 'Notify'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=255, help_text="步骤名称")
    step_type = models.CharField(max_length=50, choices=STEP_TYPES, help_text="步骤类型")
    description = models.TextField(blank=True, help_text="步骤描述")
    
    # 关联流水线
    pipeline = models.ForeignKey('pipelines.Pipeline', on_delete=models.CASCADE,
                                related_name='atomic_steps', 
                                help_text="所属流水线",
                                null=True, blank=True)
    
    # 执行顺序
    order = models.PositiveIntegerField(default=0, help_text="执行顺序")
    
    # 参数配置
    parameters = models.JSONField(default=dict, help_text="步骤参数配置")
    config = models.JSONField(default=dict, help_text="步骤配置")
    
    # 依赖关系(字符串形式的步骤名称列表)
    dependencies = models.JSONField(default=list, help_text="依赖的步骤名称列表")
    
    # 条件执行
    conditions = models.JSONField(default=dict, help_text="执行条件")
    
    # 超时和重试
    timeout = models.PositiveIntegerField(default=600, help_text="超时时间(秒)")
    retry_count = models.PositiveIntegerField(default=0, help_text="重试次数")
    
    # 所有者
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                  related_name='atomic_steps')
    is_public = models.BooleanField(default=False, help_text="是否为公共步骤")
    is_active = models.BooleanField(default=True, help_text="是否激活")
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Atomic Step"
        verbose_name_plural = "Atomic Steps"
    
    def __str__(self):
        return f"{self.name} ({self.get_step_type_display()})"


class PipelineExecution(models.Model):
    """流水线执行记录"""
    
    EXECUTION_STATUSES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('timeout', 'Timeout'),
    ]
    
    TRIGGER_TYPES = [
        ('manual', 'Manual'),
        ('webhook', 'Webhook'),
        ('schedule', 'Schedule'),
        ('api', 'API'),
    ]
    
    pipeline = models.ForeignKey('pipelines.Pipeline', on_delete=models.CASCADE,
                                related_name='executions')
    cicd_tool = models.ForeignKey(CICDTool, on_delete=models.CASCADE,
                                 related_name='executions',
                                 null=True, blank=True,
                                 help_text="关联的CI/CD工具，为空表示本地执行")
    
    # 执行信息
    external_id = models.CharField(max_length=255, blank=True, help_text="外部工具中的执行ID")
    external_url = models.URLField(blank=True, help_text="外部工具中的执行URL")
    
    status = models.CharField(max_length=20, choices=EXECUTION_STATUSES, default='pending')
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES, default='manual')
    
    # 执行配置
    definition = models.JSONField(default=dict, help_text="执行时的流水线定义")
    parameters = models.JSONField(default=dict, help_text="执行参数")
    
    # 执行结果
    logs = models.TextField(blank=True, help_text="执行日志")
    artifacts = models.JSONField(default=list, help_text="构建产物")
    test_results = models.JSONField(default=dict, help_text="测试结果")
    
    # 时间信息
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # 触发信息
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='triggered_executions')
    trigger_data = models.JSONField(default=dict, help_text="触发时的数据")
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Pipeline Execution"
        verbose_name_plural = "Pipeline Executions"
        # 移除unique_together约束，因为本地执行没有cicd_tool和external_id
    
    def __str__(self):
        return f"{self.pipeline.name} - {self.external_id} ({self.status})"
    
    @property
    def duration(self):
        """计算执行时长"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class StepExecution(models.Model):
    """步骤执行记录"""
    
    STEP_STATUSES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
        ('cancelled', 'Cancelled'),
    ]
    
    pipeline_execution = models.ForeignKey(PipelineExecution, on_delete=models.CASCADE,
                                          related_name='step_executions')
    atomic_step = models.ForeignKey(AtomicStep, on_delete=models.CASCADE,
                                   related_name='executions')
    
    # 执行信息
    external_id = models.CharField(max_length=255, blank=True, help_text="外部工具中的步骤ID")
    status = models.CharField(max_length=20, choices=STEP_STATUSES, default='pending')
    order = models.IntegerField(help_text="执行顺序")
    
    # 执行结果
    logs = models.TextField(blank=True, help_text="步骤日志")
    output = models.JSONField(default=dict, help_text="步骤输出")
    error_message = models.TextField(blank=True, help_text="错误信息")
    
    # 时间信息
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Step Execution"
        verbose_name_plural = "Step Executions"
        unique_together = ['pipeline_execution', 'order']
    
    def __str__(self):
        return f"{self.atomic_step.name} - {self.status}"
    
    @property
    def duration(self):
        """计算步骤执行时长"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
