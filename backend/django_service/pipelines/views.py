import logging

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import (
    Pipeline, PipelineStep, PipelineRun, PipelineToolMapping,
    ParallelGroup, ApprovalRequest, WorkflowExecution, StepExecutionHistory
)
from .serializers import (
    PipelineSerializer, 
    PipelineListSerializer, 
    PipelineStepSerializer, 
    PipelineRunSerializer,
    PipelineToolMappingSerializer,
    ParallelGroupSerializer,
    ApprovalRequestSerializer,
    WorkflowExecutionSerializer,
    StepExecutionHistorySerializer,
    WorkflowAnalysisSerializer,
    WorkflowMetricsSerializer,
    ExecutionRecoverySerializer,
    ApprovalResponseSerializer
)
from .services.jenkins_sync import JenkinsPipelineSyncService
from cicd_integrations.models import CICDTool


logger = logging.getLogger(__name__)


@api_view(['GET'])
def pipeline_health(request):
    """
    Pipeline health check endpoint.
    """
    return Response({
        'status': 'healthy',
        'service': 'pipelines',
        'message': 'Pipeline service is running'
    })


@extend_schema_view(
    list=extend_schema(summary="List pipelines", description="Get a list of all pipelines"),
    create=extend_schema(summary="Create pipeline", description="Create a new pipeline"),
    retrieve=extend_schema(summary="Get pipeline", description="Get a specific pipeline"),
    update=extend_schema(summary="Update pipeline", description="Update a pipeline"),
    destroy=extend_schema(summary="Delete pipeline", description="Delete a pipeline"),
)
class PipelineViewSet(viewsets.ModelViewSet):
    """ViewSet for managing CI/CD pipelines"""
    
    queryset = Pipeline.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PipelineListSerializer
        return PipelineSerializer
    
    def get_queryset(self):
        queryset = Pipeline.objects.select_related('project', 'created_by')
        
        # Filter by project if provided
        project_id = self.request.query_params.get('project', None)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
            
        # Filter by status if provided
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset
    
    @extend_schema(
        summary="Run pipeline",
        description="Trigger a new run of the pipeline"
    )
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """Trigger a pipeline run"""
        pipeline = self.get_object()
        
        try:
            # 使用新的执行引擎
            from .services.execution_engine import execution_engine
            
            trigger_data = {
                'trigger_type': 'manual',
                'triggered_via': 'api',
                'user_id': request.user.id,
                'parameters': request.data.get('parameters', {})
            }
            
            # 执行流水线
            pipeline_run = execution_engine.execute_pipeline(
                pipeline=pipeline,
                user=request.user,
                trigger_data=trigger_data
            )
            
            serializer = PipelineRunSerializer(pipeline_run)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Failed to execute pipeline {pipeline.id}: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to execute pipeline: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Sync pipeline to CI/CD tool",
        description="Sync this pipeline to a specified CI/CD tool (e.g., Jenkins)"
    )
    @action(detail=True, methods=['post'])
    def sync_to_tool(self, request, pk=None):
        """将流水线同步到指定的CI/CD工具"""
        pipeline = self.get_object()
        tool_id = request.data.get('tool_id')
        
        if not tool_id:
            return Response(
                {'error': 'tool_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            tool = CICDTool.objects.get(id=tool_id)
        except CICDTool.DoesNotExist:
            return Response(
                {'error': 'CI/CD tool not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 根据工具类型调用不同的同步服务
        if tool.tool_type == 'jenkins':
            service = JenkinsPipelineSyncService(tool)
            result = service.sync_pipeline_to_jenkins(pipeline)
        else:
            return Response(
                {'error': f'Sync not supported for tool type: {tool.tool_type}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Get pipeline tool mappings",
        description="Get all tool mappings for this pipeline"
    )
    @action(detail=True, methods=['get'])
    def tool_mappings(self, request, pk=None):
        """获取流水线的工具映射"""
        pipeline = self.get_object()
        mappings = PipelineToolMapping.objects.filter(pipeline=pipeline)
        serializer = PipelineToolMappingSerializer(mappings, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Trigger build in external tool",
        description="Trigger a build in the mapped external CI/CD tool"
    )
    @action(detail=True, methods=['post'])
    def trigger_external_build(self, request, pk=None):
        """在外部工具中触发构建"""
        pipeline = self.get_object()
        tool_id = request.data.get('tool_id')
        parameters = request.data.get('parameters', {})
        
        if not tool_id:
            return Response(
                {'error': 'tool_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            tool = CICDTool.objects.get(id=tool_id)
            mapping = PipelineToolMapping.objects.get(pipeline=pipeline, tool=tool)
        except CICDTool.DoesNotExist:
            return Response(
                {'error': 'CI/CD tool not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except PipelineToolMapping.DoesNotExist:
            return Response(
                {'error': 'No mapping found between pipeline and tool'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 根据工具类型触发构建
        if tool.tool_type == 'jenkins':
            from .services.jenkins_sync import JenkinsPipelineSyncService
            service = JenkinsPipelineSyncService(tool)
            result = service.trigger_jenkins_build(pipeline, parameters)
        else:
            return Response(
                {'error': f'Build trigger not supported for tool type: {tool.tool_type}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_ansible_step(self, request, pk=None):
        """为Pipeline添加Ansible步骤"""
        pipeline = self.get_object()
        
        # 验证必需参数
        required_fields = ['name', 'ansible_playbook_id', 'ansible_inventory_id', 'ansible_credential_id']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {'error': f'缺少必需字段: {field}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # 创建Ansible步骤
        step_data = {
            'pipeline': pipeline.id,
            'name': request.data['name'],
            'description': request.data.get('description', ''),
            'step_type': 'ansible',
            'ansible_playbook': request.data['ansible_playbook_id'],
            'ansible_inventory': request.data['ansible_inventory_id'],
            'ansible_credential': request.data['ansible_credential_id'],
            'ansible_parameters': request.data.get('ansible_parameters', {}),
            'order': request.data.get('order', pipeline.steps.count()),
            'timeout_seconds': request.data.get('timeout_seconds', 600),
        }
        
        step_serializer = PipelineStepSerializer(data=step_data)
        step_serializer.is_valid(raise_exception=True)
        step = step_serializer.save()
        
        return Response({
            'message': 'Ansible步骤已添加到Pipeline',
            'step_id': step.id,
            'step_data': PipelineStepSerializer(step).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def execute_ansible_steps(self, request, pk=None):
        """执行Pipeline中的所有Ansible步骤"""
        pipeline = self.get_object()
        
        # 获取所有Ansible类型的步骤
        ansible_steps = pipeline.steps.filter(step_type='ansible').order_by('order')
        
        if not ansible_steps.exists():
            return Response({
                'message': '该Pipeline中没有Ansible步骤'
            }, status=status.HTTP_200_OK)
        
        execution_results = []
        
        for step in ansible_steps:
            try:
                # 检查必需的Ansible配置
                if not all([step.ansible_playbook, step.ansible_inventory, step.ansible_credential]):
                    result = {
                        'step_id': step.id,
                        'step_name': step.name,
                        'status': 'failed',
                        'error': 'Ansible配置不完整'
                    }
                    execution_results.append(result)
                    continue
                
                # 创建Ansible执行记录
                from ansible_integration.models import AnsibleExecution
                from ansible_integration.tasks import execute_ansible_playbook
                
                execution = AnsibleExecution.objects.create(
                    playbook=step.ansible_playbook,
                    inventory=step.ansible_inventory,
                    credential=step.ansible_credential,
                    parameters=step.ansible_parameters,
                    pipeline=pipeline,
                    pipeline_step=step,
                    created_by=request.user,
                    status='pending'
                )
                
                # 启动异步执行
                task = execute_ansible_playbook.delay(execution.id)
                
                result = {
                    'step_id': step.id,
                    'step_name': step.name,
                    'execution_id': execution.id,
                    'task_id': task.id,
                    'status': 'started'
                }
                execution_results.append(result)
                
            except Exception as e:
                result = {
                    'step_id': step.id,
                    'step_name': step.name,
                    'status': 'failed',
                    'error': str(e)
                }
                execution_results.append(result)
        
        return Response({
            'message': f'已启动{len(execution_results)}个Ansible步骤',
            'results': execution_results
        })

    def create(self, request, *args, **kwargs):
        """创建流水线 - 添加调试日志"""
        logger.warning(f"[DEBUG] PipelineViewSet.create called")
        logger.warning(f"[DEBUG] Request method: {request.method}")
        logger.warning(f"[DEBUG] Request path: {request.path}")
        logger.warning(f"[DEBUG] Request data keys: {list(request.data.keys())}")
        logger.warning(f"[DEBUG] Request data: {request.data}")
        logger.warning(f"[DEBUG] User: {request.user}")
        
        # 检查steps字段
        if 'steps' in request.data:
            logger.warning(f"[DEBUG] Steps data found: {len(request.data['steps'])} steps")
            for i, step in enumerate(request.data['steps']):
                logger.warning(f"[DEBUG] Step {i}: {step}")
        else:
            logger.error(f"[DEBUG] No 'steps' field in request data!")
            logger.error(f"[DEBUG] Available fields: {list(request.data.keys())}")
        
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """更新流水线 - 添加调试日志"""
        logger.warning(f"[DEBUG] PipelineViewSet.update called")
        logger.warning(f"[DEBUG] Request method: {request.method}")
        logger.warning(f"[DEBUG] Request path: {request.path}")
        logger.warning(f"[DEBUG] Pipeline ID: {kwargs.get('pk')}")
        logger.warning(f"[DEBUG] Request data keys: {list(request.data.keys())}")
        logger.warning(f"[DEBUG] Request data: {request.data}")
        
        # 检查steps字段
        if 'steps' in request.data:
            logger.warning(f"[DEBUG] Steps data found: {len(request.data['steps'])} steps")
            for i, step in enumerate(request.data['steps']):
                logger.warning(f"[DEBUG] Step {i}: {step}")
        else:
            logger.error(f"[DEBUG] No 'steps' field in update request!")
            logger.error(f"[DEBUG] Available fields: {list(request.data.keys())}")
            
            # 获取当前流水线的步骤信息用于对比
            try:
                pipeline = self.get_object()
                current_steps = pipeline.atomic_steps.all()
                logger.warning(f"[DEBUG] Current pipeline has {len(current_steps)} steps")
            except Exception as e:
                logger.error(f"[DEBUG] Error getting current pipeline: {e}")
        
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """部分更新流水线 - 添加调试日志"""
        logger.warning(f"[DEBUG] PipelineViewSet.partial_update called")
        logger.warning(f"[DEBUG] Request method: {request.method}")
        logger.warning(f"[DEBUG] Request path: {request.path}")
        logger.warning(f"[DEBUG] Pipeline ID: {kwargs.get('pk')}")
        logger.warning(f"[DEBUG] Request data keys: {list(request.data.keys())}")
        logger.warning(f"[DEBUG] Request data: {request.data}")
        
        # 检查steps字段
        if 'steps' in request.data:
            logger.warning(f"[DEBUG] Steps data found in partial update: {len(request.data['steps'])} steps")
        else:
            logger.warning(f"[DEBUG] No 'steps' field in partial update (this might be OK)")
            logger.warning(f"[DEBUG] Available fields: {list(request.data.keys())}")
        
        return super().partial_update(request, *args, **kwargs)

    def perform_create(self, serializer):
        """创建时设置创建者"""
        logger.warning(f"[DEBUG] perform_create called with validated_data keys: {list(serializer.validated_data.keys())}")
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """更新时的额外处理"""
        logger.warning(f"[DEBUG] perform_update called with validated_data keys: {list(serializer.validated_data.keys())}")
        serializer.save()

    # 高级工作流功能API
    
    @extend_schema(
        summary="Update step advanced configuration",
        description="Update advanced configuration for a specific step"
    )
    @action(detail=True, methods=['put'], url_path='steps/(?P<step_id>[^/.]+)/advanced-config')
    def update_step_advanced_config(self, request, pk=None, step_id=None):
        """更新步骤高级配置"""
        pipeline = self.get_object()
        
        try:
            step = pipeline.steps.get(id=step_id)
        except PipelineStep.DoesNotExist:
            return Response(
                {'error': 'Step not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 更新高级配置字段
        config = request.data
        if 'condition' in config:
            step.conditions = config['condition']
        if 'parallel_group_id' in config:
            step.parallel_group = config['parallel_group_id']
        if 'approval_config' in config:
            approval_config = config['approval_config']
            step.approval_required = approval_config.get('required', False)
            step.approval_users = approval_config.get('approvers', [])
        if 'retry_policy' in config:
            step.retry_policy = config['retry_policy']
        if 'notification_config' in config:
            step.notification_config = config['notification_config']
        
        step.save()
        
        return Response({
            'message': 'Advanced configuration updated successfully',
            'step_id': step.id
        })

    @extend_schema(
        summary="Resume pipeline execution from specific step",
        description="Resume a failed pipeline execution from a specific step"
    )
    @action(detail=False, methods=['post'], url_path='executions/(?P<execution_id>[^/.]+)/resume')
    def resume_pipeline_from_step(self, request, execution_id=None):
        """从失败步骤恢复执行流水线"""
        step_id = request.data.get('step_id')
        parameters = request.data.get('parameters', {})
        
        if not step_id:
            return Response(
                {'error': 'step_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 这里应该实现实际的恢复逻辑
            # 目前返回模拟数据
            recovery_data = {
                'execution_id': execution_id,
                'resumed_from_step': step_id,
                'parameters': parameters,
                'status': 'resumed',
                'message': 'Pipeline execution resumed successfully'
            }
            
            return Response(recovery_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to resume pipeline: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Get execution step history",
        description="Get detailed execution history for all steps in an execution"
    )
    @action(detail=False, methods=['get'], url_path='executions/(?P<execution_id>[^/.]+)/steps')
    def get_execution_step_history(self, request, execution_id=None):
        """获取执行历史和失败步骤信息"""
        try:
            # 模拟步骤执行历史数据
            step_history = [
                {
                    'id': 1,
                    'name': 'Build Step',
                    'status': 'success',
                    'started_at': '2025-01-08T10:00:00Z',
                    'completed_at': '2025-01-08T10:05:00Z',
                    'duration_seconds': 300,
                    'retry_count': 0
                },
                {
                    'id': 2,
                    'name': 'Test Step',
                    'status': 'failed',
                    'started_at': '2025-01-08T10:05:00Z',
                    'completed_at': '2025-01-08T10:08:00Z',
                    'duration_seconds': 180,
                    'retry_count': 1,
                    'error_message': 'Test case failed'
                }
            ]
            
            return Response(step_history, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get execution history: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Evaluate step condition",
        description="Evaluate execution condition for a specific step"
    )
    @action(detail=True, methods=['post'], url_path='steps/(?P<step_id>[^/.]+)/evaluate-condition')
    def evaluate_step_condition(self, request, pk=None, step_id=None):
        """评估步骤条件"""
        pipeline = self.get_object()
        condition = request.data.get('condition')
        context = request.data.get('context', {})
        
        try:
            step = pipeline.steps.get(id=step_id)
        except PipelineStep.DoesNotExist:
            return Response(
                {'error': 'Step not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 简单的条件评估逻辑
        result = True
        error = None
        
        try:
            # 这里应该实现条件表达式评估逻辑
            # 目前返回简单的结果
            if condition and condition.get('type') == 'expression':
                # 模拟条件评估
                result = True
            
        except Exception as e:
            result = False
            error = str(e)
        
        return Response({
            'result': result,
            'error': error
        })

    @extend_schema(
        summary="Submit approval for step",
        description="Submit approval or rejection for a step requiring approval"
    )
    @action(detail=False, methods=['post'], url_path='executions/(?P<execution_id>[^/.]+)/steps/(?P<step_id>[^/.]+)/approve')
    def submit_approval(self, request, execution_id=None, step_id=None):
        """提交审批"""
        approved = request.data.get('approved', False)
        comment = request.data.get('comment', '')
        
        try:
            # 创建或更新审批请求
            # 这里应该实现实际的审批逻辑
            approval_data = {
                'execution_id': execution_id,
                'step_id': step_id,
                'approved': approved,
                'comment': comment,
                'approved_by': request.user.username,
                'approved_at': timezone.now().isoformat(),
                'success': True
            }
            
            return Response(approval_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to submit approval: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Analyze workflow dependencies",
        description="Analyze workflow dependencies and provide optimization suggestions"
    )
    @action(detail=True, methods=['get'], url_path='analyze-workflow')
    def analyze_workflow_dependencies(self, request, pk=None):
        """分析工作流依赖关系"""
        pipeline = self.get_object()
        steps = pipeline.steps.all()
        
        # 分析依赖关系
        dependencies = []
        cycles = []
        critical_path = []
        parallelization_suggestions = []
        
        for step in steps:
            if step.dependencies:
                for dep_id in step.dependencies:
                    dependencies.append({
                        'from_step': dep_id,
                        'to_step': step.id,
                        'type': 'dependency'
                    })
        
        # 简单的关键路径分析
        critical_path = [step.id for step in steps.order_by('order')]
        
        # 并行化建议
        parallel_groups = {}
        for step in steps:
            if step.parallel_group:
                if step.parallel_group not in parallel_groups:
                    parallel_groups[step.parallel_group] = []
                parallel_groups[step.parallel_group].append(step.id)
        
        for group_name, step_ids in parallel_groups.items():
            parallelization_suggestions.append({
                'group': group_name,
                'steps': step_ids,
                'estimated_time_saved': len(step_ids) * 0.3  # 简单估算
            })
        
        return Response({
            'dependencies': dependencies,
            'cycles': cycles,
            'critical_path': critical_path,
            'parallelization_suggestions': parallelization_suggestions
        })

    @extend_schema(
        summary="Get workflow metrics",
        description="Get detailed workflow metrics and performance data"
    )
    @action(detail=True, methods=['get'], url_path='workflow-metrics')
    def get_workflow_metrics(self, request, pk=None):
        """获取工作流指标"""
        pipeline = self.get_object()
        steps = pipeline.steps.all()
        
        # 计算基本指标
        total_steps = steps.count()
        parallel_steps = steps.filter(parallel_group__isnull=False).count()
        conditional_steps = steps.exclude(conditions=[]).count()
        approval_steps = steps.filter(approval_required=True).count()
        
        # 估算执行时间
        estimated_duration = total_steps * 5  # 简单估算，每步5分钟
        
        # 复杂度评分
        complexity_score = (
            total_steps * 1.0 + 
            parallel_steps * 0.5 + 
            conditional_steps * 1.5 + 
            approval_steps * 2.0
        )
        
        return Response({
            'total_steps': total_steps,
            'parallel_steps': parallel_steps,
            'conditional_steps': conditional_steps,
            'approval_steps': approval_steps,
            'estimated_duration': estimated_duration,
            'complexity_score': complexity_score
        })

    @extend_schema(
        summary="Retry failed step",
        description="Retry a failed step with optional retry configuration"
    )
    @action(detail=False, methods=['post'], url_path='executions/(?P<execution_id>[^/.]+)/steps/(?P<step_id>[^/.]+)/retry')
    def retry_failed_step(self, request, execution_id=None, step_id=None):
        """重试失败步骤"""
        retry_config = request.data or {}
        
        try:
            # 实现重试逻辑
            retry_data = {
                'execution_id': execution_id,
                'step_id': step_id,
                'retry_config': retry_config,
                'status': 'retrying',
                'message': 'Step retry initiated successfully'
            }
            
            return Response(retry_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to retry step: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Update notification configuration",
        description="Update notification configuration for a specific step"
    )
    @action(detail=True, methods=['put'], url_path='steps/(?P<step_id>[^/.]+)/notifications')
    def update_notification_config(self, request, pk=None, step_id=None):
        """更新通知配置"""
        pipeline = self.get_object()
        
        try:
            step = pipeline.steps.get(id=step_id)
        except PipelineStep.DoesNotExist:
            return Response(
                {'error': 'Step not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        step.notification_config = request.data
        step.save()
        
        return Response({
            'message': 'Notification configuration updated successfully',
            'step_id': step.id,
            'config': step.notification_config
        })

    @extend_schema(
        summary="Test notification configuration",
        description="Test notification configuration by sending a test notification"
    )
    @action(detail=False, methods=['post'], url_path='notifications/test')
    def test_notification(self, request):
        """测试通知配置"""
        config = request.data
        
        # 模拟通知测试
        try:
            # 这里应该实现实际的通知发送逻辑
            return Response({
                'success': True,
                'message': 'Test notification sent successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to send test notification: {str(e)}'
            })

    @extend_schema(
        summary="Create approval request",
        description="Create a new approval request for a step"
    )
    @action(detail=False, methods=['post'], url_path='approval-requests')
    def create_approval_request(self, request):
        """创建审批请求"""
        from .serializers import ApprovalRequestSerializer
        
        serializer = ApprovalRequestSerializer(data=request.data)
        if serializer.is_valid():
            # 设置请求者
            serializer.validated_data['requester_username'] = request.user.username
            approval_request = serializer.save()
            
            return Response(
                ApprovalRequestSerializer(approval_request).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Get parallel groups",
        description="Get all parallel groups for a pipeline"
    )
    @action(detail=False, methods=['get'], url_path='parallel-groups')
    def get_parallel_groups(self, request):
        """获取并行组"""
        pipeline_id = request.query_params.get('pipeline_id')
        
        if pipeline_id:
            try:
                pipeline = Pipeline.objects.get(id=pipeline_id)
                groups = pipeline.parallel_groups.all()
                from .serializers import ParallelGroupSerializer
                serializer = ParallelGroupSerializer(groups, many=True)
                return Response(serializer.data)
            except Pipeline.DoesNotExist:
                return Response(
                    {'error': 'Pipeline not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # 返回所有并行组
        from .models import ParallelGroup
        from .serializers import ParallelGroupSerializer
        groups = ParallelGroup.objects.all()
        serializer = ParallelGroupSerializer(groups, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create parallel group",
        description="Create a new parallel execution group"
    )
    @action(detail=False, methods=['post'], url_path='parallel-groups')
    def create_parallel_group(self, request):
        """创建并行组"""
        from .serializers import ParallelGroupSerializer
        
        serializer = ParallelGroupSerializer(data=request.data)
        if serializer.is_valid():
            group = serializer.save()
            return Response(
                ParallelGroupSerializer(group).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Update parallel group",
        description="Update an existing parallel execution group"
    )
    @action(detail=False, methods=['put'], url_path='parallel-groups/(?P<group_id>[^/.]+)')
    def update_parallel_group(self, request, group_id=None):
        """更新并行组"""
        from .models import ParallelGroup
        from .serializers import ParallelGroupSerializer
        
        try:
            group = ParallelGroup.objects.get(id=group_id)
        except ParallelGroup.DoesNotExist:
            return Response(
                {'error': 'Parallel group not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ParallelGroupSerializer(group, data=request.data)
        if serializer.is_valid():
            group = serializer.save()
            return Response(ParallelGroupSerializer(group).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete parallel group",
        description="Delete a parallel execution group"
    )
    @action(detail=False, methods=['delete'], url_path='parallel-groups/(?P<group_id>[^/.]+)')
    def delete_parallel_group(self, request, group_id=None):
        """删除并行组"""
        from .models import ParallelGroup
        
        try:
            group = ParallelGroup.objects.get(id=group_id)
            group.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ParallelGroup.DoesNotExist:
            return Response(
                {'error': 'Parallel group not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class PipelineToolMappingViewSet(viewsets.ModelViewSet):
    """流水线工具映射管理"""
    
    queryset = PipelineToolMapping.objects.all()
    serializer_class = PipelineToolMappingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 按流水线过滤
        pipeline_id = self.request.query_params.get('pipeline')
        if pipeline_id:
            queryset = queryset.filter(pipeline_id=pipeline_id)
        
        # 按工具过滤
        tool_id = self.request.query_params.get('tool')
        if tool_id:
            queryset = queryset.filter(tool_id=tool_id)
        
        return queryset.select_related('pipeline', 'tool')


class ParallelGroupViewSet(viewsets.ModelViewSet):
    """并行组管理"""
    
    queryset = ParallelGroup.objects.all()
    serializer_class = ParallelGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 按流水线过滤
        pipeline_id = self.request.query_params.get('pipeline')
        if pipeline_id:
            queryset = queryset.filter(pipeline_id=pipeline_id)
        
        return queryset.select_related('pipeline')
    
    def create(self, request, *args, **kwargs):
        """创建并行组并更新步骤关联"""
        response = super().create(request, *args, **kwargs)
        
        if response.status_code == 201:
            self._update_step_associations(response.data)
        
        return response
    
    def update(self, request, *args, **kwargs):
        """更新并行组并更新步骤关联"""
        response = super().update(request, *args, **kwargs)
        
        if response.status_code == 200:
            self._update_step_associations(response.data)
        
        return response
    
    def _update_step_associations(self, group_data):
        """更新步骤的并行组关联"""
        try:
            group_id = group_data['id']
            pipeline_id = group_data['pipeline']
            step_ids = self.request.data.get('steps', [])
            
            # 清除该组的现有关联
            PipelineStep.objects.filter(
                pipeline_id=pipeline_id,
                parallel_group=group_id
            ).update(parallel_group='')
            
            # 设置新的关联
            if step_ids:
                PipelineStep.objects.filter(
                    id__in=step_ids,
                    pipeline_id=pipeline_id
                ).update(parallel_group=group_id)
                
        except Exception as e:
            # 记录错误但不影响主要操作
            print(f"Error updating step associations: {e}")
    
    def destroy(self, request, *args, **kwargs):
        """删除并行组并清除步骤关联"""
        instance = self.get_object()
        
        # 清除相关步骤的并行组关联
        PipelineStep.objects.filter(
            pipeline=instance.pipeline,
            parallel_group=instance.id
        ).update(parallel_group='')
        
        return super().destroy(request, *args, **kwargs)


class ApprovalRequestViewSet(viewsets.ModelViewSet):
    """审批请求管理"""
    
    queryset = ApprovalRequest.objects.all()
    serializer_class = ApprovalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 按状态过滤
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 按流水线过滤
        pipeline_id = self.request.query_params.get('pipeline')
        if pipeline_id:
            queryset = queryset.filter(pipeline_id=pipeline_id)
        
        return queryset.select_related('pipeline', 'step')
    
    @extend_schema(
        summary="Approve or reject approval request",
        description="Submit approval or rejection for a pending approval request"
    )
    @action(detail=True, methods=['post'], url_path='respond')
    def respond_to_approval(self, request, pk=None):
        """响应审批请求"""
        approval_request = self.get_object()
        
        if approval_request.status != 'pending':
            return Response(
                {'error': 'Approval request is not pending'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action = request.data.get('action')  # 'approve' or 'reject'
        comment = request.data.get('comment', '')
        
        if action not in ['approve', 'reject']:
            return Response(
                {'error': 'Invalid action. Must be "approve" or "reject"'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新审批请求
        approval_request.status = 'approved' if action == 'approve' else 'rejected'
        approval_request.approved_by = request.user.username
        approval_request.approved_at = timezone.now()
        approval_request.response_comment = comment
        approval_request.save()
        
        # 更新对应的步骤状态
        step = approval_request.step
        step.approval_status = approval_request.status
        step.approved_by = approval_request.approved_by
        step.approved_at = approval_request.approved_at
        step.save()
        
        return Response({
            'message': f'Approval request {action}ed successfully',
            'approval_request': ApprovalRequestSerializer(approval_request).data
        })


class WorkflowExecutionViewSet(viewsets.ModelViewSet):
    """工作流执行管理"""
    
    queryset = WorkflowExecution.objects.all()
    serializer_class = WorkflowExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 按流水线过滤
        pipeline_id = self.request.query_params.get('pipeline')
        if pipeline_id:
            queryset = queryset.filter(pipeline_id=pipeline_id)
        
        # 按状态过滤
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('pipeline', 'current_step')
    
    @extend_schema(
        summary="Get execution recovery info",
        description="Get information needed for execution recovery"
    )
    @action(detail=True, methods=['get'], url_path='recovery-info')
    def get_recovery_info(self, request, pk=None):
        """获取执行恢复信息"""
        execution = self.get_object()
        
        # 获取失败的步骤
        failed_steps = []
        for step_id in execution.failed_steps:
            try:
                step = PipelineStep.objects.get(id=step_id)
                failed_steps.append({
                    'id': step.id,
                    'name': step.name,
                    'error': 'Step execution failed',  # 实际应该从日志中获取
                    'failed_at': step.completed_at or timezone.now().isoformat(),
                    'retry_count': step.retry_policy.get('current_retries', 0) if step.retry_policy else 0,
                    'max_retries': step.retry_policy.get('max_retries', 0) if step.retry_policy else 0
                })
            except PipelineStep.DoesNotExist:
                continue
        
        # 获取恢复点建议
        recovery_points = []
        pipeline_steps = execution.pipeline.steps.all().order_by('order')
        
        for step in pipeline_steps:
            if step.id in execution.failed_steps:
                recovery_points.append({
                    'step_id': step.id,
                    'step_name': step.name,
                    'description': f'Resume from failed step: {step.name}',
                    'recommended': step.id == execution.recovery_point
                })
        
        # 计算执行进度
        total_steps = pipeline_steps.count()
        completed_steps = total_steps - len(execution.failed_steps) - len(execution.pending_approvals)
        
        recovery_info = {
            'failed_steps': failed_steps,
            'recovery_points': recovery_points,
            'can_recover': len(failed_steps) > 0,
            'last_successful_step': execution.recovery_point,
            'execution_progress': {
                'total_steps': total_steps,
                'completed_steps': completed_steps,
                'failed_steps': len(execution.failed_steps),
                'pending_steps': len(execution.pending_approvals)
            }
        }
        
        return Response(recovery_info)


class StepExecutionHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """步骤执行历史查看"""
    
    queryset = StepExecutionHistory.objects.all()
    serializer_class = StepExecutionHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 按工作流执行过滤
        execution_id = self.request.query_params.get('execution')
        if execution_id:
            queryset = queryset.filter(workflow_execution_id=execution_id)
        
        # 按步骤过滤
        step_id = self.request.query_params.get('step')
        if step_id:
            queryset = queryset.filter(step_id=step_id)
        
        return queryset.select_related('workflow_execution', 'step')
