"""
测试 Kubernetes 集群连接的管理命令
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from kubernetes_integration.models import KubernetesCluster
from kubernetes_integration.k8s_client import KubernetesManager


class Command(BaseCommand):
    help = '测试 Kubernetes 集群连接'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cluster-id',
            type=int,
            help='要测试的集群 ID'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='测试所有集群'
        )

    def handle(self, *args, **options):
        cluster_id = options.get('cluster_id')
        test_all = options.get('all')

        if cluster_id:
            # 测试指定集群
            try:
                cluster = KubernetesCluster.objects.get(id=cluster_id)
                self.test_cluster(cluster)
            except KubernetesCluster.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'集群 ID {cluster_id} 不存在')
                )
        elif test_all:
            # 测试所有集群
            clusters = KubernetesCluster.objects.all()
            if not clusters:
                self.stdout.write(
                    self.style.WARNING('没有找到任何集群')
                )
                return

            for cluster in clusters:
                self.test_cluster(cluster)
                self.stdout.write('')  # 空行分隔
        else:
            self.stdout.write(
                self.style.ERROR('请指定 --cluster-id 或 --all 参数')
            )

    def test_cluster(self, cluster):
        """测试单个集群连接"""
        self.stdout.write(f'测试集群: {cluster.name} (ID: {cluster.id})')
        self.stdout.write(f'API 服务器: {cluster.api_server}')
        self.stdout.write(f'集群类型: {cluster.get_cluster_type_display()}')

        try:
            # 创建 K8s 管理器
            k8s_manager = KubernetesManager(cluster)
            
            # 测试连接
            cluster_info = k8s_manager.get_cluster_info()
            
            if cluster_info['connected']:
                self.stdout.write(
                    self.style.SUCCESS('✅ 连接成功!')
                )
                self.stdout.write(f'  Kubernetes 版本: {cluster_info.get("version", "未知")}')
                self.stdout.write(f'  节点状态: {cluster_info.get("ready_nodes", 0)}/{cluster_info.get("total_nodes", 0)} 就绪')
                self.stdout.write(f'  Pod 状态: {cluster_info.get("running_pods", 0)}/{cluster_info.get("total_pods", 0)} 运行中')
                
                # 更新数据库
                cluster.status = 'active'
                cluster.last_check = timezone.now()
                cluster.check_message = cluster_info.get('message', '连接成功')
                cluster.kubernetes_version = cluster_info.get('version', '')
                cluster.total_nodes = cluster_info.get('total_nodes', 0)
                cluster.ready_nodes = cluster_info.get('ready_nodes', 0)
                cluster.total_pods = cluster_info.get('total_pods', 0)
                cluster.running_pods = cluster_info.get('running_pods', 0)
                cluster.save()
                
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ 连接失败: {cluster_info.get("message", "未知错误")}')
                )
                
                # 更新数据库
                cluster.status = 'error'
                cluster.last_check = timezone.now()
                cluster.check_message = cluster_info.get('message', '连接失败')
                cluster.save()

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 测试失败: {str(e)}')
            )
            
            # 更新数据库
            cluster.status = 'error'
            cluster.last_check = timezone.now()
            cluster.check_message = f'测试失败: {str(e)}'
            cluster.save()
