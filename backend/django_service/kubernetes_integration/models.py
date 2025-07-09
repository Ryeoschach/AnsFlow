from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.utils import timezone
import json


class KubernetesCluster(models.Model):
    """Kubernetes 集群管理"""
    
    CLUSTER_STATUS_CHOICES = [
        ('active', '活跃'),
        ('inactive', '不活跃'),
        ('error', '错误'),
        ('connecting', '连接中'),
    ]
    
    CLUSTER_TYPE_CHOICES = [
        ('k8s', '标准 Kubernetes'),
        ('eks', 'Amazon EKS'),
        ('gke', 'Google GKE'),
        ('aks', 'Azure AKS'),
        ('rke', 'Rancher RKE'),
        ('k3s', 'K3s'),
        ('minikube', 'Minikube'),
        ('kind', 'Kind'),
    ]
    
    name = models.CharField(max_length=100, unique=True, verbose_name='集群名称')
    description = models.TextField(blank=True, verbose_name='描述')
    cluster_type = models.CharField(
        max_length=20, 
        choices=CLUSTER_TYPE_CHOICES, 
        default='k8s',
        verbose_name='集群类型'
    )
    
    # 连接配置
    api_server = models.URLField(verbose_name='API Server URL')
    auth_config = models.JSONField(default=dict, verbose_name='认证配置')  # 存储所有认证信息
    
    # 集群信息
    kubernetes_version = models.CharField(max_length=50, blank=True, verbose_name='K8s 版本')
    default_namespace = models.CharField(max_length=100, default='default', verbose_name='默认命名空间')
    
    # 状态和监控
    status = models.CharField(
        max_length=20, 
        choices=CLUSTER_STATUS_CHOICES, 
        default='inactive',
        verbose_name='集群状态'
    )
    last_check = models.DateTimeField(null=True, blank=True, verbose_name='最后检查时间')
    check_message = models.TextField(blank=True, verbose_name='检查信息')
    
    # 统计信息
    total_nodes = models.IntegerField(default=0, verbose_name='节点总数')
    ready_nodes = models.IntegerField(default=0, verbose_name='就绪节点数')
    total_pods = models.IntegerField(default=0, verbose_name='Pod 总数')
    running_pods = models.IntegerField(default=0, verbose_name='运行中 Pod 数')
    
    # 管理信息
    is_default = models.BooleanField(default=False, verbose_name='默认集群')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = 'Kubernetes 集群'
        verbose_name_plural = 'Kubernetes 集群'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # 确保只有一个默认集群
        if self.is_default:
            KubernetesCluster.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class KubernetesNamespace(models.Model):
    """Kubernetes 命名空间"""
    
    NAMESPACE_STATUS_CHOICES = [
        ('active', '活跃'),
        ('terminating', '终止中'),
    ]
    
    cluster = models.ForeignKey(
        KubernetesCluster, 
        on_delete=models.CASCADE, 
        related_name='namespaces',
        verbose_name='所属集群'
    )
    name = models.CharField(max_length=100, verbose_name='命名空间名称')
    status = models.CharField(
        max_length=20, 
        choices=NAMESPACE_STATUS_CHOICES,
        default='active',
        verbose_name='状态'
    )
    
    # 资源配额
    cpu_limit = models.CharField(max_length=50, blank=True, verbose_name='CPU 限制')
    memory_limit = models.CharField(max_length=50, blank=True, verbose_name='内存限制')
    storage_limit = models.CharField(max_length=50, blank=True, verbose_name='存储限制')
    
    # 标签和注解
    labels = models.JSONField(default=dict, verbose_name='标签')
    annotations = models.JSONField(default=dict, verbose_name='注解')
    
    # 统计信息
    pod_count = models.IntegerField(default=0, verbose_name='Pod 数量')
    service_count = models.IntegerField(default=0, verbose_name='Service 数量')
    deployment_count = models.IntegerField(default=0, verbose_name='Deployment 数量')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = 'Kubernetes 命名空间'
        verbose_name_plural = 'Kubernetes 命名空间'
        unique_together = ['cluster', 'name']
        ordering = ['cluster', 'name']
    
    def __str__(self):
        return f"{self.cluster.name}/{self.name}"


