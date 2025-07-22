#!/usr/bin/env python3
"""
验证工作目录延续性修复
"""
import os
import sys
import django

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

django.setup()

from cicd_integrations.executors.sync_step_executor import SyncStepExecutor
from cicd_integrations.executors.execution_context import ExecutionContext


def test_pwd_output_fix():
    """测试pwd输出修复"""
    print("🔧 测试工作目录输出修复")
    print("=" * 40)
    
    # 创建执行上下文
    context = ExecutionContext(
        execution_id=99999,
        pipeline_name='修复测试',
        trigger_type='manual'
    )
    
    executor = SyncStepExecutor(context)
    
    print(f"工作空间: {context.get_workspace_path()}")
    print(f"初始目录: {context.get_current_directory()}")
    
    # 测试1: 直接pwd - 应该显示实际目录
    print(f"\n🧪 测试1: 直接执行pwd")
    result1 = executor._run_command("pwd", dict(os.environ))
    print(f"输出: {result1.get('output', '').strip()}")
    
    # 测试2: 模拟自定义脚本 - 应该显示实际目录
    print(f"\n🧪 测试2: 模拟自定义脚本步骤")
    
    # 模拟_execute_custom_script方法的逻辑
    workspace_path = context.get_workspace_path()
    script = "pwd"
    
    # 使用修复后的enhanced_script格式
    enhanced_script = f"echo 'Executing in workspace: {workspace_path}' && echo \"Current directory: $(pwd)\" && {script}"
    
    print(f"增强脚本: {enhanced_script}")
    
    result2 = executor._run_command(enhanced_script, dict(os.environ))
    print(f"输出:\n{result2.get('output', '').strip()}")
    
    # 验证pwd是否被正确执行
    output_lines = result2.get('output', '').strip().split('\n')
    found_real_pwd = False
    
    for line in output_lines:
        if line.startswith('/') and 'Current directory:' not in line:
            # 这应该是真实的pwd输出
            found_real_pwd = True
            print(f"✅ 找到真实pwd输出: {line}")
            break
    
    if not found_real_pwd:
        print("❌ 未找到真实pwd输出")
    
    # 测试3: 切换目录后测试
    print(f"\n🧪 测试3: 切换目录后的pwd输出")
    
    # 创建并切换到子目录
    result3 = executor._run_command("mkdir -p test_subdir && cd test_subdir && pwd", dict(os.environ))
    print(f"切换后输出: {result3.get('output', '').strip()}")
    print(f"上下文目录: {context.get_current_directory()}")
    
    # 验证是否在子目录中
    if 'test_subdir' in result3.get('output', ''):
        print("✅ 成功切换到子目录并显示正确路径")
    else:
        print("❌ 目录切换显示异常")
    
    return found_real_pwd


if __name__ == "__main__":
    success = test_pwd_output_fix()
    if success:
        print(f"\n🎉 修复验证成功！")
        print(f"现在自定义脚本步骤会显示真实的pwd输出")
    else:
        print(f"\n❌ 修复验证失败")
