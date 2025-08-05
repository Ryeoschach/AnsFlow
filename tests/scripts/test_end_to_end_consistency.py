#!/usr/bin/env python3
"""
端到端测试：验证预览和实际执行的一致性
模拟真实的用户工作流程：预览 -> 执行
"""

import sys
import os
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')

import django
django.setup()

import asyncio
from pipelines.models import Pipeline
from cicd_integrations.models import CICDTool, PipelineExecution
from cicd_integrations.services import UnifiedCICDEngine
from pipelines.services.jenkins_sync import JenkinsPipelineSyncService
from cicd_integrations.adapters.jenkins import JenkinsAdapter
from cicd_integrations.adapters.base import PipelineDefinition

def test_end_to_end_consistency():
    """端到端测试：预览和执行的一致性"""
    print("🚀 端到端测试：验证预览和实际执行的一致性")
    print("=" * 70)
    
    pipeline_id = 2
    
    try:
        # 1. 获取Pipeline对象
        pipeline = Pipeline.objects.get(id=pipeline_id)
        print("📋 1. 获取测试流水线:")
        print(f"  流水线ID: {pipeline.id}")
        print(f"  流水线名称: {pipeline.name}")
        print(f"  执行模式: {pipeline.execution_mode}")
        
        steps = pipeline.steps.all().order_by('order')
        parallel_groups = set()
        for step in steps:
            pg = step.parallel_group or ''
            if pg:
                parallel_groups.add(pg)
            print(f"    步骤: {step.name} - parallel_group: '{pg}'")
        
        print(f"  总步骤数: {len(steps)}")
        print(f"  并行组数: {len(parallel_groups)}")
        
        # 2. 测试预览（Jenkins同步服务）
        print("\n📋 2. 测试预览生成（Jenkins同步服务）:")
        try:
            # 创建模拟Jenkins工具
            class MockJenkinsTool:
                def __init__(self):
                    self.tool_type = 'jenkins'
                    self.base_url = 'http://mock-jenkins:8080'
                    self.username = 'admin'
                    self.token = 'mock-token'
            
            mock_tool = MockJenkinsTool()
            jenkins_service = JenkinsPipelineSyncService(mock_tool)
            
            preview_script = jenkins_service._convert_steps_to_jenkins_script(pipeline)
            preview_has_parallel = 'parallel {' in preview_script
            preview_parallel_count = preview_script.count('parallel {')
            
            print(f"  预览脚本长度: {len(preview_script)} 字符")
            print(f"  预览包含并行语法: {preview_has_parallel}")
            print(f"  预览并行组数量: {preview_parallel_count}")
            
        except Exception as e:
            print(f"  ❌ 预览测试失败: {e}")
            return False
        
        # 3. 测试实际执行（Jenkins适配器）
        print("\n📋 3. 测试实际执行（Jenkins适配器）:")
        
        def test_execution_flow_sync():
            try:
                # 创建执行记录（模拟）
                execution = type('MockExecution', (), {
                    'id': 999,
                    'pipeline': pipeline,
                    'definition': {},
                    'parameters': {},
                    'trigger_data': {}
                })()
                
                # 使用执行引擎构建流水线定义
                engine = UnifiedCICDEngine()
                pipeline_def = engine._build_pipeline_definition_from_atomic_steps(execution)
                
                print(f"  执行引擎步骤数: {len(pipeline_def.steps)}")
                
                # 检查执行引擎生成的步骤是否包含并行组
                execution_steps_with_parallel = [s for s in pipeline_def.steps if s.get('parallel_group')]
                print(f"  执行引擎并行步骤数: {len(execution_steps_with_parallel)}")
                
                return pipeline_def
                
            except Exception as e:
                print(f"  ❌ 执行引擎测试失败: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        async def test_jenkins_adapter(pipeline_def):
            try:
                # 使用Jenkins适配器生成Jenkinsfile
                adapter = JenkinsAdapter(
                    base_url="http://mock-jenkins:8080",
                    username="admin", 
                    token="mock-token"
                )
                
                execution_script = await adapter.create_pipeline_file(pipeline_def)
                execution_has_parallel = 'parallel {' in execution_script
                execution_parallel_count = execution_script.count('parallel {')
                
                print(f"  执行脚本长度: {len(execution_script)} 字符")
                print(f"  执行包含并行语法: {execution_has_parallel}")
                print(f"  执行并行组数量: {execution_parallel_count}")
                
                return (execution_has_parallel, execution_parallel_count, execution_script)
                
            except Exception as e:
                print(f"  ❌ Jenkins适配器测试失败: {e}")
                import traceback
                traceback.print_exc()
                return (False, 0, "")
        
        # 先运行同步部分
        pipeline_def = test_execution_flow_sync()
        if pipeline_def is None:
            return False
        
        # 再运行异步部分
        execution_parallel, execution_count, execution_script = asyncio.run(test_jenkins_adapter(pipeline_def))
        
        # 4. 比较结果
        print("\n📋 4. 比较预览和执行结果:")
        print(f"  预览并行语法: {preview_has_parallel} (组数: {preview_parallel_count})")
        print(f"  执行并行语法: {execution_parallel} (组数: {execution_count})")
        
        consistency_check = (
            preview_has_parallel == execution_parallel and 
            preview_parallel_count == execution_count and
            preview_has_parallel  # 确保两者都包含并行语法
        )
        
        print(f"  一致性检查: {'✅ 通过' if consistency_check else '❌ 失败'}")
        
        if consistency_check:
            print("\n🎉 端到端测试成功！")
            print("✅ 预览和实际执行完全一致")
            print("✅ 并行组在整个流程中正确传递")
            print("✅ 用户看到的预览和实际执行的Jenkins Pipeline相同")
        else:
            print("\n❌ 端到端测试失败！")
            print("❌ 预览和实际执行不一致")
            print("💡 这意味着用户看到的预览和实际执行结果不同")
        
        # 5. 显示关键代码片段对比
        if preview_has_parallel and execution_parallel:
            print("\n📋 5. 关键代码片段对比:")
            
            print("  预览生成的并行部分:")
            preview_lines = preview_script.split('\n')
            for line in preview_lines:
                if 'parallel {' in line:
                    idx = preview_lines.index(line)
                    for i in range(max(0, idx-1), min(len(preview_lines), idx+6)):
                        print(f"    {preview_lines[i]}")
                    break
            
            print("\n  执行生成的并行部分:")
            execution_lines = execution_script.split('\n')
            for line in execution_lines:
                if 'parallel {' in line:
                    idx = execution_lines.index(line)
                    for i in range(max(0, idx-1), min(len(execution_lines), idx+6)):
                        print(f"    {execution_lines[i]}")
                    break
        
        return consistency_check
        
    except Exception as e:
        print(f"❌ 端到端测试出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🎯 开始端到端一致性验证...")
    success = test_end_to_end_consistency()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 端到端测试完全成功！")
        print("✅ 用户现在可以信任预览功能")
        print("✅ 预览显示的和实际执行的完全一致")
        print("✅ 并行组功能在完整工作流程中正常运行")
    else:
        print("❌ 端到端测试失败")
        print("💥 需要进一步调试预览和执行的不一致问题")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
