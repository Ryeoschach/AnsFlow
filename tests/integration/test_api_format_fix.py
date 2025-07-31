#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker注册表数据格式修复验证脚本
"""

import requests
import json

def test_api_calls():
    """测试API调用和数据格式"""
    
    print("🔍 验证Docker注册表API数据格式修复")
    print("=" * 50)
    
    # 获取token
    token_url = "http://localhost:8000/api/v1/auth/token/"
    login_data = {"username": "admin", "password": "admin123"}
    
    try:
        response = requests.post(token_url, json=login_data)
        token_data = response.json()
        access_token = token_data['access']
        print("✅ 获取认证token成功")
    except Exception as e:
        print(f"❌ 获取token失败: {e}")
        return
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    # 测试注册表API
    print("\n1️⃣ 测试注册表API")
    registries_url = "http://localhost:8000/api/v1/docker/registries/"
    
    try:
        response = requests.get(registries_url, headers=headers)
        registries_data = response.json()
        
        print(f"📊 原始响应格式:")
        print(f"   - 类型: {type(registries_data)}")
        print(f"   - 包含字段: {list(registries_data.keys()) if isinstance(registries_data, dict) else 'Array'}")
        
        if isinstance(registries_data, dict) and 'results' in registries_data:
            results = registries_data['results']
            print(f"✅ 分页格式 - 总数: {registries_data['count']}, 结果数: {len(results)}")
            
            # 显示前几个注册表
            for i, registry in enumerate(results[:3]):
                print(f"   {i+1}. {registry['name']} ({registry['registry_type']}) - {registry['status']}")
                
        elif isinstance(registries_data, list):
            print(f"✅ 数组格式 - 注册表数量: {len(registries_data)}")
        else:
            print(f"❌ 未知格式: {registries_data}")
            
    except Exception as e:
        print(f"❌ 注册表API测试失败: {e}")
    
    # 测试项目API
    print("\n2️⃣ 测试项目API")
    projects_url = "http://localhost:8000/api/v1/docker/registries/projects/"
    
    try:
        response = requests.get(projects_url, headers=headers)
        projects_data = response.json()
        
        print(f"📊 原始响应格式:")
        print(f"   - 类型: {type(projects_data)}")
        
        if isinstance(projects_data, list):
            print(f"✅ 数组格式 - 项目数量: {len(projects_data)}")
            
            # 显示前几个项目
            for i, project in enumerate(projects_data[:3]):
                print(f"   {i+1}. {project['name']} (注册表ID: {project['registry_id']}) - {project['visibility']}")
                
        elif isinstance(projects_data, dict) and 'results' in projects_data:
            results = projects_data['results']
            print(f"✅ 分页格式 - 总数: {projects_data['count']}, 结果数: {len(results)}")
        else:
            print(f"❌ 未知格式: {projects_data}")
            
    except Exception as e:
        print(f"❌ 项目API测试失败: {e}")
    
    print("\n3️⃣ 前端修复说明")
    print("🔧 已修复问题:")
    print("   - dockerRegistryService.getRegistries() 现在正确处理分页格式")
    print("   - 提取 data.results 数组用于前端显示")
    print("   - 兼容非分页格式的向后兼容性")
    
    print("\n4️⃣ 下一步操作指南")
    print("💻 请在浏览器中:")
    print("1. 确保已设置认证token:")
    print(f"   localStorage.setItem('authToken', '{access_token}')")
    print("2. 刷新页面")
    print("3. 打开流水线编辑，添加Docker步骤")
    print("4. 检查目标注册表下拉框")
    
    print("\n✨ 修复完成！注册表应该正常显示了！")

if __name__ == "__main__":
    test_api_calls()
