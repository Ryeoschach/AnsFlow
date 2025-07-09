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
    
    SOURCE_CHOICES = [
        ('manual', '手动输入'),
        ('file', '文件上传'),
        ('git', 'Git仓库'),
        ('dynamic', '动态Inventory'),
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
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='manual',
        verbose_name='来源类型'
    )
    file_path = models.CharField(max_length=500, blank=True, verbose_name='文件路径')
    git_url = models.URLField(blank=True, verbose_name='Git仓库URL')
    git_branch = models.CharField(max_length=100, default='main', verbose_name='Git分支')
    dynamic_script = models.TextField(blank=True, verbose_name='动态脚本')
    version = models.CharField(max_length=50, default='1.0', verbose_name='版本号')
    checksum = models.CharField(max_length=64, blank=True, verbose_name='文件校验和')
    is_validated = models.BooleanField(default=False, verbose_name='是否已验证')
    validation_message = models.TextField(blank=True, verbose_name='验证信息')
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
        ('container', '容器部署'),
        ('cloud', '云服务'),
        ('other', '其他'),
    ]
    
    SOURCE_CHOICES = [
        ('manual', '手动创建'),
        ('file', '文件上传'),
        ('git', 'Git仓库'),
        ('template', '模板克隆'),
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
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='manual',
        verbose_name='来源类型'
    )
    file_path = models.CharField(max_length=500, blank=True, verbose_name='文件路径')
    git_url = models.URLField(blank=True, verbose_name='Git仓库URL')
    git_branch = models.CharField(max_length=100, default='main', verbose_name='Git分支')
    git_path = models.CharField(max_length=500, blank=True, verbose_name='Git中的路径')
    
    # 版本和验证
    checksum = models.CharField(max_length=64, blank=True, verbose_name='内容校验和')
    is_validated = models.BooleanField(default=False, verbose_name='是否已验证')
    validation_message = models.TextField(blank=True, verbose_name='验证信息')
    syntax_check_passed = models.BooleanField(default=False, verbose_name='语法检查通过')
    
    # 配置参数
    parameters = models.JSONField(default=dict, verbose_name='可配置参数')
    required_vars = models.JSONField(default=list, verbose_name='必需变量')
    default_vars = models.JSONField(default=dict, verbose_name='默认变量')
    
    # 依赖和需求
    ansible_version = models.CharField(max_length=20, blank=True, verbose_name='Ansible版本要求')
    required_collections = models.JSONField(default=list, verbose_name='需要的Collection')
    required_roles = models.JSONField(default=list, verbose_name='需要的Role')
    
    # 执行统计
    execution_count = models.IntegerField(default=0, verbose_name='执行次数')
    success_count = models.IntegerField(default=0, verbose_name='成功次数')
    last_executed = models.DateTimeField(null=True, blank=True, verbose_name='最后执行时间')
    
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


class AnsibleInventoryVersion(models.Model):
    """Ansible主机清单版本历史"""
    inventory = models.ForeignKey(
        AnsibleInventory,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name='主机清单'
    )
    version = models.CharField(max_length=50, verbose_name='版本号')
    content = models.TextField(verbose_name='内容快照')
    checksum = models.CharField(max_length=64, verbose_name='内容校验和')
    changelog = models.TextField(blank=True, verbose_name='变更说明')
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'ansible_inventory_version'
        verbose_name = 'Inventory版本'
        verbose_name_plural = 'Inventory版本历史'
        ordering = ['-created_at']
        unique_together = ['inventory', 'version']

    def __str__(self):
        return f"{self.inventory.name} v{self.version}"


class AnsiblePlaybookVersion(models.Model):
    """Ansible Playbook版本历史"""
    playbook = models.ForeignKey(
        AnsiblePlaybook,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name='Playbook'
    )
    version = models.CharField(max_length=50, verbose_name='版本号')
    content = models.TextField(verbose_name='内容快照')
    checksum = models.CharField(max_length=64, verbose_name='内容校验和')
    changelog = models.TextField(blank=True, verbose_name='变更说明')
    is_release = models.BooleanField(default=False, verbose_name='是否为发布版本')
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'ansible_playbook_version'
        verbose_name = 'Playbook版本'
        verbose_name_plural = 'Playbook版本历史'
        ordering = ['-created_at']
        unique_together = ['playbook', 'version']

    def __str__(self):
        return f"{self.playbook.name} v{self.version}"


class AnsibleHost(models.Model):
    """Ansible主机管理"""
    STATUS_CHOICES = [
        ('active', '活跃'),
        ('inactive', '非活跃'),
        ('failed', '连接失败'),
        ('unknown', '未知'),
    ]

    hostname = models.CharField(max_length=255, verbose_name='主机名')
    ip_address = models.GenericIPAddressField(verbose_name='IP地址')
    port = models.IntegerField(default=22, verbose_name='SSH端口')
    username = models.CharField(max_length=100, verbose_name='用户名')
    
    # 主机组和标签
    groups = models.ManyToManyField(
        'AnsibleHostGroup',
        through='AnsibleHostGroupMembership',
        verbose_name='主机组'
    )
    tags = models.JSONField(default=dict, verbose_name='主机标签')
    
    # 连接配置
    connection_type = models.CharField(
        max_length=20,
        default='ssh',
        verbose_name='连接类型'
    )
    become_method = models.CharField(
        max_length=20,
        default='sudo',
        blank=True,
        verbose_name='提权方式'
    )
    
    # 状态信息
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unknown',
        verbose_name='状态'
    )
    last_check = models.DateTimeField(null=True, blank=True, verbose_name='最后检查时间')
    check_message = models.TextField(blank=True, verbose_name='检查信息')
    
    # 系统信息
    os_family = models.CharField(max_length=50, blank=True, verbose_name='操作系统家族')
    os_distribution = models.CharField(max_length=100, blank=True, verbose_name='操作系统发行版')
    os_version = models.CharField(max_length=50, blank=True, verbose_name='操作系统版本')
    ansible_facts = models.JSONField(default=dict, verbose_name='Ansible Facts')
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'ansible_host'
        verbose_name = 'Ansible主机'
        verbose_name_plural = 'Ansible主机'
        ordering = ['hostname']
        unique_together = ['hostname', 'ip_address']

    def __str__(self):
        return f"{self.hostname} ({self.ip_address})"


class AnsibleHostGroup(models.Model):
    """Ansible主机组"""
    name = models.CharField(max_length=100, unique=True, verbose_name='组名')
    description = models.TextField(blank=True, verbose_name='描述')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='父组'
    )
    variables = models.JSONField(default=dict, verbose_name='组变量')
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'ansible_host_group'
        verbose_name = 'Ansible主机组'
        verbose_name_plural = 'Ansible主机组'
        ordering = ['name']

    def __str__(self):
        return self.name


class AnsibleHostGroupMembership(models.Model):
    """主机和主机组的关联关系"""
    host = models.ForeignKey(
        AnsibleHost,
        on_delete=models.CASCADE,
        verbose_name='主机'
    )
    group = models.ForeignKey(
        AnsibleHostGroup,
        on_delete=models.CASCADE,
        verbose_name='主机组'
    )
    variables = models.JSONField(default=dict, verbose_name='主机变量')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'ansible_host_group_membership'
        verbose_name = '主机组成员关系'
        verbose_name_plural = '主机组成员关系'
        unique_together = ['host', 'group']

    def __str__(self):
        return f"{self.host.hostname} -> {self.group.name}"
