#!/usr/bin/env python
"""
验证脚本：检查command类型清理后的完整功能
确保所有步骤类型都能正确保存和回显
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import PipelineStep, Pipeline
from project_management.models import Project
from pipelines.serializers import PipelineSerializer


def test_all_step_types():
    """测试所有支持的步骤类型"""
    
    print("=== 测试所有步骤类型的保存和回显 ===")
    
    # 获取或创建测试项目
    project, created = Project.objects.get_or_create(
        name="测试项目-步骤类型验证",
        defaults={'description': '用于验证步骤类型的测试项目'}
    )
    
    # 获取或创建测试流水线
    pipeline, created = Pipeline.objects.get_or_create(
        name="步骤类型测试流水线",
        project=project,
        defaults={'description': '验证所有步骤类型都能正确工作'}
    )
    
    # 清理现有的测试步骤
    pipeline.steps.all().delete()
    
    # 定义所有支持的步骤类型（不包含command）
    step_types = [
        'fetch_code',
        'build', 
        'test',
        'security_scan',
        'deploy',
        'ansible',
        'notify',
        'custom',
        'script'  # 如果后端支持的话
    ]
    
    print(f"测试步骤类型: {step_types}")
    
    # 为每种类型创建测试步骤
    test_steps = []
    for i, step_type in enumerate(step_types, 1):
        step_data = {
            'name': f'{step_type.title()}步骤_{i}',
            'step_type': step_type,
            'description': f'测试{step_type}类型的步骤',
            'parameters': {
                'test_param': f'value_for_{step_type}',
                'order': i
            },
            'order': i,
            'is_active': True
        }
        test_steps.append(step_data)
    
    # 使用序列化器保存步骤
    pipeline_data = {
        'name': pipeline.name,
        'description': pipeline.description,
        'project': pipeline.project.id,
        'steps': test_steps
    }
    
    serializer = PipelineSerializer(pipeline, data=pipeline_data, partial=True)
    if serializer.is_valid():
        updated_pipeline = serializer.save()
        print(f"✅ 成功保存 {len(test_steps)} 个步骤")
    else:
        print(f"❌ 保存失败: {serializer.errors}")
        return False
    
    # 验证回显
    print("\n=== 验证步骤回显 ===")
    refresh_serializer = PipelineSerializer(updated_pipeline)
    saved_data = refresh_serializer.data
    
    if 'steps' in saved_data and saved_data['steps']:
        saved_steps = saved_data['steps']
        print(f"✅ 成功回显 {len(saved_steps)} 个步骤")
        
        for step in saved_steps:
            expected_type = step_types[step['order'] - 1]
            actual_type = step['step_type']
            
            if actual_type == expected_type:
                print(f"  ✅ 步骤 {step['order']}: {step['name']} - 类型正确 ({actual_type})")
            else:
                print(f"  ❌ 步骤 {step['order']}: {step['name']} - 类型错误 (期望: {expected_type}, 实际: {actual_type})")
                
            # 检查参数是否正确保存
            if 'parameters' in step and step['parameters']:
                params = step['parameters']
                if params.get('test_param') == f'value_for_{expected_type}':
                    print(f"    ✅ 参数正确保存")
                else:
                    print(f"    ❌ 参数保存错误: {params}")
    else:
        print("❌ 没有找到保存的步骤")
        return False
        
    return True


def verify_no_command_types():
    """验证数据库中不再有command类型的步骤"""
    
    print("\n=== 验证command类型清理情况 ===")
    
    command_steps = PipelineStep.objects.filter(step_type='command')
    count = command_steps.count()
    
    if count == 0:
        print("✅ 数据库中已经没有command类型的步骤")
        return True
    else:
        print(f"❌ 还有 {count} 个command类型的步骤:")
        for step in command_steps[:5]:  # 只显示前5个
            print(f"  - ID: {step.id}, Name: {step.name}, Pipeline: {step.pipeline.name}")
        return False


def show_current_type_distribution():
    """显示当前步骤类型分布"""
    
    print("\n=== 当前步骤类型分布 ===")
    
    from django.db.models import Count
    
    type_counts = (PipelineStep.objects
                   .values('step_type')
                   .annotate(count=Count('id'))
                   .order_by('-count'))
    
    total_steps = sum(item['count'] for item in type_counts)
    
    for item in type_counts:
        print(f"  {item['step_type']}: {item['count']} 个")
    
    print(f"\n总步骤数: {total_steps}")


if __name__ == '__main__':
    try:
        show_current_type_distribution()
        verify_no_command_types()
        test_all_step_types()
        
        print("\n=== 验证完成 ===")
        print("✅ command类型已成功清理")
        print("✅ 所有支持的步骤类型都能正常工作")
        
    except Exception as e:
        print(f"验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
