#!/usr/bin/env python
"""
Docker 功能数据初始化脚本
创建默认的 Docker 注册表和示例流水线步骤
"""
import os
import sys

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from django.contrib.auth.models import User
from docker_integration.models import DockerRegistry
from pipelines.models import Pipeline, PipelineStep
from project_management.models import Project


def create_default_docker_registries():
    """创建默认的 Docker 注册表"""
    print("📦 创建默认 Docker 注册表...")
    
    # 检查是否已存在
    existing_registries = list(DockerRegistry.objects.all())
    if existing_registries:
        print("  ℹ️  Docker 注册表已存在，跳过创建")
        return existing_registries
    
    # 获取或创建管理员用户
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@ansflow.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    # 创建 Docker Hub 注册表（默认）
    docker_hub = DockerRegistry.objects.create(
        name="Docker Hub",
        url="https://index.docker.io/v1/",
        registry_type="dockerhub",
        username="",
        description="Docker 官方镜像仓库",
        status="active",
        is_default=True,
        created_by=admin_user
    )
    print(f"  ✅ 创建 Docker Hub 注册表: {docker_hub.id}")
    
    # 创建示例私有注册表
    private_registry = DockerRegistry.objects.create(
        name="Private Registry",
        url="https://registry.example.com",
        registry_type="private",
        username="registry-user",
        description="示例私有镜像仓库",
        status="inactive",  # 示例用，设为非活跃
        is_default=False,
        created_by=admin_user
    )
    print(f"  ✅ 创建私有注册表: {private_registry.id}")
    
    # 创建 Harbor 注册表
    harbor_registry = DockerRegistry.objects.create(
        name="Harbor Registry",
        url="https://harbor.example.com",
        registry_type="harbor",
        username="harbor-user",
        description="Harbor 企业级镜像仓库",
        status="inactive",  # 示例用，设为非活跃
        is_default=False,
        created_by=admin_user
    )
    print(f"  ✅ 创建 Harbor 注册表: {harbor_registry.id}")
    
    return [docker_hub, private_registry, harbor_registry]


def create_sample_project_and_pipeline():
    """创建示例项目和流水线"""
    print("🔧 创建示例项目和流水线...")
    
    # 获取管理员用户
    admin_user = User.objects.get(username='admin')
    
    # 创建示例项目
    project, created = Project.objects.get_or_create(
        name="Docker Demo Project",
        defaults={
            'description': "Docker 功能演示项目",
            'owner': admin_user,
            'is_active': True
        }
    )
    
    if created:
        print(f"  ✅ 创建示例项目: {project.name}")
    else:
        print(f"  ℹ️  项目已存在: {project.name}")
    
    # 创建示例流水线
    pipeline, created = Pipeline.objects.get_or_create(
        name="Docker CI/CD Pipeline",
        project=project,
        defaults={
            'description': "Docker 构建、测试、推送流水线",
            'created_by': admin_user,
            'is_active': True
        }
    )
    
    if created:
        print(f"  ✅ 创建示例流水线: {pipeline.name}")
    else:
        print(f"  ℹ️  流水线已存在: {pipeline.name}")
    
    return project, pipeline


def create_docker_pipeline_steps(pipeline, registries):
    """创建 Docker 流水线步骤"""
    print("🚀 创建 Docker 流水线步骤...")
    
    # 检查是否已有步骤
    if pipeline.steps.filter(step_type__in=['docker_build', 'docker_run', 'docker_push', 'docker_pull']).exists():
        print("  ℹ️  Docker 步骤已存在，跳过创建")
        return
    
    docker_hub = registries[0]  # 第一个是 Docker Hub
    
    # Step 1: Docker Build
    build_step = PipelineStep.objects.create(
        pipeline=pipeline,
        name="Build Docker Image",
        step_type="docker_build",
        description="构建应用的 Docker 镜像",
        command="docker build",
        docker_image="myapp",
        docker_tag="latest",
        docker_config={
            "dockerfile_path": "Dockerfile",
            "context_path": ".",
            "platform": "linux/amd64",
            "no_cache": False,
            "pull": True,
            "build_args": {
                "NODE_ENV": "production",
                "APP_VERSION": "1.0.0"
            }
        },
        environment_vars={
            "DOCKER_BUILDKIT": "1"
        },
        timeout_seconds=1800,
        order=1
    )
    print(f"  ✅ 创建构建步骤: {build_step.name}")
    
    # Step 2: Docker Run (Test)
    test_step = PipelineStep.objects.create(
        pipeline=pipeline,
        name="Test Docker Container",
        step_type="docker_run",
        description="运行容器进行测试",
        command="docker run",
        docker_image="myapp",
        docker_tag="latest",
        docker_config={
            "command": "npm test",
            "remove": True,
            "detach": False,
            "ports": [],
            "volumes": [
                {
                    "host": "./test-results",
                    "container": "/app/test-results",
                    "mode": "rw"
                }
            ],
            "environment": {
                "NODE_ENV": "test"
            }
        },
        environment_vars={
            "CI": "true"
        },
        timeout_seconds=600,
        order=2
    )
    print(f"  ✅ 创建测试步骤: {test_step.name}")
    
    # Step 3: Docker Push
    push_step = PipelineStep.objects.create(
        pipeline=pipeline,
        name="Push to Registry",
        step_type="docker_push",
        description="推送镜像到 Docker 注册表",
        command="docker push",
        docker_image="myapp",
        docker_tag="latest",
        docker_registry=docker_hub,
        docker_config={
            "all_tags": False,
            "platform": "linux/amd64"
        },
        timeout_seconds=1800,
        order=3
    )
    print(f"  ✅ 创建推送步骤: {push_step.name}")
    
    # Step 4: Docker Pull (Deploy)
    pull_step = PipelineStep.objects.create(
        pipeline=pipeline,
        name="Pull and Deploy",
        step_type="docker_pull",
        description="拉取最新镜像并部署",
        command="docker pull",
        docker_image="myapp",
        docker_tag="latest",
        docker_registry=docker_hub,
        docker_config={
            "all_tags": False,
            "platform": "linux/amd64"
        },
        timeout_seconds=1800,
        order=4
    )
    print(f"  ✅ 创建拉取步骤: {pull_step.name}")
    
    return [build_step, test_step, push_step, pull_step]


