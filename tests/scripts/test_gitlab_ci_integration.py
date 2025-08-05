#!/usr/bin/env python3
# filepath: /Users/creed/workspace/sourceCode/AnsFlow/backend/django_service/test_gitlab_ci_integration.py
"""
GitLab CI 集成完整测试脚本

这个脚本演示了如何：
1. 测试 GitLab CI 连接
2. 注册 GitLab CI 工具
3. 创建和执行流水线
4. 监控执行状态
5. 获取执行日志

使用方法:
    python test_gitlab_ci_integration.py

环境变量:
    GITLAB_URL - GitLab 实例 URL (默认: https://gitlab.com)
    GITLAB_TOKEN - GitLab API Token (必需)
    GITLAB_PROJECT_ID - GitLab 项目 ID (必需)
"""

import os
import sys
import asyncio
import django
from pathlib import Path

# 设置 Django 环境
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.local')
django.setup()

from django.core.management import call_command
from cicd_integrations.models import CICDTool, AtomicStep, PipelineExecution
from cicd_integrations.services import UnifiedCICDEngine
from cicd_integrations.adapters import GitLabCIAdapter, PipelineDefinition
from datetime import datetime
import time


class GitLabCIIntegrationTest:
    """GitLab CI 集成测试类"""
    
    def __init__(self):
        self.gitlab_url = os.getenv('GITLAB_URL', 'https://gitlab.com')
        self.gitlab_token = os.getenv('GITLAB_TOKEN', '')
        self.project_id = os.getenv('GITLAB_PROJECT_ID', '')
        self.tool = None
        self.engine = UnifiedCICDEngine()
        
        # 验证必需的环境变量
        if not self.gitlab_token:
            raise ValueError("GITLAB_TOKEN environment variable is required")
        if not self.project_id:
            raise ValueError("GITLAB_PROJECT_ID environment variable is required")
    
    def print_header(self, title: str):
        """打印标题"""
        print("\n" + "=" * 70)
        print(f" {title}")
        print("=" * 70)
    
    def print_step(self, step: str):
        """打印步骤"""
        print(f"\n📋 {step}")
        print("-" * 50)
    
    def print_success(self, message: str):
        """打印成功消息"""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """打印错误消息"""
        print(f"❌ {message}")
    
    def print_warning(self, message: str):
        """打印警告消息"""
        print(f"⚠️  {message}")
    
    def print_info(self, message: str):
        """打印信息消息"""
        print(f"ℹ️  {message}")
    
    async def test_connection(self) -> bool:
        """测试 GitLab CI 连接"""
        self.print_step("测试 GitLab CI 连接")
        
        try:
            adapter = GitLabCIAdapter(
                base_url=self.gitlab_url,
                token=self.gitlab_token,
                project_id=self.project_id
            )
            
            # 健康检查
            health_ok = await adapter.health_check()
            if health_ok:
                self.print_success(f"GitLab CI 连接成功: {self.gitlab_url}")
            else:
                self.print_error("GitLab CI 连接失败")
                return False
            
            # 测试项目访问
            try:
                response = await adapter.client.get(f"{self.gitlab_url}/api/v4/projects/{self.project_id}")
                if response.status_code == 200:
                    project_data = response.json()
                    self.print_success(f"项目访问成功: {project_data.get('name', 'Unknown')}")
                    self.print_info(f"项目路径: {project_data.get('path_with_namespace', 'Unknown')}")
                else:
                    self.print_warning(f"项目访问受限: HTTP {response.status_code}")
            except Exception as e:
                self.print_error(f"项目访问失败: {e}")
                return False
            
            await adapter.client.aclose()
            return True
            
        except Exception as e:
            self.print_error(f"连接测试失败: {e}")
            return False
    
    def register_tool(self) -> bool:
        """注册 GitLab CI 工具"""
        self.print_step("注册 GitLab CI 工具")
        
        try:
            tool, created = CICDTool.objects.get_or_create(
                name=f'GitLab CI - {self.gitlab_url}',
                tool_type='gitlab_ci',
                defaults={
                    'description': f'GitLab CI instance at {self.gitlab_url}',
                    'base_url': self.gitlab_url,
                    'configuration': {
                        'token': '***hidden***',  # 不保存真实 token
                        'project_id': self.project_id,
                        'api_version': 'v4'
                    },
                    'is_active': True
                }
            )
            
            self.tool = tool
            
            if created:
                self.print_success("GitLab CI 工具注册成功")
            else:
                self.print_success("GitLab CI 工具已存在，使用现有配置")
            
            self.print_info(f"工具 ID: {tool.id}")
            self.print_info(f"工具名称: {tool.name}")
            
            return True
            
        except Exception as e:
            self.print_error(f"工具注册失败: {e}")
            return False
    
    def ensure_atomic_steps(self) -> bool:
        """确保原子步骤存在"""
        self.print_step("检查原子步骤")
        
        step_count = AtomicStep.objects.filter(visibility='public').count()
        if step_count == 0:
            self.print_warning("没有找到公共原子步骤，创建示例步骤...")
            try:
                call_command('create_atomic_steps')
                step_count = AtomicStep.objects.filter(visibility='public').count()
                self.print_success(f"创建了 {step_count} 个原子步骤")
            except Exception as e:
                self.print_error(f"创建原子步骤失败: {e}")
                return False
        else:
            self.print_success(f"找到 {step_count} 个公共原子步骤")
        
        # 显示可用步骤
        steps = AtomicStep.objects.filter(visibility='public')[:5]
        for step in steps:
            self.print_info(f"  - {step.name} ({step.step_type})")
        
        if step_count > 5:
            self.print_info(f"  ... 还有 {step_count - 5} 个步骤")
        
        return True
    
    async def test_pipeline_generation(self) -> bool:
        """测试流水线配置生成"""
        self.print_step("测试流水线配置生成")
        
        try:
            # 获取几个原子步骤
            atomic_steps = list(AtomicStep.objects.filter(visibility='public')[:3])
            
            if not atomic_steps:
                self.print_error("没有可用的原子步骤")
                return False
            
            # 准备步骤配置
            pipeline_steps = []
            for step in atomic_steps:
                step_config = {
                    'type': step.step_type,
                    'parameters': step.default_parameters.copy()
                }
                
                # 为 git_checkout 步骤添加分支参数
                if step.step_type == 'git_checkout':
                    step_config['parameters']['branch'] = 'main'
                
                pipeline_steps.append(step_config)
            
            # 创建流水线定义
            pipeline_def = PipelineDefinition(
                name='test-gitlab-pipeline',
                steps=pipeline_steps,
                triggers={'branch': 'main'},
                environment={'TEST_ENV': 'true', 'PROJECT_ID': self.project_id}
            )
            
            # 生成 GitLab CI 配置
            adapter = GitLabCIAdapter(
                base_url=self.gitlab_url,
                token=self.gitlab_token,
                project_id=self.project_id
            )
            
            gitlab_ci_yaml = await adapter.create_pipeline_file(pipeline_def)
            
            self.print_success("GitLab CI 配置生成成功")
            self.print_info("生成的 .gitlab-ci.yml 预览:")
            print()
            
            # 显示前25行配置
            lines = gitlab_ci_yaml.split('\n')[:25]
            for i, line in enumerate(lines, 1):
                print(f"    {i:2d}: {line}")
            
            if len(gitlab_ci_yaml.split('\n')) > 25:
                print(f"    ... 还有 {len(gitlab_ci_yaml.split('\n')) - 25} 行")
            
            await adapter.client.aclose()
            return True
            
        except Exception as e:
            self.print_error(f"配置生成失败: {e}")
            return False
    
    async def test_pipeline_execution(self) -> PipelineExecution:
        """测试流水线执行"""
        self.print_step("测试流水线执行")
        
        try:
            # 创建简单的测试流水线
            pipeline_steps = [
                {
                    'type': 'git_checkout',
                    'parameters': {
                        'branch': 'main',
                        'stage': 'checkout'
                    }
                },
                {
                    'type': 'shell_script',
                    'parameters': {
                        'script': 'echo "Hello from AnsFlow GitLab CI integration test!"',
                        'stage': 'build'
                    }
                },
                {
                    'type': 'test_execution',
                    'parameters': {
                        'test_command': 'echo "Running integration tests..."',
                        'stage': 'test'
                    }
                }
            ]
            
            pipeline_def = PipelineDefinition(
                name=f'ansflow-test-{int(time.time())}',
                steps=pipeline_steps,
                triggers={'branch': 'main', 'manual': True},
                environment={
                    'ANSFLOW_TEST': 'true',
                    'PROJECT_ID': self.project_id,
                    'TEST_TIMESTAMP': str(int(time.time()))
                }
            )
            
            # 更新工具配置
            tool_config = self.tool.configuration.copy()
            tool_config.update({
                'token': self.gitlab_token,
                'project_id': self.project_id
            })
            
            # 执行流水线
            execution = await self.engine.execute_pipeline(
                tool_id=self.tool.id,
                pipeline_definition=pipeline_def,
                project_path=self.project_id,
                tool_config=tool_config
            )
            
            if execution:
                self.print_success("流水线执行成功提交")
                self.print_info(f"执行 ID: {execution.id}")
                self.print_info(f"外部 ID: {execution.external_id}")
                if execution.external_url:
                    self.print_info(f"GitLab URL: {execution.external_url}")
                
                return execution
            else:
                self.print_error("流水线执行提交失败")
                return None
                
        except Exception as e:
            self.print_error(f"流水线执行失败: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    async def monitor_execution(self, execution: PipelineExecution, max_wait: int = 180):
        """监控流水线执行"""
        self.print_step(f"监控流水线执行 (最多等待 {max_wait} 秒)")
        
        check_interval = 10
        elapsed_time = 0
        last_status = None
        
        while elapsed_time < max_wait:
            try:
                # 更新执行状态
                await self.engine.update_execution_status(execution.id)
                execution.refresh_from_db()
                
                if execution.status != last_status:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.print_info(f"[{timestamp}] 状态: {execution.status}")
                    last_status = execution.status
                
                # 检查是否完成
                if execution.status in ['success', 'failed', 'cancelled']:
                    break
                
                await asyncio.sleep(check_interval)
                elapsed_time += check_interval
                
            except Exception as e:
                self.print_error(f"监控出错: {e}")
                break
        
        # 获取最终状态和日志
        final_status = execution.status
        
        if final_status == 'success':
            self.print_success("流水线执行成功！")
        elif final_status == 'failed':
            self.print_error("流水线执行失败！")
        elif final_status in ['cancelled']:
            self.print_warning(f"流水线已{final_status}")
        elif elapsed_time >= max_wait:
            self.print_warning("监控超时，流水线可能仍在执行")
        
        # 获取执行日志
        try:
            logs = await self.engine.get_execution_logs(execution.id)
            if logs:
                self.print_info("执行日志 (最后15行):")
                print()
                log_lines = logs.split('\n')
                display_lines = log_lines[-15:] if len(log_lines) > 15 else log_lines
                for line in display_lines:
                    if line.strip():
                        print(f"    {line}")
                print()
        except Exception as e:
            self.print_warning(f"获取日志失败: {e}")
        
        return final_status
    
    def generate_report(self, results: dict):
        """生成测试报告"""
        self.print_header("GitLab CI 集成测试报告")
        
        print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 GitLab URL: {self.gitlab_url}")
        print(f"📂 项目 ID: {self.project_id}")
        
        if self.tool:
            print(f"🔧 工具 ID: {self.tool.id}")
        
        print("\n📊 测试结果:")
        print("-" * 30)
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name:<25} {status}")
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n📈 总体结果: {passed_tests}/{total_tests} 通过 ({success_rate:.1f}%)")
        
        if success_rate == 100:
            self.print_success("所有测试通过！GitLab CI 集成工作正常。")
        elif success_rate >= 75:
            self.print_warning("大部分测试通过，但存在一些问题需要关注。")
        else:
            self.print_error("多项测试失败，请检查配置和权限设置。")
    
    async def run_full_test(self):
        """运行完整的集成测试"""
        self.print_header("GitLab CI 集成完整测试")
        
        print(f"🚀 开始测试 GitLab CI 集成...")
        print(f"🔗 GitLab URL: {self.gitlab_url}")
        print(f"📂 项目 ID: {self.project_id}")
        
        results = {}
        
        try:
            # 1. 连接测试
            results['连接测试'] = await self.test_connection()
            
            # 2. 工具注册
            results['工具注册'] = self.register_tool()
            
            # 3. 原子步骤检查
            results['原子步骤检查'] = self.ensure_atomic_steps()
            
            # 4. 配置生成测试
            results['配置生成'] = await self.test_pipeline_generation()
            
            # 5. 流水线执行测试
            execution = None
            if all(results.values()):
                execution = await self.test_pipeline_execution()
                results['流水线执行'] = execution is not None
                
                # 6. 执行监控
                if execution:
                    final_status = await self.monitor_execution(execution)
                    results['执行监控'] = final_status in ['success', 'failed', 'cancelled']
                else:
                    results['执行监控'] = False
            else:
                results['流水线执行'] = False
                results['执行监控'] = False
            
            # 生成报告
            self.generate_report(results)
            
        except KeyboardInterrupt:
            self.print_warning("测试被用户中断")
        except Exception as e:
            self.print_error(f"测试过程出现异常: {e}")
            import traceback
            print(traceback.format_exc())


async def main():
    """主函数"""
    print("🔧 GitLab CI 集成测试工具")
    print("=" * 50)
    
    # 检查环境变量
    gitlab_token = os.getenv('GITLAB_TOKEN')
    project_id = os.getenv('GITLAB_PROJECT_ID')
    
    if not gitlab_token:
        print("❌ 错误: 需要设置 GITLAB_TOKEN 环境变量")
        print("   export GITLAB_TOKEN=your_gitlab_token")
        return
    
    if not project_id:
        print("❌ 错误: 需要设置 GITLAB_PROJECT_ID 环境变量")
        print("   export GITLAB_PROJECT_ID=your_project_id")
        return
    
    try:
        tester = GitLabCIIntegrationTest()
        await tester.run_full_test()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == '__main__':
    # 运行测试
    asyncio.run(main())
