#!/usr/bin/env python3
"""
测试执行引擎修复后的并行组处理
"""
import os
import sys
import django
import traceback

# 配置Django环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from cicd_integrations.models import PipelineExecution
from cicd_integrations.services import UnifiedCICDEngine


def test_execution_engine_parallel_groups():
    """测试执行引擎并行组处理"""
    print("🔍 测试修复后的执行引擎并行组处理")
    print("=" * 60)
    
    # 查找包含并行组的测试流水线
    pipeline = Pipeline.objects.filter(name__icontains="jenkins并行测试").first()
    if not pipeline:
        print("❌ 未找到测试流水线")
        return False
    
    # 检查流水线步骤
    print("📋 1. 检查Pipeline步骤数据:")
    steps = list(pipeline.steps.all().order_by('order'))
    print(f"  总步骤数: {len(steps)}")
    
    parallel_groups = set()
    for step in steps:
        pg = step.parallel_group or ''
        if pg:
            parallel_groups.add(pg)
        print(f"    步骤: {step.name}, order: {step.order}, parallel_group: '{pg}'")
    
    print(f"  并行组数: {len(parallel_groups)}")
    
    # 测试执行引擎
    print("📋 2. 测试执行引擎的流水线定义构建:")
    try:
        # 创建一个真实的执行记录
        execution = PipelineExecution.objects.create(
            pipeline=pipeline,
            status='pending',
            parameters={}
        )
        
        # 调用流水线定义构建方法
        engine = UnifiedCICDEngine()
        pipeline_definition = engine._build_pipeline_definition_from_atomic_steps(execution)
        
        print(f"  流水线定义包含 {len(pipeline_definition.steps)} 个步骤")
        
        # 检查并行组信息
        definition_parallel_groups = set()
        for step in pipeline_definition.steps:
            pg = step.get('parallel_group', '')
            if pg:
                definition_parallel_groups.add(pg)
            print(f"    定义步骤: {step['name']}, parallel_group: '{pg}'")
        
        print(f"  定义中的并行组数: {len(definition_parallel_groups)}")
        
        # 验证
        if len(definition_parallel_groups) == len(parallel_groups) and definition_parallel_groups == parallel_groups:
            print("  ✅ 执行引擎正确保留了并行组信息!")
            success = True
        else:
            print("  ❌ 执行引擎未正确保留并行组信息")
            print(f"    原始并行组: {parallel_groups}")
            print(f"    定义并行组: {definition_parallel_groups}")
            success = False
            
        # 清理测试数据
        execution.delete()
        return success
        
    except Exception as e:
        print(f"  ❌ 执行引擎测试失败: {e}")
        traceback.print_exc()
        return False


def test_jenkins_generation():
    """测试Jenkins脚本生成"""
    print("\n📋 3. 测试Jenkins Pipeline脚本生成:")
    
    pipeline = Pipeline.objects.filter(name__icontains="jenkins并行测试").first()
    if not pipeline:
        print("❌ 未找到测试流水线")
        return False
    
    try:
        from pipelines.services.jenkins_sync import JenkinsPipelineSyncService
        
        # 创建Jenkins同步服务
        jenkins_service = JenkinsPipelineSyncService()
        
        # 生成Jenkins Pipeline脚本
        jenkins_script = jenkins_service.generate_jenkins_pipeline(pipeline)
        
        print(f"  生成的Jenkins脚本长度: {len(jenkins_script)} 字符")
        
        # 检查脚本中是否包含parallel关键字
        if 'parallel' in jenkins_script.lower():
            print("  ✅ Jenkins脚本包含parallel关键字")
            
            # 显示parallel相关的行
            lines = jenkins_script.split('\n')
            parallel_lines = [line.strip() for line in lines if 'parallel' in line.lower()]
            for line in parallel_lines[:3]:  # 只显示前3行
                print(f"    {line}")
            
            return True
        else:
            print("  ❌ Jenkins脚本不包含parallel关键字")
            print(f"  脚本预览:\n{jenkins_script[:500]}...")
            return False
            
    except Exception as e:
        print(f"  ❌ Jenkins脚本生成失败: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 运行测试
    engine_success = test_execution_engine_parallel_groups()
    jenkins_success = test_jenkins_generation()
    
    print("\n" + "=" * 60)
    if engine_success and jenkins_success:
        print("✅ 所有测试通过！并行组功能工作正常")
    else:
        print("❌ 仍有问题需要解决")
        if not engine_success:
            print("  - 执行引擎并行组处理有问题")
        if not jenkins_success:
            print("  - Jenkins脚本生成有问题")
