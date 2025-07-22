#!/usr/bin/env python3
"""
测试并行执行时的目录访问问题
"""

import os
import sys
import tempfile
import time
import threading

# 添加项目路径到sys.path
project_root = '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service'
sys.path.insert(0, project_root)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from cicd_integrations.executors.sync_step_executor import SyncStepExecutor
from cicd_integrations.executors.execution_context import ExecutionContext

def test_parallel_directory_access():
    """测试并行执行时的目录访问问题"""
    
    print("🧪 测试并行执行时的目录访问...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 临时工作目录: {temp_dir}")
        
        # 创建执行上下文
        context = ExecutionContext(
            execution_id=1,
            pipeline_name="test_parallel",
            trigger_type="manual",
            workspace_path=temp_dir,
            environment={}
        )
        
        # 创建执行器
        executor = SyncStepExecutor(context)
        
        # 记录执行结果
        results = {}
        
        def step1_create_directories():
            """步骤1: 创建目录结构（模拟代码拉取）"""
            print("\n🔨 步骤1开始: 创建目录结构")
            time.sleep(1)  # 模拟拉取代码的时间
            result = executor._run_command("mkdir -p code/test && echo 'Directory created' > code/test/README.md", {})
            results['step1'] = result
            print(f"🔨 步骤1完成: {'✅' if result['success'] else '❌'}")
            if result.get('output'):
                print(f"   输出: {result['output'].strip()}")
            if result.get('error_message'):
                print(f"   错误: {result['error_message']}")
        
        def step2_access_directory():
            """步骤2: 尝试访问目录（模拟测试步骤）"""
            print("\n🔍 步骤2开始: 尝试访问目录")
            # 立即尝试访问，可能目录还不存在
            result = executor._run_command("cd code/test && pwd && ls -la", {})
            results['step2_first'] = result
            print(f"🔍 步骤2第一次尝试: {'✅' if result['success'] else '❌'}")
            if result.get('output'):
                print(f"   输出: {result['output'].strip()}")
            if result.get('error_message'):
                print(f"   错误: {result['error_message']}")
            
            # 如果失败，等待一段时间后重试
            if not result['success']:
                print("🔍 步骤2等待后重试...")
                time.sleep(2)
                result2 = executor._run_command("cd code/test && pwd && ls -la && cat README.md", {})
                results['step2_retry'] = result2
                print(f"🔍 步骤2重试结果: {'✅' if result2['success'] else '❌'}")
                if result2.get('output'):
                    print(f"   输出: {result2['output'].strip()}")
                if result2.get('error_message'):
                    print(f"   错误: {result2['error_message']}")
        
        def step3_list_workspace():
            """步骤3: 列出工作空间内容"""
            print("\n📋 步骤3开始: 列出工作空间")
            result = executor._run_command("ls -la", {})
            results['step3'] = result
            print(f"📋 步骤3完成: {'✅' if result['success'] else '❌'}")
            if result.get('output'):
                print(f"   输出: {result['output'].strip()}")
        
        # 启动线程模拟并行执行
        thread1 = threading.Thread(target=step1_create_directories, name="Step1")
        thread2 = threading.Thread(target=step2_access_directory, name="Step2")
        thread3 = threading.Thread(target=step3_list_workspace, name="Step3")
        
        print("\n🚀 启动并行执行...")
        
        # 几乎同时启动所有步骤
        thread1.start()
        thread2.start()
        thread3.start()
        
        # 等待所有步骤完成
        thread1.join()
        thread2.join()
        thread3.join()
        
        print("\n📊 执行结果总结:")
        for step, result in results.items():
            status = '✅' if result.get('success') else '❌'
            print(f"  {step}: {status}")
        
        print(f"\n📂 最终目录状态:")
        print(f"工作目录: {context.get_current_directory()}")
        
        # 检查目录结构
        if os.path.exists(os.path.join(temp_dir, 'code', 'test')):
            print("✅ code/test 目录存在")
            readme_path = os.path.join(temp_dir, 'code', 'test', 'README.md')
            if os.path.exists(readme_path):
                print("✅ README.md 文件存在")
            else:
                print("❌ README.md 文件不存在")
        else:
            print("❌ code/test 目录不存在")

if __name__ == "__main__":
    test_parallel_directory_access()
