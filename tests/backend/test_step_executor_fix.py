#!/usr/bin/env python
"""
测试步骤执行器修复
验证 PipelineStep 和 AtomicStep 的兼容性
"""

import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from django.test import TestCase
from unittest.mock import Mock, patch
from pipelines.models import PipelineStep
from cicd_integrations.executors.sync_step_executor import SyncStepExecutor
from cicd_integrations.executors.execution_context import ExecutionContext

# 尝试导入 AtomicStep（如果存在）
try:
    from cicd_integrations.models import AtomicStep
    HAS_ATOMIC_STEP = True
except ImportError:
    AtomicStep = None
    HAS_ATOMIC_STEP = False

def test_pipeline_step_compatibility():
    """测试 PipelineStep 兼容性"""
    print("=== 测试 PipelineStep 兼容性 ===")
    
    # 创建模拟的 PipelineStep
    mock_step = Mock(spec=PipelineStep)
    mock_step.id = 1
    mock_step.name = "测试步骤"
    mock_step.step_type = "docker"
    mock_step.docker_image = "nginx"
    mock_step.docker_tag = "latest"
    mock_step.docker_config = {
        "image": "nginx:latest",
        "command": ["echo", "hello"]
    }
    
    # 创建执行器
    context = ExecutionContext(
        execution_id=1,
        pipeline_name="测试流水线",
        trigger_type="manual"
    )
    executor = SyncStepExecutor(context)
    
    try:
        # 测试 _get_step_type 方法
        step_type = executor._get_step_type(mock_step)
        print(f"✅ _get_step_type 返回: {step_type}")
        
        # 测试 _get_step_config 方法
        config = executor._get_step_config(mock_step)
        print(f"✅ _get_step_config 返回: {config}")
        
        # 测试 _get_step_name 方法
        name = executor._get_step_name(mock_step)
        print(f"✅ _get_step_name 返回: {name}")
        
        print("✅ 所有测试通过！PipelineStep 兼容性修复成功")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_atomic_step_compatibility():
    """测试 AtomicStep 兼容性（如果存在）"""
    print("\n=== 测试 AtomicStep 兼容性 ===")
    
    if not HAS_ATOMIC_STEP:
        print("ℹ️  AtomicStep 模型不存在，跳过测试")
        return True
    
    try:
        # 创建模拟的 AtomicStep
        mock_step = Mock(spec=AtomicStep)
        mock_step.id = 2
        mock_step.name = "原子步骤"
        mock_step.step_type = "shell"
        mock_step.config = {
            "command": "echo hello"
        }
        
        # 创建执行器
        context = ExecutionContext(
            execution_id=2,
            pipeline_name="测试流水线",
            trigger_type="manual"
        )
        executor = SyncStepExecutor(context)
        
        # 测试方法
        step_type = executor._get_step_type(mock_step)
        print(f"✅ _get_step_type 返回: {step_type}")
        
        config = executor._get_step_config(mock_step)
        print(f"✅ _get_step_config 返回: {config}")
        
        name = executor._get_step_name(mock_step)
        print(f"✅ _get_step_name 返回: {name}")
        
        print("✅ AtomicStep 兼容性正常")
        return True
        
    except Exception as e:
        print(f"❌ AtomicStep 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试步骤执行器修复...")
    
    success1 = test_pipeline_step_compatibility()
    success2 = test_atomic_step_compatibility()
    
    if success1 and success2:
        print("\n🎉 所有测试通过！步骤执行器修复成功完成")
        sys.exit(0)
    else:
        print("\n❌ 存在测试失败")
        sys.exit(1)
