#!/usr/bin/env python3
"""
测试预览API vs Jenkins同步的数据差异
"""

import sys
import os
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')

import django
django.setup()

from pipelines.models import Pipeline
from pipelines.services.jenkins_sync import JenkinsPipelineSyncService
from cicd_integrations.models import CICDTool

def test_jenkins_sync_vs_preview():
    """比较Jenkins同步和预览API使用的数据"""
    print("🔍 测试Jenkins同步 vs 预览API的数据差异")
    print("=" * 60)
    
    pipeline_id = 2
    
    # 获取Pipeline对象
    pipeline = Pipeline.objects.get(id=pipeline_id)
    
    print("📋 1. 检查Pipeline步骤数据:")
    steps = pipeline.steps.all().order_by('order')
    print(f"  总步骤数: {len(steps)}")
    
    parallel_groups = set()
    for step in steps:
        pg = step.parallel_group or ''
        if pg:
            parallel_groups.add(pg)
        print(f"    步骤: {step.name}, order: {step.order}, parallel_group: '{pg}'")
    
    print(f"  并行组数: {len(parallel_groups)}")
    
    # 创建Jenkins同步服务
    print("\n📋 2. 模拟Jenkins同步过程:")
    try:
        # 创建一个模拟的Jenkins工具
        class MockJenkinsTool:
            def __init__(self):
                self.tool_type = 'jenkins'
                self.base_url = 'http://mock-jenkins:8080'
                self.username = 'admin'
                self.token = 'mock-token'
        
        mock_tool = MockJenkinsTool()
        jenkins_service = JenkinsPipelineSyncService(mock_tool)
        
        # 调用Jenkins Pipeline脚本生成
        pipeline_script = jenkins_service._convert_steps_to_jenkins_script(pipeline)
        
        print(f"  Jenkins脚本长度: {len(pipeline_script)} 字符")
        
        # 检查并行语法
        has_parallel = 'parallel {' in pipeline_script
        parallel_count = pipeline_script.count('parallel {')
        
        print(f"  包含并行语法: {has_parallel}")
        print(f"  并行组数量: {parallel_count}")
        
        # 输出关键部分
        if has_parallel:
            print("\n📋 3. Jenkins Pipeline并行部分:")
            lines = pipeline_script.split('\n')
            in_parallel = False
            parallel_lines = []
            
            for line in lines:
                if 'parallel {' in line:
                    in_parallel = True
                    parallel_lines.append(line)
                elif in_parallel:
                    parallel_lines.append(line)
                    if line.strip().endswith('}') and len(line.strip()) == 1:
                        # 可能是parallel块的结束
                        break
            
            for line in parallel_lines[:10]:  # 只显示前10行
                print(f"    {line}")
            if len(parallel_lines) > 10:
                print(f"    ... 还有 {len(parallel_lines) - 10} 行")
        else:
            print("\n❌ Jenkins Pipeline中没有并行语法!")
            print("\n📋 3. Jenkins Pipeline内容预览:")
            lines = pipeline_script.split('\n')
            for i, line in enumerate(lines[:20]):  # 显示前20行
                print(f"    {i+1:2d}: {line}")
            if len(lines) > 20:
                print(f"    ... 还有 {len(lines) - 20} 行")
        
        return has_parallel and parallel_count > 0
        
    except Exception as e:
        print(f"  ❌ Jenkins同步测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    success = test_jenkins_sync_vs_preview()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Jenkins同步能正确处理并行组")
    else:
        print("❌ Jenkins同步没有正确处理并行组")
        print("\n💡 可能的原因:")
        print("  1. Jenkins同步服务的数据获取方式不同")
        print("  2. _analyze_execution_plan方法有问题")
        print("  3. 并行组字段未正确传递到Jenkins同步")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
