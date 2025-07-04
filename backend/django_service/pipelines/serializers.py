from rest_framework import serializers
from .models import Pipeline, PipelineStep, PipelineRun, PipelineToolMapping
from cicd_integrations.models import AtomicStep


class PipelineStepSerializer(serializers.ModelSerializer):
    # Ansible关联字段
    ansible_playbook_name = serializers.CharField(source='ansible_playbook.name', read_only=True)
    ansible_inventory_name = serializers.CharField(source='ansible_inventory.name', read_only=True)
    ansible_credential_name = serializers.CharField(source='ansible_credential.name', read_only=True)
    
    class Meta:
        model = PipelineStep
        fields = [
            'id', 'name', 'description', 'status', 'step_type',
            'command', 'environment_vars', 'timeout_seconds', 'order',
            'ansible_playbook', 'ansible_playbook_name',
            'ansible_inventory', 'ansible_inventory_name', 
            'ansible_credential', 'ansible_credential_name',
            'ansible_parameters',
            'output_log', 'error_log', 'exit_code',
            'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'output_log', 'error_log', 'exit_code', 'started_at', 'completed_at']


class AtomicStepInPipelineSerializer(serializers.ModelSerializer):
    """AtomicStep序列化器，用于Pipeline中的steps字段"""
    class Meta:
        model = AtomicStep
        fields = [
            'id', 'name', 'step_type', 'description', 'order',
            'parameters', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PipelineRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineRun
        fields = [
            'id', 'run_number', 'status', 'triggered_by', 'trigger_type',
            'trigger_data', 'started_at', 'completed_at', 'created_at', 'artifacts'
        ]
        read_only_fields = ['id', 'run_number', 'triggered_by', 'started_at', 'completed_at', 'created_at']


class PipelineSerializer(serializers.ModelSerializer):
    steps = PipelineStepSerializer(many=True, read_only=True)
    runs = PipelineRunSerializer(many=True, read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    # 新增：工具关联字段
    execution_tool_name = serializers.CharField(source='execution_tool.name', read_only=True)
    execution_tool_type = serializers.CharField(source='execution_tool.tool_type', read_only=True)
    
    class Meta:
        model = Pipeline
        fields = [
            'id', 'name', 'description', 'status', 'is_active', 'config',
            'project', 'project_name', 'created_by', 'created_by_username',
            'created_at', 'updated_at', 'started_at', 'completed_at',
            # 新增字段
            'execution_tool', 'execution_tool_name', 'execution_tool_type',
            'tool_job_name', 'tool_job_config', 'execution_mode',
            'steps', 'runs'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'started_at', 'completed_at']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        steps_data = validated_data.pop('steps', [])
        pipeline = super().create(validated_data)
        
        # 创建关联的Pipeline步骤
        for step_data in steps_data:
            step_data['pipeline'] = pipeline
            PipelineStep.objects.create(**step_data)
        
        return pipeline
    
    def update(self, instance, validated_data):
        steps_data = validated_data.pop('steps', None)
        instance = super().update(instance, validated_data)
        
        if steps_data is not None:
            # 删除现有的Pipeline步骤
            instance.steps.all().delete()
            
            # 创建新的Pipeline步骤
            for step_data in steps_data:
                step_data['pipeline'] = instance
                PipelineStep.objects.create(**step_data)
        
        return instance


class PipelineListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    steps_count = serializers.IntegerField(source='steps.count', read_only=True)
    runs_count = serializers.IntegerField(source='runs.count', read_only=True)
    
    # 新增：执行模式相关字段
    execution_tool_name = serializers.CharField(source='execution_tool.name', read_only=True)
    execution_tool_type = serializers.CharField(source='execution_tool.tool_type', read_only=True)
    
    class Meta:
        model = Pipeline
        fields = [
            'id', 'name', 'description', 'status', 'is_active',
            'project', 'project_name', 'created_by_username',
            'created_at', 'updated_at', 'steps_count', 'runs_count',
            # 新增：执行模式相关字段
            'execution_mode', 'execution_tool', 'execution_tool_name', 
            'execution_tool_type', 'tool_job_name'
        ]


class PipelineToolMappingSerializer(serializers.ModelSerializer):
    """流水线与工具映射序列化器"""
    
    pipeline_name = serializers.CharField(source='pipeline.name', read_only=True)
    tool_name = serializers.CharField(source='tool.name', read_only=True)
    tool_type = serializers.CharField(source='tool.tool_type', read_only=True)
    
    class Meta:
        model = PipelineToolMapping
        fields = [
            'id', 'pipeline', 'pipeline_name', 'tool', 'tool_name', 'tool_type',
            'external_job_id', 'external_job_name', 'auto_sync', 'last_sync_at',
            'sync_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_sync_at', 'created_at', 'updated_at']
