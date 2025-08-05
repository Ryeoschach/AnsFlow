#!/usr/bin/env python3
"""
测试 Jenkinsfile 生成功能
验证原子步骤是否正确映射到 Jenkins stages
"""

import os
import sys
import django

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from cicd_integrations.models import AtomicStep, CICDTool, PipelineExecution
from cicd_integrations.adapters.jenkins import JenkinsAdapter
from cicd_integrations.adapters import PipelineDefinition
from pipelines.models import Pipeline

def test_jenkinsfile_generation():
    """测试 Jenkinsfile 生成功能"""
    print("=" * 60)
    print("🧪 测试 Jenkinsfile 生成功能")
    print("=" * 60)
    
    # 获取测试流水线
    pipeline = Pipeline.objects.get(name="E-Commerce Build & Deploy")
    print(f"📋 流水线: {pipeline.name}")
    
    # 获取原子步骤
    atomic_steps = list(
        AtomicStep.objects.filter(pipeline=pipeline).order_by('order')
    )
    print(f"📝 原子步骤数量: {len(atomic_steps)}")
    
    for step in atomic_steps:
        print(f"  - {step.name} ({step.step_type})")
        print(f"    描述: {step.description}")
        print(f"    参数: {step.parameters}")
    
    # 构建流水线定义
    steps = []
    for atomic_step in atomic_steps:
        step = {
            'name': atomic_step.name,
            'type': atomic_step.step_type,
            'parameters': atomic_step.parameters,
            'description': atomic_step.description
        }
        steps.append(step)
    
    pipeline_definition = PipelineDefinition(
        name=pipeline.name,
        steps=steps,
        triggers={},
        environment={'NODE_ENV': 'test', 'APP_VERSION': '1.0.0'},
        artifacts=[],
        timeout=3600
    )
    
    print(f"\n🔧 构建的流水线定义:")
    print(f"  名称: {pipeline_definition.name}")
    print(f"  步骤数量: {len(pipeline_definition.steps)}")
    for i, step in enumerate(pipeline_definition.steps):
        print(f"    {i+1}. {step['name']} ({step['type']})")
    
    # 创建 Jenkins 适配器并生成 Jenkinsfile
    adapter = JenkinsAdapter(
        base_url='http://localhost:8080',
        username='ansflow',
        token='test-token'
    )
    
    import asyncio
    async def generate_jenkinsfile():
        return await adapter.create_pipeline_file(pipeline_definition)
    
    # 运行异步函数
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        jenkinsfile = loop.run_until_complete(generate_jenkinsfile())
        
        print(f"\n📄 生成的 Jenkinsfile:")
        print("-" * 60)
        print(jenkinsfile)
        print("-" * 60)
        
        # 验证 Jenkinsfile 内容
        print(f"\n✅ 验证结果:")
        
        # 检查是否包含原子步骤名称
        for step in atomic_steps:
            if step.name in jenkinsfile:
                print(f"  ✅ 包含步骤: {step.name}")
            else:
                print(f"  ❌ 缺失步骤: {step.name}")
        
        # 检查是否包含关键的 Jenkins 脚本
        if 'checkout' in jenkinsfile:
            print(f"  ✅ 包含代码拉取逻辑")
        else:
            print(f"  ❌ 缺失代码拉取逻辑")
            
        if 'npm test' in jenkinsfile:
            print(f"  ✅ 包含测试命令")
        else:
            print(f"  ❌ 缺失测试命令")
        
        # 检查参数是否正确映射
        for step in atomic_steps:
            if step.step_type == 'fetch_code':
                repo_url = step.parameters.get('repository', '')
                if repo_url in jenkinsfile:
                    print(f"  ✅ 代码仓库URL正确映射: {repo_url}")
                else:
                    print(f"  ❌ 代码仓库URL未映射: {repo_url}")
            
            elif step.step_type == 'test':
                test_cmd = step.parameters.get('test_command', '')
                if test_cmd and test_cmd in jenkinsfile:
                    print(f"  ✅ 测试命令正确映射: {test_cmd}")
                elif 'npm test' in jenkinsfile:  # 默认测试命令
                    print(f"  ✅ 使用默认测试命令: npm test")
                else:
                    print(f"  ❌ 测试命令未映射")
        
        print(f"\n🎉 Jenkinsfile 生成测试完成!")
        
    finally:
        loop.close()

if __name__ == "__main__":
    test_jenkinsfile_generation()
