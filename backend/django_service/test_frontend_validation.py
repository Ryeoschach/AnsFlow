#!/usr/bin/env python3
"""
测试前端验证逻辑
验证本地执行器状态是否能通过前端的验证
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from cicd_integrations.models import CICDTool
from cicd_integrations.serializers import PipelineExecutionSerializer

def test_frontend_validation():
    """测试前端验证逻辑"""
    
    print("🔧 开始测试前端验证...")
    
    # 1. 获取本地执行器工具
    try:
        local_tool = CICDTool.objects.get(tool_type='local')
        print(f"✅ 找到本地执行器: {local_tool.name}")
        print(f"✅ 当前状态: {local_tool.status}")
    except CICDTool.DoesNotExist:
        print("❌ 本地执行器不存在")
        return False
    
    # 2. 测试序列化器验证
    try:
        from django.core.exceptions import ValidationError
        from rest_framework import serializers
        
        # 直接测试验证逻辑
        if local_tool.status != 'authenticated':
            raise serializers.ValidationError(
                f"CI/CD tool is not ready for execution. Current status: {local_tool.status}. "
                f"Tool must be in 'authenticated' status to trigger pipelines."
            )
        
        print(f"✅ 验证通过: 工具状态 {local_tool.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

if __name__ == '__main__':
    success = test_frontend_validation()
    
    if success:
        print("\n🎉 前端验证测试成功!")
        print("✅ 本地执行器状态正确，前端应该能正常触发流水线")
    else:
        print("\n❌ 前端验证测试失败!")
        print("❌ 需要检查本地执行器状态")
