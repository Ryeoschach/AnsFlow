"""
Django管理命令：设置本地执行器工具
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from cicd_integrations.models import CICDTool


class Command(BaseCommand):
    help = '创建系统默认的本地执行器工具'

    def handle(self, *args, **options):
        from project_management.models import Project
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        with transaction.atomic():
            # 获取或创建系统项目
            system_project, created = Project.objects.get_or_create(
                name='系统项目',
                defaults={
                    'description': '用于存放系统级工具和配置的项目',
                    'owner': User.objects.filter(is_superuser=True).first() or User.objects.first(),
                    'is_active': True,
                    'visibility': 'private'
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ 创建系统项目: {system_project.name}')
                )
            
            # 检查是否已存在本地执行器
            local_executor, created = CICDTool.objects.get_or_create(
                tool_type='local',
                project=system_project,
                defaults={
                    'name': 'AnsFlow 本地执行器',
                    'description': '系统内置的本地执行器，用于在AnsFlow服务器上直接执行流水线步骤',
                    'base_url': 'http://localhost:8000',
                    'username': 'system',
                    'token': 'local-executor-token',
                    'status': 'authenticated',  # 本地执行器始终处于已认证状态
                    'created_by': User.objects.filter(is_superuser=True).first() or User.objects.first(),
                    'config': {
                        'executor_type': 'local',
                        'max_concurrent_jobs': 5,
                        'timeout': 3600,
                        'enable_logs': True,
                        'workspace_path': '/tmp/ansflow-workspace',
                        'is_default': True  # 标记为默认本地执行器
                    }
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ 成功创建本地执行器工具: {local_executor.name} (ID: {local_executor.id})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️ 本地执行器工具已存在: {local_executor.name} (ID: {local_executor.id})'
                    )
                )
                
                # 确保状态为active
                if local_executor.status != 'active':
                    local_executor.status = 'active'
                    local_executor.save()
                    self.stdout.write(
                        self.style.SUCCESS('✅ 已激活本地执行器工具')
                    )
