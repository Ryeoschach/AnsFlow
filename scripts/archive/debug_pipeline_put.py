#!/usr/bin/env python3
"""
调试流水线PUT请求的脚本 - 使用 requests 直接测试
用于排查400 Bad Request错误
"""
import requests
import json

def test_pipeline_put_request():
    """直接测试 PUT 请求"""
    base_url = "http://127.0.0.1:3000/api/v1/pipelines/pipelines"
    pipeline_id = 12
    
    print(f"🔍 测试流水线 {pipeline_id} 的 PUT 请求...")
    
    # 1. 首先获取现有数据
    get_url = f"{base_url}/{pipeline_id}/"
    
    try:
        print("📥 获取当前流水线数据...")
        get_response = requests.get(get_url)
        print(f"GET 状态码: {get_response.status_code}")
        
        if get_response.status_code != 200:
            print(f"❌ 无法获取流水线数据: {get_response.text}")
            return
            
        current_data = get_response.json()
        print("✅ 成功获取当前数据")
        print(f"当前流水线名称: {current_data.get('name')}")
        print(f"当前执行模式: {current_data.get('execution_mode', '未设置')}")
        
        # 2. 准备最小的更新数据
        update_data = {
            "name": current_data.get("name", "Test Pipeline"),
            "description": current_data.get("description", ""),
            "project": current_data.get("project"),
            "is_active": current_data.get("is_active", True),
            "execution_mode": "local"  # 确保设置执行模式
        }
        
        # 如果有其他必要字段，也包含进去
        for field in ["config", "execution_tool", "tool_job_name", "tool_job_config"]:
            if field in current_data:
                update_data[field] = current_data[field]
        
        print(f"\n📤 准备发送的更新数据:")
        print(json.dumps(update_data, indent=2, ensure_ascii=False))
        
        # 3. 发送 PUT 请求
        print(f"\n🚀 发送 PUT 请求到: {get_url}")
        put_response = requests.put(
            get_url,
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"PUT 状态码: {put_response.status_code}")
        
        if put_response.status_code == 200:
            print("✅ 更新成功!")
            response_data = put_response.json()
            print(f"返回数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        elif put_response.status_code == 400:
            print("❌ 400 Bad Request 错误:")
            try:
                error_data = put_response.json()
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(f"原始错误响应: {put_response.text}")
        else:
            print(f"❌ 其他错误 ({put_response.status_code}): {put_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误: 确保Django服务正在运行 (http://127.0.0.1:3000)")
    except Exception as e:
        print(f"❌ 异常: {e}")

def test_minimal_put():
    """测试最小数据的 PUT 请求"""
    url = "http://127.0.0.1:3000/api/v1/pipelines/pipelines/12/"
    
    minimal_data = {
        "name": "Updated Pipeline Name"
    }
    
    print("\n🧪 测试最小数据的 PUT 请求...")
    print(f"数据: {json.dumps(minimal_data, indent=2)}")
    
    try:
        response = requests.put(
            url,
            json=minimal_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    print("=== 流水线 PUT 请求调试工具 ===\n")
    
    # 测试完整的 PUT 请求
    test_pipeline_put_request()
    
    print("\n" + "="*60 + "\n")
    
    # 测试最小的 PUT 请求
    test_minimal_put()

from pipelines.models import Pipeline
from pipelines.serializers import PipelineSerializer
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

def test_pipeline_serializer():
    """测试流水线序列化器"""
    print("=== 测试流水线序列化器 ===")
    
    try:
        # 获取一个现有的流水线
        pipeline = Pipeline.objects.get(id=12)
        print(f"找到流水线: {pipeline.name}")
        
        # 测试序列化
        serializer = PipelineSerializer(pipeline)
        data = serializer.data
        print(f"序列化成功，字段: {list(data.keys())}")
        
        # 创建一个mock请求
        factory = APIRequestFactory()
        request = factory.put('/api/v1/pipelines/pipelines/12/')
        user = User.objects.first()
        request.user = user
        
        # 测试反序列化
        test_data = {
            'name': pipeline.name,
            'description': pipeline.description,
            'is_active': True,
            'project': pipeline.project.id,
            'execution_mode': 'local',
            'config': {},
            'steps': []
        }
        
        serializer = PipelineSerializer(
            pipeline, 
            data=test_data, 
            context={'request': Request(request)}
        )
        
        if serializer.is_valid():
            print("反序列化验证成功")
            return True
        else:
            print(f"反序列化验证失败: {serializer.errors}")
            return False
            
    except Exception as e:
        print(f"测试失败: {e}")
        return False

def test_api_request():
    """测试实际的API请求"""
    print("\n=== 测试API请求 ===")
    
    # 获取流水线数据
    get_url = "http://127.0.0.1:8000/api/v1/pipelines/pipelines/12/"
    
    try:
        # 先GET获取当前数据
        response = requests.get(get_url)
        print(f"GET请求状态码: {response.status_code}")
        
        if response.status_code == 200:
            current_data = response.json()
            print(f"当前流水线数据字段: {list(current_data.keys())}")
            
            # 准备PUT数据（只包含必要字段）
            put_data = {
                'name': current_data['name'],
                'description': current_data.get('description', ''),
                'is_active': current_data.get('is_active', True),
                'project': current_data['project'],
                'execution_mode': current_data.get('execution_mode', 'local'),
                'config': current_data.get('config', {}),
                'execution_tool': current_data.get('execution_tool'),
                'tool_job_name': current_data.get('tool_job_name', ''),
                'tool_job_config': current_data.get('tool_job_config', {}),
                'steps': current_data.get('steps', [])
            }
            
            # 移除None值
            put_data = {k: v for k, v in put_data.items() if v is not None}
            
            print(f"准备发送的PUT数据: {json.dumps(put_data, indent=2, ensure_ascii=False)}")
            
            # 发送PUT请求
            put_url = "http://127.0.0.1:8000/api/v1/pipelines/pipelines/12/"
            headers = {'Content-Type': 'application/json'}
            
            put_response = requests.put(put_url, json=put_data, headers=headers)
            print(f"PUT请求状态码: {put_response.status_code}")
            
            if put_response.status_code != 200:
                print(f"PUT请求失败:")
                print(f"响应内容: {put_response.text}")
                try:
                    error_data = put_response.json()
                    print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    pass
            else:
                print("PUT请求成功!")
                
        else:
            print(f"GET请求失败: {response.text}")
            
    except Exception as e:
        print(f"API测试失败: {e}")

def check_model_fields():
    """检查模型字段"""
    print("\n=== 检查模型字段 ===")
    
    try:
        pipeline = Pipeline.objects.get(id=12)
        
        # 检查字段是否存在
        required_fields = [
            'execution_mode', 'execution_tool', 'tool_job_name', 'tool_job_config'
        ]
        
        for field in required_fields:
            if hasattr(pipeline, field):
                value = getattr(pipeline, field)
                print(f"字段 {field}: {value} (类型: {type(value)})")
            else:
                print(f"⚠️  缺少字段: {field}")
        
        # 检查相关的外键字段
        print(f"project: {pipeline.project}")
        print(f"created_by: {pipeline.created_by}")
        print(f"execution_tool: {pipeline.execution_tool}")
        
        return True
        
    except Exception as e:
        print(f"字段检查失败: {e}")
        return False

def main():
    """主函数"""
    print("开始调试流水线PUT请求问题...\n")
    
    # 1. 检查模型字段
    if not check_model_fields():
        print("❌ 模型字段检查失败")
        return
    
    # 2. 测试序列化器
    if not test_pipeline_serializer():
        print("❌ 序列化器测试失败")
        return
    
    # 3. 测试API请求
    test_api_request()
    
    print("\n调试完成!")

if __name__ == '__main__':
    main()
