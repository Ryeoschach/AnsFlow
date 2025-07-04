from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings
import json


def get_cipher():
    """获取加密器"""
    key = getattr(settings, 'ENCRYPTION_KEY', Fernet.generate_key())
    return Fernet(key)


def encrypt_password(password):
    """加密密码"""
    if not password:
        return ''
    cipher = get_cipher()
    return cipher.encrypt(password.encode()).decode()


def decrypt_password(encrypted_password):
    """解密密码"""
    if not encrypted_password:
        return ''
    cipher = get_cipher()
    return cipher.decrypt(encrypted_password.encode()).decode()


class AnsibleInventory(models.Model):
    """Ansible主机清单"""
    FORMAT_CHOICES = [
        ('ini', 'INI格式'),
        ('yaml', 'YAML格式'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='清单名称')
    description = models.TextField(blank=True, verbose_name='描述')
    content = models.TextField(verbose_name='清单内容')
    format_type = models.CharField(
        max_length=10, 
        choices=FORMAT_CHOICES, 
        default='ini',
        verbose_name='格式类型'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'ansible_inventory'
        verbose_name = 'Ansible主机清单'
        verbose_name_plural = 'Ansible主机清单'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class AnsiblePlaybook(models.Model):
    """Ansible Playbook"""
    CATEGORY_CHOICES = [
        ('web', 'Web应用'),
        ('database', '数据库'),
        ('monitoring', '监控'),
        ('security', '安全'),
        ('networking', '网络'),
        ('system', '系统'),
        ('other', '其他'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='Playbook名称')
    description = models.TextField(blank=True, verbose_name='描述')
    content = models.TextField(verbose_name='Playbook内容')
    version = models.CharField(max_length=50, default='1.0', verbose_name='版本')
    is_template = models.BooleanField(default=False, verbose_name='是否为模板')
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES,
        default='other',
        verbose_name='分类'
    )
    parameters = models.JSONField(default=dict, verbose_name='可配置参数')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'ansible_playbook'
        verbose_name = 'Ansible Playbook'
        verbose_name_plural = 'Ansible Playbooks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (v{self.version})"


class AnsibleCredential(models.Model):
    """Ansible连接凭据"""
    CREDENTIAL_TYPE_CHOICES = [
        ('ssh_key', 'SSH密钥'),
        ('password', '用户名密码'),
        ('vault', 'Ansible Vault'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='凭据名称')
    credential_type = models.CharField(
        max_length=20, 
        choices=CREDENTIAL_TYPE_CHOICES,
        verbose_name='凭据类型'
    )
    username = models.CharField(max_length=100, blank=True, verbose_name='用户名')
    password = models.TextField(blank=True, verbose_name='密码')  # 加密存储
    ssh_private_key = models.TextField(blank=True, verbose_name='SSH私钥')  # 加密存储
    vault_password = models.TextField(blank=True, verbose_name='Vault密码')  # 加密存储
    sudo_password = models.TextField(blank=True, verbose_name='Sudo密码')  # 加密存储
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'ansible_credential'
        verbose_name = 'Ansible凭据'
        verbose_name_plural = 'Ansible凭据'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_credential_type_display()})"

    def save(self, *args, **kwargs):
        """保存时加密敏感字段"""
        if self.password:
            self.password = encrypt_password(self.password)
        if self.ssh_private_key:
            self.ssh_private_key = encrypt_password(self.ssh_private_key)
        if self.vault_password:
            self.vault_password = encrypt_password(self.vault_password)
        if self.sudo_password:
            self.sudo_password = encrypt_password(self.sudo_password)
        super().save(*args, **kwargs)

    def get_decrypted_password(self):
        """获取解密后的密码"""
        return decrypt_password(self.password) if self.password else ''

    def get_decrypted_ssh_key(self):
        """获取解密后的SSH密钥"""
        return decrypt_password(self.ssh_private_key) if self.ssh_private_key else ''

    def get_decrypted_vault_password(self):
        """获取解密后的Vault密码"""
        return decrypt_password(self.vault_password) if self.vault_password else ''

    def get_decrypted_sudo_password(self):
        """获取解密后的Sudo密码"""
        return decrypt_password(self.sudo_password) if self.sudo_password else ''

    @property
    def has_password(self):
        """是否设置了密码"""
        return bool(self.password)

    @property
    def has_ssh_key(self):
        """是否设置了SSH密钥"""
        return bool(self.ssh_private_key)

    @property
    def has_vault_password(self):
        """是否设置了Vault密码"""
        return bool(self.vault_password)


class AnsibleExecution(models.Model):
    """Ansible执行记录"""
    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]
    
    playbook = models.ForeignKey(
        AnsiblePlaybook, 
        on_delete=models.CASCADE,
        verbose_name='Playbook'
    )
    inventory = models.ForeignKey(
        AnsibleInventory, 
        on_delete=models.CASCADE,
        verbose_name='主机清单'
    )
    credential = models.ForeignKey(
        AnsibleCredential, 
        on_delete=models.CASCADE,
        verbose_name='认证凭据'
    )
    pipeline = models.ForeignKey(
        'pipelines.Pipeline',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ansible_executions',
        verbose_name='关联流水线',
        help_text='如果此Ansible执行是流水线的一部分'
    )
    pipeline_step = models.ForeignKey(
        'pipelines.PipelineStep',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ansible_executions',
        verbose_name='关联流水线步骤',
        help_text='如果此Ansible执行对应特定的流水线步骤'
    )
    parameters = models.JSONField(default=dict, verbose_name='执行参数')
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='状态'
    )
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    stdout = models.TextField(blank=True, verbose_name='标准输出')
    stderr = models.TextField(blank=True, verbose_name='错误输出')
    return_code = models.IntegerField(null=True, blank=True, verbose_name='返回码')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'ansible_execution'
        verbose_name = 'Ansible执行记录'
        verbose_name_plural = 'Ansible执行记录'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.playbook.name} - {self.get_status_display()}"

    @property
    def duration(self):
        """执行时长（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def start_execution(self):
        """开始执行"""
        self.status = 'running'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])

    def complete_execution(self, success=True, return_code=0, stdout='', stderr=''):
        """完成执行"""
        self.status = 'success' if success else 'failed'
        self.completed_at = timezone.now()
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr
        self.save(update_fields=['status', 'completed_at', 'return_code', 'stdout', 'stderr'])

    def cancel_execution(self):
        """取消执行"""
        self.status = 'cancelled'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
