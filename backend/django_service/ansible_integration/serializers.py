from rest_framework import serializers
from .models import (
    AnsibleInventory, AnsiblePlaybook, AnsibleCredential, AnsibleExecution,
    AnsibleHost, AnsibleHostGroup, AnsibleInventoryVersion, AnsiblePlaybookVersion,
    InventoryHost, InventoryGroup
)


class AnsibleInventorySerializer(serializers.ModelSerializer):
    """Ansible主机清单序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    hosts_count = serializers.SerializerMethodField()
    active_hosts_count = serializers.SerializerMethodField()
    groups_count = serializers.SerializerMethodField()
    active_groups_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AnsibleInventory
        fields = [
            'id', 'name', 'description', 'content', 'format_type', 'source_type',
            'source_type_display', 'file_path', 'git_url', 'git_branch',
            'dynamic_script', 'version', 'checksum', 'is_validated',
            'validation_message', 'hosts_count', 'active_hosts_count',
            'groups_count', 'active_groups_count',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'checksum', 'is_validated', 'validation_message',
            'hosts_count', 'active_hosts_count', 'groups_count', 'active_groups_count',
            'created_by', 'created_at', 'updated_at'
        ]

    def get_hosts_count(self, obj):
        """获取关联主机总数"""
        return obj.hosts.count()

    def get_active_hosts_count(self, obj):
        """获取激活主机数量"""
        return obj.hosts.filter(inventoryhost__is_active=True).count()

    def get_groups_count(self, obj):
        """获取关联主机组总数"""
        return InventoryGroup.objects.filter(inventory=obj).count()

    def get_active_groups_count(self, obj):
        """获取激活主机组数量"""
        return InventoryGroup.objects.filter(inventory=obj, is_active=True).count()

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
    groups = serializers.SerializerMethodField()
    
    # 临时认证字段（仅用于创建，不返回）
    temp_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    temp_ssh_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = AnsibleHost
        fields = [
            'id', 'hostname', 'ip_address', 'port', 'username',
            'connection_type', 'become_method', 'credential', 'status', 'status_display',
            'last_check', 'check_message', 'os_family', 'os_distribution',
            'os_version', 'ansible_facts', 'tags', 'group_names', 'groups',
            'created_by', 'created_by_username', 'created_at', 'updated_at',
            'temp_password', 'temp_ssh_key'
        ]
        read_only_fields = [
            'status', 'last_check', 'check_message', 'os_family',
            'os_distribution', 'os_version', 'ansible_facts',
            'created_by', 'created_at', 'updated_at'
        ]

    def get_group_names(self, obj):
        return [group.name for group in obj.groups.all()]

    def get_groups(self, obj):
        """获取主机所属的完整组信息"""
        return [
            {
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'parent_name': group.parent.name if group.parent else None
            }
            for group in obj.groups.all()
        ]

    def create(self, validated_data):
        # 提取临时认证数据
        temp_password = validated_data.pop('temp_password', None)
        temp_ssh_key = validated_data.pop('temp_ssh_key', None)
        
        validated_data['created_by'] = self.context['request'].user
        host = super().create(validated_data)
        
        # 保存临时认证信息到主机
        if temp_password:
            host.set_temp_password(temp_password)
        if temp_ssh_key:
            host.set_temp_ssh_key(temp_ssh_key)
        
        return host


class AnsibleHostGroupSerializer(serializers.ModelSerializer):
    """Ansible主机组序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    host_count = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    children = serializers.SerializerMethodField()
    hosts_count = serializers.SerializerMethodField()  # 兼容前端字段名
    
    class Meta:
        model = AnsibleHostGroup
        fields = [
            'id', 'name', 'description', 'parent', 'parent_name',
            'variables', 'host_count', 'hosts_count', 'children',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_host_count(self, obj):
        return obj.ansiblehostgroupmembership_set.count()

    def get_hosts_count(self, obj):
        """兼容前端的hosts_count字段名"""
        return obj.ansiblehostgroupmembership_set.count()

    def get_children(self, obj):
        """获取子组信息"""
        return [
            {
                'id': child.id,
                'name': child.name,
                'description': child.description,
                'hosts_count': child.ansiblehostgroupmembership_set.count()
            }
            for child in obj.children.all()
        ]

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


class InventoryHostSerializer(serializers.ModelSerializer):
    """Inventory与Host关联序列化器"""
    inventory_name_display = serializers.CharField(source='inventory.name', read_only=True)
    host_hostname = serializers.CharField(source='host.hostname', read_only=True)
    host_ip_address = serializers.CharField(source='host.ip_address', read_only=True)
    host_status = serializers.CharField(source='host.status', read_only=True)
    
    class Meta:
        from .models import InventoryHost
        model = InventoryHost
        fields = [
            'id', 'inventory', 'host', 'inventory_name', 'host_variables',
            'is_active', 'inventory_name_display', 'host_hostname',
            'host_ip_address', 'host_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class InventoryHostCreateSerializer(serializers.Serializer):
    """批量添加主机到Inventory的序列化器"""
    host_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text='主机ID列表'
    )
    inventory_names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        help_text='在清单中的名称列表，与host_ids对应'
    )
    host_variables = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
        help_text='主机变量列表，与host_ids对应'
    )
    is_active = serializers.BooleanField(default=True, help_text='是否激活')

    def validate(self, data):
        host_ids = data['host_ids']
        inventory_names = data.get('inventory_names', [])
        host_variables = data.get('host_variables', [])
        
        # 验证列表长度匹配
        if inventory_names and len(inventory_names) != len(host_ids):
            raise serializers.ValidationError(
                'inventory_names列表长度必须与host_ids匹配'
            )
        
        if host_variables and len(host_variables) != len(host_ids):
            raise serializers.ValidationError(
                'host_variables列表长度必须与host_ids匹配'
            )
        
        return data


class InventoryGroupSerializer(serializers.ModelSerializer):
    """Inventory主机组关联序列化器"""
    group_name = serializers.CharField(source='group.name', read_only=True)
    group_description = serializers.CharField(source='group.description', read_only=True)
    
    class Meta:
        model = InventoryGroup
        fields = [
            'id', 'inventory', 'group', 'group_name', 'group_description',
            'inventory_name', 'group_variables', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class InventoryGroupBatchSerializer(serializers.Serializer):
    """批量管理Inventory主机组关联的序列化器"""
    inventory_id = serializers.IntegerField(help_text='主机清单ID')
    group_ids = serializers.ListField(
        child=serializers.IntegerField(),  
        help_text='主机组ID列表'
    )
    inventory_names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        help_text='在清单中的组名列表，与group_ids对应'
    )
    group_variables = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
        help_text='主机组变量列表，与group_ids对应'
    )
    is_active = serializers.BooleanField(default=True, help_text='是否激活')

    def validate(self, data):
        group_ids = data['group_ids']
        inventory_names = data.get('inventory_names', [])
        group_variables = data.get('group_variables', [])
        
        # 验证列表长度匹配
        if inventory_names and len(inventory_names) != len(group_ids):
            raise serializers.ValidationError(
                'inventory_names列表长度必须与group_ids匹配'
            )
        
        if group_variables and len(group_variables) != len(group_ids):
            raise serializers.ValidationError(
                'group_variables列表长度必须与group_ids匹配'
            )
        
        return data
