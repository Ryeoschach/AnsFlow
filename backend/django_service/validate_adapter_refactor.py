#!/usr/bin/env python3
"""
CI/CD 适配器重构验证脚本

这个脚本验证新的模块化适配器结构是否正常工作。
"""

import sys
import os

# 添加项目路径到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """测试导入是否正常工作"""
    print("🔍 测试适配器模块导入...")
    
    try:
        # 测试基础类导入
        from cicd_integrations.adapters.base import CICDAdapter, PipelineDefinition, ExecutionResult
        print("✅ 基础类导入成功")
        
        # 测试具体适配器导入
        from cicd_integrations.adapters.jenkins import JenkinsAdapter
        from cicd_integrations.adapters.gitlab_ci import GitLabCIAdapter
        from cicd_integrations.adapters.github_actions import GitHubActionsAdapter
        print("✅ 具体适配器导入成功")
        
        # 测试工厂导入
        from cicd_integrations.adapters.factory import AdapterFactory
        print("✅ 工厂类导入成功")
        
        # 测试统一导入（通过 __init__.py）
        from cicd_integrations.adapters import (
            CICDAdapter, PipelineDefinition, ExecutionResult,
            JenkinsAdapter, GitLabCIAdapter, GitHubActionsAdapter,
            AdapterFactory
        )
        print("✅ 统一导入成功")
        
        # 测试向后兼容性导入
        from cicd_integrations.adapters import CICDAdapterFactory
        print("✅ 向后兼容性导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_factory():
    """测试工厂功能"""
    print("\n🏭 测试适配器工厂...")
    
    try:
        from cicd_integrations.adapters import AdapterFactory
        
        # 测试支持的平台列表
        platforms = AdapterFactory.get_supported_platforms()
        print(f"✅ 支持的平台: {platforms}")
        
        # 测试平台支持检查
        assert AdapterFactory.is_platform_supported('jenkins')
        assert AdapterFactory.is_platform_supported('gitlab')
        assert AdapterFactory.is_platform_supported('github')
        assert not AdapterFactory.is_platform_supported('unknown')
        print("✅ 平台支持检查正常")
        
        # 测试适配器创建（不实际连接）
        jenkins_adapter = AdapterFactory.create_adapter(
            'jenkins',
            base_url='http://jenkins.example.com',
            username='test',
            token='test-token'
        )
        print(f"✅ Jenkins 适配器创建成功: {type(jenkins_adapter).__name__}")
        
        gitlab_adapter = AdapterFactory.create_adapter(
            'gitlab',
            base_url='https://gitlab.example.com',
            token='test-token',
            project_id='123'
        )
        print(f"✅ GitLab 适配器创建成功: {type(gitlab_adapter).__name__}")
        
        github_adapter = AdapterFactory.create_adapter(
            'github',
            base_url='https://api.github.com',
            token='test-token',
            owner='test-owner',
            repo='test-repo'
        )
        print(f"✅ GitHub 适配器创建成功: {type(github_adapter).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ 工厂测试失败: {e}")
        return False

def test_data_structures():
    """测试数据结构"""
    print("\n📊 测试数据结构...")
    
    try:
        from cicd_integrations.adapters import PipelineDefinition, ExecutionResult
        
        # 测试流水线定义
        pipeline_def = PipelineDefinition(
            name="test-pipeline",
            steps=[
                {
                    "type": "git_checkout",
                    "parameters": {"repository": "https://github.com/test/repo.git"}
                }
            ],
            triggers={"push": {"branches": ["main"]}},
            environment={"NODE_ENV": "production"}
        )
        print(f"✅ PipelineDefinition 创建成功: {pipeline_def.name}")
        
        # 测试执行结果
        result = ExecutionResult(
            success=True,
            external_id="12345",
            message="Pipeline started successfully"
        )
        print(f"✅ ExecutionResult 创建成功: {result.success}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据结构测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始 CI/CD 适配器重构验证\n")
    
    success = True
    
    # 运行所有测试
    if not test_imports():
        success = False
    
    if not test_factory():
        success = False
    
    if not test_data_structures():
        success = False
    
    # 输出结果
    print("\n" + "="*50)
    if success:
        print("🎉 所有测试通过！CI/CD 适配器重构成功。")
        print("\n📝 重构总结:")
        print("• ✅ 基础类和数据结构模块化")
        print("• ✅ 平台适配器分离到独立文件")
        print("• ✅ 工厂模式实现")
        print("• ✅ 向后兼容性保持")
        print("• ✅ 统一导入接口")
        return 0
    else:
        print("❌ 有测试失败！请检查重构代码。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
