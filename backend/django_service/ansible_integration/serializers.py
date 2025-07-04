from rest_framework import serializers
from .models import AnsibleInventory, AnsiblePlaybook, AnsibleCredential, AnsibleExecution


class AnsibleInventorySerializer(serializers.ModelSerializer):
    """Ansible主机清单序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = AnsibleInventory
        fields = [
            'id', 'name', 'description', 'content', 'format_type',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AnsiblePlaybookSerializer(serializers.ModelSerializer):
    """Ansible Playbook序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = AnsiblePlaybook
        fields = [
            'id', 'name', 'description', 'content', 'version', 'is_template',
            'category', 'category_display', 'parameters', 'created_by', 
            'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AnsibleCredentialSerializer(serializers.ModelSerializer):
    """Ansible凭据序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    credential_type_display = serializers.CharField(source='get_credential_type_display', read_only=True)
    has_password = serializers.BooleanField(read_only=True)
    has_ssh_key = serializers.BooleanField(read_only=True)
    has_vault_password = serializers.BooleanField(read_only=True)
    
    # 输入字段（用于接收明文密码）
    password_input = serializers.CharField(write_only=True, required=False, allow_blank=True)
    ssh_private_key_input = serializers.CharField(write_only=True, required=False, allow_blank=True)
    vault_password_input = serializers.CharField(write_only=True, required=False, allow_blank=True)
    sudo_password_input = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = AnsibleCredential
        fields = [
            'id', 'name', 'credential_type', 'credential_type_display', 'username',
            'has_password', 'has_ssh_key', 'has_vault_password',
            'password_input', 'ssh_private_key_input', 'vault_password_input', 'sudo_password_input',
            'created_by', 'created_by_username', 'created_at'
        ]
        read_only_fields = ['created_by', 'created_at']

    def create(self, validated_data):
        # 处理输入字段
        password_input = validated_data.pop('password_input', '')
        ssh_key_input = validated_data.pop('ssh_private_key_input', '')
        vault_password_input = validated_data.pop('vault_password_input', '')
        sudo_password_input = validated_data.pop('sudo_password_input', '')
        
        validated_data['created_by'] = self.context['request'].user
        
        # 设置明文密码，模型会自动加密
        if password_input:
            validated_data['password'] = password_input
        if ssh_key_input:
            validated_data['ssh_private_key'] = ssh_key_input
        if vault_password_input:
            validated_data['vault_password'] = vault_password_input
        if sudo_password_input:
            validated_data['sudo_password'] = sudo_password_input
            
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # 处理输入字段
        password_input = validated_data.pop('password_input', None)
        ssh_key_input = validated_data.pop('ssh_private_key_input', None)
        vault_password_input = validated_data.pop('vault_password_input', None)
        sudo_password_input = validated_data.pop('sudo_password_input', None)
        
        # 只有提供了新密码才更新
        if password_input is not None:
            validated_data['password'] = password_input
        if ssh_key_input is not None:
            validated_data['ssh_private_key'] = ssh_key_input
        if vault_password_input is not None:
            validated_data['vault_password'] = vault_password_input
        if sudo_password_input is not None:
            validated_data['sudo_password'] = sudo_password_input
            
        return super().update(instance, validated_data)


class AnsibleExecutionSerializer(serializers.ModelSerializer):
    """Ansible执行记录序列化器"""
    playbook_name = serializers.CharField(source='playbook.name', read_only=True)
    inventory_name = serializers.CharField(source='inventory.name', read_only=True)
    credential_name = serializers.CharField(source='credential.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration = serializers.FloatField(read_only=True)
    
    # Pipeline关联字段
    pipeline_name = serializers.CharField(source='pipeline.name', read_only=True)
    pipeline_step_name = serializers.CharField(source='pipeline_step.name', read_only=True)
    
    # 嵌套对象（可选）
    playbook_detail = AnsiblePlaybookSerializer(source='playbook', read_only=True)
    inventory_detail = AnsibleInventorySerializer(source='inventory', read_only=True)
    credential_detail = AnsibleCredentialSerializer(source='credential', read_only=True)
    
    class Meta:
        model = AnsibleExecution
        fields = [
            'id', 'playbook', 'playbook_name', 'playbook_detail',
            'inventory', 'inventory_name', 'inventory_detail',
            'credential', 'credential_name', 'credential_detail',
            'pipeline', 'pipeline_name', 'pipeline_step', 'pipeline_step_name',
            'parameters', 'status', 'status_display', 'duration',
            'started_at', 'completed_at', 'stdout', 'stderr', 'return_code',
            'created_by', 'created_by_username', 'created_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'duration']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AnsibleExecutionListSerializer(serializers.ModelSerializer):
    """Ansible执行记录列表序列化器（简化版）"""
    playbook_name = serializers.CharField(source='playbook.name', read_only=True)
    inventory_name = serializers.CharField(source='inventory.name', read_only=True)
    credential_name = serializers.CharField(source='credential.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration = serializers.FloatField(read_only=True)
    
    # Pipeline关联字段
    pipeline_name = serializers.CharField(source='pipeline.name', read_only=True)
    pipeline_step_name = serializers.CharField(source='pipeline_step.name', read_only=True)
    
    class Meta:
        model = AnsibleExecution
        fields = [
            'id', 'playbook_name', 'inventory_name', 'credential_name',
            'pipeline_name', 'pipeline_step_name',
            'status', 'status_display', 'duration', 'started_at', 'completed_at',
            'return_code', 'created_by_username', 'created_at'
        ]


class AnsibleStatsSerializer(serializers.Serializer):
    """Ansible统计信息序列化器"""
    total_executions = serializers.IntegerField()
    successful_executions = serializers.IntegerField()
    failed_executions = serializers.IntegerField()
    running_executions = serializers.IntegerField()
    pending_executions = serializers.IntegerField()
    success_rate = serializers.FloatField()
    avg_duration = serializers.FloatField()
    total_playbooks = serializers.IntegerField()
    total_inventories = serializers.IntegerField()
    total_credentials = serializers.IntegerField()
