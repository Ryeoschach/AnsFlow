#!/usr/bin/env python3
"""
验证API端点的脚本
检查流水线编辑和执行的API端点
"""
import requests
import json

def test_pipeline_endpoints():
    """测试流水线相关的API端点"""
    base_url = "http://127.0.0.1:8000"
    
    # 测试各个端点
    endpoints = [
        ("/api/v1/pipelines/pipelines/", "GET", "流水线列表"),
        ("/api/v1/pipelines/pipelines/12/", "GET", "获取单个流水线"),
        ("/api/v1/cicd/executions/", "GET", "执行列表"),
        ("/api/v1/cicd/tools/", "GET", "工具列表"),
    ]
    
    for endpoint, method, description in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            if method == "GET":
                response = requests.get(url)
            
            print(f"{description}: {method} {endpoint}")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"响应字段: {list(data.keys())}")
                    elif isinstance(data, list) and data:
                        print(f"数组长度: {len(data)}, 第一项字段: {list(data[0].keys()) if data else '空'}")
                except:
                    print(f"响应内容: {response.text[:200]}...")
            else:
                print(f"错误响应: {response.text}")
            
            print("-" * 50)
            
        except Exception as e:
            print(f"请求失败: {e}")
            print("-" * 50)

def test_pipeline_update():
    """测试流水线更新（使用Django管理命令获取token）"""
    print("建议直接在Django shell中测试：")
    print("python manage.py shell")
    print(">>> from pipelines.models import Pipeline")
    print(">>> from pipelines.serializers import PipelineSerializer")
    print(">>> pipeline = Pipeline.objects.get(id=12)")
    print(">>> print(pipeline.name)")
    print(">>> # 测试序列化器验证")
    print(">>> serializer = PipelineSerializer(pipeline)")
    print(">>> print(serializer.data)")
    print("\n或者在前端开发服务器中检查网络请求详情")

def test_different_ports():
    """测试不同端口的API响应"""
    pipeline_id = 12
    
    ports = [
        (8000, "Django API"),
        (3000, "前端代理"),
    ]
    
    for port, description in ports:
        url = f"http://127.0.0.1:{port}/api/v1/pipelines/pipelines/{pipeline_id}/"
        print(f"\n测试 {description} (端口 {port}):")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, timeout=5)
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text[:200]}...")
        except requests.exceptions.ConnectionError:
            print("连接拒绝 - 服务可能未运行")
        except requests.exceptions.Timeout:
            print("请求超时")
        except Exception as e:
            print(f"请求失败: {e}")

def check_wrong_endpoints():
    """检查错误的端点"""
    wrong_endpoints = [
        "http://127.0.0.1:3000/api/v1/pipelines/pipelines/12/",
        "http://127.0.0.1:3000/api/v1/cicd/executions/",
    ]
    
    print("检查错误的端点（3000端口）:")
    for url in wrong_endpoints:
        try:
            response = requests.get(url, timeout=5)
            print(f"{url}: {response.status_code}")
        except Exception as e:
            print(f"{url}: 连接失败 - {e}")

if __name__ == '__main__':
    print("=== 测试API端点 ===")
    test_pipeline_endpoints()
    
    print("\n=== 测试不同端口 ===")
    test_different_ports()
    
    print("\n=== 测试流水线更新 ===")
    test_pipeline_update()
    
    print("\n=== 诊断建议 ===")
    print("1. 检查前端是否运行在开发模式（npm run dev）")
    print("2. 检查前端网络请求是否发送到正确的端口（8000）")
    print("3. 在浏览器开发者工具中检查网络请求详情")
    print("4. 确认error来自哪个具体的API端点")
