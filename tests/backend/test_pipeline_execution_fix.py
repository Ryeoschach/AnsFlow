#!/usr/bin/env python
"""
测试流水线执行创建
验证400错误修复
"""

import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import User
from cicd_integrations.views.executions import PipelineExecutionViewSet
from cicd_integrations.serializers import PipelineExecutionCreateSerializer

def test_pipeline_execution_creation():
    """测试流水线执行创建"""
    print("=== 测试流水线执行创建 ===")
    
    try:
        # 获取测试用户
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={'email': 'test@example.com'}
        )
        
        # 测试数据（和错误日志中的一样）
        test_data = {
            'pipeline_id': 1,
            'cicd_tool_id': 2,
            'trigger_type': 'manual',
            'parameters': {}
        }
        
        print(f"测试数据: {test_data}")
        
        # 测试序列化器验证
        print("1. 测试序列化器验证...")
        
        # 创建一个简单的request mock对象
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        mock_request = MockRequest(user)
        context = {'request': mock_request}
        serializer = PipelineExecutionCreateSerializer(data=test_data, context=context)
        
        if serializer.is_valid():
            print("✅ 序列化器验证通过")
            print(f"   验证后的数据: {serializer.validated_data}")
        else:
            print("❌ 序列化器验证失败")
            print(f"   错误: {serializer.errors}")
            return False
        
        # 测试视图创建
        print("2. 测试视图创建...")
        factory = APIRequestFactory()
        request = factory.post('/api/v1/cicd/executions/', test_data, format='json')
        request.user = user
        
        view = PipelineExecutionViewSet()
        view.request = request
        view.format_kwarg = None
        
        try:
            response = view.create(request)
            print(f"✅ 视图创建成功，状态码: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"   响应数据: {response.data}")
            return True
        except Exception as e:
            print(f"❌ 视图创建失败: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_status_validation():
    """测试工具状态验证"""
    print("\n=== 测试工具状态验证 ===")
    
    try:
        from cicd_integrations.models import CICDTool
        
        # 检查工具状态
        tool = CICDTool.objects.get(id=2)
        print(f"工具状态: {tool.status}")
        
        # 测试序列化器对active状态的处理
        context = {'request': type('obj', (object,), {'user': None})()}
        serializer = PipelineExecutionCreateSerializer(data={'cicd_tool_id': 2}, context=context)
        
        # 只验证cicd_tool_id字段
        try:
            validated_tool_id = serializer.validate_cicd_tool_id(2)
            print(f"✅ 工具状态验证通过，工具ID: {validated_tool_id}")
            return True
        except Exception as e:
            print(f"❌ 工具状态验证失败: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 工具状态测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试流水线执行创建修复...")
    
    test1 = test_tool_status_validation()
    test2 = test_pipeline_execution_creation()
    
    if test1 and test2:
        print("\n🎉 所有测试通过！流水线执行创建修复成功")
        return True
    else:
        print("\n❌ 存在测试失败")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
