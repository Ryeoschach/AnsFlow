#!/usr/bin/env python3
"""
测试流水线更新API的脚本
用于验证前端发送的数据和后端的处理
"""
import requests
import json

# 后端API基础URL
BASE_URL = "http://localhost:8000/api/v1"

def test_pipeline_update():
    """测试流水线更新"""
    # 首先获取一个流水线列表
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/")
    if response.status_code != 200:
        print(f"无法获取流水线列表: {response.status_code}")
        print(response.text)
        return
    
    pipelines = response.json()
    print(f"获取到 {len(pipelines)} 个流水线")
    
    if not pipelines:
        print("没有找到流水线")
        return
    
    # 选择第一个流水线进行测试
    pipeline_id = pipelines[0]['id']
    print(f"测试流水线 ID: {pipeline_id}")
    
    # 构造更新数据（模拟前端发送的数据）
    update_data = {
        "name": "测试流水线更新",
        "description": "测试描述",
        "project": 1,  # 假设项目ID为1
        "is_active": True,
        "steps": [
            {
                "name": "测试步骤1",
                "step_type": "build",
                "description": "测试步骤描述",
                "parameters": {"param1": "value1"},
                "order": 1,
                "is_active": True
            }
        ]
    }
    
    print("发送的更新数据:")
    print(json.dumps(update_data, indent=2, ensure_ascii=False))
    
    # 发送PUT请求更新流水线
    response = requests.put(
        f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/",
        json=update_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\n响应状态码: {response.status_code}")
    print("响应内容:")
    
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        print("✅ 流水线更新成功")
    else:
        print(response.text)
        print("❌ 流水线更新失败")

def test_pipeline_update_without_steps():
    """测试不包含steps字段的流水线更新"""
    # 首先获取一个流水线列表
    response = requests.get(f"{BASE_URL}/pipelines/pipelines/")
    if response.status_code != 200:
        print(f"无法获取流水线列表: {response.status_code}")
        return
    
    pipelines = response.json()
    if not pipelines:
        print("没有找到流水线")
        return
    
    pipeline_id = pipelines[0]['id']
    print(f"\n测试不包含steps字段的更新，流水线 ID: {pipeline_id}")
    
    # 构造不包含steps字段的更新数据
    update_data = {
        "name": "测试流水线更新（无steps）",
        "description": "测试描述",
        "is_active": True
    }
    
    print("发送的更新数据:")
    print(json.dumps(update_data, indent=2, ensure_ascii=False))
    
    # 发送PUT请求更新流水线
    response = requests.put(
        f"{BASE_URL}/pipelines/pipelines/{pipeline_id}/",
        json=update_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\n响应状态码: {response.status_code}")
    print("响应内容:")
    
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        print("✅ 流水线更新成功")
    else:
        print(response.text)
        print("❌ 流水线更新失败")

if __name__ == "__main__":
    print("=== 测试包含steps字段的流水线更新 ===")
    test_pipeline_update()
    
    print("\n" + "="*50)
    print("=== 测试不包含steps字段的流水线更新 ===")
    test_pipeline_update_without_steps()
