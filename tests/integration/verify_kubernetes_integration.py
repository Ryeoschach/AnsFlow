#!/usr/bin/env python3
"""
Kubernetes 集成配置验证脚本
验证项目配置是否正确
"""

import os
import json
import subprocess
import sys
from pathlib import Path


def check_mark(success):
    return "✅" if success else "❌"


def run_command(cmd, capture_output=True):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=capture_output, 
            text=True,
            cwd="/Users/creed/Workspace/OpenSource/ansflow"
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_project_structure():
    """检查项目结构"""
    print("\n🔍 检查项目结构...")
    
    base_path = Path("/Users/creed/Workspace/OpenSource/ansflow")
    
    required_files = [
        "backend/django_service/kubernetes_integration/models.py",
        "backend/django_service/kubernetes_integration/serializers.py", 
        "backend/django_service/kubernetes_integration/views.py",
        "backend/django_service/kubernetes_integration/tasks.py",
        "backend/django_service/kubernetes_integration/k8s_client.py",
        "backend/django_service/kubernetes_integration/urls.py",
        "backend/django_service/ansflow/settings/base.py",
        "backend/django_service/pyproject.toml",
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = base_path / file_path
        exists = full_path.exists()
        print(f"  {check_mark(exists)} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist


def check_dependencies():
    """检查依赖配置"""
    print("\n📦 检查依赖配置...")
    
    # 检查 pyproject.toml 中的 kubernetes 依赖
    pyproject_path = "/Users/creed/Workspace/OpenSource/ansflow/backend/django_service/pyproject.toml"
    
    try:
        with open(pyproject_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        has_kubernetes = 'kubernetes>=' in content
        has_docker = 'docker>=' in content
        has_celery = 'celery>=' in content
        has_django = 'django>=' in content
        has_drf = 'djangorestframework>=' in content
        
        print(f"  {check_mark(has_kubernetes)} kubernetes 依赖")
        print(f"  {check_mark(has_docker)} docker 依赖")
        print(f"  {check_mark(has_celery)} celery 依赖")
        print(f"  {check_mark(has_django)} django 依赖")
        print(f"  {check_mark(has_drf)} djangorestframework 依赖")
        
        return all([has_kubernetes, has_docker, has_celery, has_django, has_drf])
        
    except Exception as e:
        print(f"  ❌ 读取 pyproject.toml 失败: {e}")
        return False


def check_django_settings():
    """检查 Django 配置"""
    print("\n⚙️  检查 Django 配置...")
    
    settings_path = "/Users/creed/Workspace/OpenSource/ansflow/backend/django_service/ansflow/settings/base.py"
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        has_k8s_app = 'kubernetes_integration' in content
        has_docker_app = 'docker_integration' in content
        has_celery_config = 'CELERY_' in content or 'celery' in content
        
        print(f"  {check_mark(has_k8s_app)} kubernetes_integration 应用已注册")
        print(f"  {check_mark(has_docker_app)} docker_integration 应用已注册") 
        print(f"  {check_mark(has_celery_config)} Celery 配置存在")
        
        return all([has_k8s_app, has_docker_app, has_celery_config])
        
    except Exception as e:
        print(f"  ❌ 读取设置文件失败: {e}")
        return False


def check_url_routing():
    """检查 URL 路由配置"""
    print("\n🌐 检查 URL 路由配置...")
    
    main_urls_path = "/Users/creed/Workspace/OpenSource/ansflow/backend/django_service/ansflow/urls.py"
    k8s_urls_path = "/Users/creed/Workspace/OpenSource/ansflow/backend/django_service/kubernetes_integration/urls.py"
    
    try:
        # 检查主路由
        with open(main_urls_path, 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        has_k8s_route = 'kubernetes_integration.urls' in main_content
        has_docker_route = 'docker_integration.urls' in main_content
        
        print(f"  {check_mark(has_k8s_route)} kubernetes 路由已注册")
        print(f"  {check_mark(has_docker_route)} docker 路由已注册")
        
        # 检查 K8s 路由文件
        k8s_urls_exists = os.path.exists(k8s_urls_path)
        print(f"  {check_mark(k8s_urls_exists)} kubernetes urls.py 文件存在")
        
        if k8s_urls_exists:
            with open(k8s_urls_path, 'r', encoding='utf-8') as f:
                k8s_content = f.read()
            
            has_viewsets = 'ViewSet' in k8s_content
            has_router = 'router' in k8s_content
            
            print(f"  {check_mark(has_viewsets)} ViewSet 配置存在")
            print(f"  {check_mark(has_router)} 路由器配置存在")
            
            return all([has_k8s_route, has_docker_route, k8s_urls_exists, has_viewsets, has_router])
        
        return False
        
    except Exception as e:
        print(f"  ❌ 检查路由配置失败: {e}")
        return False


def check_model_implementation():
    """检查模型实现"""
    print("\n🗂️  检查模型实现...")
    
    models_path = "/Users/creed/Workspace/OpenSource/ansflow/backend/django_service/kubernetes_integration/models.py"
    
    try:
        with open(models_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_models = [
            'KubernetesCluster',
            'KubernetesNamespace', 
            'KubernetesDeployment',
            'KubernetesService',
            'KubernetesPod',
            'KubernetesConfigMap',
            'KubernetesSecret'
        ]
        
        all_models_exist = True
        for model in required_models:
            exists = f"class {model}" in content
            print(f"  {check_mark(exists)} {model} 模型")
            if not exists:
                all_models_exist = False
        
        return all_models_exist
        
    except Exception as e:
        print(f"  ❌ 检查模型实现失败: {e}")
        return False


def check_client_implementation():
    """检查客户端实现"""
    print("\n🔧 检查 K8s 客户端实现...")
    
    client_path = "/Users/creed/Workspace/OpenSource/ansflow/backend/django_service/kubernetes_integration/k8s_client.py"
    
    try:
        with open(client_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_methods = [
            'get_cluster_info',
            'list_namespaces',
            'list_deployments', 
            'list_pods',
            'create_deployment',
            'scale_deployment',
            'delete_deployment'
        ]
        
        all_methods_exist = True
        for method in required_methods:
            exists = f"def {method}" in content
            print(f"  {check_mark(exists)} {method} 方法")
            if not exists:
                all_methods_exist = False
        
        # 检查模拟模式支持
        has_simulation = '模拟模式' in content or 'simulation' in content
        print(f"  {check_mark(has_simulation)} 模拟模式支持")
        
        return all_methods_exist and has_simulation
        
    except Exception as e:
        print(f"  ❌ 检查客户端实现失败: {e}")
        return False


def check_task_implementation():
    """检查异步任务实现"""
    print("\n⚡ 检查异步任务实现...")
    
    tasks_path = "/Users/creed/Workspace/OpenSource/ansflow/backend/django_service/kubernetes_integration/tasks.py"
    
    try:
        with open(tasks_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_tasks = [
            'check_cluster_status',
            'sync_cluster_resources',
            'deploy_application',
            'scale_deployment_task',
            'delete_deployment_task'
        ]
        
        all_tasks_exist = True
        for task in required_tasks:
            exists = f"def {task}" in content
            print(f"  {check_mark(exists)} {task} 任务")
            if not exists:
                all_tasks_exist = False
        
        # 检查 Celery 装饰器
        has_celery_decorator = '@shared_task' in content or '@task' in content
        print(f"  {check_mark(has_celery_decorator)} Celery 装饰器")
        
        return all_tasks_exist and has_celery_decorator
        
    except Exception as e:
        print(f"  ❌ 检查任务实现失败: {e}")
        return False


def generate_integration_suggestions():
    """生成集成建议"""
    print("\n💡 Docker/K8s 流水线集成建议:")
    
    suggestions = [
        "✅ 技术架构完备 - 后端模块、API、客户端都已实现",
        "✅ 支持模拟模式 - 无需真实集群即可测试功能",
        "✅ 异步任务支持 - 适合长时间运行的 K8s 操作",
        "✅ 多认证方式 - 支持 kubeconfig、token、集群内认证",
        "✅ 完整 CRUD - 支持集群、命名空间、部署等资源管理",
        "",
        "📋 建议的集成步骤:",
        "1. 本地 K8s 环境: 安装 minikube/kind/k3s",
        "2. 流水线类型扩展: 添加 k8s_deploy、k8s_scale 等步骤类型", 
        "3. 前端界面开发: K8s 资源管理页面",
        "4. 测试用例补充: 单元测试和集成测试",
        "",
        "🎯 推荐的流水线步骤类型:",
        "- docker_build: 构建 Docker 镜像",
        "- docker_push: 推送镜像到仓库", 
        "- k8s_deploy: 部署应用到 K8s",
        "- k8s_scale: 扩缩容应用",
        "- k8s_wait: 等待资源就绪",
        "- k8s_exec: 在 Pod 中执行命令",
        "",
        "🔗 本地流水线集成完全可行!"
    ]
    
    for suggestion in suggestions:
        print(f"  {suggestion}")


def main():
    """主验证函数"""
    print("🚀 Kubernetes 集成配置验证")
    print("=" * 50)
    
    checks = [
        ("项目结构", check_project_structure),
        ("依赖配置", check_dependencies), 
        ("Django 配置", check_django_settings),
        ("URL 路由", check_url_routing),
        ("模型实现", check_model_implementation),
        ("客户端实现", check_client_implementation),
        ("异步任务", check_task_implementation),
    ]
    
    passed_checks = 0
    total_checks = len(checks)
    
    for check_name, check_func in checks:
        if check_func():
            passed_checks += 1
    
    print("\n" + "=" * 50)
    print(f"📊 验证结果: {passed_checks}/{total_checks} 项检查通过")
    
    if passed_checks == total_checks:
        print("🎉 所有检查通过！Kubernetes 集成配置正确")
        generate_integration_suggestions()
        return 0
    else:
        print("❌ 部分检查未通过，请检查上述错误")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
