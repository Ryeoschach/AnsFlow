"""
Kubernetes 集成异步任务
"""
from celery import shared_task
from django.utils import timezone
import json
import logging

# 设置日志
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def check_cluster_status(self, cluster_id):
    """检查 Kubernetes 集群状态"""
    try:
        from .models import KubernetesCluster
        from .k8s_client import KubernetesManager
        
        cluster = KubernetesCluster.objects.get(id=cluster_id)
        
        # 创建 K8s 管理器
        k8s_manager = KubernetesManager(cluster)
        
        # 检查集群连接
        cluster_info = k8s_manager.get_cluster_info()
        
        # 更新集群信息
        cluster.status = 'active' if cluster_info['connected'] else 'error'
        cluster.last_check = timezone.now()
        cluster.check_message = cluster_info.get('message', '')
        cluster.kubernetes_version = cluster_info.get('version', '')
        cluster.total_nodes = cluster_info.get('total_nodes', 0)
        cluster.ready_nodes = cluster_info.get('ready_nodes', 0)
        cluster.total_pods = cluster_info.get('total_pods', 0)
        cluster.running_pods = cluster_info.get('running_pods', 0)
        cluster.save()
        
        logger.info(f"集群 {cluster.name} 状态检查完成: {cluster.status}")
        
        return {
            'cluster_id': cluster_id,
            'status': cluster.status,
            'message': cluster.check_message,
            'cluster_info': cluster_info
        }
        
    except Exception as e:
        logger.error(f"检查集群 {cluster_id} 状态失败: {str(e)}")
        
        # 更新集群为错误状态
        try:
            cluster = KubernetesCluster.objects.get(id=cluster_id)
            cluster.status = 'error'
            cluster.last_check = timezone.now()
            cluster.check_message = f"连接失败: {str(e)}"
            cluster.save()
        except:
            pass
        
        # 重试
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            'cluster_id': cluster_id,
            'status': 'error',
            'error': str(e)
        }


