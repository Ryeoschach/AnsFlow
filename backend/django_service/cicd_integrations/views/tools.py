"""
CI/CD 工具管理视图
负责工具的注册、配置、健康检查、基础流水线执行等核心功能
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
import logging

from ..models import CICDTool
from ..serializers import (
    CICDToolSerializer, CICDToolCreateSerializer,
    PipelineExecutionCreateSerializer, PipelineExecutionSerializer
)
from ..services import cicd_engine
from pipelines.models import Pipeline
from .jenkins import JenkinsManagementMixin

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(summary="List CI/CD tools", description="Get a list of CI/CD tools"),
    create=extend_schema(summary="Register CI/CD tool", description="Register a new CI/CD tool"),
    retrieve=extend_schema(summary="Get CI/CD tool", description="Get a specific CI/CD tool"),
    update=extend_schema(summary="Update CI/CD tool", description="Update a CI/CD tool"),
    destroy=extend_schema(summary="Delete CI/CD tool", description="Delete a CI/CD tool"),
)
class CICDToolViewSet(JenkinsManagementMixin, viewsets.ModelViewSet):
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
    
    @extend_schema(
        summary="Get tool capabilities",
        description="Get the capabilities and supported features of a CI/CD tool"
    )
    @action(detail=True, methods=['get'])
    async def capabilities(self, request, pk=None):
        """获取工具能力信息"""
        tool = self.get_object()
        
        try:
            capabilities = await cicd_engine.get_tool_capabilities(tool)
            
            return Response({
                'tool_id': tool.id,
                'tool_name': tool.name,
                'tool_type': tool.tool_type,
                'capabilities': capabilities
            })
            
        except Exception as e:
            logger.error(f"Failed to get capabilities for tool {tool.id}: {e}")
            return Response(
                {'error': f"Failed to get tool capabilities: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Test tool connection",
        description="Test the connection to a CI/CD tool"
    )
    @action(detail=True, methods=['post'])
    async def test_connection(self, request, pk=None):
        """测试工具连接"""
        tool = self.get_object()
        
        try:
            connection_result = await cicd_engine.test_tool_connection(tool)
            
            return Response({
                'tool_id': tool.id,
                'tool_name': tool.name,
                'connection_test': connection_result,
                'message': 'Connection test completed'
            })
            
        except Exception as e:
            logger.error(f"Failed to test connection for tool {tool.id}: {e}")
            return Response(
                {'error': f"Failed to test connection: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
