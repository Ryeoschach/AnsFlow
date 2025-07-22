#!/usr/bin/env python
"""
真实Docker执行测试脚本
测试Docker执行器是否能够真正执行Docker命令
"""
import os
import sys
import subprocess
from datetime import datetime

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from pipelines.models import Pipeline, PipelineStep
from pipelines.services.docker_executor import DockerStepExecutor, DockerManager


def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)


def print_section(title):
    """打印小节标题"""
    print(f"\n📋 {title}")
    print("-" * 40)


def check_docker_availability():
    """检查Docker是否可用"""
    print_section("检查Docker环境")
    
    try:
        # 检查docker命令是否存在
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ Docker版本: {result.stdout.strip()}")
        else:
            print(f"  ❌ Docker命令不可用")
            return False
    except FileNotFoundError:
        print(f"  ❌ Docker未安装或不在PATH中")
        return False
    
    try:
        # 检查Docker守护进程是否运行
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ Docker守护进程运行正常")
            return True
        else:
            print(f"  ❌ Docker守护进程未运行: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ❌ Docker状态检查失败: {e}")
        return False


def test_docker_manager():
    """测试Docker管理器"""
    print_section("测试Docker管理器")
    
    # 测试模拟模式
    print("🔍 测试模拟模式:")
    mock_manager = DockerManager(enable_real_execution=False)
    
    try:
        result = mock_manager.pull_image('nginx:alpine')
        print(f"  ✅ 模拟拉取成功: {result}")
    except Exception as e:
        print(f"  ❌ 模拟拉取失败: {e}")
    
    # 测试真实模式（如果Docker可用）
    if check_docker_availability():
        print("\n🔍 测试真实模式:")
        real_manager = DockerManager(enable_real_execution=True)
        
        try:
            print("  🚀 开始拉取镜像: nginx:alpine")
            result = real_manager.pull_image('nginx:alpine')
            print(f"  ✅ 真实拉取成功!")
            print(f"  📄 输出: {result.get('pull_log', '')[:200]}...")  # 只显示前200字符
            
            # 验证镜像是否真的拉取到了
            check_result = subprocess.run(['docker', 'images', 'nginx'], capture_output=True, text=True)
            if 'nginx' in check_result.stdout and 'alpine' in check_result.stdout:
                print(f"  ✅ 验证: 镜像确实拉取到本地")
                print(f"  📋 镜像列表:")
                for line in check_result.stdout.split('\n'):
                    if 'nginx' in line:
                        print(f"    {line}")
            else:
                print(f"  ⚠️  镜像可能未正确拉取")
                
        except Exception as e:
            print(f"  ❌ 真实拉取失败: {e}")
    else:
        print("\n⚠️  跳过真实模式测试（Docker不可用）")


def test_real_docker_step_execution():
    """测试真实Docker步骤执行"""
    print_section("测试真实Docker步骤执行")
    
    if not check_docker_availability():
        print("⚠️  跳过真实执行测试（Docker不可用）")
        return
    
    # 查找现有的docker_pull步骤
    docker_pull_steps = PipelineStep.objects.filter(step_type='docker_pull')
    
    if not docker_pull_steps.exists():
        print("❌ 没有找到docker_pull步骤进行测试")
        return
    
    # 找一个有参数的步骤
    test_step = None
    for step in docker_pull_steps:
        params = step.ansible_parameters or {}
        if params.get('image'):
            test_step = step
            break
    
    if not test_step:
        print("❌ 没有找到有镜像参数的docker_pull步骤")
        return
    
    print(f"🔍 测试步骤: {test_step.name}")
    print(f"  流水线: {test_step.pipeline.name}")
    print(f"  参数: {test_step.ansible_parameters}")
    
    # 创建真实执行模式的Docker执行器
    real_executor = DockerStepExecutor(enable_real_execution=True)
    
    try:
        print("\n🚀 开始真实执行Docker步骤...")
        result = real_executor.execute_step(test_step, {})
        
        if result.get('success'):
            print("✅ Docker步骤执行成功!")
            print(f"  📄 输出: {result.get('output', '')[:300]}...")  # 显示前300字符
            
            # 验证镜像
            params = test_step.ansible_parameters or {}
            image_name = params.get('image', '')
            tag = params.get('tag', 'latest')
            full_image = f"{image_name}:{tag}"
            
            print(f"\n🔍 验证镜像是否拉取: {full_image}")
            check_result = subprocess.run(['docker', 'images', image_name], capture_output=True, text=True)
            
            if image_name in check_result.stdout:
                print("✅ 镜像确实拉取到本地!")
                print("📋 本地镜像列表:")
                for line in check_result.stdout.split('\n'):
                    if image_name in line or 'REPOSITORY' in line:
                        print(f"  {line}")
            else:
                print("❌ 镜像未在本地找到")
                
        else:
            print(f"❌ Docker步骤执行失败: {result.get('error', 'Unknown error')}")
            print(f"  📄 输出: {result.get('output', '')}")
            
    except Exception as e:
        print(f"❌ Docker步骤执行异常: {e}")
        import traceback
        traceback.print_exc()


