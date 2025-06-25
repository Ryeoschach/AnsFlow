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
import json

from .models import CICDTool, AtomicStep, PipelineExecution, StepExecution
from .serializers import (
    CICDToolSerializer, CICDToolCreateSerializer, AtomicStepSerializer,
    AtomicStepSimpleSerializer, PipelineExecutionSerializer,
    PipelineExecutionListSerializer, PipelineExecutionCreateSerializer,
    HealthCheckSerializer, ToolStatusSerializer
)
from .services import cicd_engine
from pipelines.models import Pipeline
from .adapters import JenkinsAdapter

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

    # ==========================
    # Jenkins特定的作业管理功能
    # ==========================
    
    @extend_schema(
        summary="List Jenkins jobs",
        description="Get a list of all Jenkins jobs (Jenkins only)",
        parameters=[
            {
                'name': 'folder_path',
                'in': 'query',
                'required': False,
                'description': 'Jenkins folder path (for organized jobs)',
                'schema': {'type': 'string'}
            }
        ]
    )
    @action(detail=True, methods=['get'], url_path='jenkins/jobs')
    async def jenkins_list_jobs(self, request, pk=None):
        """获取Jenkins作业列表 (仅限Jenkins工具)"""
        tool = self.get_object()
        
        if tool.tool_type != 'jenkins':
            return Response(
                {'error': 'This operation is only available for Jenkins tools'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 创建Jenkins适配器
            adapter = JenkinsAdapter(
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            folder_path = request.query_params.get('folder_path', '')
            jobs = await adapter.list_jobs(folder_path)
            
            return Response({
                'tool_id': tool.id,
                'tool_name': tool.name,
                'folder_path': folder_path,
                'jobs_count': len(jobs),
                'jobs': jobs
            })
            
        except Exception as e:
            logger.error(f"Failed to list Jenkins jobs for tool {tool.id}: {e}")
            return Response(
                {'error': f"Failed to list jobs: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get Jenkins job info",
        description="Get detailed information about a specific Jenkins job",
        parameters=[
            {
                'name': 'job_name',
                'in': 'query',
                'required': True,
                'description': 'Name of the Jenkins job',
                'schema': {'type': 'string'}
            }
        ]
    )
    @action(detail=True, methods=['get'], url_path='jenkins/job-info')
    async def jenkins_job_info(self, request, pk=None):
        """获取Jenkins作业详细信息"""
        tool = self.get_object()
        
        if tool.tool_type != 'jenkins':
            return Response(
                {'error': 'This operation is only available for Jenkins tools'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job_name = request.query_params.get('job_name')
        if not job_name:
            return Response(
                {'error': 'job_name parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = JenkinsAdapter(
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            job_info = await adapter.get_job_info(job_name)
            
            if job_info:
                return Response({
                    'tool_id': tool.id,
                    'job_name': job_name,
                    'job_info': job_info
                })
            else:
                return Response(
                    {'error': f'Job "{job_name}" not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            logger.error(f"Failed to get Jenkins job info for {job_name}: {e}")
            return Response(
                {'error': f"Failed to get job info: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Create Jenkins job",
        description="Create a new Jenkins job",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'job_name': {'type': 'string', 'description': 'Name of the job to create'},
                    'job_config': {'type': 'string', 'description': 'Jenkins XML configuration'},
                    'sample_job': {'type': 'boolean', 'description': 'Create a sample job with default configuration', 'default': False}
                },
                'required': ['job_name']
            }
        }
    )
    @action(detail=True, methods=['post'], url_path='jenkins/create-job')
    async def jenkins_create_job(self, request, pk=None):
        """创建Jenkins作业"""
        tool = self.get_object()
        
        if tool.tool_type != 'jenkins':
            return Response(
                {'error': 'This operation is only available for Jenkins tools'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job_name = request.data.get('job_name')
        job_config = request.data.get('job_config')
        sample_job = request.data.get('sample_job', False)
        
        if not job_name:
            return Response(
                {'error': 'job_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = JenkinsAdapter(
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            # 如果没有提供配置且要创建示例作业，使用默认配置
            if not job_config and sample_job:
                job_config = '''<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.40">
  <actions/>
  <description>Sample job created via AnsFlow API</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.92">
    <script>
pipeline {
    agent any
    
    stages {
        stage('Hello') {
            steps {
                echo 'Hello World from AnsFlow!'
                sh 'echo "Build Number: ${BUILD_NUMBER}"'
                sh 'echo "Current Date: $(date)"'
            }
        }
    }
}
    </script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>'''
            
            if not job_config:
                return Response(
                    {'error': 'job_config is required or set sample_job=true'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            success = await adapter.create_job(job_name, job_config)
            
            if success:
                return Response({
                    'tool_id': tool.id,
                    'job_name': job_name,
                    'message': f'Job "{job_name}" created successfully',
                    'job_url': f"{tool.base_url}/job/{job_name}"
                })
            else:
                return Response(
                    {'error': f'Failed to create job "{job_name}"'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Failed to create Jenkins job {job_name}: {e}")
            return Response(
                {'error': f"Failed to create job: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Delete Jenkins job",
        description="Delete a Jenkins job",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'job_name': {'type': 'string', 'description': 'Name of the job to delete'},
                    'confirm': {'type': 'boolean', 'description': 'Confirmation flag', 'default': False}
                },
                'required': ['job_name', 'confirm']
            }
        }
    )
    @action(detail=True, methods=['delete'], url_path='jenkins/delete-job')
    async def jenkins_delete_job(self, request, pk=None):
        """删除Jenkins作业"""
        tool = self.get_object()
        
        if tool.tool_type != 'jenkins':
            return Response(
                {'error': 'This operation is only available for Jenkins tools'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job_name = request.data.get('job_name')
        confirm = request.data.get('confirm', False)
        
        if not job_name:
            return Response(
                {'error': 'job_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not confirm:
            return Response(
                {'error': 'confirm=true is required for job deletion'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = JenkinsAdapter(
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            success = await adapter.delete_job(job_name)
            
            if success:
                return Response({
                    'tool_id': tool.id,
                    'job_name': job_name,
                    'message': f'Job "{job_name}" deleted successfully'
                })
            else:
                return Response(
                    {'error': f'Failed to delete job "{job_name}"'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Failed to delete Jenkins job {job_name}: {e}")
            return Response(
                {'error': f"Failed to delete job: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Start Jenkins build",
        description="Start a new build for a Jenkins job",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'job_name': {'type': 'string', 'description': 'Name of the job to build'},
                    'parameters': {'type': 'object', 'description': 'Build parameters (key-value pairs)'},
                    'wait_for_start': {'type': 'boolean', 'description': 'Wait for build to start', 'default': True}
                },
                'required': ['job_name']
            }
        }
    )
    @action(detail=True, methods=['post'], url_path='jenkins/start-build')
    async def jenkins_start_build(self, request, pk=None):
        """启动Jenkins构建"""
        tool = self.get_object()
        
        if tool.tool_type != 'jenkins':
            return Response(
                {'error': 'This operation is only available for Jenkins tools'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job_name = request.data.get('job_name')
        parameters = request.data.get('parameters', {})
        wait_for_start = request.data.get('wait_for_start', True)
        
        if not job_name:
            return Response(
                {'error': 'job_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = JenkinsAdapter(
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            build_info = await adapter.start_build(job_name, parameters, wait_for_start)
            
            return Response({
                'tool_id': tool.id,
                'job_name': job_name,
                'build_info': build_info,
                'message': f'Build started for job "{job_name}"'
            })
                
        except Exception as e:
            logger.error(f"Failed to start Jenkins build for {job_name}: {e}")
            return Response(
                {'error': f"Failed to start build: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Stop Jenkins build",
        description="Stop a running Jenkins build",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'job_name': {'type': 'string', 'description': 'Name of the job'},
                    'build_number': {'type': 'string', 'description': 'Build number to stop'}
                },
                'required': ['job_name', 'build_number']
            }
        }
    )
    @action(detail=True, methods=['post'], url_path='jenkins/stop-build')
    async def jenkins_stop_build(self, request, pk=None):
        """停止Jenkins构建"""
        tool = self.get_object()
        
        if tool.tool_type != 'jenkins':
            return Response(
                {'error': 'This operation is only available for Jenkins tools'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job_name = request.data.get('job_name')
        build_number = request.data.get('build_number')
        
        if not job_name or not build_number:
            return Response(
                {'error': 'job_name and build_number are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = JenkinsAdapter(
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            success = await adapter.stop_build(job_name, build_number)
            
            if success:
                return Response({
                    'tool_id': tool.id,
                    'job_name': job_name,
                    'build_number': build_number,
                    'message': f'Build #{build_number} stopped for job "{job_name}"'
                })
            else:
                return Response(
                    {'error': f'Failed to stop build #{build_number} for job "{job_name}"'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Failed to stop Jenkins build {job_name}#{build_number}: {e}")
            return Response(
                {'error': f"Failed to stop build: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get Jenkins job builds",
        description="Get build history for a Jenkins job",
        parameters=[
            {
                'name': 'job_name',
                'in': 'query',
                'required': True,
                'description': 'Name of the Jenkins job',
                'schema': {'type': 'string'}
            },
            {
                'name': 'limit',
                'in': 'query',
                'required': False,
                'description': 'Maximum number of builds to return',
                'schema': {'type': 'integer', 'default': 20}
            },
            {
                'name': 'offset',
                'in': 'query',
                'required': False,
                'description': 'Number of builds to skip',
                'schema': {'type': 'integer', 'default': 0}
            }
        ]
    )
    @action(detail=True, methods=['get'], url_path='jenkins/job-builds')
    async def jenkins_job_builds(self, request, pk=None):
        """获取Jenkins作业构建历史"""
        tool = self.get_object()
        
        if tool.tool_type != 'jenkins':
            return Response(
                {'error': 'This operation is only available for Jenkins tools'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job_name = request.query_params.get('job_name')
        if not job_name:
            return Response(
                {'error': 'job_name parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            limit = int(request.query_params.get('limit', 20))
            offset = int(request.query_params.get('offset', 0))
        except ValueError:
            return Response(
                {'error': 'limit and offset must be integers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = JenkinsAdapter(
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            builds = await adapter.get_job_builds(job_name, limit, offset)
            
            return Response({
                'tool_id': tool.id,
                'job_name': job_name,
                'limit': limit,
                'offset': offset,
                'builds_count': len(builds),
                'builds': builds
            })
                
        except Exception as e:
            logger.error(f"Failed to get Jenkins job builds for {job_name}: {e}")
            return Response(
                {'error': f"Failed to get job builds: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get Jenkins build logs",
        description="Get console logs for a specific Jenkins build",
        parameters=[
            {
                'name': 'job_name',
                'in': 'query',
                'required': True,
                'description': 'Name of the Jenkins job',
                'schema': {'type': 'string'}
            },
            {
                'name': 'build_number',
                'in': 'query',
                'required': True,
                'description': 'Build number',
                'schema': {'type': 'string'}
            },
            {
                'name': 'start',
                'in': 'query',
                'required': False,
                'description': 'Start position for incremental log retrieval',
                'schema': {'type': 'integer', 'default': 0}
            }
        ]
    )
    @action(detail=True, methods=['get'], url_path='jenkins/build-logs')
    async def jenkins_build_logs(self, request, pk=None):
        """获取Jenkins构建日志"""
        tool = self.get_object()
        
        if tool.tool_type != 'jenkins':
            return Response(
                {'error': 'This operation is only available for Jenkins tools'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job_name = request.query_params.get('job_name')
        build_number = request.query_params.get('build_number')
        
        if not job_name or not build_number:
            return Response(
                {'error': 'job_name and build_number parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start = int(request.query_params.get('start', 0))
        except ValueError:
            return Response(
                {'error': 'start must be an integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = JenkinsAdapter(
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            log_data = await adapter.get_build_console_log(job_name, build_number, start)
            
            return Response({
                'tool_id': tool.id,
                'job_name': job_name,
                'build_number': build_number,
                'log_data': log_data
            })
                
        except Exception as e:
            logger.error(f"Failed to get Jenkins build logs for {job_name}#{build_number}: {e}")
            return Response(
                {'error': f"Failed to get build logs: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get Jenkins queue info",
        description="Get information about Jenkins build queue"
    )
    @action(detail=True, methods=['get'], url_path='jenkins/queue')
    async def jenkins_queue_info(self, request, pk=None):
        """获取Jenkins构建队列信息"""
        tool = self.get_object()
        
        if tool.tool_type != 'jenkins':
            return Response(
                {'error': 'This operation is only available for Jenkins tools'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = JenkinsAdapter(
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            queue_info = await adapter.get_queue_info()
            
            return Response({
                'tool_id': tool.id,
                'tool_name': tool.name,
                'queue_count': len(queue_info),
                'queue_items': queue_info
            })
                
        except Exception as e:
            logger.error(f"Failed to get Jenkins queue info for tool {tool.id}: {e}")
            return Response(
                {'error': f"Failed to get queue info: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Enable Jenkins job",
        description="Enable a Jenkins job",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'job_name': {'type': 'string', 'description': 'Name of the job to enable'}
                },
                'required': ['job_name']
            }
        }
    )
    @action(detail=True, methods=['post'], url_path='jenkins/enable-job')
    async def jenkins_enable_job(self, request, pk=None):
        """启用Jenkins作业"""
        tool = self.get_object()
        
        if tool.tool_type != 'jenkins':
            return Response(
                {'error': 'This operation is only available for Jenkins tools'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job_name = request.data.get('job_name')
        if not job_name:
            return Response(
                {'error': 'job_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = JenkinsAdapter(
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            success = await adapter.enable_job(job_name)
            
            if success:
                return Response({
                    'tool_id': tool.id,
                    'job_name': job_name,
                    'message': f'Job "{job_name}" enabled successfully'
                })
            else:
                return Response(
                    {'error': f'Failed to enable job "{job_name}"'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Failed to enable Jenkins job {job_name}: {e}")
            return Response(
                {'error': f"Failed to enable job: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Disable Jenkins job",
        description="Disable a Jenkins job",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'job_name': {'type': 'string', 'description': 'Name of the job to disable'}
                },
                'required': ['job_name']
            }
        }
    )
    @action(detail=True, methods=['post'], url_path='jenkins/disable-job')
    async def jenkins_disable_job(self, request, pk=None):
        """禁用Jenkins作业"""
        tool = self.get_object()
        
        if tool.tool_type != 'jenkins':
            return Response(
                {'error': 'This operation is only available for Jenkins tools'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job_name = request.data.get('job_name')
        if not job_name:
            return Response(
                {'error': 'job_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = JenkinsAdapter(
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            success = await adapter.disable_job(job_name)
            
            if success:
                return Response({
                    'tool_id': tool.id,
                    'job_name': job_name,
                    'message': f'Job "{job_name}" disabled successfully'
                })
            else:
                return Response(
                    {'error': f'Failed to disable job "{job_name}"'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Failed to disable Jenkins job {job_name}: {e}")
            return Response(
                {'error': f"Failed to disable job: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get Jenkins build info",
        description="Get detailed information about a specific Jenkins build",
        parameters=[
            {
                'name': 'job_name',
                'in': 'query',
                'required': True,
                'description': 'Name of the Jenkins job',
                'schema': {'type': 'string'}
            },
            {
                'name': 'build_number',
                'in': 'query',
                'required': True,
                'description': 'Build number',
                'schema': {'type': 'string'}
            }
        ]
    )
    @action(detail=True, methods=['get'], url_path='jenkins/build-info')
    async def jenkins_build_info(self, request, pk=None):
        """获取Jenkins构建详细信息"""
        tool = self.get_object()
        
        if tool.tool_type != 'jenkins':
            return Response(
                {'error': 'This operation is only available for Jenkins tools'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job_name = request.query_params.get('job_name')
        build_number = request.query_params.get('build_number')
        
        if not job_name or not build_number:
            return Response(
                {'error': 'job_name and build_number parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = JenkinsAdapter(
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            build_info = await adapter.get_build_info(job_name, build_number)
            
            if build_info:
                return Response({
                    'tool_id': tool.id,
                    'job_name': job_name,
                    'build_number': build_number,
                    'build_info': build_info
                })
            else:
                return Response(
                    {'error': f'Build #{build_number} not found for job "{job_name}"'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            logger.error(f"Failed to get Jenkins build info for {job_name}#{build_number}: {e}")
            return Response(
                {'error': f"Failed to get build info: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==============================
# 流水线执行管理视图集
# ==============================

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
            queryset = queryset.filter(tool_id=tool_id)
        
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
        
        return queryset.select_related('pipeline', 'tool', 'triggered_by').order_by('-created_at')
    
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
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count, Avg, Q
        
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
            queryset = queryset.filter(tool_id=tool_id)
        
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


# ==============================
# 原子步骤管理视图集
# ==============================

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
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['list']:
            return AtomicStepSimpleSerializer
        return AtomicStepSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 根据类别过滤
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # 根据CI/CD工具类型过滤
        tool_type = self.request.query_params.get('tool_type')
        if tool_type:
            queryset = queryset.filter(supported_tools__contains=[tool_type])
        
        # 搜索
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )
        
        return queryset.order_by('category', 'name')
    
    def perform_create(self, serializer):
        """创建原子步骤"""
        serializer.save(created_by=self.request.user)
    
    @extend_schema(
        summary="Test atomic step",
        description="Test an atomic step with sample parameters",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'tool_id': {'type': 'string', 'description': 'CI/CD tool ID to test with'},
                    'parameters': {'type': 'object', 'description': 'Test parameters'}
                },
                'required': ['tool_id']
            }
        }
    )
    @action(detail=True, methods=['post'])
    async def test(self, request, pk=None):
        """测试原子步骤"""
        step = self.get_object()
        tool_id = request.data.get('tool_id')
        parameters = request.data.get('parameters', {})
        
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
        
        try:
            # 使用统一引擎测试步骤
            result = await cicd_engine.test_atomic_step(
                step=step,
                tool=tool,
                parameters=parameters,
                user=request.user
            )
            
            return Response({
                'step_id': step.id,
                'tool_id': tool.id,
                'test_result': result,
                'message': 'Atomic step test completed'
            })
            
        except Exception as e:
            logger.error(f"Failed to test atomic step {step.id}: {e}")
            return Response(
                {'error': f"Failed to test step: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get step categories",
        description="Get available atomic step categories"
    )
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """获取原子步骤类别"""
        categories = AtomicStep.objects.values_list('category', flat=True).distinct()
        
        category_stats = []
        for category in categories:
            count = AtomicStep.objects.filter(category=category).count()
            category_stats.append({
                'name': category,
                'count': count
            })
        
        return Response({
            'categories': category_stats,
            'total_categories': len(categories)
        })
