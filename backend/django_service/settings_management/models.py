from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class AuditLog(models.Model):
    """审计日志模型"""
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('VIEW', 'View'),
        ('EXECUTE', 'Execute'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
    ]
    
    RESULT_CHOICES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('warning', 'Warning'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="操作用户")
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, help_text="操作类型")
    resource_type = models.CharField(max_length=100, help_text="资源类型")
    resource_id = models.CharField(max_length=100, blank=True, null=True, help_text="资源ID")
    details = models.JSONField(default=dict, help_text="操作详情")
    ip_address = models.GenericIPAddressField(blank=True, null=True, help_text="IP地址")
    user_agent = models.TextField(blank=True, null=True, help_text="用户代理")
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='success', help_text="操作结果")
    timestamp = models.DateTimeField(auto_now_add=True, help_text="操作时间")
    
    class Meta:
        db_table = 'settings_audit_log'
        ordering = ['-timestamp']
        verbose_name = "审计日志"
        verbose_name_plural = "审计日志"
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.resource_type}"


class SystemAlert(models.Model):
    """系统告警模型"""
    TYPE_CHOICES = [
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('info', 'Info'),
    ]
    
    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, help_text="告警类型")
    message = models.TextField(help_text="告警消息")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, help_text="严重程度")
    component = models.CharField(max_length=100, help_text="相关组件")
    resolved = models.BooleanField(default=False, help_text="是否已解决")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    resolved_at = models.DateTimeField(null=True, blank=True, help_text="解决时间")
    resolved_by = models.CharField(max_length=100, null=True, blank=True, help_text="解决人")
    
    class Meta:
        db_table = 'settings_system_alert'
        ordering = ['-created_at']
        verbose_name = "系统告警"
        verbose_name_plural = "系统告警"
    
    def __str__(self):
        return f"{self.type}: {self.message[:50]}"

    def resolve(self, resolved_by=None):
        """标记告警为已解决"""
        self.resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = resolved_by
        self.save()


class NotificationConfig(models.Model):
    """通知配置模型"""
    TYPE_CHOICES = [
        ('email', 'Email'),
        ('webhook', 'Webhook'),
        ('slack', 'Slack'),
        ('dingtalk', 'DingTalk'),
        ('wechat', 'WeChat'),
    ]
    
    name = models.CharField(max_length=100, help_text="配置名称")
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, help_text="通知类型")
    config = models.JSONField(default=dict, help_text="配置参数")
    enabled = models.BooleanField(default=True, help_text="是否启用")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, help_text="创建者")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新时间")
    
    class Meta:
        db_table = 'settings_notification_config'
        ordering = ['-created_at']
        verbose_name = "通知配置"
        verbose_name_plural = "通知配置"
    
    def __str__(self):
        return f"{self.name} ({self.type})"


class GlobalConfig(models.Model):
    """全局配置模型"""
    CONFIG_TYPES = [
        ('system', 'System'),
        ('feature', 'Feature'),
        ('environment', 'Environment'),
        ('integration', 'Integration'),
    ]
    
    key = models.CharField(max_length=100, unique=True, help_text="配置键")
    value = models.TextField(help_text="配置值")
    type = models.CharField(max_length=50, choices=CONFIG_TYPES, help_text="配置类型")
    description = models.TextField(help_text="配置描述")
    is_sensitive = models.BooleanField(default=False, help_text="是否敏感信息")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, help_text="创建者")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新时间")
    
    class Meta:
        db_table = 'settings_global_config'
        ordering = ['key']
        verbose_name = "全局配置"
        verbose_name_plural = "全局配置"
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"


class UserProfile(models.Model):
    """用户扩展信息模型"""
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('developer', 'Developer'),
        ('viewer', 'Viewer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='viewer', help_text="用户角色")
    phone = models.CharField(max_length=20, blank=True, help_text="手机号")
    department = models.CharField(max_length=100, blank=True, help_text="部门")
    avatar = models.URLField(blank=True, help_text="头像URL")
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, help_text="最后登录IP")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新时间")
    
    class Meta:
        db_table = 'settings_user_profile'
        verbose_name = "用户档案"
        verbose_name_plural = "用户档案"
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"


