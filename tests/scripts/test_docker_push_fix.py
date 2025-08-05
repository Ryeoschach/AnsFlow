#!/usr/bin/env python3
"""
测试Docker Push注册表修复是否有效
"""

import sys
import os

# 设置Django环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')

import django
django.setup()

from cicd_integrations.models import AtomicStep
from pipelines.services.docker_executor import DockerStepExecutor

def test_docker_push_registry_fix():
    """测试Docker Push注册表修复"""
    print("🧪 测试Docker Push注册表修复...")
    print("=" * 60)
    
    # 获取Docker Push步骤
    docker_push_step = AtomicStep.objects.filter(step_type='docker_push').first()
    if not docker_push_step:
        print("❌ 没有找到Docker Push步骤")
        return
    
    print(f"📦 测试步骤: {docker_push_step.name}")
    print(f"参数: {docker_push_step.parameters}")
    
    # 创建Docker执行器
    docker_executor = DockerStepExecutor(enable_real_execution=False)  # 测试模式
    
    # 准备上下文
    context = {
        'working_directory': '/tmp/test',
        'workspace_path': '/tmp/test'
    }
    
    try:
        # 执行Docker Push步骤
        result = docker_executor.execute_step(docker_push_step, context)
        
        print("\n📊 执行结果:")
        print(f"成功: {result.get('success')}")
        print(f"消息: {result.get('message')}")
        print(f"输出: {result.get('output')}")
        
        if result.get('data'):
            data = result.get('data')
            print("\n📋 详细信息:")
            for key, value in data.items():
                print(f"  {key}: {value}")
        
        if result.get('success'):
            print("\n✅ 修复成功！注册表信息已正确处理")
        else:
            print(f"\n❌ 执行失败: {result.get('error')}")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_docker_push_registry_fix()
