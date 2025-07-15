#!/usr/bin/env python3
"""
测试页面创建的步骤结构
模拟页面创建的步骤，命令存储在parameters中
"""

import os
import sys
import django
import json
from django.conf import settings

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from project_management.models import Project
from cicd_integrations.models import CICDTool, PipelineExecution
from cicd_integrations.services import UnifiedCICDEngine
from django.contrib.auth.models import User

def test_page_style_executor():
    """测试页面风格的步骤执行"""
    
    print("🔧 开始测试页面风格的步骤执行...")
    
    # 1. 检查本地执行器工具
    try:
        local_tool = CICDTool.objects.get(tool_type='local')
        print(f"✅ 找到本地执行器工具: {local_tool.name}")
    except CICDTool.DoesNotExist:
        print("❌ 本地执行器工具不存在")
        return False
    
    # 2. 获取或创建测试项目
    try:
        project = Project.objects.filter(name='页面测试项目').first()
        if not project:
            user = User.objects.first()
            project = Project.objects.create(
                name='页面测试项目',
                description='用于测试页面风格步骤的项目',
                owner=user,
                is_active=True
            )
            print(f"✅ 创建测试项目: {project.name}")
        else:
            print(f"✅ 找到测试项目: {project.name}")
    except Exception as e:
        print(f"❌ 创建测试项目失败: {e}")
        return False
    
    # 3. 创建测试流水线
    try:
        pipeline = Pipeline.objects.filter(name='页面风格测试流水线').first()
        if not pipeline:
            user = User.objects.first()
            pipeline = Pipeline.objects.create(
                name='页面风格测试流水线',
                description='测试页面风格的步骤执行',
                project=project,
                created_by=user,
                execution_mode='local',
                is_active=True
            )
            print(f"✅ 创建测试流水线: {pipeline.name}")
        else:
            print(f"✅ 找到测试流水线: {pipeline.name}")
    except Exception as e:
        print(f"❌ 创建测试流水线失败: {e}")
        return False
    
    # 4. 创建页面风格的测试步骤（命令存储在parameters中）
    try:
        # 清理旧步骤
        pipeline.steps.all().delete()
        
        # 创建步骤1: 命令存储在parameters中
        step1 = PipelineStep.objects.create(
            pipeline=pipeline,
            name='测试步骤1',
            step_type='custom',
            description='执行简单的echo命令',
            order=1,
            command='',  # 空的command字段
            environment_vars={},
            ansible_parameters={
                'command': 'echo "Hello World"'
            }
        )
        
        # 创建步骤2: 命令存储在parameters中
        step2 = PipelineStep.objects.create(
            pipeline=pipeline,
            name='测试步骤2',
            step_type='custom',
            description='显示当前时间',
            order=2,
            command='',  # 空的command字段
            environment_vars={},
            ansible_parameters={
                'command': 'date'
            }
        )
        
        # 创建步骤3: 命令存储在parameters中
        step3 = PipelineStep.objects.create(
            pipeline=pipeline,
            name='测试步骤3',
            step_type='custom',
            description='列出目录内容',
            order=3,
            command='',  # 空的command字段
            environment_vars={},
            ansible_parameters={
                'command': 'ls -la /tmp'
            }
        )
        
        print(f"✅ 创建了 {pipeline.steps.count()} 个页面风格的测试步骤")
        
        # 打印步骤信息以便调试
        for step in pipeline.steps.all():
            print(f"  步骤 {step.order}: {step.name}")
            print(f"    命令字段: '{step.command}'")
            print(f"    参数字段: {step.ansible_parameters}")
        
    except Exception as e:
        print(f"❌ 创建测试步骤失败: {e}")
        return False
    
    # 5. 测试执行
    try:
        print("\n🚀 开始测试执行...")
        
        # 创建执行引擎
        engine = UnifiedCICDEngine()
        
        # 创建执行记录
        execution = PipelineExecution.objects.create(
            pipeline=pipeline,
            cicd_tool=local_tool,
            status='pending',
            trigger_type='manual',
            triggered_by=User.objects.first(),
            definition=pipeline.config or {},
            parameters={}
        )
        
        print(f"✅ 创建执行记录: {execution.id}")
        
        # 执行流水线
        result = engine._perform_execution(execution.id)
        
        # 检查结果
        execution.refresh_from_db()
        print(f"✅ 执行完成，状态: {execution.status}")
        
        return execution.status == 'success'
        
    except Exception as e:
        print(f"❌ 执行测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_data():
    """清理测试数据"""
    print("\n🧹 清理测试数据...")
    
    # 删除测试流水线和相关数据
    Pipeline.objects.filter(name='页面风格测试流水线').delete()
    Project.objects.filter(name='页面测试项目').delete()
    
    print("✅ 测试数据清理完成")

if __name__ == '__main__':
    success = test_page_style_executor()
    
    if success:
        print("\n🎉 页面风格步骤执行测试成功!")
    else:
        print("\n❌ 页面风格步骤执行测试失败!")
        sys.exit(1)
    
    # 询问是否清理测试数据
    response = input("\n是否清理测试数据? (y/N): ")
    if response.lower() in ['y', 'yes']:
        cleanup_test_data()
