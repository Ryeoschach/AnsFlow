#!/usr/bin/env python
"""
Docker Pull 步骤参数诊断脚本
检查docker_pull步骤的参数保存和传递情况
"""
import os
import sys
import json
from datetime import datetime

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from pipelines.models import Pipeline, PipelineStep
from pipelines.services.docker_executor import DockerStepExecutor


def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)


def print_section(title):
    """打印小节标题"""
    print(f"\n📋 {title}")
    print("-" * 40)


def analyze_docker_pull_steps():
    """分析所有docker_pull步骤的参数"""
    print_header("Docker Pull 步骤参数分析")
    
    docker_pull_steps = PipelineStep.objects.filter(step_type='docker_pull')
    
    print(f"找到 {docker_pull_steps.count()} 个 Docker Pull 步骤")
    
    for i, step in enumerate(docker_pull_steps, 1):
        print_section(f"步骤 {i}: {step.name}")
        
        print(f"流水线: {step.pipeline.name}")
        print(f"步骤ID: {step.id}")
        print(f"步骤类型: {step.step_type}")
        print(f"执行顺序: {step.order}")
        
        # 检查参数存储
        print(f"\n📦 参数存储情况:")
        
        # ansible_parameters 字段（主要参数存储）
        ansible_params = step.ansible_parameters or {}
        print(f"  ansible_parameters: {ansible_params}")
        
        # environment_vars 字段
        env_vars = step.environment_vars or {}
        print(f"  environment_vars: {env_vars}")
        
        # command 字段
        command = step.command
        print(f"  command: '{command}'")
        
        # 检查是否有镜像名参数
        image_name = None
        if 'image' in ansible_params:
            image_name = ansible_params['image']
            print(f"  ✅ 镜像名 (ansible_parameters): {image_name}")
        elif 'image_name' in ansible_params:
            image_name = ansible_params['image_name']
            print(f"  ✅ 镜像名 (image_name): {image_name}")
        elif 'docker_image' in ansible_params:
            image_name = ansible_params['docker_image']
            print(f"  ✅ 镜像名 (docker_image): {image_name}")
        else:
            print(f"  ❌ 未找到镜像名参数")
            
        # 检查其他Docker相关参数
        registry = getattr(step, 'docker_registry', None)
        if registry:
            print(f"  🏪 关联注册表: {registry.name}")
        else:
            print(f"  ⚠️  未关联注册表")
        
        # 检查标签
        tag = ansible_params.get('tag', 'latest')
        print(f"  🏷️  标签: {tag}")
        
        print()


def test_docker_executor_parameter_extraction():
    """测试Docker执行器参数提取"""
    print_header("Docker 执行器参数提取测试")
    
    docker_pull_steps = PipelineStep.objects.filter(step_type='docker_pull')
    
    if not docker_pull_steps.exists():
        print("没有找到docker_pull步骤")
        return
    
    # 测试第一个步骤
    step = docker_pull_steps.first()
    print(f"测试步骤: {step.name}")
    
    try:
        # 创建Docker执行器
        docker_executor = DockerStepExecutor()
        
        # 检查执行器是否能处理这个步骤类型
        can_execute = docker_executor.can_execute(step.step_type)
        print(f"执行器是否支持该类型: {can_execute}")
        
        if can_execute:
            # 模拟执行，检查参数提取
            context = {'environment': {}}
            
            print(f"\n🔍 参数提取测试:")
            print(f"  步骤类型: {step.step_type}")
            print(f"  ansible_parameters: {step.ansible_parameters}")
            
            # 检查镜像名提取逻辑
            params = step.ansible_parameters or {}
            image_name = (
                params.get('image') or 
                params.get('image_name') or 
                params.get('docker_image')
            )
            
            if image_name:
                print(f"  ✅ 提取到镜像名: {image_name}")
            else:
                print(f"  ❌ 未能提取镜像名")
                print(f"  可用参数键: {list(params.keys())}")
                
    except Exception as e:
        print(f"❌ 执行器测试失败: {e}")
        import traceback
        traceback.print_exc()


