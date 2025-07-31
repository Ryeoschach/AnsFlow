#!/usr/bin/env python3
"""
Docker Push步骤添加问题诊断脚本
诊断添加Docker push步骤时页面跳转到http://127.0.0.1:5173/pipelines并空白的问题
"""

import requests
import json
import sys
import os
import time

# 添加Django项目路径
sys.path.insert(0, '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def test_docker_push_step_creation():
    """测试Docker Push步骤创建流程"""
    print("🔍 Docker Push步骤添加问题诊断")
    print("=" * 60)
    
    # 1. 获取JWT token
    try:
        user = User.objects.get(username='admin')
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        print(f"✅ 获取JWT Token成功")
    except User.DoesNotExist:
        print("❌ 未找到admin用户，请先创建")
        return False
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    base_url = 'http://127.0.0.1:8000/api/v1'
    
    # 2. 测试后端API连接
    print(f"\n🧪 测试后端API连接")
    try:
        response = requests.get(f'{base_url}/pipelines/pipelines/', headers=headers, timeout=10)
        print(f"📡 /pipelines/pipelines/ 响应状态码: {response.status_code}")
        if response.status_code == 200:
            pipelines = response.json()
            print(f"📊 流水线数量: {pipelines.get('count', 0)}")
        else:
            print(f"⚠️ API响应异常: {response.text}")
    except requests.RequestException as e:
        print(f"❌ API连接失败: {e}")
        return False
    
    # 3. 创建测试流水线
    print(f"\n🔧 创建测试流水线")
    pipeline_data = {
        "name": "Docker Push Test Pipeline",
        "description": "测试Docker Push步骤添加",
        "project": 1,  # 使用现有项目ID
        "execution_mode": "local",
        "execution_tool": None,  # 使用None而不是字符串
        "is_active": True
    }
    
    try:
        response = requests.post(f'{base_url}/pipelines/pipelines/', 
                               headers=headers, 
                               json=pipeline_data, 
                               timeout=10)
        print(f"📡 创建流水线响应码: {response.status_code}")
        
        if response.status_code == 201:
            pipeline = response.json()
            pipeline_id = pipeline['id']
            print(f"✅ 流水线创建成功，ID: {pipeline_id}")
        else:
            print(f"❌ 流水线创建失败: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"❌ 流水线创建请求失败: {e}")
        return False
    
    # 4. 测试Docker注册表API
    print(f"\n🐳 测试Docker注册表API")
    try:
        response = requests.get(f'{base_url}/docker/registries/', headers=headers, timeout=10)
        print(f"📡 Docker注册表API响应码: {response.status_code}")
        
        if response.status_code == 200:
            registries = response.json()
            print(f"📊 注册表数量: {registries.get('count', 0)}")
            if registries.get('results'):
                registry_id = registries['results'][0]['id']
                print(f"🏗️ 使用注册表ID: {registry_id}")
            else:
                registry_id = None
                print("⚠️ 没有可用的Docker注册表")
        else:
            print(f"❌ Docker注册表API失败: {response.text}")
            registry_id = None
    except requests.RequestException as e:
        print(f"❌ Docker注册表API请求失败: {e}")
        registry_id = None
    
    # 5. 添加Docker Push步骤
    print(f"\n📤 添加Docker Push步骤")
    docker_push_step = {
        "name": "Push Docker Image",
        "step_type": "docker_push",
        "description": "推送Docker镜像到注册表",
        "pipeline": pipeline_id,  # 添加流水线ID
        "order": 1,
        "docker_image": "test-app",
        "docker_tag": "latest",
        "docker_registry": registry_id,
        "docker_config": {
            "all_tags": False,
            "platform": "linux/amd64"
        },
        "timeout_seconds": 1800,
        "is_active": True
    }
    
    try:
        response = requests.post(f'{base_url}/cicd/atomic-steps/', 
                               headers=headers, 
                               json=docker_push_step, 
                               timeout=10)
        print(f"📡 添加步骤响应码: {response.status_code}")
        
        if response.status_code == 201:
            step = response.json()
            print(f"✅ Docker Push步骤添加成功，ID: {step['id']}")
            print(f"📋 步骤详情: {json.dumps(step, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 步骤添加失败: {response.text}")
            print(f"🔍 请求数据: {json.dumps(docker_push_step, indent=2, ensure_ascii=False)}")
            return False
    except requests.RequestException as e:
        print(f"❌ 步骤添加请求失败: {e}")
        return False
    
    # 6. 验证步骤保存
    print(f"\n✅ 验证步骤保存")
    try:
        response = requests.get(f'{base_url}/cicd/atomic-steps/?pipeline={pipeline_id}', 
                               headers=headers, 
                               timeout=10)
        print(f"📡 获取步骤列表响应码: {response.status_code}")
        
        if response.status_code == 200:
            steps = response.json()
            print(f"📊 流水线步骤数量: {len(steps) if isinstance(steps, list) else steps.get('count', 0)}")
            
            # 查找Docker Push步骤
            docker_push_steps = []
            if isinstance(steps, list):
                docker_push_steps = [s for s in steps if s.get('step_type') == 'docker_push']
            elif 'results' in steps:
                docker_push_steps = [s for s in steps['results'] if s.get('step_type') == 'docker_push']
            
            if docker_push_steps:
                print(f"✅ 找到 {len(docker_push_steps)} 个Docker Push步骤")
                for step in docker_push_steps:
                    print(f"   - 步骤: {step.get('name')} (ID: {step.get('id')})")
            else:
                print("❌ 未找到Docker Push步骤")
        else:
            print(f"❌ 获取步骤列表失败: {response.text}")
    except requests.RequestException as e:
        print(f"❌ 获取步骤列表请求失败: {e}")
    
    # 7. 测试前端访问
    print(f"\n🌐 测试前端访问")
    frontend_urls = [
        'http://127.0.0.1:5173/',
        'http://127.0.0.1:5173/pipelines',
        f'http://127.0.0.1:5173/pipelines/{pipeline_id}'
    ]
    
    for url in frontend_urls:
        try:
            response = requests.get(url, timeout=5)
            print(f"📡 {url} - 状态码: {response.status_code}")
            if response.status_code == 200:
                content_length = len(response.content)
                print(f"   📄 内容长度: {content_length} bytes")
                if content_length < 100:
                    print(f"   ⚠️ 内容太短，可能是空白页面")
                    print(f"   📝 内容预览: {response.text[:200]}")
            else:
                print(f"   ❌ 响应异常: {response.text[:100]}")
        except requests.RequestException as e:
            print(f"❌ {url} - 连接失败: {e}")
    
    # 8. 清理测试数据
    print(f"\n🧹 清理测试数据")
    try:
        response = requests.delete(f'{base_url}/pipelines/pipelines/{pipeline_id}/', 
                                 headers=headers, 
                                 timeout=10)
        if response.status_code in [204, 200]:
            print(f"✅ 测试流水线删除成功")
        else:
            print(f"⚠️ 删除流水线失败: {response.status_code}")
    except requests.RequestException as e:
        print(f"⚠️ 删除流水线请求失败: {e}")
    
    return True

def check_frontend_dev_server():
    """检查前端开发服务器状态"""
    print(f"\n🔍 检查前端开发服务器状态")
    print("=" * 40)
    
    try:
        response = requests.get('http://127.0.0.1:5173/', timeout=5)
        print(f"📡 前端服务器状态码: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"📄 页面内容长度: {len(content)} bytes")
            
            # 检查是否是SPA应用
            if 'react' in content.lower() or 'vite' in content.lower() or 'div id="root"' in content:
                print("✅ 前端服务器正常运行（React/Vite应用）")
            else:
                print("⚠️ 前端内容异常，可能不是预期的React应用")
                print(f"📝 内容预览: {content[:300]}")
        else:
            print(f"❌ 前端服务器响应异常: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ 前端服务器连接失败: {e}")
        print("💡 请确保前端开发服务器已启动: npm run dev 或 yarn dev")

def main():
    """主诊断函数"""
    print("🛠️ Docker Push步骤添加问题完整诊断")
    print("=" * 60)
    
    # 检查前端服务器
    check_frontend_dev_server()
    
    # 测试Docker Push步骤创建
    success = test_docker_push_step_creation()
    
    print(f"\n📋 诊断结果总结")
    print("=" * 30)
    
    if success:
        print("✅ 后端API功能正常")
        print("💡 如果前端仍然出现页面跳转和空白问题，可能的原因：")
        print("   1. 前端路由配置问题")
        print("   2. 前端状态管理问题")
        print("   3. 前端组件渲染错误")
        print("   4. 浏览器缓存问题")
        print("   5. 前端开发服务器代理配置")
        
        print(f"\n🔧 建议解决步骤：")
        print("   1. 清除浏览器缓存并刷新")
        print("   2. 检查浏览器开发者工具的Console和Network面板")
        print("   3. 检查前端路由配置")
        print("   4. 重启前端开发服务器")
    else:
        print("❌ 后端API存在问题，需要先解决后端问题")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
