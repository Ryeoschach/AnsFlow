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
            
            # 根据认证方式初始化客户端
            if auth_config.get('token'):
                logger.info("使用 Token 认证方式")
                self._init_from_token(auth_config)
            elif auth_config.get('kubeconfig'):
                logger.info("使用 Kubeconfig 认证方式")
                self._init_from_kubeconfig(auth_config)
            elif auth_config.get('client_cert') and auth_config.get('client_key'):
                logger.info("使用客户端证书认证方式")
                self._init_from_cert(auth_config)
            else:
                logger.info("尝试使用集群内认证")
                # 使用默认配置（集群内认证）
                self._config.load_incluster_config()
            
            # 创建 API 实例
            self.api_client = self._client.ApiClient()
            self.core_v1_api = self._client.CoreV1Api()
            self.apps_v1_api = self._client.AppsV1Api()
            
            logger.info("Kubernetes 客户端初始化成功")
            
        except Exception as e:
            logger.error(f"初始化 K8s 客户端失败: {str(e)}")
            # 设置为模拟模式
            self._client = None
    
    def _init_from_token(self, auth_config):
        """使用 Token 初始化客户端"""
        configuration = self._client.Configuration()
        configuration.host = self.cluster.api_server
        
        # 正确的Token认证方式
        configuration.api_key = {"authorization": auth_config['token']}
        configuration.api_key_prefix = {"authorization": "Bearer"}
        
        # 设置 CA 证书
        if auth_config.get('ca_cert'):
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.crt') as f:
                f.write(auth_config['ca_cert'])
                configuration.ssl_ca_cert = f.name
        else:
            # 如果没有提供 CA 证书，根据配置决定是否验证 SSL
            configuration.verify_ssl = auth_config.get('verify_ssl', False)
        
        # 设置超时
        configuration.timeout_seconds = 30
        
        # 应用配置
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
    
    def _init_from_cert(self, auth_config):
        """使用客户端证书初始化客户端"""
        configuration = self._client.Configuration()
        configuration.host = self.cluster.api_server
        
        # 创建临时证书文件
        cert_file = None
        key_file = None
        ca_file = None
        
        try:
            # 客户端证书
            if auth_config.get('client_cert'):
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.crt') as f:
                    f.write(auth_config['client_cert'])
                    cert_file = f.name
                    configuration.cert_file = cert_file
            
            # 客户端私钥
            if auth_config.get('client_key'):
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.key') as f:
                    f.write(auth_config['client_key'])
                    key_file = f.name
                    configuration.key_file = key_file
            
            # CA 证书
            if auth_config.get('ca_cert'):
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.crt') as f:
                    f.write(auth_config['ca_cert'])
                    ca_file = f.name
                    configuration.ssl_ca_cert = ca_file
            else:
                configuration.verify_ssl = auth_config.get('verify_ssl', False)
            
            # 设置超时
            configuration.timeout_seconds = 30
            
            # 应用配置
            self._client.Configuration.set_default(configuration)
            
        except Exception as e:
            # 清理临时文件
            for temp_file in [cert_file, key_file, ca_file]:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
            raise e
    
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
            # 测试基本连接 - 使用 list_namespace 来检查连接
            namespaces = self.core_v1_api.list_namespace()
            
            # 获取版本信息 - 使用 VersionApi
            version_api = self._client.VersionApi(self.api_client)
            version_info = version_api.get_code()
            
            # 获取节点信息
            nodes = self.core_v1_api.list_node()
            total_nodes = len(nodes.items)
            ready_nodes = 0
            
            for node in nodes.items:
                if node.status.conditions:
                    for condition in node.status.conditions:
                        if condition.type == "Ready" and condition.status == "True":
                            ready_nodes += 1
                            break
            
            # 获取 Pod 信息
            pods = self.core_v1_api.list_pod_for_all_namespaces()
            total_pods = len(pods.items)
            running_pods = 0
            
            for pod in pods.items:
                if pod.status.phase == "Running":
                    running_pods += 1
            
            return {
                'connected': True,
                'version': version_info.git_version,
                'total_nodes': total_nodes,
                'ready_nodes': ready_nodes,
                'total_pods': total_pods,
                'running_pods': running_pods,
                'message': '集群连接成功'
            }
            
        except self._ApiException as e:
            logger.error(f"Kubernetes API 错误: {e}")
            return {
                'connected': False,
                'message': f'API 错误: {e.reason} (状态码: {e.status})',
                'version': '',
                'total_nodes': 0,
                'ready_nodes': 0,
                'total_pods': 0,
                'running_pods': 0,
            }
        except Exception as e:
            logger.error(f"集群连接失败: {e}")
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
    
    def list_services(self, namespace: str = None) -> List[Dict[str, Any]]:
        """获取服务列表"""
        if not self._client:
            # 模拟模式
            return [
                {
                    'name': 'nginx-service',
                    'namespace': 'default',
                    'type': 'ClusterIP',
                    'cluster_ip': '10.96.1.100',
                    'external_ip': '',
                    'ports': [{'port': 80, 'target_port': 80, 'protocol': 'TCP'}],
                    'selector': {'app': 'nginx'},
                    'labels': {}
                }
            ]
        
        try:
            result = []
            
            if namespace:
                services = self.core_v1_api.list_namespaced_service(namespace)
            else:
                services = self.core_v1_api.list_service_for_all_namespaces()
            
            for svc in services.items:
                # 获取端口信息
                ports = []
                if svc.spec.ports:
                    for port in svc.spec.ports:
                        ports.append({
                            'name': port.name or '',
                            'port': port.port,
                            'target_port': str(port.target_port) if port.target_port else '',
                            'protocol': port.protocol or 'TCP'
                        })
                
                # 获取外部IP
                external_ip = ''
                if svc.status.load_balancer and svc.status.load_balancer.ingress:
                    ingress = svc.status.load_balancer.ingress[0]
                    external_ip = ingress.ip or ingress.hostname or ''
                
                result.append({
                    'name': svc.metadata.name,
                    'namespace': svc.metadata.namespace,
                    'type': svc.spec.type or 'ClusterIP',
                    'cluster_ip': svc.spec.cluster_ip or '',
                    'external_ip': external_ip,
                    'ports': ports,
                    'selector': svc.spec.selector or {},
                    'labels': svc.metadata.labels or {}
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取服务列表失败: {str(e)}")
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

    def deploy_helm_chart(self, helm_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用 Helm 部署 Chart
        
        Args:
            helm_params: Helm 部署参数
            
        Returns:
            部署结果
        """
        import subprocess
        import tempfile
        import yaml
        
        try:
            # 构建 Helm 命令
            cmd = self._build_helm_command(helm_params)
            
            # 执行 Helm 命令
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=helm_params.get('timeout', 300)
            )
            
            if result.returncode != 0:
                raise Exception(f"Helm command failed: {result.stderr}")
            
            return {
                'status': 'success',
                'message': f"Helm chart {helm_params['chart_name']} deployed successfully",
                'output': result.stdout,
                'command': cmd
            }
            
        except subprocess.TimeoutExpired:
            raise Exception(f"Helm deployment timed out after {helm_params.get('timeout', 300)} seconds")
        except Exception as e:
            logger.error(f"Helm deployment failed: {e}")
            raise
    
    def _build_helm_command(self, helm_params: Dict[str, Any]) -> str:
        """构建 Helm 命令"""
        chart_name = helm_params['chart_name']
        release_name = helm_params['release_name']
        namespace = helm_params['namespace']
        
        # 基础命令
        if helm_params.get('upgrade', True):
            cmd = f"helm upgrade --install {release_name} {chart_name}"
        else:
            cmd = f"helm install {release_name} {chart_name}"
        
        # 添加命名空间
        cmd += f" --namespace {namespace} --create-namespace"
        
        # 添加仓库
        if helm_params.get('chart_repo'):
            # 如果有仓库 URL，先添加仓库
            repo_name = f"temp-repo-{hash(helm_params['chart_repo']) % 10000}"
            chart_name = f"{repo_name}/{chart_name}"
            # 注意：这里需要先执行 helm repo add
            pre_cmd = f"helm repo add {repo_name} {helm_params['chart_repo']} && helm repo update && "
            cmd = pre_cmd + cmd.replace(helm_params['chart_name'], chart_name)
        
        # 添加版本
        if helm_params.get('chart_version'):
            cmd += f" --version {helm_params['chart_version']}"
        
        # 添加 values 文件
        if helm_params.get('values_file'):
            cmd += f" --values {helm_params['values_file']}"
        
        # 添加自定义 values
        if helm_params.get('custom_values'):
            # 创建临时文件存储自定义 values
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(helm_params['custom_values'])
                cmd += f" --values {f.name}"
        
        # 添加选项
        if helm_params.get('wait', True):
            cmd += " --wait"
        
        if helm_params.get('atomic', False):
            cmd += " --atomic"
        
        if helm_params.get('timeout'):
            cmd += f" --timeout {helm_params['timeout']}s"
        
        if helm_params.get('dry_run', False):
            cmd += " --dry-run"
        
        return cmd
    
    def apply_manifest(self, manifest_yaml: str, namespace: str, dry_run: bool = False, wait_for_rollout: bool = True) -> Dict[str, Any]:
        """
        应用 Kubernetes YAML 清单
        
        Args:
            manifest_yaml: YAML 清单内容
            namespace: 命名空间
            dry_run: 是否执行干运行
            wait_for_rollout: 是否等待部署完成
            
        Returns:
            应用结果
        """
        import subprocess
        import tempfile
        
        try:
            # 创建临时文件存储 YAML 内容
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(manifest_yaml)
                temp_file = f.name
            
            # 构建 kubectl 命令
            cmd = f"kubectl apply -f {temp_file} -n {namespace}"
            
            if dry_run:
                cmd += " --dry-run=client"
            
            # 执行命令
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                raise Exception(f"kubectl apply failed: {result.stderr}")
            
            output = result.stdout
            
            # 如果需要等待部署完成
            if wait_for_rollout and not dry_run:
                # 尝试等待 deployment 完成
                wait_cmd = f"kubectl rollout status deployment -n {namespace} --timeout=300s"
                wait_result = subprocess.run(
                    wait_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if wait_result.stdout:
                    output += "\n" + wait_result.stdout
            
            return {
                'status': 'success',
                'message': f"Manifest applied successfully in namespace {namespace}",
                'output': output,
                'command': cmd
            }
            
        except subprocess.TimeoutExpired:
            raise Exception("kubectl apply timed out after 300 seconds")
        except Exception as e:
            logger.error(f"Manifest apply failed: {e}")
            raise
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file)
            except:
                pass
