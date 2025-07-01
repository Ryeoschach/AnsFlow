#!/usr/bin/env python3
"""
简单的HTTP请求测试脚本 - 不依赖Django
"""
import requests
import json

def test_api_with_curl():
    """使用curl风格的测试"""
    print("=== 使用 requests 测试 API ===\n")
    
    base_url = "http://127.0.0.1:3000/api/v1/pipelines/pipelines"
    pipeline_id = 12
    
    # 1. 测试GET请求（不需要认证）
    print("1. 测试 GET 请求...")
    get_url = f"{base_url}/{pipeline_id}/"
    
    try:
        response = requests.get(get_url)
        print(f"GET 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ GET 成功")
            print(f"流水线名称: {data.get('name')}")
            print(f"执行模式: {data.get('execution_mode', '未设置')}")
            
            # 2. 准备PUT数据
            put_data = {
                "name": data.get("name", "Test Pipeline") + " (Updated)",
                "description": data.get("description", "") + " Updated via script",
                "project": data.get("project"),
                "execution_mode": "local"
            }
            
            # 保留必要的字段
            for field in ["is_active", "config", "execution_tool", "tool_job_name", "tool_job_config"]:
                if field in data:
                    put_data[field] = data[field]
            
            print(f"\n2. 准备 PUT 数据:")
            print(json.dumps(put_data, indent=2, ensure_ascii=False))
            
            # 3. 发送PUT请求
            print(f"\n3. 发送 PUT 请求...")
            put_response = requests.put(
                get_url,
                json=put_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
            print(f"PUT 状态码: {put_response.status_code}")
            print(f"PUT 响应头: {dict(put_response.headers)}")
            
            if put_response.status_code == 400:
                print("❌ 400 Bad Request 详细信息:")
                print(f"原始响应: {put_response.text}")
                try:
                    error_json = put_response.json()
                    print(f"JSON 错误: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
                except:
                    print("响应不是有效的JSON")
            elif put_response.status_code == 200:
                print("✅ PUT 成功!")
                print(f"更新后数据: {json.dumps(put_response.json(), indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ 意外状态码: {put_response.status_code}")
                print(f"响应: {put_response.text}")
                
        elif response.status_code == 401:
            print("❌ 需要认证，尝试测试不需要认证的端点...")
            test_health_endpoint()
        else:
            print(f"❌ GET 失败: {response.status_code}")
            print(f"响应: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 确保服务正在运行")
    except Exception as e:
        print(f"❌ 异常: {e}")

def test_health_endpoint():
    """测试健康检查端点"""
    print("\n=== 测试健康检查端点 ===")
    
    health_urls = [
        "http://127.0.0.1:3000/api/v1/pipelines/health/",
        "http://127.0.0.1:3000/health/",
        "http://127.0.0.1:3000/api/health/"
    ]
    
    for url in health_urls:
        try:
            print(f"测试: {url}")
            response = requests.get(url)
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                print(f"响应: {response.text}")
                break
        except:
            print("连接失败")

def test_options_request():
    """测试OPTIONS请求以检查CORS和可用方法"""
    print("\n=== 测试 OPTIONS 请求 ===")
    
    url = "http://127.0.0.1:3000/api/v1/pipelines/pipelines/12/"
    
    try:
        response = requests.options(url)
        print(f"OPTIONS 状态码: {response.status_code}")
        print(f"允许的方法: {response.headers.get('Allow', '未设置')}")
        print(f"CORS头: {response.headers.get('Access-Control-Allow-Methods', '未设置')}")
        print(f"所有响应头: {dict(response.headers)}")
    except Exception as e:
        print(f"OPTIONS 请求失败: {e}")

if __name__ == "__main__":
    print("🔧 流水线 API 调试工具\n")
    
    # 测试主要功能
    test_api_with_curl()
    
    # 测试OPTIONS
    test_options_request()
    
    print("\n✅ 测试完成")
