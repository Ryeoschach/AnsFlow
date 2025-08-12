#!/usr/bin/env python3
"""
测试 Kubernetes 集群连接的脚本
用于验证不同认证方式的连接配置
"""
import os
import sys
import django
import tempfile
import yaml
from pathlib import Path

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_service.settings')
django.setup()

from kubernetes_integration.k8s_client import KubernetesManager

def test_token_connection():
    """测试 Token 认证方式"""
    print("\n=== 测试 Token 认证方式 ===")
    
    config = {
        'type': 'token',
        'api_server': 'https://your-k8s-api-server:6443',
        'token': 'your-bearer-token-here',
        'ca_cert': None  # 可选的 CA 证书
    }
    
    try:
        manager = KubernetesManager(config)
        info = manager.get_cluster_info()
        print(f"✅ Token 连接成功")
        print(f"   Kubernetes 版本: {info.get('version', 'Unknown')}")
        print(f"   节点数量: {info.get('total_nodes', 'Unknown')}")
        print(f"   就绪节点: {info.get('ready_nodes', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ Token 连接失败: {e}")
        return False

def test_kubeconfig_connection():
    """测试 Kubeconfig 认证方式"""
    print("\n=== 测试 Kubeconfig 认证方式 ===")
    
    # 示例 kubeconfig 内容
    kubeconfig_content = """
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: <CA_CERT_DATA>
    server: https://your-k8s-api-server:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: kubernetes-admin
  name: kubernetes-admin@kubernetes
current-context: kubernetes-admin@kubernetes
kind: Config
preferences: {}
users:
- name: kubernetes-admin
  user:
    client-certificate-data: <CLIENT_CERT_DATA>
    client-key-data: <CLIENT_KEY_DATA>
"""
    
    config = {
        'type': 'kubeconfig',
        'kubeconfig': kubeconfig_content
    }
    
    try:
        manager = KubernetesManager(config)
        info = manager.get_cluster_info()
        print(f"✅ Kubeconfig 连接成功")
        print(f"   Kubernetes 版本: {info.get('version', 'Unknown')}")
        print(f"   节点数量: {info.get('total_nodes', 'Unknown')}")
        print(f"   就绪节点: {info.get('ready_nodes', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ Kubeconfig 连接失败: {e}")
        return False

def test_certificate_connection():
    """测试证书认证方式"""
    print("\n=== 测试证书认证方式 ===")
    
    config = {
        'type': 'certificate',
        'api_server': 'https://your-k8s-api-server:6443',
        'client_cert': '''-----BEGIN CERTIFICATE-----
<YOUR_CLIENT_CERTIFICATE_DATA>
-----END CERTIFICATE-----''',
        'client_key': '''-----BEGIN PRIVATE KEY-----
<YOUR_CLIENT_PRIVATE_KEY_DATA>
-----END PRIVATE KEY-----''',
        'ca_cert': '''-----BEGIN CERTIFICATE-----
<YOUR_CA_CERTIFICATE_DATA>
-----END CERTIFICATE-----'''
    }
    
    try:
        manager = KubernetesManager(config)
        info = manager.get_cluster_info()
        print(f"✅ 证书连接成功")
        print(f"   Kubernetes 版本: {info.get('version', 'Unknown')}")
        print(f"   节点数量: {info.get('total_nodes', 'Unknown')}")
        print(f"   就绪节点: {info.get('ready_nodes', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ 证书连接失败: {e}")
        return False

def test_simulation_mode():
    """测试模拟模式"""
    print("\n=== 测试模拟模式 ===")
    
    config = {
        'type': 'token',
        'api_server': 'https://simulation-cluster:6443',
        'token': 'simulation-token'
    }
    
    try:
        # 强制进入模拟模式
        import kubernetes_integration.k8s_client as k8s_client
        original_value = getattr(k8s_client, 'KUBERNETES_AVAILABLE', True)
        k8s_client.KUBERNETES_AVAILABLE = False
        
        manager = KubernetesManager(config)
        info = manager.get_cluster_info()
        print(f"✅ 模拟模式运行成功")
        print(f"   Kubernetes 版本: {info.get('version', 'Unknown')}")
        print(f"   节点数量: {info.get('total_nodes', 'Unknown')}")
        print(f"   就绪节点: {info.get('ready_nodes', 'Unknown')}")
        
        # 恢复原始值
        k8s_client.KUBERNETES_AVAILABLE = original_value
        return True
    except Exception as e:
        print(f"❌ 模拟模式失败: {e}")
        return False

def test_validation_endpoint():
    """测试验证端点"""
    print("\n=== 测试验证端点 ===")
    
    from kubernetes_integration.views import validate_kubernetes_connection
    from rest_framework.test import APIRequestFactory
    from django.contrib.auth.models import User
    import json
    
    factory = APIRequestFactory()
    
    # 创建测试用户（如果不存在）
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    
    test_data = {
        'name': '测试集群',
        'api_server': 'https://test-cluster:6443',
        'auth_config': {
            'type': 'token',
            'token': 'test-token'
        }
    }
    
    request = factory.post(
        '/api/kubernetes/validate-connection/',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    request.user = user
    
    try:
        response = validate_kubernetes_connection(request)
        print(f"✅ 验证端点响应成功")
        print(f"   状态码: {response.status_code}")
        print(f"   响应内容: {response.data}")
        return True
    except Exception as e:
        print(f"❌ 验证端点失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始测试 Kubernetes 集群连接功能")
    print("=" * 50)
    
    results = []
    
    # 测试各种连接方式
    results.append(("模拟模式", test_simulation_mode()))
    results.append(("验证端点", test_validation_endpoint()))
    
    # 显示测试结果总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print("=" * 50)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name:20} {status}")
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    print(f"\n总计: {success_count}/{total_count} 个测试通过")
    
    if success_count == total_count:
        print("🎉 所有测试都通过了！")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置")
        return 1

if __name__ == '__main__':
    sys.exit(main())
