"""
Kubernetes 集成视图
"""
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone

from .models import (
    KubernetesCluster, KubernetesNamespace, KubernetesDeployment,
    KubernetesService, KubernetesPod, KubernetesConfigMap,
    KubernetesSecret
)
from .serializers import (
    KubernetesClusterSerializer, KubernetesClusterListSerializer,
    KubernetesNamespaceSerializer, KubernetesNamespaceListSerializer,
    KubernetesDeploymentSerializer, KubernetesDeploymentListSerializer,
    KubernetesServiceSerializer, KubernetesPodSerializer,
    KubernetesConfigMapSerializer, KubernetesSecretSerializer
)
from .tasks import (
    check_cluster_status, sync_cluster_resources, deploy_application,
    scale_deployment, delete_resource
)


class KubernetesClusterViewSet(viewsets.ModelViewSet):
    """Kubernetes 集群管理视图集"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取当前用户可访问的集群"""
        return KubernetesCluster.objects.all().order_by('-created_at')
    
    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == 'list':
            return KubernetesClusterListSerializer
        return KubernetesClusterSerializer
    
    def perform_create(self, serializer):
        """创建集群时设置创建者"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def check_connection(self, request, pk=None):
        """检查集群连接状态"""
        cluster = self.get_object()
        
        # 启动异步任务检查集群状态
        task = check_cluster_status.delay(cluster.id)
        
        return Response({
            'message': '集群连接检查已启动',
            'task_id': task.id,
            'cluster_id': cluster.id
        })
    
    @action(detail=True, methods=['post'])
    def sync_resources(self, request, pk=None):
        """同步集群资源"""
        cluster = self.get_object()
        
        # 启动异步任务同步资源
        task = sync_cluster_resources.delay(cluster.id)
        
        return Response({
            'message': '集群资源同步已启动',
            'task_id': task.id,
            'cluster_id': cluster.id
        })
    
    @action(detail=True, methods=['get'])
    def namespaces(self, request, pk=None):
        """获取集群下的命名空间"""
        cluster = self.get_object()
        namespaces = cluster.namespaces.all()
        serializer = KubernetesNamespaceListSerializer(namespaces, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def overview(self, request, pk=None):
        """获取集群概览信息"""
        cluster = self.get_object()
        
        # 统计各种资源数量
        namespaces_count = cluster.namespaces.count()
        deployments_count = KubernetesDeployment.objects.filter(
            namespace__cluster=cluster
        ).count()
        services_count = KubernetesService.objects.filter(
            namespace__cluster=cluster
        ).count()
        pods_count = KubernetesPod.objects.filter(
            namespace__cluster=cluster
        ).count()
        
        return Response({
            'cluster': KubernetesClusterSerializer(cluster).data,
            'statistics': {
                'namespaces': namespaces_count,
                'deployments': deployments_count,
                'services': services_count,
                'pods': pods_count,
                'last_sync': cluster.last_check,
            }
        })


class KubernetesNamespaceViewSet(viewsets.ModelViewSet):
    """Kubernetes 命名空间管理视图集"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取命名空间列表"""
        queryset = KubernetesNamespace.objects.select_related('cluster')
        
        # 按集群过滤
        cluster_id = self.request.query_params.get('cluster_id')
        if cluster_id:
            queryset = queryset.filter(cluster_id=cluster_id)
        
        return queryset.order_by('cluster__name', 'name')
    
    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == 'list':
            return KubernetesNamespaceListSerializer
        return KubernetesNamespaceSerializer
    
    @action(detail=True, methods=['get'])
    def resources(self, request, pk=None):
        """获取命名空间下的资源"""
        namespace = self.get_object()
        
        deployments = namespace.deployments.all()
        services = namespace.services.all()
        pods = namespace.pods.all()
        configmaps = namespace.configmaps.all()
        secrets = namespace.secrets.all()
        
        return Response({
            'namespace': KubernetesNamespaceSerializer(namespace).data,
            'deployments': KubernetesDeploymentListSerializer(deployments, many=True).data,
            'services': KubernetesServiceSerializer(services, many=True).data,
            'pods': KubernetesPodSerializer(pods, many=True).data,
            'configmaps': KubernetesConfigMapSerializer(configmaps, many=True).data,
            'secrets': KubernetesSecretSerializer(secrets, many=True).data,
        })


