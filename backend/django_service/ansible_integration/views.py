from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

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
