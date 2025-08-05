#!/usr/bin/env python3
"""
测试简化的Jenkins Pipeline反斜杠转义
"""

import sys
import os
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')

from cicd_integrations.adapters.jenkins import JenkinsAdapter
from cicd_integrations.adapters.base import PipelineDefinition

def test_backslash_escaping():
    """测试反斜杠转义功能"""
    print("=== 测试Jenkins反斜杠转义 ===\n")
    
    adapter = JenkinsAdapter(
        base_url="http://localhost:8080",
        username="test",
        token="test"
    )
    
    # 测试各种包含单引号的命令
    test_commands = [
        "echo 'hello world'",
        "echo 'It's working'",
        "python -c 'print(\"Hello!\")'",
        "npm test -- --testNamePattern='integration tests'",
        "git commit -m 'Fix: resolve the issue'",
        "docker run ubuntu bash -c 'echo \"Test\"'"
    ]
    
    print("1. 转义前后对比:")
    for i, cmd in enumerate(test_commands, 1):
        escaped = adapter._escape_shell_command(cmd)
        safe_cmd = adapter._safe_shell_command(cmd)
        
        print(f"  {i}. 原始命令: {cmd}")
        print(f"     转义后:   {escaped}")
        print(f"     完整形式: {safe_cmd}")
        print()
    
    # 测试流水线步骤
    print("2. 测试流水线步骤生成:")
    test_step = {
        "name": "测试步骤",
        "type": "test_execution",
        "parameters": {
            "test_command": "echo 'hello world'"
        }
    }
    
    script = adapter._generate_stage_script(test_step['type'], test_step['parameters'])
    print(f"  步骤脚本: {script}")
    
    # 测试完整Jenkinsfile
    print("\n3. 测试完整Jenkinsfile生成:")
    pipeline_def = PipelineDefinition(
        name="backslash-test-pipeline",
        steps=[test_step],
        triggers={},
        environment={}
    )
    
    try:
        import asyncio
        
        async def generate_jenkinsfile():
            return await adapter.create_pipeline_file(pipeline_def)
        
        jenkinsfile = asyncio.run(generate_jenkinsfile())
        
        print("生成的Jenkinsfile:")
        print("-" * 50)
        print(jenkinsfile)
        print("-" * 50)
        
        # 检查是否包含正确的转义
        if "\\\'" in jenkinsfile:
            print("✅ 包含反斜杠转义")
        else:
            print("❌ 未找到反斜杠转义")
        
        # 检查是否仍包含危险的引号嵌套
        if "sh 'echo 'hello" in jenkinsfile:
            print("❌ 仍包含危险的引号嵌套")
        else:
            print("✅ 无危险的引号嵌套")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_backslash_escaping()
