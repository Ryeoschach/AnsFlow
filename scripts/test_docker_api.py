#!/usr/bin/env python
"""
Docker集成功能测试脚本
"""
import os
import sys
import json
import requests
from datetime import datetime

# 设置Django环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from docker_integration.models import DockerRegistry, DockerImage, DockerContainer


def get_auth_token():
    """获取认证Token"""
    try:
        # 尝试获取已存在的用户
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            # 创建超级用户
            user = User.objects.create_superuser(
                username='admin',
                email='admin@ansflow.com',
                password='admin123'
            )
            print(f"创建超级用户: {user.username}")
        
        # 生成JWT Token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        print(f"用户: {user.username}")
        print(f"Token: {access_token[:50]}...")
        return access_token, user
        
    except Exception as e:
        print(f"获取认证Token失败: {e}")
        return None, None


def test_docker_registry_api(token):
    """测试Docker仓库API"""
    print("\n=== 测试Docker仓库API ===")
    
    base_url = "http://127.0.0.1:8000/api/v1/docker"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 生成唯一的名称
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. 创建Docker仓库
    registry_data = {
        "name": f"Docker Hub Test {timestamp}",
        "url": "https://hub.docker.com",
        "registry_type": "dockerhub",
        "username": "testuser",
        "description": f"测试Docker Hub仓库 {timestamp}",
        "is_default": False
    }
    
    try:
        response = requests.post(
            f"{base_url}/registries/",
            json=registry_data,
            headers=headers
        )
        
        if response.status_code == 201:
            registry = response.json()
            print(f"✅ 创建仓库成功: {registry['name']}")
            print(f"   ID: {registry['id']}")
            print(f"   类型: {registry['registry_type']}")
            
            # 2. 获取仓库列表
            response = requests.get(f"{base_url}/registries/", headers=headers)
            if response.status_code == 200:
                registries = response.json()
                print(f"✅ 获取仓库列表成功: {len(registries['results'])} 个仓库")
            
            # 3. 测试仓库连接
            response = requests.post(
                f"{base_url}/registries/{registry['id']}/test/",
                headers=headers
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 仓库连接测试: {result.get('message', '成功')}")
            
            return registry['id']
            
        else:
            print(f"❌ 创建仓库失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            print(f"   错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Docker仓库API测试失败: {e}")
        return None


def test_docker_image_api(token, registry_id):
    """测试Docker镜像API"""
    print("\n=== 测试Docker镜像API ===")
    
    base_url = "http://127.0.0.1:8000/api/v1/docker"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 生成唯一的名称
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. 创建Docker镜像
    image_data = {
        "name": f"test-app-{timestamp}",
        "tag": "v1.0.0",
        "registry": registry_id,
        "dockerfile_content": """FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]""",
        "build_context": ".",
        "build_args": {
            "NODE_ENV": "production"
        },
        "description": f"测试应用镜像 {timestamp}",
        "is_template": True
    }
    
    try:
        response = requests.post(
            f"{base_url}/images/",
            json=image_data,
            headers=headers
        )
        
        if response.status_code == 201:
            image = response.json()
            print(f"✅ 创建镜像成功: {image['name']}:{image['tag']}")
            print(f"   ID: {image['id']}")
            print(f"   完整名称: {image['full_name']}")
            print(f"   构建状态: {image['build_status']}")
            
            # 2. 获取镜像列表
            response = requests.get(f"{base_url}/images/", headers=headers)
            if response.status_code == 200:
                images = response.json()
                print(f"✅ 获取镜像列表成功: {len(images['results'])} 个镜像")
            
            # 3. 获取Dockerfile模板
            response = requests.get(
                f"{base_url}/images/{image['id']}/dockerfile_template/?type=python",
                headers=headers
            )
            if response.status_code == 200:
                template = response.json()
                print(f"✅ 获取Dockerfile模板成功")
                print(f"   模板类型: Python")
            
            # 4. 创建镜像版本
            version_data = {
                "version": "v1.0.1",
                "dockerfile_content": image['dockerfile_content'],
                "build_context": ".",
                "changelog": "初始版本",
                "is_release": True
            }
            
            response = requests.post(
                f"{base_url}/images/{image['id']}/create_version/",
                json=version_data,
                headers=headers
            )
            if response.status_code == 201:
                version = response.json()
                print(f"✅ 创建镜像版本成功: {version['version']}")
            
            return image['id']
            
        else:
            print(f"❌ 创建镜像失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Docker镜像API测试失败: {e}")
        return None


def test_docker_container_api(token, image_id):
    """测试Docker容器API"""
    print("\n=== 测试Docker容器API ===")
    
    base_url = "http://127.0.0.1:8000/api/v1/docker"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 生成唯一的名称
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. 创建Docker容器
    container_data = {
        "name": f"test-container-{timestamp}",
        "image": image_id,
        "command": "npm start",
        "working_dir": "/app",
        "environment_vars": {
            "NODE_ENV": "production",
            "PORT": "3000"
        },
        "port_mappings": [
            {"host": "3000", "container": "3000"}
        ],
        "volumes": [
            {"host": "/data", "container": "/app/data"}
        ],
        "memory_limit": "512m",
        "cpu_limit": "0.5",
        "description": f"测试容器实例 {timestamp}",
        "restart_policy": "unless-stopped"
    }
    
    try:
        response = requests.post(
            f"{base_url}/containers/",
            json=container_data,
            headers=headers
        )
        
        if response.status_code == 201:
            container = response.json()
            print(f"✅ 创建容器成功: {container['name']}")
            print(f"   ID: {container['id']}")
            print(f"   镜像: {container['image_name']}")
            print(f"   状态: {container['status']}")
            
            # 2. 获取容器列表
            response = requests.get(f"{base_url}/containers/", headers=headers)
            if response.status_code == 200:
                containers = response.json()
                print(f"✅ 获取容器列表成功: {len(containers['results'])} 个容器")
            
            # 3. 获取容器统计信息
            response = requests.get(
                f"{base_url}/containers/{container['id']}/stats/",
                headers=headers
            )
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ 获取容器统计信息成功")
            else:
                print(f"ℹ️  容器统计信息: {response.json().get('message', '暂无数据')}")
            
            return container['id']
            
        else:
            print(f"❌ 创建容器失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Docker容器API测试失败: {e}")
        return None


def test_docker_compose_api(token):
    """测试Docker Compose API"""
    print("\n=== 测试Docker Compose API ===")
    
    base_url = "http://127.0.0.1:8000/api/v1/docker"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 生成唯一的名称
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. 创建Docker Compose项目
    compose_data = {
        "name": f"test-compose-{timestamp}",
        "compose_content": """version: '3.8'
services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
""",
        "working_directory": f"/tmp/test-compose-{timestamp}",
        "environment_file": "NODE_ENV=production\nDATABASE_URL=postgresql://user:password@db:5432/myapp",
        "description": f"测试Web应用Compose项目 {timestamp}"
    }
    
    try:
        response = requests.post(
            f"{base_url}/compose/",
            json=compose_data,
            headers=headers
        )
        
        if response.status_code == 201:
            compose = response.json()
            print(f"✅ 创建Compose项目成功: {compose['name']}")
            print(f"   ID: {compose['id']}")
            print(f"   状态: {compose['status']}")
            
            # 2. 获取Compose列表
            response = requests.get(f"{base_url}/compose/", headers=headers)
            if response.status_code == 200:
                composes = response.json()
                print(f"✅ 获取Compose列表成功: {len(composes['results'])} 个项目")
            
            # 3. 验证Compose文件
            response = requests.post(
                f"{base_url}/compose/{compose['id']}/validate_compose/",
                headers=headers
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Compose文件验证成功")
                print(f"   服务列表: {result.get('services', [])}")
            
            # 4. 获取Compose模板
            response = requests.get(
                f"{base_url}/compose/template/?type=web-app",
                headers=headers
            )
            if response.status_code == 200:
                template = response.json()
                print(f"✅ 获取Compose模板成功")
            
            return compose['id']
            
        else:
            print(f"❌ 创建Compose项目失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Docker Compose API测试失败: {e}")
        return None


def main():
    """主测试函数"""
    print("🐳 开始Docker集成功能测试")
    print("=" * 50)
    
    # 获取认证Token
    token, user = get_auth_token()
    if not token:
        print("❌ 无法获取认证Token，测试终止")
        return
    
    # 测试Docker仓库API
    registry_id = test_docker_registry_api(token)
    if not registry_id:
        print("❌ Docker仓库API测试失败，跳过后续测试")
        return
    
    # 测试Docker镜像API
    image_id = test_docker_image_api(token, registry_id)
    if not image_id:
        print("❌ Docker镜像API测试失败，跳过容器测试")
    else:
        # 测试Docker容器API
        container_id = test_docker_container_api(token, image_id)
    
    # 测试Docker Compose API
    compose_id = test_docker_compose_api(token)
    
    print("\n" + "=" * 50)
    print("🎉 Docker集成功能测试完成！")
    
    # 显示测试总结
    print("\n📊 测试总结:")
    print(f"   ✅ Docker仓库功能: {'通过' if registry_id else '失败'}")
    print(f"   ✅ Docker镜像功能: {'通过' if image_id else '失败'}")
    print(f"   ✅ Docker容器功能: {'通过' if 'container_id' in locals() else '失败'}")
    print(f"   ✅ Docker Compose功能: {'通过' if compose_id else '失败'}")


if __name__ == "__main__":
    main()
