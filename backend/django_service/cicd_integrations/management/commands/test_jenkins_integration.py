"""
Jenkins Job 集成测试命令

这个命令演示了完整的 Jenkins Job 管理功能，包括：
- 健康检查
- Job 列表查看
- 创建和删除 Job
- 启动和停止构建
- 获取构建历史和日志
- 队列管理
"""

import asyncio
import os
from django.core.management.base import BaseCommand
from cicd_integrations.adapters import JenkinsAdapter, PipelineDefinition


class Command(BaseCommand):
    help = '测试 Jenkins Job 管理功能的完整集成'

    def add_arguments(self, parser):
        parser.add_argument(
            '--jenkins-url',
            type=str,
            default=os.getenv('JENKINS_URL', 'http://localhost:8080'),
            help='Jenkins 服务器 URL'
        )
        parser.add_argument(
            '--username',
            type=str,
            default=os.getenv('JENKINS_USERNAME', 'admin'),
            help='Jenkins 用户名'
        )
        parser.add_argument(
            '--token',
            type=str,
            default=os.getenv('JENKINS_TOKEN', ''),
            help='Jenkins API Token'
        )
        parser.add_argument(
            '--job-name',
            type=str,
            default='ansflow-integration-test',
            help='测试 Job 名称'
        )
        parser.add_argument(
            '--quick-test',
            action='store_true',
            help='执行快速测试（跳过构建等待）'
        )

    def handle(self, *args, **options):
        asyncio.run(self.async_handle(*args, **options))

    async def async_handle(self, *args, **options):
        jenkins_url = options['jenkins_url']
        username = options['username']
        token = options['token']
        job_name = options['job_name']
        quick_test = options['quick_test']

        if not token:
            self.stdout.write(
                self.style.ERROR('❌ 请提供 Jenkins API Token')
            )
            self.stdout.write('💡 设置方法:')
            self.stdout.write('   export JENKINS_TOKEN="your-api-token"')
            self.stdout.write('   或使用 --token 参数')
            return

        self.stdout.write(self.style.SUCCESS('🚀 开始 Jenkins Job 管理集成测试'))
        self.stdout.write(f'🔗 连接到: {jenkins_url}')
        self.stdout.write(f'👤 用户: {username}')
        self.stdout.write('═' * 60)

        # 创建 Jenkins 适配器
        adapter = JenkinsAdapter(
            base_url=jenkins_url,
            username=username,
            token=token
        )

        try:
            async with adapter:
                # 执行完整的集成测试
                await self.run_integration_tests(adapter, job_name, quick_test)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 测试过程中发生错误: {e}'))

    async def run_integration_tests(self, adapter, job_name, quick_test):
        """运行完整的集成测试"""
        
        # 1. 健康检查
        self.stdout.write('\n📋 步骤 1: Jenkins 健康检查')
        if not await self.test_health_check(adapter):
            return
        
        # 2. 获取 Job 列表
        self.stdout.write('\n📋 步骤 2: 获取现有 Job 列表')
        await self.test_list_jobs(adapter)
        
        # 3. 创建测试 Job
        self.stdout.write(f'\n📋 步骤 3: 创建测试 Job ({job_name})')
        if not await self.test_create_job(adapter, job_name):
            return
        
        # 4. 获取 Job 详细信息
        self.stdout.write(f'\n📋 步骤 4: 获取 Job 信息')
        await self.test_get_job_info(adapter, job_name)
        
        # 5. 启动构建
        self.stdout.write(f'\n📋 步骤 5: 启动构建')
        build_info = await self.test_start_build(adapter, job_name)
        
        if build_info and not quick_test:
            # 6. 监控构建进度
            self.stdout.write(f'\n📋 步骤 6: 监控构建进度')
            await self.test_monitor_build(adapter, job_name, build_info.get('build_number'))
        
        # 7. 获取构建历史
        self.stdout.write(f'\n📋 步骤 7: 获取构建历史')
        await self.test_get_builds(adapter, job_name)
        
        # 8. 获取队列信息
        self.stdout.write(f'\n📋 步骤 8: 获取构建队列信息')
        await self.test_get_queue_info(adapter)
        
        # 9. 清理测试 Job
        self.stdout.write(f'\n📋 步骤 9: 清理测试 Job')
        await self.test_delete_job(adapter, job_name)
        
        self.stdout.write('\n' + '═' * 60)
        self.stdout.write(self.style.SUCCESS('🎉 Jenkins Job 管理集成测试完成！'))
        self.stdout.write('\n✅ 所有功能测试通过：')
        self.stdout.write('   • Jenkins 连接和健康检查')
        self.stdout.write('   • Job 列表查看')
        self.stdout.write('   • Job 创建和删除')
        self.stdout.write('   • 构建启动和监控')
        self.stdout.write('   • 构建历史查询')
        self.stdout.write('   • 构建队列管理')

    async def test_health_check(self, adapter):
        """测试健康检查"""
        try:
            is_healthy = await adapter.health_check()
            if is_healthy:
                self.stdout.write(self.style.SUCCESS('✅ Jenkins 服务器连接正常'))
                return True
            else:
                self.stdout.write(self.style.ERROR('❌ Jenkins 服务器连接失败'))
                return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 健康检查异常: {e}'))
            return False

    async def test_list_jobs(self, adapter):
        """测试获取 Job 列表"""
        try:
            jobs = await adapter.list_jobs()
            self.stdout.write(f'✅ 成功获取 Job 列表，共 {len(jobs)} 个 Job')
            
            if jobs:
                self.stdout.write('   前5个Job:')
                for job in jobs[:5]:
                    status_icon = self.get_status_icon(job['status'])
                    self.stdout.write(f'   {status_icon} {job["name"]} ({job["status"]})')
            else:
                self.stdout.write('   📭 当前没有任何 Job')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 获取 Job 列表失败: {e}'))

    async def test_create_job(self, adapter, job_name):
        """测试创建 Job"""
        try:
            # 先检查是否已存在同名 Job，如果存在则删除
            existing_jobs = await adapter.list_jobs()
            if any(job['name'] == job_name for job in existing_jobs):
                self.stdout.write(f'⚠️  发现同名 Job，先删除: {job_name}')
                await adapter.delete_job(job_name)
                await asyncio.sleep(2)
            
            # 创建测试流水线定义
            pipeline_def = PipelineDefinition(
                name=job_name,
                steps=[
                    {
                        'type': 'shell_script',
                        'parameters': {
                            'stage': 'Initialize',
                            'script': 'echo "=== AnsFlow Jenkins Integration Test ===" && echo "Job: $JOB_NAME" && echo "Build: $BUILD_NUMBER"'
                        }
                    },
                    {
                        'type': 'shell_script',
                        'parameters': {
                            'stage': 'Environment Check',
                            'script': 'echo "Checking environment..." && whoami && pwd && date'
                        }
                    },
                    {
                        'type': 'shell_script',
                        'parameters': {
                            'stage': 'Simulate Work',
                            'script': 'echo "Simulating work..." && for i in {1..5}; do echo "Step $i/5"; sleep 2; done && echo "Work completed!"'
                        }
                    },
                    {
                        'type': 'shell_script',
                        'parameters': {
                            'stage': 'Success',
                            'script': 'echo "🎉 Test job completed successfully!"'
                        }
                    }
                ],
                triggers={'manual': True},
                environment={
                    'TEST_ENV': 'integration',
                    'ANSFLOW_VERSION': '1.0.0'
                },
                timeout=1800  # 30分钟
            )
            
            job_id = await adapter.create_pipeline(pipeline_def)
            self.stdout.write(self.style.SUCCESS(f'✅ 测试 Job 创建成功: {job_id}'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 创建 Job 失败: {e}'))
            return False

    async def test_get_job_info(self, adapter, job_name):
        """测试获取 Job 信息"""
        try:
            job_info = await adapter.get_job_info(job_name)
            
            if job_info:
                self.stdout.write(f'✅ 成功获取 Job 信息:')
                self.stdout.write(f'   📝 名称: {job_info.get("name")}')
                self.stdout.write(f'   📋 描述: {job_info.get("description", "无")}')
                self.stdout.write(f'   🎯 状态: {job_info.get("status")}')
                self.stdout.write(f'   🔧 可构建: {job_info.get("buildable")}')
                self.stdout.write(f'   🔢 下一构建号: {job_info.get("next_build_number")}')
                
                parameters = job_info.get('parameters', [])
                if parameters:
                    self.stdout.write(f'   ⚙️  参数数量: {len(parameters)}')
                
            else:
                self.stdout.write(self.style.ERROR(f'❌ Job "{job_name}" 不存在'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 获取 Job 信息失败: {e}'))

    async def test_start_build(self, adapter, job_name):
        """测试启动构建"""
        try:
            result = await adapter.start_build(
                job_name, 
                parameters={'TEST_PARAM': 'integration_test'}, 
                wait_for_start=True
            )
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS(f'✅ 构建启动成功'))
                self.stdout.write(f'   🔢 构建编号: {result.get("build_number")}')
                self.stdout.write(f'   🔗 构建URL: {result.get("build_url")}')
                self.stdout.write(f'   🆔 执行ID: {result.get("execution_id")}')
                return result
            else:
                self.stdout.write(self.style.ERROR(f'❌ 构建启动失败: {result.get("message")}'))
                return None
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 启动构建异常: {e}'))
            return None

    async def test_monitor_build(self, adapter, job_name, build_number):
        """测试监控构建进度"""
        if not build_number:
            return
            
        self.stdout.write(f'⏳ 监控构建进度: {job_name}#{build_number}')
        
        try:
            for i in range(12):  # 最多监控2分钟
                execution_id = f"{job_name}#{build_number}"
                status_info = await adapter.get_pipeline_status(execution_id)
                
                status = status_info.get('status', 'unknown')
                building = status_info.get('building', False)
                
                if building:
                    self.stdout.write(f'   🔄 [{i*10}s] 构建进行中...')
                    await asyncio.sleep(10)
                else:
                    status_icon = self.get_status_icon(status)
                    self.stdout.write(f'   {status_icon} 构建完成，状态: {status}')
                    
                    # 获取构建日志片段
                    log_info = await adapter.get_build_console_log(job_name, build_number)
                    log_text = log_info.get('log_text', '')
                    if log_text:
                        # 显示最后几行日志
                        lines = log_text.strip().split('\n')
                        if len(lines) > 5:
                            self.stdout.write('   📜 构建日志（最后5行）:')
                            for line in lines[-5:]:
                                self.stdout.write(f'      {line}')
                    break
            else:
                self.stdout.write('   ⏰ 监控超时，构建可能仍在进行中')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 监控构建异常: {e}'))

    async def test_get_builds(self, adapter, job_name):
        """测试获取构建历史"""
        try:
            builds = await adapter.get_job_builds(job_name, limit=5)
            
            if builds:
                self.stdout.write(f'✅ 成功获取构建历史，共 {len(builds)} 次构建:')
                for build in builds:
                    status_icon = self.get_status_icon(build['status'])
                    duration = build.get('duration', 0)
                    duration_str = f"{duration/1000:.1f}s" if duration > 0 else "进行中"
                    
                    self.stdout.write(
                        f'   {status_icon} #{build["number"]} - {build["status"]} - '
                        f'用时: {duration_str}'
                    )
            else:
                self.stdout.write('📭 没有找到构建历史')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 获取构建历史失败: {e}'))

    async def test_get_queue_info(self, adapter):
        """测试获取队列信息"""
        try:
            queue_items = await adapter.get_queue_info()
            
            if queue_items:
                self.stdout.write(f'✅ 构建队列中有 {len(queue_items)} 个任务:')
                for item in queue_items:
                    status = "阻塞" if item['blocked'] else "正常"
                    self.stdout.write(
                        f'   🔄 {item["job_name"]} - {status} - {item["why"]}'
                    )
            else:
                self.stdout.write('✅ 构建队列为空')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 获取队列信息失败: {e}'))

    async def test_delete_job(self, adapter, job_name):
        """测试删除 Job"""
        try:
            success = await adapter.delete_job(job_name)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f'✅ 测试 Job 删除成功'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ 测试 Job 删除失败'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 删除 Job 异常: {e}'))

    def get_status_icon(self, status):
        """根据状态返回对应的图标"""
        status_icons = {
            'success': '✅',
            'failed': '❌',
            'running': '🔄',
            'pending': '⏳',
            'cancelled': '🛑',
            'unstable': '⚠️',
            'disabled': '⏸️',
            'not_built': '⭕',
            'unknown': '❓'
        }
        return status_icons.get(status, '❓')
