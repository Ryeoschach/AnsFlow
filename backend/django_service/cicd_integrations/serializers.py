"""
CI/CD 集成 API 序列化器
"""
from rest_framework import serializers
from .models import CICDTool, AtomicStep, PipelineExecution, StepExecution, GitCredential


class CICDToolSerializer(serializers.ModelSerializer):
    """CI/CD 工具序列化器"""
    
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    tool_type_display = serializers.CharField(source='get_tool_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_active = serializers.SerializerMethodField()
    detailed_status = serializers.SerializerMethodField()
    # 添加一个只读的token状态字段，用于前端判断是否已设置token
    has_token = serializers.SerializerMethodField()
    
    # token字段在创建时也是可选的
    token = serializers.CharField(required=False, allow_blank=True, help_text="密码或访问令牌，可选")
    
    def get_is_active(self, obj):
        """根据状态确定是否活跃"""
        return obj.status in ['active', 'authenticated', 'needs_auth']
    
    def get_detailed_status(self, obj):
        """返回详细状态信息"""
        return obj.status
    
    def get_has_token(self, obj):
        """返回是否已设置token"""
        return bool(obj.token)
    
    class Meta:
        model = CICDTool
        fields = [
            'id', 'name', 'tool_type', 'tool_type_display', 'base_url', 'description',
            'username', 'token', 'config', 'metadata', 'status', 'status_display',
            'is_active', 'detailed_status', 'has_token', 'last_health_check', 'project', 'project_name',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'updated_at', 'last_health_check'
        ]
        extra_kwargs = {
            'token': {'write_only': True}  # 不在响应中返回 token
        }
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CICDToolUpdateSerializer(serializers.ModelSerializer):
    """CI/CD 工具更新序列化器"""
    
    # token字段在更新时是可选的，如果不提供则保持原值
    token = serializers.CharField(required=False, allow_blank=True, help_text="如果不修改则留空")
    
    class Meta:
        model = CICDTool
        fields = [
            'name', 'tool_type', 'base_url', 'description', 'username', 'token',
            'config', 'metadata'
        ]
    
    def update(self, instance, validated_data):
        # 如果token字段为空或未提供，则不更新token
        token = validated_data.get('token')
        token_updated = False
        
        if not token:
            validated_data.pop('token', None)
        else:
            # 检查token是否真的发生了变化
            token_updated = token != instance.token
        
        # 执行更新
        instance = super().update(instance, validated_data)
        
        # 如果token被更新了，重置状态为待检查
        if token_updated:
            instance.status = 'inactive'  # 重置状态，等待健康检查
            instance.save(update_fields=['status'])
        
        return instance
    
    def validate(self, data):
        # 验证同一项目下工具名称唯一（排除当前实例）
        if 'name' in data:
            existing_tool = CICDTool.objects.filter(
                project=self.instance.project,
                name=data['name']
            ).exclude(id=self.instance.id)
            
            if existing_tool.exists():
                raise serializers.ValidationError(
                    "A tool with this name already exists in the project."
                )
        return data


class AtomicStepSerializer(serializers.ModelSerializer):
    """原子步骤序列化器"""
    
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    step_type_display = serializers.CharField(source='get_step_type_display', read_only=True)
    dependencies_count = serializers.IntegerField(source='dependencies.count', read_only=True)
    
    # Git凭据相关字段
    git_credential_name = serializers.CharField(source='git_credential.name', read_only=True)
    
    # Ansible相关字段
    ansible_playbook_name = serializers.CharField(source='ansible_playbook.name', read_only=True)
    ansible_inventory_name = serializers.CharField(source='ansible_inventory.name', read_only=True)
    ansible_credential_name = serializers.CharField(source='ansible_credential.name', read_only=True)
    
    class Meta:
        model = AtomicStep
        fields = [
            'id', 'name', 'step_type', 'step_type_display', 'description',
            'order', 'parameters', 'config', 'dependencies', 'dependencies_count', 
            'conditions', 'timeout', 'retry_count',
            'git_credential', 'git_credential_name',
            'ansible_playbook', 'ansible_playbook_name',
            'ansible_inventory', 'ansible_inventory_name', 
            'ansible_credential', 'ansible_credential_name',
            'pipeline', 'created_by', 'created_by_username', 'is_public', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AtomicStepSimpleSerializer(serializers.ModelSerializer):
    """简化的原子步骤序列化器"""
    
    step_type_display = serializers.CharField(source='get_step_type_display', read_only=True)
    
    class Meta:
        model = AtomicStep
        fields = ['id', 'name', 'step_type', 'step_type_display', 'description']


class StepExecutionSerializer(serializers.ModelSerializer):
    """步骤执行序列化器"""
    
    atomic_step_name = serializers.CharField(source='atomic_step.name', read_only=True)
    pipeline_step_name = serializers.CharField(source='pipeline_step.name', read_only=True)
    step_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = StepExecution
        fields = [
            'id', 'atomic_step', 'atomic_step_name', 'pipeline_step', 'pipeline_step_name', 
            'step_name', 'external_id', 'status', 'status_display', 'order', 'logs', 'output',
            'error_message', 'started_at', 'completed_at', 'duration',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'started_at', 'completed_at'
        ]
    
    def get_step_name(self, obj):
        """获取步骤名称，优先使用 pipeline_step，回退到 atomic_step"""
        if obj.pipeline_step:
            return obj.pipeline_step.name
        elif obj.atomic_step:
            return obj.atomic_step.name
        else:
            return f"Step {obj.order}"


class PipelineExecutionSerializer(serializers.ModelSerializer):
    """流水线执行序列化器"""
    
    pipeline_name = serializers.CharField(source='pipeline.name', read_only=True)
    cicd_tool_name = serializers.CharField(source='cicd_tool.name', read_only=True)
    cicd_tool_type = serializers.CharField(source='cicd_tool.tool_type', read_only=True)
    triggered_by_username = serializers.CharField(source='triggered_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    trigger_type_display = serializers.CharField(source='get_trigger_type_display', read_only=True)
    duration = serializers.ReadOnlyField()
    step_executions = StepExecutionSerializer(many=True, read_only=True)
    
    class Meta:
        model = PipelineExecution
        fields = [
            'id', 'pipeline', 'pipeline_name', 'cicd_tool', 'cicd_tool_name',
            'cicd_tool_type', 'external_id', 'external_url', 'status',
            'status_display', 'trigger_type', 'trigger_type_display',
            'definition', 'parameters', 'logs', 'artifacts', 'test_results',
            'started_at', 'completed_at', 'duration', 'triggered_by',
            'triggered_by_username', 'trigger_data', 'step_executions',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'external_id', 'external_url', 'logs', 'artifacts',
            'test_results', 'started_at', 'completed_at', 'created_at', 'updated_at'
        ]


class PipelineExecutionListSerializer(serializers.ModelSerializer):
    """流水线执行列表序列化器（简化版）"""
    
    pipeline_name = serializers.CharField(source='pipeline.name', read_only=True)
    cicd_tool_name = serializers.CharField(source='cicd_tool.name', read_only=True)
    triggered_by_username = serializers.CharField(source='triggered_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = PipelineExecution
        fields = [
            'id', 'pipeline_name', 'cicd_tool_name', 'external_id',
            'external_url', 'status', 'status_display', 'trigger_type',
            'started_at', 'completed_at', 'duration', 'triggered_by_username',
            'created_at'
        ]


class PipelineExecutionCreateSerializer(serializers.Serializer):
    """流水线执行创建序列化器"""
    
    pipeline_id = serializers.IntegerField()
    cicd_tool_id = serializers.IntegerField()
    trigger_type = serializers.ChoiceField(
        choices=PipelineExecution.TRIGGER_TYPES,
        default='manual'
    )
    parameters = serializers.JSONField(default=dict)
    
    def validate_pipeline_id(self, value):
        from pipelines.models import Pipeline
        try:
            pipeline = Pipeline.objects.get(id=value)
            # 检查用户是否有权限访问此流水线
            request = self.context.get('request')
            if request and request.user:
                # 这里可以添加更复杂的权限检查逻辑
                pass
            return value
        except Pipeline.DoesNotExist:
            raise serializers.ValidationError("Pipeline not found.")
    
    def validate_cicd_tool_id(self, value):
        try:
            tool = CICDTool.objects.get(id=value)
            # 只有 authenticated 状态的工具才能被用于触发流水线
            if tool.status != 'authenticated':
                raise serializers.ValidationError(
                    f"CI/CD tool is not ready for execution. Current status: {tool.status}. "
                    f"Tool must be in 'authenticated' status to trigger pipelines."
                )
            return value
        except CICDTool.DoesNotExist:
            raise serializers.ValidationError("CI/CD tool not found.")


class HealthCheckSerializer(serializers.Serializer):
    """健康检查序列化器"""
    
    tool_id = serializers.IntegerField()
    
    def validate_tool_id(self, value):
        try:
            CICDTool.objects.get(id=value)
            return value
        except CICDTool.DoesNotExist:
            raise serializers.ValidationError("CI/CD tool not found.")


class ToolStatusSerializer(serializers.Serializer):
    """工具状态序列化器"""
    
    tool_id = serializers.IntegerField(read_only=True)
    tool_name = serializers.CharField(read_only=True)
    tool_type = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    is_healthy = serializers.BooleanField(read_only=True)
    last_check = serializers.DateTimeField(read_only=True)
    error_message = serializers.CharField(read_only=True, allow_null=True)


class GitCredentialSerializer(serializers.ModelSerializer):
    """Git认证凭据序列化器"""
    password = serializers.CharField(write_only=True, required=False, help_text="密码/Token")
    ssh_private_key = serializers.CharField(write_only=True, required=False, help_text="SSH私钥")
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    credential_type_display = serializers.CharField(source='get_credential_type_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    has_password = serializers.SerializerMethodField(read_only=True, help_text="是否已设置密码")
    has_ssh_key = serializers.SerializerMethodField(read_only=True, help_text="是否已设置SSH密钥")
    
    class Meta:
        model = GitCredential
        fields = [
            'id', 'name', 'platform', 'platform_display', 'credential_type', 
            'credential_type_display', 'server_url', 'username', 'password',
            'ssh_private_key', 'ssh_public_key', 'description', 'is_active',
            'last_test_at', 'last_test_result', 'created_by_username',
            'has_password', 'has_ssh_key', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'ssh_private_key': {'write_only': True},
        }
    
    def get_has_password(self, obj):
        """检查是否已设置密码"""
        return bool(obj.password_encrypted)
    
    def get_has_ssh_key(self, obj):
        """检查是否已设置SSH密钥"""
        return bool(obj.ssh_private_key_encrypted)
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        ssh_private_key = validated_data.pop('ssh_private_key', None)
        
        # 设置创建者
        validated_data['created_by'] = self.context['request'].user
        
        credential = GitCredential.objects.create(**validated_data)
        
        # 加密敏感信息
        if password:
            credential.encrypt_password(password)
        if ssh_private_key:
            credential.encrypt_ssh_key(ssh_private_key)
        
        credential.save()
        return credential
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        ssh_private_key = validated_data.pop('ssh_private_key', None)
        
        # 更新基本字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # 更新敏感信息 - 只有在提供了非空值时才加密
        if password is not None and password.strip():
            instance.encrypt_password(password)
        if ssh_private_key is not None and ssh_private_key.strip():
            instance.encrypt_ssh_key(ssh_private_key)
        
        instance.save()
        return instance


class GitCredentialListSerializer(serializers.ModelSerializer):
    """Git认证凭据列表序列化器（不包含敏感信息）"""
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    credential_type_display = serializers.CharField(source='get_credential_type_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    has_credentials = serializers.SerializerMethodField()
    has_password = serializers.SerializerMethodField()
    has_ssh_key = serializers.SerializerMethodField()
    
    class Meta:
        model = GitCredential
        fields = [
            'id', 'name', 'platform', 'platform_display', 'credential_type',
            'credential_type_display', 'server_url', 'username', 'description', 
            'is_active', 'last_test_at', 'last_test_result', 'created_by_username',
            'has_credentials', 'has_password', 'has_ssh_key', 'created_at', 'updated_at'
        ]
    
    def get_has_credentials(self, obj):
        """检查是否已设置凭据"""
        if obj.credential_type == 'ssh_key':
            return bool(obj.ssh_private_key_encrypted)
        else:
            return bool(obj.password_encrypted)
    
    def get_has_password(self, obj):
        """检查是否已设置密码/Token"""
        return bool(obj.password_encrypted)
    
    def get_has_ssh_key(self, obj):
        """检查是否已设置SSH私钥"""
        return bool(obj.ssh_private_key_encrypted)
