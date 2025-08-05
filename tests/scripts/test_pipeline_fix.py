#!/usr/bin/env python3
"""
测试流水线更新修复
"""
import os
import sys
import django
from pathlib import Path

# 设置Django环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import Pipeline
from pipelines.serializers import PipelineSerializer
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

def test_pipeline_update_without_steps():
    """测试不包含steps字段的流水线更新"""
    print("=== 测试流水线更新（不包含steps） ===")
    
    try:
        # 获取流水线
        pipeline = Pipeline.objects.get(id=12)
        print(f"流水线: {pipeline.name}")
        print(f"现有步骤数量: {pipeline.atomic_steps.count()}")
        
        # 创建请求上下文
        factory = APIRequestFactory()
        request = factory.put('/api/v1/pipelines/pipelines/12/')
        user = User.objects.first()
        request.user = user
        
        # 测试数据（不包含steps）
        update_data = {
            'name': pipeline.name,
            'description': '更新后的描述',
            'is_active': True,
            'project': pipeline.project.id,
            'execution_mode': 'local',
            'config': {'test': 'value'}
        }
        
        print(f"更新数据（不含steps）: {update_data}")
        
        # 验证序列化器
        serializer = PipelineSerializer(
            pipeline, 
            data=update_data, 
            context={'request': Request(request)}
        )
        
        if serializer.is_valid():
            print("✅ 序列化器验证成功（不含steps）")
            updated_instance = serializer.save()
            print(f"✅ 更新成功，步骤数量: {updated_instance.atomic_steps.count()}")
            print(f"描述已更新: {updated_instance.description}")
            return True
        else:
            print(f"❌ 序列化器验证失败: {serializer.errors}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_pipeline_update_with_steps():
    """测试包含steps字段的流水线更新"""
    print("\n=== 测试流水线更新（包含steps） ===")
    
    try:
        # 获取流水线
        pipeline = Pipeline.objects.get(id=12)
        
        # 创建请求上下文
        factory = APIRequestFactory()
        request = factory.put('/api/v1/pipelines/pipelines/12/')
        user = User.objects.first()
        request.user = user
        
        # 测试数据（包含steps）
        update_data = {
            'name': pipeline.name,
            'description': '再次更新的描述',
            'is_active': True,
            'project': pipeline.project.id,
            'execution_mode': 'hybrid',
            'config': {'test': 'value2'},
            'steps': [
                {
                    'name': '新测试步骤',
                    'step_type': 'test',
                    'description': '这是一个新的测试步骤',
                    'order': 1,
                    'parameters': {'command': 'echo "test"'},
                    'is_active': True
                }
            ]
        }
        
        print(f"更新数据（含steps）: {update_data}")
        
        # 验证序列化器
        serializer = PipelineSerializer(
            pipeline, 
            data=update_data, 
            context={'request': Request(request)}
        )
        
        if serializer.is_valid():
            print("✅ 序列化器验证成功（含steps）")
            updated_instance = serializer.save()
            print(f"✅ 更新成功，步骤数量: {updated_instance.atomic_steps.count()}")
            print(f"描述已更新: {updated_instance.description}")
            print(f"执行模式: {updated_instance.execution_mode}")
            return True
        else:
            print(f"❌ 序列化器验证失败: {serializer.errors}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_pipeline_serialization():
    """测试流水线序列化"""
    print("\n=== 测试流水线序列化 ===")
    
    try:
        pipeline = Pipeline.objects.get(id=12)
        serializer = PipelineSerializer(pipeline)
        data = serializer.data
        
        print(f"序列化成功，字段: {list(data.keys())}")
        print(f"steps字段类型: {type(data.get('steps'))}")
        print(f"steps数量: {len(data.get('steps', []))}")
        
        return True
    except Exception as e:
        print(f"❌ 序列化测试失败: {e}")
        return False

if __name__ == '__main__':
    print("开始测试流水线更新修复...\n")
    
    # 1. 测试序列化
    if not test_pipeline_serialization():
        exit(1)
    
    # 2. 测试不含steps的更新
    if not test_pipeline_update_without_steps():
        exit(1)
    
    # 3. 测试含steps的更新
    if not test_pipeline_update_with_steps():
        exit(1)
    
    print("\n🎉 所有测试通过！流水线更新修复成功！")
