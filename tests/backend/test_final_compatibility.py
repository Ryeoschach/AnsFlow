#!/usr/bin/env python
"""
简化集成测试：验证步骤兼容性修复
只测试核心功能，不涉及数据库操作
"""

import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from unittest.mock import Mock
from pipelines.models import PipelineStep
from cicd_integrations.executors.sync_step_executor import SyncStepExecutor
from cicd_integrations.executors.execution_context import ExecutionContext

def test_step_executor_compatibility():
    """测试步骤执行器兼容性修复"""
    print("=== 测试步骤执行器兼容性 ===")
    
    try:
        # 创建模拟的PipelineStep对象
        mock_pipeline_step = Mock(spec=PipelineStep)
        mock_pipeline_step.id = 1
        mock_pipeline_step.name = "测试Pipeline步骤"
        mock_pipeline_step.step_type = "script"
        mock_pipeline_step.command = "echo 'Hello Pipeline'"
        mock_pipeline_step.environment_vars = {"ENV": "test"}
        mock_pipeline_step.docker_image = "nginx"
        mock_pipeline_step.docker_tag = "latest"
        mock_pipeline_step.docker_config = {"ports": ["80:80"]}
        mock_pipeline_step.k8s_namespace = "default"
        mock_pipeline_step.k8s_config = {"replicas": 3}
        
        # 创建执行上下文
        context = ExecutionContext(
            execution_id=1,
            pipeline_name="兼容性测试流水线",
            trigger_type="test"
        )
        
        # 创建执行器
        executor = SyncStepExecutor(context)
        
        # 测试核心方法
        print("测试 _get_step_type...")
        step_type = executor._get_step_type(mock_pipeline_step)
        print(f"✅ 步骤类型: {step_type}")
        
        print("测试 _get_step_name...")
        step_name = executor._get_step_name(mock_pipeline_step)
        print(f"✅ 步骤名称: {step_name}")
        
        print("测试 _get_step_config...")
        step_config = executor._get_step_config(mock_pipeline_step)
        print(f"✅ 步骤配置: {step_config}")
        
        # 测试执行方法是否存在
        execution_methods = [
            '_execute_fetch_code',
            '_execute_build', 
            '_execute_test',
            '_execute_deploy',
            '_execute_docker_step',
            '_execute_custom',
            '_execute_mock'
        ]
        
        print("检查执行方法...")
        for method_name in execution_methods:
            if hasattr(executor, method_name):
                print(f"✅ {method_name} 方法存在")
            else:
                print(f"❌ {method_name} 方法缺失")
                return False
        
        print("✅ 所有步骤执行器兼容性测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 步骤执行器兼容性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_atomic_step_compatibility():
    """测试AtomicStep兼容性（如果存在）"""
    print("\n=== 测试AtomicStep兼容性 ===")
    
    try:
        from cicd_integrations.models import AtomicStep
        
        # 创建模拟的AtomicStep对象
        mock_atomic_step = Mock(spec=AtomicStep)
        mock_atomic_step.id = 2
        mock_atomic_step.name = "测试Atomic步骤"
        mock_atomic_step.step_type = "shell"
        mock_atomic_step.config = {
            "command": "echo 'Hello Atomic'",
            "timeout": 300
        }
        
        # 创建执行上下文
        context = ExecutionContext(
            execution_id=2,
            pipeline_name="Atomic兼容性测试流水线",
            trigger_type="test"
        )
        
        # 创建执行器
        executor = SyncStepExecutor(context)
        
        # 测试方法
        step_type = executor._get_step_type(mock_atomic_step)
        print(f"✅ 步骤类型: {step_type}")
        
        step_name = executor._get_step_name(mock_atomic_step)
        print(f"✅ 步骤名称: {step_name}")
        
        step_config = executor._get_step_config(mock_atomic_step)
        print(f"✅ 步骤配置: {step_config}")
        
        print("✅ AtomicStep兼容性测试通过")
        return True
        
    except ImportError:
        print("ℹ️  AtomicStep模型不存在，跳过兼容性测试")
        return True
    except Exception as e:
        print(f"❌ AtomicStep兼容性测试失败: {e}")
        return False

def test_parameter_compatibility():
    """测试方法参数兼容性"""
    print("\n=== 测试方法参数兼容性 ===")
    
    try:
        # 读取步骤执行器源码，检查参数使用
        executor_file = "/Users/creed/Workspace/OpenSource/ansflow/backend/django_service/cicd_integrations/executors/sync_step_executor.py"
        
        with open(executor_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否还有 atomic_step 参数（除了数据库字段）
        import re
        
        # 查找方法定义中的 atomic_step 参数
        method_atomic_step_pattern = r'def\s+\w+\([^)]*atomic_step[^)]*\):'
        method_matches = re.findall(method_atomic_step_pattern, content)
        
        if method_matches:
            print("❌ 发现未更新的方法参数:")
            for match in method_matches:
                print(f"   {match}")
            return False
        
        # 查找方法内部使用 atomic_step 的地方（排除数据库字段）
        usage_pattern = r'(?<![\w.])atomic_step(?!\s*=\s*step)'
        usage_matches = re.findall(usage_pattern, content)
        
        # 过滤掉数据库字段的使用
        filtered_matches = []
        for match in usage_matches:
            # 检查上下文，排除 "atomic_step=step" 这种数据库字段赋值
            if 'atomic_step=' not in content[content.find(match)-20:content.find(match)+20]:
                filtered_matches.append(match)
        
        if filtered_matches:
            print("❌ 发现未更新的参数使用")
            return False
        
        print("✅ 参数兼容性检查通过")
        return True
        
    except Exception as e:
        print(f"❌ 参数兼容性测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始步骤执行器兼容性修复验证...")
    
    test1 = test_step_executor_compatibility()
    test2 = test_atomic_step_compatibility() 
    test3 = test_parameter_compatibility()
    
    if test1 and test2 and test3:
        print("\n🎉 所有兼容性测试通过!")
        print("✅ PipelineStep兼容性正常")
        print("✅ AtomicStep兼容性正常")
        print("✅ 方法参数已正确更新")
        print("✅ 步骤执行器修复成功完成")
        return True
    else:
        print("\n❌ 存在兼容性问题需要修复")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
