#!/usr/bin/env python3
"""
测试CI/CD工具状态修复
验证 authenticated 状态的工具可以正常触发流水线
"""

import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_service.settings')
django.setup()

from cicd_integrations.models import CICDTool
from cicd_integrations.serializers import PipelineExecutionSerializer
from pipelines.models import Pipeline

def test_tool_status_validation():
    """测试工具状态验证"""
    print("🔍 测试CI/CD工具状态验证修复...")
    
    # 获取所有工具
    tools = CICDTool.objects.all()
    print(f"\n📋 当前所有CI/CD工具:")
    for tool in tools:
        print(f"  ID: {tool.id}, Name: {tool.name}, Type: {tool.tool_type}, Status: {tool.status}")
    
    # 获取一个流水线用于测试
    pipeline = Pipeline.objects.first()
    if not pipeline:
        print("❌ 没有找到流水线，无法测试")
        return
    
    print(f"\n🔧 使用流水线: {pipeline.name} (ID: {pipeline.id})")
    
    # 测试不同状态的工具
    for tool in tools:
        print(f"\n🧪 测试工具: {tool.name} (状态: {tool.status})")
        
        # 构造测试数据
        test_data = {
            'pipeline_id': pipeline.id,
            'cicd_tool_id': tool.id,
            'parameters': {}
        }
        
        # 创建序列化器并验证
        serializer = PipelineExecutionSerializer(data=test_data)
        
        if serializer.is_valid():
            print(f"  ✅ 验证通过 - {tool.name} 可以触发流水线")
        else:
            print(f"  ❌ 验证失败 - {tool.name}: {serializer.errors}")
    
    # 总结
    authenticated_tools = tools.filter(status='authenticated')
    print(f"\n📊 总结:")
    print(f"  - 总工具数量: {tools.count()}")
    print(f"  - 已认证工具数量: {authenticated_tools.count()}")
    print(f"  - 可用于触发流水线的工具: {list(authenticated_tools.values_list('name', flat=True))}")

def test_status_choices():
    """测试状态选择是否更新"""
    print("\n🔍 测试状态选择更新...")
    
    status_choices = dict(CICDTool.STATUSES)
    print("📋 可用状态:")
    for key, value in status_choices.items():
        print(f"  - {key}: {value}")
    
    # 检查新状态是否包含
    required_statuses = ['authenticated', 'needs_auth', 'offline', 'unknown']
    for status in required_statuses:
        if status in status_choices:
            print(f"  ✅ {status} 状态已定义")
        else:
            print(f"  ❌ {status} 状态缺失")

if __name__ == "__main__":
    try:
        test_status_choices()
        test_tool_status_validation()
        print("\n🎉 测试完成！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
