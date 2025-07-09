"""
Kubernetes 客户端封装
"""
import json
import base64
import tempfile
import os
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class KubernetesManager:
    """Kubernetes 管理器"""
    
    def __init__(self, cluster):
        """初始化 K8s 管理器"""
        self.cluster = cluster
        self.api_client = None
        self.apps_v1_api = None
        self.core_v1_api = None
        
        # 延迟导入以避免启动时的依赖问题
        try:
            from kubernetes import client, config
            from kubernetes.client.rest import ApiException
            self._client = client
            self._config = config
            self._ApiException = ApiException
            
            # 初始化客户端
            self._init_client()
            
        except ImportError:
            logger.warning("kubernetes 库未安装，使用模拟模式")
            self._client = None
            self._config = None
            self._ApiException = Exception
    
    def _init_client(self):
        """初始化 Kubernetes 客户端"""
        try:
            if not self._client:
                # 模拟模式
                return
            
            # 从集群配置创建客户端配置
            auth_config = self.cluster.auth_config or {}
            
            # 创建临时的 kubeconfig 文件
            if auth_config.get('token'):
                self._init_from_token(auth_config)
            elif auth_config.get('kubeconfig'):
                self._init_from_kubeconfig(auth_config)
            else:
                # 使用默认配置
                self._config.load_incluster_config()
            
            # 创建 API 实例
            self.api_client = self._client.ApiClient()
            self.core_v1_api = self._client.CoreV1Api()
            self.apps_v1_api = self._client.AppsV1Api()
            
        except Exception as e:
            logger.error(f"初始化 K8s 客户端失败: {str(e)}")
            # 设置为模拟模式
            self._client = None
    
    def _init_from_token(self, auth_config):
        """使用 Token 初始化客户端"""
        configuration = self._client.Configuration()
        configuration.host = self.cluster.api_server
        configuration.api_key = {"authorization": f"Bearer {auth_config['token']}"}
        
        # 设置 CA 证书
        if auth_config.get('ca_cert'):
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.crt') as f:
                f.write(auth_config['ca_cert'])
                configuration.ssl_ca_cert = f.name
        else:
            configuration.verify_ssl = False
        
        self._client.Configuration.set_default(configuration)
    
    def _init_from_kubeconfig(self, auth_config):
        """使用 kubeconfig 初始化客户端"""
        kubeconfig_content = auth_config['kubeconfig']
        
        # 创建临时的 kubeconfig 文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            f.write(kubeconfig_content)
            kubeconfig_path = f.name
        
        try:
            self._config.load_kube_config(config_file=kubeconfig_path)
        finally:
            # 清理临时文件
            if os.path.exists(kubeconfig_path):
                os.unlink(kubeconfig_path)
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """获取集群信息"""
        if not self._client:
            # 模拟模式
            return {
                'connected': True,
                'version': 'v1.28.0',
                'total_nodes': 3,
                'ready_nodes': 3,
                'total_pods': 10,
                'running_pods': 8,
                'message': '模拟集群连接成功'
            }
        
        try:
            # 获取版本信息
            version_info = self.core_v1_api.get_code_version()
            
            # 获取节点信息
            nodes = self.core_v1_api.list_node()
            total_nodes = len(nodes.items)
            ready_nodes = sum(1 for node in nodes.items 
                            if any(condition.type == "Ready" and condition.status == "True" 
                                  for condition in node.status.conditions))
            
            # 获取 Pod 信息
            pods = self.core_v1_api.list_pod_for_all_namespaces()
            total_pods = len(pods.items)
            running_pods = sum(1 for pod in pods.items 
                             if pod.status.phase == "Running")
            
            return {
                'connected': True,
                'version': version_info.git_version,
                'total_nodes': total_nodes,
                'ready_nodes': ready_nodes,
                'total_pods': total_pods,
                'running_pods': running_pods,
                'message': '集群连接成功'
            }
            
        except Exception as e:
            return {
                'connected': False,
                'message': f'连接失败: {str(e)}',
                'version': '',
                'total_nodes': 0,
                'ready_nodes': 0,
                'total_pods': 0,
                'running_pods': 0,
            }
    
    def list_namespaces(self) -> List[Dict[str, Any]]:
        """获取命名空间列表"""
        if not self._client:
            # 模拟模式
            return [
                {
                    'name': 'default',
                    'status': 'active',
                    'labels': {},
                    'annotations': {}
                },
                {
                    'name': 'kube-system',
                    'status': 'active',
                    'labels': {},
                    'annotations': {}
                }
            ]
        
        try:
            namespaces = self.core_v1_api.list_namespace()
            result = []
            
            for ns in namespaces.items:
                result.append({
                    'name': ns.metadata.name,
                    'status': ns.status.phase.lower() if ns.status.phase else 'active',
                    'labels': ns.metadata.labels or {},
                    'annotations': ns.metadata.annotations or {}
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取命名空间列表失败: {str(e)}")
            return []
    
    def list_deployments(self, namespace: str = None) -> List[Dict[str, Any]]:
        """获取部署列表"""
        if not self._client:
            # 模拟模式
            return [
                {
                    'name': 'nginx-deployment',
                    'namespace': 'default',
                    'image': 'nginx:1.20',
                    'replicas': 3,
                    'ready_replicas': 3,
                    'status': 'available',
                    'labels': {'app': 'nginx'}
                }
            ]
        
        try:
            result = []
            
            if namespace:
                deployments = self.apps_v1_api.list_namespaced_deployment(namespace)
            else:
                deployments = self.apps_v1_api.list_deployment_for_all_namespaces()
            
            for deploy in deployments.items:
                # 获取第一个容器的镜像
                image = ''
                if deploy.spec.template.spec.containers:
                    image = deploy.spec.template.spec.containers[0].image
                
                # 确定状态
                status = 'unknown'
                if deploy.status.conditions:
                    for condition in deploy.status.conditions:
                        if condition.type == 'Available' and condition.status == 'True':
                            status = 'available'
                        elif condition.type == 'Progressing' and condition.status == 'True':
                            status = 'progressing'
                
                result.append({
                    'name': deploy.metadata.name,
                    'namespace': deploy.metadata.namespace,
                    'image': image,
                    'replicas': deploy.spec.replicas or 1,
                    'ready_replicas': deploy.status.ready_replicas or 0,
                    'status': status,
                    'labels': deploy.metadata.labels or {}
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取部署列表失败: {str(e)}")
            return []
    
    def list_pods(self, namespace: str = None) -> List[Dict[str, Any]]:
        """获取 Pod 列表"""
        if not self._client:
            # 模拟模式
            return [
                {
                    'name': 'nginx-deployment-abc123',
                    'namespace': 'default',
                    'phase': 'Running',
                    'node_name': 'node-1',
                    'pod_ip': '10.244.1.5',
                    'containers': [{'name': 'nginx', 'image': 'nginx:1.20'}],
                    'labels': {'app': 'nginx'},
                    'ready': True
                }
            ]
        
        try:
            result = []
            
            if namespace:
                pods = self.core_v1_api.list_namespaced_pod(namespace)
            else:
                pods = self.core_v1_api.list_pod_for_all_namespaces()
            
            for pod in pods.items:
                # 获取容器信息
                containers = []
                for container in pod.spec.containers:
                    containers.append({
                        'name': container.name,
                        'image': container.image
                    })
                
                # 检查就绪状态
                ready = False
                if pod.status.conditions:
                    for condition in pod.status.conditions:
                        if condition.type == 'Ready' and condition.status == 'True':
                            ready = True
                            break
                
                result.append({
                    'name': pod.metadata.name,
                    'namespace': pod.metadata.namespace,
                    'phase': pod.status.phase,
                    'node_name': pod.spec.node_name or '',
                    'pod_ip': pod.status.pod_ip or '',
                    'containers': containers,
                    'labels': pod.metadata.labels or {},
                    'ready': ready
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取 Pod 列表失败: {str(e)}")
            return []
    
    def create_deployment(self, deploy_spec: Dict[str, Any]) -> Dict[str, Any]:
        """创建部署"""
        if not self._client:
            # 模拟模式
            return {
                'status': 'success',
                'message': f"部署 {deploy_spec['name']} 创建成功（模拟）"
            }
        
        try:
            # 构建部署对象
            deployment = self._build_deployment_object(deploy_spec)
            
            # 创建部署
            result = self.apps_v1_api.create_namespaced_deployment(
                namespace=deploy_spec['namespace'],
                body=deployment
            )
            
            return {
                'status': 'success',
                'message': f"部署 {deploy_spec['name']} 创建成功",
                'deployment_name': result.metadata.name
            }
            
        except Exception as e:
            logger.error(f"创建部署失败: {str(e)}")
            return {
                'status': 'error',
                'message': f"创建部署失败: {str(e)}"
            }
    
    def scale_deployment(self, name: str, namespace: str, replicas: int) -> Dict[str, Any]:
        """扩缩容部署"""
        if not self._client:
            # 模拟模式
            return {
                'status': 'success',
                'message': f"部署 {name} 扩缩容到 {replicas} 个副本成功（模拟）"
            }
        
        try:
            # 获取当前部署
            deployment = self.apps_v1_api.read_namespaced_deployment(name, namespace)
            
            # 更新副本数
            deployment.spec.replicas = replicas
            
            # 更新部署
            result = self.apps_v1_api.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment
            )
            
            return {
                'status': 'success',
                'message': f"部署 {name} 扩缩容到 {replicas} 个副本成功",
                'replicas': result.spec.replicas
            }
            
        except Exception as e:
            logger.error(f"扩缩容部署失败: {str(e)}")
            return {
                'status': 'error',
                'message': f"扩缩容部署失败: {str(e)}"
            }
    
    def delete_deployment(self, name: str, namespace: str) -> Dict[str, Any]:
        """删除部署"""
        if not self._client:
            # 模拟模式
            return {
                'status': 'success',
                'message': f"部署 {name} 删除成功（模拟）"
            }
        
        try:
            self.apps_v1_api.delete_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            
            return {
                'status': 'success',
                'message': f"部署 {name} 删除成功"
            }
            
        except Exception as e:
            logger.error(f"删除部署失败: {str(e)}")
            return {
                'status': 'error',
                'message': f"删除部署失败: {str(e)}"
            }
    
    def delete_pod(self, name: str, namespace: str) -> Dict[str, Any]:
        """删除 Pod"""
        if not self._client:
            # 模拟模式
            return {
                'status': 'success',
                'message': f"Pod {name} 删除成功（模拟）"
            }
        
        try:
            self.core_v1_api.delete_namespaced_pod(
                name=name,
                namespace=namespace
            )
            
            return {
                'status': 'success',
                'message': f"Pod {name} 删除成功"
            }
            
        except Exception as e:
            logger.error(f"删除 Pod 失败: {str(e)}")
            return {
                'status': 'error',
                'message': f"删除 Pod 失败: {str(e)}"
            }
    
    def delete_service(self, name: str, namespace: str) -> Dict[str, Any]:
        """删除服务"""
        if not self._client:
            # 模拟模式
            return {
                'status': 'success',
                'message': f"服务 {name} 删除成功（模拟）"
            }
        
        try:
            self.core_v1_api.delete_namespaced_service(
                name=name,
                namespace=namespace
            )
            
            return {
                'status': 'success',
                'message': f"服务 {name} 删除成功"
            }
            
        except Exception as e:
            logger.error(f"删除服务失败: {str(e)}")
            return {
                'status': 'error',
                'message': f"删除服务失败: {str(e)}"
            }
    
    def _build_deployment_object(self, deploy_spec: Dict[str, Any]):
        """构建部署对象"""
        if not self._client:
            return {}
        
        # 构建容器定义
        container = self._client.V1Container(
            name=deploy_spec['name'],
            image=deploy_spec['image'],
            ports=[self._client.V1ContainerPort(container_port=port.get('container_port', 80)) 
                   for port in deploy_spec.get('ports', [])],
            env=[self._client.V1EnvVar(name=k, value=str(v)) 
                 for k, v in deploy_spec.get('environment_vars', {}).items()],
            resources=self._client.V1ResourceRequirements(
                requests=deploy_spec.get('resources', {}).get('requests', {}),
                limits=deploy_spec.get('resources', {}).get('limits', {})
            )
        )
        
        # 构建 Pod 模板
        template = self._client.V1PodTemplateSpec(
            metadata=self._client.V1ObjectMeta(
                labels=deploy_spec.get('labels', {})
            ),
            spec=self._client.V1PodSpec(containers=[container])
        )
        
        # 构建部署规格
        spec = self._client.V1DeploymentSpec(
            replicas=deploy_spec.get('replicas', 1),
            selector=self._client.V1LabelSelector(
                match_labels=deploy_spec.get('labels', {})
            ),
            template=template
        )
        
        # 构建部署对象
        deployment = self._client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=self._client.V1ObjectMeta(
                name=deploy_spec['name'],
                labels=deploy_spec.get('labels', {})
            ),
            spec=spec
        )
        
        return deployment
