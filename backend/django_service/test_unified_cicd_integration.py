#!/usr/bin/env python3
# filepath: /Users/creed/workspace/sourceCode/AnsFlow/backend/django_service/test_unified_cicd_integration.py
"""
统一 CI/CD 集成测试脚本

这个脚本测试整个 AnsFlow CI/CD 集成系统，包括：
1. 多个 CI/CD 工具适配器（Jenkins、GitLab CI、GitHub Actions）
2. 统一 CI/CD 引擎
3. 原子步骤系统
4. 流水线执行和监控

使用方法:
    python test_unified_cicd_integration.py --tools jenkins gitlab github
    
环境变量:
    # Jenkins
    JENKINS_URL, JENKINS_USERNAME, JENKINS_TOKEN
    
    # GitLab CI
    GITLAB_URL, GITLAB_TOKEN, GITLAB_PROJECT_ID
    
    # GitHub Actions
    GITHUB_URL, GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO
"""

import os
import sys
import asyncio
import django
from pathlib import Path
from typing import Dict, List, Any
import argparse
from datetime import datetime

# 设置 Django 环境
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.local')
django.setup()

from django.core.management import call_command
from cicd_integrations.models import CICDTool, AtomicStep, PipelineExecution
from cicd_integrations.services import UnifiedCICDEngine
from cicd_integrations.adapters import (
    CICDAdapterFactory, 
    JenkinsAdapter, 
    GitLabCIAdapter, 
    GitHubActionsAdapter,
    PipelineDefinition
)


