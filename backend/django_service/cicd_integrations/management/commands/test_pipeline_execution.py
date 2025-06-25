"""
Django 管理命令 - 测试流水线执行
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from pipelines.models import Pipeline
from cicd_integrations.models import CICDTool, AtomicStep
from cicd_integrations.services import cicd_engine
import asyncio
import json


class Command(BaseCommand):
    """测试流水线执行的管理命令"""
    
    help = 'Test pipeline execution with CI/CD tools'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--tool-id',
            type=int,
            required=True,
            help='CI/CD 工具 ID'
        )
        parser.add_argument(
            '--pipeline-id',
            type=int,
            help='流水线 ID (如果不指定，将创建示例流水线)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示配置，不实际执行'
        )
        parser.add_argument(
            '--parameters',
            type=str,
            help='执行参数 (JSON 格式)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 开始测试流水线执行...')
        )
        
        try:
            # 获取 CI/CD 工具
            tool = self._get_tool(options['tool_id'])
            self.stdout.write(f"使用 CI/CD 工具: {tool.name} ({tool.tool_type})")
            
            # 获取或创建流水线
            pipeline = self._get_or_create_pipeline(options['pipeline_id'], tool)
            self.stdout.write(f"使用流水线: {pipeline.name}")
            
            # 解析执行参数
            parameters = {}
            if options['parameters']:
                try:
                    parameters = json.loads(options['parameters'])
                except json.JSONDecodeError:
                    raise CommandError("参数格式错误，请使用有效的 JSON 格式")
            
            # 显示配置信息
            self._display_configuration(tool, pipeline, parameters)
            
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING("🔍 DRY RUN 模式 - 不会实际执行流水线")
                )
                return
            
            # 获取用户
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                raise CommandError("没有找到超级用户")
            
            # 执行流水线
            self.stdout.write("\n🏃 开始执行流水线...")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                execution = loop.run_until_complete(
                    cicd_engine.execute_pipeline(
                        pipeline=pipeline,
                        tool=tool,
                        trigger_type='manual',
                        triggered_by=user,
                        parameters=parameters
                    )
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ 流水线执行已启动!")
                )
                
                self._display_execution_info(execution)
                self._show_monitoring_commands(execution)
                
            finally:
                loop.close()
                
        except Exception as e:
            raise CommandError(f"执行失败: {str(e)}")
    
    def _get_tool(self, tool_id):
        """获取 CI/CD 工具"""
        try:
            tool = CICDTool.objects.get(id=tool_id)
            if tool.status != 'active':
                raise CommandError(f"工具 {tool.name} 状态为 {tool.status}，无法执行")
            return tool
        except CICDTool.DoesNotExist:
            raise CommandError(f"CI/CD 工具 ID {tool_id} 不存在")
    
    def _get_or_create_pipeline(self, pipeline_id, tool):
        """获取或创建流水线"""
        if pipeline_id:
            try:
                return Pipeline.objects.get(id=pipeline_id)
            except Pipeline.DoesNotExist:
                raise CommandError(f"流水线 ID {pipeline_id} 不存在")
        else:
            # 创建示例流水线
            return self._create_sample_pipeline(tool)
    
    def _create_sample_pipeline(self, tool):
        """创建示例流水线"""
        self.stdout.write("📝 创建示例流水线...")
        
        # 获取一些原子步骤
        fetch_step = AtomicStep.objects.filter(step_type='fetch_code').first()
        build_step = AtomicStep.objects.filter(step_type='build').first()
        test_step = AtomicStep.objects.filter(step_type='test').first()
        
        if not all([fetch_step, build_step, test_step]):
            raise CommandError(
                "缺少必要的原子步骤，请先运行: python manage.py create_atomic_steps"
            )
        
        # 创建流水线配置
        pipeline_config = {
            'steps': [
                {
                    'name': 'Checkout Code',
                    'type': 'fetch_code',
                    'parameters': {
                        'repository_url': 'https://github.com/example/repo.git',
                        'branch': 'main',
                        'shallow_clone': True
                    }
                },
                {
                    'name': 'Build Application',
                    'type': 'build',
                    'parameters': {
                        'tool': 'mvn',
                        'command': 'clean compile',
                        'skip_tests': False
                    }
                },
                {
                    'name': 'Run Tests',
                    'type': 'test',
                    'parameters': {
                        'command': 'mvn test',
                        'coverage': True,
                        'coverage_threshold': 80
                    }
                }
            ],
            'environment': {
                'JAVA_HOME': '/usr/lib/jvm/java-11-openjdk',
                'MAVEN_OPTS': '-Xmx512m',
                'BUILD_NUMBER': '${BUILD_NUMBER}'
            },
            'triggers': {
                'webhook': True,
                'schedule': '0 2 * * *'  # 每天凌晨2点
            },
            'artifacts': [
                'target/*.jar',
                'reports/test-results.xml',
                'reports/coverage/**'
            ],
            'timeout': 1800  # 30分钟
        }
        
        # 创建流水线
        user = User.objects.filter(is_superuser=True).first()
        pipeline = Pipeline.objects.create(
            name=f'Sample Pipeline for {tool.name}',
            description=f'示例流水线，用于测试 {tool.name} 集成',
            project=tool.project,
            created_by=user,
            config=pipeline_config
        )
        
        return pipeline
    
    def _display_configuration(self, tool, pipeline, parameters):
        """显示配置信息"""
        self.stdout.write("\n📋 执行配置:")
        self.stdout.write(f"  🔧 CI/CD 工具:")
        self.stdout.write(f"    • 名称: {tool.name}")
        self.stdout.write(f"    • 类型: {tool.get_tool_type_display()}")
        self.stdout.write(f"    • URL: {tool.base_url}")
        self.stdout.write(f"    • 状态: {tool.get_status_display()}")
        
        self.stdout.write(f"\n  📄 流水线:")
        self.stdout.write(f"    • 名称: {pipeline.name}")
        self.stdout.write(f"    • 项目: {pipeline.project.name}")
        self.stdout.write(f"    • 步骤数量: {len(pipeline.config.get('steps', []))}")
        
        if parameters:
            self.stdout.write(f"\n  ⚙️  执行参数:")
            for key, value in parameters.items():
                self.stdout.write(f"    • {key}: {value}")
        
        # 显示步骤详情
        steps = pipeline.config.get('steps', [])
        if steps:
            self.stdout.write(f"\n  📋 流水线步骤:")
            for i, step in enumerate(steps, 1):
                self.stdout.write(f"    {i}. {step.get('name', 'Unknown')} ({step.get('type', 'custom')})")
    
    def _display_execution_info(self, execution):
        """显示执行信息"""
        self.stdout.write(f"\n📊 执行信息:")
        self.stdout.write(f"  • 执行 ID: {execution.id}")
        self.stdout.write(f"  • 外部 ID: {execution.external_id or '待分配'}")
        self.stdout.write(f"  • 状态: {execution.get_status_display()}")
        self.stdout.write(f"  • 触发类型: {execution.get_trigger_type_display()}")
        self.stdout.write(f"  • 触发者: {execution.triggered_by.username if execution.triggered_by else 'System'}")
        self.stdout.write(f"  • 创建时间: {execution.created_at}")
        
        if execution.external_url:
            self.stdout.write(f"  • 外部 URL: {execution.external_url}")
    
    def _show_monitoring_commands(self, execution):
        """显示监控命令"""
        self.stdout.write(f"\n🔍 监控命令:")
        self.stdout.write("1. 查看执行状态:")
        self.stdout.write(f"   GET /api/v1/cicd/executions/{execution.id}/")
        
        self.stdout.write("\n2. 获取执行日志:")
        self.stdout.write(f"   GET /api/v1/cicd/executions/{execution.id}/logs/")
        
        self.stdout.write("\n3. 取消执行:")
        self.stdout.write(f"   POST /api/v1/cicd/executions/{execution.id}/cancel/")
        
        self.stdout.write("\n4. 在管理界面查看:")
        self.stdout.write(f"   http://localhost:8000/admin/cicd_integrations/pipelineexecution/{execution.id}/change/")
        
        self.stdout.write(f"\n5. 使用 curl 监控状态:")
        self.stdout.write(f'   curl -H "Authorization: Bearer <token>" \\')
        self.stdout.write(f'        http://localhost:8000/api/v1/cicd/executions/{execution.id}/')