@shared_task(bind=True, max_retries=3)
def sync_cluster_resources(self, cluster_id):
    """同步集群资源信息"""
    try:
        from .models import (
            KubernetesCluster, KubernetesNamespace, KubernetesDeployment,
            KubernetesService, KubernetesPod
        )
        from .k8s_client import KubernetesManager
        
        cluster = KubernetesCluster.objects.get(id=cluster_id)
        k8s_manager = KubernetesManager(cluster)
        
        sync_results = {
            'cluster_id': cluster_id,
            'synced_resources': {},
            'errors': []
        }
        
        try:
            # 同步命名空间
            namespaces = k8s_manager.list_namespaces()
            synced_namespaces = 0
            
            for ns_data in namespaces:
                namespace, created = KubernetesNamespace.objects.get_or_create(
                    cluster=cluster,
                    name=ns_data['name'],
                    defaults={
                        'status': ns_data.get('status', 'active'),
                        'labels': ns_data.get('labels', {}),
                        'annotations': ns_data.get('annotations', {}),
                    }
                )
                if not created:
                    # 更新现有命名空间
                    namespace.status = ns_data.get('status', 'active')
                    namespace.labels = ns_data.get('labels', {})
                    namespace.annotations = ns_data.get('annotations', {})
                    namespace.save()
                
                synced_namespaces += 1
            
            sync_results['synced_resources']['namespaces'] = synced_namespaces
            
        except Exception as e:
            sync_results['errors'].append(f"同步命名空间失败: {str(e)}")
        
        try:
            # 同步部署
            deployments = k8s_manager.list_deployments()
            synced_deployments = 0
            
            for deploy_data in deployments:
                try:
                    namespace = KubernetesNamespace.objects.get(
                        cluster=cluster,
                        name=deploy_data['namespace']
                    )
                    
                    deployment, created = KubernetesDeployment.objects.get_or_create(
                        cluster=cluster,
                        namespace=namespace,
                        name=deploy_data['name'],
                        defaults={
                            'image': deploy_data.get('image', ''),
                            'replicas': deploy_data.get('replicas', 1),
                            'status': deploy_data.get('status', 'unknown'),
                            'ready_replicas': deploy_data.get('ready_replicas', 0),
                            'labels': deploy_data.get('labels', {}),
                            'created_by_id': 1,  # 系统用户
                        }
                    )
                    if not created:
                        # 更新现有部署
                        deployment.image = deploy_data.get('image', deployment.image)
                        deployment.replicas = deploy_data.get('replicas', deployment.replicas)
                        deployment.status = deploy_data.get('status', deployment.status)
                        deployment.ready_replicas = deploy_data.get('ready_replicas', 0)
                        deployment.labels = deploy_data.get('labels', {})
                        deployment.save()
                    
                    synced_deployments += 1
                    
                except KubernetesNamespace.DoesNotExist:
                    sync_results['errors'].append(
                        f"命名空间 {deploy_data['namespace']} 不存在，跳过部署 {deploy_data['name']}"
                    )
            
            sync_results['synced_resources']['deployments'] = synced_deployments
            
        except Exception as e:
            sync_results['errors'].append(f"同步部署失败: {str(e)}")
        
        try:
            # 同步 Pod
            pods = k8s_manager.list_pods()
            synced_pods = 0
            
            for pod_data in pods:
                try:
                    namespace = KubernetesNamespace.objects.get(
                        cluster=cluster,
                        name=pod_data['namespace']
                    )
                    
                    pod, created = KubernetesPod.objects.get_or_create(
                        cluster=cluster,
                        namespace=namespace,
                        name=pod_data['name'],
                        defaults={
                            'phase': pod_data.get('phase', 'Unknown'),
                            'node_name': pod_data.get('node_name', ''),
                            'pod_ip': pod_data.get('pod_ip', ''),
                            'containers': pod_data.get('containers', []),
                            'labels': pod_data.get('labels', {}),
                            'ready': pod_data.get('ready', False),
                        }
                    )
                    if not created:
                        # 更新现有 Pod
                        pod.phase = pod_data.get('phase', pod.phase)
                        pod.node_name = pod_data.get('node_name', pod.node_name)
                        pod.pod_ip = pod_data.get('pod_ip', pod.pod_ip)
                        pod.containers = pod_data.get('containers', pod.containers)
                        pod.labels = pod_data.get('labels', pod.labels)
                        pod.ready = pod_data.get('ready', pod.ready)
                        pod.save()
                    
                    synced_pods += 1
                    
                except KubernetesNamespace.DoesNotExist:
                    sync_results['errors'].append(
                        f"命名空间 {pod_data['namespace']} 不存在，跳过 Pod {pod_data['name']}"
                    )
            
            sync_results['synced_resources']['pods'] = synced_pods
            
        except Exception as e:
            sync_results['errors'].append(f"同步 Pod 失败: {str(e)}")
        
        # 更新集群最后同步时间
        cluster.last_check = timezone.now()
        cluster.save()
        
        logger.info(f"集群 {cluster.name} 资源同步完成: {sync_results}")
        
        return sync_results
        
    except Exception as e:
        logger.error(f"同步集群 {cluster_id} 资源失败: {str(e)}")
        
        # 重试
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            'cluster_id': cluster_id,
            'error': str(e),
            'synced_resources': {},
            'errors': [str(e)]
        }


@shared_task(bind=True, max_retries=3)
def deploy_application(self, deployment_id):
    """部署应用到 Kubernetes"""
    try:
        from .models import KubernetesDeployment
        from .k8s_client import KubernetesManager
        
        deployment = KubernetesDeployment.objects.get(id=deployment_id)
        k8s_manager = KubernetesManager(deployment.cluster)
        
        # 构建部署规格
        deploy_spec = {
            'name': deployment.name,
            'namespace': deployment.namespace.name,
            'image': deployment.image,
            'replicas': deployment.replicas,
            'labels': deployment.labels,
            'environment_vars': deployment.environment_vars,
            'ports': deployment.ports,
            'resources': {
                'requests': {
                    'cpu': deployment.cpu_request,
                    'memory': deployment.memory_request,
                },
                'limits': {
                    'cpu': deployment.cpu_limit,
                    'memory': deployment.memory_limit,
                }
            }
        }
        
        # 执行部署
        result = k8s_manager.create_deployment(deploy_spec)
        
        # 更新部署状态
        deployment.status = 'progressing'
        deployment.save()
        
        logger.info(f"应用 {deployment.name} 部署已启动")
        
        return {
            'deployment_id': deployment_id,
            'status': 'success',
            'message': '部署已启动',
            'result': result
        }
        
    except Exception as e:
        logger.error(f"部署应用 {deployment_id} 失败: {str(e)}")
        
        # 更新部署状态为失败
        try:
            deployment = KubernetesDeployment.objects.get(id=deployment_id)
            deployment.status = 'replicafailure'
            deployment.save()
        except:
            pass
        
        # 重试
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            'deployment_id': deployment_id,
            'status': 'error',
            'error': str(e)
        }


