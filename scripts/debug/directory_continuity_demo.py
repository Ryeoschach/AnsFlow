#!/usr/bin/env python3
"""
工作目录延续性演示脚本
模拟您的使用场景
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


def demonstrate_directory_continuity():
    """演示工作目录延续性 - 模拟您的使用场景"""
    print("🎯 工作目录延续性演示")
    print("=" * 50)
    print("模拟您的使用场景:")
    print("1. 拉取代码到 code/test 目录")
    print("2. cd code/test")  
    print("3. pwd (应该显示在 code/test 中)")
    print("=" * 50)
    
    # 创建执行上下文
    context = ExecutionContext(
        execution_id=12345,
        pipeline_name='本地docker测试',
        trigger_type='manual'
    )
    
    print(f"🏠 工作空间: {context.get_workspace_path()}")
    print(f"📂 初始目录: {context.get_current_directory()}")
    
    # 创建执行器
    executor = SyncStepExecutor(context)
    
    # 步骤1: 拉取代码 (模拟)
    print(f"\n🔄 步骤1: 拉取代码")
    print("命令: mkdir -p code && git clone ssh://git@gitlab.cyfee.com:2424/root/test.git code/test")
    result1 = executor._run_command(
        "mkdir -p code && echo '模拟git clone操作' && mkdir -p code/test && echo '# 测试项目' > code/test/README.md",
        dict(os.environ)
    )
    
    print(f"✅ 状态: {'成功' if result1['success'] else '失败'}")
    print(f"📂 当前目录: {context.get_current_directory()}")
    output1 = result1.get('output', '').strip()
    if output1:
        print(f"输出: {output1}")
    
    # 步骤2: 切换到代码目录
    print(f"\n🔄 步骤2: 切换目录")
    print("命令: cd code/test")
    result2 = executor._run_command("cd code/test", dict(os.environ))
    
    print(f"✅ 状态: {'成功' if result2['success'] else '失败'}")
    print(f"📂 当前目录: {context.get_current_directory()}")
    
    # 步骤3: 验证当前目录
    print(f"\n🔄 步骤3: 验证当前目录")
    print("命令: pwd")
    result3 = executor._run_command("pwd", dict(os.environ))
    
    print(f"✅ 状态: {'成功' if result3['success'] else '失败'}")
    output3 = result3.get('output', '').strip()
    print(f"📍 PWD输出: {output3}")
    print(f"📂 上下文目录: {context.get_current_directory()}")
    
    # 验证目录是否正确
    expected_suffix = "code/test"
    if output3.endswith(expected_suffix):
        print(f"✅ 成功！PWD显示在正确的目录: {expected_suffix}")
    else:
        print(f"❌ 失败！期望目录包含 {expected_suffix}，实际: {output3}")
    
    # 额外验证：在当前目录执行命令
    print(f"\n🔄 步骤4: 在当前目录执行操作")
    print("命令: ls -la && cat README.md")
    result4 = executor._run_command("ls -la && echo '--- README.md 内容 ---' && cat README.md", dict(os.environ))
    
    print(f"✅ 状态: {'成功' if result4['success'] else '失败'}")
    output4 = result4.get('output', '').strip()
    if output4:
        print(f"输出:\n{output4}")
    
    print(f"\n🎯 总结:")
    print(f"- 工作空间: {context.get_workspace_path()}")
    print(f"- 最终目录: {context.get_current_directory()}")
    
    # 验证最终状态
    if context.get_current_directory().endswith('code/test'):
        print("✅ 工作目录状态正确延续！")
        return True
    else:
        print("❌ 工作目录状态未正确延续")
        return False


def test_complex_directory_operations():
    """测试复杂的目录操作"""
    print(f"\n🧪 复杂目录操作测试")
    print("-" * 40)
    
    context = ExecutionContext(
        execution_id=54321,
        pipeline_name='复杂测试',
        trigger_type='manual'
    )
    
    executor = SyncStepExecutor(context)
    
    # 测试多层目录创建和切换
    operations = [
        ("创建多层目录", "mkdir -p a/b/c/d && cd a/b/c"),
        ("验证位置", "pwd"),
        ("创建文件", "echo 'test content' > test.txt"),
        ("返回根目录", "cd ../../.."),
        ("验证返回", "pwd"),
        ("再次进入", "cd a/b/c"),
        ("验证文件", "cat test.txt"),
        ("相对路径", "cd ../.."),
        ("最终验证", "pwd && ls -la")
    ]
    
    for i, (desc, cmd) in enumerate(operations, 1):
        print(f"\n{i}. {desc}: {cmd}")
        result = executor._run_command(cmd, dict(os.environ))
        print(f"   状态: {'✅' if result['success'] else '❌'}")
        print(f"   目录: {context.get_current_directory()}")
        
        output = result.get('output', '').strip()
        if output:
            print(f"   输出: {output}")


if __name__ == "__main__":
    print("🚀 工作目录延续性功能演示")
    print("=" * 60)
    
    # 主要演示
    success = demonstrate_directory_continuity()
    
    # 复杂测试
    test_complex_directory_operations()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 演示成功！工作目录延续功能正常工作")
        print("\n💡 现在您的流水线中：")
        print("- 第一个步骤：git clone ssh://git@gitlab.cyfee.com:2424/root/test.git")
        print("- 第二个步骤：cd code/test  ✅ 会正确切换目录")
        print("- 第三个步骤：pwd  ✅ 会显示在 code/test 目录中")
    else:
        print("❌ 演示失败")
    
    print("\n🔧 如需重启服务使更改生效：")
    print("cd /Users/creed/Workspace/OpenSource/ansflow/backend/django_service")
    print("uv run python manage.py runserver 0.0.0.0:8000")