class KubernetesDeploymentViewSet(viewsets.ModelViewSet):
    """Kubernetes 部署管理视图集"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取部署列表"""
        queryset = KubernetesDeployment.objects.select_related(
            'namespace', 'namespace__cluster', 'created_by'
        )
        
        # 按集群过滤
        cluster_id = self.request.query_params.get('cluster_id')
        if cluster_id:
            queryset = queryset.filter(namespace__cluster_id=cluster_id)
        
        # 按命名空间过滤
        namespace_id = self.request.query_params.get('namespace_id')
        if namespace_id:
            queryset = queryset.filter(namespace_id=namespace_id)
        
        # 按状态过滤
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == 'list':
            return KubernetesDeploymentListSerializer
        return KubernetesDeploymentSerializer
    
    @action(detail=True, methods=['post'])
    def deploy(self, request, pk=None):
        """部署应用"""
        deployment = self.get_object()
        
        # 启动异步任务部署应用
        task = deploy_application.delay(deployment.id)
        
        return Response({
            'message': '应用部署已启动',
            'task_id': task.id,
            'deployment_id': deployment.id
        })
    
    @action(detail=True, methods=['post'])
    def scale(self, request, pk=None):
        """扩缩容部署"""
        deployment = self.get_object()
        replicas = request.data.get('replicas')
        
        if not replicas or not isinstance(replicas, int) or replicas < 0:
            return Response({
                'error': '副本数必须是非负整数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 启动异步任务扩缩容
        task = scale_deployment.delay(deployment.id, replicas)
        
        return Response({
            'message': f'部署扩缩容到 {replicas} 个副本已启动',
            'task_id': task.id,
            'deployment_id': deployment.id,
            'replicas': replicas
        })
    
    @action(detail=True, methods=['get'])
    def pods(self, request, pk=None):
        """获取部署相关的 Pod"""
        deployment = self.get_object()
        
        # 通过标签选择器找到相关的 Pod
        pods = KubernetesPod.objects.filter(
            namespace=deployment.namespace,
            labels__icontains=deployment.name  # 简化的标签匹配
        )
        
        serializer = KubernetesPodSerializer(pods, many=True)
        return Response(serializer.data)


class KubernetesServiceViewSet(viewsets.ModelViewSet):
    """Kubernetes 服务管理视图集"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取服务列表"""
        queryset = KubernetesService.objects.select_related(
            'namespace', 'namespace__cluster', 'created_by'
        )
        
        # 按集群过滤
        cluster_id = self.request.query_params.get('cluster_id')
        if cluster_id:
            queryset = queryset.filter(namespace__cluster_id=cluster_id)
        
        # 按命名空间过滤
        namespace_id = self.request.query_params.get('namespace_id')
        if namespace_id:
            queryset = queryset.filter(namespace_id=namespace_id)
        
        # 按服务类型过滤
        service_type = self.request.query_params.get('service_type')
        if service_type:
            queryset = queryset.filter(service_type=service_type)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """根据动作选择序列化器"""
        return KubernetesServiceSerializer


class KubernetesPodViewSet(viewsets.ModelViewSet):
    """Kubernetes Pod 管理视图集"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取 Pod 列表"""
        queryset = KubernetesPod.objects.select_related(
            'namespace', 'namespace__cluster'
        )
        
        # 按集群过滤
        cluster_id = self.request.query_params.get('cluster_id')
        if cluster_id:
            queryset = queryset.filter(namespace__cluster_id=cluster_id)
        
        # 按命名空间过滤
        namespace_id = self.request.query_params.get('namespace_id')
        if namespace_id:
            queryset = queryset.filter(namespace_id=namespace_id)
        
        # 按状态过滤
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 按阶段过滤
        phase = self.request.query_params.get('phase')
        if phase:
            queryset = queryset.filter(phase=phase)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """根据动作选择序列化器"""
        return KubernetesPodSerializer
    
    @action(detail=True, methods=['delete'])
    def force_delete(self, request, pk=None):
        """强制删除 Pod"""
        pod = self.get_object()
        
        # 启动异步任务删除 Pod
        task = delete_resource.delay('pod', pod.id)
        
        return Response({
            'message': 'Pod 强制删除已启动',
            'task_id': task.id,
            'pod_id': pod.id
        })
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """获取 Pod 日志（模拟）"""
        pod = self.get_object()
        
        # 这里应该调用 Kubernetes API 获取实际日志
        # 暂时返回模拟数据
        return Response({
            'pod_name': pod.name,
            'namespace': pod.namespace.name,
            'logs': f'模拟日志内容 for {pod.name}\n2024-01-01 12:00:00 应用启动\n2024-01-01 12:00:01 服务就绪'
        })


class KubernetesConfigMapViewSet(viewsets.ModelViewSet):
    """Kubernetes ConfigMap 管理视图集"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取 ConfigMap 列表"""
        queryset = KubernetesConfigMap.objects.select_related(
            'namespace', 'namespace__cluster', 'created_by'
        )
        
        # 按集群过滤
        cluster_id = self.request.query_params.get('cluster_id')
        if cluster_id:
            queryset = queryset.filter(namespace__cluster_id=cluster_id)
        
        # 按命名空间过滤
        namespace_id = self.request.query_params.get('namespace_id')
        if namespace_id:
            queryset = queryset.filter(namespace_id=namespace_id)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """根据动作选择序列化器"""
        return KubernetesConfigMapSerializer


class KubernetesSecretViewSet(viewsets.ModelViewSet):
    """Kubernetes Secret 管理视图集"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取 Secret 列表"""
        queryset = KubernetesSecret.objects.select_related(
            'namespace', 'namespace__cluster', 'created_by'
        )
        
        # 按集群过滤
        cluster_id = self.request.query_params.get('cluster_id')
        if cluster_id:
            queryset = queryset.filter(namespace__cluster_id=cluster_id)
        
        # 按命名空间过滤
        namespace_id = self.request.query_params.get('namespace_id')
        if namespace_id:
            queryset = queryset.filter(namespace_id=namespace_id)
        
        # 按类型过滤
        secret_type = self.request.query_params.get('secret_type')
        if secret_type:
            queryset = queryset.filter(secret_type=secret_type)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """根据动作选择序列化器"""
        return KubernetesSecretSerializer
