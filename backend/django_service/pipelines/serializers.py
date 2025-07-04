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
    # 将steps字段改为可写字段，既能读取又能写入
    steps = serializers.JSONField(required=False, allow_null=True, default=list)
    atomic_steps = AtomicStepInPipelineSerializer(many=True, read_only=True)  # 兼容字段
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
            'steps', 'atomic_steps', 'runs'  # 包含合并的steps和兼容的atomic_steps
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'started_at', 'completed_at']
    
    def to_representation(self, instance):
        """自定义序列化输出，合并返回PipelineStep和AtomicStep数据"""
        data = super().to_representation(instance)
        
        # 首先尝试获取PipelineStep
        pipeline_steps = instance.steps.all().order_by('order')
        if pipeline_steps.exists():
            data['steps'] = PipelineStepSerializer(pipeline_steps, many=True).data
        else:
            # 如果没有PipelineStep，返回AtomicStep数据（转换为兼容格式）
            atomic_steps = instance.atomic_steps.all().order_by('order')
            if atomic_steps.exists():
                # 将AtomicStep转换为PipelineStep兼容格式
                steps_data = []
                for atomic_step in atomic_steps:
                    step_data = {
                        'id': atomic_step.id,
                        'name': atomic_step.name,
                        'description': atomic_step.description,
                        'step_type': atomic_step.step_type,
                        'order': atomic_step.order,
                        'status': 'pending',  # 默认状态
                        'ansible_parameters': atomic_step.parameters,
                        # 从parameters中提取ansible字段
                        'ansible_playbook': atomic_step.ansible_playbook_id if atomic_step.ansible_playbook else None,
                        'ansible_inventory': atomic_step.ansible_inventory_id if atomic_step.ansible_inventory else None,
                        'ansible_credential': atomic_step.ansible_credential_id if atomic_step.ansible_credential else None,
                    }
                    steps_data.append(step_data)
                data['steps'] = steps_data
            else:
                data['steps'] = []
        
        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        steps_data = validated_data.pop('steps', [])
        pipeline = super().create(validated_data)
        
        # 创建关联的Pipeline步骤
        self._create_pipeline_steps(pipeline, steps_data)
        
        return pipeline
    
    def update(self, instance, validated_data):
        steps_data = validated_data.pop('steps', None)
        instance = super().update(instance, validated_data)
        
        if steps_data is not None:
            # 删除现有的Pipeline步骤
            instance.steps.all().delete()
            
            # 创建新的Pipeline步骤
            self._create_pipeline_steps(instance, steps_data)
        
        return instance
    
    def _create_pipeline_steps(self, pipeline, steps_data):
        """创建Pipeline步骤的辅助方法"""
        for step_data in steps_data:
            try:
                # 转换步骤数据格式以匹配PipelineStep模型
                pipeline_step_data = {
                    'pipeline': pipeline,
                    'name': step_data.get('name', ''),
                    'description': step_data.get('description', ''),
                    'step_type': self._map_step_type(step_data.get('step_type', 'custom')),
                    'order': step_data.get('order', 0),
                    'status': 'pending',  # 默认状态
                    'ansible_parameters': step_data.get('parameters', {}),
                }
                
                # 处理Ansible相关字段
                parameters = step_data.get('parameters', {})
                if step_data.get('step_type') == 'ansible':
                    playbook_id = parameters.get('playbook_id')
                    inventory_id = parameters.get('inventory_id')
                    credential_id = parameters.get('credential_id')
                    
                    if playbook_id:
                        pipeline_step_data['ansible_playbook_id'] = playbook_id
                    if inventory_id:
                        pipeline_step_data['ansible_inventory_id'] = inventory_id
                    if credential_id:
                        pipeline_step_data['ansible_credential_id'] = credential_id
                
                # 处理Git凭据
                if step_data.get('git_credential'):
                    # Git凭据存储在parameters中
                    pipeline_step_data['ansible_parameters']['git_credential_id'] = step_data['git_credential']
                
                print(f"Creating PipelineStep with data: {pipeline_step_data}")
                created_step = PipelineStep.objects.create(**pipeline_step_data)
                print(f"Successfully created PipelineStep: {created_step.id} - {created_step.name}")
                
            except Exception as e:
                print(f"Error creating PipelineStep: {e}")
                print(f"Step data causing error: {step_data}")
                raise
    
    def _map_step_type(self, frontend_step_type):
        """映射前端步骤类型到PipelineStep模型的choices"""
        # 定义支持的步骤类型
        valid_step_types = [
            'fetch_code', 'build', 'test', 'security_scan',
            'deploy', 'ansible', 'notify', 'custom', 'script'
        ]
        
        # 如果前端传来的类型在支持列表中，直接使用
        if frontend_step_type in valid_step_types:
            return frontend_step_type
        
        # 否则映射到custom类型作为兜底
        return 'custom'

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
