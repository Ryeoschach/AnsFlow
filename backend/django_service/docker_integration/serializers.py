"""
Docker集成序列化器
"""
from rest_framework import serializers
from .models import (
    DockerRegistry, DockerImage, DockerImageVersion,
    DockerContainer, DockerContainerStats, DockerCompose
)


class DockerRegistrySerializer(serializers.ModelSerializer):
    """Docker仓库序列化器"""
    
    class Meta:
        model = DockerRegistry
        fields = [
            'id', 'name', 'url', 'registry_type', 'username', 'description',
            'status', 'last_check', 'check_message', 'is_default',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'last_check']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DockerImageVersionSerializer(serializers.ModelSerializer):
    """Docker镜像版本序列化器"""
    
    class Meta:
        model = DockerImageVersion
        fields = [
            'id', 'version', 'dockerfile_content', 'build_context', 'build_args',
            'checksum', 'changelog', 'docker_image_id', 'image_size', 'is_release',
            'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'checksum', 'created_by', 'created_at']


class DockerImageSerializer(serializers.ModelSerializer):
    """Docker镜像序列化器"""
    versions = DockerImageVersionSerializer(many=True, read_only=True)
    registry_name = serializers.CharField(source='registry.name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = DockerImage
        fields = [
            'id', 'name', 'tag', 'registry', 'registry_name', 'full_name',
            'dockerfile_content', 'build_context', 'build_args',
            'image_size', 'image_id', 'image_digest',
            'build_status', 'build_logs', 'build_started_at', 'build_completed_at', 'build_duration',
            'is_pushed', 'pushed_at', 'description', 'labels', 'is_template',
            'created_by', 'created_at', 'updated_at', 'versions'
        ]
        read_only_fields = [
            'id', 'full_name', 'registry_name', 'image_id', 'image_digest',
            'build_logs', 'build_started_at', 'build_completed_at', 'build_duration',
            'is_pushed', 'pushed_at', 'created_by', 'created_at', 'updated_at', 'versions'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DockerContainerStatsSerializer(serializers.ModelSerializer):
    """Docker容器统计序列化器"""
    
    class Meta:
        model = DockerContainerStats
        fields = [
            'id', 'cpu_usage_percent', 'cpu_system_usage', 'cpu_total_usage',
            'memory_usage', 'memory_limit', 'memory_percent',
            'network_rx_bytes', 'network_tx_bytes',
            'block_read_bytes', 'block_write_bytes', 'pids', 'recorded_at'
        ]
        read_only_fields = ['id', 'recorded_at']


class DockerContainerSerializer(serializers.ModelSerializer):
    """Docker容器序列化器"""
    stats = DockerContainerStatsSerializer(many=True, read_only=True)
    image_name = serializers.CharField(source='image.name', read_only=True)
    image_tag = serializers.CharField(source='image.tag', read_only=True)
    
    class Meta:
        model = DockerContainer
        fields = [
            'id', 'name', 'image', 'image_name', 'image_tag', 'container_id',
            'command', 'working_dir', 'environment_vars', 'port_mappings', 'volumes', 'network_mode',
            'memory_limit', 'cpu_limit', 'status', 'exit_code',
            'started_at', 'finished_at', 'description', 'labels',
            'auto_remove', 'restart_policy', 'created_by', 'created_at', 'updated_at', 'stats'
        ]
        read_only_fields = [
            'id', 'image_name', 'image_tag', 'container_id', 'status', 'exit_code',
            'started_at', 'finished_at', 'created_by', 'created_at', 'updated_at', 'stats'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DockerComposeSerializer(serializers.ModelSerializer):
    """Docker Compose序列化器"""
    
    class Meta:
        model = DockerCompose
        fields = [
            'id', 'name', 'compose_content', 'working_directory', 'environment_file',
            'status', 'services', 'networks', 'volumes', 'description', 'labels',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'services', 'networks', 'volumes',
            'created_by', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


# 简化的序列化器用于列表视图
class DockerRegistryListSerializer(serializers.ModelSerializer):
    """Docker仓库列表序列化器"""
    
    class Meta:
        model = DockerRegistry
        fields = ['id', 'name', 'url', 'registry_type', 'status', 'is_default']


class DockerImageListSerializer(serializers.ModelSerializer):
    """Docker镜像列表序列化器"""
    registry_name = serializers.CharField(source='registry.name', read_only=True)
    
    class Meta:
        model = DockerImage
        fields = [
            'id', 'name', 'tag', 'registry_name', 'build_status', 
            'image_size', 'is_template', 'created_at'
        ]


class DockerContainerListSerializer(serializers.ModelSerializer):
    """Docker容器列表序列化器"""
    image_name = serializers.CharField(source='image.name', read_only=True)
    
    class Meta:
        model = DockerContainer
        fields = [
            'id', 'name', 'image_name', 'status', 'started_at', 'created_at'
        ]


class DockerComposeListSerializer(serializers.ModelSerializer):
    """Docker Compose列表序列化器"""
    
    class Meta:
        model = DockerCompose
        fields = ['id', 'name', 'status', 'created_at']
