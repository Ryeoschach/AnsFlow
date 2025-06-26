"""
测试原子步骤执行引擎的管理命令
"""
import asyncio
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from pipelines.models import Pipeline
from cicd_integrations.models import AtomicStep, PipelineExecution
from cicd_integrations.services import cicd_engine

User = get_user_model()


class Command(BaseCommand):
    help = '测试原子步骤执行引擎'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pipeline-id',
            type=int,
            help='要测试的流水线ID'
        )
        parser.add_argument(
            '--create-test-pipeline',
            action='store_true',
            help='创建测试流水线'
        )
        parser.add_argument(
            '--list-pipelines',
            action='store_true',
            help='列出所有流水线'
        )

    def handle(self, *args, **options):
        if options['list_pipelines']:
            self.list_pipelines()
        elif options['create_test_pipeline']:
            asyncio.run(self.create_test_pipeline())
        elif options['pipeline_id']:
            asyncio.run(self.test_pipeline_execution(options['pipeline_id']))
        else:
            self.stdout.write(
                self.style.ERROR('请指定 --pipeline-id, --create-test-pipeline 或 --list-pipelines')
            )

    def list_pipelines(self):
        """列出所有流水线"""
        self.stdout.write(self.style.SUCCESS('=== 流水线列表 ==='))
        
        pipelines = Pipeline.objects.all()
        if not pipelines:
            self.stdout.write(self.style.WARNING('没有找到流水线'))
            return
        
        for pipeline in pipelines:
            self.stdout.write(f"ID: {pipeline.id}, 名称: {pipeline.name}")
            atomic_steps = AtomicStep.objects.filter(pipeline=pipeline).order_by('order')
            self.stdout.write(f"  原子步骤数量: {atomic_steps.count()}")
            for step in atomic_steps:
                self.stdout.write(f"    - {step.name} ({step.step_type})")
            self.stdout.write("")

    async def create_test_pipeline(self):
        """创建测试流水线"""
        self.stdout.write(self.style.SUCCESS('=== 创建测试流水线 ==='))
        
        # 获取或创建用户
        user, _ = await User.objects.aget_or_create(
            username='admin',
            defaults={'email': 'admin@example.com'}
        )
        
        # 获取或创建项目
        from project_management.models import Project
        project, _ = await Project.objects.aget_or_create(
            name='测试项目',
            defaults={
                'description': '用于测试原子步骤执行引擎的项目',
                'owner': user
            }
        )
        
        # 创建流水线
        pipeline = await Pipeline.objects.acreate(
            name='测试原子步骤流水线',
            description='用于测试原子步骤执行引擎的测试流水线',
            project=project,
            created_by=user,
            config={
                'triggers': {'manual': True},
                'environment': {'NODE_ENV': 'test'},
                'timeout': 1800
            }
        )
        
        # 创建原子步骤
        steps_config = [
            {
                'name': '获取代码',
                'step_type': 'fetch_code',
                'order': 1,
                'config': {
                    'repository': 'https://github.com/example/test-repo.git',
                    'branch': 'main'
                },
                'timeout': 300
            },
            {
                'name': '安装依赖',
                'step_type': 'build',
                'order': 2,
                'config': {
                    'command': 'npm install',
                    'working_directory': '${WORKSPACE}'
                },
                'dependencies': ['获取代码'],
                'timeout': 600
            },
            {
                'name': '运行测试',
                'step_type': 'test',
                'order': 3,
                'config': {
                    'command': 'npm test',
                    'working_directory': '${WORKSPACE}',
                    'test_results_path': 'test-results.xml'
                },
                'dependencies': ['安装依赖'],
                'timeout': 900
            },
            {
                'name': '安全扫描',
                'step_type': 'security_scan',
                'order': 4,
                'config': {
                    'scan_type': 'dependency',
                    'tool': 'npm audit'
                },
                'dependencies': ['安装依赖'],
                'timeout': 300
            },
            {
                'name': '构建应用',
                'step_type': 'build',
                'order': 5,
                'config': {
                    'command': 'npm run build',
                    'working_directory': '${WORKSPACE}',
                    'artifacts': ['dist/']
                },
                'dependencies': ['运行测试', '安全扫描'],
                'timeout': 600
            },
            {
                'name': '部署到测试环境',
                'step_type': 'deploy',
                'order': 6,
                'config': {
                    'environment': 'test',
                    'target': 'test.example.com',
                    'artifacts': ['dist/']
                },
                'dependencies': ['构建应用'],
                'conditions': {
                    'branch': 'main',
                    'test_passed': True
                },
                'timeout': 300
            },
            {
                'name': '发送通知',
                'step_type': 'notify',
                'order': 7,
                'config': {
                    'webhook_url': 'https://hooks.slack.com/services/TEST',
                    'message': '流水线执行完成: ${PIPELINE_NAME}'
                },
                'dependencies': ['部署到测试环境'],
                'timeout': 60
            }
        ]
        
        for step_config in steps_config:
            await AtomicStep.objects.acreate(
                pipeline=pipeline,
                name=step_config['name'],
                step_type=step_config['step_type'],
                order=step_config['order'],
                config=step_config['config'],
                dependencies=step_config.get('dependencies', []),
                conditions=step_config.get('conditions', {}),
                timeout=step_config.get('timeout', 600),
                retry_count=step_config.get('retry_count', 0),
                created_by=user
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'测试流水线创建成功，ID: {pipeline.id}')
        )
        self.stdout.write(f'流水线名称: {pipeline.name}')
        self.stdout.write(f'原子步骤数量: {len(steps_config)}')

    async def test_pipeline_execution(self, pipeline_id):
        """测试流水线执行"""
        self.stdout.write(self.style.SUCCESS(f'=== 测试流水线执行 (ID: {pipeline_id}) ==='))
        
        try:
            # 获取流水线
            pipeline = await Pipeline.objects.aget(id=pipeline_id)
            self.stdout.write(f'流水线: {pipeline.name}')
            
            # 检查原子步骤
            atomic_steps = await AtomicStep.objects.filter(
                pipeline=pipeline
            ).acount()
            
            if atomic_steps == 0:
                self.stdout.write(
                    self.style.ERROR('该流水线没有原子步骤，请先创建原子步骤')
                )
                return
            
            self.stdout.write(f'原子步骤数量: {atomic_steps}')
            
            # 获取用户
            user, _ = await User.objects.aget_or_create(
                username='admin',
                defaults={'email': 'admin@example.com'}
            )
            
            # 设置执行参数
            parameters = {
                'WORKSPACE': '/tmp/pipeline_workspace',
                'PIPELINE_NAME': pipeline.name,
                'BUILD_NUMBER': str(int(timezone.now().timestamp())),
                'GIT_COMMIT': 'test-commit-hash',
                'NODE_ENV': 'test'
            }
            
            # 启动执行
            self.stdout.write('启动流水线执行...')
            execution = await cicd_engine.execute_atomic_steps_locally(
                pipeline=pipeline,
                trigger_type='manual',
                triggered_by=user,
                parameters=parameters
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'流水线执行已启动，执行ID: {execution.id}')
            )
            self.stdout.write(f'状态: {execution.status}')
            self.stdout.write(f'触发类型: {execution.trigger_type}')
            self.stdout.write(f'参数: {parameters}')
            
            # 等待执行完成（最多等待10分钟）
            self.stdout.write('等待执行完成...')
            max_wait = 600  # 10分钟
            wait_time = 0
            
            while wait_time < max_wait:
                await asyncio.sleep(5)
                wait_time += 5
                
                # 刷新执行状态
                await execution.arefresh_from_db()
                
                self.stdout.write(f'当前状态: {execution.status} (等待时间: {wait_time}s)')
                
                if execution.status in ['success', 'failed', 'cancelled', 'timeout']:
                    break
            
            # 显示最终结果
            await execution.arefresh_from_db()
            self.stdout.write(self.style.SUCCESS('=== 执行结果 ==='))
            self.stdout.write(f'最终状态: {execution.status}')
            self.stdout.write(f'开始时间: {execution.started_at}')
            self.stdout.write(f'完成时间: {execution.completed_at}')
            
            if execution.logs:
                self.stdout.write('执行日志:')
                self.stdout.write(execution.logs)
            
            # 显示步骤执行详情
            from cicd_integrations.models import StepExecution
            step_executions = StepExecution.objects.filter(
                pipeline_execution=execution
            ).order_by('started_at')
            
            self.stdout.write('\n=== 步骤执行详情 ===')
            async for step_exec in step_executions:
                self.stdout.write(f'步骤: {step_exec.atomic_step.name}')
                self.stdout.write(f'  状态: {step_exec.status}')
                self.stdout.write(f'  开始: {step_exec.started_at}')
                self.stdout.write(f'  完成: {step_exec.completed_at}')
                if step_exec.output:
                    self.stdout.write(f'  输出: {step_exec.output[:200]}...')
                if step_exec.error_message:
                    self.stdout.write(f'  错误: {step_exec.error_message}')
                self.stdout.write('')
            
        except Pipeline.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'流水线 ID {pipeline_id} 不存在')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'执行测试失败: {str(e)}')
            )
