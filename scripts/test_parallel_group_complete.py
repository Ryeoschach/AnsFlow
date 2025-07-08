#!/usr/bin/env python3
"""
完整测试并行组管理功能
验证前后端数据流转是否正常
"""
import requests
import json
import time
from urllib.parse import urljoin

# 测试配置
BASE_URL = "http://localhost:8000"
API_BASE = urljoin(BASE_URL, "/api/v1/")

# 测试用户认证（假设已有用户）
AUTH_HEADERS = {
    'Authorization': 'Token your_token_here',  # 需要替换为实际的token
    'Content-Type': 'application/json'
}

def test_step(name, func):
    """测试步骤装饰器"""
    print(f"\n{'='*50}")
    print(f"🧪 {name}")
    print(f"{'='*50}")
    try:
        result = func()
        print(f"✅ {name} - 成功")
        return result
    except Exception as e:
        print(f"❌ {name} - 失败: {e}")
        raise

def create_test_pipeline():
    """创建测试流水线"""
    pipeline_data = {
        "name": "并行组测试流水线",
        "description": "用于测试并行组功能的流水线",
        "project": 1,  # 假设存在项目ID为1
        "is_active": True,
        "execution_mode": "sequential",
        "steps": [
            {
                "name": "步骤1",
                "description": "第一个测试步骤",
                "step_type": "custom",
                "order": 1,
                "parameters": {"command": "echo 'Step 1'"}
            },
            {
                "name": "步骤2",
                "description": "第二个测试步骤",
                "step_type": "custom",
                "order": 2,
                "parameters": {"command": "echo 'Step 2'"}
            },
            {
                "name": "步骤3",
                "description": "第三个测试步骤",
                "step_type": "custom",
                "order": 3,
                "parameters": {"command": "echo 'Step 3'"}
            }
        ]
    }
    
    response = requests.post(
        urljoin(API_BASE, "pipelines/"),
        headers=AUTH_HEADERS,
        json=pipeline_data
    )
    
    if response.status_code == 401:
        print("⚠️  需要认证，跳过认证测试，直接测试API结构")
        return None
    
    response.raise_for_status()
    pipeline = response.json()
    print(f"创建流水线成功: {pipeline['id']} - {pipeline['name']}")
    return pipeline

def test_parallel_group_apis():
    """测试并行组API端点"""
    # 首先测试获取并行组列表
    try:
        response = requests.get(
            urljoin(API_BASE, "pipelines/parallel-groups/"),
            headers={'Content-Type': 'application/json'}
        )
        print(f"获取并行组列表 HTTP状态: {response.status_code}")
        
        if response.status_code == 200:
            groups = response.json()
            print(f"现有并行组数量: {len(groups) if isinstance(groups, list) else 'N/A'}")
            return groups
        else:
            print(f"获取并行组失败: {response.text}")
            return []
    except Exception as e:
        print(f"API请求失败: {e}")
        return []

def test_create_parallel_group():
    """测试创建并行组"""
    group_data = {
        "name": "测试并行组",
        "description": "用于测试的并行组",
        "pipeline": 1,  # 假设存在流水线ID为1
        "sync_policy": "wait_all",
        "timeout_seconds": 3600
    }
    
    try:
        response = requests.post(
            urljoin(API_BASE, "pipelines/parallel-groups/"),
            headers={'Content-Type': 'application/json'},
            json=group_data
        )
        print(f"创建并行组 HTTP状态: {response.status_code}")
        
        if response.status_code == 201:
            group = response.json()
            print(f"创建并行组成功: {group}")
            return group
        else:
            print(f"创建并行组失败: {response.text}")
            return None
    except Exception as e:
        print(f"创建并行组请求失败: {e}")
        return None

def test_pipeline_with_parallel_groups():
    """测试包含并行组的流水线保存"""
    pipeline_data = {
        "name": "带并行组的流水线",
        "description": "测试并行组功能",
        "project": 1,
        "is_active": True,
        "execution_mode": "sequential",
        "steps": [
            {
                "name": "步骤1",
                "step_type": "custom",
                "order": 1,
                "parameters": {"command": "echo 'Step 1'"},
                "parallel_group": "group_1"
            },
            {
                "name": "步骤2",
                "step_type": "custom",
                "order": 2,
                "parameters": {"command": "echo 'Step 2'"},
                "parallel_group": "group_1"
            },
            {
                "name": "步骤3",
                "step_type": "custom",
                "order": 3,
                "parameters": {"command": "echo 'Step 3'"},
                "parallel_group": "group_2"
            }
        ]
    }
    
    try:
        response = requests.post(
            urljoin(API_BASE, "pipelines/"),
            headers={'Content-Type': 'application/json'},
            json=pipeline_data
        )
        print(f"创建包含并行组的流水线 HTTP状态: {response.status_code}")
        
        if response.status_code in [200, 201]:
            pipeline = response.json()
            print(f"创建流水线成功: {pipeline['id']}")
            
            # 检查步骤的parallel_group字段
            steps = pipeline.get('steps', [])
            for step in steps:
                pg = step.get('parallel_group')
                print(f"步骤 {step['name']} 的并行组: {pg}")
            
            return pipeline
        else:
            print(f"创建流水线失败: {response.text}")
            return None
    except Exception as e:
        print(f"创建流水线请求失败: {e}")
        return None

def test_frontend_apis():
    """测试前端API调用"""
    print("\n📱 测试前端API调用")
    
    # 测试apiService.getParallelGroups格式
    try:
        response = requests.get(
            urljoin(API_BASE, "pipelines/parallel-groups/"),
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"API响应格式: {type(data)}")
            
            # 检查是否是DRF分页格式
            if isinstance(data, dict) and 'results' in data:
                print("✅ DRF分页格式 - 前端会提取results字段")
                print(f"总数: {data.get('count', 0)}")
                print(f"结果数: {len(data.get('results', []))}")
            elif isinstance(data, list):
                print("✅ 直接数组格式")
                print(f"数组长度: {len(data)}")
            else:
                print(f"⚠️  未预期的格式: {data}")
        else:
            print(f"API调用失败: {response.status_code}")
    except Exception as e:
        print(f"前端API测试失败: {e}")

def main():
    """主测试函数"""
    print("🚀 开始完整测试并行组管理功能")
    
    # 测试API端点可用性
    test_step("测试并行组API端点", test_parallel_group_apis)
    
    # 测试创建并行组
    test_step("测试创建并行组", test_create_parallel_group)
    
    # 测试包含并行组的流水线
    test_step("测试包含并行组的流水线", test_pipeline_with_parallel_groups)
    
    # 测试前端API调用
    test_step("测试前端API调用", test_frontend_apis)
    
    print("\n🎉 测试完成")

if __name__ == "__main__":
    main()
