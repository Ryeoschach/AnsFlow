#!/usr/bin/env python3
"""
端到端测试：验证修复后的Docker推送流程
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from pipelines.services.docker_executor import DockerExecutor

def test_end_to_end_docker_push():
    print("🚀 端到端 Docker 推送测试")
    print("=" * 50)
    
    # 获取推送步骤
    step = PipelineStep.objects.filter(step_type='docker_push').first()
    if not step:
        print("❌ 找不到 docker_push 步骤")
        return
    
    print(f"📋 步骤信息:")
    print(f"  名称: {step.name}")
    print(f"  类型: {step.step_type}")
    print(f"  ansible_parameters: {step.ansible_parameters}")
    
    # 创建Docker执行器
    executor = DockerExecutor()
    
    # 模拟执行上下文
    context = {}
    
    try:
        print("\n🔄 开始执行推送...")
        result = executor._execute_docker_push(step, context)
        
        print("\n✅ 推送成功!")
        print(f"📄 消息: {result['message']}")
        print(f"💾 数据: {result['data']}")
        
        # 检查是否推送到正确的注册表
        registry_url = result['data'].get('registry_url', '')
        if 'reg.cyfee.com:10443' in registry_url:
            print("🎯 正确：推送到了 Harbor 注册表!")
        elif 'registry-1.docker.io' in registry_url:
            print("❌ 错误：仍然推送到了 Docker Hub")
        else:
            print(f"❓ 未知注册表: {registry_url}")
            
    except Exception as e:
        print(f"\n❌ 推送失败: {str(e)}")
        
        # 检查错误类型
        error_msg = str(e).lower()
        if 'docker hub' in error_msg or 'registry-1.docker.io' in error_msg:
            print("🔍 这个错误与 Docker Hub 相关，说明仍有问题")
        elif 'reg.cyfee.com' in error_msg:
            print("🔍 这个错误与 Harbor 注册表相关，说明修复起作用了，但连接有问题")
        else:
            print("🔍 未知类型的错误")

if __name__ == "__main__":
    test_end_to_end_docker_push()
