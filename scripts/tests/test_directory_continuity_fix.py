#!/usr/bin/env python3
"""
测试目录连续性功能
这个脚本测试流水线步骤之间的目录状态是否能正确传递
"""

import os
import sys
import tempfile
import shutil

# 添加项目路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend', 'django_service'))
sys.path.insert(0, project_root)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from cicd_integrations.models import AtomicStep, CICDTool, StepExecution
from cicd_integrations.executors.sync_step_executor import SyncStepExecutor
from cicd_integrations.executors.execution_context import ExecutionContext

def test_directory_continuity():
    """测试目录连续性"""
    
    print("🧪 开始测试目录连续性功能...")
    
    # 创建临时工作目录
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 创建临时工作目录: {temp_dir}")
        
        # 创建执行上下文
        context = ExecutionContext(
            execution_id=1,
            pipeline_name="test_pipeline",
            trigger_type="manual",
            workspace_path=temp_dir,
            environment={}
        )
        
        # 创建执行器
        executor = SyncStepExecutor(context)
        
        # 创建虚拟工具
        tool = CICDTool.objects.create(
            name="test_tool",
            tool_type="custom",
            config={}
        )
        
        print("\n--- 步骤 1: 创建目录结构 ---")
        
        # 步骤1: 创建目录结构
        step1 = AtomicStep.objects.create(
            name="创建目录",
            step_type="custom",
            tool=tool,
            config={
                "command": "mkdir -p code/test && echo '创建目录结构完成'"
            }
        )
        
        result1 = executor.execute_step(step1, {})
        print(f"步骤1执行结果: {result1['status']}")
        print(f"当前工作目录: {context.get_current_directory()}")
        
        print("\n--- 步骤 2: 切换到子目录并创建文件 ---")
        
        # 步骤2: 切换目录
        step2 = AtomicStep.objects.create(
            name="切换目录",
            step_type="custom",
            tool=tool,
            config={
                "command": "cd code/test && echo 'hello world' > test.txt && pwd"
            }
        )
        
        result2 = executor.execute_step(step2, {})
        print(f"步骤2执行结果: {result2['status']}")
        print(f"当前工作目录: {context.get_current_directory()}")
        
        print("\n--- 步骤 3: 在当前目录执行命令 ---")
        
        # 步骤3: 验证目录状态
        step3 = AtomicStep.objects.create(
            name="验证目录",
            step_type="custom",
            tool=tool,
            config={
                "command": "pwd && ls -la && cat test.txt"
            }
        )
        
        result3 = executor.execute_step(step3, {})
        print(f"步骤3执行结果: {result3['status']}")
        print(f"当前工作目录: {context.get_current_directory()}")
        
        print("\n--- 步骤 4: 切换到上级目录 ---")
        
        # 步骤4: 切换到上级目录
        step4 = AtomicStep.objects.create(
            name="返回上级",
            step_type="custom",
            tool=tool,
            config={
                "command": "cd .. && pwd && ls -la"
            }
        )
        
        result4 = executor.execute_step(step4, {})
        print(f"步骤4执行结果: {result4['status']}")
        print(f"当前工作目录: {context.get_current_directory()}")
        
        print("\n🎯 测试结果分析:")
        
        # 分析结果
        all_success = all([
            result1['status'] == 'success',
            result2['status'] == 'success', 
            result3['status'] == 'success',
            result4['status'] == 'success'
        ])
        
        if all_success:
            print("✅ 所有步骤执行成功")
            
            # 检查目录状态变化
            if 'code/test' in context.get_current_directory():
                print("❌ 目录连续性测试失败：最终目录应该在code目录而不是code/test")
            elif 'code' in context.get_current_directory():
                print("✅ 目录连续性测试成功：正确保持了目录状态变化")
            else:
                print("⚠️  目录状态不确定，需要进一步检查")
        else:
            print("❌ 部分步骤执行失败")
        
        print(f"\n📋 详细输出信息:")
        print("=" * 50)
        for i, result in enumerate([result1, result2, result3, result4], 1):
            print(f"\n步骤{i}输出:")
            print(result.get('output', '无输出'))
            
        # 清理数据
        step1.delete()
        step2.delete() 
        step3.delete()
        step4.delete()
        tool.delete()

if __name__ == "__main__":
    test_directory_continuity()
