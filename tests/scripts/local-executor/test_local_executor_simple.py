#!/usr/bin/env python
"""
简单测试本地执行器
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from django.contrib.auth.models import User
from project_management.models import Project
from pipelines.models import Pipeline, PipelineStep
from cicd_integrations.models import CICDTool, PipelineExecution
from cicd_integrations.services import UnifiedCICDEngine


def test_local_executor():
    """测试本地执行器"""
    print("🔧 开始测试本地执行器...")
    
    # 1. 检查本地执行器工具是否存在
    try:
        local_tool = CICDTool.objects.get(tool_type='local')
        print(f"✅ 找到本地执行器工具: {local_tool.name}")
    except CICDTool.DoesNotExist:
        print("❌ 本地执行器工具不存在!")
        return False
    
    # 2. 获取或创建测试项目
    test_user = User.objects.get(username='admin')
    project, created = Project.objects.get_or_create(
        name='测试项目',
        defaults={'owner': test_user}
    )
    print(f"✅ 找到测试项目: {project.name}")
    
    # 3. 创建测试流水线
    pipeline, created = Pipeline.objects.get_or_create(
        name='本地执行器测试流水线',
        defaults={
            'project': project,
            'git_repo': 'https://github.com/test/repo.git',
            'git_branch': 'main',
            'execution_mode': 'local',
            'cicd_tool': local_tool,
            'description': '测试本地执行器的流水线'
        }
    )
    
    if created:
        print(f"✅ 创建了测试流水线: {pipeline.name}")
    else:
        print(f"✅ 找到测试流水线: {pipeline.name}")
    
    # 4. 清理旧的步骤
    pipeline.steps.all().delete()
    
    # 5. 创建一个简单的测试步骤（更容易成功）
    test_step = PipelineStep.objects.create(
        pipeline=pipeline,
        name='简单测试步骤',
        description='简单的测试步骤',
        step_type='custom',
        command='echo "Hello World"',
        order=1,
        environment_vars={'TEST_VAR': 'test_value'}
    )
    
    print(f"✅ 创建了 1 个测试步骤")
    
    # 6. 测试执行
    print("🚀 开始测试执行...")
    
    # 创建执行记录
    execution = PipelineExecution.objects.create(
        pipeline=pipeline,
        trigger_type='manual',
        trigger_user=test_user,
        status='pending'
    )
    
    print(f"✅ 创建执行记录: {execution.id}")
    
    # 使用统一执行引擎
    engine = UnifiedCICDEngine()
    
    # 开始执行
    result = engine.execute_pipeline(execution.id)
    
    print(f"✅ 执行完成，状态: {result.get('status', 'unknown')}")
    
    # 检查结果
    if result.get('status') == 'success':
        print("✅ 本地执行器测试成功!")
        return True
    else:
        print(f"❌ 本地执行器测试失败: {result.get('error_message', '未知错误')}")
        return False


if __name__ == '__main__':
    success = test_local_executor()
    sys.exit(0 if success else 1)
