"""
Django 管理命令 - Jenkins Job 管理
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from project_management.models import Project
from cicd_integrations.models import CICDTool
from cicd_integrations.adapters import JenkinsAdapter, PipelineDefinition
import asyncio
import json


class Command(BaseCommand):
    """Jenkins Job 管理命令"""
    
    help = 'Manage Jenkins jobs (list, create, delete, start, stop)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--tool-id',
            type=int,
            required=True,
            help='Jenkins 工具 ID'
        )
        
        parser.add_argument(
            '--action',
            type=str,
            choices=['list', 'info', 'create', 'delete', 'enable', 'disable', 'start', 'stop', 'builds', 'logs', 'queue'],
            required=True,
            help='要执行的操作'
        )
        
        parser.add_argument(
            '--job-name',
            type=str,
            help='Job 名称 (对于 info, delete, enable, disable, start, stop, builds, logs 操作)'
        )
        
        parser.add_argument(
            '--build-number',
            type=str,
            help='构建编号 (对于 stop, logs 操作)'
        )
        
        parser.add_argument(
            '--parameters',
            type=str,
            help='构建参数 JSON 字符串 (对于 start 操作)'
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='结果限制数量 (对于 list, builds 操作)'
        )
        
        parser.add_argument(
            '--sample-job',
            action='store_true',
            help='创建示例Job (仅用于 create 操作)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'🚀 开始 Jenkins Job 管理操作: {options["action"]}')
        )
        
        try:
            # 获取Jenkins工具
            tool = self._get_jenkins_tool(options['tool_id'])
            self.stdout.write(f"使用Jenkins工具: {tool.name} ({tool.base_url})")
            
            # 创建适配器
            adapter = JenkinsAdapter(
                base_url=tool.base_url,
                username=tool.username,
                token=tool.token,
                **tool.config
            )
            
            # 执行操作
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(
                    self._execute_action(adapter, options)
                )
            finally:
                loop.close()
                
        except Exception as e:
            raise CommandError(f"操作失败: {str(e)}")
    
    def _get_jenkins_tool(self, tool_id):
        """获取Jenkins工具"""
        try:
            tool = CICDTool.objects.get(id=tool_id, tool_type='jenkins')
            return tool
        except CICDTool.DoesNotExist:
            raise CommandError(f"Jenkins 工具 ID {tool_id} 不存在")
    
    async def _execute_action(self, adapter: JenkinsAdapter, options):
        """执行具体操作"""
        action = options['action']
        
        if action == 'list':
            await self._list_jobs(adapter, options)
        elif action == 'info':
            await self._get_job_info(adapter, options)
        elif action == 'create':
            await self._create_job(adapter, options)
        elif action == 'delete':
            await self._delete_job(adapter, options)
        elif action == 'enable':
            await self._enable_job(adapter, options)
        elif action == 'disable':
            await self._disable_job(adapter, options)
        elif action == 'start':
            await self._start_build(adapter, options)
        elif action == 'stop':
            await self._stop_build(adapter, options)
        elif action == 'builds':
            await self._get_job_builds(adapter, options)
        elif action == 'logs':
            await self._get_build_logs(adapter, options)
        elif action == 'queue':
            await self._get_queue_info(adapter, options)
    
    async def _list_jobs(self, adapter: JenkinsAdapter, options):
        """列出所有Jobs"""
        self.stdout.write("\n📋 获取 Jenkins Jobs 列表...")
        
        jobs = await adapter.list_jobs()
        
        if jobs:
            self.stdout.write(f"\n找到 {len(jobs)} 个 Jobs:")
            self.stdout.write("-" * 80)
            self.stdout.write(f"{'名称':<30} {'状态':<15} {'最后构建':<20} {'可构建':<10}")
            self.stdout.write("-" * 80)
            
            for job in jobs[:options['limit']]:
                name = job['name'][:29]
                status = job['status']
                last_build = 'N/A'
                if job['last_build']:
                    last_build = f"#{job['last_build']['number']}"
                buildable = '是' if job['buildable'] else '否'
                
                # 根据状态设置颜色
                if status == 'success':
                    status_colored = self.style.SUCCESS(status)
                elif status == 'failed':
                    status_colored = self.style.ERROR(status)
                elif status == 'running':
                    status_colored = self.style.WARNING(status)
                else:
                    status_colored = status
                
                self.stdout.write(f"{name:<30} {status_colored:<15} {last_build:<20} {buildable:<10}")
        else:
            self.stdout.write(self.style.WARNING("未找到任何 Jobs"))
    
    async def _get_job_info(self, adapter: JenkinsAdapter, options):
        """获取Job详细信息"""
        job_name = options.get('job_name')
        if not job_name:
            raise CommandError("--job-name 参数是必需的")
        
        self.stdout.write(f"\n📊 获取 Job '{job_name}' 详细信息...")
        
        job_info = await adapter.get_job_info(job_name)
        
        if job_info:
            self.stdout.write(f"\n🔧 Job 基本信息:")
            self.stdout.write(f"  • 名称: {job_info.get('name')}")
            self.stdout.write(f"  • 描述: {job_info.get('description', 'N/A')}")
            self.stdout.write(f"  • 状态: {job_info.get('status')}")
            self.stdout.write(f"  • 可构建: {'是' if job_info.get('buildable') else '否'}")
            self.stdout.write(f"  • 并发构建: {'是' if job_info.get('concurrent_build') else '否'}")
            self.stdout.write(f"  • 下次构建编号: {job_info.get('next_build_number')}")
            
            # 参数信息
            parameters = job_info.get('parameters', [])
            if parameters:
                self.stdout.write(f"\n⚙️  Job 参数:")
                for param in parameters:
                    self.stdout.write(f"  • {param['name']} ({param['type']}): {param.get('description', 'N/A')}")
            
            # 最近构建
            builds = job_info.get('builds', [])
            if builds:
                self.stdout.write(f"\n🏗️  最近构建:")
                for build in builds[:5]:
                    self.stdout.write(f"  • 构建 #{build.get('number')}: {build.get('url')}")
            
            # 健康报告
            health_report = job_info.get('health_report', [])
            if health_report:
                self.stdout.write(f"\n💚 健康报告:")
                for report in health_report:
                    self.stdout.write(f"  • {report.get('description', 'N/A')}")
        else:
            self.stdout.write(self.style.WARNING(f"Job '{job_name}' 不存在或无法访问"))
    
    async def _create_job(self, adapter: JenkinsAdapter, options):
        """创建新Job"""
        if not options.get('sample_job'):
            raise CommandError("目前只支持 --sample-job 选项创建示例Job")
        
        job_name = options.get('job_name', 'ansflow-sample-job')
        
        self.stdout.write(f"\n🔨 创建示例 Job '{job_name}'...")
        
        # 创建示例流水线定义
        pipeline_def = PipelineDefinition(
            name=job_name,
            steps=[
                {
                    "type": "git_checkout",
                    "parameters": {
                        "repository_url": "https://github.com/octocat/Hello-World.git",
                        "branch": "main"
                    }
                },
                {
                    "type": "shell_script",
                    "parameters": {
                        "script": "echo 'Hello from AnsFlow!'"
                    }
                },
                {
                    "type": "shell_script",
                    "parameters": {
                        "script": "ls -la"
                    }
                }
            ],
            triggers={"webhook": True},
            environment={
                "BUILD_ENV": "sample",
                "ANSFLOW_VERSION": "1.0.0"
            }
        )
        
        # 生成Jenkinsfile配置
        job_config = await self._generate_sample_job_config(job_name, pipeline_def)
        
        # 创建Job
        success = await adapter.create_job(
            job_name=job_name,
            job_config=job_config,
            description="AnsFlow 示例 Job - 由管理命令创建"
        )
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Job '{job_name}' 创建成功!")
            )
            self.stdout.write(f"访问地址: {adapter.base_url}/job/{job_name}/")
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ Job '{job_name}' 创建失败")
            )
    
    async def _generate_sample_job_config(self, job_name: str, pipeline_def: PipelineDefinition) -> str:
        """生成示例Job的XML配置"""
        jenkinsfile = f"""
