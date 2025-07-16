#!/usr/bin/env python
"""
测试新建流水线的PipelineStep命令配置
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from pipelines.serializers import PipelineSerializer
from project_management.models import Project
from django.contrib.auth.models import User

def test_pipeline_creation():
    """测试创建新流水线时PipelineStep的command字段是否正确设置"""
    
    # 获取项目和用户
    project = Project.objects.first()
    user = User.objects.first()
    
    if not project or not user:
        print('❌ 需要先创建项目和用户')
        return
    
    print(f'✅ 使用项目: {project.name}')
    print(f'✅ 使用用户: {user.username}')
    
    # 准备测试数据
    test_data = {
        'name': '测试命令修复流水线',
        'description': '测试PipelineStep命令字段修复',
        'project': project.id,
        'execution_mode': 'local',
        'steps': [
            {
                'name': '测试步骤1',
                'step_type': 'custom',
                'order': 1,
                'parameters': {
                    'command': 'echo "Hello from step 1"'
                }
            },
            {
                'name': '测试步骤2',
                'step_type': 'custom',
                'order': 2,
                'parameters': {
                    'command': 'echo "Hello from step 2" && sleep 3'
                },
                'parallel_group': 'test_group'
            },
            {
                'name': '测试步骤3',
                'step_type': 'custom',
                'order': 3,
                'parameters': {
                    'command': 'echo "Hello from step 3" && sleep 2'
                },
                'parallel_group': 'test_group'
            }
        ]
    }
    
    print('\\n=== 创建测试流水线 ===')
    
    # 创建流水线
    serializer = PipelineSerializer(data=test_data, context={'request': type('Request', (), {'user': user})()})
    if serializer.is_valid():
        pipeline = serializer.save()
        print(f'✅ 成功创建流水线: {pipeline.name} (ID: {pipeline.id})')
        
        # 检查PipelineStep
        pipeline_steps = pipeline.steps.all().order_by('order')
        print(f'\\n=== 验证PipelineStep配置 ===')
        
        for step in pipeline_steps:
            print(f'步骤 {step.order}: {step.name}')
            print(f'  命令: "{step.command}"')
            print(f'  并行组: {step.parallel_group}')
            print(f'  参数: {step.ansible_parameters}')
            print()
        
        # 统计结果
        steps_with_command = [s for s in pipeline_steps if s.command]
        steps_with_parallel = [s for s in pipeline_steps if s.parallel_group]
        
        print(f'📊 总步骤数: {pipeline_steps.count()}')
        print(f'📊 有命令的步骤数: {len(steps_with_command)}')
        print(f'📊 有并行组的步骤数: {len(steps_with_parallel)}')
        
        if len(steps_with_command) == pipeline_steps.count():
            print('✅ 所有PipelineStep都有命令配置！')
        else:
            missing = pipeline_steps.count() - len(steps_with_command)
            print(f'❌ {missing} 个PipelineStep缺少命令配置')
        
        # 检查并行组
        if steps_with_parallel:
            parallel_groups = set(s.parallel_group for s in steps_with_parallel)
            print(f'✅ 检测到并行组: {parallel_groups}')
        else:
            print('⚠️ 没有检测到并行组')
            
        return pipeline
    else:
        print(f'❌ 流水线创建失败: {serializer.errors}')
        return None

if __name__ == '__main__':
    pipeline = test_pipeline_creation()
    if pipeline:
        print(f'\\n🎉 测试完成，流水线ID: {pipeline.id}')
        print('现在你可以在页面上执行这个流水线来测试命令是否正常工作！')
    else:
        print('\\n❌ 测试失败')
