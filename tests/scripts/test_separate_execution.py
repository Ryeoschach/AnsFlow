#!/usr/bin/env python3
"""
简单测试 Jenkins Adapter 的分离执行逻辑
"""

import os
import sys
import django
import asyncio
import logging

# 设置路径
sys.path.insert(0, '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

try:
    django.setup()
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

from cicd_integrations.adapters.jenkins import JenkinsAdapter
from cicd_integrations.adapters.base import PipelineDefinition

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_separate_create_and_trigger():
    """测试分离的创建和触发流程"""
    print("=== 测试分离的 create_pipeline 和 trigger_pipeline 调用 ===")
    
    # Jenkins 配置
    jenkins_config = {
        'base_url': 'http://localhost:8080',
        'username': 'admin',
        'token': '117a66ac1f854f5e2c38c0e2e81f8f9e46'
    }
    
    # 测试流水线定义
    pipeline_def = PipelineDefinition(
        name="Test Separate Execution",
        steps=[
            {
                'name': 'Setup Environment',
                'type': 'fetch_code',
                'config': {
                    'repository': 'https://github.com/test/repo.git',
                    'branch': 'main'
                }
            },
            {
                'name': 'Run Tests',
                'type': 'test',
                'config': {
                    'command': 'echo "Running tests..."'
                }
            },
            {
                'name': 'Deploy',
                'type': 'custom',
                'config': {
                    'command': 'echo "Deploying application..."'
                }
            }
        ],
        triggers={},
        environment={},
        artifacts=[],
        timeout=3600
    )
    
    try:
        adapter = JenkinsAdapter(**jenkins_config)
        
        async with adapter:
            print("1. 调用 create_pipeline...")
            job_name = await adapter.create_pipeline(pipeline_def)
            print(f"   ✅ 流水线创建完成: {job_name}")
            
            print("\n2. 调用 trigger_pipeline...")
            execution_result = await adapter.trigger_pipeline(pipeline_def)
            print(f"   ✅ 触发结果: success={execution_result.success}")
            print(f"   ✅ 外部ID: {execution_result.external_id}")
            print(f"   ✅ 消息: {execution_result.message}")
            
        print("\n✅ 测试完成")
        print("检查上述日志，应该只看到一次 'Attempting to update Jenkins job' 消息")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_separate_create_and_trigger())
