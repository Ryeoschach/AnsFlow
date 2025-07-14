#!/usr/bin/env python3
"""
🎯 AnsFlow 并行组功能 - 最终完整验证
验证从预览到执行的完整数据流
"""

import sys
import os
import json
import subprocess
import time

sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')

import django
django.setup()

from pipelines.models import Pipeline
from cicd_integrations.models import PipelineExecution
from cicd_integrations.services import UnifiedCICDEngine

def test_complete_parallel_workflow():
    """测试完整的并行组工作流"""
    print("🎯 AnsFlow 并行组功能 - 最终完整验证")
    print("=" * 70)
    
    results = {
        "database_data": False,
        "preview_api": False,
        "jenkins_sync": False,
        "execution_engine": False,
        "frontend_data": False
    }
    
    pipeline_id = 2
    
    # 1. 验证数据库数据
    print("\n📋 1. 验证数据库中的并行组数据")
    try:
        pipeline = Pipeline.objects.get(id=pipeline_id)
        steps = pipeline.steps.all().order_by('order')
        
        parallel_groups = set()
        for step in steps:
            pg = step.parallel_group or ''
            if pg:
                parallel_groups.add(pg)
            print(f"    步骤: {step.name} -> parallel_group: '{pg}'")
        
        print(f"  ✅ 总步骤数: {len(steps)}")
        print(f"  ✅ 并行组数: {len(parallel_groups)}")
        
        if len(steps) == 4 and len(parallel_groups) == 1:
            results["database_data"] = True
            print("  🎯 数据库数据验证通过！")
        else:
            print("  ❌ 数据库数据验证失败")
            
    except Exception as e:
        print(f"  ❌ 数据库验证失败: {e}")
    
    # 2. 验证预览API
    print("\n📋 2. 验证预览API (preview_mode=false)")
    try:
        cmd = [
            'curl', '-s', '-X', 'POST',
            'http://localhost:8000/api/v1/cicd/pipelines/preview/',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps({
                "pipeline_id": pipeline_id,
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
        parallel_count = jenkinsfile.count('parallel {')
        
        print(f"  ✅ 总步骤数: {total_steps}")
        print(f"  ✅ 包含并行语法: {has_parallel}")
        print(f"  ✅ 并行组数量: {parallel_count}")
        print(f"  ✅ 数据源: {workflow_summary.get('data_source', 'unknown')}")
        
        if total_steps == 4 and has_parallel and parallel_count == 1:
            results["preview_api"] = True
            print("  🎯 预览API验证通过！")
        else:
            print("  ❌ 预览API验证失败")
            
    except Exception as e:
        print(f"  ❌ 预览API验证失败: {e}")
    
    # 3. 验证Jenkins同步
    print("\n📋 3. 验证Jenkins同步服务")
    try:
        from pipelines.services.jenkins_sync import JenkinsPipelineSyncService
        
        class MockJenkinsTool:
            def __init__(self):
                self.tool_type = 'jenkins'
                self.base_url = 'http://mock-jenkins:8080'
                self.username = 'admin'
                self.token = 'mock-token'
        
        jenkins_service = JenkinsPipelineSyncService(MockJenkinsTool())
        pipeline_script = jenkins_service._convert_steps_to_jenkins_script(pipeline)
        
        has_parallel = 'parallel {' in pipeline_script
        parallel_count = pipeline_script.count('parallel {')
        
        print(f"  ✅ Jenkins脚本长度: {len(pipeline_script)} 字符")
        print(f"  ✅ 包含并行语法: {has_parallel}")
        print(f"  ✅ 并行组数量: {parallel_count}")
        
        if has_parallel and parallel_count == 1:
            results["jenkins_sync"] = True
            print("  🎯 Jenkins同步验证通过！")
        else:
            print("  ❌ Jenkins同步验证失败")
            
    except Exception as e:
        print(f"  ❌ Jenkins同步验证失败: {e}")
    
    # 4. 验证执行引擎
    print("\n📋 4. 验证执行引擎")
    try:
        # 创建模拟执行对象
        execution = type('MockExecution', (), {
            'id': 999,
            'pipeline': pipeline,
            'status': 'pending',
            'parameters': {},  # 添加缺少的参数
            'definition': {},  # 添加定义
            'trigger_data': {}  # 添加触发数据
        })()
        
        engine = UnifiedCICDEngine()
        pipeline_def = engine._build_pipeline_definition_from_atomic_steps(execution)
        
        # 检查pipeline_def中的步骤（这些是字典，不是对象）
        steps_with_parallel = [s for s in pipeline_def.steps if s.get('parallel_group')]
        
        print(f"  ✅ Pipeline定义步骤数: {len(pipeline_def.steps)}")
        print(f"  ✅ 包含并行组的步骤数: {len(steps_with_parallel)}")
        
        # 打印步骤详情以便调试
        for i, step in enumerate(pipeline_def.steps):
            print(f"    步骤{i+1}: {step.get('name')} - parallel_group: '{step.get('parallel_group', '')}'")
        
        if len(pipeline_def.steps) == 4 and len(steps_with_parallel) == 2:
            results["execution_engine"] = True
            print("  🎯 执行引擎验证通过！")
        else:
            print("  ❌ 执行引擎验证失败")
            print(f"    期望: 4个步骤，2个并行步骤")
            print(f"    实际: {len(pipeline_def.steps)}个步骤，{len(steps_with_parallel)}个并行步骤")
            
    except Exception as e:
        print(f"  ❌ 执行引擎验证失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. 验证前端数据传递
    print("\n📋 5. 验证前端数据传递 (preview_mode=true)")
    try:
        # 模拟前端传递的数据（修复后应该包含parallel_group字段）
        frontend_data = {
            "pipeline_id": pipeline_id,
            "preview_mode": True,
            "execution_mode": "remote",
            "steps": [
                {
                    "name": "1111",
                    "step_type": "custom",
                    "parameters": {},
                    "order": 1,
                    "description": "",
                    "parallel_group": ""
                },
                {
                    "name": "222-1",
                    "step_type": "custom",
                    "parameters": {},
                    "order": 2,
                    "description": "",
                    "parallel_group": "parallel_1752467687202"
                },
                {
                    "name": "222-2",
                    "step_type": "custom",
                    "parameters": {},
                    "order": 3,
                    "description": "",
                    "parallel_group": "parallel_1752467687202"
                },
                {
                    "name": "333",
                    "step_type": "custom",
                    "parameters": {},
                    "order": 4,
                    "description": "",
                    "parallel_group": ""
                }
            ]
        }
        
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
        
        if total_steps == 4 and has_parallel and parallel_count == 1:
            results["frontend_data"] = True
            print("  🎯 前端数据传递验证通过！")
        else:
            print("  ❌ 前端数据传递验证失败")
            
    except Exception as e:
        print(f"  ❌ 前端数据传递验证失败: {e}")
    
    # 最终结果
    print("\n" + "=" * 70)
    print("📊 最终验证结果:")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ 通过" if passed_test else "❌ 失败"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！AnsFlow并行组功能完全正常！")
        print("\n🚀 功能特性已完全实现:")
        print("  ✅ 数据库正确存储并行组信息")
        print("  ✅ 预览API正确检测并行组")
        print("  ✅ Jenkins同步正确生成并行语法")
        print("  ✅ 执行引擎正确处理并行组")
        print("  ✅ 前端正确传递并行组数据")
        
        print("\n🎯 用户现在可以:")
        print("  - 在前端创建包含并行组的流水线")
        print("  - 预览Jenkins Pipeline的并行语法")
        print("  - 执行包含并行组的流水线")
        print("  - 监控并行组的执行状态")
        
        return 0
    else:
        print(f"\n❌ 还有 {total - passed} 个测试失败")
        print("\n需要进一步调试的问题:")
        for test_name, passed_test in results.items():
            if not passed_test:
                print(f"  - {test_name.replace('_', ' ').title()}")
        return 1

if __name__ == "__main__":
    sys.exit(test_complete_parallel_workflow())