pipeline {{
    agent any
    
    environment {{
        BUILD_ENV = 'sample'
        ANSFLOW_VERSION = '1.0.0'
    }}
    
    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
                echo 'Code checked out successfully'
            }}
        }}
        
        stage('Hello AnsFlow') {{
            steps {{
                sh 'echo "Hello from AnsFlow!"'
                sh 'echo "Current directory: $(pwd)"'
                sh 'ls -la'
            }}
        }}
        
        stage('Environment Info') {{
            steps {{
                sh 'echo "Build Environment: $BUILD_ENV"'
                sh 'echo "AnsFlow Version: $ANSFLOW_VERSION"'
                sh 'echo "Jenkins Build Number: $BUILD_NUMBER"'
            }}
        }}
    }}
    
    post {{
        always {{
            echo 'Pipeline execution completed'
            cleanWs()
        }}
        success {{
            echo 'Pipeline succeeded!'
        }}
        failure {{
            echo 'Pipeline failed!'
        }}
    }}
}}"""
        
        return f"""<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.40">
  <actions/>
  <description>AnsFlow 示例 Job - 展示基本的流水线功能</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers/>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.92">
    <script>{jenkinsfile}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>"""
    
    async def _delete_job(self, adapter: JenkinsAdapter, options):
        """删除Job"""
        job_name = options.get('job_name')
        if not job_name:
            raise CommandError("--job-name 参数是必需的")
        
        self.stdout.write(f"\n🗑️  删除 Job '{job_name}'...")
        
        # 确认操作
        confirm = input(f"确定要删除 Job '{job_name}' 吗? (y/N): ")
        if confirm.lower() != 'y':
            self.stdout.write("操作已取消")
            return
        
        success = await adapter.delete_job(job_name)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Job '{job_name}' 删除成功!")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ Job '{job_name}' 删除失败")
            )
    
    async def _enable_job(self, adapter: JenkinsAdapter, options):
        """启用Job"""
        job_name = options.get('job_name')
        if not job_name:
            raise CommandError("--job-name 参数是必需的")
        
        self.stdout.write(f"\n✅ 启用 Job '{job_name}'...")
        
        success = await adapter.enable_job(job_name)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Job '{job_name}' 启用成功!")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ Job '{job_name}' 启用失败")
            )
    
    async def _disable_job(self, adapter: JenkinsAdapter, options):
        """禁用Job"""
        job_name = options.get('job_name')
        if not job_name:
            raise CommandError("--job-name 参数是必需的")
        
        self.stdout.write(f"\n❌ 禁用 Job '{job_name}'...")
        
        success = await adapter.disable_job(job_name)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Job '{job_name}' 禁用成功!")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ Job '{job_name}' 禁用失败")
            )
    
    async def _start_build(self, adapter: JenkinsAdapter, options):
        """启动构建"""
        job_name = options.get('job_name')
        if not job_name:
            raise CommandError("--job-name 参数是必需的")
        
        # 解析参数
        parameters = {}
        if options.get('parameters'):
            try:
                parameters = json.loads(options['parameters'])
            except json.JSONDecodeError:
                raise CommandError("构建参数必须是有效的 JSON 格式")
        
        self.stdout.write(f"\n🚀 启动 Job '{job_name}' 构建...")
        if parameters:
            self.stdout.write(f"构建参数: {parameters}")
        
        result = await adapter.start_build(job_name, parameters)
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(f"✅ 构建启动成功!")
            )
            if 'build_number' in result:
                self.stdout.write(f"构建编号: #{result['build_number']}")
                self.stdout.write(f"构建地址: {result['build_url']}")
            self.stdout.write(f"消息: {result['message']}")
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ 构建启动失败: {result['message']}")
            )
    
    async def _stop_build(self, adapter: JenkinsAdapter, options):
        """停止构建"""
        job_name = options.get('job_name')
        build_number = options.get('build_number')
        
        if not job_name or not build_number:
            raise CommandError("--job-name 和 --build-number 参数都是必需的")
        
        self.stdout.write(f"\n🛑 停止 Job '{job_name}' 构建 #{build_number}...")
        
        success = await adapter.stop_build(job_name, build_number)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f"✅ 构建 #{build_number} 停止成功!")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ 构建 #{build_number} 停止失败")
            )
    
    async def _get_job_builds(self, adapter: JenkinsAdapter, options):
        """获取Job构建历史"""
        job_name = options.get('job_name')
        if not job_name:
            raise CommandError("--job-name 参数是必需的")
        
        self.stdout.write(f"\n📈 获取 Job '{job_name}' 构建历史...")
        
        builds = await adapter.get_job_builds(job_name, limit=options['limit'])
        
        if builds:
            self.stdout.write(f"\n找到 {len(builds)} 个构建:")
            self.stdout.write("-" * 80)
            self.stdout.write(f"{'构建编号':<12} {'状态':<15} {'开始时间':<20} {'持续时间':<15}")
            self.stdout.write("-" * 80)
            
            for build in builds:
                number = f"#{build['number']}"
                status = build['status']
                started_at = build['started_at'][:19] if build['started_at'] else 'N/A'
                duration = f"{build['duration'] // 1000}s" if build['duration'] > 0 else 'N/A'
                
                # 根据状态设置颜色
                if status == 'success':
                    status_colored = self.style.SUCCESS(status)
                elif status == 'failed':
                    status_colored = self.style.ERROR(status)
                elif status == 'running':
                    status_colored = self.style.WARNING(status)
                else:
                    status_colored = status
                
                self.stdout.write(f"{number:<12} {status_colored:<15} {started_at:<20} {duration:<15}")
        else:
            self.stdout.write(self.style.WARNING(f"Job '{job_name}' 没有构建历史"))
    
    async def _get_build_logs(self, adapter: JenkinsAdapter, options):
        """获取构建日志"""
        job_name = options.get('job_name')
        build_number = options.get('build_number', 'lastBuild')
        
        if not job_name:
            raise CommandError("--job-name 参数是必需的")
        
        self.stdout.write(f"\n📄 获取 Job '{job_name}' 构建 #{build_number} 日志...")
        
        log_info = await adapter.get_build_console_log(job_name, build_number)
        
        if log_info['log_text']:
            self.stdout.write(f"\n🔍 构建日志 (位置: {log_info['current_position']}):")
            self.stdout.write("-" * 80)
            self.stdout.write(log_info['log_text'][:2000])  # 限制显示长度
            
            if len(log_info['log_text']) > 2000:
                self.stdout.write("\n... (日志内容被截断)")
            
            if log_info['has_more']:
                self.stdout.write(f"\n📝 还有更多日志内容 (下一位置: {log_info['next_position']})")
        else:
            self.stdout.write(self.style.WARNING("无法获取日志内容"))
    
    async def _get_queue_info(self, adapter: JenkinsAdapter, options):
        """获取构建队列信息"""
        self.stdout.write("\n⏳ 获取 Jenkins 构建队列信息...")
        
        queue_items = await adapter.get_queue_info()
        
        if queue_items:
            self.stdout.write(f"\n队列中有 {len(queue_items)} 个项目:")
            self.stdout.write("-" * 80)
            self.stdout.write(f"{'Job名称':<30} {'状态':<15} {'等待原因':<35}")
            self.stdout.write("-" * 80)
            
            for item in queue_items[:options['limit']]:
                job_name = item['job_name'][:29] if item['job_name'] else 'N/A'
                
                status = []
                if item['blocked']:
                    status.append('阻塞')
                if item['buildable']:
                    status.append('可构建')
                if item['stuck']:
                    status.append('卡住')
                status_str = ','.join(status) if status else '等待'
                
                why = item['why'][:34] if item['why'] else 'N/A'
                
                self.stdout.write(f"{job_name:<30} {status_str:<15} {why:<35}")
        else:
            self.stdout.write(self.style.SUCCESS("构建队列为空"))