@shared_task(bind=True, max_retries=3)
def scale_deployment(self, deployment_id, replicas):
    """扩缩容部署"""
    try:
        from .models import KubernetesDeployment
        from .k8s_client import KubernetesManager
        
        deployment = KubernetesDeployment.objects.get(id=deployment_id)
        k8s_manager = KubernetesManager(deployment.cluster)
        
        # 执行扩缩容
        result = k8s_manager.scale_deployment(
            deployment.name,
            deployment.namespace.name,
            replicas
        )
        
        # 更新部署副本数
        deployment.replicas = replicas
        deployment.save()
        
        logger.info(f"部署 {deployment.name} 已扩缩容到 {replicas} 个副本")
        
        return {
            'deployment_id': deployment_id,
            'status': 'success',
            'message': f'已扩缩容到 {replicas} 个副本',
            'replicas': replicas,
            'result': result
        }
        
    except Exception as e:
        logger.error(f"扩缩容部署 {deployment_id} 失败: {str(e)}")
        
        # 重试
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (self.request.retries + 1))
        
        return {
            'deployment_id': deployment_id,
            'status': 'error',
            'error': str(e),
            'replicas': replicas
        }


@shared_task(bind=True, max_retries=3)
def delete_resource(self, resource_type, resource_id):
    """删除 Kubernetes 资源"""
    try:
        from .models import KubernetesPod, KubernetesDeployment, KubernetesService
        from .k8s_client import KubernetesManager
        
        resource_models = {
            'pod': KubernetesPod,
            'deployment': KubernetesDeployment,
            'service': KubernetesService,
        }
        
        if resource_type not in resource_models:
            raise ValueError(f"不支持的资源类型: {resource_type}")
        
        model_class = resource_models[resource_type]
        resource = model_class.objects.get(id=resource_id)
        
        k8s_manager = KubernetesManager(resource.cluster)
        
        # 删除 Kubernetes 资源
        if resource_type == 'pod':
            result = k8s_manager.delete_pod(resource.name, resource.namespace.name)
        elif resource_type == 'deployment':
            result = k8s_manager.delete_deployment(resource.name, resource.namespace.name)
        elif resource_type == 'service':
            result = k8s_manager.delete_service(resource.name, resource.namespace.name)
        
        # 删除数据库记录
        resource.delete()
        
        logger.info(f"{resource_type} {resource.name} 已删除")
        
        return {
            'resource_type': resource_type,
            'resource_id': resource_id,
            'status': 'success',
            'message': f'{resource_type} 已删除',
            'result': result
        }
        
    except Exception as e:
        logger.error(f"删除 {resource_type} {resource_id} 失败: {str(e)}")
        
        # 重试
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (self.request.retries + 1))
        
        return {
            'resource_type': resource_type,
            'resource_id': resource_id,
            'status': 'error',
            'error': str(e)
        }


