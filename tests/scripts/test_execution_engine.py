#!/usr/bin/env python
"""
测试流水线执行引擎的脚本
"""

import os
import sys
import django

# Django设置
django_path = "/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service"
if django_path not in sys.path:
    sys.path.append(django_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from pipelines.models import Pipeline
from pipelines.services.execution_engine import execution_engine
from django.contrib.auth.models import User

def test_execution_engine():
    """测试执行引擎"""
    
    # 获取一个测试流水线
    pipeline = Pipeline.objects.filter(execution_mode='remote').first()
    if not pipeline:
        print("没有找到remote模式的流水线")
        return
    
    print(f"测试流水线: {pipeline.name}")
    print(f"执行模式: {pipeline.execution_mode}")
    print(f"执行工具: {pipeline.execution_tool}")
    print(f"工具作业名: {pipeline.tool_job_name}")
    
    # 获取admin用户
    user = User.objects.get(username='admin')
    
    # 准备触发数据
    trigger_data = {
        'trigger_type': 'manual',
        'triggered_via': 'test_script',
        'user_id': user.id
    }
    
    try:
        # 执行流水线
        print("\n开始执行流水线...")
        result = execution_engine.execute_pipeline(pipeline, user, trigger_data)
        print(f"执行结果: {result}")
        print(f"运行ID: {result.id}")
        print(f"状态: {result.status}")
        print(f"触发数据: {result.trigger_data}")
        
    except Exception as e:
        print(f"执行异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_execution_engine()