class UnifiedCICDIntegrationTest:
    """统一 CI/CD 集成测试类"""
    
    def __init__(self, tools_to_test: List[str] = None):
        self.tools_to_test = tools_to_test or ['jenkins', 'gitlab_ci', 'github_actions']
        self.engine = UnifiedCICDEngine()
        self.registered_tools = {}
        self.test_results = {}
        
        # 工具配置
        self.tool_configs = {
            'jenkins': {
                'base_url': os.getenv('JENKINS_URL', 'http://localhost:8080'),
                'username': os.getenv('JENKINS_USERNAME', 'admin'),
                'token': os.getenv('JENKINS_TOKEN', ''),
            },
            'gitlab_ci': {
                'base_url': os.getenv('GITLAB_URL', 'https://gitlab.com'),
                'token': os.getenv('GITLAB_TOKEN', ''),
                'project_id': os.getenv('GITLAB_PROJECT_ID', ''),
            },
            'github_actions': {
                'base_url': os.getenv('GITHUB_URL', 'https://api.github.com'),
                'token': os.getenv('GITHUB_TOKEN', ''),
                'owner': os.getenv('GITHUB_OWNER', ''),
                'repo': os.getenv('GITHUB_REPO', ''),
            }
        }
    
    def print_header(self, title: str):
        """打印标题"""
        print("\n" + "=" * 80)
        print(f" {title}")
        print("=" * 80)
    
    def print_section(self, section: str):
        """打印章节"""
        print(f"\n🔸 {section}")
        print("-" * 60)
    
    def print_step(self, step: str):
        """打印步骤"""
        print(f"\n📋 {step}")
    
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
    
    async def test_tool_connection(self, tool_type: str) -> bool:
        """测试单个工具的连接"""
        self.print_step(f"测试 {tool_type} 连接")
        
        config = self.tool_configs.get(tool_type, {})
        
        # 检查必需的配置
        required_fields = {
            'jenkins': ['base_url', 'username', 'token'],
            'gitlab_ci': ['base_url', 'token', 'project_id'],
            'github_actions': ['base_url', 'token', 'owner', 'repo']
        }
        
        missing_fields = []
        for field in required_fields.get(tool_type, []):
            if not config.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            self.print_error(f"缺少必需配置: {', '.join(missing_fields)}")
            return False
        
        try:
            # 创建适配器
            adapter = CICDAdapterFactory.create_adapter(tool_type, **config)
            
            # 健康检查
            health_ok = await adapter.health_check()
            if health_ok:
                self.print_success(f"{tool_type} 连接成功")
                
                # 注册工具到数据库
                tool = await self._register_tool(tool_type, config)
                if tool:
                    self.registered_tools[tool_type] = tool
                    return True
            else:
                self.print_error(f"{tool_type} 连接失败")
                return False
                
        except Exception as e:
            self.print_error(f"{tool_type} 测试失败: {e}")
            return False
    
    async def _register_tool(self, tool_type: str, config: dict) -> CICDTool:
        """注册工具到数据库"""
        try:
            tool_names = {
                'jenkins': f'Jenkins - {config["base_url"]}',
                'gitlab_ci': f'GitLab CI - {config["base_url"]}',
                'github_actions': f'GitHub Actions - {config.get("owner", "")}/{config.get("repo", "")}'
            }
            
            # 准备安全的配置（不保存敏感信息）
            safe_config = config.copy()
            if 'token' in safe_config:
                safe_config['token'] = '***hidden***'
            if 'username' in safe_config and 'password' in safe_config:
                safe_config['password'] = '***hidden***'
            
            tool, created = CICDTool.objects.get_or_create(
                name=tool_names.get(tool_type, f'{tool_type} tool'),
                tool_type=tool_type,
                defaults={
                    'description': f'{tool_type} integration for AnsFlow',
                    'base_url': config.get('base_url', ''),
                    'configuration': safe_config,
                    'is_active': True
                }
            )
            
            action = "注册" if created else "更新"
            self.print_info(f"工具{action}成功: {tool.name} (ID: {tool.id})")
            return tool
            
        except Exception as e:
            self.print_error(f"工具注册失败: {e}")
            return None
    
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
        
        return True
    
    async def test_pipeline_generation(self, tool_type: str) -> bool:
        """测试流水线配置生成"""
        self.print_step(f"测试 {tool_type} 流水线配置生成")
        
        try:
            # 获取原子步骤
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
                pipeline_steps.append(step_config)
            
            # 创建流水线定义
            pipeline_def = PipelineDefinition(
                name=f'test-{tool_type}-pipeline',
                steps=pipeline_steps,
                triggers={'branch': 'main'},
                environment={'TEST_ENV': 'true', 'TOOL_TYPE': tool_type}
            )
            
            # 生成配置
            config = self.tool_configs[tool_type]
            adapter = CICDAdapterFactory.create_adapter(tool_type, **config)
            
            pipeline_config = await adapter.create_pipeline_file(pipeline_def)
            
            self.print_success(f"{tool_type} 配置生成成功")
            self.print_info(f"配置长度: {len(pipeline_config)} 字符")
            
            # 显示配置预览
            lines = pipeline_config.split('\n')[:10]
            for line in lines:
                print(f"    {line}")
            if len(pipeline_config.split('\n')) > 10:
                print(f"    ... (还有 {len(pipeline_config.split('\n')) - 10} 行)")
            
            await adapter.client.aclose()
            return True
            
        except Exception as e:
            self.print_error(f"{tool_type} 配置生成失败: {e}")
            return False
    
    async def test_unified_engine(self) -> bool:
        """测试统一 CI/CD 引擎"""
        self.print_step("测试统一 CI/CD 引擎")
        
        try:
            # 测试工具注册
            engine_tools = self.engine.list_registered_tools()
            self.print_info(f"引擎中注册的工具数量: {len(engine_tools)}")
            
            # 测试健康检查
            for tool_id, tool in self.registered_tools.items():
                health_result = await self.engine.check_tool_health(tool.id)
                status = "健康" if health_result else "不可用"
                self.print_info(f"  {tool.name}: {status}")
            
            self.print_success("统一引擎测试通过")
            return True
            
        except Exception as e:
            self.print_error(f"统一引擎测试失败: {e}")
            return False
    
    async def test_pipeline_execution(self, tool_type: str) -> bool:
        """测试流水线执行"""
        self.print_step(f"测试 {tool_type} 流水线执行")
        
        if tool_type not in self.registered_tools:
            self.print_error(f"{tool_type} 工具未注册")
            return False
        
        try:
            tool = self.registered_tools[tool_type]
            
            # 创建简单的测试流水线
            pipeline_steps = [
                {
                    'type': 'shell_script',
                    'parameters': {
                        'script': f'echo "Hello from {tool_type} via AnsFlow!"',
                        'stage': 'test'
                    }
                }
            ]
            
            pipeline_def = PipelineDefinition(
                name=f'ansflow-{tool_type}-test',
                steps=pipeline_steps,
                triggers={'manual': True},
                environment={'ANSFLOW_TEST': 'true', 'TOOL': tool_type}
            )
            
            # 准备工具配置（包含敏感信息）
            tool_config = self.tool_configs[tool_type].copy()
            
            # 执行流水线
            execution = await self.engine.execute_pipeline(
                tool_id=tool.id,
                pipeline_definition=pipeline_def,
                project_path="test-project",
                tool_config=tool_config
            )
            
            if execution:
                self.print_success(f"{tool_type} 流水线执行成功提交")
                self.print_info(f"执行 ID: {execution.id}")
                self.print_info(f"外部 ID: {execution.external_id}")
                
                # 简单的状态检查
                await asyncio.sleep(5)  # 等待5秒
                await self.engine.update_execution_status(execution.id)
                execution.refresh_from_db()
                self.print_info(f"当前状态: {execution.status}")
                
                return True
            else:
                self.print_error(f"{tool_type} 流水线执行失败")
                return False
                
        except Exception as e:
            self.print_error(f"{tool_type} 流水线执行测试失败: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """运行综合测试"""
        self.print_header("AnsFlow 统一 CI/CD 集成综合测试")
        
        print(f"🚀 开始综合测试...")
        print(f"📋 待测试工具: {', '.join(self.tools_to_test)}")
        print(f"🕐 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 预检查
        self.print_section("1. 预检查")
        
        # 检查原子步骤
        atomic_steps_ok = self.ensure_atomic_steps()
        self.test_results['原子步骤检查'] = atomic_steps_ok
        
        # 检查支持的工具
        supported_tools = CICDAdapterFactory.get_supported_tools()
        self.print_info(f"支持的 CI/CD 工具: {', '.join(supported_tools)}")
        
        # 2. 连接测试
        self.print_section("2. CI/CD 工具连接测试")
        
        connection_results = {}
        for tool_type in self.tools_to_test:
            if tool_type in supported_tools:
                result = await self.test_tool_connection(tool_type)
                connection_results[tool_type] = result
                self.test_results[f'{tool_type}_连接'] = result
            else:
                self.print_warning(f"不支持的工具类型: {tool_type}")
                connection_results[tool_type] = False
                self.test_results[f'{tool_type}_连接'] = False
        
        # 3. 配置生成测试
        self.print_section("3. 流水线配置生成测试")
        
        for tool_type in self.tools_to_test:
            if connection_results.get(tool_type):
                result = await self.test_pipeline_generation(tool_type)
                self.test_results[f'{tool_type}_配置生成'] = result
            else:
                self.print_warning(f"跳过 {tool_type} 配置生成测试（连接失败）")
                self.test_results[f'{tool_type}_配置生成'] = False
        
        # 4. 统一引擎测试
        self.print_section("4. 统一 CI/CD 引擎测试")
        
        engine_result = await self.test_unified_engine()
        self.test_results['统一引擎'] = engine_result
        
        # 5. 流水线执行测试
        self.print_section("5. 流水线执行测试")
        
        for tool_type in self.tools_to_test:
            if connection_results.get(tool_type):
                result = await self.test_pipeline_execution(tool_type)
                self.test_results[f'{tool_type}_执行'] = result
            else:
                self.print_warning(f"跳过 {tool_type} 执行测试（连接失败）")
                self.test_results[f'{tool_type}_执行'] = False
        
        # 6. 生成报告
        self.generate_final_report()
    
    def generate_final_report(self):
        """生成最终测试报告"""
        self.print_header("测试报告")
        
        print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 测试工具: {', '.join(self.tools_to_test)}")
        print(f"📊 注册工具数: {len(self.registered_tools)}")
        
        # 按类别显示结果
        categories = {
            '基础功能': ['原子步骤检查', '统一引擎'],
            '工具连接': [f'{tool}_连接' for tool in self.tools_to_test],
            '配置生成': [f'{tool}_配置生成' for tool in self.tools_to_test],
            '流水线执行': [f'{tool}_执行' for tool in self.tools_to_test]
        }
        
        print(f"\n📈 详细结果:")
        print("-" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in categories.items():
            print(f"\n{category}:")
            for test in tests:
                if test in self.test_results:
                    result = self.test_results[test]
                    status = "✅ 通过" if result else "❌ 失败"
                    print(f"  {test:<25} {status}")
                    total_tests += 1
                    if result:
                        passed_tests += 1
        
        # 计算成功率
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n📊 总体结果:")
        print(f"  总测试数: {total_tests}")
        print(f"  通过数量: {passed_tests}")
        print(f"  成功率: {success_rate:.1f}%")
        
        # 工具状态总结
        print(f"\n🔧 工具状态总结:")
        for tool_type in self.tools_to_test:
            connection = self.test_results.get(f'{tool_type}_连接', False)
            config_gen = self.test_results.get(f'{tool_type}_配置生成', False)
            execution = self.test_results.get(f'{tool_type}_执行', False)
            
            if connection and config_gen and execution:
                status = "🟢 完全可用"
            elif connection and config_gen:
                status = "🟡 部分可用"
            elif connection:
                status = "🟠 仅连接"
            else:
                status = "🔴 不可用"
            
            print(f"  {tool_type:<15} {status}")
        
        # 最终评估
        print(f"\n🎯 最终评估:")
        if success_rate >= 90:
            self.print_success("优秀！CI/CD 集成系统工作完美。")
        elif success_rate >= 75:
            self.print_success("良好！大部分功能正常，系统基本可用。")
        elif success_rate >= 50:
            self.print_warning("一般。系统部分可用，需要解决一些问题。")
        else:
            self.print_error("较差。系统存在较多问题，需要重点修复。")
        
        # 建议
        print(f"\n💡 建议:")
        failed_tools = []
        for tool_type in self.tools_to_test:
            if not self.test_results.get(f'{tool_type}_连接', False):
                failed_tools.append(tool_type)
        
        if failed_tools:
            print(f"  - 检查以下工具的配置和权限: {', '.join(failed_tools)}")
        
        if not self.test_results.get('原子步骤检查', False):
            print(f"  - 确保原子步骤已正确创建")
        
        if len(self.registered_tools) == 0:
            print(f"  - 至少需要注册一个可用的 CI/CD 工具")
        
        print(f"\n🏁 测试完成！")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AnsFlow 统一 CI/CD 集成测试')
    parser.add_argument(
        '--tools',
        nargs='+',
        choices=['jenkins', 'gitlab_ci', 'github_actions'],
        default=['jenkins', 'gitlab_ci', 'github_actions'],
        help='要测试的 CI/CD 工具'
    )
    
    args = parser.parse_args()
    
    print("🔧 AnsFlow 统一 CI/CD 集成测试工具")
    print("=" * 60)
    
    try:
        tester = UnifiedCICDIntegrationTest(args.tools)
        asyncio.run(tester.run_comprehensive_test())
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == '__main__':
    main()
