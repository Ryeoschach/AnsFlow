"""
Kubernetes 集成序列化器
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    KubernetesCluster, KubernetesNamespace, KubernetesDeployment,
    KubernetesService, KubernetesPod, KubernetesConfigMap,
    KubernetesSecret
)


class KubernetesClusterSerializer(serializers.ModelSerializer):
    """Kubernetes 集群序列化器"""
    
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = KubernetesCluster
        fields = [
            'id', 'name', 'description', 'cluster_type', 'api_server',
            'auth_config', 'kubernetes_version', 'default_namespace',
            'status', 'last_check', 'check_message', 'total_nodes',
            'ready_nodes', 'total_pods', 'running_pods', 'is_default',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'last_check', 'check_message', 'total_nodes',
            'ready_nodes', 'total_pods', 'running_pods', 'created_at', 
            'updated_at', 'created_by_name'
        ]

    def create(self, validated_data):
        """创建集群时设置创建者"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def validate_auth_config(self, value):
        """验证认证配置"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("认证配置必须是有效的 JSON 对象")
        return value


class KubernetesNamespaceSerializer(serializers.ModelSerializer):
    """Kubernetes 命名空间序列化器"""
    
    cluster_name = serializers.CharField(source='cluster.name', read_only=True)
    
    class Meta:
        model = KubernetesNamespace
        fields = [
            'id', 'cluster', 'cluster_name', 'name', 'status',
            'labels', 'annotations', 'resource_quota', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'cluster_name', 'created_at', 'updated_at']

    def validate_labels(self, value):
        """验证标签格式"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("标签必须是有效的 JSON 对象")
        return value

    def validate_annotations(self, value):
        """验证注解格式"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("注解必须是有效的 JSON 对象")
        return value


class KubernetesDeploymentSerializer(serializers.ModelSerializer):
    """Kubernetes 部署序列化器"""
    
    namespace_name = serializers.CharField(source='namespace.name', read_only=True)
    cluster_name = serializers.CharField(source='namespace.cluster.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = KubernetesDeployment
        fields = [
            'id', 'namespace', 'namespace_name', 'cluster_name', 'name',
            'image', 'replicas', 'status', 'ready_replicas', 'deployment_spec',
            'labels', 'annotations', 'description', 'created_by',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'namespace_name', 'cluster_name', 'status', 'ready_replicas',
            'created_at', 'updated_at', 'created_by_name'
        ]

    def create(self, validated_data):
        """创建部署时设置创建者"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def validate_deployment_spec(self, value):
        """验证部署规格"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("部署规格必须是有效的 JSON 对象")
        return value


class KubernetesServiceSerializer(serializers.ModelSerializer):
    """Kubernetes 服务序列化器"""
    
    namespace_name = serializers.CharField(source='namespace.name', read_only=True)
    cluster_name = serializers.CharField(source='namespace.cluster.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = KubernetesService
        fields = [
            'id', 'namespace', 'namespace_name', 'cluster_name', 'name',
            'service_type', 'selector', 'ports', 'cluster_ip', 'external_ip',
            'labels', 'annotations', 'description', 'created_by',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'namespace_name', 'cluster_name', 'cluster_ip', 'external_ip',
            'created_at', 'updated_at', 'created_by_name'
        ]

    def create(self, validated_data):
        """创建服务时设置创建者"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def validate_selector(self, value):
        """验证选择器"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("选择器必须是有效的 JSON 对象")
        return value

    def validate_ports(self, value):
        """验证端口配置"""
        if not isinstance(value, list):
            raise serializers.ValidationError("端口配置必须是有效的数组")
        return value


class KubernetesPodSerializer(serializers.ModelSerializer):
    """Kubernetes Pod 序列化器"""
    
    namespace_name = serializers.CharField(source='namespace.name', read_only=True)
    cluster_name = serializers.CharField(source='namespace.cluster.name', read_only=True)
    
    class Meta:
        model = KubernetesPod
        fields = [
            'id', 'namespace', 'namespace_name', 'cluster_name', 'name',
            'status', 'phase', 'node_name', 'pod_ip', 'containers',
            'labels', 'annotations', 'restart_count', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'namespace_name', 'cluster_name', 'status', 'phase',
            'node_name', 'pod_ip', 'restart_count', 'created_at', 'updated_at'
        ]

    def validate_containers(self, value):
        """验证容器配置"""
        if not isinstance(value, list):
            raise serializers.ValidationError("容器配置必须是有效的数组")
        return value


class KubernetesConfigMapSerializer(serializers.ModelSerializer):
    """Kubernetes ConfigMap 序列化器"""
    
    namespace_name = serializers.CharField(source='namespace.name', read_only=True)
    cluster_name = serializers.CharField(source='namespace.cluster.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = KubernetesConfigMap
        fields = [
            'id', 'namespace', 'namespace_name', 'cluster_name', 'name',
            'data', 'labels', 'annotations', 'description', 'created_by',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'namespace_name', 'cluster_name', 'created_at', 
            'updated_at', 'created_by_name'
        ]

    def create(self, validated_data):
        """创建 ConfigMap 时设置创建者"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def validate_data(self, value):
        """验证配置数据"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("配置数据必须是有效的 JSON 对象")
        return value


class KubernetesSecretSerializer(serializers.ModelSerializer):
    """Kubernetes Secret 序列化器"""
    
    namespace_name = serializers.CharField(source='namespace.name', read_only=True)
    cluster_name = serializers.CharField(source='namespace.cluster.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = KubernetesSecret
        fields = [
            'id', 'namespace', 'namespace_name', 'cluster_name', 'name',
            'secret_type', 'data', 'labels', 'annotations', 'description',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'namespace_name', 'cluster_name', 'created_at', 
            'updated_at', 'created_by_name'
        ]

    def create(self, validated_data):
        """创建 Secret 时设置创建者"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def validate_data(self, value):
        """验证 Secret 数据"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Secret 数据必须是有效的 JSON 对象")
        return value

    def to_representation(self, instance):
        """序列化时隐藏敏感数据"""
        data = super().to_representation(instance)
        # 在列表视图中隐藏敏感数据详情，只显示是否有数据
        if self.context.get('request') and self.context['request'].method == 'GET':
            if 'data' in data and isinstance(data['data'], dict):
                data['data_keys'] = list(data['data'].keys())
                data['has_data'] = bool(data['data'])
                data.pop('data', None)  # 移除实际数据
        return data


# 简化的序列化器用于列表视图
class KubernetesClusterListSerializer(serializers.ModelSerializer):
    """Kubernetes 集群列表序列化器"""
    
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = KubernetesCluster
        fields = [
            'id', 'name', 'cluster_type', 'status', 'kubernetes_version',
            'total_nodes', 'ready_nodes', 'total_pods', 'running_pods',
            'is_default', 'created_by_name', 'created_at'
        ]


class KubernetesNamespaceListSerializer(serializers.ModelSerializer):
    """Kubernetes 命名空间列表序列化器"""
    
    cluster_name = serializers.CharField(source='cluster.name', read_only=True)
    
    class Meta:
        model = KubernetesNamespace
        fields = [
            'id', 'cluster_name', 'name', 'status', 'created_at'
        ]


class KubernetesDeploymentListSerializer(serializers.ModelSerializer):
    """Kubernetes 部署列表序列化器"""
    
    namespace_name = serializers.CharField(source='namespace.name', read_only=True)
    cluster_name = serializers.CharField(source='namespace.cluster.name', read_only=True)
    
    class Meta:
        model = KubernetesDeployment
        fields = [
            'id', 'namespace_name', 'cluster_name', 'name', 'image',
            'replicas', 'ready_replicas', 'status', 'created_at'
        ]
