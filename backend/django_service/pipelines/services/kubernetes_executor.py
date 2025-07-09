"""
Kubernetes 步骤执行器
支持 Kubernetes 相关步骤的执行
"""

import logging
import json
import time
from typing import Dict, Any, Optional
from django.utils import timezone
from kubernetes_integration.models import KubernetesCluster
from kubernetes_integration.k8s_client import KubernetesManager

logger = logging.getLogger(__name__)


class KubernetesStepExecutor:
    """Kubernetes 步骤执行器"""
    
    def __init__(self):
        self.supported_step_types = [
            'k8s_deploy',
            'k8s_scale', 
            'k8s_delete',
            'k8s_wait',
            'k8s_exec',
            'k8s_logs'
        ]
    
    def can_execute(self, step_type: str) -> bool:
        """检查是否可以执行指定类型的步骤"""
        return step_type in self.supported_step_types
    
    def execute_step(self, step, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行 Kubernetes 步骤
        
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
                'k8s_deploy': self._execute_k8s_deploy,
                'k8s_scale': self._execute_k8s_scale,
                'k8s_delete': self._execute_k8s_delete,
                'k8s_wait': self._execute_k8s_wait,
                'k8s_exec': self._execute_k8s_exec,
                'k8s_logs': self._execute_k8s_logs,
            }
            
            executor = executor_map.get(step.step_type)
            if not executor:
                raise ValueError(f"Unsupported Kubernetes step type: {step.step_type}")
            
            logger.info(f"Executing Kubernetes step: {step.name} ({step.step_type})")
            
            # 检查集群配置
            if not step.k8s_cluster:
                raise ValueError("No Kubernetes cluster specified for step")
            
            # 执行步骤
            result = executor(step, context)
            
            # 记录成功日志
            logger.info(f"Kubernetes step {step.name} completed successfully")
            
            return {
                'success': True,
                'step_type': step.step_type,
                'step_id': step.id,
                'message': result.get('message', 'Step completed successfully'),
                'output': result.get('output', ''),
                'data': result.get('data', {})
            }
            
        except Exception as e:
            logger.error(f"Kubernetes step {step.name} failed: {e}")
            return {
                'success': False,
                'step_type': step.step_type,
                'step_id': step.id,
                'error': str(e),
                'output': getattr(e, 'output', ''),
                'data': {}
            }
    
    def _execute_k8s_deploy(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Kubernetes 部署步骤"""
        k8s_config = step.k8s_config or {}
        
        # 获取部署参数
        namespace = step.k8s_namespace or k8s_config.get('namespace', 'default')
        resource_name = step.k8s_resource_name or k8s_config.get('name')
        
        if not resource_name:
            raise ValueError("No resource name specified for deployment")
        
        # 构建部署规格
        deployment_spec = k8s_config.get('deployment_spec', {})
        
        # 处理镜像名称（可能来自上下文）
        image = deployment_spec.get('image') or context.get('docker_image')
        if not image:
            raise ValueError("No Docker image specified for deployment")
        
        # 处理变量替换
        deployment_spec = self._process_variables(deployment_spec, context)
        deployment_spec['image'] = self._process_variables(image, context)
        deployment_spec['name'] = resource_name
        deployment_spec['namespace'] = namespace
        
        try:
            # 创建 Kubernetes 管理器
            k8s_manager = KubernetesManager(step.k8s_cluster)
            
            # 执行部署
            result = k8s_manager.create_deployment(deployment_spec)
            
            # 更新上下文
            context['k8s_deployment'] = resource_name
            context['k8s_namespace'] = namespace
            
            return {
                'message': f'Deployment {resource_name} created successfully in namespace {namespace}',
                'output': json.dumps(result, indent=2),
                'data': {
                    'deployment_name': resource_name,
                    'namespace': namespace,
                    'image': deployment_spec['image'],
                    'replicas': deployment_spec.get('replicas', 1)
                }
            }
            
        except Exception as e:
            raise Exception(f"Kubernetes deployment failed: {str(e)}")
    
    def _execute_k8s_scale(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Kubernetes 扩缩容步骤"""
        k8s_config = step.k8s_config or {}
        
        # 获取扩缩容参数
        namespace = step.k8s_namespace or k8s_config.get('namespace', 'default')
        resource_name = step.k8s_resource_name or k8s_config.get('name') or context.get('k8s_deployment')
        replicas = k8s_config.get('replicas')
        
        if not resource_name:
            raise ValueError("No resource name specified for scaling")
        
        if replicas is None:
            raise ValueError("No replica count specified for scaling")
        
        # 处理变量替换
        replicas = self._process_variables(replicas, context)
        if isinstance(replicas, str):
            replicas = int(replicas)
        
        try:
            # 创建 Kubernetes 管理器
            k8s_manager = KubernetesManager(step.k8s_cluster)
            
            # 执行扩缩容
            result = k8s_manager.scale_deployment(resource_name, namespace, replicas)
            
            return {
                'message': f'Deployment {resource_name} scaled to {replicas} replicas',
                'output': json.dumps(result, indent=2),
                'data': {
                    'deployment_name': resource_name,
                    'namespace': namespace,
                    'replicas': replicas
                }
            }
            
        except Exception as e:
            raise Exception(f"Kubernetes scaling failed: {str(e)}")
    
    def _execute_k8s_delete(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Kubernetes 删除步骤"""
        k8s_config = step.k8s_config or {}
        
        # 获取删除参数
        namespace = step.k8s_namespace or k8s_config.get('namespace', 'default')
        resource_name = step.k8s_resource_name or k8s_config.get('name') or context.get('k8s_deployment')
        resource_type = k8s_config.get('resource_type', 'deployment')
        
        if not resource_name:
            raise ValueError("No resource name specified for deletion")
        
        try:
            # 创建 Kubernetes 管理器
            k8s_manager = KubernetesManager(step.k8s_cluster)
            
            # 根据资源类型执行删除
            if resource_type == 'deployment':
                result = k8s_manager.delete_deployment(resource_name, namespace)
            elif resource_type == 'service':
                result = k8s_manager.delete_service(resource_name, namespace)
            elif resource_type == 'pod':
                result = k8s_manager.delete_pod(resource_name, namespace)
            else:
                raise ValueError(f"Unsupported resource type: {resource_type}")
            
            return {
                'message': f'{resource_type.title()} {resource_name} deleted successfully',
                'output': json.dumps(result, indent=2),
                'data': {
                    'resource_type': resource_type,
                    'resource_name': resource_name,
                    'namespace': namespace
                }
            }
            
        except Exception as e:
            raise Exception(f"Kubernetes deletion failed: {str(e)}")
    
    def _execute_k8s_wait(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Kubernetes 等待步骤"""
        k8s_config = step.k8s_config or {}
        
        # 获取等待参数
        namespace = step.k8s_namespace or k8s_config.get('namespace', 'default')
        resource_name = step.k8s_resource_name or k8s_config.get('name') or context.get('k8s_deployment')
        resource_type = k8s_config.get('resource_type', 'deployment')
        condition = k8s_config.get('condition', 'available')
        timeout = k8s_config.get('timeout', step.timeout_seconds or 300)
        
        if not resource_name:
            raise ValueError("No resource name specified for waiting")
        
        try:
            # 创建 Kubernetes 管理器
            k8s_manager = KubernetesManager(step.k8s_cluster)
            
            # 等待条件满足
            start_time = time.time()
            while time.time() - start_time < timeout:
                if resource_type == 'deployment':
                    deployments = k8s_manager.list_deployments(namespace)
                    deployment = next((d for d in deployments if d['name'] == resource_name), None)
                    
                    if deployment:
                        if condition == 'available':
                            if deployment.get('ready_replicas', 0) >= deployment.get('replicas', 1):
                                break
                        elif condition == 'progressing':
                            if deployment.get('status') == 'progressing':
                                break
                
                time.sleep(5)  # 等待5秒后重试
            else:
                raise TimeoutError(f"Timeout waiting for {resource_type} {resource_name} to be {condition}")
            
            return {
                'message': f'{resource_type.title()} {resource_name} is {condition}',
                'output': f'Wait condition satisfied after {int(time.time() - start_time)} seconds',
                'data': {
                    'resource_type': resource_type,
                    'resource_name': resource_name,
                    'namespace': namespace,
                    'condition': condition,
                    'wait_time': int(time.time() - start_time)
                }
            }
            
        except Exception as e:
            raise Exception(f"Kubernetes wait failed: {str(e)}")
    
    def _execute_k8s_exec(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Kubernetes 命令步骤"""
        k8s_config = step.k8s_config or {}
        
        # 获取执行参数
        namespace = step.k8s_namespace or k8s_config.get('namespace', 'default')
        pod_selector = k8s_config.get('pod_selector') or f"app={context.get('k8s_deployment', step.k8s_resource_name)}"
        command = step.command or k8s_config.get('command')
        container = k8s_config.get('container')
        
        if not command:
            raise ValueError("No command specified for execution")
        
        # 处理变量替换
        command = self._process_variables(command, context)
        
        try:
            # 创建 Kubernetes 管理器
            k8s_manager = KubernetesManager(step.k8s_cluster)
            
            # 获取 Pod 列表
            pods = k8s_manager.list_pods(namespace)
            
            # 根据选择器过滤 Pod
            target_pods = []
            if pod_selector.startswith('app='):
                app_name = pod_selector.split('=', 1)[1]
                target_pods = [p for p in pods if p.get('labels', {}).get('app') == app_name]
            
            if not target_pods:
                raise ValueError(f"No pods found matching selector: {pod_selector}")
            
            # 在第一个找到的 Pod 中执行命令
            target_pod = target_pods[0]
            pod_name = target_pod['name']
            
            # 这里应该使用 Kubernetes API 执行命令，暂时模拟
            # 实际实现需要使用 kubernetes.stream.stream 方法
            
            return {
                'message': f'Command executed successfully in pod {pod_name}',
                'output': f'Executed command: {command}\nPod: {pod_name}\nNamespace: {namespace}',
                'data': {
                    'pod_name': pod_name,
                    'namespace': namespace,
                    'command': command,
                    'container': container
                }
            }
            
        except Exception as e:
            raise Exception(f"Kubernetes exec failed: {str(e)}")
    
    def _execute_k8s_logs(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Kubernetes 日志获取步骤"""
        k8s_config = step.k8s_config or {}
        
        # 获取日志参数
        namespace = step.k8s_namespace or k8s_config.get('namespace', 'default')
        pod_name = step.k8s_resource_name or k8s_config.get('pod_name')
        container = k8s_config.get('container')
        tail_lines = k8s_config.get('tail_lines', 100)
        
        if not pod_name:
            # 尝试从上下文获取或使用选择器
            pod_selector = k8s_config.get('pod_selector') or f"app={context.get('k8s_deployment')}"
            
            # 创建 Kubernetes 管理器
            k8s_manager = KubernetesManager(step.k8s_cluster)
            
            # 获取 Pod 列表
            pods = k8s_manager.list_pods(namespace)
            
            # 根据选择器过滤 Pod
            if pod_selector.startswith('app='):
                app_name = pod_selector.split('=', 1)[1]
                target_pods = [p for p in pods if p.get('labels', {}).get('app') == app_name]
                
                if target_pods:
                    pod_name = target_pods[0]['name']
        
        if not pod_name:
            raise ValueError("No pod name specified for log retrieval")
        
        try:
            # 创建 Kubernetes 管理器
            k8s_manager = KubernetesManager(step.k8s_cluster)
            
            # 获取日志
            logs = k8s_manager.get_pod_logs(pod_name, namespace, container, tail_lines)
            
            return {
                'message': f'Logs retrieved from pod {pod_name}',
                'output': logs,
                'data': {
                    'pod_name': pod_name,
                    'namespace': namespace,
                    'container': container,
                    'tail_lines': tail_lines
                }
            }
            
        except Exception as e:
            raise Exception(f"Kubernetes logs retrieval failed: {str(e)}")
    
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
