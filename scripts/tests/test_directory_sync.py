#!/usr/bin/env python3
"""
测试目录状态在并行执行中的同步问题
"""

import os
import sys
import tempfile
import threading
import time

# 添加项目路径到sys.path
project_root = '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service'
sys.path.insert(0, project_root)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from cicd_integrations.executors.execution_context import ExecutionContext

def test_concurrent_directory_state():
    """测试并发环境下的目录状态同步"""
    
    print("🧪 测试并发目录状态同步...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 临时工作目录: {temp_dir}")
        
        # 创建执行上下文
        context = ExecutionContext(
            execution_id=1,
            pipeline_name="test_concurrent",
            trigger_type="manual",
            workspace_path=temp_dir,
            environment={}
        )
        
        # 创建测试目录结构
        code_dir = os.path.join(temp_dir, 'code')
        test_dir = os.path.join(code_dir, 'test')
        os.makedirs(test_dir, exist_ok=True)
        
        # 模拟并行执行的结果
        results = {}
        
        def thread1_change_directory():
            """线程1: 模拟拉取代码步骤"""
            print(f"\n🔨 线程1开始 (Thread: {threading.current_thread().name})")
            
            # 模拟代码拉取，切换到code目录
            context.set_current_directory(code_dir)
            print(f"🔨 线程1: 切换到目录 {code_dir}")
            results['thread1_dir'] = context.get_current_directory()
            
            time.sleep(1)  # 模拟执行时间
            print(f"🔨 线程1完成，当前目录: {context.get_current_directory()}")
        
        def thread2_change_directory():
            """线程2: 模拟测试步骤，依赖线程1"""
            print(f"\n🔍 线程2开始 (Thread: {threading.current_thread().name})")
            
            # 等待线程1完成
            time.sleep(1.5)
            
            # 获取当前目录状态
            current_dir = context.get_current_directory()
            print(f"🔍 线程2: 当前目录状态 {current_dir}")
            
            # 模拟cd code/test命令
            context.set_current_directory(test_dir)
            print(f"🔍 线程2: 切换到目录 {test_dir}")
            results['thread2_dir'] = context.get_current_directory()
            
            time.sleep(1)  # 模拟执行时间
            print(f"🔍 线程2完成，当前目录: {context.get_current_directory()}")
        
        def thread3_use_directory():
            """线程3: 模拟第三个步骤，应该使用线程2的目录状态"""
            print(f"\n📋 线程3开始 (Thread: {threading.current_thread().name})")
            
            # 等待线程2完成
            time.sleep(3)
            
            # 获取当前目录状态
            current_dir = context.get_current_directory()
            print(f"📋 线程3: 当前目录状态 {current_dir}")
            results['thread3_dir'] = current_dir
            
            # 检查是否在正确的目录
            expected_dir = test_dir
            if current_dir == expected_dir:
                print(f"📋 线程3: ✅ 目录状态正确")
                results['thread3_success'] = True
            else:
                print(f"📋 线程3: ❌ 目录状态错误！期望: {expected_dir}, 实际: {current_dir}")
                results['thread3_success'] = False
        
        # 创建并启动线程
        t1 = threading.Thread(target=thread1_change_directory, name="PullCode")
        t2 = threading.Thread(target=thread2_change_directory, name="Test")  
        t3 = threading.Thread(target=thread3_use_directory, name="List")
        
        print("\n🚀 启动并行线程...")
        t1.start()
        t2.start()
        t3.start()
        
        # 等待所有线程完成
        t1.join()
        t2.join() 
        t3.join()
        
        print(f"\n📊 测试结果:")
        print(f"  线程1最终目录: {results.get('thread1_dir', 'N/A')}")
        print(f"  线程2最终目录: {results.get('thread2_dir', 'N/A')}")
        print(f"  线程3最终目录: {results.get('thread3_dir', 'N/A')}")
        print(f"  线程3是否成功: {'✅' if results.get('thread3_success') else '❌'}")
        
        # 验证最终状态
        if results.get('thread3_success'):
            print("\n🎉 目录状态同步测试: ✅ 通过")
            return True
        else:
            print("\n❌ 目录状态同步测试: 失败")
            return False

if __name__ == "__main__":
    success = test_concurrent_directory_state()
    sys.exit(0 if success else 1)
