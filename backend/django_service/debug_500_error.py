#!/usr/bin/env python3
"""
简单的500错误诊断脚本
用于快速诊断/api/v1/executions/7/的500错误
"""

import sys
import os
import traceback

# 添加Django项目路径
django_path = "/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service"
if django_path not in sys.path:
    sys.path.append(django_path)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

try:
    import django
    django.setup()
    print("✅ Django环境设置成功")
    
    # 测试导入
    from cicd_integrations.views import PipelineExecutionViewSet
    from cicd_integrations.models import PipelineExecution
    from rest_framework.test import APIRequestFactory
    from django.contrib.auth.models import User
    
    print("✅ 模块导入成功")
    
    # 测试数据库连接
    execution_count = PipelineExecution.objects.count()
    print(f"✅ 数据库连接正常，找到{execution_count}个执行记录")
    
    # 检查execution ID 7是否存在
    try:
        execution = PipelineExecution.objects.get(id=7)
        print(f"✅ 找到执行记录ID 7: {execution.pipeline.name}")
    except PipelineExecution.DoesNotExist:
        print("⚠️ 执行记录ID 7不存在")
    
    # 模拟API请求
    factory = APIRequestFactory()
    request = factory.get('/api/v1/executions/7/')
    
    # 创建视图实例
    view = PipelineExecutionViewSet()
    view.action = 'retrieve'
    view.request = request
    view.format_kwarg = None
    
    try:
        # 测试获取对象
        view.kwargs = {'pk': 7}
        obj = view.get_object()
        print(f"✅ ViewSet正常工作，获取到对象: {obj.id}")
    except Exception as e:
        print(f"❌ ViewSet错误: {e}")
        traceback.print_exc()

except ImportError as e:
    print(f"❌ 导入错误: {e}")
except Exception as e:
    print(f"❌ 其他错误: {e}")
    traceback.print_exc()
