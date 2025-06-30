"""
Jenkins 特定功能视图混入类 - 简化版本
包含基本的Jenkins管理功能，使用同步实现
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from requests.auth import HTTPBasicAuth
import logging
import requests

logger = logging.getLogger(__name__)


class JenkinsManagementMixin:
    """Jenkins管理功能混入类，提供基本的Jenkins API端点"""
    
    def _validate_jenkins_tool(self, tool):
        """验证工具是否为Jenkins类型"""
        if tool.tool_type != 'jenkins':
            return Response(
                {'error': 'This operation is only available for Jenkins tools'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return None
    
    def _get_jenkins_auth(self, tool):
        """获取Jenkins认证信息"""
        if tool.username and tool.token:
            return requests.auth.HTTPBasicAuth(tool.username, tool.token)
        return None
    
    def _get_jenkins_crumb(self, tool, auth):
        """获取Jenkins CSRF token"""
        try:
            response = requests.get(
                f"{tool.base_url}/crumbIssuer/api/json",
                auth=auth,
                timeout=10,
                verify=False
            )
            if response.status_code == 200:
                crumb_data = response.json()
                return {crumb_data['crumbRequestField']: crumb_data['crumb']}
        except:
            pass
        return {}
    
    # ==========================
    # Jenkins作业管理功能
    # ==========================
    
    @extend_schema(
        summary="List Jenkins jobs",
        description="Get a list of all Jenkins jobs"
    )
    @action(detail=True, methods=['get'], url_path='jenkins/jobs')
    def jenkins_jobs(self, request, pk=None):
        """获取Jenkins作业列表"""
        tool = self.get_object()
        
        validation_error = self._validate_jenkins_tool(tool)
        if validation_error:
            return validation_error
        
        try:
            auth = self._get_jenkins_auth(tool)
            
            response = requests.get(
                f"{tool.base_url}/api/json",
                auth=auth,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                jenkins_data = response.json()
                jobs = jenkins_data.get('jobs', [])
                
                # 为每个作业获取更详细的信息
                detailed_jobs = []
                for job in jobs:
                    try:
                        job_response = requests.get(
                            f"{job['url']}api/json",
                            auth=auth,
                            timeout=5,
                            verify=False
                        )
                        if job_response.status_code == 200:
                            job_detail = job_response.json()
                            
                            # 处理 lastBuild 字段，确保其结构完整
                            last_build = job_detail.get('lastBuild')
                            if last_build:
                                # 如果构建结果为空且不在构建中，尝试获取最新状态
                                if (last_build.get('result') is None and 
                                    not job_detail.get('color', '').endswith('_anime')):
                                    try:
                                        # 主动获取最新构建状态
                                        build_url = f"{last_build.get('url', '')}api/json"
                                        if build_url != "api/json":  # 确保URL有效
                                            build_response = requests.get(build_url, auth=auth, timeout=3)
                                            if build_response.status_code == 200:
                                                latest_build = build_response.json()
                                                last_build = {
                                                    'number': latest_build.get('number', last_build.get('number')),
                                                    'url': latest_build.get('url', last_build.get('url')),
                                                    'timestamp': latest_build.get('timestamp', last_build.get('timestamp', 0)),
                                                    'result': latest_build.get('result'),  # 使用最新的result
                                                    'duration': latest_build.get('duration', last_build.get('duration', 0))
                                                }
                                    except Exception as e:
                                        logger.debug(f"Failed to get latest build status for {job['name']}: {e}")
                                        # 如果获取失败，使用原始数据
                                        pass
                                
                                # 确保 lastBuild 有完整的字段
                                if not isinstance(last_build, dict):
                                    last_build = {}
                                
                                last_build = {
                                    'number': last_build.get('number'),
                                    'url': last_build.get('url'),
                                    'timestamp': last_build.get('timestamp', 0),  # 默认为0而不是None
                                    'result': last_build.get('result'),
                                    'duration': last_build.get('duration', 0)
                                }
                            
                            detailed_jobs.append({
                                '_class': job_detail.get('_class', ''),
                                'name': job_detail.get('name', job['name']),
                                'url': job_detail.get('url', job['url']),
                                'color': job_detail.get('color', job['color']),
                                'buildable': job_detail.get('buildable', True),
                                'inQueue': job_detail.get('inQueue', False),
                                'description': job_detail.get('description', ''),
                                'lastBuild': last_build,
                                'healthReport': job_detail.get('healthReport', [])
                            })
                        else:
                            # 如果无法获取详细信息，使用基本信息并添加默认值
                            detailed_jobs.append({
                                '_class': job.get('_class', ''),
                                'name': job.get('name', ''),
                                'url': job.get('url', ''),
                                'color': job.get('color', 'grey'),
                                'buildable': True,
                                'inQueue': False,
                                'description': '',
                                'lastBuild': None,
                                'healthReport': []
                            })
                    except Exception as e:
                        logger.warning(f"Failed to get details for job {job.get('name', 'unknown')}: {e}")
                        # 添加基本信息
                        detailed_jobs.append({
                            '_class': job.get('_class', ''),
                            'name': job.get('name', ''),
                            'url': job.get('url', ''),
                            'color': job.get('color', 'grey'),
                            'buildable': True,
                            'inQueue': False,
                            'description': '',
                            'lastBuild': None,
                            'healthReport': []
                        })
                
                return Response({
                    'tool_id': tool.id,
                    'jobs': detailed_jobs,
                    'total_jobs': len(detailed_jobs)
                })
            else:
                return Response(
                    {'error': f'Failed to get Jenkins jobs: HTTP {response.status_code}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Failed to get Jenkins jobs for tool {tool.id}: {e}")
            return Response(
                {'error': f"Failed to get jobs: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get Jenkins job details",
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
    def jenkins_job_info(self, request, pk=None):
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
            auth = self._get_jenkins_auth(tool)
            
            response = requests.get(
                f"{tool.base_url}/job/{job_name}/api/json",
                auth=auth,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                job_info = response.json()
                return Response({
                    'tool_id': tool.id,
                    'job_name': job_name,
                    'job_info': job_info
                })
            elif response.status_code == 404:
                return Response(
                    {'error': f'Job "{job_name}" not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            else:
                return Response(
                    {'error': f'Failed to get job info: HTTP {response.status_code}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Failed to get Jenkins job info for {job_name}: {e}")
            return Response(
                {'error': f"Failed to get job info: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Trigger Jenkins build",
        description="Trigger a build for a specific Jenkins job",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'job_name': {'type': 'string', 'description': 'Name of the job to build'},
                    'parameters': {'type': 'object', 'description': 'Build parameters (optional)'}
                },
                'required': ['job_name']
            }
        }
    )
    @action(detail=True, methods=['post'], url_path='jenkins/build')
    def jenkins_build(self, request, pk=None):
        """触发Jenkins作业构建"""
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
            auth = self._get_jenkins_auth(tool)
            headers = self._get_jenkins_crumb(tool, auth)
            
            # 触发构建
            build_url = f"{tool.base_url}/job/{job_name}/build"
            parameters = request.data.get('parameters', {})
            
            if parameters:
                # 如果有参数，使用带参数的构建URL
                build_url = f"{tool.base_url}/job/{job_name}/buildWithParameters"
                
            response = requests.post(
                build_url,
                auth=auth,
                headers=headers,
                data=parameters,
                timeout=10,
                verify=False
            )
            
            if response.status_code in [200, 201]:
                return Response({
                    'tool_id': tool.id,
                    'job_name': job_name,
                    'message': 'Build triggered successfully',
                    'build_triggered': True
                })
            else:
                return Response(
                    {'error': f'Failed to trigger build: HTTP {response.status_code}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Failed to trigger Jenkins build for {job_name}: {e}")
            return Response(
                {'error': f"Failed to trigger build: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='jenkins/builds')
    def jenkins_job_builds(self, request, pk=None):
        """获取Jenkins作业构建历史（需要作业名称参数）"""
        job_name = request.query_params.get('job_name')
        if not job_name:
            return Response(
                {'error': 'job_name parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tool = self.get_object()
        try:
            auth = HTTPBasicAuth(tool.username, tool.token)
            
            # 获取作业的构建历史
            url = f"{tool.base_url}/job/{job_name}/api/json?tree=builds[number,url,timestamp,result,duration,description,estimatedDuration]"
            response = requests.get(url, auth=auth, timeout=10, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                builds = data.get('builds', [])
                
                # 处理构建数据，确保字段完整，并智能更新状态
                processed_builds = []
                for build in builds:
                    processed_build = {
                        'number': build.get('number'),
                        'url': build.get('url'),
                        'timestamp': build.get('timestamp', 0),
                        'result': build.get('result'),
                        'duration': build.get('duration', 0),
                        'description': build.get('description', ''),
                        'estimatedDuration': build.get('estimatedDuration', 0)
                    }
                    
                    # 如果构建结果为空，尝试获取最新状态
                    if (processed_build['result'] is None and 
                        processed_build.get('url')):
                        try:
                            # 获取单个构建的最新状态
                            build_detail_url = f"{processed_build['url']}api/json"
                            build_response = requests.get(build_detail_url, auth=auth, timeout=3)
                            if build_response.status_code == 200:
                                build_detail = build_response.json()
                                # 更新结果，但保持其他字段不变
                                if build_detail.get('result') is not None:
                                    processed_build['result'] = build_detail.get('result')
                                    processed_build['duration'] = build_detail.get('duration', processed_build['duration'])
                                    logger.info(f"Updated build {processed_build['number']} status to {processed_build['result']}")
                        except Exception as e:
                            logger.debug(f"Failed to get latest status for build {processed_build['number']}: {e}")
                    
                    processed_builds.append(processed_build)
                
                return Response({
                    'tool_id': tool.id,
                    'job_name': job_name,
                    'builds': processed_builds
                })
            else:
                return Response(
                    {'error': f'Failed to get builds: HTTP {response.status_code}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Failed to get Jenkins builds for tool {tool.id}, job {job_name}: {e}")
            return Response(
                {'error': f"Failed to get builds: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['delete'], url_path='jenkins/delete-job')
    def jenkins_delete_job(self, request, pk=None):
        """删除Jenkins作业 - 简化版本"""
        return Response(
            {'message': 'This feature is under development. Please use Jenkins web interface.'},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )
    
    @action(detail=True, methods=['get'], url_path='jenkins/build-logs')
    def jenkins_build_logs(self, request, pk=None):
        """获取Jenkins构建日志"""
        job_name = request.query_params.get('job_name')
        build_number = request.query_params.get('build_number')
        
        if not job_name or not build_number:
            return Response(
                {'error': 'job_name and build_number parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tool = self.get_object()
        try:
            auth = HTTPBasicAuth(tool.username, tool.token)
            
            # 获取构建的控制台日志
            url = f"{tool.base_url}/job/{job_name}/{build_number}/consoleText"
            response = requests.get(url, auth=auth, timeout=30, verify=False)
            
            if response.status_code == 200:
                return Response({
                    'tool_id': tool.id,
                    'job_name': job_name,
                    'build_number': build_number,
                    'logs': response.text
                })
            else:
                return Response(
                    {'error': f'Failed to get build logs: HTTP {response.status_code}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Failed to get Jenkins build logs for tool {tool.id}, job {job_name}, build {build_number}: {e}")
            return Response(
                {'error': f"Failed to get build logs: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='jenkins/build-info')
    def jenkins_build_info(self, request, pk=None):
        """获取Jenkins构建详细信息"""
        job_name = request.query_params.get('job_name')
        build_number = request.query_params.get('build_number')
        
        if not job_name or not build_number:
            return Response(
                {'error': 'job_name and build_number parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tool = self.get_object()
        try:
            auth = HTTPBasicAuth(tool.username, tool.token)
            
            # 获取构建详细信息
            url = f"{tool.base_url}/job/{job_name}/{build_number}/api/json"
            response = requests.get(url, auth=auth, timeout=10, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                return Response({
                    'tool_id': tool.id,
                    'job_name': job_name,
                    'build_number': build_number,
                    'build_info': {
                        'number': data.get('number'),
                        'url': data.get('url'),
                        'timestamp': data.get('timestamp', 0),
                        'result': data.get('result'),
                        'duration': data.get('duration', 0),
                        'description': data.get('description', ''),
                        'estimatedDuration': data.get('estimatedDuration', 0),
                        'builtOn': data.get('builtOn', ''),
                        'changeSet': data.get('changeSet', {}),
                        'actions': data.get('actions', [])
                    }
                })
            else:
                return Response(
                    {'error': f'Failed to get build info: HTTP {response.status_code}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Failed to get Jenkins build info for tool {tool.id}, job {job_name}, build {build_number}: {e}")
            return Response(
                {'error': f"Failed to get build info: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
