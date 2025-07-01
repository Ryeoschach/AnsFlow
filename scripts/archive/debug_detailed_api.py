#!/usr/bin/env python3
"""
详细调试流水线触发API的脚本
用于排查"CI/CD tool is not active"错误
"""

import os
import sys
import django
import requests
import json
from pprint import pprint

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')

django.setup()

from cicd_integrations.models import CICDTool, PipelineExecution
from cicd_integrations.serializers import PipelineExecutionCreateSerializer
from pipelines.models import Pipeline

def debug_tool_status():
    """调试工具状态"""
    print("=== 调试工具状态 ===")
    
    try:
        tool = CICDTool.objects.get(id=3)
        print(f"工具ID: {tool.id}")
        print(f"工具名称: {tool.name}")
        print(f"工具类型: {tool.tool_type}")
        print(f"工具状态: {tool.status}")
        print(f"最后健康检查: {tool.last_health_check}")
        print(f"工具配置: {tool.config}")
        print()
        
        # 检查所有工具状态
        print("=== 所有工具状态 ===")
        for t in CICDTool.objects.all():
            print(f"ID: {t.id}, 名称: {t.name}, 状态: {t.status}")
        print()
        
        return tool
    except CICDTool.DoesNotExist:
        print("工具ID 3 不存在")
        return None

def debug_pipeline_status():
    """调试流水线状态"""
    print("=== 调试流水线状态 ===")
    
    try:
        pipeline = Pipeline.objects.get(id=1)
        print(f"流水线ID: {pipeline.id}")
        print(f"流水线名称: {pipeline.name}")
        print(f"流水线状态: {pipeline.status}")
        print(f"流水线是否活跃: {pipeline.is_active}")
        print(f"执行工具: {pipeline.execution_tool}")
        print(f"执行模式: {pipeline.execution_mode}")
        print()
        
        return pipeline
    except Pipeline.DoesNotExist:
        print("流水线ID 1 不存在")
        return None

def test_serializer_validation():
    """测试序列化器验证"""
    print("=== 测试序列化器验证 ===")
    
    data = {
        'pipeline_id': 1,
        'cicd_tool_id': 3,
        'trigger_type': 'manual',
        'parameters': {'branch': 'main'}
    }
    
    print(f"测试数据: {data}")
    
    try:
        serializer = PipelineExecutionCreateSerializer(data=data)
        is_valid = serializer.is_valid()
        print(f"序列化器验证结果: {is_valid}")
        
        if is_valid:
            print("验证成功!")
            print(f"验证后数据: {serializer.validated_data}")
        else:
            print("验证失败!")
            print(f"错误: {serializer.errors}")
            
    except Exception as e:
        print(f"序列化器测试异常: {e}")
        import traceback
        traceback.print_exc()

def test_api_call():
    """测试API调用"""
    print("=== 测试API调用 ===")
    
    # API端点
    url = "http://localhost:8000/api/cicd/executions/"
    
    # 请求数据
    data = {
        'pipeline_id': 1,
        'cicd_tool_id': 3,
        'trigger_type': 'manual',
        'parameters': {'branch': 'main'}
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_TOKEN_HERE'  # 需要替换为实际token
    }
    
    print(f"请求URL: {url}")
    print(f"请求数据: {json.dumps(data, indent=2)}")
    print(f"请求头: {json.dumps(headers, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"响应文本: {response.text}")
            
    except Exception as e:
        print(f"API调用异常: {e}")

def check_database_consistency():
    """检查数据库一致性"""
    print("=== 检查数据库一致性 ===")
    
    # 检查是否有多个数据库连接
    from django.db import connections
    print(f"数据库连接: {list(connections.databases.keys())}")
    
    # 检查工具是否真的存在且状态正确
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, status FROM cicd_integrations_cicdtool WHERE id = 3")
    row = cursor.fetchone()
    if row:
        print(f"直接SQL查询结果: ID={row[0]}, 名称={row[1]}, 状态={row[2]}")
    else:
        print("直接SQL查询: 工具ID 3 不存在")

def main():
    """主函数"""
    print("开始详细调试流水线触发API...")
    print("=" * 50)
    
    # 1. 调试工具状态
    tool = debug_tool_status()
    
    # 2. 调试流水线状态
    pipeline = debug_pipeline_status()
    
    # 3. 检查数据库一致性
    check_database_consistency()
    
    # 4. 测试序列化器验证
    test_serializer_validation()
    
    # 5. 测试API调用 (需要token)
    print("注意: API调用需要有效的认证token")
    # test_api_call()
    
    print("=" * 50)
    print("调试完成")

if __name__ == "__main__":
    main()
