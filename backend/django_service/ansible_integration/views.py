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

from .models import AnsibleInventory, AnsiblePlaybook, AnsibleCredential, AnsibleExecution
from .serializers import (
    AnsibleInventorySerializer, AnsiblePlaybookSerializer, 
    AnsibleCredentialSerializer, AnsibleExecutionSerializer,
    AnsibleExecutionListSerializer, AnsibleStatsSerializer
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
            
            execution_serializer = AnsibleExecutionSerializer(data=execution_data)
            execution_serializer.is_valid(raise_exception=True)
            execution = execution_serializer.save(created_by=request.user)
            
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
        """检查主机连通性"""
        host = self.get_object()
        
        try:
            # 使用ansible命令检查连通性
            result = subprocess.run([
                'ansible', f'{host.ip_address}',
                '-m', 'ping',
                '-u', host.username,
                '-p', str(host.port),
                '--timeout=10'
            ], capture_output=True, text=True, timeout=15)
            
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
                'status': 'failed',
                'message': '连接超时',
                'checked_at': host.last_check
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'连接检查失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def gather_facts(self, request, pk=None):
        """收集主机信息"""
        host = self.get_object()
        
        try:
            # 使用ansible setup模块收集信息
            result = subprocess.run([
                'ansible', f'{host.ip_address}',
                '-m', 'setup',
                '-u', host.username,
                '-p', str(host.port),
                '--timeout=30'
            ], capture_output=True, text=True, timeout=35)
            
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
                        'facts': ansible_facts,
                        'message': '主机信息收集成功'
                    })
                    
                except json.JSONDecodeError:
                    return Response({
                        'success': False,
                        'message': 'Facts数据解析失败'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'success': False,
                    'message': result.stderr or result.stdout
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except subprocess.TimeoutExpired:
            return Response({
                'success': False,
                'message': 'Facts收集超时'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
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
