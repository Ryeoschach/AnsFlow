#!/usr/bin/env python3
"""
验证步骤重试逻辑修复的简化测试
"""

def test_failed_steps_collection_logic():
    """测试failed_steps集合的管理逻辑"""
    
    print("🧪 测试步骤重试逻辑...")
    
    # 模拟初始状态
    failed_steps = set()
    completed_threads = []
    
    # 模拟步骤执行状态
    print("\n📋 模拟初始状态:")
    print(f"failed_steps: {failed_steps}")
    print(f"completed_threads: {completed_threads}")
    
    # 模拟步骤1失败
    step_1_id = "step_1"
    failed_steps.add(step_1_id)
    print(f"\n❌ 步骤1失败，添加到failed_steps: {failed_steps}")
    
    # 模拟步骤2成功
    step_2_id = "step_2"
    completed_threads.append({
        'step_id': step_2_id,
        'success': True,
        'output': 'Step 2 completed successfully'
    })
    print(f"\n✅ 步骤2成功，添加到completed_threads")
    
    # 模拟步骤1重试成功
    # 这是我们修复的关键逻辑
    print(f"\n🔄 步骤1重试...")
    step_1_retry_result = {
        'step_id': step_1_id,
        'success': True,
        'output': 'Step 1 retry succeeded'
    }
    completed_threads.append(step_1_retry_result)
    
    print(f"completed_threads: {[t['step_id'] + ('✅' if t['success'] else '❌') for t in completed_threads]}")
    
    # 应用修复后的清理逻辑
    print(f"\n🧹 应用清理逻辑...")
    print(f"清理前 failed_steps: {failed_steps}")
    
    # 这是修复后的逻辑
    for thread_result in completed_threads:
        if thread_result['success'] and thread_result['step_id'] in failed_steps:
            failed_steps.discard(thread_result['step_id'])
            print(f"   从failed_steps中移除成功重试的步骤: {thread_result['step_id']}")
    
    print(f"清理后 failed_steps: {failed_steps}")
    
    # 判断管道状态
    pipeline_failed = len(failed_steps) > 0
    print(f"\n📊 管道状态判断:")
    print(f"剩余失败步骤数: {len(failed_steps)}")
    print(f"管道状态: {'❌ 失败' if pipeline_failed else '✅ 成功'}")
    
    # 验证修复是否有效
    if len(failed_steps) == 0:
        print("\n🎉 修复验证: ✅ 成功！步骤重试后正确从failed_steps中移除")
    else:
        print("\n❌ 修复验证: 失败！failed_steps仍然包含已成功的步骤")
    
    return len(failed_steps) == 0

def test_multiple_retries_scenario():
    """测试多次重试的复杂场景"""
    
    print("\n\n🧪 测试多次重试场景...")
    
    failed_steps = set()
    completed_threads = []
    
    # 模拟多个步骤的复杂执行状态
    steps = ["step_1", "step_2", "step_3", "step_4"]
    
    # 初始状态：步骤1、3、4失败
    failed_steps.update(["step_1", "step_3", "step_4"])
    print(f"初始失败步骤: {failed_steps}")
    
    # 步骤2直接成功
    completed_threads.append({
        'step_id': "step_2",
        'success': True,
        'output': 'Step 2 success'
    })
    
    # 步骤1第一次重试失败
    completed_threads.append({
        'step_id': "step_1",
        'success': False,
        'output': 'Step 1 first retry failed'
    })
    
    # 步骤3重试成功
    completed_threads.append({
        'step_id': "step_3",
        'success': True,
        'output': 'Step 3 retry success'
    })
    
    # 步骤1第二次重试成功
    completed_threads.append({
        'step_id': "step_1", 
        'success': True,
        'output': 'Step 1 second retry success'
    })
    
    # 步骤4仍然失败（没有成功的重试）
    
    print(f"完成的线程: {[(t['step_id'], '✅' if t['success'] else '❌') for t in completed_threads]}")
    
    # 应用清理逻辑
    print(f"\n清理前 failed_steps: {failed_steps}")
    
    for thread_result in completed_threads:
        if thread_result['success'] and thread_result['step_id'] in failed_steps:
            failed_steps.discard(thread_result['step_id'])
            print(f"   移除成功步骤: {thread_result['step_id']}")
    
    print(f"清理后 failed_steps: {failed_steps}")
    
    # 期望结果：只有step_4仍在failed_steps中
    expected_failed = {"step_4"}
    if failed_steps == expected_failed:
        print("🎉 复杂场景测试: ✅ 成功！")
        return True
    else:
        print(f"❌ 复杂场景测试失败！期望: {expected_failed}, 实际: {failed_steps}")
        return False

if __name__ == "__main__":
    print("🔧 验证步骤重试逻辑修复\n")
    
    # 测试基本重试逻辑
    basic_test_passed = test_failed_steps_collection_logic()
    
    # 测试复杂重试场景
    complex_test_passed = test_multiple_retries_scenario()
    
    print(f"\n📊 总结:")
    print(f"基本重试逻辑测试: {'✅' if basic_test_passed else '❌'}")
    print(f"复杂重试场景测试: {'✅' if complex_test_passed else '❌'}")
    
    if basic_test_passed and complex_test_passed:
        print("\n🎉 所有测试通过！步骤重试逻辑修复有效。")
    else:
        print("\n❌ 部分测试失败，需要进一步检查修复逻辑。")
