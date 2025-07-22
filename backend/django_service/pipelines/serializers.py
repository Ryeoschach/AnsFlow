from rest_framework import serializers
from .models import (
    Pipeline, PipelineStep, PipelineRun, PipelineToolMapping,
    ParallelGroup, ApprovalRequest, WorkflowExecution, StepExecutionHistory
)
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
            # 高级工作流功能字段
            'dependencies', 'parallel_group', 'conditions',
            'approval_required', 'approval_users', 'approval_status',
            'approved_by', 'approved_at', 'retry_policy', 'notification_config',
            'output_log', 'error_log', 'exit_code',
            'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'output_log', 'error_log', 'exit_code', 'started_at', 'completed_at',
                           'approval_status', 'approved_by', 'approved_at']


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
        # 检查原始数据中是否包含steps字段
        request_data = getattr(self.context.get('request'), 'data', {})
        has_steps_field = 'steps' in request_data
        
        steps_data = validated_data.pop('steps', None)
        instance = super().update(instance, validated_data)
        
        # 只有当请求中明确包含steps字段时才更新步骤
        if has_steps_field and steps_data is not None:
            # 删除现有的Pipeline步骤
            instance.steps.all().delete()
            
            # 同时删除现有的AtomicStep（这是关键修复）
            instance.atomic_steps.all().delete()
            
            # 创建新的Pipeline步骤和AtomicStep
            self._create_pipeline_steps(instance, steps_data)
        
        return instance
    
    def _create_pipeline_steps(self, pipeline, steps_data):
        """创建Pipeline步骤的辅助方法 - 同时创建PipelineStep和AtomicStep"""
        for step_data in steps_data:
            try:
                # 创建AtomicStep（这是预览API使用的数据源）
                atomic_step_data = {
                    'pipeline': pipeline,
                    'name': step_data.get('name', ''),
                    'description': step_data.get('description', ''),
                    'step_type': step_data.get('step_type', 'custom'),
                    'order': step_data.get('order', 0),
                    'parameters': step_data.get('parameters', {}),
                    'is_active': True,
                    'created_by': pipeline.created_by,
                }
                
                # 处理Ansible相关字段（如果需要）
                parameters = step_data.get('parameters', {})
                if step_data.get('step_type') == 'ansible':
                    playbook_id = parameters.get('playbook_id')
                    inventory_id = parameters.get('inventory_id')
                    credential_id = parameters.get('credential_id')
                    
                    if playbook_id:
                        atomic_step_data['ansible_playbook_id'] = playbook_id
                    if inventory_id:
                        atomic_step_data['ansible_inventory_id'] = inventory_id
                    if credential_id:
                        atomic_step_data['ansible_credential_id'] = credential_id
                
                print(f"Creating AtomicStep with data: {atomic_step_data}")
                created_atomic_step = AtomicStep.objects.create(**atomic_step_data)
                print(f"Successfully created AtomicStep: {created_atomic_step.id} - {created_atomic_step.name}")
                
                # 同时创建PipelineStep（为了向后兼容）
                pipeline_step_data = {
                    'pipeline': pipeline,
                    'name': step_data.get('name', ''),
                    'description': step_data.get('description', ''),
                    'step_type': self._map_step_type(step_data.get('step_type', 'custom')),
                    'order': step_data.get('order', 0),
                    'status': 'pending',  # 默认状态
                    'ansible_parameters': step_data.get('parameters', {}),
                    # 关键修复：处理并行组字段
                    'parallel_group': step_data.get('parallel_group', ''),
                    # 关键修复：从parameters中提取command字段
                    'command': parameters.get('command', ''),
                }
                
                # 处理Ansible相关字段
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
                
                # 调试日志：显示并行组字段
                if step_data.get('parallel_group'):
                    print(f"🔗 步骤 '{step_data.get('name')}' 分配到并行组: {step_data.get('parallel_group')}")
                
                print(f"Creating PipelineStep with data: {pipeline_step_data}")
                created_step = PipelineStep.objects.create(**pipeline_step_data)
                print(f"Successfully created PipelineStep: {created_step.id} - {created_step.name} - parallel_group: {created_step.parallel_group}")
                
            except Exception as e:
                print(f"Error creating pipeline steps: {e}")
                print(f"Step data causing error: {step_data}")
                raise
    
    def _map_step_type(self, frontend_step_type):
        """映射前端步骤类型到PipelineStep模型的choices"""
        # 定义支持的步骤类型 - 保持与PipelineStep.STEP_TYPE_CHOICES一致
        valid_step_types = [
            'fetch_code', 'build', 'test', 'security_scan',
            'deploy', 'ansible', 'notify', 'custom', 'script',
            # Docker 步骤类型
            'docker_build', 'docker_run', 'docker_push', 'docker_pull',
            # Kubernetes 步骤类型
            'k8s_deploy', 'k8s_scale', 'k8s_delete', 'k8s_wait',
            'k8s_exec', 'k8s_logs',
            # 其他高级步骤类型
            'approval', 'condition'
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


# 新增高级工作流功能序列化器

class ParallelGroupSerializer(serializers.ModelSerializer):
    """并行组序列化器"""
    steps = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        write_only=False,
        help_text="步骤ID列表"
    )
    
    class Meta:
        model = ParallelGroup
        fields = [
            'id', 'name', 'description', 'pipeline', 'sync_policy',
            'timeout_seconds', 'steps', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def to_representation(self, instance):
        """自定义序列化输出，包含关联的步骤"""
        data = super().to_representation(instance)
        
        # 获取属于该并行组的步骤ID列表
        group_id_str = str(instance.id)
        steps = instance.pipeline.steps.filter(parallel_group=group_id_str)
        data['steps'] = [step.id for step in steps]
        
        return data
    
    def create(self, validated_data):
        """创建并行组并处理步骤关联"""
        # 提取steps数据
        steps_data = validated_data.pop('steps', [])
        
        # 创建并行组（不包含steps字段）
        parallel_group = super().create(validated_data)
        
        # 处理步骤关联
        if steps_data:
            self._update_step_associations(parallel_group, steps_data)
        
        return parallel_group
    
    def update(self, instance, validated_data):
        """更新并行组并处理步骤关联"""
        # 提取steps数据
        steps_data = validated_data.pop('steps', None)
        
        # 更新并行组基本信息
        parallel_group = super().update(instance, validated_data)
        
        # 如果提供了steps数据，更新步骤关联
        if steps_data is not None:
            self._update_step_associations(parallel_group, steps_data)
        
        return parallel_group
        
        # 如果提供了steps数据，更新步骤关联
        if steps_data is not None:
            self._update_step_associations(parallel_group, steps_data)
        
        return parallel_group
    
    def _update_step_associations(self, parallel_group, steps_data):
        """更新步骤与并行组的关联"""
        from .models import PipelineStep
        
        # 确保并行组有有效的ID
        if not parallel_group.id:
            print(f"❌ 并行组没有有效的ID，无法关联步骤")
            return
        
        # 将 parallel_group.id 转换为字符串，因为 parallel_group 字段是 CharField
        group_id_str = str(parallel_group.id)
        
        print(f"🔗 更新并行组 {parallel_group.id} 的步骤关联: {steps_data}")
        
        # 1. 清除该并行组的所有现有关联
        cleared_count = PipelineStep.objects.filter(
            pipeline=parallel_group.pipeline,
            parallel_group=group_id_str
        ).update(parallel_group='')
        
        print(f"✅ 已清除并行组 {parallel_group.id} 的 {cleared_count} 个现有关联")
        
        # 2. 设置新的关联
        if steps_data:
            updated_count = PipelineStep.objects.filter(
                pipeline=parallel_group.pipeline,
                id__in=steps_data
            ).update(parallel_group=group_id_str)
            
            print(f"✅ 已将 {updated_count} 个步骤关联到并行组 {parallel_group.id}")
            
            # 验证更新结果
            associated_steps = PipelineStep.objects.filter(
                pipeline=parallel_group.pipeline,
                parallel_group=group_id_str
            )
            
            print(f"🔍 验证: 并行组 {parallel_group.id} 现在包含 {associated_steps.count()} 个步骤")
            for step in associated_steps:
                print(f"  - 步骤 {step.name} (ID: {step.id})")
        else:
            print(f"📝 并行组 {parallel_group.id} 没有分配任何步骤")


class ApprovalRequestSerializer(serializers.ModelSerializer):
    """审批请求序列化器"""
    
    pipeline_name = serializers.CharField(source='pipeline.name', read_only=True)
    step_name = serializers.CharField(source='step.name', read_only=True)
    requester_username = serializers.CharField(source='requester.username', read_only=True)
    
    class Meta:
        model = ApprovalRequest
        fields = [
            'id', 'pipeline', 'pipeline_name', 'step', 'step_name',
            'execution_id', 'requester', 'requester_username',
            'approvers', 'required_approvals', 'status', 'approval_message',
            'timeout_hours', 'auto_approve_on_timeout',
            'approved_by', 'approved_at', 'response_comment',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'approved_by', 'approved_at', 'created_at', 'updated_at']


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    """工作流执行序列化器"""
    
    pipeline_name = serializers.CharField(source='pipeline.name', read_only=True)
    current_step_name = serializers.CharField(source='current_step.name', read_only=True)
    
    class Meta:
        model = WorkflowExecution
        fields = [
            'id', 'pipeline', 'pipeline_name', 'execution_id',
            'status', 'trigger_data', 'context_variables', 'step_results',
            'current_step', 'current_step_name', 'failed_steps',
            'pending_approvals', 'recovery_point',
            'started_at', 'completed_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class StepExecutionHistorySerializer(serializers.ModelSerializer):
    """步骤执行历史序列化器"""
    
    step_name = serializers.CharField(source='step.name', read_only=True)
    
    class Meta:
        model = StepExecutionHistory
        fields = [
            'id', 'workflow_execution', 'step', 'step_name',
            'status', 'retry_count', 'max_retries',
            'logs', 'error_message', 'output_data',
            'started_at', 'completed_at', 'duration_seconds',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class WorkflowAnalysisSerializer(serializers.Serializer):
    """工作流分析结果序列化器"""
    
    total_steps = serializers.IntegerField()
    parallel_groups = serializers.IntegerField()
    approval_steps = serializers.IntegerField()
    conditional_steps = serializers.IntegerField()
    estimated_duration_minutes = serializers.FloatField(required=False)
    critical_path = serializers.ListField(child=serializers.IntegerField(), required=False)
    potential_bottlenecks = serializers.ListField(child=serializers.CharField(), required=False)
    
    
class WorkflowMetricsSerializer(serializers.Serializer):
    """工作流指标序列化器"""
    
    total_steps = serializers.IntegerField()
    parallel_steps = serializers.IntegerField()
    conditional_steps = serializers.IntegerField()
    approval_steps = serializers.IntegerField()
    estimated_duration = serializers.FloatField()
    complexity_score = serializers.FloatField()
    critical_path = serializers.ListField(child=serializers.IntegerField())
    
    
class ExecutionRecoverySerializer(serializers.Serializer):
    """执行恢复序列化器"""
    
    from_step_id = serializers.IntegerField()
    skip_failed = serializers.BooleanField(default=False)
    modify_parameters = serializers.BooleanField(default=False)
    parameters = serializers.JSONField(default=dict)
    recovery_strategy = serializers.ChoiceField(
        choices=['continue', 'restart_from', 'skip_and_continue'],
        default='continue'
    )
    force_retry = serializers.BooleanField(default=False)
    custom_timeout = serializers.IntegerField(required=False)
    
    
class ApprovalResponseSerializer(serializers.Serializer):
    """审批响应序列化器"""
    
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    comment = serializers.CharField(required=False, allow_blank=True)
