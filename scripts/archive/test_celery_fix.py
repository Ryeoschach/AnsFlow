#!/usr/bin/env python3
"""
测试 Celery 执行修复 - 验证是否消除了重复的 create_pipeline 调用
"""

import os
import sys
import django
import asyncio
import logging

# 设置 Django
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_service.settings')

django.setup()

from django_service.pipelines.models import Pipeline, AtomicStep, PipelineExecution
from django_service.cicd_integrations.models import CICDToolConfig
from django_service.cicd_integrations.services import UnifiedCICDEngine
from django_service.cicd_integrations.adapters.jenkins import JenkinsAdapter
from django_service.cicd_integrations.adapters.base import PipelineDefinition

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_fixed_execution():
    """测试修复后的执行流程"""
    print("=== 测试修复后的远程执行流程 ===")
    
    try:
        # 获取测试流水线
        pipeline = Pipeline.objects.get(name="Integration Test Pipeline")
        print(f"找到测试流水线: {pipeline.name}")
        
        # 获取原子步骤
        atomic_steps = list(AtomicStep.objects.filter(pipeline=pipeline).order_by('step_order'))
        print(f"找到 {len(atomic_steps)} 个原子步骤:")
        for step in atomic_steps:
            print(f"  - {step.name} ({step.step_type})")
        
        # 获取 Jenkins 配置
        jenkins_config = CICDToolConfig.objects.get(name="Jenkins Dev")
        print(f"使用 Jenkins 配置: {jenkins_config.name}")
        
        # 创建流水线定义
        pipeline_definition = PipelineDefinition(
            name=pipeline.name,
            steps=[{
                'name': step.name,
                'type': step.step_type,
                'config': step.parameters
            } for step in atomic_steps]
        )
        
        # 测试单独调用 create_pipeline 和 trigger_pipeline
        print("\n--- 测试分离的创建和触发流程 ---")
        
        # 创建 Jenkins adapter
        adapter = JenkinsAdapter(jenkins_config.config)
        
        async with adapter:
            # Step 1: 创建流水线（应该只有一次 "Attempting to update Jenkins job" 日志）
            print("1. 创建流水线...")
            job_name = await adapter.create_pipeline(pipeline_definition)
            print(f"   流水线创建完成: {job_name}")
            
            # Step 2: 触发流水线（应该不会再有创建日志）
            print("2. 触发流水线...")
            execution_result = await adapter.trigger_pipeline(pipeline_definition)
            print(f"   触发结果: {execution_result.success}")
            print(f"   外部ID: {execution_result.external_id}")
            print(f"   消息: {execution_result.message}")
        
        print("\n✅ 测试完成 - 检查日志确认没有重复的配置更新请求")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fixed_execution())
