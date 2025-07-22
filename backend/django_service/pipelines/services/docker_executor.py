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
    """真实的 Docker 管理器 - 执行实际的Docker命令"""
    
    def __init__(self, enable_real_execution=True):
        """
        初始化Docker管理器
        Args:
            enable_real_execution: 是否启用真实Docker命令执行，False时为模拟模式
        """
        self.enable_real_execution = enable_real_execution
    
    def _run_docker_command(self, command, capture_output=True):
        """执行Docker命令"""
        if not self.enable_real_execution:
            # 模拟模式
            logger.info(f"[模拟] 执行Docker命令: {' '.join(command)}")
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="模拟执行成功".encode(),
                stderr=b""
            )
        
        try:
            logger.info(f"执行Docker命令: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=False,  # 使用bytes处理输出
                timeout=300  # 5分钟超时
            )
            return result
        except subprocess.TimeoutExpired:
            raise Exception(f"Docker命令执行超时: {' '.join(command)}")
        except FileNotFoundError:
            raise Exception("Docker命令未找到，请确保Docker已安装并在PATH中")
        except Exception as e:
            raise Exception(f"Docker命令执行失败: {e}")
    
    def build_image(self, dockerfile_path, build_context, image_name, build_args=None, no_cache=False):
        """执行 Docker 构建"""
        command = ['docker', 'build', '-t', image_name, '-f', dockerfile_path]
        
        if no_cache:
            command.append('--no-cache')
        
        if build_args:
            for key, value in build_args.items():
                command.extend(['--build-arg', f'{key}={value}'])
        
        command.append(build_context)
        
        result = self._run_docker_command(command)
        
        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8') if result.stderr else "构建失败"
            raise Exception(f"Docker构建失败: {error_msg}")
        
        return {
            'image_name': image_name,
            'build_log': result.stdout.decode('utf-8') if result.stdout else '',
            'build_time': 0,  # 可以通过计时获得
            'success': True
        }
    
    def run_container(self, image_name, command=None, environment=None, volumes=None, ports=None, working_dir=None, remove=True):
        """执行 Docker 运行"""
        docker_cmd = ['docker', 'run']
        
        if remove:
            docker_cmd.append('--rm')
        
        if working_dir:
            docker_cmd.extend(['-w', working_dir])
        
        if environment:
            for key, value in environment.items():
                docker_cmd.extend(['-e', f'{key}={value}'])
        
        if volumes:
            for volume in volumes:
                docker_cmd.extend(['-v', volume])
        
        if ports:
            for container_port, host_port in ports.items():
                docker_cmd.extend(['-p', f'{host_port}:{container_port}'])
        
        docker_cmd.append(image_name)
        
        if command:
            if isinstance(command, str):
                docker_cmd.extend(command.split())
            else:
                docker_cmd.extend(command)
        
        result = self._run_docker_command(docker_cmd)
        
        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8') if result.stderr else "容器运行失败"
            raise Exception(f"Docker运行失败: {error_msg}")
        
        return {
            'output': result.stdout.decode('utf-8') if result.stdout else '',
            'exit_code': result.returncode,
            'runtime': 0,  # 可以通过计时获得
            'success': True
        }
    
    def push_image(self, image_name):
        """执行 Docker 推送"""
        command = ['docker', 'push', image_name]
        
        result = self._run_docker_command(command)
        
        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8') if result.stderr else "推送失败"
            raise Exception(f"Docker推送失败: {error_msg}")
        
        return {
            'push_log': result.stdout.decode('utf-8') if result.stdout else '',
            'image_name': image_name,
            'success': True
        }
    
    def pull_image(self, image_name):
        """执行 Docker 拉取"""
        command = ['docker', 'pull', image_name]
        
        result = self._run_docker_command(command)
        
        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8') if result.stderr else "拉取失败"
            raise Exception(f"Docker拉取失败: {error_msg}")
        
        return {
            'pull_log': result.stdout.decode('utf-8') if result.stdout else '',
            'image_name': image_name,
            'success': True
        }
    
    def login_registry(self, registry_url, username, password):
        """登录Docker仓库"""
        command = ['docker', 'login', registry_url, '-u', username, '--password-stdin']
        
        try:
            result = subprocess.run(
                command,
                input=password.encode(),
                capture_output=True,
                timeout=60
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8') if result.stderr else "登录失败"
                raise Exception(f"Docker登录失败: {error_msg}")
            
            return True
        except Exception as e:
            logger.warning(f"Docker仓库登录失败: {e}")
            return False
    
    def tag_image(self, source_image, target_image):
        """标记Docker镜像"""
        command = ['docker', 'tag', source_image, target_image]
        
        result = self._run_docker_command(command)
        
        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8') if result.stderr else "标记失败"
            raise Exception(f"Docker标记失败: {error_msg}")
        
        return True


class DockerStepExecutor:
    """Docker 步骤执行器"""
    
    def __init__(self, enable_real_execution=True):
        """
        初始化Docker步骤执行器
        Args:
            enable_real_execution: 是否启用真实Docker命令执行
        """
        self.supported_step_types = [
            'docker_build',
            'docker_run', 
            'docker_push',
            'docker_pull'
        ]
        self.enable_real_execution = enable_real_execution
    
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
        # 从 ansible_parameters 中获取参数
        params = step.ansible_parameters or {}
        docker_config = params.get('docker_config', {})
        
        # 获取构建参数
        dockerfile_path = params.get('dockerfile') or docker_config.get('dockerfile', 'Dockerfile')
        build_context = params.get('context') or docker_config.get('context', '.')
        build_args = params.get('build_args') or docker_config.get('build_args', {})
        
        # 构建镜像名称和标签 - 支持多种参数名称
        image_name = (
            params.get('image') or 
            params.get('image_name') or 
            params.get('docker_image') or
            getattr(step, 'docker_image', None) or 
            docker_config.get('image_name', 'unnamed')
        )
        tag = params.get('tag') or params.get('docker_tag') or getattr(step, 'docker_tag', None) or docker_config.get('tag', 'latest')
        full_image_name = f"{image_name}:{tag}"
        
        # 处理变量替换
        build_args = self._process_variables(build_args, context)
        full_image_name = self._process_variables(full_image_name, context)
        
        try:
            # 创建 Docker 管理器 - 支持真实执行
            docker_manager = DockerManager(enable_real_execution=self.enable_real_execution)
            
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
        # 从 ansible_parameters 中获取参数
        params = step.ansible_parameters or {}
        docker_config = params.get('docker_config', {})
        
        # 获取运行参数 - 支持多种参数名称
        image_name = (
            params.get('image') or 
            params.get('image_name') or 
            params.get('docker_image') or
            getattr(step, 'docker_image', None) or 
            context.get('docker_image')
        )
        if not image_name:
            raise ValueError("No Docker image specified for run step")
        
        command = params.get('command') or docker_config.get('command') or step.command
        environment = {**step.environment_vars, **params.get('env_vars', {}), **docker_config.get('environment', {})}
        volumes = params.get('volumes') or docker_config.get('volumes', [])
        ports = params.get('ports') or docker_config.get('ports', {})
        working_dir = params.get('working_dir') or docker_config.get('working_dir')
        
        # 处理变量替换
        command = self._process_variables(command, context)
        environment = self._process_variables(environment, context)
        
        try:
            # 创建 Docker 管理器 - 支持真实执行  
            docker_manager = DockerManager(enable_real_execution=self.enable_real_execution)
            
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
        # 从 ansible_parameters 中获取参数
        params = step.ansible_parameters or {}
        docker_config = params.get('docker_config', {})
        
        # 获取镜像信息 - 支持多种参数名称
        image_name = (
            params.get('image') or 
            params.get('image_name') or 
            params.get('docker_image') or
            getattr(step, 'docker_image', None) or 
            context.get('docker_image')
        )
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
            # 创建 Docker 管理器 - 支持真实执行
            docker_manager = DockerManager(enable_real_execution=self.enable_real_execution)
            
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
        # 从 ansible_parameters 中获取参数
        params = step.ansible_parameters or {}
        docker_config = params.get('docker_config', {})
        
        # 获取镜像信息 - 支持多种参数名称
        image_name = (
            params.get('image') or 
            params.get('image_name') or 
            params.get('docker_image') or
            getattr(step, 'docker_image', None)
        )
        
        if not image_name:
            raise ValueError("No Docker image specified for pull step")
        
        tag = params.get('tag') or params.get('docker_tag') or getattr(step, 'docker_tag', None) or 'latest'
        full_image_name = f"{image_name}:{tag}"
        
        # 获取仓库信息
        registry = getattr(step, 'docker_registry', None)
        if registry:
            username = registry.username
            password = registry.get_decrypted_password()
            registry_url = registry.url
        else:
            username = docker_config.get('username')
            password = docker_config.get('password')
            registry_url = docker_config.get('registry_url')
        
        try:
            # 创建 Docker 管理器 - 支持真实执行
            docker_manager = DockerManager(enable_real_execution=self.enable_real_execution)
            
            # 登录仓库（如果需要）
            if username and password and registry_url:
                login_success = docker_manager.login_registry(registry_url, username, password)
                if not login_success:
                    logger.warning(f"Docker仓库登录失败，继续尝试拉取: {registry_url}")
            
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
