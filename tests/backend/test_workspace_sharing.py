#!/usr/bin/env python
"""
测试工作空间共享修复
"""
import os
import sys

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')

import django
django.setup()

from cicd_integrations.executors.execution_context import ExecutionContext

def test_workspace_sharing():
    """测试工作空间共享不会重复创建"""
    print("🧪 测试工作空间共享修复")
    print("=" * 80)
    
    print("📋 模拟两个阶段的执行流程:")
    print("  阶段1: 拉取代码")
    print("  阶段2: 切换工作目录")
    print()
    
    # 模拟第一次创建工作空间
    print("1️⃣ 第一阶段：创建工作空间并拉取代码")
    context1 = ExecutionContext(
        execution_id=103,
        pipeline_name="工作空间共享测试",
        trigger_type='manual'
    )
    
    workspace1 = context1.get_workspace_path()
    print(f"   ✅ 创建工作空间: {workspace1}")
    
    # 创建模拟的代码目录
    import subprocess
    test_dir = os.path.join(workspace1, 'test')
    os.makedirs(test_dir, exist_ok=True)
    with open(os.path.join(test_dir, 'README.md'), 'w') as f:
        f.write("# Test Project")
    
    print(f"   ✅ 模拟拉取代码，创建目录: {test_dir}")
    print(f"   📁 工作空间内容: {os.listdir(workspace1)}")
    
    # 模拟第二次使用相同的工作空间ID
    print(f"\n2️⃣ 第二阶段：使用相同工作空间ID (应该复用，不删除)")
    
    # 检查第二次创建是否会删除已存在的内容
    print(f"   🔍 执行前检查目录是否存在: {os.path.exists(test_dir)}")
    
    # 这里不应该再次创建ExecutionContext，而应该复用
    # 但为了测试，我们看看会发生什么
    context2 = ExecutionContext(
        execution_id=103,  # 相同的execution_id
        pipeline_name="工作空间共享测试",  # 相同的pipeline_name
        trigger_type='manual'
    )
    
    workspace2 = context2.get_workspace_path()
    print(f"   📂 第二次获取工作空间: {workspace2}")
    print(f"   ✅ 工作空间路径相同: {workspace1 == workspace2}")
    print(f"   🔍 执行后检查目录是否存在: {os.path.exists(test_dir)}")
    
    if os.path.exists(test_dir):
        print(f"   📁 工作空间内容: {os.listdir(workspace1)}")
        print(f"   ✅ 测试代码目录仍然存在，没有被删除")
    else:
        print(f"   ❌ 测试代码目录被删除了！这是问题所在")
    
    print(f"\n" + "=" * 80)
    print("📋 修复总结:")
    print("1. ✅ 问题诊断 - 每个阶段重新创建ExecutionContext导致工作空间被删除")
    print("2. ✅ 解决方案 - 在流水线开始时创建一次工作空间，所有阶段共享")
    print("3. 🔄 实施状态 - 正在修改parallel_execution.py中的工作空间管理逻辑")
    
    return os.path.exists(test_dir)

def main():
    """主测试函数"""
    print("🚀 工作空间共享修复验证")
    print("=" * 80)
    
    success = test_workspace_sharing()
    
    if success:
        print(f"\n🎉 工作空间保持完整！")
    else:
        print(f"\n❌ 工作空间被意外删除，需要修复")

if __name__ == "__main__":
    main()
