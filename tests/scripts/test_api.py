#!/usr/bin/env python3
"""
测试Django API 8000端口的流水线PUT请求
"""
import requests
import json

def test_django_api():
    """测试Django API"""
    print("=== 测试Django API (8000端口) ===")
    
    # Django API URL
    base_url = "http://127.0.0.1:8000"
    pipeline_id = 12
    
    # 测试健康检查
    try:
        health_response = requests.get(f"{base_url}/api/v1/pipelines/health/")
        print(f"健康检查状态: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"健康检查响应: {health_response.json()}")
    except Exception as e:
        print(f"健康检查失败: {e}")
    
    # 测试获取流水线列表
    try:
        list_response = requests.get(f"{base_url}/api/v1/pipelines/pipelines/")
        print(f"流水线列表状态: {list_response.status_code}")
        if list_response.status_code == 200:
            pipelines = list_response.json()
            print(f"找到 {len(pipelines)} 个流水线")
        elif list_response.status_code == 401:
            print("需要认证")
        else:
            print(f"列表请求失败: {list_response.text}")
    except Exception as e:
        print(f"列表请求异常: {e}")
    
    # 测试获取特定流水线
    try:
        get_response = requests.get(f"{base_url}/api/v1/pipelines/pipelines/{pipeline_id}/")
        print(f"获取流水线{pipeline_id}状态: {get_response.status_code}")
        
        if get_response.status_code == 200:
            pipeline_data = get_response.json()
            print(f"流水线名称: {pipeline_data.get('name')}")
            print(f"流水线字段: {list(pipeline_data.keys())}")
            
            # 尝试PUT更新
            put_data = {
                'name': pipeline_data['name'],
                'description': pipeline_data.get('description', ''),
                'is_active': True,
                'project': pipeline_data['project'],
                'execution_mode': 'local',
                'config': pipeline_data.get('config', {}),
                'steps': []
            }
            
            print(f"准备PUT数据: {json.dumps(put_data, indent=2)}")
            
            put_response = requests.put(
                f"{base_url}/api/v1/pipelines/pipelines/{pipeline_id}/",
                json=put_data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"PUT请求状态: {put_response.status_code}")
            if put_response.status_code != 200:
                print(f"PUT失败响应: {put_response.text}")
                try:
                    error_json = put_response.json()
                    print(f"错误详情: {json.dumps(error_json, indent=2)}")
                except:
                    pass
            else:
                print("PUT请求成功!")
                
        elif get_response.status_code == 401:
            print("需要认证才能访问流水线")
        else:
            print(f"获取流水线失败: {get_response.text}")
            
    except Exception as e:
        print(f"GET/PUT请求异常: {e}")

def main():
    """主函数"""
    print("开始测试Django API...\n")
    test_django_api()
    print("\n测试完成!")
    """Test health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/api/health/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)

def test_authentication():
    """Test JWT authentication"""
    print("Testing authentication...")
    
    # Try to get token
    auth_data = {
        "username": "admin",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/token/", json=auth_data)
    print(f"Auth Status: {response.status_code}")
    
    if response.status_code == 200:
        tokens = response.json()
        print(f"Access Token: {tokens['access'][:50]}...")
        return tokens['access']
    else:
        print(f"Auth failed: {response.text}")
        return None

def test_projects_api(token=None):
    """Test projects API"""
    print("Testing projects API...")
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    response = requests.get(f"{BASE_URL}/api/v1/projects/projects/", headers=headers)
    print(f"Projects Status: {response.status_code}")
    
    if response.status_code == 200:
        projects = response.json()
        print(f"Found {len(projects['results']) if 'results' in projects else len(projects)} projects")
        if projects:
            first_project = projects['results'][0] if 'results' in projects else projects[0]
            print(f"First project: {first_project.get('name', 'N/A')}")
    else:
        print(f"Projects API failed: {response.text}")
    print("-" * 50)

def test_pipelines_api(token=None):
    """Test pipelines API"""
    print("Testing pipelines API...")
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    response = requests.get(f"{BASE_URL}/api/v1/pipelines/pipelines/", headers=headers)
    print(f"Pipelines Status: {response.status_code}")
    
    if response.status_code == 200:
        pipelines = response.json()
        print(f"Found {len(pipelines['results']) if 'results' in pipelines else len(pipelines)} pipelines")
        if pipelines:
            first_pipeline = pipelines['results'][0] if 'results' in pipelines else pipelines[0]
            print(f"First pipeline: {first_pipeline.get('name', 'N/A')}")
    else:
        print(f"Pipelines API failed: {response.text}")
    print("-" * 50)

def main():
    print("=" * 60)
    print("AnsFlow Django API Test")
    print("=" * 60)
    
    # Test health check
    test_health_check()
    
    # Test authentication
    token = test_authentication()
    
    # Test API endpoints
    test_projects_api(token)
    test_pipelines_api(token)
    
    print("=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    main()