def analyze_pipeline_creation_data():
    """分析流水线创建时的数据格式"""
    print_header("流水线创建数据格式分析")
    
    # 查找包含docker_pull步骤的流水线
    pipelines_with_docker = Pipeline.objects.filter(
        steps__step_type='docker_pull'
    ).distinct()
    
    for pipeline in pipelines_with_docker:
        print_section(f"流水线: {pipeline.name}")
        
        docker_steps = pipeline.steps.filter(step_type='docker_pull')
        
        for step in docker_steps:
            print(f"步骤: {step.name}")
            print(f"创建时间: {step.created_at}")
            print(f"更新时间: {step.updated_at}")
            
            # 检查原始JSON数据
            print(f"原始参数数据:")
            print(f"  ansible_parameters: {json.dumps(step.ansible_parameters, indent=2, ensure_ascii=False)}")
            
            if step.environment_vars:
                print(f"  environment_vars: {json.dumps(step.environment_vars, indent=2, ensure_ascii=False)}")


def check_docker_step_defaults():
    """检查Docker步骤默认参数配置"""
    print_header("Docker 步骤默认参数检查")
    
    try:
        from pipelines.services.docker_step_defaults import DockerStepDefaults
        
        # 获取docker_pull的默认参数
        defaults = DockerStepDefaults.get_step_defaults('docker_pull')
        
        print("Docker Pull 默认参数:")
        for key, value in defaults.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"❌ 获取默认参数失败: {e}")


def simulate_docker_pull_execution():
    """模拟Docker Pull执行，检查参数传递"""
    print_header("Docker Pull 执行模拟")
    
    docker_pull_steps = PipelineStep.objects.filter(step_type='docker_pull')
    
    if not docker_pull_steps.exists():
        print("没有找到docker_pull步骤进行测试")
        return
    
    step = docker_pull_steps.first()
    print(f"模拟执行步骤: {step.name}")
    
    try:
        from pipelines.services.docker_executor import DockerStepExecutor
        
        docker_executor = DockerStepExecutor()
        context = {'environment': {}}
        
        print(f"\n🔍 执行前参数检查:")
        print(f"  步骤参数: {step.ansible_parameters}")
        
        # 检查是否有image参数
        params = step.ansible_parameters or {}
        required_params = ['image', 'image_name', 'docker_image']
        
        found_image_param = None
        for param in required_params:
            if param in params and params[param]:
                found_image_param = param
                break
        
        if found_image_param:
            print(f"  ✅ 找到镜像参数: {found_image_param} = {params[found_image_param]}")
            
            # 尝试模拟执行
            print(f"\n🚀 模拟执行 Docker Pull...")
            
            # 这里不实际执行，只检查参数
            print(f"  镜像名: {params[found_image_param]}")
            print(f"  标签: {params.get('tag', 'latest')}")
            print(f"  注册表: {getattr(step, 'docker_registry', None)}")
            
        else:
            print(f"  ❌ 未找到镜像参数，可用参数: {list(params.keys())}")
            
    except Exception as e:
        print(f"❌ 模拟执行失败: {e}")


def main():
    """主函数"""
    print_header("Docker Pull 步骤参数诊断")
    print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 分析所有docker_pull步骤
        analyze_docker_pull_steps()
        
        # 检查默认参数
        check_docker_step_defaults()
        
        # 测试执行器参数提取
        test_docker_executor_parameter_extraction()
        
        # 分析流水线创建数据
        analyze_pipeline_creation_data()
        
        # 模拟执行
        simulate_docker_pull_execution()
        
        print_header("诊断完成")
        print("请检查上述输出，确认镜像名参数是否正确保存和传递")
        
    except Exception as e:
        print(f"\n❌ 诊断过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