def create_advanced_docker_pipeline():
    """创建高级 Docker 流水线示例"""
    print("🎯 创建高级 Docker 流水线...")
    
    admin_user = User.objects.get(username='admin')
    
    # 创建微服务项目
    microservice_project, created = Project.objects.get_or_create(
        name="Microservices Demo",
        defaults={
            'description': "微服务 Docker 部署示例",
            'owner': admin_user,
            'is_active': True
        }
    )
    
    # 创建多服务流水线
    multi_service_pipeline, created = Pipeline.objects.get_or_create(
        name="Multi-Service Docker Pipeline",
        project=microservice_project,
        defaults={
            'description': "多服务 Docker 构建和部署",
            'created_by': admin_user,
            'is_active': True
        }
    )
    
    if not created:
        print("  ℹ️  高级流水线已存在，跳过创建")
        return
    
    docker_hub = DockerRegistry.objects.get(name="Docker Hub")
    
    # 前端服务构建
    frontend_build = PipelineStep.objects.create(
        pipeline=multi_service_pipeline,
        name="Build Frontend Service",
        step_type="docker_build",
        description="构建前端 React 应用",
        docker_image="frontend-app",
        docker_tag="v1.0.0",
        docker_config={
            "dockerfile_path": "frontend/Dockerfile",
            "context_path": "frontend",
            "target_stage": "production",
            "build_args": {
                "REACT_APP_API_URL": "https://api.example.com",
                "REACT_APP_ENV": "production"
            }
        },
        timeout_seconds=1200,
        order=1
    )
    
    # 后端服务构建
    backend_build = PipelineStep.objects.create(
        pipeline=multi_service_pipeline,
        name="Build Backend Service",
        step_type="docker_build",
        description="构建后端 Node.js API",
        docker_image="backend-api",
        docker_tag="v1.0.0",
        docker_config={
            "dockerfile_path": "backend/Dockerfile",
            "context_path": "backend",
            "build_args": {
                "NODE_ENV": "production"
            }
        },
        timeout_seconds=1200,
        order=2
    )
    
    # 集成测试
    integration_test = PipelineStep.objects.create(
        pipeline=multi_service_pipeline,
        name="Integration Test",
        step_type="docker_run",
        description="运行集成测试",
        docker_image="test-runner",
        docker_tag="latest",
        docker_config={
            "command": "npm run test:integration",
            "environment": {
                "FRONTEND_URL": "http://frontend-app:3000",
                "BACKEND_URL": "http://backend-api:8000"
            },
            "remove": True
        },
        timeout_seconds=900,
        order=3
    )
    
    # 推送前端镜像
    frontend_push = PipelineStep.objects.create(
        pipeline=multi_service_pipeline,
        name="Push Frontend Image",
        step_type="docker_push",
        description="推送前端镜像",
        docker_image="frontend-app",
        docker_tag="v1.0.0",
        docker_registry=docker_hub,
        timeout_seconds=1200,
        order=4
    )
    
    # 推送后端镜像
    backend_push = PipelineStep.objects.create(
        pipeline=multi_service_pipeline,
        name="Push Backend Image",
        step_type="docker_push",
        description="推送后端镜像",
        docker_image="backend-api",
        docker_tag="v1.0.0",
        docker_registry=docker_hub,
        timeout_seconds=1200,
        order=5
    )
    
    print(f"  ✅ 创建高级流水线: {multi_service_pipeline.name}")
    print(f"    📦 前端构建: {frontend_build.name}")
    print(f"    📦 后端构建: {backend_build.name}")
    print(f"    🧪 集成测试: {integration_test.name}")
    print(f"    📤 前端推送: {frontend_push.name}")
    print(f"    📤 后端推送: {backend_push.name}")


def main():
    """主函数"""
    print("🚀 初始化 AnsFlow Docker 功能数据")
    print("=" * 50)
    
    try:
        # 创建默认注册表
        registries = create_default_docker_registries()
        
        # 创建示例项目和流水线
        project, pipeline = create_sample_project_and_pipeline()
        
        # 创建 Docker 步骤
        steps = create_docker_pipeline_steps(pipeline, registries)
        
        # 创建高级示例
        create_advanced_docker_pipeline()
        
        print("\n" + "=" * 50)
        print("🎉 Docker 功能数据初始化完成！")
        print(f"📊 创建了 {len(registries)} 个注册表")
        print(f"📊 创建了 {len(steps)} 个基础步骤")
        print("📊 创建了 1 个高级流水线示例")
        
        print("\n🔍 验证创建的数据:")
        print(f"  📦 Docker 注册表: {DockerRegistry.objects.count()}")
        print(f"  📋 流水线: {Pipeline.objects.count()}")
        print(f"  🚀 Docker 步骤: {PipelineStep.objects.filter(step_type__in=['docker_build', 'docker_run', 'docker_push', 'docker_pull']).count()}")
        
    except Exception as e:
        print(f"❌ 初始化过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
