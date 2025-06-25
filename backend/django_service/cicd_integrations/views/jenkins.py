"""
Jenkins 特定功能视图混入类
包含所有Jenkins特定的作业管理功能
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
import logging

from ..adapters import JenkinsAdapter

logger = logging.getLogger(__name__)


class JenkinsManagementMixin:
    """Jenkins管理功能混入类，提供所有Jenkins特定的API端点"""
    
    def _validate_jenkins_tool(self, tool):
        """验证工具是否为Jenkins类型"""
        if tool.tool_type != 'jenkins':
            return Response(
                {'error': 'This operation is only available for Jenkins tools'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return None
    
    def _create_jenkins_adapter(self, tool):
        """创建Jenkins适配器实例"""
        return JenkinsAdapter(
            base_url=tool.base_url,
            username=tool.username,
            token=tool.token,
            **tool.config
        )
    
    # ==========================
    # Jenkins作业管理功能
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
        
        validation_error = self._validate_jenkins_tool(tool)
        if validation_error:
            return validation_error
        
        try:
            adapter = self._create_jenkins_adapter(tool)
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
        
        validation_error = self._validate_jenkins_tool(tool)
        if validation_error:
            return validation_error
        
        job_name = request.query_params.get('job_name')
        if not job_name:
            return Response(
                {'error': 'job_name parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = self._create_jenkins_adapter(tool)
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
        
        validation_error = self._validate_jenkins_tool(tool)
        if validation_error:
            return validation_error
        
        job_name = request.data.get('job_name')
        job_config = request.data.get('job_config')
        sample_job = request.data.get('sample_job', False)
        
        if not job_name:
            return Response(
                {'error': 'job_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = self._create_jenkins_adapter(tool)
            
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
        
        validation_error = self._validate_jenkins_tool(tool)
        if validation_error:
            return validation_error
        
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
            adapter = self._create_jenkins_adapter(tool)
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
        
        validation_error = self._validate_jenkins_tool(tool)
        if validation_error:
            return validation_error
        
        job_name = request.data.get('job_name')
        parameters = request.data.get('parameters', {})
        wait_for_start = request.data.get('wait_for_start', True)
        
        if not job_name:
            return Response(
                {'error': 'job_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = self._create_jenkins_adapter(tool)
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
        
        validation_error = self._validate_jenkins_tool(tool)
        if validation_error:
            return validation_error
        
        job_name = request.data.get('job_name')
        build_number = request.data.get('build_number')
        
        if not job_name or not build_number:
            return Response(
                {'error': 'job_name and build_number are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = self._create_jenkins_adapter(tool)
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
        
        validation_error = self._validate_jenkins_tool(tool)
        if validation_error:
            return validation_error
        
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
            adapter = self._create_jenkins_adapter(tool)
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
        
        validation_error = self._validate_jenkins_tool(tool)
        if validation_error:
            return validation_error
        
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
            adapter = self._create_jenkins_adapter(tool)
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
        
        validation_error = self._validate_jenkins_tool(tool)
        if validation_error:
            return validation_error
        
        try:
            adapter = self._create_jenkins_adapter(tool)
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
        
        validation_error = self._validate_jenkins_tool(tool)
        if validation_error:
            return validation_error
        
        job_name = request.data.get('job_name')
        if not job_name:
            return Response(
                {'error': 'job_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = self._create_jenkins_adapter(tool)
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
        
        validation_error = self._validate_jenkins_tool(tool)
        if validation_error:
            return validation_error
        
        job_name = request.data.get('job_name')
        if not job_name:
            return Response(
                {'error': 'job_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = self._create_jenkins_adapter(tool)
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
        
        validation_error = self._validate_jenkins_tool(tool)
        if validation_error:
            return validation_error
        
        job_name = request.query_params.get('job_name')
        build_number = request.query_params.get('build_number')
        
        if not job_name or not build_number:
            return Response(
                {'error': 'job_name and build_number parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = self._create_jenkins_adapter(tool)
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
