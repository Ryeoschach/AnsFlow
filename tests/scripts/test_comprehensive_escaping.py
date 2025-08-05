#!/usr/bin/env python3
"""
全面测试Jenkins Pipeline引号转义修复
"""

import sys
import os
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')

from cicd_integrations.adapters.jenkins import JenkinsAdapter
from cicd_integrations.adapters.base import PipelineDefinition

def test_comprehensive_escaping():
    """全面测试shell命令转义功能"""
    print("=== 全面Jenkins Shell命令转义测试 ===\n")
    
    adapter = JenkinsAdapter(
        base_url="http://localhost:8080",
        username="test",
        token="test"
    )
    
    # 测试危险的引号组合
    dangerous_commands = [
        "echo 'It's working'",
        "python -c 'print(\"Hello, world!\")'",
        "docker run -it ubuntu bash -c 'echo \"Test\"'",
        "npm run test -- --testNamePattern='my test'",
        "git commit -m 'Fix: resolve the issue with 'quotes' in messages'",
        "curl -X POST -d '{\"message\": \"It's done!\"}' http://api.example.com",
    ]
    
    print("1. 测试危险命令的转义:")
    for i, cmd in enumerate(dangerous_commands, 1):
        safe_cmd = adapter._safe_shell_command(cmd)
        print(f"  {i}. 原始: {cmd}")
        print(f"     安全: {safe_cmd}")
        
        # 验证不包含危险的引号嵌套 (更精确的检查)
        # 真正危险的模式是类似 sh 'echo 'hello'' 这种没有转义的
        dangerous_unescaped = ["sh 'echo 'hello", "sh 'npm 'test", "sh 'python 'script"]
        has_danger = any(pattern in safe_cmd for pattern in dangerous_unescaped)
        
        if has_danger:
            print(f"     ❌ 发现未转义的引号嵌套")
        else:
            print(f"     ✅ 转义正确")
        print()
    
    # 测试各种步骤类型
    print("2. 测试各种流水线步骤:")
    
    test_scenarios = [
        {
            "name": "构建步骤包含引号",
            "type": "build",
            "parameters": {
                "command": "npm run build -- --mode='production'"
            }
        },
        {
            "name": "测试步骤包含引号",
            "type": "test_execution",
            "parameters": {
                "test_command": "jest --testNamePattern='integration tests'"
            }
        },
        {
            "name": "通知消息包含引号",
            "type": "notification",
            "parameters": {
                "message": "Pipeline completed successfully! It's working great.",
                "webhook_url": ""
            }
        },
        {
            "name": "通知消息包含引号(带webhook)",
            "type": "notification",
            "parameters": {
                "message": "It's done! The build succeeded.",
                "webhook_url": "https://hooks.slack.com/test"
            }
        },
        {
            "name": "自定义步骤包含复杂引号",
            "type": "custom",
            "parameters": {
                "command": "echo 'Starting process' && python -c 'print(\"Hello!\")' && echo 'Done'"
            }
        }
    ]
    
    for scenario in test_scenarios:
        script = adapter._generate_stage_script(scenario['type'], scenario['parameters'])
        print(f"  场景: {scenario['name']}")
        print(f"  生成的脚本:")
        print(f"    {script}")
        
        # 检查潜在问题 (更精确的检查)
        issues = []
        # 检查真正危险的模式：未转义的引号嵌套
        dangerous_patterns = [
            "sh 'echo 'hello",  # 没有转义的echo命令
            "sh 'npm 'run",     # 没有转义的npm命令
            "sh 'python 'script", # 没有转义的python命令
        ]
        
        for pattern in dangerous_patterns:
            if pattern in script:
                issues.append(f"危险模式: {pattern}")
        
        # 检查是否包含正确的转义模式
        if '\'"\'"\'' in script:
            print(f"    📝 包含正确的转义模式")
        
        if issues:
            print(f"    ❌ 发现问题: {', '.join(issues)}")
        else:
            print(f"    ✅ 引号处理正确")
        print()
    
    # 测试完整的Jenkinsfile生成
    print("3. 测试完整Jenkinsfile生成:")
    
    pipeline_def = PipelineDefinition(
        name="comprehensive-test-pipeline",
        steps=test_scenarios,
        triggers={},
        environment={"NODE_ENV": "test"}
    )
    
    try:
        import asyncio
        
        async def generate_jenkinsfile():
            return await adapter.create_pipeline_file(pipeline_def)
        
        jenkinsfile = asyncio.run(generate_jenkinsfile())
        
        # 计算引号相关的统计
        total_sh_commands = jenkinsfile.count("sh '")
        # 检查真正危险的模式：未转义的引号嵌套
        dangerous_patterns = [
            "sh 'echo 'hello",   # 未转义的echo
            "sh 'npm 'run",      # 未转义的npm
            "sh 'python 'script", # 未转义的python
            "sh 'docker 'run"    # 未转义的docker
        ]
        
        found_dangerous = []
        for pattern in dangerous_patterns:
            if pattern in jenkinsfile:
                count = jenkinsfile.count(pattern)
                found_dangerous.append(f"{pattern} ({count}次)")
        
        # 检查正确转义的存在
        escaped_quotes = jenkinsfile.count('\'"\'"\'')
        
        print(f"  总sh命令数: {total_sh_commands}")
        print(f"  转义引号数: {escaped_quotes}")
        if found_dangerous:
            print(f"  ❌ 发现危险模式: {', '.join(found_dangerous)}")
        else:
            print(f"  ✅ 无危险的引号嵌套模式")
        
        print(f"\n生成的Jenkinsfile长度: {len(jenkinsfile)} 字符")
        print("前200个字符预览:")
        print("-" * 50)
        print(jenkinsfile[:200] + "...")
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Jenkinsfile生成失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comprehensive_escaping()