class KubernetesDeployment(models.Model):
    """Kubernetes 部署"""
    
    DEPLOYMENT_STATUS_CHOICES = [
        ('progressing', '部署中'),
        ('available', '可用'),
        ('replicafailure', '副本失败'),
        ('unknown', '未知'),
    ]
    
    cluster = models.ForeignKey(
        KubernetesCluster, 
        on_delete=models.CASCADE, 
        related_name='deployments',
        verbose_name='所属集群'
    )
    namespace = models.ForeignKey(
        KubernetesNamespace,
        on_delete=models.CASCADE,
        related_name='deployments',
        verbose_name='命名空间'
    )
    
    name = models.CharField(max_length=100, verbose_name='部署名称')
    status = models.CharField(
        max_length=20,
        choices=DEPLOYMENT_STATUS_CHOICES,
        default='unknown',
        verbose_name='部署状态'
    )
    
    # 镜像信息
    image = models.CharField(max_length=500, verbose_name='容器镜像')
    image_pull_policy = models.CharField(
        max_length=20,
        choices=[
            ('Always', '总是拉取'),
            ('IfNotPresent', '如果不存在则拉取'),
            ('Never', '从不拉取'),
        ],
        default='IfNotPresent',
        verbose_name='镜像拉取策略'
    )
    
    # 副本配置
    replicas = models.IntegerField(default=1, verbose_name='期望副本数')
    ready_replicas = models.IntegerField(default=0, verbose_name='就绪副本数')
    available_replicas = models.IntegerField(default=0, verbose_name='可用副本数')
    
    # 资源配置
    cpu_request = models.CharField(max_length=50, blank=True, verbose_name='CPU 请求')
    cpu_limit = models.CharField(max_length=50, blank=True, verbose_name='CPU 限制')
    memory_request = models.CharField(max_length=50, blank=True, verbose_name='内存请求')
    memory_limit = models.CharField(max_length=50, blank=True, verbose_name='内存限制')
    
    # 环境变量和配置
    environment_vars = models.JSONField(default=dict, verbose_name='环境变量')
    config_maps = models.JSONField(default=list, verbose_name='ConfigMap 引用')
    secrets = models.JSONField(default=list, verbose_name='Secret 引用')
    
    # 端口配置
    ports = models.JSONField(default=list, verbose_name='端口配置')
    
    # 卷配置
    volumes = models.JSONField(default=list, verbose_name='卷配置')
    volume_mounts = models.JSONField(default=list, verbose_name='卷挂载')
    
    # 标签和选择器
    labels = models.JSONField(default=dict, verbose_name='标签')
    selector = models.JSONField(default=dict, verbose_name='选择器')
    
    # 部署策略
    strategy_type = models.CharField(
        max_length=20,
        choices=[
            ('RollingUpdate', '滚动更新'),
            ('Recreate', '重新创建'),
        ],
        default='RollingUpdate',
        verbose_name='部署策略'
    )
    max_surge = models.CharField(max_length=20, default='25%', verbose_name='最大激增')
    max_unavailable = models.CharField(max_length=20, default='25%', verbose_name='最大不可用')
    
    # 元数据
    description = models.TextField(blank=True, verbose_name='描述')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = 'Kubernetes 部署'
        verbose_name_plural = 'Kubernetes 部署'
        unique_together = ['cluster', 'namespace', 'name']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.cluster.name}/{self.namespace.name}/{self.name}"


class KubernetesService(models.Model):
    """Kubernetes 服务"""
    
    SERVICE_TYPE_CHOICES = [
        ('ClusterIP', '集群内部'),
        ('NodePort', '节点端口'),
        ('LoadBalancer', '负载均衡器'),
        ('ExternalName', '外部名称'),
    ]
    
    cluster = models.ForeignKey(
        KubernetesCluster, 
        on_delete=models.CASCADE, 
        related_name='services',
        verbose_name='所属集群'
    )
    namespace = models.ForeignKey(
        KubernetesNamespace,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name='命名空间'
    )
    
    name = models.CharField(max_length=100, verbose_name='服务名称')
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPE_CHOICES,
        default='ClusterIP',
        verbose_name='服务类型'
    )
    
    # 网络配置
    cluster_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='集群 IP')
    external_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='外部 IP')
    load_balancer_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='负载均衡器 IP')
    
    # 端口配置
    ports = models.JSONField(default=list, verbose_name='端口配置')
    
    # 选择器和标签
    selector = models.JSONField(default=dict, verbose_name='选择器')
    labels = models.JSONField(default=dict, verbose_name='标签')
    
    # 会话亲和性
    session_affinity = models.CharField(
        max_length=20,
        choices=[
            ('None', '无'),
            ('ClientIP', '客户端 IP'),
        ],
        default='None',
        verbose_name='会话亲和性'
    )
    
    # 元数据
    description = models.TextField(blank=True, verbose_name='描述')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = 'Kubernetes 服务'
        verbose_name_plural = 'Kubernetes 服务'
        unique_together = ['cluster', 'namespace', 'name']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.cluster.name}/{self.namespace.name}/{self.name}"


