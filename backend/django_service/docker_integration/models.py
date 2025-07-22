"""
Docker集成数据模型
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import hashlib


class DockerRegistry(models.Model):
    """Docker镜像仓库"""
    REGISTRY_TYPE_CHOICES = [
        ('dockerhub', 'Docker Hub'),
        ('private', '私有仓库'),
        ('harbor', 'Harbor'),
        ('ecr', 'AWS ECR'),
        ('gcr', 'Google GCR'),
        ('acr', 'Azure ACR'),
    ]
    
    STATUS_CHOICES = [
        ('active', '活跃'),
        ('inactive', '非活跃'),
        ('error', '错误'),
    ]

    name = models.CharField(max_length=100, unique=True, verbose_name='仓库名称')
    url = models.URLField(verbose_name='仓库地址')
    registry_type = models.CharField(
        max_length=20,
        choices=REGISTRY_TYPE_CHOICES,
        default='dockerhub',
        verbose_name='仓库类型'
    )
    username = models.CharField(max_length=100, blank=True, verbose_name='用户名')
    description = models.TextField(blank=True, verbose_name='描述')
    
    # Harbor/私有仓库项目名称配置
    project_name = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='项目名称',
        help_text='Harbor等私有仓库的项目名称，如果为空则直接使用镜像名'
    )
    
    # 加密存储的认证信息
    auth_config = models.JSONField(default=dict, verbose_name='认证配置')
    
    # 状态信息
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='状态'
    )
    last_check = models.DateTimeField(null=True, blank=True, verbose_name='最后检查时间')
    check_message = models.TextField(blank=True, verbose_name='检查信息')
    
    # 元数据
    is_default = models.BooleanField(default=False, verbose_name='默认仓库')
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'docker_registry'
        verbose_name = 'Docker仓库'
        verbose_name_plural = 'Docker仓库'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.registry_type})"


class DockerImage(models.Model):
    """Docker镜像管理"""
    BUILD_STATUS_CHOICES = [
        ('pending', '待构建'),
        ('building', '构建中'),
        ('success', '构建成功'),
        ('failed', '构建失败'),
        ('cancelled', '已取消'),
    ]

    name = models.CharField(max_length=200, verbose_name='镜像名称')
    tag = models.CharField(max_length=100, default='latest', verbose_name='镜像标签')
    registry = models.ForeignKey(
        DockerRegistry,
        on_delete=models.CASCADE,
        verbose_name='镜像仓库'
    )
    
    # 构建配置
    dockerfile_content = models.TextField(verbose_name='Dockerfile内容')
    build_context = models.CharField(max_length=500, default='.', verbose_name='构建上下文')
    build_args = models.JSONField(default=dict, verbose_name='构建参数')
    
    # 镜像信息
    image_size = models.BigIntegerField(null=True, blank=True, verbose_name='镜像大小(字节)')
    image_id = models.CharField(max_length=100, blank=True, verbose_name='镜像ID')  # 增加长度以支持完整SHA256
    image_digest = models.CharField(max_length=100, blank=True, verbose_name='镜像摘要')
    
    # 构建状态
    build_status = models.CharField(
        max_length=20,
        choices=BUILD_STATUS_CHOICES,
        default='pending',
        verbose_name='构建状态'
    )
    build_logs = models.TextField(blank=True, verbose_name='构建日志')
    build_started_at = models.DateTimeField(null=True, blank=True, verbose_name='构建开始时间')
    build_completed_at = models.DateTimeField(null=True, blank=True, verbose_name='构建完成时间')
    build_duration = models.IntegerField(null=True, blank=True, verbose_name='构建耗时(秒)')
    
    # 推送状态
    is_pushed = models.BooleanField(default=False, verbose_name='是否已推送')
    pushed_at = models.DateTimeField(null=True, blank=True, verbose_name='推送时间')
    
    # 元数据
    description = models.TextField(blank=True, verbose_name='描述')
    labels = models.JSONField(default=dict, verbose_name='标签')
    is_template = models.BooleanField(default=False, verbose_name='是否为模板')
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'docker_image'
        verbose_name = 'Docker镜像'
        verbose_name_plural = 'Docker镜像'
        ordering = ['-created_at']
        unique_together = ['name', 'tag', 'registry']

    def __str__(self):
        return f"{self.registry.name}/{self.name}:{self.tag}"

    @property
    def full_name(self):
        """完整的镜像名称"""
        if self.registry.registry_type == 'dockerhub':
            return f"{self.name}:{self.tag}"
        return f"{self.registry.url.replace('https://', '').replace('http://', '')}/{self.name}:{self.tag}"


class DockerImageVersion(models.Model):
    """Docker镜像版本历史"""
    image = models.ForeignKey(
        DockerImage,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name='镜像'
    )
    version = models.CharField(max_length=50, verbose_name='版本号')
    dockerfile_content = models.TextField(verbose_name='Dockerfile内容快照')
    build_context = models.CharField(max_length=500, verbose_name='构建上下文')
    build_args = models.JSONField(default=dict, verbose_name='构建参数')
    checksum = models.CharField(max_length=64, verbose_name='内容校验和')
    changelog = models.TextField(blank=True, verbose_name='变更说明')
    
    # 构建信息
    docker_image_id = models.CharField(max_length=100, blank=True, verbose_name='镜像ID')  # 增加长度以支持完整SHA256
    size = models.BigIntegerField(null=True, blank=True, verbose_name='镜像大小')
    is_release = models.BooleanField(default=False, verbose_name='是否为发布版本')
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'docker_image_version'
        verbose_name = 'Docker镜像版本'
        verbose_name_plural = 'Docker镜像版本历史'
        ordering = ['-created_at']
        unique_together = ['image', 'version']

    def __str__(self):
        return f"{self.image.name} v{self.version}"

    def save(self, *args, **kwargs):
        if not self.checksum:
            content = f"{self.dockerfile_content}{self.build_context}{str(self.build_args)}"
            self.checksum = hashlib.sha256(content.encode()).hexdigest()
        super().save(*args, **kwargs)


class DockerContainer(models.Model):
    """Docker容器管理"""
    STATUS_CHOICES = [
        ('created', '已创建'),
        ('running', '运行中'),
        ('paused', '已暂停'),
        ('restarting', '重启中'),
        ('removing', '删除中'),
        ('stopped', '已停止'),
        ('exited', '已退出'),
        ('dead', '已死亡'),
    ]

    name = models.CharField(max_length=100, unique=True, verbose_name='容器名称')
    image = models.ForeignKey(
        DockerImage,
        on_delete=models.CASCADE,
        verbose_name='镜像'
    )
    container_id = models.CharField(max_length=100, blank=True, verbose_name='容器ID')  # 增加长度以支持完整SHA256
    
    # 容器配置
    command = models.TextField(blank=True, verbose_name='启动命令')
    working_dir = models.CharField(max_length=255, blank=True, verbose_name='工作目录')
    environment_vars = models.JSONField(default=dict, verbose_name='环境变量')
    port_mappings = models.JSONField(default=list, verbose_name='端口映射')
    volumes = models.JSONField(default=list, verbose_name='数据卷')
    network_mode = models.CharField(max_length=50, default='bridge', verbose_name='网络模式')
    
    # 资源限制
    memory_limit = models.CharField(max_length=20, blank=True, verbose_name='内存限制')
    cpu_limit = models.CharField(max_length=20, blank=True, verbose_name='CPU限制')
    
    # 运行状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='created',
        verbose_name='状态'
    )
    exit_code = models.IntegerField(null=True, blank=True, verbose_name='退出代码')
    
    # 时间信息
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='启动时间')
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    
    # 元数据
    description = models.TextField(blank=True, verbose_name='描述')
    labels = models.JSONField(default=dict, verbose_name='标签')
    auto_remove = models.BooleanField(default=False, verbose_name='自动删除')
    restart_policy = models.CharField(max_length=20, default='no', verbose_name='重启策略')
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'docker_container'
        verbose_name = 'Docker容器'
        verbose_name_plural = 'Docker容器'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.status})"


class DockerContainerStats(models.Model):
    """Docker容器统计信息"""
    container = models.ForeignKey(
        DockerContainer,
        on_delete=models.CASCADE,
        related_name='stats',
        verbose_name='容器'
    )
    
    # CPU统计
    cpu_usage_percent = models.FloatField(verbose_name='CPU使用率(%)')
    cpu_system_usage = models.BigIntegerField(verbose_name='系统CPU使用')
    cpu_total_usage = models.BigIntegerField(verbose_name='总CPU使用')
    
    # 内存统计
    memory_usage = models.BigIntegerField(verbose_name='内存使用(字节)')
    memory_limit = models.BigIntegerField(verbose_name='内存限制(字节)')
    memory_percent = models.FloatField(verbose_name='内存使用率(%)')
    
    # 网络统计
    network_rx_bytes = models.BigIntegerField(default=0, verbose_name='网络接收字节')
    network_tx_bytes = models.BigIntegerField(default=0, verbose_name='网络发送字节')
    
    # 磁盘统计
    block_read_bytes = models.BigIntegerField(default=0, verbose_name='磁盘读取字节')
    block_write_bytes = models.BigIntegerField(default=0, verbose_name='磁盘写入字节')
    
    # 进程信息
    pids = models.IntegerField(default=0, verbose_name='进程数')
    
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')

    class Meta:
        db_table = 'docker_container_stats'
        verbose_name = 'Docker容器统计'
        verbose_name_plural = 'Docker容器统计'
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.container.name} @ {self.recorded_at}"


class DockerCompose(models.Model):
    """Docker Compose项目管理"""
    STATUS_CHOICES = [
        ('created', '已创建'),
        ('running', '运行中'),
        ('stopped', '已停止'),
        ('paused', '已暂停'),
        ('error', '错误'),
    ]

    name = models.CharField(max_length=100, unique=True, verbose_name='项目名称')
    compose_content = models.TextField(verbose_name='docker-compose.yml内容')
    working_directory = models.CharField(max_length=500, verbose_name='工作目录')
    environment_file = models.TextField(blank=True, verbose_name='.env文件内容')
    
    # 项目状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='created',
        verbose_name='状态'
    )
    
    # 服务信息
    services = models.JSONField(default=list, verbose_name='服务列表')
    networks = models.JSONField(default=list, verbose_name='网络列表')
    volumes = models.JSONField(default=list, verbose_name='数据卷列表')
    
    # 元数据
    description = models.TextField(blank=True, verbose_name='描述')
    labels = models.JSONField(default=dict, verbose_name='标签')
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'docker_compose'
        verbose_name = 'Docker Compose'
        verbose_name_plural = 'Docker Compose项目'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.status})"
