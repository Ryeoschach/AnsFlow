from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    AuditLog, SystemAlert, NotificationConfig, 
    GlobalConfig, UserProfile, BackupRecord,
    APIKey, APIEndpoint, SystemSetting, Team, 
    TeamMembership, BackupSchedule
)


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'is_active', 'is_staff', 'date_joined', 'last_login', 'profile']
        read_only_fields = ['date_joined', 'last_login']
    
    def get_profile(self, obj):
        try:
            profile = obj.profile
            return {
                'role': profile.role,
                'phone': profile.phone,
                'department': profile.department,
                'avatar': profile.avatar,
                'last_login_ip': profile.last_login_ip,
            }
        except UserProfile.DoesNotExist:
            return None


class UserCreateSerializer(serializers.ModelSerializer):
    """用户创建序列化器"""
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.CharField(required=False, default='viewer')
    phone = serializers.CharField(required=False, allow_blank=True)
    department = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 
                 'password', 'role', 'phone', 'department']
    
    def create(self, validated_data):
        # 提取profile相关字段
        profile_data = {
            'role': validated_data.pop('role', 'viewer'),
            'phone': validated_data.pop('phone', ''),
            'department': validated_data.pop('department', ''),
        }
        
        # 创建用户
        user = User.objects.create_user(**validated_data)
        
        # 创建用户档案
        UserProfile.objects.create(user=user, **profile_data)
        
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """用户档案序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'role', 'phone', 'department', 
                 'avatar', 'last_login_ip', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'last_login_ip']


class AuditLogSerializer(serializers.ModelSerializer):
    """审计日志序列化器"""
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'resource_type', 'resource_id', 
                 'details', 'ip_address', 'user_agent', 'result', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class SystemAlertSerializer(serializers.ModelSerializer):
    """系统告警序列化器"""
    
    class Meta:
        model = SystemAlert
        fields = ['id', 'type', 'message', 'severity', 'component', 
                 'resolved', 'created_at', 'resolved_at', 'resolved_by']
        read_only_fields = ['id', 'created_at', 'resolved_at']

    def update(self, instance, validated_data):
        # 如果设置为已解决，自动设置解决时间
        if validated_data.get('resolved') and not instance.resolved:
            from django.utils import timezone
            instance.resolved_at = timezone.now()
        return super().update(instance, validated_data)


class NotificationConfigSerializer(serializers.ModelSerializer):
    """通知配置序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = NotificationConfig
        fields = ['id', 'name', 'type', 'config', 'enabled', 
                 'created_by', 'created_by_username', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class GlobalConfigSerializer(serializers.ModelSerializer):
    """全局配置序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    display_value = serializers.SerializerMethodField()
    
    class Meta:
        model = GlobalConfig
        fields = ['id', 'key', 'value', 'display_value', 'type', 'description', 
                 'is_sensitive', 'created_by', 'created_by_username', 
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_display_value(self, obj):
        """为敏感信息返回掩码值"""
        if obj.is_sensitive:
            return "********"
        return obj.value
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class BackupRecordSerializer(serializers.ModelSerializer):
    """备份记录序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    file_size_human = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = BackupRecord
        fields = ['id', 'name', 'file_path', 'file_size', 'file_size_human',
                 'backup_type', 'status', 'created_by', 'created_by_username',
                 'created_at', 'completed_at', 'duration', 'error_message']
        read_only_fields = ['id', 'created_by', 'created_at', 'completed_at']
    
    def get_file_size_human(self, obj):
        """返回人性化的文件大小"""
        size = obj.file_size
        if size == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.2f} {units[unit_index]}"
    
    def get_duration(self, obj):
        """返回备份耗时"""
        if obj.completed_at and obj.created_at:
            duration = obj.completed_at - obj.created_at
            return str(duration)
        return None
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class SystemStatusSerializer(serializers.Serializer):
    """系统状态序列化器"""
    cpu_usage = serializers.FloatField()
    memory_usage = serializers.FloatField()
    disk_usage = serializers.FloatField()
    network_io = serializers.DictField()
    active_users = serializers.IntegerField()
    running_jobs = serializers.IntegerField()
    system_health = serializers.CharField()
    uptime = serializers.CharField()
    last_updated = serializers.DateTimeField()


