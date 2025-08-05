#!/usr/bin/env python3
"""
测试Jenkins适配器的并行组处理
"""

import sys
import os
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')

import django
django.setup()

import asyncio
from cicd_integrations.adapters.jenkins import JenkinsAdapter
from cicd_integrations.adapters.base import PipelineDefinition

def test_jenkins_adapter_parallel():
    """测试Jenkins适配器的并行组处理"""
    print("🔍 测试Jenkins适配器的并行组处理")
    print("=" * 60)
    
    # 使用真实的数据库数据
    from pipelines.models import Pipeline
    from cicd_integrations.services import UnifiedCICDEngine
    
    pipeline_id = 2
    pipeline = Pipeline.objects.get(id=pipeline_id)
    
    print(f"📋 1. 获取真实Pipeline数据 (ID: {pipeline_id}):")
    steps = pipeline.steps.all().order_by('order')
    
    parallel_groups = set()
    for step in steps:
        pg = step.parallel_group or ''
        if pg:
            parallel_groups.add(pg)
        print(f"    步骤: {step.name}, command: '{step.command}', parallel_group: '{pg}'")
    
    print(f"  总步骤数: {len(steps)}")
    print(f"  并行组数: {len(parallel_groups)}")
    
    # 使用执行引擎构建Pipeline定义
    print("\n📋 2. 构建Pipeline定义:")
    
    # 创建模拟执行记录
    execution = type('MockExecution', (), {
        'id': 999,
        'pipeline': pipeline,
        'definition': {},
        'parameters': {},
        'trigger_data': {}
    })()
    
    engine = UnifiedCICDEngine()
    pipeline_def = engine._build_pipeline_definition_from_atomic_steps(execution)
    
    print(f"  Pipeline定义步骤数: {len(pipeline_def.steps)}")
    
    # 显示构建的步骤详情
    for i, step in enumerate(pipeline_def.steps):
        print(f"    步骤{i+1}: {step.get('name')} - command: '{step.get('parameters', {}).get('command', 'None')}' - parallel_group: '{step.get('parallel_group', '')}'")
    
    # 创建Jenkins适配器
    print("\n📋 3. 测试Jenkins适配器:")
    
    adapter = JenkinsAdapter(
        base_url="http://mock-jenkins:8080",
        username="admin",
        token="mock-token"
    )
    
    async def test_create_pipeline_file():
        try:
            # 调用create_pipeline_file方法
            jenkinsfile_content = await adapter.create_pipeline_file(pipeline_def)
            
            print(f"  Jenkinsfile长度: {len(jenkinsfile_content)} 字符")
            
            # 检查并行语法
            has_parallel = 'parallel {' in jenkinsfile_content
            parallel_count = jenkinsfile_content.count('parallel {')
            
            print(f"  包含并行语法: {has_parallel}")
            print(f"  并行组数量: {parallel_count}")
            
            # 输出关键部分
            if has_parallel:
                print("\n📋 3. Jenkinsfile并行部分:")
                lines = jenkinsfile_content.split('\n')
                in_parallel = False
                parallel_lines = []
                
                for line in lines:
                    if 'parallel {' in line:
                        in_parallel = True
                        parallel_lines.append(line)
                    elif in_parallel:
                        parallel_lines.append(line)
                        if line.strip().endswith('}') and 'stage(' not in line and 'steps {' not in line:
                            # 可能是parallel块的结束
                            break
                
                for line in parallel_lines[:15]:  # 显示前15行
                    print(f"    {line}")
                if len(parallel_lines) > 15:
                    print(f"    ... 还有 {len(parallel_lines) - 15} 行")
            else:
                print("\n❌ Jenkinsfile中没有并行语法!")
                print("\n📋 3. Jenkinsfile内容预览:")
                lines = jenkinsfile_content.split('\n')
                for i, line in enumerate(lines[:25]):  # 显示前25行
                    print(f"    {i+1:2d}: {line}")
                if len(lines) > 25:
                    print(f"    ... 还有 {len(lines) - 25} 行")
            
            return has_parallel and parallel_count > 0
            
        except Exception as e:
            print(f"  ❌ Jenkins适配器测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # 运行异步测试
    success = asyncio.run(test_create_pipeline_file())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Jenkins适配器能正确处理并行组")
    else:
        print("❌ Jenkins适配器没有正确处理并行组")
        print("\n💡 可能的原因:")
        print("  1. _convert_atomic_steps_to_jenkinsfile方法没有正确处理并行组")
        print("  2. parallel_group字段未正确传递")
        print("  3. 并行语法生成有问题")
    
    return success

def main():
    """主函数"""
    success = test_jenkins_adapter_parallel()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
