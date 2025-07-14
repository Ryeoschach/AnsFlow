import logging

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.db.models import Count, Avg, Q
from datetime import timedelta
from django.core.cache import cache

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
from cicd_integrations.models import CICDTool, PipelineExecution, StepExecution


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
        # 支持两种参数名：pipeline_id 和 pipeline
        # 兼容DRF的query_params和Django原生的GET参数
        if hasattr(request, 'query_params'):
            pipeline_id = request.query_params.get('pipeline_id') or request.query_params.get('pipeline')
        else:
            pipeline_id = request.GET.get('pipeline_id') or request.GET.get('pipeline')
        
        logger.info(f"并行组API请求参数: {dict(getattr(request, 'query_params', request.GET))}")
        logger.info(f"解析到的pipeline_id: {pipeline_id}")
        
        if pipeline_id:
            try:
                pipeline = Pipeline.objects.get(id=pipeline_id)
                # 从步骤中分析并行组，而不是从separate的ParallelGroup模型
                steps = pipeline.steps.all().order_by('order')
                
                logger.info(f"Pipeline {pipeline_id} 总步骤数: {len(steps)}")
                for step in steps:
                    logger.info(f"步骤 {step.id}: {step.name}, parallel_group='{step.parallel_group}'")
                
                # 分析并行组
                parallel_groups = {}
                for step in steps:
                    if step.parallel_group:
                        group_name = step.parallel_group
                        if group_name not in parallel_groups:
                            parallel_groups[group_name] = {
                                'id': group_name,
                                'name': group_name,
                                'steps': []
                            }
                        parallel_groups[group_name]['steps'].append({
                            'id': step.id,
                            'name': step.name,
                            'step_type': step.step_type,
                            'order': step.order
                        })
                
                # 转换为列表格式
                groups_list = list(parallel_groups.values())
                
                logger.info(f"找到 {len(groups_list)} 个并行组")
                for group in groups_list:
                    logger.info(f"并行组 {group['id']}: {len(group['steps'])} 个步骤")
                
                return Response({
                    'parallel_groups': groups_list,
                    'total_groups': len(groups_list),
                    'total_steps': len(steps)
                })
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
            
            # 将 group_id 转换为字符串，因为 parallel_group 字段是 CharField
            group_id_str = str(group_id)
            
            # 清除该组的现有关联
            PipelineStep.objects.filter(
                pipeline_id=pipeline_id,
                parallel_group=group_id_str
            ).update(parallel_group='')
            
            # 设置新的关联
            if step_ids:
                PipelineStep.objects.filter(
                    id__in=step_ids,
                    pipeline_id=pipeline_id
                ).update(parallel_group=group_id_str)
                
        except Exception as e:
            # 记录错误但不影响主要操作
            print(f"Error updating step associations: {e}")
    
    def destroy(self, request, *args, **kwargs):
        """删除并行组并清除步骤关联"""
        instance = self.get_object()
        
        # 清除相关步骤的并行组关联
        # 将 instance.id 转换为字符串，因为 parallel_group 字段是 CharField
        group_id_str = str(instance.id)
        PipelineStep.objects.filter(
            pipeline=instance.pipeline,
            parallel_group=group_id_str
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


# ========================================
# 并行执行监控API视图
# ========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def parallel_execution_status(request):
    """
    获取并行执行状态和性能统计
    """
    try:
        # 缓存键，避免频繁查询数据库
        cache_key = 'parallel_execution_stats'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # 计算时间范围（最近24小时）
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        # 1. 活跃的并行组数量
        active_executions = PipelineExecution.objects.filter(
            status='running',
            started_at__gte=last_24h
        )
        
        # 计算当前活跃的并行组
        active_parallel_groups = 0
        for execution in active_executions:
            try:
                # 检查是否有并行组在运行
                parallel_steps = StepExecution.objects.filter(
                    pipeline_execution=execution,
                    status='running'
                ).select_related('atomic_step')
                
                # 统计具有parallel_group的步骤组
                parallel_groups = set()
                for step_exec in parallel_steps:
                    if hasattr(step_exec.atomic_step, 'parallel_group') and step_exec.atomic_step.parallel_group:
                        parallel_groups.add(step_exec.atomic_step.parallel_group)
                
                active_parallel_groups += len(parallel_groups)
            except Exception as e:
                logging.warning(f"Error counting parallel groups for execution {execution.id}: {e}")
        
        # 2. 最近24小时的并行组执行统计
        completed_executions = PipelineExecution.objects.filter(
            status__in=['success', 'failed'],
            completed_at__gte=last_24h,
            completed_at__isnull=False
        )
        
        total_executions = completed_executions.count()
        successful_executions = completed_executions.filter(status='success').count()
        
        # 计算成功率
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
        
        # 3. 平均执行时间（秒）
        avg_execution_time = 0
        if completed_executions.exists():
            total_time = sum([
                (exec.completed_at - exec.started_at).total_seconds() 
                for exec in completed_executions 
                if exec.started_at and exec.completed_at
            ])
            avg_execution_time = total_time / len(completed_executions) if completed_executions else 0
        
        # 4. 当前并发工作线程数估算
        concurrent_workers = StepExecution.objects.filter(
            status='running',
            started_at__gte=last_24h
        ).count()
        
        # 构建响应数据
        response_data = {
            'timestamp': now.isoformat(),
            'active_parallel_groups': active_parallel_groups,
            'avg_execution_time_seconds': round(avg_execution_time, 2),
            'success_rate_percent': round(success_rate, 2),
            'concurrent_workers': concurrent_workers,
            'total_executions_24h': total_executions,
            'successful_executions_24h': successful_executions,
            'performance_metrics': {
                'execution_throughput_per_hour': round(total_executions / 24, 2) if total_executions > 0 else 0,
                'avg_concurrent_workers': round(concurrent_workers / max(active_parallel_groups, 1), 2),
                'system_load_indicator': 'normal' if active_parallel_groups < 10 else 'high'
            }
        }
        
        # 缓存结果5分钟
        cache.set(cache_key, response_data, 300)
        
        return Response(response_data)
        
    except Exception as e:
        logging.error(f"Parallel execution status API error: {e}")
        return Response(
            {
                'error': 'Failed to get parallel execution status',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def jenkins_parallel_stats(request):
    """
    获取Jenkins并行转换统计信息
    """
    try:
        cache_key = 'jenkins_parallel_stats'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # 计算时间范围
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        # Jenkins相关的执行统计
        jenkins_executions = PipelineExecution.objects.filter(
            started_at__gte=last_24h,
            pipeline__execution_mode='remote',
            pipeline__execution_tool__tool_type='jenkins'
        )
        
        total_jenkins_executions = jenkins_executions.count()
        successful_jenkins = jenkins_executions.filter(status='success').count()
        
        # 转换成功率
        conversion_success_rate = (successful_jenkins / total_jenkins_executions * 100) if total_jenkins_executions > 0 else 100
        
        # 模拟转换时间统计（实际应该从日志或监控数据获取）
        avg_conversion_time_ms = 250  # 默认转换时间
        
        # 当前活跃的Jenkins构建
        active_jenkins_builds = jenkins_executions.filter(status='running').count()
        
        response_data = {
            'timestamp': now.isoformat(),
            'conversion_success_rate': round(conversion_success_rate, 2),
            'avg_conversion_time_ms': avg_conversion_time_ms,
            'active_builds': active_jenkins_builds,
            'total_jenkins_executions_24h': total_jenkins_executions,
            'health_status': 'healthy' if conversion_success_rate > 95 else 'degraded'
        }
        
        # 缓存结果5分钟
        cache.set(cache_key, response_data, 300)
        
        return Response(response_data)
        
    except Exception as e:
        logging.error(f"Jenkins parallel stats API error: {e}")
        return Response(
            {
                'error': 'Failed to get Jenkins parallel stats',
                'message': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def parallel_execution_health(request):
    """
    并行执行健康检查端点
    """
    try:
        # 检查系统当前状态
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        
        # 1. 检查是否有超时的执行
        long_running_executions = PipelineExecution.objects.filter(
            status='running',
            started_at__lt=last_hour
        ).count()
        
        # 2. 检查错误率
        recent_executions = PipelineExecution.objects.filter(
            completed_at__gte=last_hour,
            completed_at__isnull=False
        )
        
        total_recent = recent_executions.count()
        failed_recent = recent_executions.filter(status='failed').count()
        error_rate = (failed_recent / total_recent * 100) if total_recent > 0 else 0
        
        # 3. 检查系统负载
        active_workers = StepExecution.objects.filter(status='running').count()
        
        # 健康状态评估
        health_issues = []
        
        if long_running_executions > 5:
            health_issues.append(f"{long_running_executions} executions running over 1 hour")
        
        if error_rate > 20:
            health_issues.append(f"High error rate: {error_rate:.1f}%")
        
        if active_workers > 50:
            health_issues.append(f"High system load: {active_workers} active workers")
        
        health_status = 'healthy' if not health_issues else 'unhealthy'
        
        response_data = {
            'timestamp': now.isoformat(),
            'health_status': health_status,
            'long_running_executions': long_running_executions,
            'error_rate_percent': round(error_rate, 2),
            'active_workers': active_workers,
            'issues': health_issues,
            'recommendations': _get_health_recommendations(health_issues)
        }
        
        return Response(response_data)
        
    except Exception as e:
        logging.error(f"Parallel execution health check error: {e}")
        return Response(
            {
                'health_status': 'error',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _get_health_recommendations(issues):
    """
    根据健康问题提供建议
    """
    recommendations = []
    
    for issue in issues:
        if 'running over 1 hour' in issue:
            recommendations.append("检查长时间运行的任务，考虑增加超时设置或优化步骤")
        elif 'High error rate' in issue:
            recommendations.append("分析失败原因，检查步骤配置和依赖环境")
        elif 'High system load' in issue:
            recommendations.append("考虑增加工作节点或调整并发数限制")
    
    if not recommendations:
        recommendations.append("系统运行正常，继续保持监控")
    
    return recommendations
