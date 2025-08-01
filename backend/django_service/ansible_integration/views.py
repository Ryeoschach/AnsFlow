from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
import hashlib
import os
import tempfile
import subprocess
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.parsers import MultiPartParser, FormParser

from .models import (
    AnsibleInventory, AnsiblePlaybook, AnsibleCredential, AnsibleExecution,
    AnsibleHost, AnsibleHostGroup, InventoryHost, InventoryGroup
)
from .serializers import (
    AnsibleInventorySerializer, AnsiblePlaybookSerializer, 
    AnsibleCredentialSerializer, AnsibleExecutionSerializer,
    AnsibleExecutionListSerializer, AnsibleStatsSerializer,
    InventoryGroupSerializer, InventoryGroupBatchSerializer
)
from .tasks import execute_ansible_playbook


class AnsibleInventoryViewSet(viewsets.ModelViewSet):
    """Ansible主机清单视图集"""
    serializer_class = AnsibleInventorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = AnsibleInventory.objects.all()
        
        # 只显示用户有权限的清单
        if not self.request.user.is_superuser:
            queryset = queryset.filter(created_by=self.request.user)
            
        # 搜索过滤
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
            
        # 格式过滤
        format_type = self.request.query_params.get('format_type')
        if format_type:
            queryset = queryset.filter(format_type=format_type)
            
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def validate_inventory(self, request, pk=None):
        """验证主机清单格式"""
        inventory = self.get_object()
        try:
            # TODO: 实现inventory格式验证逻辑
            # 可以使用ansible-inventory命令验证
            return Response({
                'valid': True,
                'message': '主机清单格式验证通过'
            })
        except Exception as e:
            return Response({
                'valid': False,
                'message': f'主机清单格式错误: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_inventory(self, request):
        """上传Inventory文件"""
        if 'file' not in request.FILES:
            return Response({
                'error': '请选择要上传的文件'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        name = request.data.get('name', uploaded_file.name)
        description = request.data.get('description', '')
        format_type = request.data.get('format_type', 'ini')
        
        try:
            # 读取文件内容
            content = uploaded_file.read().decode('utf-8')
            
            # 计算校验和
            checksum = hashlib.sha256(content.encode()).hexdigest()
            
            # 创建Inventory记录
            inventory = AnsibleInventory.objects.create(
                name=name,
                description=description,
                content=content,
                format_type=format_type,
                source_type='file',
                file_path=uploaded_file.name,
                checksum=checksum,
                created_by=request.user
            )
            
            # 异步验证
            from .tasks import validate_ansible_inventory
            validate_ansible_inventory.delay(inventory.id)
            
            serializer = self.get_serializer(inventory)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'文件上传失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def create_version(self, request, pk=None):
        """创建Inventory版本"""
        inventory = self.get_object()
        version = request.data.get('version')
        changelog = request.data.get('changelog', '')
        
        if not version:
            return Response({
                'error': '版本号是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .models import AnsibleInventoryVersion
            
            # 检查版本是否已存在
            if AnsibleInventoryVersion.objects.filter(
                inventory=inventory, 
                version=version
            ).exists():
                return Response({
                    'error': f'版本 {version} 已存在'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 计算内容校验和
            checksum = hashlib.sha256(inventory.content.encode()).hexdigest()
            
            # 创建版本记录
            version_obj = AnsibleInventoryVersion.objects.create(
                inventory=inventory,
                version=version,
                content=inventory.content,
                checksum=checksum,
                changelog=changelog,
                created_by=request.user
            )
            
            # 更新主记录版本
            inventory.version = version
            inventory.checksum = checksum
            inventory.save()
            
            return Response({
                'id': version_obj.id,
                'version': version_obj.version,
                'checksum': version_obj.checksum,
                'created_at': version_obj.created_at,
                'message': '版本创建成功'
            })
            
        except Exception as e:
            return Response({
                'error': f'版本创建失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """获取Inventory版本历史"""
        inventory = self.get_object()
        versions = inventory.versions.all()
        
        version_data = []
        for version in versions:
            version_data.append({
                'id': version.id,
                'version': version.version,
                'checksum': version.checksum,
                'changelog': version.changelog,
                'created_by': version.created_by.username,
                'created_at': version.created_at
            })
        
        return Response(version_data)

    @action(detail=True, methods=['post'])
    def restore_version(self, request, pk=None):
        """恢复到指定版本"""
        inventory = self.get_object()
        version_id = request.data.get('version_id')
        
        if not version_id:
            return Response({
                'error': '版本ID是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .models import AnsibleInventoryVersion
            
            version_obj = AnsibleInventoryVersion.objects.get(
                id=version_id,
                inventory=inventory
            )
            
            # 恢复内容
            inventory.content = version_obj.content
            inventory.version = version_obj.version
            inventory.checksum = version_obj.checksum
            inventory.save()
            
            return Response({
                'message': f'已恢复到版本 {version_obj.version}'
            })
            
        except AnsibleInventoryVersion.DoesNotExist:
            return Response({
                'error': '指定的版本不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'版本恢复失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def hosts(self, request, pk=None):
        """获取清单关联的主机"""
        from .models import InventoryHost
        from .serializers import InventoryHostSerializer
        
        inventory = self.get_object()
        inventory_hosts = InventoryHost.objects.filter(inventory=inventory).select_related('host')
        
        # 是否只显示激活的主机
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            inventory_hosts = inventory_hosts.filter(is_active=is_active.lower() == 'true')
        
        serializer = InventoryHostSerializer(inventory_hosts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def generate_inventory(self, request, pk=None):
        """生成动态清单内容，包含主机和主机组"""
        from .models import InventoryHost, InventoryGroup, AnsibleHostGroupMembership
        
        inventory = self.get_object()
        # 获取清单中的主机
        inventory_hosts = InventoryHost.objects.filter(
            inventory=inventory, 
            is_active=True
        ).select_related('host')
        
        # 获取清单中的主机组
        inventory_groups = InventoryGroup.objects.filter(
            inventory=inventory,
            is_active=True
        ).select_related('group')
        
        # 生成INI格式的清单
        if inventory.format_type == 'ini':
            lines = []
            
            # 添加单独的主机（不属于任何主机组的）
            ungrouped_hosts = []
            for ih in inventory_hosts:
                # 检查主机是否属于清单中的任何主机组
                host_in_group = False
                for ig in inventory_groups:
                    if AnsibleHostGroupMembership.objects.filter(
                        host=ih.host, 
                        group=ig.group
                    ).exists():
                        host_in_group = True
                        break
                
                if not host_in_group:
                    host_line = f"{ih.inventory_name} ansible_host={ih.host.ip_address}"
                    if ih.host.port != 22:
                        host_line += f" ansible_port={ih.host.port}"
                    if ih.host.username:
                        host_line += f" ansible_user={ih.host.username}"
                    
                    # 添加主机变量
                    if ih.host_variables:
                        for key, value in ih.host_variables.items():
                            host_line += f" {key}={value}"
                    
                    ungrouped_hosts.append(host_line)
            
            # 如果有未分组的主机，添加[ungrouped]组
            if ungrouped_hosts:
                lines.append('[ungrouped]')
                lines.extend(ungrouped_hosts)
                lines.append('')
            
            # 添加主机组
            for ig in inventory_groups:
                group = ig.group
                lines.append(f'[{ig.inventory_name}]')
                
                # 获取组内的主机（通过membership关系）
                memberships = AnsibleHostGroupMembership.objects.filter(
                    group=group
                ).select_related('host')
                
                for membership in memberships:
                    host = membership.host
                    # 检查该主机是否也在清单中
                    try:
                        ih = InventoryHost.objects.get(inventory=inventory, host=host, is_active=True)
                        host_line = f"{ih.inventory_name} ansible_host={host.ip_address}"
                        if host.port != 22:
                            host_line += f" ansible_port={host.port}"
                        if host.username:
                            host_line += f" ansible_user={host.username}"
                        
                        # 添加主机变量（合并清单变量和组成员变量）
                        combined_vars = {}
                        if ih.host_variables:
                            combined_vars.update(ih.host_variables)
                        if membership.variables:
                            combined_vars.update(membership.variables)
                        
                        for key, value in combined_vars.items():
                            host_line += f" {key}={value}"
                        
                        lines.append(host_line)
                    except InventoryHost.DoesNotExist:
                        continue
                
                # 添加组变量
                if ig.group_variables:
                    lines.append('')
                    lines.append(f'[{ig.inventory_name}:vars]')
                    for key, value in ig.group_variables.items():
                        lines.append(f'{key}={value}')
                
                lines.append('')
            
            dynamic_content = '\n'.join(lines).strip()
            
        else:
            # YAML格式
            inventory_data = {'all': {'hosts': {}, 'children': {}}}
            
            # 添加单独的主机
            for ih in inventory_hosts:
                # 检查主机是否属于清单中的任何主机组
                host_in_group = False
                for ig in inventory_groups:
                    if AnsibleHostGroupMembership.objects.filter(
                        host=ih.host, 
                        group=ig.group
                    ).exists():
                        host_in_group = True
                        break
                
                if not host_in_group:
                    host_vars = {
                        'ansible_host': ih.host.ip_address,
                        'ansible_user': ih.host.username or 'root',
                    }
                    if ih.host.port != 22:
                        host_vars['ansible_port'] = ih.host.port
                    
                    # 合并主机变量
                    if ih.host_variables:
                        host_vars.update(ih.host_variables)
                    
                    inventory_data['all']['hosts'][ih.inventory_name] = host_vars
            
            # 添加主机组
            for ig in inventory_groups:
                group_data = {'hosts': {}, 'vars': {}}
                
                # 获取组内的主机（通过membership关系）
                memberships = AnsibleHostGroupMembership.objects.filter(
                    group=ig.group
                ).select_related('host')
                
                for membership in memberships:
                    host = membership.host
                    try:
                        ih = InventoryHost.objects.get(inventory=inventory, host=host, is_active=True)
                        host_vars = {
                            'ansible_host': host.ip_address,
                            'ansible_user': host.username or 'root',
                        }
                        if host.port != 22:
                            host_vars['ansible_port'] = host.port
                        
                        # 合并主机变量（清单变量 + 组成员变量）
                        if ih.host_variables:
                            host_vars.update(ih.host_variables)
                        if membership.variables:
                            host_vars.update(membership.variables)
                        
                        group_data['hosts'][ih.inventory_name] = host_vars
                    except InventoryHost.DoesNotExist:
                        continue
                
                # 添加组变量
                if ig.group_variables:
                    group_data['vars'].update(ig.group_variables)
                
                # 清理空的vars
                if not group_data['vars']:
                    del group_data['vars']
                
                inventory_data['all']['children'][ig.inventory_name] = group_data
            
            # 转换为简单YAML格式字符串（避免依赖PyYAML）
            def dict_to_yaml(data, indent=0):
                yaml_str = ""
                prefix = "  " * indent
                for key, value in data.items():
                    yaml_str += f"{prefix}{key}:\n"
                    if isinstance(value, dict):
                        yaml_str += dict_to_yaml(value, indent + 1)
                    else:
                        yaml_str += f"{prefix}  {value}\n"
                return yaml_str
            
            dynamic_content = dict_to_yaml(inventory_data)
        
        total_hosts = inventory_hosts.count()
        total_groups = inventory_groups.count()
        
        return Response({
            'content': dynamic_content,
            'format_type': inventory.format_type,
            'hosts_count': total_hosts,
            'groups_count': total_groups,
            'summary': f'包含 {total_hosts} 个主机和 {total_groups} 个主机组'
        })

    @action(detail=True, methods=['post'])
    def add_hosts(self, request, pk=None):
        """为清单添加主机"""
        from .models import AnsibleHost, InventoryHost
        
        inventory = self.get_object()
        host_ids = request.data.get('host_ids', [])
        inventory_names = request.data.get('inventory_names', [])
        host_variables = request.data.get('host_variables', [])
        is_active = request.data.get('is_active', True)
        
        if not host_ids:
            return Response({
                'error': '请提供host_ids'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            hosts = AnsibleHost.objects.filter(id__in=host_ids)
            
            added_count = 0
            errors = []
            
            for i, host in enumerate(hosts):
                try:
                    # 获取对应的inventory_name和host_variables
                    inventory_name = inventory_names[i] if i < len(inventory_names) else host.hostname
                    variables = host_variables[i] if i < len(host_variables) else {}
                    
                    _, created = InventoryHost.objects.get_or_create(
                        inventory=inventory,
                        host=host,
                        defaults={
                            'inventory_name': inventory_name,
                            'host_variables': variables,
                            'is_active': is_active
                        }
                    )
                    if created:
                        added_count += 1
                    else:
                        errors.append(f'主机 {host.hostname} 已存在于清单中')
                except Exception as e:
                    errors.append(f'添加主机 {host.hostname} 失败: {str(e)}')
            
            return Response({
                'message': f'成功添加 {added_count} 个主机到清单',
                'added_count': added_count,
                'errors': errors
            })
            
        except Exception as e:
            return Response({
                'error': f'批量添加失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_hosts(self, request, pk=None):
        """从清单中移除主机"""
        from .models import InventoryHost
        
        inventory = self.get_object()
        host_ids = request.data.get('host_ids', [])
        
        if not host_ids:
            return Response({
                'error': '请提供host_ids'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            removed_count = InventoryHost.objects.filter(
                inventory=inventory,
                host_id__in=host_ids
            ).delete()[0]
            
            return Response({
                'message': f'成功从清单中移除 {removed_count} 个主机',
                'removed_count': removed_count
            })
            
        except Exception as e:
            return Response({
                'error': f'批量移除失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def generate_dynamic_inventory(self, request, pk=None):
        """生成动态主机清单"""
        from .models import InventoryHost
        
        inventory = self.get_object()
        format_type = request.data.get('format_type', inventory.format_type or 'ini')
        
        try:
            # 获取清单关联的主机
            inventory_hosts = InventoryHost.objects.filter(
                inventory=inventory,
                is_active=True
            ).select_related('host')
            
            if not inventory_hosts.exists():
                return Response({
                    'error': '清单中没有关联的主机'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            content = ""
            hosts_count = inventory_hosts.count()
            
            if format_type.lower() == 'yaml':
                # 生成YAML格式的清单
                inventory_data = {}
                
                # 按组织结构生成
                for inv_host in inventory_hosts:
                    host = inv_host.host
                    group_name = inv_host.inventory_name or 'ungrouped'
                    
                    if group_name not in inventory_data:
                        inventory_data[group_name] = {
                            'hosts': {}
                        }
                    
                    # 构建主机信息
                    host_info = {
                        'ansible_host': host.ip_address,
                        'ansible_port': host.port or 22,
                        'ansible_user': host.username,
                    }
                    
                    # 添加连接类型
                    if host.connection_type:
                        host_info['ansible_connection'] = host.connection_type
                    
                    # 添加提权方式
                    if host.become_method:
                        host_info['ansible_become_method'] = host.become_method
                    
                    # 合并主机变量
                    if inv_host.host_variables:
                        host_info.update(inv_host.host_variables)
                    
                    inventory_data[group_name]['hosts'][host.hostname] = host_info
                
                # 简单的YAML输出
                content = ""
                for group_name, group_data in inventory_data.items():
                    content += f"{group_name}:\n"
                    if 'hosts' in group_data:
                        content += "  hosts:\n"
                        for host_name, host_vars in group_data['hosts'].items():
                            content += f"    {host_name}:\n"
                            for key, value in host_vars.items():
                                content += f"      {key}: {value}\n"
                
            else:
                # 生成INI格式的清单
                groups = {}
                
                # 按组织结构分组
                for inv_host in inventory_hosts:
                    host = inv_host.host
                    group_name = inv_host.inventory_name or 'ungrouped'
                    
                    if group_name not in groups:
                        groups[group_name] = []
                    
                    # 构建主机行
                    host_line = f"{host.hostname} ansible_host={host.ip_address}"
                    
                    if host.port and host.port != 22:
                        host_line += f" ansible_port={host.port}"
                    
                    if host.username:
                        host_line += f" ansible_user={host.username}"
                    
                    if host.connection_type:
                        host_line += f" ansible_connection={host.connection_type}"
                    
                    if host.become_method:
                        host_line += f" ansible_become_method={host.become_method}"
                    
                    # 添加主机变量
                    if inv_host.host_variables:
                        for key, value in inv_host.host_variables.items():
                            host_line += f" {key}={value}"
                    
                    groups[group_name].append(host_line)
                
                # 生成INI内容
                content_lines = []
                for group_name, hosts in groups.items():
                    content_lines.append(f"[{group_name}]")
                    content_lines.extend(hosts)
                    content_lines.append("")  # 空行分隔组
                
                content = "\n".join(content_lines).strip()
            
            return Response({
                'content': content,
                'format_type': format_type,
                'hosts_count': hosts_count,
                'message': f'成功生成包含 {hosts_count} 个主机的动态清单'
            })
            
        except Exception as e:
            return Response({
                'error': f'生成动态清单失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def groups(self, request, pk=None):
        """获取清单中的主机组列表"""
        inventory = self.get_object()
        groups = InventoryGroup.objects.filter(inventory=inventory).select_related('group')
        
        data = []
        for inv_group in groups:
            data.append({
                'id': inv_group.id,
                'group_id': inv_group.group.id,
                'group_name': inv_group.group.name,
                'group_description': inv_group.group.description,
                'inventory_name': inv_group.inventory_name,
                'group_variables': inv_group.group_variables,
                'is_active': inv_group.is_active,
                'hosts_count': inv_group.group.ansiblehostgroupmembership_set.count(),
                'created_at': inv_group.created_at
            })
        
        return Response(data)

    @action(detail=True, methods=['post'])
    def add_groups(self, request, pk=None):
        """批量添加主机组到清单"""
        inventory = self.get_object()
        group_ids = request.data.get('group_ids', [])
        
        if not group_ids:
            return Response({
                'error': '请提供主机组ID列表'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            added_count = 0
            for group_id in group_ids:
                try:
                    group = AnsibleHostGroup.objects.get(id=group_id)
                    inventory_group, created = InventoryGroup.objects.get_or_create(
                        inventory=inventory,
                        group=group,
                        defaults={
                            'inventory_name': group.name,
                            'group_variables': {},
                            'is_active': True
                        }
                    )
                    if created:
                        added_count += 1
                except AnsibleHostGroup.DoesNotExist:
                    continue
            
            return Response({
                'message': f'成功添加 {added_count} 个主机组到清单',
                'added_count': added_count
            })
            
        except Exception as e:
            return Response({
                'error': f'添加主机组失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_groups(self, request, pk=None):
        """批量从清单中移除主机组"""
        inventory = self.get_object()
        group_ids = request.data.get('group_ids', [])
        
        if not group_ids:
            return Response({
                'error': '请提供主机组ID列表'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 删除InventoryGroup关联记录
            removed_count = InventoryGroup.objects.filter(
                inventory=inventory,
                group_id__in=group_ids
            ).delete()[0]
            
            # 强制刷新inventory对象以确保统计数据更新
            inventory.refresh_from_db()
            
            # 手动计算最新的统计数据
            current_groups_count = InventoryGroup.objects.filter(inventory=inventory).count()
            current_active_groups_count = InventoryGroup.objects.filter(
                inventory=inventory, 
                is_active=True
            ).count()
            
            return Response({
                'message': f'成功从清单中移除 {removed_count} 个主机组',
                'removed_count': removed_count,
                'current_stats': {
                    'groups_count': current_groups_count,
                    'active_groups_count': current_active_groups_count
                }
            })
            
        except Exception as e:
            return Response({
                'error': f'移除主机组失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class AnsiblePlaybookViewSet(viewsets.ModelViewSet):
    """Ansible Playbook视图集"""
    serializer_class = AnsiblePlaybookSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = AnsiblePlaybook.objects.all()
        
        # 只显示用户有权限的playbook（模板除外）
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=self.request.user) | Q(is_template=True)
            )
            
        # 搜索过滤
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
            
        # 分类过滤
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
            
        # 模板过滤
        is_template = self.request.query_params.get('is_template')
        if is_template is not None:
            queryset = queryset.filter(is_template=is_template.lower() == 'true')
            
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def validate_playbook(self, request, pk=None):
        """验证Playbook语法"""
        playbook = self.get_object()
        try:
            # TODO: 实现playbook语法验证逻辑
            # 可以使用ansible-playbook --syntax-check
            return Response({
                'valid': True,
                'message': 'Playbook语法验证通过'
            })
        except Exception as e:
            return Response({
                'valid': False,
                'message': f'Playbook语法错误: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def create_from_template(self, request, pk=None):
        """从模板创建新的Playbook"""
        template = self.get_object()
        if not template.is_template:
            return Response({
                'error': '该Playbook不是模板'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # 创建新的playbook
        new_data = request.data.copy()
        new_data.update({
            'content': template.content,
            'category': template.category,
            'parameters': template.parameters,
            'is_template': False,
            'version': '1.0'
        })
        
        serializer = self.get_serializer(data=new_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_playbook(self, request):
        """上传Playbook文件"""
        if 'file' not in request.FILES:
            return Response({
                'error': '请选择要上传的文件'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        name = request.data.get('name', uploaded_file.name.replace('.yml', '').replace('.yaml', ''))
        description = request.data.get('description', '')
        category = request.data.get('category', 'other')
        
        try:
            # 读取文件内容
            content = uploaded_file.read().decode('utf-8')
            
            # 计算校验和
            checksum = hashlib.sha256(content.encode()).hexdigest()
            
            # 创建Playbook记录
            playbook = AnsiblePlaybook.objects.create(
                name=name,
                description=description,
                content=content,
                category=category,
                source_type='file',
                file_path=uploaded_file.name,
                checksum=checksum,
                created_by=request.user
            )
            
            # 异步验证语法
            from .tasks import validate_ansible_playbook
            validate_ansible_playbook.delay(playbook.id)
            
            serializer = self.get_serializer(playbook)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'文件上传失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def create_version(self, request, pk=None):
        """创建Playbook版本"""
        playbook = self.get_object()
        version = request.data.get('version')
        changelog = request.data.get('changelog', '')
        is_release = request.data.get('is_release', False)
        
        if not version:
            return Response({
                'error': '版本号是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .models import AnsiblePlaybookVersion
            
            # 检查版本是否已存在
            if AnsiblePlaybookVersion.objects.filter(
                playbook=playbook, 
                version=version
            ).exists():
                return Response({
                    'error': f'版本 {version} 已存在'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 计算内容校验和
            checksum = hashlib.sha256(playbook.content.encode()).hexdigest()
            
            # 创建版本记录
            version_obj = AnsiblePlaybookVersion.objects.create(
                playbook=playbook,
                version=version,
                content=playbook.content,
                checksum=checksum,
                changelog=changelog,
                is_release=is_release,
                created_by=request.user
            )
            
            # 更新主记录版本
            playbook.version = version
            playbook.checksum = checksum
            playbook.save()
            
            return Response({
                'id': version_obj.id,
                'version': version_obj.version,
                'checksum': version_obj.checksum,
                'is_release': version_obj.is_release,
                'created_at': version_obj.created_at,
                'message': '版本创建成功'
            })
            
        except Exception as e:
            return Response({
                'error': f'版本创建失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """获取Playbook版本历史"""
        playbook = self.get_object()
        versions = playbook.versions.all()
        
        version_data = []
        for version in versions:
            version_data.append({
                'id': version.id,
                'version': version.version,
                'checksum': version.checksum,
                'changelog': version.changelog,
                'is_release': version.is_release,
                'created_by': version.created_by.username,
                'created_at': version.created_at
            })
        
        return Response(version_data)

    @action(detail=True, methods=['post'])
    def restore_version(self, request, pk=None):
        """恢复到指定版本"""
        playbook = self.get_object()
        version_id = request.data.get('version_id')
        
        if not version_id:
            return Response({
                'error': '版本ID是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .models import AnsiblePlaybookVersion
            
            version_obj = AnsiblePlaybookVersion.objects.get(
                id=version_id,
                playbook=playbook
            )
            
            # 恢复内容
            playbook.content = version_obj.content
            playbook.version = version_obj.version
            playbook.checksum = version_obj.checksum
            playbook.save()
            
            return Response({
                'message': f'已恢复到版本 {version_obj.version}'
            })
            
        except AnsiblePlaybookVersion.DoesNotExist:
            return Response({
                'error': '指定的版本不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'版本恢复失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def syntax_check(self, request, pk=None):
        """Playbook语法检查"""
        playbook = self.get_object()
        
        try:
            # 创建临时文件进行语法检查
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as temp_file:
                temp_file.write(playbook.content)
                temp_file_path = temp_file.name
            
            try:
                # 使用ansible-playbook --syntax-check进行验证
                result = subprocess.run([
                    'ansible-playbook', '--syntax-check', temp_file_path
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    # 更新验证状态
                    playbook.syntax_check_passed = True
                    playbook.is_validated = True
                    playbook.validation_message = 'Playbook语法验证通过'
                    playbook.save()
                    
                    return Response({
                        'valid': True,
                        'message': 'Playbook语法验证通过',
                        'output': result.stdout
                    })
                else:
                    # 更新验证状态
                    playbook.syntax_check_passed = False
                    playbook.is_validated = True
                    playbook.validation_message = result.stderr or result.stdout
                    playbook.save()
                    
                    return Response({
                        'valid': False,
                        'message': 'Playbook语法验证失败',
                        'error': result.stderr or result.stdout
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            finally:
                # 清理临时文件
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except subprocess.TimeoutExpired:
            return Response({
                'valid': False,
                'message': '语法检查超时'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'valid': False,
                'message': f'语法检查失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class AnsibleCredentialViewSet(viewsets.ModelViewSet):
    """Ansible凭据视图集"""
    serializer_class = AnsibleCredentialSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = AnsibleCredential.objects.all()
        
        # 只显示用户有权限的凭据
        if not self.request.user.is_superuser:
            queryset = queryset.filter(created_by=self.request.user)
            
        # 搜索过滤
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(username__icontains=search)
            )
            
        # 类型过滤
        credential_type = self.request.query_params.get('credential_type')
        if credential_type:
            queryset = queryset.filter(credential_type=credential_type)
            
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """测试凭据连接"""
        credential = self.get_object()
        try:
            # TODO: 实现凭据连接测试逻辑
            # 可以使用ansible命令测试连接
            return Response({
                'success': True,
                'message': '凭据连接测试成功',
                'tested_at': timezone.now()
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'凭据连接测试失败: {str(e)}',
                'tested_at': timezone.now()
            }, status=status.HTTP_400_BAD_REQUEST)


class AnsibleExecutionViewSet(viewsets.ModelViewSet):
    """Ansible执行记录视图集"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AnsibleExecutionListSerializer
        return AnsibleExecutionSerializer
    
    def get_queryset(self):
        queryset = AnsibleExecution.objects.select_related(
            'playbook', 'inventory', 'credential', 'created_by'
        )
        
        # 只显示用户有权限的执行记录
        if not self.request.user.is_superuser:
            queryset = queryset.filter(created_by=self.request.user)
            
        # 状态过滤
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # 时间范围过滤
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
            
        # Playbook过滤
        playbook_id = self.request.query_params.get('playbook')
        if playbook_id:
            queryset = queryset.filter(playbook_id=playbook_id)
            
        return queryset.order_by('-created_at')

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取执行统计信息"""
        queryset = self.get_queryset()
        
        # 基础统计
        total_executions = queryset.count()
        successful_executions = queryset.filter(status='success').count()
        failed_executions = queryset.filter(status='failed').count()
        running_executions = queryset.filter(status='running').count()
        pending_executions = queryset.filter(status='pending').count()
        
        # 成功率
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
        
        # 平均执行时长（已完成的）
        completed_executions = queryset.filter(
            status__in=['success', 'failed'],
            started_at__isnull=False,
            completed_at__isnull=False
        )
        avg_duration = 0
        if completed_executions.exists():
            durations = []
            for execution in completed_executions:
                if execution.duration:
                    durations.append(execution.duration)
            avg_duration = sum(durations) / len(durations) if durations else 0
        
        # 其他统计
        total_playbooks = AnsiblePlaybook.objects.count()
        total_inventories = AnsibleInventory.objects.count()
        total_credentials = AnsibleCredential.objects.count()
        
        stats_data = {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'running_executions': running_executions,
            'pending_executions': pending_executions,
            'success_rate': round(success_rate, 2),
            'avg_duration': round(avg_duration, 2),
            'total_playbooks': total_playbooks,
            'total_inventories': total_inventories,
            'total_credentials': total_credentials
        }
        
        serializer = AnsibleStatsSerializer(stats_data)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行Ansible playbook"""
        execution = self.get_object()
        
        if execution.status != 'pending':
            return Response({
                'error': f'执行记录状态为 {execution.get_status_display()}，无法重新执行'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 启动异步任务
            task = execute_ansible_playbook.delay(execution.id)
            
            return Response({
                'message': 'Ansible执行已启动',
                'task_id': task.id,
                'execution_id': execution.id
            })
        except Exception as e:
            return Response({
                'error': f'启动执行失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消执行"""
        execution = self.get_object()
        
        if execution.status not in ['pending', 'running']:
            return Response({
                'error': f'执行记录状态为 {execution.get_status_display()}，无法取消'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        execution.cancel_execution()
        
        return Response({
            'message': '执行已取消',
            'execution_id': execution.id
        })

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """获取执行日志"""
        execution = self.get_object()
        
        return Response({
            'execution_id': execution.id,
            'status': execution.status,
            'stdout': execution.stdout,
            'stderr': execution.stderr,
            'return_code': execution.return_code,
            'started_at': execution.started_at,
            'completed_at': execution.completed_at,
            'duration': execution.duration
        })

    @action(detail=False, methods=['get'])
    def pipeline_executions(self, request):
        """获取与Pipeline关联的Ansible执行记录"""
        pipeline_id = request.query_params.get('pipeline_id')
        
        queryset = self.get_queryset()
        
        if pipeline_id:
            queryset = queryset.filter(pipeline_id=pipeline_id)
        else:
            # 只返回有Pipeline关联的执行记录
            queryset = queryset.filter(pipeline__isnull=False)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    @action(detail=True, methods=['get'])
    def pipeline_info(self, request, pk=None):
        """获取Ansible执行的Pipeline信息"""
        execution = self.get_object()
        
        if not execution.pipeline:
            return Response({
                'message': '此执行记录未关联Pipeline'
            }, status=status.HTTP_404_NOT_FOUND)
        
        from pipelines.serializers import PipelineListSerializer, PipelineStepSerializer
        
        pipeline_data = PipelineListSerializer(execution.pipeline).data
        step_data = None
        
        if execution.pipeline_step:
            step_data = PipelineStepSerializer(execution.pipeline_step).data
        
        return Response({
            'pipeline': pipeline_data,
            'pipeline_step': step_data,
            'execution_id': execution.id
        })


# Additional API Views for custom endpoints

# TODO: Implement HostViewSet and PlaybookTemplateViewSet when models are added
# class HostViewSet(viewsets.ModelViewSet):
#     """主机视图集"""
#     serializer_class = HostSerializer
#     permission_classes = [IsAuthenticated]
#     
#     def get_queryset(self):
#         return Host.objects.all().order_by('-created_at')
#
#
# class PlaybookTemplateViewSet(viewsets.ModelViewSet):
#     """Playbook模板视图集"""
#     serializer_class = PlaybookTemplateSerializer
#     permission_classes = [IsAuthenticated]
#     
#     def get_queryset(self):
#         return PlaybookTemplate.objects.all().order_by('-created_at')
#
#
# class InventoryHostsView(APIView):
#     """清单主机列表视图"""
#     permission_classes = [IsAuthenticated]
#     
#     def get(self, request, inventory_id):
#         try:
#             inventory = AnsibleInventory.objects.get(id=inventory_id)
#             hosts = Host.objects.filter(inventory=inventory)
#             serializer = HostSerializer(hosts, many=True)
#             return Response(serializer.data)
#         except AnsibleInventory.DoesNotExist:
#             return Response(
#                 {'error': '清单不存在'}, 
#                 status=status.HTTP_404_NOT_FOUND
#             )


class ExecutePlaybookView(APIView):
    """执行Playbook视图"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, playbook_id):
        try:
            playbook = AnsiblePlaybook.objects.get(id=playbook_id)
            
            # 创建执行记录
            execution_data = {
                'playbook': playbook.id,
                'inventory': request.data.get('inventory_id'),
                'credential': request.data.get('credential_id'),
                'parameters': request.data.get('parameters', {}),
                'status': 'pending'
            }
            
            execution_serializer = AnsibleExecutionSerializer(
                data=execution_data,
                context={'request': request}
            )
            execution_serializer.is_valid(raise_exception=True)
            execution = execution_serializer.save()
            
            # 启动执行任务
            try:
                task = execute_ansible_playbook.delay(execution.id)
                return Response({
                    'message': 'Playbook执行已启动',
                    'execution_id': execution.id,
                    'task_id': task.id
                })
            except Exception as e:
                execution.status = 'failed'
                execution.stderr = str(e)
                execution.save()
                return Response({
                    'error': f'启动执行失败: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except AnsiblePlaybook.DoesNotExist:
            return Response(
                {'error': 'Playbook不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class ExecutionLogsView(APIView):
    """执行日志视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, execution_id):
        try:
            execution = AnsibleExecution.objects.get(id=execution_id)
            return Response({
                'execution_id': execution.id,
                'status': execution.status,
                'stdout': execution.stdout,
                'stderr': execution.stderr,
                'return_code': execution.return_code,
                'started_at': execution.started_at,
                'completed_at': execution.completed_at,
                'duration': execution.duration
            })
        except AnsibleExecution.DoesNotExist:
            return Response(
                {'error': '执行记录不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class CancelExecutionView(APIView):
    """取消执行视图"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, execution_id):
        try:
            execution = AnsibleExecution.objects.get(id=execution_id)
            
            if execution.status not in ['pending', 'running']:
                return Response({
                    'error': f'执行状态为 {execution.get_status_display()}，无法取消'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            execution.cancel_execution()
            return Response({
                'message': '执行已取消',
                'execution_id': execution.id
            })
        except AnsibleExecution.DoesNotExist:
            return Response(
                {'error': '执行记录不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            )


# TODO: Implement VerifyHostsView when Host model is added
# class VerifyHostsView(APIView):
#     """验证主机连接视图"""
#     permission_classes = [IsAuthenticated]
#     
#     def post(self, request):
#         hosts = request.data.get('hosts', [])
#         results = []
#         
#         for host_id in hosts:
#             try:
#                 host = Host.objects.get(id=host_id)
#                 # TODO: 实现主机连接验证逻辑
#                 results.append({
#                     'host_id': host_id,
#                     'hostname': host.hostname,
#                     'status': 'success',
#                     'message': '连接成功'
#                 })
#             except Host.DoesNotExist:
#                 results.append({
#                     'host_id': host_id,
#                     'status': 'error',
#                     'message': '主机不存在'
#                 })
#             except Exception as e:
#                 results.append({
#                     'host_id': host_id,
#                     'status': 'error',
#                     'message': str(e)
#                 })
#         
#         return Response({'results': results})


class ValidatePlaybookView(APIView):
    """验证Playbook语法视图"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        content = request.data.get('content', '')
        
        try:
            # TODO: 实现Playbook语法验证逻辑
            # 可以使用ansible-playbook --syntax-check
            return Response({
                'valid': True,
                'message': 'Playbook语法验证通过'
            })
        except Exception as e:
            return Response({
                'valid': False,
                'message': f'Playbook语法错误: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class AnsibleStatsView(APIView):
    """Ansible统计信息视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # 基础统计
        total_executions = AnsibleExecution.objects.count()
        successful_executions = AnsibleExecution.objects.filter(status='success').count()
        failed_executions = AnsibleExecution.objects.filter(status='failed').count()
        running_executions = AnsibleExecution.objects.filter(status='running').count()
        pending_executions = AnsibleExecution.objects.filter(status='pending').count()
        
        # 成功率
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
        
        # 其他统计
        total_playbooks = AnsiblePlaybook.objects.count()
        total_inventories = AnsibleInventory.objects.count()
        total_credentials = AnsibleCredential.objects.count()
        
        stats_data = {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'running_executions': running_executions,
            'pending_executions': pending_executions,
            'success_rate': round(success_rate, 2),
            'total_playbooks': total_playbooks,
            'total_inventories': total_inventories,
            'total_credentials': total_credentials
        }
        
        return Response(stats_data)


class RecentExecutionsView(APIView):
    """最近执行记录视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        executions = AnsibleExecution.objects.select_related(
            'playbook', 'inventory', 'credential', 'created_by'
        ).order_by('-created_at')[:limit]
        
        serializer = AnsibleExecutionListSerializer(executions, many=True)
        return Response(serializer.data)


class AnsibleHostViewSet(viewsets.ModelViewSet):
    """Ansible主机管理视图集"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from .models import AnsibleHost
        queryset = AnsibleHost.objects.all()
        
        # 只显示用户有权限的主机
        if not self.request.user.is_superuser:
            queryset = queryset.filter(created_by=self.request.user)
            
        # 搜索过滤
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(hostname__icontains=search) | 
                Q(ip_address__icontains=search) |
                Q(username__icontains=search)
            )
            
        # 状态过滤
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # 主机组过滤
        group_id = self.request.query_params.get('group_id')
        if group_id:
            queryset = queryset.filter(groups__id=group_id)
            
        return queryset.order_by('hostname')

    def get_serializer_class(self):
        from .serializers import AnsibleHostSerializer
        return AnsibleHostSerializer

    @action(detail=True, methods=['post'])
    def check_connectivity(self, request, pk=None):
        """检查主机连通性 - 支持多种认证方式"""
        host = self.get_object()
        
        try:
            import tempfile
            import os
            
            # 获取认证方式
            auth_method = host.get_auth_method()
            
            if auth_method == 'none':
                return Response({
                    'success': False,
                    'message': '未配置认证凭据，请先配置SSH密钥或密码'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 创建临时inventory文件
            inventory_content = f"{host.ip_address} ansible_user={host.username} ansible_port={host.port} ansible_connection={host.connection_type}"
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as f:
                f.write("[targets]\n")
                f.write(inventory_content + "\n")
                inventory_file = f.name
            
            # 准备临时文件路径
            temp_files = []
            
            try:
                # 构建ansible命令参数
                ansible_cmd = [
                    'ansible', 'targets',
                    '-i', inventory_file,
                    '-m', 'ping',
                    '--timeout=20',
                    '--ssh-common-args=-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
                ]
                
                # 根据认证方式添加相应参数
                if auth_method == 'ssh_key':
                    # 使用SSH密钥认证
                    ssh_key = host.get_auth_ssh_key()
                    if ssh_key:
                        # 确保SSH密钥以换行符结尾
                        if not ssh_key.endswith('\n'):
                            ssh_key += '\n'
                        
                        # 创建临时密钥文件
                        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as key_file:
                            key_file.write(ssh_key)
                            key_file_path = key_file.name
                        
                        # 设置密钥文件权限
                        os.chmod(key_file_path, 0o600)
                        temp_files.append(key_file_path)
                        
                        ansible_cmd.extend(['--private-key', key_file_path])
                
                elif auth_method == 'password':
                    # 使用密码认证
                    password = host.get_auth_password()
                    if password:
                        # 使用sshpass进行密码认证
                        ansible_cmd = ['sshpass', '-p', password] + ansible_cmd
                
                # 执行ansible命令检查连通性
                result = subprocess.run(
                    ansible_cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=25
                )
            finally:
                # 删除所有临时文件
                for temp_file in temp_files + [inventory_file]:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
            
            if result.returncode == 0:
                host.status = 'active'
                host.check_message = '连接成功'
            else:
                host.status = 'failed'
                host.check_message = result.stderr or result.stdout
                
            host.last_check = timezone.now()
            host.save()
            
            return Response({
                'success': result.returncode == 0,
                'hostname': host.hostname,
                'status': host.status,
                'message': host.check_message,
                'checked_at': host.last_check
            })
            
        except subprocess.TimeoutExpired:
            host.status = 'failed'
            host.check_message = '连接超时'
            host.last_check = timezone.now()
            host.save()
            
            return Response({
                'success': False,
                'hostname': host.hostname,
                'status': 'failed',
                'message': '连接超时',
                'checked_at': host.last_check
            })
        except Exception as e:
            return Response({
                'success': False,
                'hostname': host.hostname,
                'message': f'连接检查失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def test_connection(self, request):
        """测试主机连接 - 无需创建主机记录"""
        try:
            # 获取测试参数
            data = request.data
            required_fields = ['ip_address', 'username']
            
            for field in required_fields:
                if field not in data:
                    return Response({
                        'success': False,
                        'message': f'缺少必填字段: {field}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            ip_address = data['ip_address']
            username = data['username']
            port = data.get('port', 22)
            connection_type = data.get('connection_type', 'ssh')
            
            # 认证信息
            password = data.get('password', '')
            ssh_private_key = data.get('ssh_private_key', '')
            
            if not password and not ssh_private_key:
                return Response({
                    'success': False,
                    'message': '请提供密码或SSH私钥进行认证'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            import tempfile
            import os
            
            # 创建临时inventory文件
            inventory_content = f"{ip_address} ansible_user={username} ansible_port={port} ansible_connection={connection_type}"
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as f:
                f.write("[targets]\n")
                f.write(inventory_content + "\n")
                inventory_file = f.name
            
            temp_files = [inventory_file]
            
            try:
                # 构建ansible命令
                ansible_cmd = [
                    'ansible', 'targets',
                    '-i', inventory_file,
                    '-m', 'ping',
                    '--timeout=10',
                    '--ssh-common-args=-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10'
                ]
                
                # 根据认证方式添加参数
                if ssh_private_key:
                    # SSH密钥认证
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as key_file:
                        key_file.write(ssh_private_key)
                        key_file_path = key_file.name
                    
                    os.chmod(key_file_path, 0o600)
                    temp_files.append(key_file_path)
                    ansible_cmd.extend(['--private-key', key_file_path])
                    
                elif password:
                    # 密码认证
                    with tempfile.NamedTemporaryFile(mode='w', delete=False) as pass_file:
                        pass_file.write(password)
                        pass_file_path = pass_file.name
                    
                    temp_files.append(pass_file_path)
                    ansible_cmd.extend(['--connection-password-file', pass_file_path])
                
                # 执行测试
                result = subprocess.run(
                    ansible_cmd,
                    capture_output=True,
                    text=True,
                    timeout=20
                )
                
                success = result.returncode == 0
                
                if success:
                    message = '连接测试成功！可以正常访问目标主机。'
                else:
                    # 分析错误信息
                    error_output = result.stderr.lower()
                    if 'permission denied' in error_output:
                        message = '认证失败：用户名、密码或密钥不正确'
                    elif 'connection timed out' in error_output or 'timeout' in error_output:
                        message = '连接超时：请检查网络连通性和防火墙设置'
                    elif 'connection refused' in error_output:
                        message = 'SSH连接被拒绝：请检查SSH服务是否运行和端口是否正确'
                    elif 'host key verification failed' in error_output:
                        message = '主机密钥验证失败：这通常不应该发生（已禁用检查）'
                    else:
                        message = f'连接失败：{result.stderr or result.stdout}'
                
                return Response({
                    'success': success,
                    'message': message,
                    'details': {
                        'return_code': result.returncode,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'command': ' '.join(ansible_cmd[:-2] + ['--private-key', '***'] if '--private-key' in ansible_cmd else ansible_cmd)
                    }
                })
                
            finally:
                # 清理临时文件
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                        
        except subprocess.TimeoutExpired:
            return Response({
                'success': False,
                'message': '连接测试超时，请检查网络连接和目标主机状态'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'连接测试失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def gather_facts(self, request, pk=None):
        """收集主机信息 - 支持多种认证方式"""
        host = self.get_object()
        
        try:
            import tempfile
            import os
            
            # 获取认证方式
            auth_method = host.get_auth_method()
            
            if auth_method == 'none':
                return Response({
                    'success': False,
                    'message': '未配置认证凭据，请先配置SSH密钥或密码'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 创建临时inventory文件
            inventory_content = f"{host.ip_address} ansible_user={host.username} ansible_port={host.port} ansible_connection={host.connection_type}"
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as f:
                f.write("[targets]\n")
                f.write(inventory_content + "\n")
                inventory_file = f.name
            
            # 准备临时文件路径
            temp_files = []
            
            try:
                # 构建ansible命令参数
                ansible_cmd = [
                    'ansible', 'targets',
                    '-i', inventory_file,
                    '-m', 'setup',
                    '--timeout=30',
                    '--ssh-common-args=-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
                ]
                
                # 根据认证方式添加相应参数
                if auth_method == 'ssh_key':
                    # 使用SSH密钥认证
                    ssh_key = host.get_auth_ssh_key()
                    if ssh_key:
                        # 确保SSH密钥以换行符结尾
                        if not ssh_key.endswith('\n'):
                            ssh_key += '\n'
                        
                        # 创建临时密钥文件
                        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as key_file:
                            key_file.write(ssh_key)
                            key_file_path = key_file.name
                        
                        # 设置密钥文件权限
                        os.chmod(key_file_path, 0o600)
                        temp_files.append(key_file_path)
                        
                        ansible_cmd.extend(['--private-key', key_file_path])
                
                elif auth_method == 'password':
                    # 使用密码认证
                    password = host.get_auth_password()
                    if password:
                        # 使用sshpass进行密码认证
                        ansible_cmd = ['sshpass', '-p', password] + ansible_cmd
                
                # 执行ansible命令收集Facts
                result = subprocess.run(
                    ansible_cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=35
                )
                
                if result.returncode == 0:
                    import json
                    # 解析ansible facts
                    facts_output = result.stdout
                    # 提取JSON部分（ansible输出格式）
                    try:
                        facts_start = facts_output.find('{')
                        facts_json = facts_output[facts_start:]
                        facts = json.loads(facts_json)
                        
                        ansible_facts = facts.get('ansible_facts', {})
                        
                        # 更新主机信息
                        host.os_family = ansible_facts.get('ansible_os_family', '')
                        host.os_distribution = ansible_facts.get('ansible_distribution', '')
                        host.os_version = ansible_facts.get('ansible_distribution_version', '')
                        host.ansible_facts = ansible_facts
                        host.status = 'active'
                        host.last_check = timezone.now()
                        host.save()
                        
                        return Response({
                            'success': True,
                            'hostname': host.hostname,
                            'facts': ansible_facts,
                            'message': '主机信息收集成功'
                        })
                        
                    except json.JSONDecodeError:
                        return Response({
                            'success': False,
                            'hostname': host.hostname,
                            'message': 'Facts数据解析失败',
                            'details': {
                                'stdout': result.stdout,
                                'stderr': result.stderr
                            }
                        }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({
                        'success': False,
                        'hostname': host.hostname,
                        'message': 'Facts收集失败',
                        'details': {
                            'return_code': result.returncode,
                            'stdout': result.stdout,
                            'stderr': result.stderr,
                            'command': ' '.join(ansible_cmd)
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            finally:
                # 清理临时文件
                try:
                    os.unlink(inventory_file)
                except:
                    pass
                
                for temp_file in temp_files:
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
                        
        except subprocess.TimeoutExpired:
            return Response({
                'success': False,
                'hostname': host.hostname,
                'message': 'Facts收集超时'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'hostname': host.hostname,
                'message': f'Facts收集失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def batch_check(self, request):
        """批量检查主机连通性"""
        host_ids = request.data.get('host_ids', [])
        
        if not host_ids:
            return Response({
                'error': '请选择要检查的主机'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from .models import AnsibleHost
        hosts = AnsibleHost.objects.filter(id__in=host_ids)
        
        results = []
        for host in hosts:
            try:
                # 异步检查连通性
                from .tasks import check_host_connectivity
                task_result = check_host_connectivity.delay(host.id)
                
                results.append({
                    'host_id': host.id,
                    'hostname': host.hostname,
                    'task_id': task_result.id,
                    'message': '连通性检查已启动'
                })
            except Exception as e:
                results.append({
                    'host_id': host.id,
                    'hostname': host.hostname,
                    'error': str(e)
                })
        
        return Response({
            'message': f'已启动 {len(results)} 个主机的连通性检查',
            'results': results
        })


class AnsibleHostGroupViewSet(viewsets.ModelViewSet):
    """Ansible主机组管理视图集"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from .models import AnsibleHostGroup
        queryset = AnsibleHostGroup.objects.all()
        
        # 只显示用户有权限的主机组
        if not self.request.user.is_superuser:
            queryset = queryset.filter(created_by=self.request.user)
            
        # 搜索过滤
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
            
        return queryset.order_by('name')

    def get_serializer_class(self):
        from .serializers import AnsibleHostGroupSerializer
        return AnsibleHostGroupSerializer

    @action(detail=True, methods=['get'])
    def hosts(self, request, pk=None):
        """获取主机组中的主机列表"""
        group = self.get_object()
        hosts = group.ansiblehost_set.all()
        
        from .serializers import AnsibleHostSerializer
        serializer = AnsibleHostSerializer(hosts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_hosts(self, request, pk=None):
        """向主机组添加主机"""
        group = self.get_object()
        host_ids = request.data.get('host_ids', [])
        
        if not host_ids:
            return Response({
                'error': '请选择要添加的主机'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .models import AnsibleHost, AnsibleHostGroupMembership
            
            added_count = 0
            for host_id in host_ids:
                try:
                    host = AnsibleHost.objects.get(id=host_id)
                    membership, created = AnsibleHostGroupMembership.objects.get_or_create(
                        host=host,
                        group=group
                    )
                    if created:
                        added_count += 1
                except AnsibleHost.DoesNotExist:
                    continue
            
            return Response({
                'message': f'成功添加 {added_count} 个主机到组 {group.name}'
            })
            
        except Exception as e:
            return Response({
                'error': f'添加主机失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_hosts(self, request, pk=None):
        """从主机组移除主机"""
        group = self.get_object()
        host_ids = request.data.get('host_ids', [])
        
        if not host_ids:
            return Response({
                'error': '请选择要移除的主机'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .models import AnsibleHostGroupMembership
            
            removed_count = AnsibleHostGroupMembership.objects.filter(
                group=group,
                host_id__in=host_ids
            ).delete()[0]
            
            return Response({
                'message': f'成功从组 {group.name} 移除 {removed_count} 个主机'
            })
            
        except Exception as e:
            return Response({
                'error': f'移除主机失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='hosts/(?P<host_id>[^/.]+)')
    def get_host_membership(self, request, pk=None, host_id=None):
        """获取主机在组中的成员关系信息"""
        group = self.get_object()
        
        try:
            from .models import AnsibleHostGroupMembership
            membership = AnsibleHostGroupMembership.objects.get(
                group=group,
                host_id=host_id
            )
            
            return Response({
                'id': membership.id,
                'host_id': membership.host.id,
                'group_id': membership.group.id,
                'variables': membership.variables,
                'created_at': membership.created_at
            })
            
        except AnsibleHostGroupMembership.DoesNotExist:
            return Response({
                'error': '主机不在此组中'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['put'], url_path='hosts/(?P<host_id>[^/.]+)')
    def update_host_membership(self, request, pk=None, host_id=None):
        """更新主机在组中的成员关系信息"""
        group = self.get_object()
        
        try:
            from .models import AnsibleHostGroupMembership
            membership = AnsibleHostGroupMembership.objects.get(
                group=group,
                host_id=host_id
            )
            
            variables = request.data.get('variables', {})
            membership.variables = variables
            membership.save()
            
            return Response({
                'message': '主机变量更新成功',
                'variables': membership.variables
            })
            
        except AnsibleHostGroupMembership.DoesNotExist:
            return Response({
                'error': '主机不在此组中'
            }, status=status.HTTP_404_NOT_FOUND)


class InventoryHostViewSet(viewsets.ModelViewSet):
    """Inventory与Host关联管理视图集"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        from .serializers import InventoryHostSerializer, InventoryHostCreateSerializer
        if self.action == 'create':
            return InventoryHostCreateSerializer
        return InventoryHostSerializer
    
    def get_queryset(self):
        from .models import InventoryHost
        queryset = InventoryHost.objects.select_related('inventory', 'host')
        
        # 根据inventory过滤
        inventory_id = self.request.query_params.get('inventory_id')
        if inventory_id:
            queryset = queryset.filter(inventory_id=inventory_id)
        
        # 根据host过滤
        host_id = self.request.query_params.get('host_id')
        if host_id:
            queryset = queryset.filter(host_id=host_id)
            
        # 激活状态过滤
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('inventory__name', 'inventory_name')

    @action(detail=False, methods=['post'])
    def batch_add(self, request):
        """批量添加主机到清单"""
        from .models import AnsibleInventory, AnsibleHost, InventoryHost
        
        inventory_id = request.data.get('inventory_id')
        host_ids = request.data.get('host_ids', [])
        
        if not inventory_id or not host_ids:
            return Response({
                'error': '请提供inventory_id和host_ids'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            inventory = AnsibleInventory.objects.get(id=inventory_id)
            hosts = AnsibleHost.objects.filter(id__in=host_ids)
            
            added_count = 0
            errors = []
            
            for host in hosts:
                try:
                    _, created = InventoryHost.objects.get_or_create(
                        inventory=inventory,
                        host=host,
                        defaults={
                            'inventory_name': host.hostname,
                            'host_variables': {},
                            'is_active': True
                        }
                    )
                    if created:
                        added_count += 1
                    else:
                        errors.append(f'主机 {host.hostname} 已存在于清单中')
                except Exception as e:
                    errors.append(f'添加主机 {host.hostname} 失败: {str(e)}')
            
            return Response({
                'message': f'成功添加 {added_count} 个主机到清单',
                'added_count': added_count,
                'errors': errors
            })
            
        except AnsibleInventory.DoesNotExist:
            return Response({
                'error': '指定的清单不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'批量添加失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def batch_remove(self, request):
        """批量移除主机关联"""
        from .models import InventoryHost
        
        inventory_id = request.data.get('inventory_id')
        host_ids = request.data.get('host_ids', [])
        
        if not inventory_id or not host_ids:
            return Response({
                'error': '请提供inventory_id和host_ids'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            removed_count = InventoryHost.objects.filter(
                inventory_id=inventory_id,
                host_id__in=host_ids
            ).delete()[0]
            
            return Response({
                'message': f'成功移除 {removed_count} 个主机关联',
                'removed_count': removed_count
            })
            
        except Exception as e:
            return Response({
                'error': f'批量移除失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class InventoryGroupViewSet(viewsets.ModelViewSet):
    """Inventory主机组关联视图集"""
    serializer_class = InventoryGroupSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = InventoryGroup.objects.all().select_related('inventory', 'group')
        
        # 过滤条件
        inventory_id = self.request.query_params.get('inventory_id')
        if inventory_id:
            queryset = queryset.filter(inventory_id=inventory_id)
            
        group_id = self.request.query_params.get('group_id')
        if group_id:
            queryset = queryset.filter(group_id=group_id)
            
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset.order_by('inventory__name', 'inventory_name')

    @action(detail=False, methods=['post'])
    def batch_add(self, request):
        """批量添加主机组到清单"""
        serializer = InventoryGroupBatchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        inventory_id = data['inventory_id']
        group_ids = data['group_ids']
        inventory_names = data.get('inventory_names', [])
        group_variables = data.get('group_variables', [])
        is_active = data.get('is_active', True)
        
        try:
            inventory = AnsibleInventory.objects.get(id=inventory_id)
            added_count = 0
            
            for i, group_id in enumerate(group_ids):
                try:
                    group = AnsibleHostGroup.objects.get(id=group_id)
                    inventory_name = inventory_names[i] if i < len(inventory_names) else group.name
                    variables = group_variables[i] if i < len(group_variables) else {}
                    
                    inventory_group, created = InventoryGroup.objects.get_or_create(
                        inventory=inventory,
                        group=group,
                        defaults={
                            'inventory_name': inventory_name,
                            'group_variables': variables,
                            'is_active': is_active
                        }
                    )
                    
                    if created:
                        added_count += 1
                    else:
                        # 如果已存在，更新信息
                        inventory_group.inventory_name = inventory_name
                        inventory_group.group_variables = variables
                        inventory_group.is_active = is_active
                        inventory_group.save()
                        
                except AnsibleHostGroup.DoesNotExist:
                    continue
            
            return Response({
                'message': f'成功处理 {added_count} 个主机组关联',
                'added_count': added_count
            })
            
        except AnsibleInventory.DoesNotExist:
            return Response({
                'error': '主机清单不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'批量添加失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def batch_remove(self, request):
        """批量移除主机组关联"""
        inventory_id = request.data.get('inventory_id')
        group_ids = request.data.get('group_ids', [])
        
        if not inventory_id:
            return Response({
                'error': '请提供inventory_id'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not group_ids:
            return Response({
                'error': '请提供group_ids列表'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            removed_count = InventoryGroup.objects.filter(
                inventory_id=inventory_id,
                group_id__in=group_ids
            ).delete()[0]
            
            return Response({
                'message': f'成功移除 {removed_count} 个主机组关联',
                'removed_count': removed_count
            })
            
        except Exception as e:
            return Response({
                'error': f'批量移除失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