@shared_task
def periodic_cluster_sync():
    """定期同步所有活跃集群的资源"""
    try:
        from .models import KubernetesCluster
        
        active_clusters = KubernetesCluster.objects.filter(status='active')
        
        results = []
        for cluster in active_clusters:
            try:
                # 启动异步同步任务
                task = sync_cluster_resources.delay(cluster.id)
                results.append({
                    'cluster_id': cluster.id,
                    'cluster_name': cluster.name,
                    'sync_task_id': task.id
                })
            except Exception as e:
                results.append({
                    'cluster_id': cluster.id,
                    'cluster_name': cluster.name,
                    'error': str(e)
                })
        
        logger.info(f"定期同步已启动，共 {len(results)} 个集群")
        
        return {
            'status': 'success',
            'clusters_synced': len(results),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"定期同步失败: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task
def cleanup_stale_resources():
    """清理过期的资源记录"""
    try:
        from .models import KubernetesPod
        from datetime import timedelta
        
        # 删除超过7天没有更新的 Pod 记录
        cutoff_time = timezone.now() - timedelta(days=7)
        stale_pods = KubernetesPod.objects.filter(
            updated_at__lt=cutoff_time
        )
        
        deleted_count = stale_pods.count()
        stale_pods.delete()
        
        logger.info(f"清理了 {deleted_count} 个过期 Pod 记录")
        
        return {
            'status': 'success',
            'deleted_pods': deleted_count
        }
        
    except Exception as e:
        logger.error(f"清理过期资源失败: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task
def scale_deployment_task(cluster_id: int, deployment_name: str, namespace: str, replicas: int):
    """扩缩容部署任务"""
    try:
        from .models import KubernetesCluster, KubernetesDeployment, KubernetesNamespace
        from .k8s_client import KubernetesManager
        
        # 获取集群
        cluster = KubernetesCluster.objects.get(id=cluster_id)
        
        # 创建 K8s 管理器
        k8s_manager = KubernetesManager(cluster)
        
        # 执行扩缩容
        result = k8s_manager.scale_deployment(deployment_name, namespace, replicas)
        
        if result.get('status') == 'success':
            # 更新数据库记录
            try:
                namespace_obj = KubernetesNamespace.objects.get(
                    cluster=cluster,
                    name=namespace
                )
                deployment = KubernetesDeployment.objects.get(
                    namespace=namespace_obj,
                    name=deployment_name
                )
                deployment.replicas = replicas
                deployment.save()
                
                logger.info(f"部署 {deployment_name} 扩缩容到 {replicas} 个副本成功")
                
            except (KubernetesNamespace.DoesNotExist, KubernetesDeployment.DoesNotExist):
                logger.warning(f"数据库中未找到部署记录: {deployment_name}")
        
        return {
            'cluster_id': cluster_id,
            'deployment_name': deployment_name,
            'namespace': namespace,
            'replicas': replicas,
            'status': 'success',
            'message': result.get('message', '扩缩容完成'),
            'k8s_result': result
        }
        
    except Exception as e:
        logger.error(f"扩缩容任务失败: {str(e)}")
        return {
            'cluster_id': cluster_id,
            'deployment_name': deployment_name,
            'namespace': namespace,
            'replicas': replicas,
            'status': 'error',
            'error': str(e)
        }


@shared_task
def delete_deployment_task(cluster_id: int, deployment_name: str, namespace: str):
    """删除部署任务"""
    try:
        from .models import KubernetesCluster, KubernetesDeployment, KubernetesNamespace
        from .k8s_client import KubernetesManager
        
        # 获取集群
        cluster = KubernetesCluster.objects.get(id=cluster_id)
        
        # 创建 K8s 管理器
        k8s_manager = KubernetesManager(cluster)
        
        # 执行删除
        result = k8s_manager.delete_deployment(deployment_name, namespace)
        
        if result.get('status') == 'success':
            # 删除数据库记录
            try:
                namespace_obj = KubernetesNamespace.objects.get(
                    cluster=cluster,
                    name=namespace
                )
                deployment = KubernetesDeployment.objects.get(
                    namespace=namespace_obj,
                    name=deployment_name
                )
                deployment.delete()
                
                logger.info(f"部署 {deployment_name} 删除成功")
                
            except (KubernetesNamespace.DoesNotExist, KubernetesDeployment.DoesNotExist):
                logger.warning(f"数据库中未找到部署记录: {deployment_name}")
        
        return {
            'cluster_id': cluster_id,
            'deployment_name': deployment_name,
            'namespace': namespace,
            'status': 'success',
            'message': result.get('message', '删除完成'),
            'k8s_result': result
        }
        
    except Exception as e:
        logger.error(f"删除任务失败: {str(e)}")
        return {
            'cluster_id': cluster_id,
            'deployment_name': deployment_name,
            'namespace': namespace,
            'status': 'error',
            'error': str(e)
        }


@shared_task
def delete_pod_task(cluster_id: int, pod_name: str, namespace: str):
    """删除 Pod 任务"""
    try:
        from .models import KubernetesCluster, KubernetesPod, KubernetesNamespace
        from .k8s_client import KubernetesManager
        
        # 获取集群
        cluster = KubernetesCluster.objects.get(id=cluster_id)
        
        # 创建 K8s 管理器
        k8s_manager = KubernetesManager(cluster)
        
        # 执行删除
        result = k8s_manager.delete_pod(pod_name, namespace)
        
        if result.get('status') == 'success':
            # 删除数据库记录
            try:
                namespace_obj = KubernetesNamespace.objects.get(
                    cluster=cluster,
                    name=namespace
                )
                pod = KubernetesPod.objects.get(
                    namespace=namespace_obj,
                    name=pod_name
                )
                pod.delete()
                
                logger.info(f"Pod {pod_name} 删除成功")
                
            except (KubernetesNamespace.DoesNotExist, KubernetesPod.DoesNotExist):
                logger.warning(f"数据库中未找到 Pod 记录: {pod_name}")
        
        return {
            'cluster_id': cluster_id,
            'pod_name': pod_name,
            'namespace': namespace,
            'status': 'success',
            'message': result.get('message', '删除完成'),
            'k8s_result': result
        }
        
    except Exception as e:
        logger.error(f"删除 Pod 任务失败: {str(e)}")
        return {
            'cluster_id': cluster_id,
            'pod_name': pod_name,
            'namespace': namespace,
            'status': 'error',
            'error': str(e)
        }
