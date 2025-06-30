#!/usr/bin/env python3
"""
Django shell脚本：测试流水线序列化器
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

# 现在可以导入Django模型
from pipelines.models import Pipeline
from pipelines.serializers import PipelineSerializer
from cicd_integrations.serializers import PipelineExecutionCreateSerializer
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from django.contrib.auth.models import User

def test_pipeline_serializer():
    """测试流水线序列化器"""
    print("=== 测试流水线序列化器 ===")
    
    try:
        # 获取流水线
        pipeline = Pipeline.objects.get(id=12)
        print(f"流水线: {pipeline.name}")
        print(f"执行模式: {pipeline.execution_mode}")
        print(f"执行工具: {pipeline.execution_tool}")
        
        # 创建mock请求
        factory = APIRequestFactory()
        request = factory.put('/api/v1/pipelines/pipelines/12/')
        user = User.objects.first()
        request.user = user
        
        # 序列化现有数据
        serializer = PipelineSerializer(pipeline)
        current_data = serializer.data
        print(f"当前数据字段: {list(current_data.keys())}")
        
        # 测试更新（只包含必要字段）
        update_data = {
            'name': current_data['name'],
            'description': current_data.get('description', ''),
            'is_active': True,
            'project': current_data['project'],
            'execution_mode': 'local',
            'config': current_data.get('config', {}),
            'steps': current_data.get('steps', [])
        }
        
        print(f"更新数据: {update_data}")
        
        # 测试序列化器验证
        serializer = PipelineSerializer(
            pipeline, 
            data=update_data, 
            context={'request': Request(request)}
        )
        
        if serializer.is_valid():
            print("✅ 流水线序列化器验证成功")
            updated_instance = serializer.save()
            print(f"更新后的流水线: {updated_instance.name}")
            return True
        else:
            print(f"❌ 流水线序列化器验证失败: {serializer.errors}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_execution_serializer():
    """测试执行序列化器（这可能是错误的来源）"""
    print("\n=== 测试执行序列化器 ===")
    
    try:
        # 测试空数据
        data = {}
        serializer = PipelineExecutionCreateSerializer(data=data)
        
        if serializer.is_valid():
            print("✅ 执行序列化器验证成功")
        else:
            print(f"❌ 执行序列化器验证失败: {serializer.errors}")
            print("这可能就是前端收到的错误！")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def analyze_error():
    """分析可能的错误原因"""
    print("\n=== 错误分析 ===")
    print("前端错误: {'pipeline_id': ['This field is required.'], 'cicd_tool_id': ['This field is required.']}")
    print()
    print("可能的原因:")
    print("1. 前端误调用了 /api/v1/cicd/executions/ 而不是 /api/v1/pipelines/pipelines/12/")
    print("2. 前端在保存流水线后自动触发了执行")
    print("3. 有某个信号或钩子在流水线保存时创建执行")
    print("4. 前端的路由配置错误")
    print()
    print("解决方案:")
    print("1. 检查前端网络请求，确认URL是否正确")
    print("2. 检查是否有意外的API调用")
    print("3. 在PipelineExecutionCreateSerializer中添加调试日志")

if __name__ == '__main__':
    test_pipeline_serializer()
    test_execution_serializer()
    analyze_error()