class BackupRecord(models.Model):
    """备份记录模型"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    name = models.CharField(max_length=100, help_text="备份名称")
    file_path = models.CharField(max_length=500, help_text="备份文件路径")
    file_size = models.BigIntegerField(default=0, help_text="文件大小(字节)")
    backup_type = models.CharField(max_length=50, help_text="备份类型")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text="备份状态")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, help_text="创建者")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="完成时间")
    error_message = models.TextField(blank=True, help_text="错误信息")
    
    class Meta:
        db_table = 'settings_backup_record'
        ordering = ['-created_at']
        verbose_name = "备份记录"
        verbose_name_plural = "备份记录"
    
    def __str__(self):
        return f"{self.name} - {self.status}"


class APIKey(models.Model):
    """API 密钥管理模型"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
    ]
    
    name = models.CharField(max_length=100, help_text="密钥名称")
    key = models.CharField(max_length=64, unique=True, help_text="API密钥")
    secret = models.CharField(max_length=128, help_text="API秘钥")
    permissions = models.JSONField(default=list, help_text="权限列表")
    rate_limit = models.IntegerField(default=1000, help_text="速率限制(每小时)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', help_text="状态")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, help_text="创建者")
    expires_at = models.DateTimeField(null=True, blank=True, help_text="过期时间")
    last_used_at = models.DateTimeField(null=True, blank=True, help_text="最后使用时间")
    usage_count = models.IntegerField(default=0, help_text="使用次数")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新时间")
    
    class Meta:
        db_table = 'settings_api_key'
        ordering = ['-created_at']
        verbose_name = "API密钥"
        verbose_name_plural = "API密钥"
    
    def __str__(self):
        return f"{self.name} - {self.status}"


class APIEndpoint(models.Model):
    """API 端点配置模型"""
    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
        ('PATCH', 'PATCH'),
        ('OPTIONS', 'OPTIONS'),
        ('HEAD', 'HEAD'),
    ]
    
    SERVICE_TYPE_CHOICES = [
        ('django', 'Django Service'),
        ('fastapi', 'FastAPI Service'),
        ('external', 'External API'),
    ]
    
    name = models.CharField(max_length=200, help_text="端点名称")
    path = models.CharField(max_length=500, help_text="API路径")
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, help_text="HTTP方法")
    description = models.TextField(blank=True, help_text="端点描述")
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES, default='django', help_text="服务类型")
    
    # 功能配置
    is_enabled = models.BooleanField(default=True, help_text="是否启用")
    auth_required = models.BooleanField(default=True, help_text="是否需要认证")
    rate_limit = models.IntegerField(default=100, help_text="速率限制(每分钟)")
    permissions_required = models.JSONField(default=list, help_text="所需权限")
    
    # 文档信息
    request_schema = models.JSONField(default=dict, help_text="请求体Schema")
    response_schema = models.JSONField(default=dict, help_text="响应体Schema")
    parameters = models.JSONField(default=list, help_text="参数说明")
    examples = models.JSONField(default=dict, help_text="使用示例")
    
    # 统计信息
    call_count = models.IntegerField(default=0, help_text="调用次数")
    last_called_at = models.DateTimeField(null=True, blank=True, help_text="最后调用时间")
    avg_response_time = models.FloatField(default=0, help_text="平均响应时间(ms)")
    
    # 元数据
    tags = models.JSONField(default=list, help_text="标签")
    version = models.CharField(max_length=20, default='v1', help_text="API版本")
    deprecated = models.BooleanField(default=False, help_text="是否废弃")
    
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新时间")
    
    class Meta:
        db_table = 'settings_api_endpoint'
        unique_together = ['path', 'method']
        verbose_name = "API端点"
        verbose_name_plural = "API端点"
        indexes = [
            models.Index(fields=['service_type', 'is_enabled']),
            models.Index(fields=['method', 'path']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.path}"

    def increment_call_count(self, response_time=None):
        """增加调用计数并更新统计信息"""
        self.call_count += 1
        self.last_called_at = timezone.now()
        
        if response_time is not None:
            # 计算移动平均响应时间
            if self.avg_response_time == 0:
                self.avg_response_time = response_time
            else:
                # 使用指数移动平均
                alpha = 0.1
                self.avg_response_time = (1 - alpha) * self.avg_response_time + alpha * response_time
        
        self.save(update_fields=['call_count', 'last_called_at', 'avg_response_time'])


class SystemSetting(models.Model):
    """系统设置模型 - 扩展版全局配置"""
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('security', 'Security'),
        ('notification', 'Notification'),
        ('performance', 'Performance'),
        ('integration', 'Integration'),
        ('backup', 'Backup'),
        ('monitoring', 'Monitoring'),
    ]
    
    TYPE_CHOICES = [
        ('string', 'String'),
        ('number', 'Number'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
        ('list', 'List'),
        ('password', 'Password'),
    ]
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, help_text="设置分类")
    key = models.CharField(max_length=100, unique=True, help_text="设置键")
    value = models.TextField(help_text="设置值")
    default_value = models.TextField(help_text="默认值")
    data_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='string', help_text="数据类型")
    description = models.TextField(help_text="设置描述")
    is_encrypted = models.BooleanField(default=False, help_text="是否加密")
    is_public = models.BooleanField(default=False, help_text="是否公开")
    validation_rules = models.JSONField(default=dict, help_text="验证规则")
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, help_text="更新者")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新时间")
    
    class Meta:
        db_table = 'settings_system_setting'
        ordering = ['category', 'key']
        verbose_name = "系统设置"
        verbose_name_plural = "系统设置"
    
    def __str__(self):
        return f"{self.category}.{self.key}"


