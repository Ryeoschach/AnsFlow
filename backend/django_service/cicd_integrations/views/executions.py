"""
流水线执行管理视图
负责流水线执行的生命周期管理、监控、日志查看等功能
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
import logging

from ..models import PipelineExecution, StepExecution
from ..serializers import (
    PipelineExecutionSerializer, PipelineExecutionListSerializer,
    PipelineExecutionCreateSerializer
)
from ..services import cicd_engine

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(summary="List pipeline executions", description="Get a list of pipeline executions"),
    retrieve=extend_schema(summary="Get pipeline execution", description="Get a specific pipeline execution"),
    update=extend_schema(summary="Update pipeline execution", description="Update a pipeline execution"),
    destroy=extend_schema(summary="Delete pipeline execution", description="Delete a pipeline execution"),
)
class PipelineExecutionViewSet(viewsets.ModelViewSet):
    """流水线执行管理视图集"""
    
    queryset = PipelineExecution.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PipelineExecutionListSerializer
        elif self.action == 'create':
            return PipelineExecutionCreateSerializer
        return PipelineExecutionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 根据项目过滤
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(pipeline__project_id=project_id)
        
        # 根据流水线过滤
        pipeline_id = self.request.query_params.get('pipeline_id')
        if pipeline_id:
            queryset = queryset.filter(pipeline_id=pipeline_id)
        
        # 根据CI/CD工具过滤
        tool_id = self.request.query_params.get('tool_id')
        if tool_id:
            queryset = queryset.filter(cicd_tool_id=tool_id)
        
        # 根据状态过滤
        execution_status = self.request.query_params.get('status')
        if execution_status:
            queryset = queryset.filter(status=execution_status)
        
        # 根据触发类型过滤
        trigger_type = self.request.query_params.get('trigger_type')
        if trigger_type:
            queryset = queryset.filter(trigger_type=trigger_type)
        
        # 根据触发者过滤
        triggered_by = self.request.query_params.get('triggered_by')
        if triggered_by:
            queryset = queryset.filter(triggered_by_id=triggered_by)
        
        return queryset.select_related('pipeline', 'cicd_tool', 'triggered_by').order_by('-created_at')
    
    @extend_schema(
        summary="Cancel execution",
        description="Cancel a running pipeline execution"
    )
    @action(detail=True, methods=['post'])
    async def cancel(self, request, pk=None):
        """取消执行中的流水线"""
        execution = self.get_object()
        
        if execution.status not in ['pending', 'running']:
            return Response(
                {'error': f'Cannot cancel execution with status "{execution.status}"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 使用统一引擎取消执行
            success = await cicd_engine.cancel_execution(execution)
            
            if success:
                execution.refresh_from_db()
                serializer = PipelineExecutionSerializer(execution)
                return Response({
                    'message': 'Pipeline execution cancelled successfully',
                    'execution': serializer.data
                })
            else:
                return Response(
                    {'error': 'Failed to cancel pipeline execution'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Failed to cancel execution {execution.id}: {e}")
            return Response(
                {'error': f"Failed to cancel execution: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Retry execution",
        description="Retry a failed pipeline execution"
    )
    @action(detail=True, methods=['post'])
    async def retry(self, request, pk=None):
        """重试失败的流水线执行"""
        execution = self.get_object()
        
        if execution.status not in ['failed', 'cancelled']:
            return Response(
                {'error': f'Cannot retry execution with status "{execution.status}"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 使用统一引擎重试执行
            new_execution = await cicd_engine.retry_execution(execution, request.user)
            
            serializer = PipelineExecutionSerializer(new_execution)
            return Response({
                'message': 'Pipeline execution retried successfully',
                'execution': serializer.data
            }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Failed to retry execution {execution.id}: {e}")
            return Response(
                {'error': f"Failed to retry execution: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get execution logs",
        description="Get logs for a pipeline execution",
        parameters=[
            {
                'name': 'step_id',
                'in': 'query',
                'required': False,
                'description': 'Specific step ID to get logs for',
                'schema': {'type': 'string'}
            },
            {
                'name': 'follow',
                'in': 'query',
                'required': False,
                'description': 'Follow live logs (for running executions)',
                'schema': {'type': 'boolean', 'default': False}
            }
        ]
    )
    @action(detail=True, methods=['get'])
    async def logs(self, request, pk=None):
        """获取流水线执行日志"""
        execution = self.get_object()
        step_id = request.query_params.get('step_id')
        follow = request.query_params.get('follow', 'false').lower() == 'true'
        
        try:
            if step_id:
                # 获取特定步骤的日志
                try:
                    step_execution = execution.steps.get(id=step_id)
                    logs = await cicd_engine.get_step_logs(step_execution, follow)
                except StepExecution.DoesNotExist:
                    return Response(
                        {'error': f'Step execution {step_id} not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # 获取整个执行的日志
                logs = await cicd_engine.get_execution_logs(execution, follow)
            
            return Response({
                'execution_id': execution.id,
                'step_id': step_id,
                'follow': follow,
                'logs': logs
            })
            
        except Exception as e:
            logger.error(f"Failed to get logs for execution {execution.id}: {e}")
            return Response(
                {'error': f"Failed to get logs: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get execution statistics",
        description="Get statistics for pipeline executions",
        parameters=[
            {
                'name': 'pipeline_id',
                'in': 'query',
                'required': False,
                'description': 'Filter by pipeline ID',
                'schema': {'type': 'string'}
            },
            {
                'name': 'tool_id',
                'in': 'query',
                'required': False,
                'description': 'Filter by CI/CD tool ID',
                'schema': {'type': 'string'}
            },
            {
                'name': 'days',
                'in': 'query',
                'required': False,
                'description': 'Number of days to look back',
                'schema': {'type': 'integer', 'default': 30}
            }
        ]
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取流水线执行统计信息"""
        # 过滤参数
        pipeline_id = request.query_params.get('pipeline_id')
        tool_id = request.query_params.get('tool_id')
        days = int(request.query_params.get('days', 30))
        
        # 基础查询集
        queryset = self.get_queryset()
        
        # 时间范围过滤
        since = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(created_at__gte=since)
        
        # 额外过滤
        if pipeline_id:
            queryset = queryset.filter(pipeline_id=pipeline_id)
        if tool_id:
            queryset = queryset.filter(cicd_tool_id=tool_id)
        
        # 计算统计信息
        total_executions = queryset.count()
        
        status_stats = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        avg_duration = queryset.filter(
            status='completed'
        ).aggregate(
            avg_duration=Avg('duration')
        )['avg_duration'] or 0
        
        # 成功率计算
        success_count = queryset.filter(status='completed').count()
        success_rate = (success_count / total_executions * 100) if total_executions > 0 else 0
        
        # 按天统计
        daily_stats = []
        for i in range(days):
            day = timezone.now().date() - timedelta(days=i)
            day_start = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time()))
            day_end = day_start + timedelta(days=1)
            
            day_executions = queryset.filter(
                created_at__gte=day_start,
                created_at__lt=day_end
            )
            
            daily_stats.append({
                'date': day.isoformat(),
                'total': day_executions.count(),
                'completed': day_executions.filter(status='completed').count(),
                'failed': day_executions.filter(status='failed').count(),
                'cancelled': day_executions.filter(status='cancelled').count()
            })
        
        return Response({
            'period_days': days,
            'total_executions': total_executions,
            'success_rate': round(success_rate, 2),
            'average_duration_seconds': round(avg_duration, 2) if avg_duration else 0,
            'status_breakdown': list(status_stats),
            'daily_statistics': daily_stats
        })
    
    @extend_schema(
        summary="Get execution timeline",
        description="Get detailed timeline of a pipeline execution"
    )
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """获取流水线执行时间线"""
        execution = self.get_object()
        
        try:
            # 获取所有步骤执行记录
            steps = execution.steps.all().order_by('created_at')
            
            timeline_events = []
            
            # 添加执行开始事件
            timeline_events.append({
                'timestamp': execution.created_at,
                'event_type': 'execution_started',
                'title': 'Pipeline Execution Started',
                'description': f'Pipeline "{execution.pipeline.name}" execution started',
                'status': 'info'
            })
            
            # 添加步骤事件
            for step in steps:
                # 步骤开始
                if step.started_at:
                    timeline_events.append({
                        'timestamp': step.started_at,
                        'event_type': 'step_started',
                        'title': f'Step Started: {step.step.name}',
                        'description': step.step.description or 'No description',
                        'status': 'running',
                        'step_id': step.id
                    })
                
                # 步骤完成
                if step.finished_at:
                    status_mapping = {
                        'completed': 'success',
                        'failed': 'error',
                        'cancelled': 'warning',
                        'skipped': 'info'
                    }
                    
                    timeline_events.append({
                        'timestamp': step.finished_at,
                        'event_type': 'step_finished',
                        'title': f'Step {step.status.title()}: {step.step.name}',
                        'description': step.error_message or f'Step {step.status}',
                        'status': status_mapping.get(step.status, 'info'),
                        'step_id': step.id,
                        'duration': step.duration
                    })
            
            # 添加执行结束事件
            if execution.finished_at:
                status_mapping = {
                    'completed': 'success',
                    'failed': 'error',
                    'cancelled': 'warning'
                }
                
                timeline_events.append({
                    'timestamp': execution.finished_at,
                    'event_type': 'execution_finished',
                    'title': f'Pipeline Execution {execution.status.title()}',
                    'description': f'Total duration: {execution.duration}s' if execution.duration else 'No duration recorded',
                    'status': status_mapping.get(execution.status, 'info')
                })
            
            # 按时间排序
            timeline_events.sort(key=lambda x: x['timestamp'])
            
            return Response({
                'execution_id': execution.id,
                'pipeline_name': execution.pipeline.name,
                'total_events': len(timeline_events),
                'timeline': timeline_events
            })
            
        except Exception as e:
            logger.error(f"Failed to get timeline for execution {execution.id}: {e}")
            return Response(
                {'error': f"Failed to get execution timeline: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, *args, **kwargs):
        """创建流水线执行 - 添加调试日志"""
        logger.warning(f"[DEBUG] PipelineExecutionViewSet.create called")
        logger.warning(f"[DEBUG] Request method: {request.method}")
        logger.warning(f"[DEBUG] Request path: {request.path}")
        logger.warning(f"[DEBUG] Request data: {request.data}")
        logger.warning(f"[DEBUG] User: {request.user}")
        
        # 检查是否是误调用
        if not request.data.get('pipeline_id') or not request.data.get('cicd_tool_id'):
            logger.error(f"[DEBUG] Missing required fields in execution create request!")
            logger.error(f"[DEBUG] This might be a misdirected pipeline edit request")
        
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """更新流水线执行 - 添加调试日志"""
        logger.warning(f"[DEBUG] PipelineExecutionViewSet.update called")
        logger.warning(f"[DEBUG] Request method: {request.method}")
        logger.warning(f"[DEBUG] Request path: {request.path}")
        logger.warning(f"[DEBUG] Request data: {request.data}")
        
        return super().update(request, *args, **kwargs)
