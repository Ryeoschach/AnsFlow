#!/usr/bin/env python3
"""
Docker/Kubernetes 流水线步骤测试脚本
验证新的步骤类型是否正常工作
"""

import os
import sys
import django
import json
from datetime import datetime

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from pipelines.models import Pipeline, PipelineStep
from pipelines.services.docker_executor import DockerStepExecutor
from pipelines.services.kubernetes_executor import KubernetesStepExecutor
from kubernetes_integration.models import KubernetesCluster
from docker_integration.models import DockerRegistry


def test_print(title, status="INFO"):
    """打印测试信息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_colors = {
        "INFO": "\033[94m",    # 蓝色
        "SUCCESS": "\033[92m", # 绿色
        "ERROR": "\033[91m",   # 红色
        "WARNING": "\033[93m"  # 黄色
    }
    reset_color = "\033[0m"
    color = status_colors.get(status, "")
    print(f"{color}[{timestamp}] [{status}] {title}{reset_color}")


def test_step_types():
    """测试新的步骤类型"""
    test_print("测试新的流水线步骤类型...", "INFO")
    
    try:
        # 检查步骤类型选择是否包含新类型
        step_choices = dict(PipelineStep.STEP_TYPE_CHOICES)
        
        docker_types = ['docker_build', 'docker_run', 'docker_push', 'docker_pull']
        k8s_types = ['k8s_deploy', 'k8s_scale', 'k8s_delete', 'k8s_wait', 'k8s_exec', 'k8s_logs']
        
        for step_type in docker_types:
            if step_type in step_choices:
                test_print(f"✅ Docker 步骤类型 {step_type}: {step_choices[step_type]}", "SUCCESS")
            else:
                test_print(f"❌ Docker 步骤类型 {step_type} 缺失", "ERROR")
                return False
        
        for step_type in k8s_types:
            if step_type in step_choices:
                test_print(f"✅ K8s 步骤类型 {step_type}: {step_choices[step_type]}", "SUCCESS")
            else:
                test_print(f"❌ K8s 步骤类型 {step_type} 缺失", "ERROR")
                return False
        
        test_print("✅ 所有新步骤类型验证通过", "SUCCESS")
        return True
        
    except Exception as e:
        test_print(f"❌ 步骤类型测试失败: {e}", "ERROR")
        return False


def test_docker_executor():
    """测试 Docker 执行器"""
    test_print("测试 Docker 执行器...", "INFO")
    
    try:
        executor = DockerStepExecutor()
        
        # 测试支持的步骤类型
        docker_types = ['docker_build', 'docker_run', 'docker_push', 'docker_pull']
        for step_type in docker_types:
            can_execute = executor.can_execute(step_type)
            test_print(f"✅ Docker 执行器支持 {step_type}: {can_execute}", "SUCCESS" if can_execute else "ERROR")
            if not can_execute:
                return False
        
        # 测试不支持的步骤类型
        unsupported = executor.can_execute('unsupported_type')
        test_print(f"✅ Docker 执行器正确拒绝不支持的类型: {not unsupported}", "SUCCESS" if not unsupported else "ERROR")
        
        test_print("✅ Docker 执行器测试通过", "SUCCESS")
        return True
        
    except Exception as e:
        test_print(f"❌ Docker 执行器测试失败: {e}", "ERROR")
        return False


def test_kubernetes_executor():
    """测试 Kubernetes 执行器"""
    test_print("测试 Kubernetes 执行器...", "INFO")
    
    try:
        executor = KubernetesStepExecutor()
        
        # 测试支持的步骤类型
        k8s_types = ['k8s_deploy', 'k8s_scale', 'k8s_delete', 'k8s_wait', 'k8s_exec', 'k8s_logs']
        for step_type in k8s_types:
            can_execute = executor.can_execute(step_type)
            test_print(f"✅ K8s 执行器支持 {step_type}: {can_execute}", "SUCCESS" if can_execute else "ERROR")
            if not can_execute:
                return False
        
        # 测试不支持的步骤类型
        unsupported = executor.can_execute('unsupported_type')
        test_print(f"✅ K8s 执行器正确拒绝不支持的类型: {not unsupported}", "SUCCESS" if not unsupported else "ERROR")
        
        test_print("✅ Kubernetes 执行器测试通过", "SUCCESS")
        return True
        
    except Exception as e:
        test_print(f"❌ Kubernetes 执行器测试失败: {e}", "ERROR")
        return False


def test_pipeline_step_model():
    """测试 PipelineStep 模型的新字段"""
    test_print("测试 PipelineStep 模型新字段...", "INFO")
    
    try:
        # 检查模型字段是否存在
        step_fields = [field.name for field in PipelineStep._meta.get_fields()]
        
        required_fields = [
            'docker_image', 'docker_tag', 'docker_registry', 'docker_config',
            'k8s_cluster', 'k8s_namespace', 'k8s_resource_name', 'k8s_config'
        ]
        
        for field_name in required_fields:
            if field_name in step_fields:
                test_print(f"✅ 字段 {field_name} 存在", "SUCCESS")
            else:
                test_print(f"❌ 字段 {field_name} 缺失", "ERROR")
                return False
        
        test_print("✅ PipelineStep 模型字段验证通过", "SUCCESS")
        return True
        
    except Exception as e:
        test_print(f"❌ PipelineStep 模型测试失败: {e}", "ERROR")
        return False


def test_create_sample_steps():
    """测试创建示例步骤"""
    test_print("测试创建示例流水线步骤...", "INFO")
    
    try:
        from django.contrib.auth.models import User
        from project_management.models import Project
        
        # 创建测试用户和项目
        user, _ = User.objects.get_or_create(
            username='test_pipeline_user',
            defaults={'email': 'test@example.com'}
        )
        
        project, _ = Project.objects.get_or_create(
            name='Test Pipeline Project',
            defaults={
                'description': 'Test project for pipeline steps',
                'created_by': user
            }
        )
        
        # 创建测试流水线
        pipeline, _ = Pipeline.objects.get_or_create(
            name='Docker-K8s Integration Test Pipeline',
            defaults={
                'description': 'Test pipeline with Docker and K8s steps',
                'project': project,
                'created_by': user,
                'execution_mode': 'local'
            }
        )
        
        # 清理现有步骤
        pipeline.steps.filter(name__startswith='Test ').delete()
        
        # 创建 Docker 构建步骤
        docker_build_step = PipelineStep.objects.create(
            pipeline=pipeline,
            name='Test Docker Build',
            description='Build Docker image',
            step_type='docker_build',
            order=1,
            docker_image='test-app',
            docker_tag='latest',
            docker_config={
                'dockerfile': 'Dockerfile',
                'context': '.',
                'build_args': {
                    'NODE_ENV': 'production'
                }
            }
        )
        test_print(f"✅ 创建 Docker 构建步骤: {docker_build_step.name}", "SUCCESS")
        
        # 创建 Docker 推送步骤
        docker_push_step = PipelineStep.objects.create(
            pipeline=pipeline,
            name='Test Docker Push',
            description='Push Docker image',
            step_type='docker_push',
            order=2,
            docker_image='test-app',
            docker_tag='latest',
            docker_config={
                'registry_url': 'registry.example.com',
                'username': 'testuser',
                'password': 'testpass'
            }
        )
        test_print(f"✅ 创建 Docker 推送步骤: {docker_push_step.name}", "SUCCESS")
        
        # 创建测试集群
        cluster, _ = KubernetesCluster.objects.get_or_create(
            name='test-cluster',
            defaults={
                'description': '测试集群',
                'api_server': 'https://localhost:6443',
                'auth_config': {
                    'type': 'kubeconfig',
                    'kubeconfig': 'fake-kubeconfig'
                },
                'status': 'connected'
            }
        )
        
        # 创建 K8s 部署步骤
        k8s_deploy_step = PipelineStep.objects.create(
            pipeline=pipeline,
            name='Test K8s Deploy',
            description='Deploy to Kubernetes',
            step_type='k8s_deploy',
            order=3,
            k8s_cluster=cluster,
            k8s_namespace='default',
            k8s_resource_name='test-app',
            k8s_config={
                'deployment_spec': {
                    'replicas': 2,
                    'image': '{{docker_image}}',  # 变量替换
                    'ports': [{'container_port': 8080}],
                    'environment': {
                        'NODE_ENV': 'production'
                    }
                }
            }
        )
        test_print(f"✅ 创建 K8s 部署步骤: {k8s_deploy_step.name}", "SUCCESS")
        
        # 创建 K8s 等待步骤
        k8s_wait_step = PipelineStep.objects.create(
            pipeline=pipeline,
            name='Test K8s Wait',
            description='Wait for deployment ready',
            step_type='k8s_wait',
            order=4,
            k8s_cluster=cluster,
            k8s_namespace='default',
            k8s_resource_name='test-app',
            k8s_config={
                'resource_type': 'deployment',
                'condition': 'available',
                'timeout': 300
            }
        )
        test_print(f"✅ 创建 K8s 等待步骤: {k8s_wait_step.name}", "SUCCESS")
        
        # 创建 K8s 扩缩容步骤
        k8s_scale_step = PipelineStep.objects.create(
            pipeline=pipeline,
            name='Test K8s Scale',
            description='Scale deployment',
            step_type='k8s_scale',
            order=5,
            k8s_cluster=cluster,
            k8s_namespace='default',
            k8s_resource_name='test-app',
            k8s_config={
                'replicas': 3
            }
        )
        test_print(f"✅ 创建 K8s 扩缩容步骤: {k8s_scale_step.name}", "SUCCESS")
        
        test_print(f"✅ 示例流水线创建成功，共 {pipeline.steps.count()} 个步骤", "SUCCESS")
        
        # 展示完整的流水线配置
        test_print("📋 完整流水线配置:", "INFO")
        for step in pipeline.steps.order_by('order'):
            test_print(f"  {step.order}. {step.name} ({step.step_type})", "INFO")
        
        return True
        
    except Exception as e:
        test_print(f"❌ 创建示例步骤失败: {e}", "ERROR")
        return False


def test_variable_replacement():
    """测试变量替换功能"""
    test_print("测试变量替换功能...", "INFO")
    
    try:
        from pipelines.services.docker_executor import DockerStepExecutor
        
        executor = DockerStepExecutor()
        
        # 测试字符串变量替换
        context = {
            'build_number': '123',
            'git_branch': 'main',
            'docker_image': 'my-app:latest'
        }
        
        test_string = "my-app:{{build_number}}-{{git_branch}}"
        result = executor._process_variables(test_string, context)
        expected = "my-app:123-main"
        
        if result == expected:
            test_print(f"✅ 字符串变量替换正确: {result}", "SUCCESS")
        else:
            test_print(f"❌ 字符串变量替换错误: 期望 {expected}, 得到 {result}", "ERROR")
            return False
        
        # 测试字典变量替换
        test_dict = {
            "image": "{{docker_image}}",
            "tag": "{{build_number}}",
            "env": {
                "BRANCH": "{{git_branch}}"
            }
        }
        result_dict = executor._process_variables(test_dict, context)
        expected_dict = {
            "image": "my-app:latest",
            "tag": "123", 
            "env": {
                "BRANCH": "main"
            }
        }
        
        if result_dict == expected_dict:
            test_print("✅ 字典变量替换正确", "SUCCESS")
        else:
            test_print(f"❌ 字典变量替换错误: {result_dict}", "ERROR")
            return False
        
        test_print("✅ 变量替换功能测试通过", "SUCCESS")
        return True
        
    except Exception as e:
        test_print(f"❌ 变量替换测试失败: {e}", "ERROR")
        return False


def cleanup_test_data():
    """清理测试数据"""
    test_print("清理测试数据...", "INFO")
    
    try:
        # 清理测试步骤
        PipelineStep.objects.filter(name__startswith='Test ').delete()
        
        # 清理测试流水线
        Pipeline.objects.filter(name__contains='Test Pipeline').delete()
        
        # 清理测试集群
        KubernetesCluster.objects.filter(name='test-cluster').delete()
        
        test_print("✅ 测试数据清理完成", "SUCCESS")
        
    except Exception as e:
        test_print(f"⚠️  清理测试数据时出错: {e}", "WARNING")


def main():
    """主测试函数"""
    test_print("=== Docker/K8s 流水线步骤集成测试 ===", "INFO")
    
    tests = [
        ("步骤类型", test_step_types),
        ("Docker 执行器", test_docker_executor),
        ("Kubernetes 执行器", test_kubernetes_executor),
        ("PipelineStep 模型", test_pipeline_step_model),
        ("创建示例步骤", test_create_sample_steps),
        ("变量替换", test_variable_replacement),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        test_print(f"\n--- 测试 {test_name} ---", "INFO")
        if test_func():
            passed_tests += 1
    
    # 清理测试数据
    cleanup_test_data()
    
    # 测试结果汇总
    test_print("\n=== 测试结果汇总 ===", "INFO")
    test_print(f"总测试数: {total_tests}", "INFO")
    test_print(f"通过测试: {passed_tests}", "SUCCESS" if passed_tests == total_tests else "WARNING")
    test_print(f"失败测试: {total_tests - passed_tests}", "ERROR" if passed_tests < total_tests else "INFO")
    
    if passed_tests == total_tests:
        test_print("🎉 所有测试通过！Docker/K8s 流水线步骤集成成功", "SUCCESS")
        return 0
    else:
        test_print("❌ 部分测试失败，请检查错误信息", "ERROR")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
