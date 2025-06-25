"""
Django 管理命令 - 创建示例原子步骤
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from cicd_integrations.models import AtomicStep


class Command(BaseCommand):
    """创建示例原子步骤的管理命令"""
    
    help = 'Create sample atomic steps for CI/CD pipelines'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='用户 ID (如果不指定，将使用第一个超级用户)'
        )
        parser.add_argument(
            '--public',
            action='store_true',
            help='创建公共步骤 (默认为私有)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 开始创建示例原子步骤...')
        )
        
        # 获取用户
        user = self._get_user(options['user_id'])
        is_public = options['public']
        
        # 定义示例步骤
        sample_steps = [
            {
                'name': 'Git Checkout',
                'step_type': 'fetch_code',
                'description': '从 Git 仓库检出代码',
                'parameters': {
                    'repository_url': '${GIT_URL}',
                    'branch': '${GIT_BRANCH}',
                    'shallow_clone': True,
                    'submodules': False
                }
            },
            {
                'name': 'Maven Build',
                'step_type': 'build',
                'description': '使用 Maven 构建 Java 项目',
                'parameters': {
                    'tool': 'mvn',
                    'command': 'clean compile',
                    'profiles': ['dev'],
                    'skip_tests': False
                }
            },
            {
                'name': 'NPM Install & Build',
                'step_type': 'build',
                'description': '安装 NPM 依赖并构建前端项目',
                'parameters': {
                    'tool': 'npm',
                    'commands': ['npm install', 'npm run build'],
                    'node_version': '18',
                    'cache_dependencies': True
                }
            },
            {
                'name': 'Docker Build',
                'step_type': 'build',
                'description': '构建 Docker 镜像',
                'parameters': {
                    'dockerfile': 'Dockerfile',
                    'tag': '${BUILD_NUMBER}',
                    'build_args': {
                        'NODE_ENV': 'production'
                    },
                    'no_cache': False
                }
            },
            {
                'name': 'Unit Tests',
                'step_type': 'test',
                'description': '运行单元测试',
                'parameters': {
                    'command': 'mvn test',
                    'coverage': True,
                    'coverage_threshold': 80,
                    'report_format': 'xml',
                    'fail_on_error': True
                }
            },
            {
                'name': 'Integration Tests',
                'step_type': 'test',
                'description': '运行集成测试',
                'parameters': {
                    'command': 'mvn verify -P integration-tests',
                    'database_setup': True,
                    'test_data': 'fixtures/integration.sql',
                    'parallel': False
                }
            },
            {
                'name': 'SonarQube Scan',
                'step_type': 'security_scan',
                'description': 'SonarQube 代码质量扫描',
                'parameters': {
                    'tool': 'sonarqube',
                    'project_key': '${PROJECT_KEY}',
                    'quality_gate': True,
                    'fail_on_gate_failure': True
                }
            },
            {
                'name': 'OWASP Dependency Check',
                'step_type': 'security_scan',
                'description': 'OWASP 依赖安全扫描',
                'parameters': {
                    'tool': 'dependency-check',
                    'format': 'XML',
                    'fail_on_cvss': 7.0,
                    'suppress_file': 'dependency-check-suppressions.xml'
                }
            },
            {
                'name': 'Deploy to Staging',
                'step_type': 'deploy',
                'description': '部署到测试环境',
                'parameters': {
                    'environment': 'staging',
                    'strategy': 'rolling',
                    'health_check_url': '${STAGING_URL}/health',
                    'rollback_on_failure': True,
                    'timeout': 300
                }
            },
            {
                'name': 'Deploy to Production',
                'step_type': 'deploy',
                'description': '部署到生产环境',
                'parameters': {
                    'environment': 'production',
                    'strategy': 'blue_green',
                    'approval_required': True,
                    'health_check_url': '${PROD_URL}/health',
                    'rollback_on_failure': True,
                    'timeout': 600
                },
                'conditions': {
                    'branch': 'main',
                    'previous_steps_success': True,
                    'manual_approval': True
                }
            },
            {
                'name': 'Slack Notification',
                'step_type': 'notify',
                'description': '发送 Slack 通知',
                'parameters': {
                    'channel': '${SLACK_CHANNEL}',
                    'on_success': True,
                    'on_failure': True,
                    'include_logs': False,
                    'mention_users': ['@channel']
                }
            },
            {
                'name': 'Email Notification',
                'step_type': 'notify',
                'description': '发送邮件通知',
                'parameters': {
                    'recipients': ['${TEAM_EMAIL}'],
                    'on_success': False,
                    'on_failure': True,
                    'template': 'pipeline_status',
                    'include_artifacts': True
                }
            }
        ]
        
        created_count = 0
        skipped_count = 0
        
        for step_data in sample_steps:
            # 检查是否已存在
            if AtomicStep.objects.filter(
                name=step_data['name'],
                created_by=user
            ).exists():
                self.stdout.write(
                    self.style.WARNING(f"  跳过已存在的步骤: {step_data['name']}")
                )
                skipped_count += 1
                continue
            
            # 创建步骤
            step = AtomicStep.objects.create(
                name=step_data['name'],
                step_type=step_data['step_type'],
                description=step_data['description'],
                parameters=step_data['parameters'],
                conditions=step_data.get('conditions', {}),
                created_by=user,
                is_public=is_public
            )
            
            self.stdout.write(
                self.style.SUCCESS(f"  ✅ 创建步骤: {step.name}")
            )
            created_count += 1
        
        # 显示结果
        self.stdout.write(f"\n📊 创建结果:")
        self.stdout.write(f"  • 新创建: {created_count} 个步骤")
        self.stdout.write(f"  • 跳过: {skipped_count} 个步骤")
        self.stdout.write(f"  • 步骤类型: {'公共' if is_public else '私有'}")
        self.stdout.write(f"  • 创建者: {user.username}")
        
        if created_count > 0:
            self.stdout.write(f"\n🎯 下一步操作:")
            self.stdout.write("1. 在管理界面查看步骤:")
            self.stdout.write("   http://localhost:8000/admin/cicd_integrations/atomicstep/")
            
            self.stdout.write("\n2. 通过 API 获取步骤:")
            self.stdout.write("   GET /api/v1/cicd/atomic-steps/")
            
            self.stdout.write("\n3. 创建流水线使用这些步骤:")
            self.stdout.write("   python manage.py create_sample_pipeline")
    
    def _get_user(self, user_id):
        """获取用户"""
        if user_id:
            try:
                return User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise CommandError(f"用户 ID {user_id} 不存在")
        else:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                raise CommandError("没有找到超级用户，请先创建一个超级用户")
            return user