class KubernetesPod(models.Model):
    """Kubernetes Pod"""
    
    POD_PHASE_CHOICES = [
        ('Pending', '等待中'),
        ('Running', '运行中'),
        ('Succeeded', '已成功'),
        ('Failed', '已失败'),
        ('Unknown', '未知'),
    ]
    
    cluster = models.ForeignKey(
        KubernetesCluster, 
        on_delete=models.CASCADE, 
        related_name='pods',
        verbose_name='所属集群'
    )
    namespace = models.ForeignKey(
        KubernetesNamespace,
        on_delete=models.CASCADE,
        related_name='pods',
        verbose_name='命名空间'
    )
    deployment = models.ForeignKey(
        KubernetesDeployment,
        on_delete=models.CASCADE,
        related_name='pods',
        null=True,
        blank=True,
        verbose_name='所属部署'
    )
    
    name = models.CharField(max_length=100, verbose_name='Pod 名称')
    phase = models.CharField(
        max_length=20,
        choices=POD_PHASE_CHOICES,
        default='Pending',
        verbose_name='Pod 阶段'
    )
    
    # 节点信息
    node_name = models.CharField(max_length=100, blank=True, verbose_name='节点名称')
    pod_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='Pod IP')
    host_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='主机 IP')
    
    # 容器信息
    containers = models.JSONField(default=list, verbose_name='容器信息')
    restart_count = models.IntegerField(default=0, verbose_name='重启次数')
    
    # 资源使用
    cpu_usage = models.FloatField(null=True, blank=True, verbose_name='CPU 使用率')
    memory_usage = models.BigIntegerField(null=True, blank=True, verbose_name='内存使用 (字节)')
    
    # 状态信息
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='启动时间')
    ready = models.BooleanField(default=False, verbose_name='就绪状态')
    
    # 标签和注解
    labels = models.JSONField(default=dict, verbose_name='标签')
    annotations = models.JSONField(default=dict, verbose_name='注解')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = 'Kubernetes Pod'
        verbose_name_plural = 'Kubernetes Pod'
        unique_together = ['cluster', 'namespace', 'name']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.cluster.name}/{self.namespace.name}/{self.name}"


class KubernetesConfigMap(models.Model):
    """Kubernetes ConfigMap"""
    
    cluster = models.ForeignKey(
        KubernetesCluster, 
        on_delete=models.CASCADE, 
        related_name='configmaps',
        verbose_name='所属集群'
    )
    namespace = models.ForeignKey(
        KubernetesNamespace,
        on_delete=models.CASCADE,
        related_name='configmaps',
        verbose_name='命名空间'
    )
    
    name = models.CharField(max_length=100, verbose_name='ConfigMap 名称')
    data = models.JSONField(default=dict, verbose_name='配置数据')
    binary_data = models.JSONField(default=dict, verbose_name='二进制数据')
    
    # 标签和注解
    labels = models.JSONField(default=dict, verbose_name='标签')
    annotations = models.JSONField(default=dict, verbose_name='注解')
    
    # 元数据
    description = models.TextField(blank=True, verbose_name='描述')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = 'Kubernetes ConfigMap'
        verbose_name_plural = 'Kubernetes ConfigMap'
        unique_together = ['cluster', 'namespace', 'name']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.cluster.name}/{self.namespace.name}/{self.name}"


class KubernetesSecret(models.Model):
    """Kubernetes Secret"""
    
    SECRET_TYPE_CHOICES = [
        ('Opaque', '不透明'),
        ('kubernetes.io/service-account-token', '服务账户令牌'),
        ('kubernetes.io/dockercfg', 'Docker 配置'),
        ('kubernetes.io/dockerconfigjson', 'Docker 配置 JSON'),
        ('kubernetes.io/basic-auth', '基础认证'),
        ('kubernetes.io/ssh-auth', 'SSH 认证'),
        ('kubernetes.io/tls', 'TLS'),
    ]
    
    cluster = models.ForeignKey(
        KubernetesCluster, 
        on_delete=models.CASCADE, 
        related_name='secrets',
        verbose_name='所属集群'
    )
    namespace = models.ForeignKey(
        KubernetesNamespace,
        on_delete=models.CASCADE,
        related_name='secrets',
        verbose_name='命名空间'
    )
    
    name = models.CharField(max_length=100, verbose_name='Secret 名称')
    secret_type = models.CharField(
        max_length=50,
        choices=SECRET_TYPE_CHOICES,
        default='Opaque',
        verbose_name='Secret 类型'
    )
    
    # 加密存储的数据
    data = models.JSONField(default=dict, verbose_name='Secret 数据')
    
    # 标签和注解
    labels = models.JSONField(default=dict, verbose_name='标签')
    annotations = models.JSONField(default=dict, verbose_name='注解')
    
    # 元数据
    description = models.TextField(blank=True, verbose_name='描述')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = 'Kubernetes Secret'
        verbose_name_plural = 'Kubernetes Secret'
        unique_together = ['cluster', 'namespace', 'name']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.cluster.name}/{self.namespace.name}/{self.name}"
    
    def get_data(self):
        """获取解密后的数据"""
        try:
            return json.loads(self.data)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_data(self, data_dict):
        """设置加密数据"""
        self.data = json.dumps(data_dict)
