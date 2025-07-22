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
    CICDToolSerializer, CICDToolUpdateSerializer,
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
            return CICDToolSerializer
        elif self.action in ['update', 'partial_update']:
            return CICDToolUpdateSerializer
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
    
    def perform_create(self, serializer):
        """创建 CI/CD 工具并进行健康检查"""
        tool_data = serializer.validated_data
        tool_data['created_by'] = self.request.user
        
        # 添加调试日志
        logger.info(f"Creating CI/CD tool with data: {tool_data}")
        logger.info(f"Project from validated_data: {tool_data.get('project')}")
        
        try:
            # 暂时使用简单的创建方式，不使用异步引擎
            tool = serializer.save()
            logger.info(f"Tool created successfully: {tool.id}, project: {tool.project}")
            return tool
        except Exception as e:
            logger.error(f"Failed to register CI/CD tool: {e}")
            raise
    
    @extend_schema(
        summary="Health check tool",
        description="Perform health check on a CI/CD tool"
    )
    @action(detail=True, methods=['post'])
    def health_check(self, request, pk=None):
        """执行工具健康检查"""
        tool = self.get_object()
        
        try:
            # 简单的健康检查实现
            import requests
            from django.utils import timezone
            
            if tool.tool_type == 'jenkins':
                try:
                    auth = None
                    if tool.username and tool.token:
                        auth = requests.auth.HTTPBasicAuth(tool.username, tool.token)
                    
                    response = requests.get(
                        f"{tool.base_url}/api/json",
                        auth=auth,
                        timeout=10,
                        verify=False
                    )
                    
                    # Jenkins响应分析：
                    # 200: 认证成功，服务健康
                    # 401: 认证失败，需要正确的认证信息
                    # 403: 认证失败或权限不足
                    # 其他: 服务不可用
                    
                    if response.status_code == 200:
                        tool.status = 'authenticated'  # 在线已认证
                        is_healthy = True
                        message = 'Jenkins service is healthy and authenticated'
                        detailed_status = 'authenticated'
                    elif response.status_code in [401, 403]:
                        # 如果提供了认证信息但仍然401/403，说明认证失败
                        if tool.username and tool.token:
                            tool.status = 'needs_auth'  # 认证失败
                            is_healthy = False
                            message = f'Authentication failed - please check credentials (HTTP {response.status_code})'
                            detailed_status = 'needs_auth'
                        else:
                            tool.status = 'needs_auth'  # 需要认证
                            is_healthy = True  # 服务在线，只是需要认证
                            message = f'Jenkins service is running but requires authentication (HTTP {response.status_code})'
                            detailed_status = 'needs_auth'
                    else:
                        tool.status = 'offline'  # 离线
                        is_healthy = False
                        message = f'Jenkins service is not responding correctly (HTTP {response.status_code})'
                        detailed_status = 'offline'
                    
                    tool.last_health_check = timezone.now()
                    tool.save(update_fields=['status', 'last_health_check'])
                    
                except Exception as e:
                    is_healthy = False
                    tool.status = 'offline'
                    tool.last_health_check = timezone.now()
                    tool.save(update_fields=['status', 'last_health_check'])
                    message = f'Health check failed: {str(e)}'
                    detailed_status = 'offline'
            else:
                is_healthy = False
                message = 'Unsupported tool type for health check'
                detailed_status = 'unknown'
            
            return Response({
                'tool_id': tool.id,
                'tool_name': tool.name,
                'tool_type': tool.tool_type,
                'status': tool.status,
                'detailed_status': detailed_status,
                'is_healthy': is_healthy,
                'last_check': tool.last_health_check,
                'message': message
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
    def execute_pipeline(self, request, pk=None):
        """使用此工具执行流水线"""
        tool = self.get_object()
        serializer = PipelineExecutionCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            try:
                pipeline = Pipeline.objects.get(id=serializer.validated_data['pipeline_id'])
                
                # 简化的流水线执行实现
                from ..models import PipelineExecution
                execution = PipelineExecution.objects.create(
                    pipeline=pipeline,
                    cicd_tool=tool,
                    status='pending',
                    trigger_type=serializer.validated_data['trigger_type'],
                    triggered_by=request.user,
                    definition=pipeline.config or {},
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
    def capabilities(self, request, pk=None):
        """获取工具能力信息"""
        tool = self.get_object()
        
        try:
            # 简单的能力信息返回
            capabilities = {
                'supported_features': [],
                'max_concurrent_jobs': 0,
                'supported_scm': [],
                'available_plugins': []
            }
            
            if tool.tool_type == 'jenkins':
                capabilities = {
                    'supported_features': ['build', 'deploy', 'test', 'pipeline'],
                    'max_concurrent_jobs': 10,
                    'supported_scm': ['git', 'svn'],
                    'available_plugins': ['git', 'pipeline', 'build-timeout']
                }
            
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
    def test_connection(self, request, pk=None):
        """测试工具连接"""
        tool = self.get_object()
        
        try:
            # 使用同步方式测试连接，避免 httpx 代理问题
            import requests
            from django.utils import timezone
            
            if tool.tool_type == 'jenkins':
                try:
                    # 测试 Jenkins API 连接
                    import requests.auth
                    auth = requests.auth.HTTPBasicAuth(tool.username, tool.token) if tool.username and tool.token else None
                    
                    response = requests.get(
                        f"{tool.base_url}/api/json",
                        auth=auth,
                        timeout=10,
                        verify=False,
                        proxies={'http': None, 'https': None}  # 禁用代理
                    )
                    
                    if response.status_code == 200:
                        # 更新工具状态
                        tool.status = 'active'
                        tool.last_health_check = timezone.now()
                        tool.save(update_fields=['status', 'last_health_check'])
                        
                        connection_result = {
                            'success': True,
                            'message': f'Successfully connected to Jenkins at {tool.base_url}',
                            'status': 'online',
                            'response_time': f'{response.elapsed.total_seconds():.2f}s'
                        }
                    else:
                        tool.status = 'error'
                        tool.save(update_fields=['status'])
                        
                        connection_result = {
                            'success': False,
                            'message': f'Jenkins returned status code {response.status_code}',
                            'status': 'offline',
                            'error': f'HTTP {response.status_code}'
                        }
                
                except requests.exceptions.ConnectionError:
                    tool.status = 'error'
                    tool.save(update_fields=['status'])
                    
                    connection_result = {
                        'success': False,
                        'message': f'Cannot connect to Jenkins at {tool.base_url}',
                        'status': 'offline',
                        'error': 'Connection refused'
                    }
                
                except requests.exceptions.Timeout:
                    tool.status = 'error'
                    tool.save(update_fields=['status'])
                    
                    connection_result = {
                        'success': False,
                        'message': f'Timeout connecting to Jenkins at {tool.base_url}',
                        'status': 'offline',
                        'error': 'Connection timeout'
                    }
            
            else:
                connection_result = {
                    'success': False,
                    'message': f'Connection test not implemented for {tool.tool_type}',
                    'status': 'unknown',
                    'error': 'Not implemented'
                }
            
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

    @extend_schema(
        summary="Create local executor",
        description="Create system default local executor tool"
    )
    @action(detail=False, methods=['post'])
    def create_local_executor(self, request):
        """创建系统默认的本地执行器工具"""
        try:
            from project_management.models import Project
            from django.contrib.auth import get_user_model
            from django.db import transaction
            
            User = get_user_model()
            
            with transaction.atomic():
                # 检查是否已存在本地执行器
                existing_local_tool = CICDTool.objects.filter(tool_type='local').first()
                if existing_local_tool:
                    return Response({
                        'success': True,
                        'message': '本地执行器已存在',
                        'tool': {
                            'id': existing_local_tool.id,
                            'name': existing_local_tool.name,
                            'status': existing_local_tool.status
                        }
                    })
                
                # 获取或创建系统项目
                system_project, project_created = Project.objects.get_or_create(
                    name='系统项目',
                    defaults={
                        'description': '用于存放系统级工具和配置的项目',
                        'owner': User.objects.filter(is_superuser=True).first() or User.objects.first(),
                        'is_active': True,
                        'visibility': 'private'
                    }
                )
                
                # 创建本地执行器
                local_executor = CICDTool.objects.create(
                    tool_type='local',
                    project=system_project,
                    name='AnsFlow 本地执行器',
                    description='系统内置的本地执行器，用于在AnsFlow服务器上直接执行流水线步骤',
                    base_url='http://localhost:8000',
                    username='system',
                    token='local-executor-token',
                    status='active',
                    created_by=request.user,
                    config={
                        'executor_type': 'local',
                        'max_concurrent_jobs': 5,
                        'timeout': 3600,
                        'enable_logs': True,
                        'workspace_path': '/tmp/ansflow-workspace',
                        'is_default': True
                    }
                )
                
                logger.info(f"Created local executor tool: {local_executor.name} (ID: {local_executor.id})")
                
                return Response({
                    'success': True,
                    'message': '本地执行器创建成功',
                    'tool': {
                        'id': local_executor.id,
                        'name': local_executor.name,
                        'tool_type': local_executor.tool_type,
                        'status': local_executor.status,
                        'base_url': local_executor.base_url,
                        'description': local_executor.description
                    }
                })
                
        except Exception as e:
            logger.error(f"Failed to create local executor: {e}")
            return Response(
                {'success': False, 'error': f"创建本地执行器失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
