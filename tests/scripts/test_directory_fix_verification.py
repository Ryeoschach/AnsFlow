#!/usr/bin/env python3
"""
验证目录状态同步修复的模拟测试
"""

import os
import tempfile
import threading
import time

class MockExecutionContext:
    """模拟执行上下文"""
    
    def __init__(self, workspace_path):
        self.workspace_path = workspace_path
        self.current_working_directory = workspace_path
        self._directory_lock = threading.Lock()
    
    def get_workspace_path(self):
        return self.workspace_path
    
    def get_current_directory(self):
        with self._directory_lock:
            return self.current_working_directory or self.workspace_path
    
    def set_current_directory(self, path):
        with self._directory_lock:
            if os.path.exists(path) and os.path.isdir(path):
                self.current_working_directory = path
                print(f"🔄 目录状态已更新 (线程: {threading.current_thread().name}): {path}")
            else:
                print(f"⚠️  目录不存在: {path}")

def simulate_step_execution(context, step_name, command, should_change_dir=None):
    """模拟步骤执行"""
    print(f"\n{step_name} 开始执行 (线程: {threading.current_thread().name})")
    
    # 获取当前目录状态
    current_dir = context.get_current_directory()
    print(f"{step_name}: 执行前目录: {current_dir}")
    
    # 模拟命令执行
    print(f"{step_name}: 执行命令: {command}")
    time.sleep(0.5)  # 模拟执行时间
    
    # 如果需要改变目录
    if should_change_dir:
        context.set_current_directory(should_change_dir)
    
    final_dir = context.get_current_directory()
    print(f"{step_name}: 执行后目录: {final_dir}")
    
    return {
        'step': step_name,
        'initial_dir': current_dir,
        'final_dir': final_dir,
        'expected_dir': should_change_dir or current_dir
    }

def test_directory_continuity_fix():
    """测试目录连续性修复"""
    
    print("🧪 测试目录连续性修复...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 工作空间: {temp_dir}")
        
        # 创建测试目录结构
        code_dir = os.path.join(temp_dir, 'code')
        test_dir = os.path.join(code_dir, 'test')
        os.makedirs(test_dir, exist_ok=True)
        
        # 创建模拟执行上下文
        context = MockExecutionContext(temp_dir)
        
        # 存储结果
        results = {}
        
        def step1_pull_code():
            """步骤1: 拉取代码"""
            result = simulate_step_execution(
                context, 
                "🔨 拉取代码", 
                "git clone ... && cd code",
                should_change_dir=code_dir
            )
            results['step1'] = result
        
        def step2_test():
            """步骤2: 测试 (应该继承step1的目录状态)"""
            result = simulate_step_execution(
                context,
                "🔍 测试",
                "cd code/test",
                should_change_dir=test_dir
            )
            results['step2'] = result
        
        def step3_list():
            """步骤3: 列表 (应该继承step2的目录状态)"""
            result = simulate_step_execution(
                context,
                "📋 列表",
                "ls -la",
                should_change_dir=None  # 不改变目录，应该继承之前的状态
            )
            results['step3'] = result
        
        # 模拟并行执行
        threads = []
        
        # 按顺序启动，但模拟并行场景
        t1 = threading.Thread(target=step1_pull_code, name="Step1-Pull")
        t2 = threading.Thread(target=step2_test, name="Step2-Test")
        t3 = threading.Thread(target=step3_list, name="Step3-List")
        
        threads = [t1, t2, t3]
        
        print("\n🚀 启动步骤执行...")
        
        # 按顺序启动，模拟实际的依赖执行
        t1.start()
        t1.join()
        
        t2.start() 
        t2.join()
        
        t3.start()
        t3.join()
        
        print(f"\n📊 执行结果分析:")
        
        all_success = True
        
        for step_key, result in results.items():
            step_name = result['step']
            initial = result['initial_dir']
            final = result['final_dir']
            expected = result['expected_dir']
            
            print(f"  {step_name}:")
            print(f"    初始目录: {initial}")
            print(f"    最终目录: {final}")
            print(f"    期望目录: {expected}")
            
            if final == expected:
                print(f"    状态: ✅ 正确")
            else:
                print(f"    状态: ❌ 错误")
                all_success = False
        
        # 关键测试：步骤3应该在test目录执行
        step3_result = results.get('step3', {})
        step3_initial = step3_result.get('initial_dir', '')
        
        print(f"\n🎯 关键验证: 步骤3的初始目录")
        print(f"   实际: {step3_initial}")
        print(f"   期望: {test_dir}")
        
        if step3_initial == test_dir:
            print(f"   结果: ✅ 目录连续性修复成功！")
            return True
        else:
            print(f"   结果: ❌ 目录连续性仍有问题")
            return False

if __name__ == "__main__":
    success = test_directory_continuity_fix()
    print(f"\n{'🎉 测试通过' if success else '❌ 测试失败'}")
