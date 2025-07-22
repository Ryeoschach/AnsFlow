#!/usr/bin/env python3
"""
测试完整的 Docker 推送流程，验证认证信息传递
"""

import os
import sys
import django

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from docker_integration.models import DockerRegistry
from pipelines.services.docker_executor import DockerStepExecutor

class MockStep:
    """模拟步骤对象"""
    def __init__(self, parameters):
        self.parameters = parameters
        self.step_type = 'docker_push'

def test_complete_docker_push_flow():
    """测试完整的 Docker 推送流程"""
    
    print("=== 测试完整的 Docker 推送流程 ===")
    
    # 获取 Harbor 注册表
    try:
        harbor_registry = DockerRegistry.objects.get(id=5)
        print(f"✅ 找到 Harbor 注册表: {harbor_registry.name}")
        print(f"   URL: {harbor_registry.url}")  
        print(f"   用户名: {harbor_registry.username}")
        print(f"   认证配置: {harbor_registry.auth_config}")
        
        # 创建模拟步骤
        mock_step = MockStep({
            'image': 'test',
            'tag': '072201',
            'registry_id': 5
        })
        
        print(f"\n--- 测试 Docker 推送执行器 ---")
        print(f"步骤参数: {mock_step.parameters}")
        
        # 创建 Docker 执行器（模拟模式）
        executor = DockerStepExecutor()
        
        # 创建模拟上下文
        context = {}
        
        # 调用 Docker 推送方法
        try:
            print("\n--- 执行 Docker 推送 ---")
            result = executor._execute_docker_push(mock_step, context)
            print(f"✅ Docker 推送执行完成")
            print(f"执行结果: {result}")
            
        except Exception as e:
            print(f"❌ Docker 推送执行失败: {e}")
            import traceback
            traceback.print_exc()
            
    except DockerRegistry.DoesNotExist:
        print("❌ 未找到 Harbor 注册表 ID: 5")

def test_auth_info_extraction():
    """测试认证信息提取"""
    print("\n=== 测试认证信息提取 ===")
    
    try:
        registry = DockerRegistry.objects.get(id=5)
        
        # 模拟认证信息提取逻辑
        username = registry.username
        password = None
        
        if registry.auth_config and isinstance(registry.auth_config, dict):
            password = registry.auth_config.get('password')
        
        print(f"注册表: {registry.name}")
        print(f"URL: {registry.url}")
        print(f"用户名: {username}")
        print(f"密码: {'*' * len(password) if password else 'None'}")
        
        if username and password:
            print("✅ 认证信息完整")
            
            # 模拟登录命令构建
            login_command = [
                'docker', 'login',
                registry.url.replace('https://', '').replace('http://', ''),
                '-u', username,
                '-p', password
            ]
            
            # 隐藏密码显示
            safe_command = login_command.copy()
            safe_command[-1] = '*' * len(password)
            
            print(f"登录命令: {' '.join(safe_command)}")
            
        else:
            print("❌ 认证信息不完整")
            
    except Exception as e:
        print(f"❌ 认证信息提取失败: {e}")

if __name__ == '__main__':
    test_auth_info_extraction()
    test_complete_docker_push_flow()
