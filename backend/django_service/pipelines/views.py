import logging

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Pipeline, PipelineStep, PipelineRun, PipelineToolMapping
from .serializers import (
    PipelineSerializer, 
    PipelineListSerializer, 
    PipelineStepSerializer, 
    PipelineRunSerializer,
    PipelineToolMappingSerializer
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
