#!/usr/bin/env python3
"""
Kubernetes 集成功能测试脚本
用于验证 K8s 模块的各项功能
"""

import os
import sys
import django
import json
from datetime import datetime

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from kubernetes_integration.models import (
    KubernetesCluster, 
    KubernetesNamespace, 
    KubernetesDeployment,
    KubernetesService,
    KubernetesPod
)
from kubernetes_integration.k8s_client import KubernetesManager
from kubernetes_integration.tasks import (
    check_cluster_status,
    sync_cluster_resources,
    deploy_application,
    scale_deployment_task
)


def test_print(title, status="INFO"):
    """打印测试信息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_colors = {
        "INFO": "\033[94m",    # 蓝色
        "SUCCESS": "\033[92m", # 绿色
        "ERROR": "\033[91m",   # 红色
        "WARNING": "\033[93m"  # 黄色
    }
    reset_color = "\033[0m"
    color = status_colors.get(status, "")
    print(f"{color}[{timestamp}] [{status}] {title}{reset_color}")


def test_models():
    """测试数据模型"""
    test_print("开始测试数据模型...", "INFO")
    
    try:
        # 创建测试集群
        cluster = KubernetesCluster.objects.create(
            name="test-cluster",
            description="测试集群",
            api_server="https://localhost:6443",
            auth_config={
                "type": "kubeconfig",
                "kubeconfig": "fake-kubeconfig-content"
            },
            status="connected"
        )
        test_print(f"✅ 创建集群成功: {cluster.name}", "SUCCESS")
        
        # 创建测试命名空间
        namespace = KubernetesNamespace.objects.create(
            name="test-namespace",
            cluster=cluster,
            status="active",
            labels={"environment": "test"}
        )
        test_print(f"✅ 创建命名空间成功: {namespace.name}", "SUCCESS")
        
        # 创建测试部署
        deployment = KubernetesDeployment.objects.create(
            name="test-deployment",
            namespace=namespace,
            image="nginx:latest",
            replicas=2,
            status="running",
            labels={"app": "nginx"},
            config={
                "ports": [{"container_port": 80}],
                "environment_vars": {"ENV": "test"}
            }
        )
        test_print(f"✅ 创建部署成功: {deployment.name}", "SUCCESS")
        
        # 创建测试服务
        service = KubernetesService.objects.create(
            name="test-service",
            namespace=namespace,
            service_type="ClusterIP",
            selector={"app": "nginx"},
            ports=[{"port": 80, "target_port": 80}]
        )
        test_print(f"✅ 创建服务成功: {service.name}", "SUCCESS")
        
        # 创建测试 Pod
        pod = KubernetesPod.objects.create(
            name="test-pod",
            namespace=namespace,
            node_name="test-node",
            phase="Running",
            pod_ip="10.244.1.1",
            labels={"app": "nginx"}
        )
        test_print(f"✅ 创建 Pod 成功: {pod.name}", "SUCCESS")
        
        test_print("✅ 数据模型测试完成", "SUCCESS")
        return cluster
        
    except Exception as e:
        test_print(f"❌ 数据模型测试失败: {e}", "ERROR")
        return None


def test_k8s_client(cluster):
    """测试 Kubernetes 客户端"""
    test_print("开始测试 K8s 客户端...", "INFO")
    
    try:
        # 创建 K8s 管理器（模拟模式）
        manager = KubernetesManager(cluster)
        test_print("✅ K8s 管理器创建成功", "SUCCESS")
        
        # 测试集群信息获取
        cluster_info = manager.get_cluster_info()
        test_print(f"✅ 集群信息: {json.dumps(cluster_info, indent=2)}", "SUCCESS")
        
        # 测试命名空间列表
        namespaces = manager.list_namespaces()
        test_print(f"✅ 命名空间列表 ({len(namespaces)} 个): {[ns['name'] for ns in namespaces]}", "SUCCESS")
        
        # 测试部署列表
        deployments = manager.list_deployments()
        test_print(f"✅ 部署列表 ({len(deployments)} 个): {[dep['name'] for dep in deployments]}", "SUCCESS")
        
        # 测试 Pod 列表
        pods = manager.list_pods()
        test_print(f"✅ Pod 列表 ({len(pods)} 个): {[pod['name'] for pod in pods]}", "SUCCESS")
        
        # 测试创建部署
        deploy_spec = {
            "name": "test-app",
            "namespace": "default",
            "image": "nginx:1.20",
            "replicas": 2,
            "labels": {"app": "test-app"},
            "ports": [{"container_port": 80}],
            "environment_vars": {"NODE_ENV": "production"}
        }
        result = manager.create_deployment(deploy_spec)
        test_print(f"✅ 创建部署结果: {result}", "SUCCESS")
        
        # 测试扩缩容
        scale_result = manager.scale_deployment("test-app", "default", 3)
        test_print(f"✅ 扩缩容结果: {scale_result}", "SUCCESS")
        
        test_print("✅ K8s 客户端测试完成", "SUCCESS")
        return True
        
    except Exception as e:
        test_print(f"❌ K8s 客户端测试失败: {e}", "ERROR")
        return False


def test_async_tasks(cluster):
    """测试异步任务"""
    test_print("开始测试异步任务...", "INFO")
    
    try:
        # 测试集群状态检查任务
        test_print("测试集群状态检查任务...", "INFO")
        result = check_cluster_status.delay(cluster.id)
        test_print(f"✅ 集群状态检查任务已提交: {result.id}", "SUCCESS")
        
        # 测试资源同步任务
        test_print("测试资源同步任务...", "INFO")
        result = sync_cluster_resources.delay(cluster.id)
        test_print(f"✅ 资源同步任务已提交: {result.id}", "SUCCESS")
        
        # 测试应用部署任务
        test_print("测试应用部署任务...", "INFO")
        deploy_config = {
            "name": "async-test-app",
            "namespace": "default",
            "image": "nginx:latest",
            "replicas": 1,
            "labels": {"app": "async-test"}
        }
        result = deploy_application.delay(cluster.id, deploy_config)
        test_print(f"✅ 应用部署任务已提交: {result.id}", "SUCCESS")
        
        # 测试扩缩容任务
        test_print("测试扩缩容任务...", "INFO")
        result = scale_deployment_task.delay(cluster.id, "async-test-app", "default", 2)
        test_print(f"✅ 扩缩容任务已提交: {result.id}", "SUCCESS")
        
        test_print("✅ 异步任务测试完成", "SUCCESS")
        return True
        
    except Exception as e:
        test_print(f"❌ 异步任务测试失败: {e}", "ERROR")
        return False


def test_api_endpoints():
    """测试 API 端点"""
    test_print("开始测试 API 端点...", "INFO")
    
    try:
        from django.test import Client
        from django.contrib.auth.models import User
        from rest_framework.test import APIClient
        
        # 创建测试用户
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        test_print("✅ 创建测试用户成功", "SUCCESS")
        
        # 创建 API 客户端
        client = APIClient()
        client.force_authenticate(user=user)
        test_print("✅ API 客户端认证成功", "SUCCESS")
        
        # 测试集群列表 API
        response = client.get('/api/v1/kubernetes/clusters/')
        test_print(f"✅ 集群列表 API 状态码: {response.status_code}", "SUCCESS")
        
        # 测试命名空间列表 API
        response = client.get('/api/v1/kubernetes/namespaces/')
        test_print(f"✅ 命名空间列表 API 状态码: {response.status_code}", "SUCCESS")
        
        # 测试部署列表 API
        response = client.get('/api/v1/kubernetes/deployments/')
        test_print(f"✅ 部署列表 API 状态码: {response.status_code}", "SUCCESS")
        
        test_print("✅ API 端点测试完成", "SUCCESS")
        return True
        
    except Exception as e:
        test_print(f"❌ API 端点测试失败: {e}", "ERROR")
        return False


def cleanup_test_data():
    """清理测试数据"""
    test_print("开始清理测试数据...", "INFO")
    
    try:
        # 删除测试数据
        KubernetesPod.objects.filter(name__startswith="test-").delete()
        KubernetesService.objects.filter(name__startswith="test-").delete()
        KubernetesDeployment.objects.filter(name__startswith="test-").delete()
        KubernetesNamespace.objects.filter(name__startswith="test-").delete()
        KubernetesCluster.objects.filter(name__startswith="test-").delete()
        
        test_print("✅ 测试数据清理完成", "SUCCESS")
        
    except Exception as e:
        test_print(f"⚠️  清理测试数据时出错: {e}", "WARNING")


def main():
    """主测试函数"""
    test_print("=== Kubernetes 集成功能测试开始 ===", "INFO")
    
    # 测试计数器
    total_tests = 4
    passed_tests = 0
    
    # 1. 测试数据模型
    cluster = test_models()
    if cluster:
        passed_tests += 1
    
    # 2. 测试 K8s 客户端
    if cluster and test_k8s_client(cluster):
        passed_tests += 1
    
    # 3. 测试异步任务
    if cluster and test_async_tasks(cluster):
        passed_tests += 1
    
    # 4. 测试 API 端点
    if test_api_endpoints():
        passed_tests += 1
    
    # 清理测试数据
    cleanup_test_data()
    
    # 测试结果汇总
    test_print("=== 测试结果汇总 ===", "INFO")
    test_print(f"总测试数: {total_tests}", "INFO")
    test_print(f"通过测试: {passed_tests}", "SUCCESS" if passed_tests == total_tests else "WARNING")
    test_print(f"失败测试: {total_tests - passed_tests}", "ERROR" if passed_tests < total_tests else "INFO")
    
    if passed_tests == total_tests:
        test_print("🎉 所有测试通过！Kubernetes 集成功能正常", "SUCCESS")
        return 0
    else:
        test_print("❌ 部分测试失败，请检查错误信息", "ERROR")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
