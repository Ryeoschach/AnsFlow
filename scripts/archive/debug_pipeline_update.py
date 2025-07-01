#!/usr/bin/env python3
"""
调试流水线更新请求
"""
import requests
import json

# 配置
API_BASE = "http://127.0.0.1:3000"
PIPELINE_ID = 12

def test_pipeline_update():
    """测试流水线更新"""
    
    # 首先获取现有流水线数据
    get_url = f"{API_BASE}/api/v1/pipelines/pipelines/{PIPELINE_ID}/"
    print(f"获取流水线数据: {get_url}")
    
    try:
        response = requests.get(get_url)
        print(f"GET Status: {response.status_code}")
        
        if response.status_code == 200:
            pipeline_data = response.json()
            print("当前流水线数据:")
            print(json.dumps(pipeline_data, indent=2, ensure_ascii=False))
            
            # 准备更新数据（只更新允许的字段）
            update_data = {
                'name': pipeline_data['name'],
                'description': pipeline_data['description'],
                'status': pipeline_data['status'],
                'is_active': pipeline_data['is_active'],
                'config': pipeline_data['config'],
                'project': pipeline_data['project'],
                'execution_mode': pipeline_data.get('execution_mode', 'local'),
                'execution_tool': pipeline_data.get('execution_tool'),
                'tool_job_name': pipeline_data.get('tool_job_name', ''),
                'tool_job_config': pipeline_data.get('tool_job_config', {}),
                # 去掉只读字段
                # 'steps': pipeline_data.get('steps', [])
            }
            
            print("\n准备更新的数据:")
            print(json.dumps(update_data, indent=2, ensure_ascii=False))
            
            # 发送更新请求
            put_url = f"{API_BASE}/api/v1/pipelines/pipelines/{PIPELINE_ID}/"
            print(f"\n发送PUT请求: {put_url}")
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            response = requests.put(put_url, json=update_data, headers=headers)
            print(f"PUT Status: {response.status_code}")
            print(f"PUT Response: {response.text}")
            
        else:
            print(f"无法获取流水线数据: {response.text}")
            
    except Exception as e:
        print(f"请求错误: {e}")

if __name__ == "__main__":
    test_pipeline_update()
