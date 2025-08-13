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
from .k8s_client import KubernetesManager


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
    
    @action(detail=False, methods=['post'])
    def validate_connection(self, request):
        """验证集群连接配置（创建前验证）"""
        from .k8s_client import KubernetesManager
        from .serializers import KubernetesClusterValidationSerializer
        
        serializer = KubernetesClusterValidationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': '参数验证失败', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 创建临时集群对象用于验证
        temp_cluster = type('TempCluster', (), {
            'api_server': serializer.validated_data['api_server'],
            'auth_config': serializer.validated_data['auth_config'],
            'name': serializer.validated_data.get('name', 'temp-cluster')
        })()
        
        try:
            # 使用临时集群对象测试连接
            k8s_manager = KubernetesManager(temp_cluster)
            cluster_info = k8s_manager.get_cluster_info()
            
            if cluster_info['connected']:
                return Response({
                    'valid': True,
                    'message': '集群连接验证成功',
                    'cluster_info': {
                        'version': cluster_info.get('version'),
                        'total_nodes': cluster_info.get('total_nodes'),
                        'ready_nodes': cluster_info.get('ready_nodes'),
                        'total_pods': cluster_info.get('total_pods'),
                        'running_pods': cluster_info.get('running_pods')
                    }
                })
            else:
                return Response({
                    'valid': False,
                    'message': cluster_info.get('message', '连接失败')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'valid': False,
                'message': f'连接验证失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
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
    
    @action(detail=True, methods=['get'])
    def cluster_info(self, request, pk=None):
        """获取集群实时统计信息"""
        cluster = self.get_object()
        
        try:
            # 使用KubernetesManager获取集群实时信息
            k8s_manager = KubernetesManager(cluster)
            cluster_info = k8s_manager.get_cluster_info()
            
            return Response({
                'cluster_id': cluster.id,
                'cluster_name': cluster.name,
                'connected': cluster_info['connected'],
                'message': cluster_info.get('message', ''),
                'cluster_stats': {
                    'version': cluster_info.get('version', ''),
                    'total_nodes': cluster_info.get('total_nodes', 0),
                    'ready_nodes': cluster_info.get('ready_nodes', 0),
                    'total_pods': cluster_info.get('total_pods', 0),
                    'running_pods': cluster_info.get('running_pods', 0),
                }
            })
            
        except Exception as e:
            return Response({
                'cluster_id': cluster.id,
                'cluster_name': cluster.name,
                'connected': False,
                'message': f'获取集群信息失败: {str(e)}',
                'cluster_stats': {
                    'version': '',
                    'total_nodes': 0,
                    'ready_nodes': 0,
                    'total_pods': 0,
                    'running_pods': 0,
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def token_status(self, request, pk=None):
        """获取集群 Token 状态"""
        from .token_manager import KubernetesTokenManager
        
        cluster = self.get_object()
        token_manager = KubernetesTokenManager(cluster)
        
        try:
            status_data = token_manager.get_token_status()
            return Response(status_data)
        except Exception as e:
            return Response({
                'error': f'获取 Token 状态失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def token_renewal_strategy(self, request, pk=None):
        """获取集群 Token 更新策略"""
        from .token_manager import KubernetesTokenManager
        
        cluster = self.get_object()
        token_manager = KubernetesTokenManager(cluster)
        
        try:
            strategy_data = token_manager.suggest_token_renewal_strategy()
            return Response(strategy_data)
        except Exception as e:
            return Response({
                'error': f'生成更新策略失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def validate_token(self, request, pk=None):
        """立即验证集群 Token"""
        from .token_manager import KubernetesTokenManager
        
        cluster = self.get_object()
        auth_config = cluster.auth_config or {}
        current_token = auth_config.get('token')
        
        if not current_token:
            return Response({
                'valid': False,
                'message': '集群未配置 Token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        token_manager = KubernetesTokenManager(cluster)
        
        try:
            is_valid, connection_info = token_manager.validate_token_connection(current_token)
            
            return Response({
                'valid': is_valid,
                'message': connection_info.get('message', '验证完成'),
                'cluster_info': {
                    'version': connection_info.get('cluster_version'),
                    'total_nodes': connection_info.get('total_nodes'),
                    'ready_nodes': connection_info.get('ready_nodes'),
                    'total_pods': connection_info.get('total_pods'),
                    'running_pods': connection_info.get('running_pods')
                } if is_valid else None
            })
        except Exception as e:
            return Response({
                'valid': False,
                'message': f'Token 验证失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
