#!/usr/bin/env python3
"""
测试 Docker 推送步骤执行器 - 验证注册表 ID 5
"""
import os
import sys

# 设置Django环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from pipelines.services.docker_executor import DockerStepExecutor
from docker_integration.models import DockerRegistry


class MockAtomicStep:
    """模拟 AtomicStep 对象"""
    def __init__(self, parameters):
        self.parameters = parameters
        self.ansible_parameters = None
        
    def __str__(self):
        return f"MockAtomicStep(parameters={self.parameters})"


def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_info(message):
    print(f"📋 {message}")


def print_success(message):
    print(f"✅ {message}")


def print_error(message):
    print(f"❌ {message}")


def test_docker_push_registry_selection():
    """测试 Docker 推送注册表选择逻辑"""
    print_header("测试 Docker 推送注册表选择")
    
    # 创建 Docker 步骤执行器（模拟模式）
    executor = DockerStepExecutor(enable_real_execution=False)
    
    # 测试场景 1: 使用 registry_id = 5
    print_info("测试场景 1: 指定 registry_id = 5 (Harbor)")
    test_step = MockAtomicStep({
        'image': 'test-app',
        'tag': 'v1.0.0',
        'registry_id': 5
    })
    
    try:
        # 模拟执行
        context = {}
        result = executor._execute_docker_push(test_step, context)
        
        print_success(f"执行成功: {result['message']}")
        print_info(f"推送的镜像名: {result['data']['image_name']}")
        print_info(f"使用的注册表: {result['data']['registry_name']}")
        print_info(f"注册表URL: {result['data']['registry_url']}")
        
        # 验证是否使用了正确的注册表
        if 'reg.cyfee.com:10443' in result['data']['image_name']:
            print_success("✅ 正确使用了 Harbor 注册表 (ID: 5)")
        else:
            print_error(f"❌ 错误：未使用指定的注册表，实际镜像名: {result['data']['image_name']}")
            
    except Exception as e:
        print_error(f"执行失败: {e}")
    
    # 测试场景 2: 使用 registry_id = 4
    print_info("\n测试场景 2: 指定 registry_id = 4 (GitLab)")
    test_step2 = MockAtomicStep({
        'image': 'another-app',
        'tag': 'v2.0.0',
        'registry_id': 4
    })
    
    try:
        result2 = executor._execute_docker_push(test_step2, context)
        
        print_success(f"执行成功: {result2['message']}")
        print_info(f"推送的镜像名: {result2['data']['image_name']}")
        print_info(f"使用的注册表: {result2['data']['registry_name']}")
        
        if 'gitlab.cyfee.com:8443' in result2['data']['image_name']:
            print_success("✅ 正确使用了 GitLab 注册表 (ID: 4)")
        else:
            print_error(f"❌ 错误：未使用指定的注册表，实际镜像名: {result2['data']['image_name']}")
            
    except Exception as e:
        print_error(f"执行失败: {e}")
    
    # 测试场景 3: 不指定 registry_id（应该使用默认）
    print_info("\n测试场景 3: 不指定 registry_id (应该使用默认)")
    test_step3 = MockAtomicStep({
        'image': 'default-app',
        'tag': 'latest'
        # 没有 registry_id
    })
    
    try:
        result3 = executor._execute_docker_push(test_step3, context)
        
        print_success(f"执行成功: {result3['message']}")
        print_info(f"推送的镜像名: {result3['data']['image_name']}")
        print_info(f"使用的注册表: {result3['data']['registry_name']}")
        
        # 应该使用默认注册表或 Docker Hub
        print_info(f"注册表URL: {result3['data']['registry_url']}")
        
    except Exception as e:
        print_error(f"执行失败: {e}")


def check_registry_configuration():
    """检查注册表配置"""
    print_header("检查注册表配置")
    
    registries = DockerRegistry.objects.all()
    
    for registry in registries:
        print_info(f"注册表 ID {registry.id}: {registry.name}")
        print(f"   URL: {registry.url}")
        print(f"   类型: {registry.registry_type}")
        print(f"   默认: {registry.is_default}")
        print(f"   状态: {registry.status}")
        print(f"   用户名: {registry.username}")
        print(f"   认证配置: {registry.auth_config}")
        print()


def test_image_name_construction():
    """测试镜像名构造逻辑"""
    print_header("测试镜像名构造逻辑")
    
    try:
        # 获取注册表
        harbor_registry = DockerRegistry.objects.get(id=5)
        gitlab_registry = DockerRegistry.objects.get(id=4)
        
        test_cases = [
            {
                'registry': harbor_registry,
                'image': 'my-app',
                'tag': 'v1.0.0',
                'expected_prefix': 'reg.cyfee.com:10443'
            },
            {
                'registry': gitlab_registry,
                'image': 'gitlab-app',
                'tag': 'latest',
                'expected_prefix': 'gitlab.cyfee.com:8443'
            }
        ]
        
        for case in test_cases:
            registry = case['registry']
            image = case['image']
            tag = case['tag']
            expected_prefix = case['expected_prefix']
            
            # 模拟镜像名构造逻辑
            if registry and registry.registry_type != 'dockerhub':
                registry_host = registry.url.replace('https://', '').replace('http://', '')
                if not image.startswith(registry_host):
                    full_image_name = f"{registry_host}/{image}"
                else:
                    full_image_name = image
            else:
                full_image_name = image
            
            # 添加标签
            image_part = full_image_name.split('/')[-1] if '/' in full_image_name else full_image_name
            if ':' not in image_part:
                full_image_name = f"{full_image_name}:{tag}"
            
            print_info(f"注册表: {registry.name}")
            print(f"   输入镜像: {image}:{tag}")
            print(f"   构造结果: {full_image_name}")
            print(f"   期望前缀: {expected_prefix}")
            
            if expected_prefix in full_image_name:
                print_success("✅ 镜像名构造正确")
            else:
                print_error("❌ 镜像名构造错误")
            print()
            
    except Exception as e:
        print_error(f"测试失败: {e}")


def main():
    """主函数"""
    print_header("Docker 推送注册表测试")
    
    # 1. 检查注册表配置
    check_registry_configuration()
    
    # 2. 测试镜像名构造
    test_image_name_construction()
    
    # 3. 测试推送逻辑
    test_docker_push_registry_selection()
    
    print_header("测试总结")
    print_info("如果所有测试都通过，说明注册表选择逻辑正常")
    print_info("如果测试失败，请检查:")
    print("   1. 注册表配置是否正确")
    print("   2. 步骤参数 registry_id 是否正确传递")
    print("   3. DockerStepExecutor 逻辑是否有问题")


if __name__ == "__main__":
    main()
