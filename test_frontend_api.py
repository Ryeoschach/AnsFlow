#!/usr/bin/env python3
"""
测试前端API调用 - 验证前端能正确访问后端日志API
"""

import requests
import json

def test_frontend_api_call():
    """模拟前端API调用"""
    
    # 使用新的有效token
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUxMzg1NTgzLCJpYXQiOjE3NTEzODE5ODMsImp0aSI6IjA1NDExNzQwYzk0ZTQxZDBiMWFhMTY3MzgwYmNjODBjIiwidXNlcl9pZCI6MX0.QSQ3RI_WHt9QnlzT5fdw9t43x6VH5zxVnNTkNFnrOko'
    
    execution_id = 33
    
    # 使用前端相同的API路径和headers
    url = f'http://localhost:8000/api/v1/cicd/executions/{execution_id}/logs/'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print(f"🔗 测试前端API调用: {url}")
    print(f"🔐 使用Token: {token[:50]}...")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"📊 HTTP状态码: {response.status_code}")
        print(f"📦 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API调用成功!")
            print(f"📝 logs字段存在: {'logs' in data}")
            print(f"📏 logs长度: {len(data.get('logs', ''))}")
            print(f"📄 logs类型: {type(data.get('logs', ''))}")
            
            logs_content = data.get('logs', '')
            if logs_content:
                print(f"📋 logs内容预览: {logs_content[:100]}...")
            else:
                print("⚠️  logs内容为空")
                
            # 输出完整响应结构
            print(f"🏗️  响应结构: {list(data.keys())}")
            print(f"📦 完整响应: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
            
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"📄 错误响应: {response.text}")
            
    except Exception as e:
        print(f"💥 请求异常: {e}")

if __name__ == '__main__':
    test_frontend_api_call()
