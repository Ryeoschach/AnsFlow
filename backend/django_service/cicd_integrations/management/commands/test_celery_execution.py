"""
测试Celery异步任务执行命令
"""
import time
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pipelines.models import Pipeline
from ...models import PipelineExecution
from ...tasks import execute_pipeline_task


class Command(BaseCommand):
    help = '测试Celery异步任务执行'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pipeline-id',
            type=int,
            help='指定要执行的流水线ID'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='使用异步任务执行'
        )

    def handle(self, *args, **options):
        pipeline_id = options.get('pipeline_id')
        use_async = options.get('async', False)
        
        if not pipeline_id:
            self.stdout.write(self.style.ERROR('请指定 --pipeline-id'))
            return
        
        try:
            # 获取流水线
            pipeline = Pipeline.objects.get(id=pipeline_id)
            user = User.objects.filter(is_superuser=True).first()
            
            self.stdout.write(f"=== 测试流水线执行 (ID: {pipeline_id}) ===")
            self.stdout.write(f"流水线: {pipeline.name}")
            self.stdout.write(f"执行模式: {'异步 (Celery)' if use_async else '同步'}")
            
            # 创建流水线执行记录
            execution = PipelineExecution.objects.create(
                pipeline=pipeline,
                triggered_by=user,
                trigger_type='manual',
                status='pending',
                parameters={
                    'WORKSPACE': '/tmp/pipeline_workspace',
                    'PIPELINE_NAME': pipeline.name,
                    'BUILD_NUMBER': str(int(time.time())),
                    'GIT_COMMIT': 'test-commit-hash',
                    'NODE_ENV': 'test'
                }
            )
            
            self.stdout.write(f"创建执行记录，ID: {execution.id}")
            
            if use_async:
                # 使用Celery异步执行
                self.stdout.write("启动Celery异步任务...")
                
                task_result = execute_pipeline_task.delay(
                    execution_id=execution.id,
                    pipeline_id=pipeline.id,
                    trigger_type='manual',
                    triggered_by_id=user.id,
                    parameters=execution.parameters
                )
                
                self.stdout.write(f"Celery任务ID: {task_result.id}")
                self.stdout.write("监控任务执行状态...")
                
                # 监控任务执行状态
                start_time = time.time()
                while not task_result.ready():
                    execution.refresh_from_db()
                    elapsed_time = int(time.time() - start_time)
                    self.stdout.write(f"当前状态: {execution.status} (等待时间: {elapsed_time}s)")
                    time.sleep(3)
                    
                    if elapsed_time > 120:  # 2分钟超时
                        self.stdout.write(self.style.ERROR("任务执行超时"))
                        break
                
                # 获取最终结果
                execution.refresh_from_db()
                
                if task_result.ready():
                    try:
                        result = task_result.get()
                        self.stdout.write(self.style.SUCCESS("=== Celery任务执行完成 ==="))
                        self.stdout.write(f"任务状态: {task_result.status}")
                        self.stdout.write(f"执行结果: {result}")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"获取任务结果失败: {str(e)}"))
                
            else:
                # 同步执行
                self.stdout.write("启动同步执行...")
                
                # 直接调用任务函数（同步）
                result = execute_pipeline_task(
                    execution_id=execution.id,
                    pipeline_id=pipeline.id,
                    trigger_type='manual',
                    triggered_by_id=user.id,
                    parameters=execution.parameters
                )
                
                execution.refresh_from_db()
                self.stdout.write(self.style.SUCCESS("=== 同步执行完成 ==="))
                self.stdout.write(f"执行结果: {result}")
            
            # 显示最终状态
            self.stdout.write("\n=== 最终执行状态 ===")
            self.stdout.write(f"流水线执行ID: {execution.id}")
            self.stdout.write(f"最终状态: {execution.status}")
            self.stdout.write(f"开始时间: {execution.started_at}")
            self.stdout.write(f"完成时间: {execution.completed_at}")
            
            if execution.logs:
                self.stdout.write(f"执行日志: {execution.logs}")
                
        except Pipeline.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'流水线不存在: {pipeline_id}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'执行失败: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
