"""
CI/CD 集成 API 视图
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.db.models import Q
import logging

from .models import CICDTool, AtomicStep, PipelineExecution, StepExecution
from .serializers import (
    CICDToolSerializer, CICDToolCreateSerializer, AtomicStepSerializer,
    AtomicStepSimpleSerializer, PipelineExecutionSerializer,
    PipelineExecutionListSerializer, PipelineExecutionCreateSerializer,
    HealthCheckSerializer, ToolStatusSerializer
)
from .services import cicd_engine
from pipelines.models import Pipeline

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(summary="List CI/CD tools", description="Get a list of CI/CD tools"),
    create=extend_schema(summary="Register CI/CD tool", description="Register a new CI/CD tool"),
    retrieve=extend_schema(summary="Get CI/CD tool", description="Get a specific CI/CD tool"),
    update=extend_schema(summary="Update CI/CD tool", description="Update a CI/CD tool"),
    destroy=extend_schema(summary="Delete CI/CD tool", description="Delete a CI/CD tool"),
)
class CICDToolViewSet(viewsets.ModelViewSet):
    """CI/CD 工具管理视图集"""
    
    queryset = CICDTool.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CICDToolCreateSerializer
        return CICDToolSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 根据项目过滤
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # 根据工具类型过滤
        tool_type = self.request.query_params.get('tool_type')
        if tool_type:
            queryset = queryset.filter(tool_type=tool_type)
        
        # 根据状态过滤
        tool_status = self.request.query_params.get('status')
        if tool_status:
            queryset = queryset.filter(status=tool_status)
        
        return queryset.select_related('project', 'created_by')
    
    async def perform_create(self, serializer):
        """创建 CI/CD 工具并进行健康检查"""
        tool_data = serializer.validated_data
        tool_data['created_by'] = self.request.user
        
        try:
            # 使用统一引擎注册工具
            tool = await cicd_engine.register_tool(tool_data, self.request.user)
            return tool
        except Exception as e:
            logger.error(f"Failed to register CI/CD tool: {e}")
            raise
    
    @extend_schema(
        summary="Health check tool",
        description="Perform health check on a CI/CD tool"
    )
    @action(detail=True, methods=['post'])
    async def health_check(self, request, pk=None):
        """执行工具健康检查"""
        tool = self.get_object()
        
        try:
            is_healthy = await cicd_engine.health_check_tool(tool)
            
            return Response({
                'tool_id': tool.id,
                'tool_name': tool.name,
                'tool_type': tool.tool_type,
                'status': tool.status,
                'is_healthy': is_healthy,
                'last_check': tool.last_health_check,
                'message': 'Health check completed successfully' if is_healthy else 'Health check failed'
            })
        
        except Exception as e:
            logger.error(f"Health check failed for tool {tool.id}: {e}")
            return Response(
                {'error': f"Health check failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Execute pipeline",
        description="Execute a pipeline using this CI/CD tool"
    )
    @action(detail=True, methods=['post'])
    async def execute_pipeline(self, request, pk=None):
        """使用此工具执行流水线"""
        tool = self.get_object()
        serializer = PipelineExecutionCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            try:
                pipeline = Pipeline.objects.get(id=serializer.validated_data['pipeline_id'])
                
                execution = await cicd_engine.execute_pipeline(
                    pipeline=pipeline,
                    tool=tool,
                    trigger_type=serializer.validated_data['trigger_type'],
                    triggered_by=request.user,
                    parameters=serializer.validated_data['parameters']
                )
                
                response_serializer = PipelineExecutionSerializer(execution)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
            except Pipeline.DoesNotExist:
                return Response(
                    {'error': 'Pipeline not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                logger.error(f"Failed to execute pipeline: {e}")
                return Response(
                    {'error': f"Failed to execute pipeline: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(summary="List atomic steps", description="Get a list of atomic steps"),
    create=extend_schema(summary="Create atomic step", description="Create a new atomic step"),
    retrieve=extend_schema(summary="Get atomic step", description="Get a specific atomic step"),
    update=extend_schema(summary="Update atomic step", description="Update an atomic step"),
    destroy=extend_schema(summary="Delete atomic step", description="Delete an atomic step"),
)
class AtomicStepViewSet(viewsets.ModelViewSet):
    """原子步骤管理视图集"""
    
    queryset = AtomicStep.objects.all()
    serializer_class = AtomicStepSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 用户只能看到自己创建的私有步骤和所有公共步骤
        user_filter = Q(created_by=self.request.user) | Q(is_public=True)
        queryset = queryset.filter(user_filter)
        
        # 根据步骤类型过滤
        step_type = self.request.query_params.get('step_type')
        if step_type:
            queryset = queryset.filter(step_type=step_type)
        
        # 根据是否公共过滤
        is_public = self.request.query_params.get('is_public')
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public.lower() == 'true')
        
        return queryset.select_related('created_by').prefetch_related('dependencies')
    
    @extend_schema(
        summary="Get simple steps",
        description="Get simplified list of atomic steps for selection"
    )
    @action(detail=False, methods=['get'])
    def simple(self, request):
        """获取简化的步骤列表，用于选择"""
        queryset = self.get_queryset()
        serializer = AtomicStepSimpleSerializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary="List pipeline executions", description="Get a list of pipeline executions"),
    retrieve=extend_schema(summary="Get pipeline execution", description="Get a specific pipeline execution"),
    update=extend_schema(summary="Update pipeline execution", description="Update a pipeline execution"),
)
class PipelineExecutionViewSet(viewsets.ModelViewSet):
    """流水线执行管理视图集"""
    
    queryset = PipelineExecution.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']  # 只读，不允许直接创建或删除
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PipelineExecutionListSerializer
        return PipelineExecutionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 根据流水线过滤
        pipeline_id = self.request.query_params.get('pipeline_id')
        if pipeline_id:
            queryset = queryset.filter(pipeline_id=pipeline_id)
        
        # 根据工具过滤
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
        
        return queryset.select_related(
            'pipeline', 'cicd_tool', 'triggered_by'
        ).prefetch_related('step_executions')
    
    @extend_schema(
        summary="Cancel execution",
        description="Cancel a running pipeline execution"
    )
    @action(detail=True, methods=['post'])
    async def cancel(self, request, pk=None):
        """取消流水线执行"""
        execution = self.get_object()
        
        if execution.status not in ['pending', 'running']:
            return Response(
                {'error': 'Execution cannot be cancelled in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            success = await cicd_engine.cancel_execution(execution.id)
            
            if success:
                # 刷新对象以获取最新状态
                execution.refresh_from_db()
                serializer = self.get_serializer(execution)
                return Response(serializer.data)
            else:
                return Response(
                    {'error': 'Failed to cancel execution'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        except Exception as e:
            logger.error(f"Failed to cancel execution {execution.id}: {e}")
            return Response(
                {'error': f"Failed to cancel execution: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get execution logs",
        description="Get logs for a pipeline execution"
    )
    @action(detail=True, methods=['get'])
    async def logs(self, request, pk=None):
        """获取执行日志"""
        execution = self.get_object()
        
        try:
            logs = await cicd_engine.get_execution_logs(execution.id)
            
            return Response({
                'execution_id': execution.id,
                'logs': logs,
                'last_updated': execution.updated_at
            })
        
        except Exception as e:
            logger.error(f"Failed to get logs for execution {execution.id}: {e}")
            return Response(
                {'error': f"Failed to get logs: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Refresh status",
        description="Refresh the status of a pipeline execution from external tool"
    )
    @action(detail=True, methods=['post'])
    async def refresh_status(self, request, pk=None):
        """刷新执行状态"""
        execution = self.get_object()
        
        if not execution.external_id:
            return Response(
                {'error': 'No external ID available for status refresh'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 这里可以实现从外部工具刷新状态的逻辑
            # 目前先返回当前状态
            serializer = self.get_serializer(execution)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f"Failed to refresh status for execution {execution.id}: {e}")
            return Response(
                {'error': f"Failed to refresh status: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