def test_docker_command_comparison():
    """对比模拟模式和真实模式的差异"""
    print_section("模拟模式 vs 真实模式对比")
    
    # 创建测试参数
    test_params = {
        'image': 'hello-world',
        'tag': 'latest'
    }
    
    # 创建模拟步骤
    class MockStep:
        def __init__(self):
            self.id = 'test-step-001'  # 添加id属性
            self.ansible_parameters = test_params
            self.name = "测试步骤"
            self.step_type = "docker_pull"
    
    mock_step = MockStep()
    
    # 测试模拟模式
    print("🔍 模拟模式执行:")
    mock_executor = DockerStepExecutor(enable_real_execution=False)
    mock_result = mock_executor.execute_step(mock_step, {})
    print(f"  结果: {mock_result.get('success', False)}")
    print(f"  输出: {mock_result.get('output', '')[:100]}...")
    
    # 测试真实模式（如果可用）
    if check_docker_availability():
        print("\n🔍 真实模式执行:")
        real_executor = DockerStepExecutor(enable_real_execution=True)
        try:
            real_result = real_executor.execute_step(mock_step, {})
            print(f"  结果: {real_result.get('success', False)}")
            print(f"  输出: {real_result.get('output', '')[:100]}...")
            
            # 检查hello-world镜像
            check_result = subprocess.run(['docker', 'images', 'hello-world'], capture_output=True, text=True)
            if 'hello-world' in check_result.stdout:
                print("  ✅ hello-world镜像成功拉取")
            else:
                print("  ⚠️  hello-world镜像未找到")
                
        except Exception as e:
            print(f"  ❌ 真实模式执行失败: {e}")
    else:
        print("\n⚠️  跳过真实模式（Docker不可用）")


def main():
    """主函数"""
    print_header("Docker真实执行功能测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 检查Docker环境
        docker_available = check_docker_availability()
        
        # 测试Docker管理器
        test_docker_manager()
        
        # 对比测试
        test_docker_command_comparison()
        
        # 测试真实步骤执行
        test_real_docker_step_execution()
        
        print_header("测试总结")
        
        if docker_available:
            print("🎉 Docker真实执行功能已启用!")
            print("✅ 现在AnsFlow可以真正执行Docker命令")
            print("✅ 拉取的镜像会真实保存到本地Docker环境")
            print("\n📋 使用说明:")
            print("  1. 编辑Docker步骤时填写正确的镜像名和标签")
            print("  2. 执行流水线时会真正执行docker pull/build/run/push命令") 
            print("  3. 可使用 'docker images' 查看拉取的镜像")
            print("  4. 可使用 'docker ps -a' 查看运行的容器")
        else:
            print("⚠️  Docker环境不可用，将使用模拟模式")
            print("🔧 请确保:")
            print("  1. Docker已正确安装")
            print("  2. Docker守护进程正在运行")
            print("  3. 当前用户有Docker执行权限")
            
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
