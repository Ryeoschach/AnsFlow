from rest_framework import serializers
from .models import (
    AnsibleInventory, AnsiblePlaybook, AnsibleCredential, AnsibleExecution,
    AnsibleHost, AnsibleHostGroup, AnsibleInventoryVersion, AnsiblePlaybookVersion
)


class AnsibleInventorySerializer(serializers.ModelSerializer):
    """Ansible主机清单序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    
    class Meta:
        model = AnsibleInventory
        fields = [
            'id', 'name', 'description', 'content', 'format_type', 'source_type',
            'source_type_display', 'file_path', 'git_url', 'git_branch',
            'dynamic_script', 'version', 'checksum', 'is_validated',
            'validation_message', 'created_by', 'created_by_username', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'checksum', 'is_validated', 'validation_message',
            'created_by', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AnsiblePlaybookSerializer(serializers.ModelSerializer):
    """Ansible Playbook序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = AnsiblePlaybook
        fields = [
            'id', 'name', 'description', 'content', 'version', 'is_template',
            'category', 'category_display', 'source_type', 'source_type_display',
            'file_path', 'git_url', 'git_branch', 'git_path', 'checksum',
            'is_validated', 'validation_message', 'syntax_check_passed',
            'parameters', 'required_vars', 'default_vars', 'ansible_version',
            'required_collections', 'required_roles', 'execution_count',
            'success_count', 'last_executed', 'success_rate',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'checksum', 'is_validated', 'validation_message', 'syntax_check_passed',
            'execution_count', 'success_count', 'last_executed',
            'created_by', 'created_at', 'updated_at'
        ]

    def get_success_rate(self, obj):
        """计算成功率"""
        if obj.execution_count > 0:
            return round((obj.success_count / obj.execution_count) * 100, 2)
        return 0

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


class AnsibleHostSerializer(serializers.ModelSerializer):
    """Ansible主机序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    group_names = serializers.SerializerMethodField()
    
    class Meta:
        model = AnsibleHost
        fields = [
            'id', 'hostname', 'ip_address', 'port', 'username',
            'connection_type', 'become_method', 'status', 'status_display',
            'last_check', 'check_message', 'os_family', 'os_distribution',
            'os_version', 'ansible_facts', 'tags', 'group_names',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'status', 'last_check', 'check_message', 'os_family',
            'os_distribution', 'os_version', 'ansible_facts',
            'created_by', 'created_at', 'updated_at'
        ]

    def get_group_names(self, obj):
        return [group.name for group in obj.groups.all()]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AnsibleHostGroupSerializer(serializers.ModelSerializer):
    """Ansible主机组序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    host_count = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = AnsibleHostGroup
        fields = [
            'id', 'name', 'description', 'parent', 'parent_name',
            'variables', 'host_count', 'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_host_count(self, obj):
        return obj.ansiblehost_set.count()

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AnsibleInventoryVersionSerializer(serializers.ModelSerializer):
    """Ansible Inventory版本序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    inventory_name = serializers.CharField(source='inventory.name', read_only=True)
    
    class Meta:
        model = AnsibleInventoryVersion
        fields = [
            'id', 'inventory', 'inventory_name', 'version', 'content',
            'checksum', 'changelog', 'created_by', 'created_by_username',
            'created_at'
        ]
        read_only_fields = ['created_by', 'created_at']


class AnsiblePlaybookVersionSerializer(serializers.ModelSerializer):
    """Ansible Playbook版本序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    playbook_name = serializers.CharField(source='playbook.name', read_only=True)
    
    class Meta:
        model = AnsiblePlaybookVersion
        fields = [
            'id', 'playbook', 'playbook_name', 'version', 'content',
            'checksum', 'changelog', 'is_release', 'created_by',
            'created_by_username', 'created_at'
        ]
        read_only_fields = ['created_by', 'created_at']
