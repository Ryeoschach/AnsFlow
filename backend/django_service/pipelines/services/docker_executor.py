"""
Docker 步骤执行器
支持 Docker 相关步骤的执行
"""

import logging
import json
import tempfile
import os
import subprocess
from typing import Dict, Any, Optional
from django.utils import timezone
from docker_integration.models import DockerRegistry

logger = logging.getLogger(__name__)


class DockerManager:
    """简化版 Docker 管理器（用于演示）"""
    
    def build_image(self, dockerfile_path, build_context, image_name, build_args=None, no_cache=False):
        """模拟 Docker 构建"""
        return {
            'image_id': 'sha256:abc123',
            'build_log': f'Successfully built {image_name}',
            'build_time': 120
        }
    
    def run_container(self, image_name, command=None, environment=None, volumes=None, ports=None, working_dir=None, remove=True):
        """模拟 Docker 运行"""
        return {
            'container_id': 'container_123',
            'output': f'Container {image_name} executed successfully',
            'exit_code': 0,
            'runtime': 30
        }
    
    def push_image(self, image_name):
        """模拟 Docker 推送"""
        return {
            'push_log': f'Successfully pushed {image_name}',
            'digest': 'sha256:def456',
            'size': '50MB'
        }
    
    def pull_image(self, image_name):
        """模拟 Docker 拉取"""
        return {
            'pull_log': f'Successfully pulled {image_name}',
            'image_id': 'sha256:ghi789',
            'size': '45MB'
        }
    
    def login_registry(self, registry_url, username, password):
        """模拟仓库登录"""
        return True
    
    def tag_image(self, source_image, target_image):
        """模拟镜像标记"""
        return True


