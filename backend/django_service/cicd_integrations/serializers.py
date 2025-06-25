"""
CI/CD 集成 API 序列化器
"""
from rest_framework import serializers
from .models import CICDTool, AtomicStep, PipelineExecution, StepExecution


class CICDToolSerializer(serializers.ModelSerializer):
    """CI/CD 工具序列化器"""
    
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    tool_type_display = serializers.CharField(source='get_tool_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CICDTool
        fields = [
            'id', 'name', 'tool_type', 'tool_type_display', 'base_url',
            'username', 'config', 'metadata', 'status', 'status_display',
            'last_health_check', 'project', 'project_name',
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


class CICDToolCreateSerializer(serializers.ModelSerializer):
    """CI/CD 工具创建序列化器"""
    
    class Meta:
        model = CICDTool
        fields = [
            'name', 'tool_type', 'base_url', 'username', 'token',
            'config', 'metadata', 'project'
        ]
    
    def validate(self, data):
        # 验证同一项目下工具名称唯一
        if CICDTool.objects.filter(
            project=data['project'],
            name=data['name']
        ).exists():
            raise serializers.ValidationError(
                "A tool with this name already exists in the project."
            )
        return data


class AtomicStepSerializer(serializers.ModelSerializer):
    """原子步骤序列化器"""
    
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    step_type_display = serializers.CharField(source='get_step_type_display', read_only=True)
    dependencies_count = serializers.IntegerField(source='dependencies.count', read_only=True)
    
    class Meta:
        model = AtomicStep
        fields = [
            'id', 'name', 'step_type', 'step_type_display', 'description',
            'parameters', 'dependencies', 'dependencies_count', 'conditions',
            'created_by', 'created_by_username', 'is_public',
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
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = StepExecution
        fields = [
            'id', 'atomic_step', 'atomic_step_name', 'external_id',
            'status', 'status_display', 'order', 'logs', 'output',
            'error_message', 'started_at', 'completed_at', 'duration',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'started_at', 'completed_at'
        ]


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
            if tool.status != 'active':
                raise serializers.ValidationError("CI/CD tool is not active.")
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
