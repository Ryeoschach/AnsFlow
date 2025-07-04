#!/usr/bin/env python3
"""
调试Ansible步骤参数保存的脚本
检查参数是否正确保存和回显
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_service.settings')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from cicd_integrations.models import AtomicStep
import json

def test_ansible_parameters():
    """测试Ansible参数的保存和读取"""
    print("=== 测试Ansible参数保存和读取 ===")
    
    # 1. 查找现有的流水线
    pipelines = Pipeline.objects.all()
    print(f"找到 {pipelines.count()} 个流水线")
    
    for pipeline in pipelines:
        print(f"\n流水线: {pipeline.id} - {pipeline.name}")
        
        # 检查PipelineStep
        pipeline_steps = pipeline.steps.all().order_by('order')
        if pipeline_steps.exists():
            print(f"  PipelineStep 数量: {pipeline_steps.count()}")
            for step in pipeline_steps:
                print(f"    步骤 {step.id}: {step.name}")
                print(f"      类型: {step.step_type}")
                print(f"      ansible_parameters: {step.ansible_parameters}")
                print(f"      ansible_playbook: {step.ansible_playbook}")
                print(f"      ansible_inventory: {step.ansible_inventory}")
                print(f"      ansible_credential: {step.ansible_credential}")
                
                # 如果是ansible类型，检查参数字段映射
                if step.step_type == 'ansible':
                    print(f"      [Ansible步骤详细信息]")
                    print(f"        playbook_id in parameters: {step.ansible_parameters.get('playbook_id') if step.ansible_parameters else None}")
                    print(f"        inventory_id in parameters: {step.ansible_parameters.get('inventory_id') if step.ansible_parameters else None}")
                    print(f"        credential_id in parameters: {step.ansible_parameters.get('credential_id') if step.ansible_parameters else None}")
        
        # 检查AtomicStep（如果存在）
        atomic_steps = pipeline.atomic_steps.all().order_by('order')
        if atomic_steps.exists():
            print(f"  AtomicStep 数量: {atomic_steps.count()}")
            for step in atomic_steps:
                print(f"    步骤 {step.id}: {step.name}")
                print(f"      类型: {step.step_type}")
                print(f"      parameters: {step.parameters}")

def test_create_ansible_step():
    """测试创建Ansible步骤并保存参数"""
    print("\n=== 测试创建Ansible步骤 ===")
    
    # 创建测试数据
    test_parameters = {
        'playbook_id': 1,
        'inventory_id': 2,
        'credential_id': 3,
        'extra_vars': {'var1': 'value1', 'var2': 'value2'},
        'limit': 'web_servers',
        'tags': 'deploy,restart'
    }
    
    # 获取第一个流水线进行测试
    pipeline = Pipeline.objects.first()
    if not pipeline:
        print("没有找到流水线，先创建一个测试流水线")
        from django.contrib.auth.models import User
        user = User.objects.first()
        if not user:
            user = User.objects.create_user('testuser', 'test@example.com', 'password')
        
        pipeline = Pipeline.objects.create(
            name='测试Ansible参数流水线',
            description='用于测试Ansible参数保存',
            created_by=user,
            status='active'
        )
    
    print(f"使用流水线: {pipeline.id} - {pipeline.name}")
    
    # 创建Ansible步骤
    step = PipelineStep.objects.create(
        pipeline=pipeline,
        name='测试Ansible步骤',
        description='测试Ansible参数保存',
        step_type='ansible',
        order=1,
        ansible_parameters=test_parameters,
        ansible_playbook_id=test_parameters.get('playbook_id'),
        ansible_inventory_id=test_parameters.get('inventory_id'),
        ansible_credential_id=test_parameters.get('credential_id')
    )
    
    print(f"创建的步骤: {step.id} - {step.name}")
    print(f"ansible_parameters: {step.ansible_parameters}")
    print(f"ansible_playbook_id: {step.ansible_playbook_id}")
    print(f"ansible_inventory_id: {step.ansible_inventory_id}")
    print(f"ansible_credential_id: {step.ansible_credential_id}")
    
    # 重新从数据库读取验证
    step_from_db = PipelineStep.objects.get(id=step.id)
    print(f"\n从数据库重新读取的数据:")
    print(f"ansible_parameters: {step_from_db.ansible_parameters}")
    print(f"ansible_playbook_id: {step_from_db.ansible_playbook_id}")
    print(f"ansible_inventory_id: {step_from_db.ansible_inventory_id}")
    print(f"ansible_credential_id: {step_from_db.ansible_credential_id}")
    
    return step

def test_serializer_output():
    """测试序列化器输出"""
    print("\n=== 测试序列化器输出 ===")
    
    from pipelines.serializers import PipelineSerializer, PipelineStepSerializer
    from rest_framework.request import Request
    from django.test import RequestFactory
    from django.contrib.auth.models import User
    
    # 创建模拟请求
    factory = RequestFactory()
    request = factory.get('/')
    user = User.objects.first()
    if user:
        request.user = user
    
    # 测试流水线序列化
    pipeline = Pipeline.objects.first()
    if pipeline:
        serializer = PipelineSerializer(pipeline, context={'request': request})
        data = serializer.data
        
        print(f"流水线 {pipeline.name} 的序列化输出:")
        print(f"steps字段: {json.dumps(data.get('steps', []), indent=2, ensure_ascii=False)}")
        
        # 测试单个步骤序列化
        steps = pipeline.steps.all()
        if steps.exists():
            for step in steps:
                step_serializer = PipelineStepSerializer(step)
                step_data = step_serializer.data
                print(f"\n步骤 {step.name} 的序列化输出:")
                print(f"  ansible_parameters: {step_data.get('ansible_parameters')}")
                print(f"  ansible_playbook: {step_data.get('ansible_playbook')}")
                print(f"  ansible_inventory: {step_data.get('ansible_inventory')}")
                print(f"  ansible_credential: {step_data.get('ansible_credential')}")

if __name__ == '__main__':
    test_ansible_parameters()
    step = test_create_ansible_step()
    test_serializer_output()
    
    print("\n=== 清理测试数据 ===")
    # 可选：清理测试数据
    if input("是否删除测试步骤? (y/N): ").lower() == 'y':
        step.delete()
        print("测试步骤已删除")
