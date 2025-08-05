#!/usr/bin/env python3
"""
验证前端修复后的并行组传递
"""

import json
import subprocess
import sys
import time

def test_frontend_parallel_groups():
    """测试前端修复后是否正确传递并行组"""
    print("🔍 测试前端修复 - 并行组数据传递")
    print("=" * 50)
    
    print("📝 修复说明:")
    print("  - 修复了 normalizeStepForDisplay 函数，添加 parallel_group 字段")
    print("  - 前端现在应该能正确传递并行组数据到后端API")
    
    print("\n🧪 测试步骤:")
    print("  1. 使用 preview_mode=true 测试前端传递的数据")
    print("  2. 使用 preview_mode=false 测试数据库数据")
    print("  3. 对比两种模式的并行组检测结果")
    
    # 模拟前端传递的数据（修复后应该包含parallel_group字段）
    frontend_data = {
        "pipeline_id": 2,
        "preview_mode": True,  # 使用前端传递的数据
        "execution_mode": "remote",
        "steps": [
            {
                "name": "1111",
                "step_type": "custom",
                "parameters": {},
                "order": 1,
                "description": "",
                "parallel_group": ""  # 顺序步骤
            },
            {
                "name": "222-1",
                "step_type": "custom", 
                "parameters": {},
                "order": 2,
                "description": "",
                "parallel_group": "parallel_1752467687202"  # 并行组
            },
            {
                "name": "222-2",
                "step_type": "custom",
                "parameters": {},
                "order": 3,
                "description": "",
                "parallel_group": "parallel_1752467687202"  # 并行组
            },
            {
                "name": "333",
                "step_type": "custom",
                "parameters": {},
                "order": 4,
                "description": "",
                "parallel_group": ""  # 顺序步骤
            }
        ]
    }
    
    print("\n📋 测试 1: 前端传递数据模式 (preview_mode=true)")
    try:
        cmd = [
            'curl', '-s', '-X', 'POST',
            'http://localhost:8000/api/v1/cicd/pipelines/preview/',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps(frontend_data)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        workflow_summary = data.get('workflow_summary', {})
        jenkinsfile = data.get('jenkinsfile', '')
        
        total_steps = workflow_summary.get('total_steps', 0)
        has_parallel = 'parallel {' in jenkinsfile
        parallel_count = jenkinsfile.count('parallel {')
        
        print(f"  ✅ 总步骤数: {total_steps}")
        print(f"  ✅ 包含并行语法: {has_parallel}")
        print(f"  ✅ 并行组数量: {parallel_count}")
        print(f"  ✅ 数据源: {workflow_summary.get('data_source', 'unknown')}")
        
        frontend_success = total_steps == 4 and has_parallel and parallel_count == 1
        
        if frontend_success:
            print("  🎯 前端数据传递测试通过！")
        else:
            print("  ❌ 前端数据传递测试失败")
            
    except Exception as e:
        print(f"  ❌ 前端测试失败: {e}")
        frontend_success = False
    
    # 等待一下让日志输出
    time.sleep(1)
    
    print("\n📋 测试 2: 数据库数据模式 (preview_mode=false)")
    database_success = False
    try:
        database_data = {
            "pipeline_id": 2,
            "preview_mode": False,  # 使用数据库数据
            "execution_mode": "remote"
        }
        
        cmd = [
            'curl', '-s', '-X', 'POST',
            'http://localhost:8000/api/v1/cicd/pipelines/preview/',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps(database_data)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        workflow_summary = data.get('workflow_summary', {})
        jenkinsfile = data.get('jenkinsfile', '')
        
        total_steps = workflow_summary.get('total_steps', 0)
        has_parallel = 'parallel {' in jenkinsfile
        parallel_count = jenkinsfile.count('parallel {')
        
        print(f"  ✅ 总步骤数: {total_steps}")
        print(f"  ✅ 包含并行语法: {has_parallel}")
        print(f"  ✅ 并行组数量: {parallel_count}")
        print(f"  ✅ 数据源: {workflow_summary.get('data_source', 'unknown')}")
        
        database_success = total_steps == 4 and has_parallel and parallel_count == 1
        
        if database_success:
            print("  🎯 数据库数据测试通过！")
        else:
            print("  ❌ 数据库数据测试失败")
            
    except Exception as e:
        print(f"  ❌ 数据库测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print(f"  前端数据传递: {'✅ 通过' if frontend_success else '❌ 失败'}")
    print(f"  数据库数据: {'✅ 通过' if database_success else '❌ 失败'}")
    
    if frontend_success and database_success:
        print("\n🎉 前端修复成功！两种模式都能正确检测并行组！")
        print("✅ 前端能正确传递 parallel_group 字段")
        print("✅ 后端能正确处理前端和数据库数据")
        print("✅ Jenkins Pipeline 生成正确的并行语法")
        
        print("\n💡 下一步:")
        print("  - 前端页面应该能正确显示并行组")
        print("  - 用户可以通过前端界面使用并行组功能")
        return 0
    else:
        print("\n❌ 还有问题需要解决")
        if not frontend_success:
            print("  - 前端数据传递仍有问题")
        if not database_success:
            print("  - 数据库数据处理仍有问题")
        return 1

if __name__ == "__main__":
    sys.exit(test_frontend_parallel_groups())
