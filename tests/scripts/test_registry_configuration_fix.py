#!/usr/bin/env python3
"""
测试注册表配置获取修复
验证 Docker 推送能正确识别 Harbor 注册表
"""

import os
import sys
import django

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.services.docker_executor import DockerStepExecutor
from pipelines.models import Pipeline

def test_registry_configuration_fix():
    """测试注册表配置获取修复"""
    
    print("=== 测试注册表配置获取修复 ===")
    
    # 获取真实的推送步骤
    try:
        pipeline = Pipeline.objects.get(name='本地docker测试')
        push_step = pipeline.steps.filter(step_type='docker_push').first()
        
        if not push_step:
            print("❌ 未找到推送步骤")
            return False
            
        print(f"📋 推送步骤信息:")
        print(f"  名称: {push_step.name}")
        print(f"  类型: {push_step.step_type}")
        print(f"  参数: {push_step.ansible_parameters}")
        
        # 检查步骤属性
        print(f"\n🔍 步骤对象分析:")
        print(f"  hasattr(step, 'parameters'): {hasattr(push_step, 'parameters')}")
        print(f"  hasattr(step, 'docker_registry'): {hasattr(push_step, 'docker_registry')}")
        print(f"  hasattr(step, 'ansible_parameters'): {hasattr(push_step, 'ansible_parameters')}")
        
        if hasattr(push_step, 'ansible_parameters') and push_step.ansible_parameters:
            print(f"  ansible_parameters 内容: {push_step.ansible_parameters}")
        
        # 使用Docker执行器测试
        executor = DockerStepExecutor(enable_real_execution=False)
        
        print(f"\n🚀 执行推送步骤测试...")
        context = {}
        
        try:
            result = executor._execute_docker_push(push_step, context)
            
            print(f"\n✅ 推送测试成功!")
            print(f"📄 消息: {result.get('message', '')}")
            
            # 检查是否使用了正确的注册表
            message = result.get('message', '')
            if 'harbor' in message.lower():
                print(f"✅ 正确使用了 Harbor 注册表")
                return True
            elif 'docker hub' in message.lower():
                print(f"❌ 错误：仍然使用了 Docker Hub")
                return False
            else:
                print(f"⚠️  无法确定使用的注册表")
                return False
                
        except Exception as e:
            print(f"\n❌ 推送测试失败: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 获取步骤失败: {e}")
        return False

def test_registry_fallback_logic():
    """测试注册表回退逻辑"""
    
    print(f"\n=== 测试注册表回退逻辑 ===")
    
    class MockStep:
        def __init__(self, ansible_parameters):
            self.ansible_parameters = ansible_parameters
            # 确保没有其他属性
            
    # 测试用例：只有 ansible_parameters
    mock_step = MockStep({
        'image': 'myapp',
        'tag': '0722', 
        'registry_id': 5
    })
    
    print(f"📋 模拟步骤:")
    print(f"  ansible_parameters: {mock_step.ansible_parameters}")
    print(f"  hasattr(step, 'parameters'): {hasattr(mock_step, 'parameters')}")
    print(f"  hasattr(step, 'docker_registry'): {hasattr(mock_step, 'docker_registry')}")
    
    executor = DockerStepExecutor(enable_real_execution=False)
    
    try:
        result = executor._execute_docker_push(mock_step, {})
        
        print(f"\n✅ 模拟步骤测试成功!")
        print(f"📄 消息: {result.get('message', '')}")
        
        # 检查注册表
        message = result.get('message', '')
        if 'harbor' in message.lower():
            print(f"✅ 模拟步骤正确使用了 Harbor 注册表")
            return True
        else:
            print(f"❌ 模拟步骤使用了错误的注册表")
            return False
            
    except Exception as e:
        print(f"❌ 模拟步骤测试失败: {e}")
        return False

if __name__ == '__main__':
    print("🔧 Docker 注册表配置获取修复测试")
    print("="*50)
    
    # 测试真实步骤
    real_step_success = test_registry_configuration_fix()
    
    # 测试回退逻辑
    fallback_logic_success = test_registry_fallback_logic()
    
    print(f"\n" + "="*50)
    print(f"📊 测试结果:")
    print(f"  真实步骤测试: {'✅' if real_step_success else '❌'}")
    print(f"  回退逻辑测试: {'✅' if fallback_logic_success else '❌'}")
    
    if real_step_success and fallback_logic_success:
        print(f"\n🎉 修复成功！现在 Docker 推送应该使用正确的 Harbor 注册表")
        print(f"\n💡 预期效果:")
        print(f"  - 推送目标: reg.cyfee.com:10443/test/myapp:0722")
        print(f"  - 不再推送到: registry-1.docker.io")
        print(f"  - 使用 Harbor 认证: admin/admin123")
    else:
        print(f"\n⚠️  修复可能不完整，需要进一步调试")
        print(f"\n🔍 建议:")
        print(f"  1. 检查步骤模型的属性结构")
        print(f"  2. 验证 ansible_parameters 是否正确保存")
        print(f"  3. 确认注册表ID 5存在且配置正确")
    
    print(f"\n🚀 下一步：重新执行流水线测试真实推送")
