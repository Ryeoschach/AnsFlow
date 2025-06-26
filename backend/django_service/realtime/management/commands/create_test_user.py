"""
创建测试用户的Django管理命令
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = '创建WebSocket测试用户'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='testuser',
            help='用户名 (默认: testuser)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='testpass123',
            help='密码 (默认: testpass123)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='test@example.com',
            help='邮箱 (默认: test@example.com)'
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']
        
        with transaction.atomic():
            # 检查用户是否已存在
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'用户 {username} 已存在，跳过创建')
                )
                return
            
            # 创建测试用户
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_active=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'成功创建测试用户: {username}')
            )
            self.stdout.write(f'邮箱: {email}')
            self.stdout.write(f'密码: {password}')
            
            # 创建一些测试数据
            self._create_test_data(user)
    
    def _create_test_data(self, user):
        """创建一些测试数据"""
        try:
            from pipelines.models import Pipeline
            from cicd_integrations.models import PipelineExecution
            
            # 创建测试流水线
            pipeline, created = Pipeline.objects.get_or_create(
                name='测试流水线',
                defaults={
                    'description': '用于WebSocket测试的流水线',
                    'repository_url': 'https://github.com/test/repo.git',
                    'branch': 'main',
                    'created_by': user,
                    'config': {
                        'steps': [
                            {'name': '代码检出', 'type': 'git', 'order': 1},
                            {'name': '构建应用', 'type': 'build', 'order': 2},
                            {'name': '运行测试', 'type': 'test', 'order': 3},
                            {'name': '部署应用', 'type': 'deploy', 'order': 4}
                        ]
                    }
                }
            )
            
            if created:
                self.stdout.write(f'创建测试流水线: {pipeline.name}')
            
            # 创建测试执行记录
            execution, created = PipelineExecution.objects.get_or_create(
                id=999,
                defaults={
                    'pipeline': pipeline,
                    'status': 'pending',
                    'trigger_type': 'manual',
                    'triggered_by': user,
                    'parameters': {
                        'environment': {'TEST_MODE': 'true'}
                    }
                }
            )
            
            if created:
                self.stdout.write(f'创建测试执行记录: {execution.id}')
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'创建测试数据时出错: {e}')
            )