class SystemMetricsSerializer(serializers.Serializer):
    """系统指标序列化器"""
    timestamp = serializers.DateTimeField()
    cpu_usage = serializers.FloatField()
    memory_usage = serializers.FloatField()
    disk_usage = serializers.FloatField()
    network_in = serializers.FloatField()
    network_out = serializers.FloatField()


class APIKeySerializer(serializers.ModelSerializer):
    """API密钥序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    usage_info = serializers.SerializerMethodField()
    
    class Meta:
        model = APIKey
        fields = ['id', 'name', 'key', 'permissions', 'rate_limit', 'status',
                 'created_by', 'created_by_username', 'expires_at', 'last_used_at', 
                 'usage_count', 'usage_info', 'created_at', 'updated_at']
        read_only_fields = ['key', 'secret', 'usage_count', 'last_used_at', 'created_at', 'updated_at']
        extra_kwargs = {
            'secret': {'write_only': True},
        }
    
    def get_usage_info(self, obj):
        """获取使用情况信息"""
        return {
            'usage_count': obj.usage_count,
            'rate_limit': obj.rate_limit,
            'last_used': obj.last_used_at,
            'expires_at': obj.expires_at,
            'is_expired': obj.expires_at and obj.expires_at < timezone.now() if hasattr(obj, 'expires_at') and obj.expires_at else False,
        }


class APIEndpointSerializer(serializers.ModelSerializer):
    """API端点序列化器"""
    
    class Meta:
        model = APIEndpoint
        fields = ['id', 'name', 'path', 'method', 'description', 'is_enabled',
                 'rate_limit', 'auth_required', 'permissions_required', 
                 'created_at', 'updated_at']


class SystemSettingSerializer(serializers.ModelSerializer):
    """系统设置序列化器"""
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    display_value = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemSetting
        fields = ['id', 'category', 'key', 'value', 'default_value', 'data_type',
                 'description', 'is_encrypted', 'is_public', 'validation_rules',
                 'updated_by', 'updated_by_username', 'display_value',
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_display_value(self, obj):
        """获取显示值（加密字段显示为 ***）"""
        if obj.is_encrypted:
            return '***'
        return obj.value


class TeamMembershipSerializer(serializers.ModelSerializer):
    """团队成员序列化器"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    invited_by_username = serializers.CharField(source='invited_by.username', read_only=True)
    
    class Meta:
        model = TeamMembership
        fields = ['id', 'user', 'user_username', 'user_email', 'role', 
                 'joined_at', 'invited_by', 'invited_by_username']


class TeamSerializer(serializers.ModelSerializer):
    """团队序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    members_info = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'avatar', 'is_active',
                 'created_by', 'created_by_username', 'members_info', 
                 'member_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_members_info(self, obj):
        """获取成员信息"""
        memberships = TeamMembership.objects.filter(team=obj).select_related('user')
        return TeamMembershipSerializer(memberships, many=True).data
    
    def get_member_count(self, obj):
        """获取成员数量"""
        return obj.members.count()


class BackupScheduleSerializer(serializers.ModelSerializer):
    """备份计划序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    next_backup_info = serializers.SerializerMethodField()
    
    class Meta:
        model = BackupSchedule
        fields = ['id', 'name', 'description', 'backup_type', 'frequency',
                 'cron_expression', 'retain_days', 'status', 'notification_config',
                 'last_run_at', 'next_run_at', 'created_by', 'created_by_username',
                 'next_backup_info', 'created_at', 'updated_at']
        read_only_fields = ['last_run_at', 'next_run_at', 'created_at', 'updated_at']
    
    def get_next_backup_info(self, obj):
        """获取下次备份信息"""
        return {
            'next_run_at': obj.next_run_at,
            'last_run_at': obj.last_run_at,
            'status': obj.status,
            'is_overdue': obj.next_run_at and obj.next_run_at < timezone.now() if hasattr(obj, 'next_run_at') and obj.next_run_at else False,
        }
