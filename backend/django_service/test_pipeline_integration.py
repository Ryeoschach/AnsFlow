#!/usr/bin/env python
"""
流水线与CI/CD工具集成功能测试脚本
测试执行模式、工具关联和同步功能
"""

import requests
import json
import sys
import os

# Django设置
django_path = "/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service"
if django_path not in sys.path:
    sys.path.append(django_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

# API基础URL
BASE_URL = "http://localhost:8000"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print(f"{'='*60}")

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def get_jwt_token():
    """获取JWT认证token"""
    auth_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/token/", json=auth_data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('access')
    except Exception as e:
        print_error(f"获取JWT token失败: {e}")
    
    return None

def test_pipeline_api(jwt_token):
    """测试流水线API"""
    print_header("流水线API测试")
    
    headers = {'Authorization': f'Bearer {jwt_token}'}
    
    # 获取流水线列表
    try:
        response = requests.get(f"{BASE_URL}/api/v1/pipelines/pipelines/", headers=headers)
        if response.status_code == 200:
            pipelines = response.json()
            print_success(f"获取流水线列表成功 - 共 {len(pipelines)} 条记录")
            
            if pipelines:
                # 测试获取单个流水线详情
                first_pipeline = pipelines[0]
                pipeline_id = first_pipeline['id']
                print_info(f"测试流水线: {first_pipeline['name']} (ID: {pipeline_id})")
                
                # 检查新增的字段
                execution_mode = first_pipeline.get('execution_mode', 'local')
                execution_tool = first_pipeline.get('execution_tool')
                tool_job_name = first_pipeline.get('tool_job_name')
                
                print_info(f"执行模式: {execution_mode}")
                print_info(f"执行工具: {execution_tool}")
                print_info(f"工具作业名: {tool_job_name}")
                
                return pipeline_id
            else:
                print_info("没有找到流水线记录")
                return None
        else:
            print_error(f"获取流水线列表失败: {response.status_code}")
            print_error(f"错误信息: {response.text}")
    except Exception as e:
        print_error(f"流水线API测试异常: {e}")
    
    return None

def test_tools_api(jwt_token):
    """测试CI/CD工具API"""
    print_header("CI/CD工具API测试")
    
    headers = {'Authorization': f'Bearer {jwt_token}'}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cicd/tools/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            tools = data.get('results', data) if isinstance(data, dict) else data
            print_success(f"获取工具列表成功 - 共 {len(tools)} 条记录")
            
            if tools:
                first_tool = tools[0]
                tool_id = first_tool['id']
                print_info(f"测试工具: {first_tool['name']} (ID: {tool_id}, 类型: {first_tool['tool_type']})")
                return tool_id
            else:
                print_info("没有找到CI/CD工具记录")
                return None
        else:
            print_error(f"获取工具列表失败: {response.status_code}")
            print_error(f"错误信息: {response.text}")
    except Exception as e:
        print_error(f"工具API测试异常: {e}")
    
    return None

def test_create_pipeline_with_tool(jwt_token, tool_id):
    """测试创建带工具关联的流水线"""
    print_header("创建工具关联流水线测试")
    
    headers = {'Authorization': f'Bearer {jwt_token}'}
    
    # 获取项目列表
    try:
        projects_response = requests.get(f"{BASE_URL}/api/v1/projects/projects/", headers=headers)
        if projects_response.status_code == 200:
            projects_data = projects_response.json()
            projects = projects_data.get('results', projects_data) if isinstance(projects_data, dict) else projects_data
            
            if not projects:
                print_error("没有找到项目，无法创建流水线")
                return None
            
            project_id = projects[0]['id']
            print_info(f"使用项目: {projects[0]['name']} (ID: {project_id})")
            
            # 创建带工具关联的流水线
            pipeline_data = {
                'name': 'Integration Test Pipeline',
                'description': '测试工具集成功能的流水线',
                'project': project_id,
                'execution_mode': 'remote',
                'execution_tool': tool_id,
                'tool_job_name': 'test_integration_job',
                'is_active': True,
                'steps': [
                    {
                        'name': 'Build Step',
                        'step_type': 'build',
                        'description': '构建步骤',
                        'parameters': {'command': 'npm run build'},
                        'order': 1
                    },
                    {
                        'name': 'Test Step',
                        'step_type': 'test',
                        'description': '测试步骤',
                        'parameters': {'test_command': 'npm test'},
                        'order': 2
                    }
                ]
            }
            
            response = requests.post(f"{BASE_URL}/api/v1/pipelines/pipelines/", 
                                   json=pipeline_data, headers=headers)
            
            if response.status_code == 201:
                pipeline = response.json()
                print_success(f"创建工具关联流水线成功 - ID: {pipeline['id']}")
                print_info(f"执行模式: {pipeline.get('execution_mode')}")
                print_info(f"关联工具: {pipeline.get('execution_tool_name')}")
                return pipeline['id']
            else:
                print_error(f"创建流水线失败: {response.status_code}")
                print_error(f"错误信息: {response.text}")
                
        else:
            print_error(f"获取项目列表失败: {projects_response.status_code}")
            
    except Exception as e:
        print_error(f"创建流水线测试异常: {e}")
    
    return None

def test_pipeline_tool_mapping(jwt_token):
    """测试流水线工具映射API"""
    print_header("流水线工具映射API测试")
    
    headers = {'Authorization': f'Bearer {jwt_token}'}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/pipelines/pipeline-mappings/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            mappings = data.get('results', data) if isinstance(data, dict) else data
            print_success(f"获取工具映射列表成功 - 共 {len(mappings)} 条记录")
            
            if mappings:
                for mapping in mappings:
                    print_info(f"映射: Pipeline {mapping.get('pipeline_name')} -> Tool {mapping.get('tool_name')}")
                    print_info(f"外部作业: {mapping.get('external_job_name')}")
                    print_info(f"同步状态: {mapping.get('sync_status')}")
            else:
                print_info("没有找到工具映射记录")
        else:
            print_error(f"获取工具映射失败: {response.status_code}")
            print_error(f"错误信息: {response.text}")
    except Exception as e:
        print_error(f"工具映射API测试异常: {e}")

def test_execution_engine(jwt_token, pipeline_id):
    """测试执行引擎"""
    print_header("执行引擎测试")
    
    if not pipeline_id:
        print_error("没有可测试的流水线ID")
        return
    
    headers = {'Authorization': f'Bearer {jwt_token}'}
    
    try:
        # 测试运行流水线
        response = requests.post(f"{BASE_URL}/api/v1/pipelines/pipelines/{pipeline_id}/run/", 
                               headers=headers)
        
        if response.status_code == 200:
            run_data = response.json()
            print_success(f"流水线运行成功 - Run ID: {run_data.get('id')}")
            print_info(f"运行状态: {run_data.get('status')}")
            print_info(f"触发类型: {run_data.get('trigger_type')}")
            
            # 检查trigger_data中的执行信息
            trigger_data = run_data.get('trigger_data', {})
            execution_mode = trigger_data.get('execution_mode')
            if execution_mode:
                print_info(f"执行模式: {execution_mode}")
                
                if execution_mode == 'local':
                    task_id = trigger_data.get('celery_task_id')
                    if task_id:
                        print_info(f"Celery任务ID: {task_id}")
                elif execution_mode == 'remote':
                    tool_id = trigger_data.get('tool_id')
                    build_url = trigger_data.get('jenkins_build_url')
                    if tool_id:
                        print_info(f"工具ID: {tool_id}")
                    if build_url:
                        print_info(f"构建URL: {build_url}")
            
        else:
            print_error(f"流水线运行失败: {response.status_code}")
            print_error(f"错误信息: {response.text}")
            
    except Exception as e:
        print_error(f"执行引擎测试异常: {e}")

def main():
    print_header("AnsFlow 流水线集成功能测试")
    
    # 1. 获取认证token
    jwt_token = get_jwt_token()
    if not jwt_token:
        print_error("无法获取认证token，测试终止")
        return
    
    # 2. 测试流水线API
    pipeline_id = test_pipeline_api(jwt_token)
    
    # 3. 测试CI/CD工具API
    tool_id = test_tools_api(jwt_token)
    
    # 4. 测试创建工具关联的流水线
    if tool_id:
        new_pipeline_id = test_create_pipeline_with_tool(jwt_token, tool_id)
        if new_pipeline_id:
            pipeline_id = new_pipeline_id
    
    # 5. 测试流水线工具映射
    test_pipeline_tool_mapping(jwt_token)
    
    # 6. 测试执行引擎
    if pipeline_id:
        test_execution_engine(jwt_token, pipeline_id)
    
    print_header("测试完成")
    print_success("流水线集成功能测试完成")

if __name__ == "__main__":
    main()
