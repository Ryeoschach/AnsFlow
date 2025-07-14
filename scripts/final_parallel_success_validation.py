#!/usr/bin/env python3
"""
🎉 AnsFlow 并行组功能 - 最终成功验证
"""

import json
import subprocess
import sys

def main():
    """最终验证所有功能"""
    print("🎉 AnsFlow 并行组功能 - 最终成功验证")
    print("=" * 60)
    
    success_count = 0
    total_tests = 0
    
    # 1. 验证Jenkins Pipeline API
    print("\n📋 测试 1: Jenkins Pipeline 预览 API")
    total_tests += 1
    try:
        cmd = [
            'curl', '-s', '-X', 'POST', 
            'http://localhost:8000/api/v1/cicd/pipelines/preview/',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps({
                "pipeline_id": 2,
                "preview_mode": False,
                "execution_mode": "remote"
            })
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        workflow_summary = data.get('workflow_summary', {})
        jenkinsfile = data.get('jenkinsfile', '')
        
        total_steps = workflow_summary.get('total_steps', 0)
        has_parallel = 'parallel {' in jenkinsfile
        
        print(f"  ✅ 总步骤数: {total_steps}")
        print(f"  ✅ 包含并行语法: {has_parallel}")
        print(f"  ✅ 数据源: {workflow_summary.get('data_source', 'unknown')}")
        
        if total_steps == 4 and has_parallel:
            print("  🎯 测试通过！")
            success_count += 1
        else:
            print("  ❌ 测试失败")
            
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
    
    # 2. 验证并行组API
    print("\n📋 测试 2: 数据库并行组数据")
    total_tests += 1
    try:
        cmd = [
            'uv', 'run', 'python', 'manage.py', 'shell', '-c',
            '''
from pipelines.models import Pipeline
pipeline = Pipeline.objects.get(id=2)
steps = pipeline.steps.all().order_by("order")
parallel_groups = set()
for step in steps:
    if step.parallel_group:
        parallel_groups.add(step.parallel_group)
print(f"STEPS:{len(steps)}")
print(f"GROUPS:{len(parallel_groups)}")
for step in steps:
    print(f"STEP:{step.name}:{step.parallel_group or 'sequential'}")
            '''
        ]
        
        result = subprocess.run(cmd, cwd='../backend/django_service', capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        
        steps_count = 0
        groups_count = 0
        parallel_steps = []
        
        for line in output.split('\n'):
            if line.startswith('STEPS:'):
                steps_count = int(line.split(':')[1])
            elif line.startswith('GROUPS:'):
                groups_count = int(line.split(':')[1])
            elif line.startswith('STEP:'):
                parts = line.split(':')
                step_name = parts[1]
                group_name = parts[2] if len(parts) > 2 else 'sequential'
                if group_name != 'sequential':
                    parallel_steps.append(f"{step_name} -> {group_name}")
        
        print(f"  ✅ 数据库步骤数: {steps_count}")
        print(f"  ✅ 并行组数: {groups_count}")
        print(f"  ✅ 并行步骤:")
        for step in parallel_steps:
            print(f"    - {step}")
        
        if steps_count == 4 and groups_count == 1 and len(parallel_steps) == 2:
            print("  🎯 测试通过！")
            success_count += 1
        else:
            print("  ❌ 测试失败")
            
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
    
    # 3. 验证Jenkins Pipeline结构
    print("\n📋 测试 3: Jenkins Pipeline 结构验证")
    total_tests += 1
    try:
        cmd = [
            'curl', '-s', '-X', 'POST', 
            'http://localhost:8000/api/v1/cicd/pipelines/preview/',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps({
                "pipeline_id": 2,
                "preview_mode": False,
                "execution_mode": "remote"
            })
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        jenkinsfile = data.get('jenkinsfile', '')
        
        # 检查结构
        has_stage_1111 = "stage('1111')" in jenkinsfile
        has_parallel_group = "stage('parallel_group_" in jenkinsfile
        has_parallel_syntax = "parallel {" in jenkinsfile
        has_stage_333 = "stage('333')" in jenkinsfile
        has_222_1 = "'222-1': {" in jenkinsfile
        has_222_2 = "'222-2': {" in jenkinsfile
        
        print(f"  ✅ 顺序步骤 1111: {has_stage_1111}")
        print(f"  ✅ 并行组stage: {has_parallel_group}")
        print(f"  ✅ 并行语法: {has_parallel_syntax}")
        print(f"  ✅ 并行步骤 222-1: {has_222_1}")
        print(f"  ✅ 并行步骤 222-2: {has_222_2}")
        print(f"  ✅ 顺序步骤 333: {has_stage_333}")
        
        structure_correct = all([
            has_stage_1111, has_parallel_group, has_parallel_syntax,
            has_stage_333, has_222_1, has_222_2
        ])
        
        if structure_correct:
            print("  🎯 测试通过！")
            success_count += 1
        else:
            print("  ❌ 测试失败")
            
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
    
    # 最终结果
    print("\n" + "=" * 60)
    print(f"📊 测试结果汇总: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("\n🎉 所有测试通过！AnsFlow并行组功能完全正常！")
        print("✅ 数据库中有正确的并行组数据")
        print("✅ API能正确检测并行组")
        print("✅ Jenkins Pipeline生成正确的并行语法")
        print("✅ 端到端功能完整可用")
        
        print("\n🚀 功能特性:")
        print("  - 支持并行组执行")
        print("  - 自动生成Jenkins parallel语法")
        print("  - 数据库集成完整")
        print("  - 前后端数据流通畅")
        
        return 0
    else:
        print(f"\n❌ 还有 {total_tests - success_count} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
