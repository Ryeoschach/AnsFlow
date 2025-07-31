#!/usr/bin/env python
"""
调试脚本：检查 Docker push 步骤的注册表参数处理
"""

import os
import sys
import django

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_service.settings')
django.setup()

from pipelines.models import PipelineRun, PipelineStep
from docker_integration.models import DockerRegistry, DockerRegistryProject

def main():
    print("🔍 检查最新流水线执行的 Docker 步骤参数...")
    
    # 获取最新的流水线执行
    try:
        latest_run = PipelineRun.objects.latest('id')
        print(f"✅ 最新流水线执行 ID: {latest_run.id}")
        print(f"   状态: {latest_run.status}")
        print(f"   流水线: {latest_run.pipeline.name}")
    except PipelineRun.DoesNotExist:
        print("❌ 未找到流水线执行记录")
        return
    
    # 查找 Docker push 步骤
    docker_steps = latest_run.pipeline.steps.filter(step_type__in=['docker_push', 'docker_build'])
    
    if not docker_steps.exists():
        print("❌ 未找到 Docker 相关步骤")
        return
    
    for step in docker_steps:
        print(f"\n📋 步骤: {step.name} (类型: {step.step_type})")
        
        # 检查参数
        params = step.ansible_parameters or {}
        print(f"   ansible_parameters: {params}")
        
        # 检查关键参数
        registry_id = params.get('registry_id')
        project_id = params.get('project_id')
        
        print(f"   🔗 registry_id: {registry_id}")
        print(f"   🔗 project_id: {project_id}")
        
        # 验证注册表
        if registry_id:
            try:
                registry = DockerRegistry.objects.get(id=registry_id)
                print(f"   ✅ 注册表详情:")
                print(f"      名称: {registry.name}")
                print(f"      URL: {registry.url}")
                print(f"      类型: {registry.registry_type}")
                print(f"      用户名: {registry.username}")
            except DockerRegistry.DoesNotExist:
                print(f"   ❌ registry_id={registry_id} 的注册表不存在")
        
        # 验证项目
        if project_id:
            try:
                project = DockerRegistryProject.objects.get(id=project_id)
                print(f"   ✅ 项目详情:")
                print(f"      名称: {project.name}")
                print(f"      注册表: {project.registry.name}")
            except DockerRegistryProject.DoesNotExist:
                print(f"   ❌ project_id={project_id} 的项目不存在")
        
        # 检查步骤的 docker_registry 字段
        if hasattr(step, 'docker_registry') and step.docker_registry:
            print(f"   🔗 步骤关联的注册表: {step.docker_registry.name}")
        else:
            print(f"   ⚠️  步骤未关联注册表")

if __name__ == '__main__':
    main()
