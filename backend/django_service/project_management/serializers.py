from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Project, ProjectMembership, Environment


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class ProjectMembershipSerializer(serializers.ModelSerializer):
    """Project membership serializer"""
    
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ProjectMembership
        fields = ['id', 'user', 'user_id', 'role', 'created_at']
        read_only_fields = ['id', 'created_at']


class EnvironmentSerializer(serializers.ModelSerializer):
    """Environment serializer"""
    
    class Meta:
        model = Environment
        fields = [
            'id', 'name', 'env_type', 'url', 'config',
            'auto_deploy', 'deploy_branch', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProjectSerializer(serializers.ModelSerializer):
    """Project serializer"""
    
    owner = UserSerializer(read_only=True)
    members = ProjectMembershipSerializer(source='projectmembership_set', many=True, read_only=True)
    environments = EnvironmentSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    pipeline_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'visibility',
            'repository_url', 'default_branch', 'is_active',
            'settings', 'owner', 'members', 'environments',
            'member_count', 'pipeline_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.members.count()
    
    def get_pipeline_count(self, obj):
        return obj.pipelines.count()
    
    def create(self, validated_data):
        # Set the owner to the current user
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight project serializer for list views"""
    
    owner = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    pipeline_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'visibility',
            'is_active', 'owner', 'member_count', 'pipeline_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.members.count()
    
    def get_pipeline_count(self, obj):
        return obj.pipelines.count()
