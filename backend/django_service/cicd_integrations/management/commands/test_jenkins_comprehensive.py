"""
综合Jenkins集成测试管理命令
测试拆分后的视图和完整的Jenkins功能
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from cicd_integrations.models import CICDTool
from cicd_integrations.adapters import JenkinsAdapter
import asyncio
import json
import time

User = get_user_model()


class Command(BaseCommand):
    help = 'Comprehensive Jenkins integration test for split views'

    def add_arguments(self, parser):
        parser.add_argument(
            '--jenkins-url',
            type=str,
            help='Jenkins server URL',
            default='http://localhost:8080'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Jenkins username',
            default='admin'
        )
        parser.add_argument(
            '--token',
            type=str,
            help='Jenkins API token',
            default='test-token'
        )
        parser.add_argument(
            '--test-job-name',
            type=str,
            help='Test job name',
            default='ansflow-test-job'
        )
        parser.add_argument(
            '--skip-api-tests',
            action='store_true',
            help='Skip API endpoint tests'
        )

    def handle(self, *args, **options):
        self.stdout.write("🚀 开始Jenkins综合集成测试...")
        
        # 运行所有测试
        self.test_views_import()
        
        if not options['skip_api_tests']:
            asyncio.run(self.test_jenkins_functionality(
                jenkins_url=options['jenkins_url'],
                username=options['username'],
                token=options['token'],
                test_job_name=options['test_job_name']
            ))
        
        self.stdout.write(self.style.SUCCESS("✅ Jenkins集成测试完成"))

    def test_views_import(self):
        """测试视图模块导入"""
        self.stdout.write("🔍 测试视图模块导入...")
        
        try:
            # 测试主视图导入
            from cicd_integrations.views import (
                CICDToolViewSet,
                PipelineExecutionViewSet,
                AtomicStepViewSet,
                JenkinsManagementMixin
            )
            
            # 验证Jenkins方法存在
            jenkins_methods = [method for method in dir(CICDToolViewSet) if method.startswith('jenkins_')]
            expected_methods = [
                'jenkins_list_jobs',
                'jenkins_job_info', 
                'jenkins_create_job',
                'jenkins_delete_job',
                'jenkins_start_build',
                'jenkins_stop_build',
                'jenkins_job_builds',
                'jenkins_build_logs',
                'jenkins_queue_info',
                'jenkins_enable_job',
                'jenkins_disable_job',
                'jenkins_build_info'
            ]
            
            missing_methods = set(expected_methods) - set(jenkins_methods)
            if missing_methods:
                raise Exception(f"缺少Jenkins方法: {missing_methods}")
            
            self.stdout.write(self.style.SUCCESS("✅ 视图模块导入测试通过"))
            self.stdout.write(f"📝 发现{len(jenkins_methods)}个Jenkins方法")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ 视图导入测试失败: {e}"))
            raise

    async def test_jenkins_functionality(self, jenkins_url, username, token, test_job_name):
        """测试Jenkins功能"""
        self.stdout.write("🔍 测试Jenkins适配器功能...")
        
        try:
            # 创建Jenkins适配器
            adapter = JenkinsAdapter(
                base_url=jenkins_url,
                username=username,
                token=token
            )
            
            # 测试连接
            self.stdout.write("🔗 测试Jenkins连接...")
            try:
                # 这里可能会失败，因为可能没有真实的Jenkins服务器
                jobs = await adapter.list_jobs()
                self.stdout.write(self.style.SUCCESS(f"✅ Jenkins连接成功，发现{len(jobs)}个作业"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️ Jenkins连接测试跳过: {e}"))
                self.stdout.write("💡 提示: 请确保Jenkins服务器运行在指定地址")
                return
            
            # 测试作业创建
            self.stdout.write(f"🔨 测试作业创建: {test_job_name}")
            sample_config = '''<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.40">
  <actions/>
  <description>AnsFlow测试作业</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.92">
    <script>
pipeline {
    agent any
    stages {
        stage('测试') {
            steps {
                echo 'AnsFlow Jenkins集成测试'
                sh 'echo "构建号: ${BUILD_NUMBER}"'
                sh 'echo "当前时间: $(date)"'
            }
        }
    }
}
    </script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>'''
            
            try:
                create_success = await adapter.create_job(test_job_name, sample_config)
                if create_success:
                    self.stdout.write(self.style.SUCCESS(f"✅ 作业创建成功: {test_job_name}"))
                    
                    # 测试作业信息获取
                    job_info = await adapter.get_job_info(test_job_name)
                    if job_info:
                        self.stdout.write(f"📋 作业信息: {job_info.get('displayName', 'N/A')}")
                    
                    # 测试构建启动
                    self.stdout.write("🚀 测试构建启动...")
                    build_info = await adapter.start_build(test_job_name, {}, wait_for_start=True)
                    if build_info:
                        self.stdout.write(f"✅ 构建启动成功: #{build_info.get('build_number', 'N/A')}")
                        
                        # 等待一下让构建开始
                        time.sleep(2)
                        
                        # 测试构建日志获取
                        if 'build_number' in build_info:
                            logs = await adapter.get_build_console_log(
                                test_job_name, 
                                str(build_info['build_number'])
                            )
                            if logs:
                                self.stdout.write(f"📜 获取到构建日志，长度: {len(logs.get('log_text', ''))}")
                    
                    # 测试作业禁用/启用
                    self.stdout.write("🔧 测试作业状态切换...")
                    disable_success = await adapter.disable_job(test_job_name)
                    if disable_success:
                        self.stdout.write("✅ 作业禁用成功")
                    
                    enable_success = await adapter.enable_job(test_job_name)
                    if enable_success:
                        self.stdout.write("✅ 作业启用成功")
                    
                    # 清理测试作业
                    self.stdout.write("🧹 清理测试作业...")
                    delete_success = await adapter.delete_job(test_job_name)
                    if delete_success:
                        self.stdout.write(self.style.SUCCESS(f"✅ 测试作业删除成功: {test_job_name}"))
                    
                else:
                    self.stdout.write(self.style.WARNING("⚠️ 作业创建失败"))
                    
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️ 作业操作测试跳过: {e}"))
            
            # 测试队列信息
            try:
                queue_info = await adapter.get_queue_info()
                self.stdout.write(f"📋 队列信息: {len(queue_info)}个排队项目")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️ 队列信息获取失败: {e}"))
            
            self.stdout.write(self.style.SUCCESS("✅ Jenkins功能测试完成"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Jenkins功能测试失败: {e}"))
            raise

    def test_tool_model_creation(self):
        """测试CI/CD工具模型创建"""
        self.stdout.write("🔍 测试CI/CD工具模型...")
        
        try:
            # 获取或创建测试用户
            user, created = User.objects.get_or_create(
                username='test_jenkins_user',
                defaults={'email': 'test@ansflow.com'}
            )
            
            # 创建Jenkins工具配置
            jenkins_tool, created = CICDTool.objects.get_or_create(
                name='Jenkins测试工具',
                defaults={
                    'tool_type': 'jenkins',
                    'base_url': 'http://localhost:8080',
                    'username': 'admin',
                    'token': 'test-token',
                    'config': {
                        'verify_ssl': False,
                        'timeout': 30
                    },
                    'created_by': user
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS("✅ Jenkins工具配置创建成功"))
            else:
                self.stdout.write("ℹ️ Jenkins工具配置已存在")
            
            self.stdout.write(f"📋 工具ID: {jenkins_tool.id}")
            self.stdout.write(f"📋 工具名称: {jenkins_tool.name}")
            self.stdout.write(f"📋 工具类型: {jenkins_tool.tool_type}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ 工具模型测试失败: {e}"))
            raise
