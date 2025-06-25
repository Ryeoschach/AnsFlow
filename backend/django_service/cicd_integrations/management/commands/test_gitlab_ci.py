"""
测试 GitLab CI 集成的管理命令
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import asyncio
import os
from cicd_integrations.models import CICDTool, AtomicStep
from cicd_integrations.adapters import GitLabCIAdapter


class Command(BaseCommand):
    help = '测试 GitLab CI 连接并注册工具'

    def add_arguments(self, parser):
        parser.add_argument(
            '--gitlab-url',
            type=str,
            default=os.getenv('GITLAB_URL', 'https://gitlab.com'),
            help='GitLab 实例 URL'
        )
        parser.add_argument(
            '--token',
            type=str,
            default=os.getenv('GITLAB_TOKEN', ''),
            help='GitLab API Token'
        )
        parser.add_argument(
            '--project-id',
            type=str,
            default=os.getenv('GITLAB_PROJECT_ID', ''),
            help='GitLab 项目 ID'
        )
        parser.add_argument(
            '--register',
            action='store_true',
            help='注册 GitLab CI 工具到数据库'
        )

    def handle(self, *args, **options):
        gitlab_url = options['gitlab_url']
        token = options['token']
        project_id = options['project_id']
        
        if not token:
            self.stdout.write(
                self.style.ERROR('GitLab token is required. Use --token or set GITLAB_TOKEN environment variable.')
            )
            return
        
        self.stdout.write(f'Testing GitLab CI connection to: {gitlab_url}')
        
        # 运行异步测试
        asyncio.run(self._test_gitlab_ci(gitlab_url, token, project_id, options['register']))

    async def _test_gitlab_ci(self, gitlab_url: str, token: str, project_id: str, should_register: bool):
        """异步测试 GitLab CI 连接"""
        try:
            # 创建 GitLab CI 适配器
            adapter = GitLabCIAdapter(
                base_url=gitlab_url,
                token=token,
                project_id=project_id
            )
            
            # 1. 健康检查
            self.stdout.write('1. 执行健康检查...')
            health_ok = await adapter.health_check()
            if health_ok:
                self.stdout.write(self.style.SUCCESS('✓ GitLab CI 连接正常'))
            else:
                self.stdout.write(self.style.ERROR('✗ GitLab CI 连接失败'))
                return
            
            # 2. 测试项目访问（如果提供了项目ID）
            if project_id:
                self.stdout.write(f'2. 测试项目 {project_id} 访问权限...')
                try:
                    project_response = await adapter.client.get(f"{gitlab_url}/api/v4/projects/{project_id}")
                    if project_response.status_code == 200:
                        project_data = project_response.json()
                        self.stdout.write(self.style.SUCCESS(f'✓ 项目访问成功: {project_data.get("name", "Unknown")}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'⚠ 项目访问受限: HTTP {project_response.status_code}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'✗ 项目访问失败: {e}'))
            else:
                self.stdout.write('2. 跳过项目访问测试（未提供项目ID）')
            
            # 3. 测试流水线配置生成
                        self.stdout.write('3. 测试流水线配置生成...')
            try:
                from cicd_integrations.adapters import PipelineDefinition
                
                # 获取一些原子步骤进行测试
                atomic_steps = list(AtomicStep.objects.filter(visibility='public')[:3])
                if atomic_steps:
                    test_steps = []
                    for step in atomic_steps:
                        test_steps.append({
                            'type': step.step_type,
                            'parameters': step.default_parameters
                        })
                    
                    pipeline_def = PipelineDefinition(
                        name='test-pipeline',
                        steps=test_steps,
                        triggers={'branch': 'main'},
                        environment={'TEST_ENV': 'true'}
                    )
                    
                    gitlab_ci_yaml = await adapter.create_pipeline_file(pipeline_def)
                    self.stdout.write(self.style.SUCCESS('✓ GitLab CI 配置生成成功'))
                    self.stdout.write('生成的 .gitlab-ci.yml 预览:')
                    self.stdout.write('-' * 50)
                    # 只显示前20行
                    lines = gitlab_ci_yaml.split('\n')[:20]
                    for line in lines:
                        self.stdout.write(f'  {line}')
                    if len(gitlab_ci_yaml.split('\n')) > 20:
                        self.stdout.write('  ... (更多内容)')
                    self.stdout.write('-' * 50)
                else:
                    self.stdout.write(self.style.WARNING('⚠ 没有找到原子步骤，跳过配置生成测试'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ 配置生成失败: {e}'))
            
            # 4. 注册工具到数据库
            if should_register:
                self.stdout.write('4. 注册 GitLab CI 工具到数据库...')
                try:
                    tool, created = CICDTool.objects.get_or_create(
                        name='GitLab CI',
                        tool_type='gitlab_ci',
                        defaults={
                            'description': f'GitLab CI instance at {gitlab_url}',
                            'base_url': gitlab_url,
                            'configuration': {
                                'token': '***hidden***',  # 不保存真实 token 到数据库
                                'project_id': project_id,
                                'api_version': 'v4'
                            },
                            'is_active': True
                        }
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS('✓ GitLab CI 工具注册成功'))
                    else:
                        self.stdout.write(self.style.SUCCESS('✓ GitLab CI 工具已存在，配置已更新'))
                        
                    self.stdout.write(f'工具ID: {tool.id}')
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'✗ 工具注册失败: {e}'))
            else:
                self.stdout.write('4. 跳过工具注册（使用 --register 启用）')
            
            # 关闭连接
            await adapter.client.aclose()
            
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(self.style.SUCCESS('GitLab CI 集成测试完成！'))
            self.stdout.write('=' * 60)
            
            if not should_register:
                self.stdout.write('\n提示: 使用 --register 参数可以将 GitLab CI 工具注册到数据库')
            
            if not project_id:
                self.stdout.write('\n提示: 使用 --project-id 参数可以测试特定项目的访问权限')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'GitLab CI 集成测试失败: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())
