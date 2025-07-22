"""
CI/CD 工具集成数据模型
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.conf import settings
from cryptography.fernet import Fernet
import json


class CICDTool(models.Model):
    """CI/CD 工具配置模型"""
    
    TOOL_TYPES = [
        ('jenkins', 'Jenkins'),
        ('gitlab_ci', 'GitLab CI'),
        ('circleci', 'CircleCI'),
        ('github_actions', 'GitHub Actions'),
        ('azure_devops', 'Azure DevOps'),
        ('local', 'Local Executor'),  # 本地执行器
        ('custom', 'Custom Tool'),
    ]
    
    STATUSES = [
        ('authenticated', 'Authenticated'),  # 已认证，可以正常使用
        ('needs_auth', 'Needs Authentication'),  # 需要认证
        ('offline', 'Offline'),  # 离线或不可访问
        ('unknown', 'Unknown'),  # 状态未知
        ('error', 'Error'),  # 出错
        # 保留向后兼容
        ('active', 'Active'),  # 保留旧状态以避免数据问题
        ('inactive', 'Inactive'),
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


class GitCredential(models.Model):
    """Git仓库认证凭据"""
    CREDENTIAL_TYPES = [
        ('username_password', '用户名密码'),
        ('ssh_key', 'SSH密钥'),
        ('access_token', '访问令牌'),
        ('oauth', 'OAuth认证'),
    ]
    
    PLATFORM_TYPES = [
        ('gitlab', 'GitLab'),
        ('github', 'GitHub'),
        ('gitee', 'Gitee'),
        ('bitbucket', 'Bitbucket'),
        ('azure_devops', 'Azure DevOps'),
        ('custom', '自定义Git服务'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='凭据名称')
    platform = models.CharField(max_length=20, choices=PLATFORM_TYPES, verbose_name='Git平台')
    credential_type = models.CharField(max_length=20, choices=CREDENTIAL_TYPES, verbose_name='认证类型')
    
    # 基础信息
    server_url = models.URLField(verbose_name='服务器地址', help_text='如: https://gitlab.company.com')
    username = models.CharField(max_length=100, blank=True, verbose_name='用户名')
    
    # 敏感信息(加密存储)
    password_encrypted = models.TextField(blank=True, verbose_name='加密后的密码/Token')
    ssh_private_key_encrypted = models.TextField(blank=True, verbose_name='加密后的SSH私钥')
    ssh_public_key = models.TextField(blank=True, verbose_name='SSH公钥')
    
    # 元数据
    description = models.TextField(blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 测试连接状态
    last_test_at = models.DateTimeField(null=True, blank=True, verbose_name='上次测试时间')
    last_test_result = models.BooleanField(null=True, blank=True, verbose_name='上次测试结果')
    
    class Meta:
        verbose_name = 'Git认证凭据'
        verbose_name_plural = 'Git认证凭据'
        unique_together = ['name', 'created_by']  # 同一用户下凭据名称唯一
    
    def __str__(self):
        return f"{self.name} ({self.get_platform_display()})"
    
    def encrypt_password(self, password):
        """加密密码/Token"""
        if not password or not password.strip():
            return
        
        try:
            # 使用项目密钥进行加密，如果没有设置则生成一个
            key = getattr(settings, 'GIT_CREDENTIAL_ENCRYPTION_KEY', None)
            if not key:
                # 生成一个默认密钥（生产环境中应该设置在settings中）
                key = Fernet.generate_key()
            if isinstance(key, str):
                key = key.encode()
            f = Fernet(key)
            self.password_encrypted = f.encrypt(password.encode()).decode()
        except Exception as e:
            # 如果加密失败，记录错误但不阻止保存
            print(f"Failed to encrypt password: {e}")
            self.password_encrypted = ""
    
    def decrypt_password(self):
        """解密密码/Token"""
        if not self.password_encrypted:
            return None
        try:
            key = getattr(settings, 'GIT_CREDENTIAL_ENCRYPTION_KEY', None)
            if not key:
                return None
            if isinstance(key, str):
                key = key.encode()
            f = Fernet(key)
            return f.decrypt(self.password_encrypted.encode()).decode()
        except Exception as e:
            print(f"Failed to decrypt password: {e}")
            return None
    
    def encrypt_ssh_key(self, private_key):
        """加密SSH私钥"""
        if not private_key or not private_key.strip():
            return
        
        try:
            key = getattr(settings, 'GIT_CREDENTIAL_ENCRYPTION_KEY', None)
            if not key:
                key = Fernet.generate_key()
            if isinstance(key, str):
                key = key.encode()
            f = Fernet(key)
            self.ssh_private_key_encrypted = f.encrypt(private_key.encode()).decode()
        except Exception as e:
            print(f"Failed to encrypt SSH key: {e}")
            self.ssh_private_key_encrypted = ""
    
    def decrypt_ssh_key(self):
        """解密SSH私钥"""
        if not self.ssh_private_key_encrypted:
            return None
        try:
            key = getattr(settings, 'GIT_CREDENTIAL_ENCRYPTION_KEY', None)
            if not key:
                return None
            if isinstance(key, str):
                key = key.encode()
            f = Fernet(key)
            return f.decrypt(self.ssh_private_key_encrypted.encode()).decode()
        except Exception as e:
            print(f"Failed to decrypt SSH key: {e}")
            return None


class AtomicStep(models.Model):
    """原子化步骤定义"""
    
    STEP_TYPES = [
        ('fetch_code', 'Fetch Code'),
        ('build', 'Build'),
        ('test', 'Test'),
        ('security_scan', 'Security Scan'),
        ('deploy', 'Deploy'),
        ('ansible', 'Ansible Automation'),
        ('notify', 'Notify'),
        ('custom', 'Custom'),
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
        # 工作流控制步骤
        ('approval', 'Approval'),
        ('shell_script', 'Shell Script'),
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
    
    # Git认证凭据(用于fetch_code步骤)
    git_credential = models.ForeignKey(
        GitCredential, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="代码拉取步骤使用的Git认证凭据"
    )
    
    # Ansible相关字段(用于ansible步骤)
    ansible_playbook = models.ForeignKey(
        'ansible_integration.AnsiblePlaybook',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Ansible步骤使用的Playbook"
    )
    ansible_inventory = models.ForeignKey(
        'ansible_integration.AnsibleInventory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Ansible步骤使用的Inventory"
    )
    ansible_credential = models.ForeignKey(
        'ansible_integration.AnsibleCredential',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Ansible步骤使用的SSH认证凭据"
    )
    
    # 依赖关系(字符串形式的步骤名称列表)
    dependencies = models.JSONField(default=list, help_text="依赖的步骤名称列表")
    
    # 并行执行组
    parallel_group = models.CharField(max_length=100, blank=True, help_text="并行执行组名称")
    
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
                                   related_name='executions', null=True, blank=True)
    
    # 支持新的PipelineStep（为了向后兼容，保留atomic_step字段）
    pipeline_step = models.ForeignKey('pipelines.PipelineStep', on_delete=models.CASCADE,
                                     related_name='executions', null=True, blank=True)
    
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
        if self.atomic_step:
            return f"{self.atomic_step.name} - {self.status}"
        elif self.pipeline_step:
            return f"{self.pipeline_step.name} - {self.status}"
        else:
            return f"Step {self.order} - {self.status}"
    
    @property
    def step_name(self):
        """获取步骤名称"""
        if self.atomic_step:
            return self.atomic_step.name
        elif self.pipeline_step:
            return self.pipeline_step.name
        else:
            return f"Step {self.order}"
    
    def clean(self):
        """确保atomic_step和pipeline_step中至少有一个不为空"""
        from django.core.exceptions import ValidationError
        if not self.atomic_step and not self.pipeline_step:
            raise ValidationError("Must have either atomic_step or pipeline_step")
    
    @property
    def duration(self):
        """计算步骤执行时长"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