class DockerStepExecutor:
    """Docker 步骤执行器"""
    
    def __init__(self):
        self.supported_step_types = [
            'docker_build',
            'docker_run', 
            'docker_push',
            'docker_pull'
        ]
    
    def can_execute(self, step_type: str) -> bool:
        """检查是否可以执行指定类型的步骤"""
        return step_type in self.supported_step_types
    
    def execute_step(self, step, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行 Docker 步骤
        
        Args:
            step: PipelineStep 对象
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        context = context or {}
        
        try:
            # 根据步骤类型选择执行方法
            executor_map = {
                'docker_build': self._execute_docker_build,
                'docker_run': self._execute_docker_run,
                'docker_push': self._execute_docker_push,
                'docker_pull': self._execute_docker_pull,
            }
            
            executor = executor_map.get(step.step_type)
            if not executor:
                raise ValueError(f"Unsupported Docker step type: {step.step_type}")
            
            logger.info(f"Executing Docker step: {step.name} ({step.step_type})")
            
            # 执行步骤
            result = executor(step, context)
            
            # 记录成功日志
            logger.info(f"Docker step {step.name} completed successfully")
            
            return {
                'success': True,
                'step_type': step.step_type,
                'step_id': step.id,
                'message': result.get('message', 'Step completed successfully'),
                'output': result.get('output', ''),
                'data': result.get('data', {})
            }
            
        except Exception as e:
            logger.error(f"Docker step {step.name} failed: {e}")
            return {
                'success': False,
                'step_type': step.step_type,
                'step_id': step.id,
                'error': str(e),
                'output': getattr(e, 'output', ''),
                'data': {}
            }
    
    def _execute_docker_build(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Docker 构建步骤"""
        docker_config = step.docker_config or {}
        
        # 获取构建参数
        dockerfile_path = docker_config.get('dockerfile', 'Dockerfile')
        build_context = docker_config.get('context', '.')
        build_args = docker_config.get('build_args', {})
        
        # 构建镜像名称和标签
        image_name = step.docker_image or docker_config.get('image_name', 'unnamed')
        tag = step.docker_tag or docker_config.get('tag', 'latest')
        full_image_name = f"{image_name}:{tag}"
        
        # 处理变量替换
        build_args = self._process_variables(build_args, context)
        full_image_name = self._process_variables(full_image_name, context)
        
        try:
            # 创建 Docker 管理器
            docker_manager = DockerManager()
            
            # 执行构建
            result = docker_manager.build_image(
                dockerfile_path=dockerfile_path,
                build_context=build_context,
                image_name=full_image_name,
                build_args=build_args,
                no_cache=docker_config.get('no_cache', False)
            )
            
            # 更新上下文
            context['docker_image'] = full_image_name
            context['docker_image_id'] = result.get('image_id')
            
            return {
                'message': f'Image {full_image_name} built successfully',
                'output': result.get('build_log', ''),
                'data': {
                    'image_name': full_image_name,
                    'image_id': result.get('image_id'),
                    'build_time': result.get('build_time')
                }
            }
            
        except Exception as e:
            raise Exception(f"Docker build failed: {str(e)}")
    
    def _execute_docker_run(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Docker 运行步骤"""
        docker_config = step.docker_config or {}
        
        # 获取运行参数
        image_name = step.docker_image or context.get('docker_image')
        if not image_name:
            raise ValueError("No Docker image specified for run step")
        
        command = docker_config.get('command') or step.command
        environment = {**step.environment_vars, **docker_config.get('environment', {})}
        volumes = docker_config.get('volumes', [])
        ports = docker_config.get('ports', {})
        working_dir = docker_config.get('working_dir')
        
        # 处理变量替换
        command = self._process_variables(command, context)
        environment = self._process_variables(environment, context)
        
        try:
            # 创建 Docker 管理器
            docker_manager = DockerManager()
            
            # 运行容器
            result = docker_manager.run_container(
                image_name=image_name,
                command=command,
                environment=environment,
                volumes=volumes,
                ports=ports,
                working_dir=working_dir,
                remove=docker_config.get('remove', True)
            )
            
            return {
                'message': f'Container ran successfully',
                'output': result.get('output', ''),
                'data': {
                    'container_id': result.get('container_id'),
                    'exit_code': result.get('exit_code'),
                    'runtime': result.get('runtime')
                }
            }
            
        except Exception as e:
            raise Exception(f"Docker run failed: {str(e)}")
    
    def _execute_docker_push(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Docker 推送步骤"""
        docker_config = step.docker_config or {}
        
        # 获取镜像信息
        image_name = step.docker_image or context.get('docker_image')
        if not image_name:
            raise ValueError("No Docker image specified for push step")
        
        # 获取仓库信息
        registry = step.docker_registry
        if registry:
            # 使用配置的仓库
            registry_url = registry.url
            username = registry.username
            password = registry.get_decrypted_password()
        else:
            # 使用步骤配置中的仓库信息
            registry_url = docker_config.get('registry_url')
            username = docker_config.get('username')
            password = docker_config.get('password')
        
        # 构建完整的镜像名称
        if registry_url and not image_name.startswith(registry_url):
            full_image_name = f"{registry_url}/{image_name}"
        else:
            full_image_name = image_name
        
        try:
            # 创建 Docker 管理器
            docker_manager = DockerManager()
            
            # 登录仓库（如果需要）
            if username and password:
                docker_manager.login_registry(registry_url, username, password)
            
            # 标记镜像
            if full_image_name != image_name:
                docker_manager.tag_image(image_name, full_image_name)
            
            # 推送镜像
            result = docker_manager.push_image(full_image_name)
            
            return {
                'message': f'Image {full_image_name} pushed successfully',
                'output': result.get('push_log', ''),
                'data': {
                    'image_name': full_image_name,
                    'digest': result.get('digest'),
                    'size': result.get('size')
                }
            }
            
        except Exception as e:
            raise Exception(f"Docker push failed: {str(e)}")
    
    def _execute_docker_pull(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Docker 拉取步骤"""
        docker_config = step.docker_config or {}
        
        # 获取镜像信息
        image_name = step.docker_image
        if not image_name:
            raise ValueError("No Docker image specified for pull step")
        
        tag = step.docker_tag or 'latest'
        full_image_name = f"{image_name}:{tag}"
        
        # 获取仓库信息
        registry = step.docker_registry
        if registry:
            username = registry.username
            password = registry.get_decrypted_password()
            registry_url = registry.url
        else:
            username = docker_config.get('username')
            password = docker_config.get('password')
            registry_url = docker_config.get('registry_url')
        
        try:
            # 创建 Docker 管理器
            docker_manager = DockerManager()
            
            # 登录仓库（如果需要）
            if username and password and registry_url:
                docker_manager.login_registry(registry_url, username, password)
            
            # 拉取镜像
            result = docker_manager.pull_image(full_image_name)
            
            # 更新上下文
            context['docker_image'] = full_image_name
            
            return {
                'message': f'Image {full_image_name} pulled successfully',
                'output': result.get('pull_log', ''),
                'data': {
                    'image_name': full_image_name,
                    'image_id': result.get('image_id'),
                    'size': result.get('size')
                }
            }
            
        except Exception as e:
            raise Exception(f"Docker pull failed: {str(e)}")
    
    def _process_variables(self, value, context: Dict[str, Any]):
        """处理变量替换"""
        if isinstance(value, str):
            # 简单的变量替换，支持 {{variable}} 格式
            import re
            def replace_var(match):
                var_name = match.group(1).strip()
                return str(context.get(var_name, match.group(0)))
            
            return re.sub(r'\{\{([^}]+)\}\}', replace_var, value)
        elif isinstance(value, dict):
            return {k: self._process_variables(v, context) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._process_variables(item, context) for item in value]
        else:
            return value
