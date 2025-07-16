#!/usr/bin/env python3
"""
创建带有并行组的测试数据
"""

import os
import sys
import django
from django.conf import settings

# 设置Django环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from pipelines.models import Pipeline
from cicd_integrations.models import AtomicStep
from django.contrib.auth.models import User
from project_management.models import Project

def create_test_data():
    """创建测试数据"""
    print("🔧 创建测试数据...")
    
    # 获取或创建测试用户
    user, created = User.objects.get_or_create(
        username='frontend_test_user',
        defaults={'email': 'frontend_test@example.com'}
    )
    
    # 创建测试项目
    project, created = Project.objects.get_or_create(
        name='前端测试项目',
        defaults={'description': '用于测试前端并行组功能的项目', 'owner': user}
    )
    
    # 创建测试流水线
    pipeline, created = Pipeline.objects.get_or_create(
        name='前端并行组测试流水线',
        defaults={
            'description': '测试前端并行组功能',
            'project': project,
            'created_by': user,
            'execution_mode': 'local'
        }
    )
    
    # 清除现有步骤
    AtomicStep.objects.filter(pipeline=pipeline).delete()
    
    # 创建测试步骤
    steps_config = [
        {'name': 'Step1-初始化', 'order': 1, 'parallel_group': '', 'step_type': 'custom'},
        {'name': 'Step2-构建前端', 'order': 2, 'parallel_group': 'build_group', 'step_type': 'build'},
        {'name': 'Step3-构建后端', 'order': 3, 'parallel_group': 'build_group', 'step_type': 'build'},
        {'name': 'Step4-单元测试', 'order': 4, 'parallel_group': 'test_group', 'step_type': 'test'},
        {'name': 'Step5-集成测试', 'order': 5, 'parallel_group': 'test_group', 'step_type': 'test'},
        {'name': 'Step6-部署', 'order': 6, 'parallel_group': '', 'step_type': 'deploy'},
    ]
    
    for step_config in steps_config:
        step = AtomicStep.objects.create(
            pipeline=pipeline,
            name=step_config['name'],
            order=step_config['order'],
            parallel_group=step_config['parallel_group'],
            step_type=step_config['step_type'],
            description=f"测试步骤: {step_config['name']}",
            created_by=user,
            config={'command': f'echo "执行 {step_config["name"]}" && sleep 2'}
        )
        print(f"  ✅ 创建步骤: {step.name} (并行组: {step.parallel_group or '无'})")
    
    print(f"\n✅ 测试数据创建完成!")
    print(f"流水线ID: {pipeline.id}")
    print(f"流水线名称: {pipeline.name}")
    print(f"包含 {AtomicStep.objects.filter(pipeline=pipeline).count()} 个步骤")
    print(f"前端访问地址: http://localhost:5173/pipelines")
    
    return pipeline

if __name__ == '__main__':
    try:
        pipeline = create_test_data()
        print("\n🎯 测试说明:")
        print("1. 打开前端页面: http://localhost:5173/pipelines")
        print("2. 找到流水线: 前端并行组测试流水线")
        print("3. 点击编辑按钮，查看步骤配置")
        print("4. 验证并行组字段是否正确显示")
        print("5. 尝试修改并行组配置")
        print("6. 执行流水线，验证并行执行效果")
    except Exception as e:
        print(f"\n❌ 创建测试数据失败: {e}")
        import traceback
        traceback.print_exc()
