"""
测试 GitHub Actions 集成的管理命令
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import asyncio
import os
from cicd_integrations.models import CICDTool, AtomicStep
from cicd_integrations.adapters import GitHubActionsAdapter


class Command(BaseCommand):
    help = '测试 GitHub Actions 连接并注册工具'

    def add_arguments(self, parser):
        parser.add_argument(
            '--github-url',
            type=str,
            default=os.getenv('GITHUB_URL', 'https://api.github.com'),
            help='GitHub API URL'
        )
        parser.add_argument(
            '--token',
            type=str,
            default=os.getenv('GITHUB_TOKEN', ''),
            help='GitHub Personal Access Token'
        )
        parser.add_argument(
            '--owner',
            type=str,
            default=os.getenv('GITHUB_OWNER', ''),
            help='GitHub 仓库所有者（用户名或组织名）'
        )
        parser.add_argument(
            '--repo',
            type=str,
            default=os.getenv('GITHUB_REPO', ''),
            help='GitHub 仓库名称'
        )
        parser.add_argument(
            '--register',
            action='store_true',
            help='注册 GitHub Actions 工具到数据库'
        )

    def handle(self, *args, **options):
        github_url = options['github_url']
        token = options['token']
        owner = options['owner']
        repo = options['repo']
        
        if not token:
            self.stdout.write(
                self.style.ERROR('GitHub token is required. Use --token or set GITHUB_TOKEN environment variable.')
            )
            return
        
        self.stdout.write(f'Testing GitHub Actions connection to: {github_url}')
        
        # 运行异步测试
        asyncio.run(self._test_github_actions(github_url, token, owner, repo, options['register']))

    async def _test_github_actions(self, github_url: str, token: str, owner: str, repo: str, should_register: bool):
        """异步测试 GitHub Actions 连接"""
        try:
            # 创建 GitHub Actions 适配器
            adapter = GitHubActionsAdapter(
                base_url=github_url,
                token=token,
                owner=owner,
                repo=repo
            )
            
            # 1. 健康检查
            self.stdout.write('1. 执行健康检查...')
            health_ok = await adapter.health_check()
            if health_ok:
                self.stdout.write(self.style.SUCCESS('✓ GitHub Actions 连接正常'))
            else:
                self.stdout.write(self.style.ERROR('✗ GitHub Actions 连接失败'))
                return
            
            # 2. 测试用户信息获取
            self.stdout.write('2. 测试用户信息获取...')
            try:
                user_response = await adapter.client.get(f"{github_url}/user")
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    self.stdout.write(self.style.SUCCESS(f'✓ 用户信息获取成功: {user_data.get("login", "Unknown")}'))
                else:
                    self.stdout.write(self.style.WARNING(f'⚠ 用户信息获取失败: HTTP {user_response.status_code}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ 用户信息获取失败: {e}'))
            
            # 3. 测试仓库访问（如果提供了仓库信息）
            if owner and repo:
                self.stdout.write(f'3. 测试仓库 {owner}/{repo} 访问权限...')
                try:
                    repo_response = await adapter.client.get(f"{github_url}/repos/{owner}/{repo}")
                    if repo_response.status_code == 200:
                        repo_data = repo_response.json()
                        self.stdout.write(self.style.SUCCESS(f'✓ 仓库访问成功: {repo_data.get("full_name", "Unknown")}'))
                        self.stdout.write(f'  仓库描述: {repo_data.get("description", "无描述")}')
                        self.stdout.write(f'  默认分支: {repo_data.get("default_branch", "unknown")}')
                        
                        # 检查 Actions 权限
                        actions_response = await adapter.client.get(f"{github_url}/repos/{owner}/{repo}/actions/permissions")
                        if actions_response.status_code == 200:
                            actions_data = actions_response.json()
                            self.stdout.write(f'  Actions 启用: {actions_data.get("enabled", False)}')
                        
                    else:
                        self.stdout.write(self.style.WARNING(f'⚠ 仓库访问受限: HTTP {repo_response.status_code}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'✗ 仓库访问失败: {e}'))
            else:
                self.stdout.write('3. 跳过仓库访问测试（未提供仓库信息）')
            
            # 4. 测试工作流配置生成
            self.stdout.write('4. 测试工作流配置生成...')
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
                        name='AnsFlow Test Pipeline',
                        steps=test_steps,
                        triggers={'branch': 'main', 'manual': True},
                        environment={'TEST_ENV': 'true', 'ANSFLOW': 'github-actions'}
                    )
                    
                    workflow_yaml = await adapter.create_pipeline_file(pipeline_def)
                    self.stdout.write(self.style.SUCCESS('✓ GitHub Actions 工作流配置生成成功'))
                    self.stdout.write('生成的工作流 YAML 预览:')
                    self.stdout.write('-' * 50)
                    # 只显示前25行
                    lines = workflow_yaml.split('\n')[:25]
                    for line in lines:
                        self.stdout.write(f'  {line}')
                    if len(workflow_yaml.split('\n')) > 25:
                        self.stdout.write('  ... (更多内容)')
                    self.stdout.write('-' * 50)
                else:
                    self.stdout.write(self.style.WARNING('⚠ 没有找到原子步骤，跳过配置生成测试'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ 配置生成失败: {e}'))
            
            # 5. 测试工作流列表获取（如果有仓库权限）
            if owner and repo:
                self.stdout.write('5. 测试工作流列表获取...')
                try:
                    workflows_response = await adapter.client.get(f"{github_url}/repos/{owner}/{repo}/actions/workflows")
                    if workflows_response.status_code == 200:
                        workflows_data = workflows_response.json()
                        workflow_count = workflows_data.get('total_count', 0)
                        self.stdout.write(self.style.SUCCESS(f'✓ 工作流列表获取成功，共 {workflow_count} 个工作流'))
                        
                        # 显示前几个工作流
                        for workflow in workflows_data.get('workflows', [])[:3]:
                            self.stdout.write(f'  - {workflow.get("name", "Unnamed")} ({workflow.get("state", "unknown")})')
                    else:
                        self.stdout.write(self.style.WARNING(f'⚠ 工作流列表获取失败: HTTP {workflows_response.status_code}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'✗ 工作流列表获取失败: {e}'))
            else:
                self.stdout.write('5. 跳过工作流列表测试（未提供仓库信息）')
            
            # 6. 注册工具到数据库
            if should_register:
                self.stdout.write('6. 注册 GitHub Actions 工具到数据库...')
                try:
                    tool_name = f'GitHub Actions'
                    if owner and repo:
                        tool_name += f' - {owner}/{repo}'
                    
                    tool, created = CICDTool.objects.get_or_create(
                        name=tool_name,
                        tool_type='github_actions',
                        defaults={
                            'description': f'GitHub Actions for repository {owner}/{repo}' if owner and repo else 'GitHub Actions integration',
                            'base_url': github_url,
                            'configuration': {
                                'token': '***hidden***',  # 不保存真实 token 到数据库
                                'owner': owner,
                                'repo': repo,
                                'api_version': '2022-11-28'
                            },
                            'is_active': True
                        }
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS('✓ GitHub Actions 工具注册成功'))
                    else:
                        self.stdout.write(self.style.SUCCESS('✓ GitHub Actions 工具已存在，配置已更新'))
                        
                    self.stdout.write(f'工具ID: {tool.id}')
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'✗ 工具注册失败: {e}'))
            else:
                self.stdout.write('6. 跳过工具注册（使用 --register 启用）')
            
            # 关闭连接
            await adapter.client.aclose()
            
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(self.style.SUCCESS('GitHub Actions 集成测试完成！'))
            self.stdout.write('=' * 60)
            
            if not should_register:
                self.stdout.write('\n提示: 使用 --register 参数可以将 GitHub Actions 工具注册到数据库')
            
            if not owner or not repo:
                self.stdout.write('\n提示: 使用 --owner 和 --repo 参数可以测试特定仓库的权限')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'GitHub Actions 集成测试失败: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())
