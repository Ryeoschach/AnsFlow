from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from kubernetes_integration.models import KubernetesCluster


class Command(BaseCommand):
    help = '创建测试 Kubernetes 集群数据'

    def handle(self, *args, **options):
        # 获取或创建测试用户
        test_user, created = User.objects.get_or_create(
            username='test_admin',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'Admin',
                'is_staff': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ 创建测试用户: {test_user.username}')
            )
        
        # 清除现有测试数据
        KubernetesCluster.objects.filter(name__contains='环境').delete()
        
        # 创建测试集群
        test_clusters = [
            {
                'name': '开发环境集群',
                'description': '开发环境 Kubernetes 集群',
                'api_server': 'https://dev-k8s.example.com:6443',
                'auth_config': {
                    'type': 'token',
                    'token': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...'
                },
                'status': 'inactive',
                'is_default': False,
                'created_by': test_user
            },
            {
                'name': '生产环境集群',
                'description': '生产环境 Kubernetes 集群',
                'api_server': 'https://prod-k8s.example.com:6443',
                'auth_config': {
                    'type': 'kubeconfig',
                    'kubeconfig': '''apiVersion: v1
clusters:
- cluster:
    server: https://prod-k8s.example.com:6443
  name: production
contexts:
- context:
    cluster: production
    user: admin
  name: production-admin
current-context: production-admin
kind: Config
users:
- name: admin
  user:
    token: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...'''
                },
                'status': 'inactive',
                'is_default': True,
                'created_by': test_user
            },
            {
                'name': '测试环境集群',
                'description': '测试环境 Kubernetes 集群',
                'api_server': 'https://test-k8s.example.com:6443',
                'auth_config': {
                    'type': 'certificate',
                    'client_cert': '''-----BEGIN CERTIFICATE-----
MIIBkTCB+wIJAJ...
-----END CERTIFICATE-----''',
                    'client_key': '''-----BEGIN PRIVATE KEY-----
MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQC...
-----END PRIVATE KEY-----''',
                    'ca_cert': '''-----BEGIN CERTIFICATE-----
MIIBkTCB+wIJAJ...
-----END CERTIFICATE-----'''
                },
                'status': 'inactive',
                'is_default': False,
                'created_by': test_user
            }
        ]
        
        created_clusters = []
        for cluster_data in test_clusters:
            cluster = KubernetesCluster.objects.create(**cluster_data)
            created_clusters.append(cluster)
            self.stdout.write(
                self.style.SUCCESS(f'✅ 创建集群: {cluster.name} (ID: {cluster.id})')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 成功创建 {len(created_clusters)} 个测试集群！')
        )
