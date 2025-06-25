"""
Django 管理命令 - 测试 Jenkins 连接
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from project_management.models import Project
from cicd_integrations.models import CICDTool
from cicd_integrations.services import cicd_engine
import asyncio


class Command(BaseCommand):
    """测试 Jenkins 连接的管理命令"""
    
    help = 'Test Jenkins connection and create a sample CI/CD tool configuration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--jenkins-url',
            type=str,
            required=True,
            help='Jenkins 服务器 URL (例如: http://localhost:8080)'
        )
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='Jenkins 用户名'
        )
        parser.add_argument(
            '--token',
            type=str,
            required=True,
            help='Jenkins API Token'
        )
        parser.add_argument(
            '--project-id',
            type=int,
            help='项目 ID (如果不指定，将使用第一个可用项目)'
        )
        parser.add_argument(
            '--tool-name',
            type=str,
            default='jenkins-test',
            help='CI/CD 工具名称 (默认: jenkins-test)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 开始测试 Jenkins 连接...')
        )
        
        try:
            # 获取项目
            project = self._get_project(options['project_id'])
            self.stdout.write(
                f"使用项目: {project.name} (ID: {project.id})"
            )
            
            # 获取用户 (使用第一个超级用户)
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                raise CommandError("没有找到超级用户，请先创建一个超级用户")
            
            # 准备工具配置
            tool_data = {
                'name': options['tool_name'],
                'tool_type': 'jenkins',
                'base_url': options['jenkins_url'],
                'username': options['username'],
                'token': options['token'],
                'project_id': project.id,
                'config': {
                    'crumb_issuer': True,
                    'timeout': 30
                },
                'metadata': {
                    'test_connection': True,
                    'created_via': 'management_command'
                }
            }
            
            # 使用异步方法测试连接
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                tool = loop.run_until_complete(
                    cicd_engine.register_tool(tool_data, user)
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Jenkins 工具注册成功!")
                )
                self.stdout.write(f"工具 ID: {tool.id}")
                self.stdout.write(f"工具名称: {tool.name}")
                self.stdout.write(f"状态: {tool.get_status_display()}")
                self.stdout.write(f"最后健康检查: {tool.last_health_check}")
                
                # 执行额外的连接测试
                self.stdout.write("\n🔍 执行详细连接测试...")
                success = loop.run_until_complete(
                    cicd_engine.health_check_tool(tool)
                )
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS("✅ Jenkins 连接测试成功!")
                    )
                    
                    # 显示工具信息
                    self._display_tool_info(tool)
                    
                    # 提供下一步指导
                    self._show_next_steps(tool)
                else:
                    self.stdout.write(
                        self.style.WARNING("⚠️  连接测试失败，请检查配置")
                    )
                    
            finally:
                loop.close()
                
        except Exception as e:
            raise CommandError(f"测试失败: {str(e)}")
    
    def _get_project(self, project_id):
        """获取项目"""
        if project_id:
            try:
                return Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                raise CommandError(f"项目 ID {project_id} 不存在")
        else:
            project = Project.objects.first()
            if not project:
                raise CommandError("没有找到任何项目，请先创建一个项目")
            return project
    
    def _display_tool_info(self, tool):
        """显示工具信息"""
        self.stdout.write("\n📊 工具配置信息:")
        self.stdout.write(f"  • 名称: {tool.name}")
        self.stdout.write(f"  • 类型: {tool.get_tool_type_display()}")
        self.stdout.write(f"  • URL: {tool.base_url}")
        self.stdout.write(f"  • 用户名: {tool.username}")
        self.stdout.write(f"  • 项目: {tool.project.name}")
        self.stdout.write(f"  • 状态: {tool.get_status_display()}")
        self.stdout.write(f"  • 创建时间: {tool.created_at}")
    
    def _show_next_steps(self, tool):
        """显示下一步操作指导"""
        self.stdout.write("\n🎯 下一步操作:")
        self.stdout.write("1. 创建原子步骤:")
        self.stdout.write(f"   python manage.py create_atomic_steps")
        
        self.stdout.write("\n2. 测试流水线执行:")
        self.stdout.write(f"   python manage.py test_pipeline_execution --tool-id {tool.id}")
        
        self.stdout.write("\n3. 访问管理界面:")
        self.stdout.write("   http://localhost:8000/admin/cicd_integrations/")
        
        self.stdout.write("\n4. 访问 API 文档:")
        self.stdout.write("   http://localhost:8000/api/schema/swagger-ui/")
        
        self.stdout.write(f"\n5. 工具 API 端点:")
        self.stdout.write(f"   GET  /api/v1/cicd/tools/{tool.id}/")
        self.stdout.write(f"   POST /api/v1/cicd/tools/{tool.id}/health_check/")
        self.stdout.write(f"   POST /api/v1/cicd/tools/{tool.id}/execute_pipeline/")