class Team(models.Model):
    """团队模型"""
    name = models.CharField(max_length=100, unique=True, help_text="团队名称")
    description = models.TextField(blank=True, help_text="团队描述")
    avatar = models.URLField(blank=True, help_text="团队头像")
    is_active = models.BooleanField(default=True, help_text="是否活跃")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_teams', help_text="创建者")
    members = models.ManyToManyField(User, through='TeamMembership', through_fields=('team', 'user'), related_name='teams', help_text="团队成员")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新时间")
    
    class Meta:
        db_table = 'settings_team'
        ordering = ['name']
        verbose_name = "团队"
        verbose_name_plural = "团队"
    
    def __str__(self):
        return self.name


class TeamMembership(models.Model):
    """团队成员关系模型"""
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, help_text="团队")
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="用户")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member', help_text="角色")
    joined_at = models.DateTimeField(auto_now_add=True, help_text="加入时间")
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invited_memberships', null=True, blank=True, help_text="邀请者")
    
    class Meta:
        db_table = 'settings_team_membership'
        unique_together = ['team', 'user']
        verbose_name = "团队成员"
        verbose_name_plural = "团队成员"
    
    def __str__(self):
        return f"{self.team.name} - {self.user.username} ({self.role})"


class BackupSchedule(models.Model):
    """备份计划模型"""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('paused', 'Paused'),
    ]
    
    name = models.CharField(max_length=100, help_text="计划名称")
    description = models.TextField(blank=True, help_text="计划描述")
    backup_type = models.CharField(max_length=50, help_text="备份类型")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, help_text="备份频率")
    cron_expression = models.CharField(max_length=100, blank=True, help_text="Cron表达式")
    retain_days = models.IntegerField(default=30, help_text="保留天数")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', help_text="状态")
    notification_config = models.JSONField(default=dict, help_text="通知配置")
    last_run_at = models.DateTimeField(null=True, blank=True, help_text="最后运行时间")
    next_run_at = models.DateTimeField(null=True, blank=True, help_text="下次运行时间")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, help_text="创建者")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新时间")
    
    class Meta:
        db_table = 'settings_backup_schedule'
        ordering = ['-created_at']
        verbose_name = "备份计划"
        verbose_name_plural = "备份计划"
    
    def __str__(self):
        return f"{self.name} - {self.frequency}"


class AuditLogData:
    """用于创建审计日志数据的辅助类"""
    
    @staticmethod
    def create_sample_data():
        """创建示例审计日志数据"""
        import secrets
        from django.contrib.auth.models import User
        
        # 获取或创建用户
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@ansflow.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        developer_user, _ = User.objects.get_or_create(
            username='developer',
            defaults={
                'email': 'developer@ansflow.com',
                'first_name': 'Developer',
                'last_name': 'User',
            }
        )
        
        # 创建示例审计日志
        sample_logs = [
            {
                'user': admin_user,
                'action': 'CREATE',
                'resource_type': 'Pipeline',
                'resource_id': '123',
                'details': {'name': 'Build Pipeline', 'description': 'CI/CD Pipeline'},
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'result': 'success',
            },
            {
                'user': developer_user,
                'action': 'UPDATE',
                'resource_type': 'User',
                'resource_id': '456',
                'details': {'username': 'test_user', 'email': 'test@example.com'},
                'ip_address': '192.168.1.101',
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'result': 'success',
            },
            {
                'user': admin_user,
                'action': 'DELETE',
                'resource_type': 'Tool',
                'resource_id': '789',
                'details': {'tool_name': 'old_jenkins', 'tool_type': 'jenkins'},
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'result': 'warning',
            },
            {
                'user': developer_user,
                'action': 'LOGIN',
                'resource_type': 'Auth',
                'details': {'login_method': 'username_password'},
                'ip_address': '192.168.1.102',
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                'result': 'success',
            },
            {
                'user': admin_user,
                'action': 'EXECUTE',
                'resource_type': 'Pipeline',
                'resource_id': '123',
                'details': {'execution_id': 'exec_001', 'trigger_type': 'manual'},
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'result': 'failure',
            },
        ]
        
        created_logs = []
        for log_data in sample_logs:
            log, created = AuditLog.objects.get_or_create(
                user=log_data['user'],
                action=log_data['action'],
                resource_type=log_data['resource_type'],
                resource_id=log_data.get('resource_id'),
                defaults=log_data
            )
            if created:
                created_logs.append(log)
        
        return created_logs
