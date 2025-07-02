#!/usr/bin/env python3
"""
测试Jenkins Pipeline中shell命令转义的修复
"""

import sys
import os
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')

from cicd_integrations.adapters.jenkins import JenkinsAdapter
from cicd_integrations.adapters.base import PipelineDefinition

def test_shell_command_escaping():
    """测试shell命令转义功能"""
    print("=== 测试Jenkins Shell命令转义 ===\n")
    
    # 创建Jenkins适配器实例
    adapter = JenkinsAdapter(
        base_url="http://localhost:8080",
        username="test",
        token="test"
    )
    
    # 测试单引号转义
    test_cases = [
        "echo 'hello world'",
        "echo 'It's a test'",
        "echo 'Multiple \"quotes\" and 'nested' quotes'",
        "python -c 'print(\"Hello, world!\")'",
        "docker run -it ubuntu:latest bash -c 'echo \"Test command\"'"
    ]
    
    print("1. 测试单引号转义:")
    for i, cmd in enumerate(test_cases, 1):
        escaped = adapter._escape_shell_command(cmd)
        safe_cmd = adapter._safe_shell_command(cmd)
        print(f"  测试 {i}:")
        print(f"    原始命令: {cmd}")
        print(f"    转义后:   {escaped}")
        print(f"    安全包装: {safe_cmd}")
        print()
    
    # 测试流水线步骤生成
    print("2. 测试流水线步骤生成:")
    
    test_steps = [
        {
            "name": "测试构建",
            "type": "build",
            "parameters": {
                "command": "echo 'Building project with special chars'"
            }
        },
        {
            "name": "测试部署",
            "type": "test_execution",
            "parameters": {
                "test_command": "npm test -- --coverage --watchAll=false"
            }
        },
        {
            "name": "Docker构建",
            "type": "docker_build",
            "parameters": {
                "dockerfile": "Dockerfile",
                "tag": "my-app:latest",
                "context": "."
            }
        },
        {
            "name": "通知",
            "type": "notification",
            "parameters": {
                "message": "Pipeline completed successfully!",
                "webhook_url": "https://hooks.slack.com/services/test"
            }
        }
    ]
    
    for step in test_steps:
        script = adapter._generate_stage_script(step['type'], step['parameters'])
        print(f"  步骤: {step['name']}")
        print(f"  类型: {step['type']}")
        print(f"  生成脚本:")
        print(f"    {script}")
        print()
    
    # 测试完整Jenkinsfile生成
    print("3. 测试完整Jenkinsfile生成:")
    
    pipeline_def = PipelineDefinition(
        name="test-pipeline",
        steps=test_steps,
        triggers={},
        environment={"NODE_ENV": "test"}
    )
    
    try:
        import asyncio
        
        async def test_pipeline():
            jenkinsfile = await adapter.create_pipeline_file(pipeline_def)
            return jenkinsfile
        
        jenkinsfile = asyncio.run(test_pipeline())
        print("生成的Jenkinsfile:")
        print("-" * 50)
        print(jenkinsfile)
        print("-" * 50)
        
        # 检查是否包含危险的引号嵌套
        dangerous_patterns = [
            "sh 'echo 'hello",
            "sh 'npm test '",
            "sh 'docker run '",
        ]
        
        found_issues = []
        for pattern in dangerous_patterns:
            if pattern in jenkinsfile:
                found_issues.append(pattern)
        
        if found_issues:
            print("❌ 发现引号嵌套问题:")
            for issue in found_issues:
                print(f"   - {issue}")
        else:
            print("✅ 未发现引号嵌套问题，转义正常工作")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_shell_command_escaping()
