#!/usr/bin/env python
"""
Docker 集成功能验证脚本
验证 AnsFlow 项目中 Docker 功能的完整性
"""
import os
import sys
import json
from datetime import datetime

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from django.contrib.auth.models import User
from docker_integration.models import (
    DockerRegistry, DockerImage, DockerImageVersion,
    DockerContainer, DockerContainerStats, DockerCompose
)
from pipelines.models import Pipeline, PipelineStep


def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)


def print_section(title):
    """打印小节标题"""
    print(f"\n📋 {title}")
    print("-" * 40)


def check_docker_models():
    """检查 Docker 数据模型"""
    print_section("检查 Docker 数据模型")
    
    models_info = {
        'DockerRegistry': DockerRegistry.objects.count(),
        'DockerImage': DockerImage.objects.count(),
        'DockerImageVersion': DockerImageVersion.objects.count(),
        'DockerContainer': DockerContainer.objects.count(),
        'DockerContainerStats': DockerContainerStats.objects.count(),
        'DockerCompose': DockerCompose.objects.count(),
    }
    
    for model_name, count in models_info.items():
        print(f"  ✅ {model_name}: {count} 条记录")
    
    return models_info


def check_pipeline_docker_integration():
    """检查流水线 Docker 集成"""
    print_section("检查流水线 Docker 集成")
    
    # 检查有 Docker 配置的步骤
    docker_steps = PipelineStep.objects.filter(
        step_type__in=['docker_build', 'docker_run', 'docker_push', 'docker_pull']
    )
    
    print(f"  ✅ Docker 步骤总数: {docker_steps.count()}")
    
    # 按类型统计
    step_types = {}
    for step in docker_steps:
        step_types[step.step_type] = step_types.get(step.step_type, 0) + 1
    
    for step_type, count in step_types.items():
        print(f"  📊 {step_type}: {count} 个步骤")
    
    # 检查有注册表关联的步骤
    steps_with_registry = PipelineStep.objects.filter(
        docker_registry__isnull=False
    ).count()
    
    print(f"  🔗 关联注册表的步骤: {steps_with_registry}")
    
    return {
        'total_docker_steps': docker_steps.count(),
        'step_types': step_types,
        'steps_with_registry': steps_with_registry
    }


def check_docker_services():
    """检查 Docker 服务"""
    print_section("检查 Docker 服务")
    
    try:
        from pipelines.services.docker_step_defaults import DockerStepDefaults
        print("  ✅ DockerStepDefaults 服务可用")
        
        # 测试获取默认配置
        for step_type in ['docker_build', 'docker_run', 'docker_push', 'docker_pull']:
            defaults = DockerStepDefaults.get_step_defaults(step_type)
            print(f"    📋 {step_type}: {len(defaults)} 个默认参数")
    except ImportError as e:
        print(f"  ❌ DockerStepDefaults 服务不可用: {e}")
    
    try:
        from pipelines.services.docker_registry_association import DockerRegistryAssociationService
        print("  ✅ DockerRegistryAssociationService 服务可用")
        
        # 测试获取可用注册表
        registries = DockerRegistryAssociationService.get_available_registries()
        print(f"    🏪 可用注册表: {len(registries)}")
        
        # 测试获取默认注册表
        default_registry = DockerRegistryAssociationService.get_default_registry()
        if default_registry:
            print(f"    🎯 默认注册表: {default_registry['name']}")
        else:
            print("    ⚠️  未设置默认注册表")
            
    except ImportError as e:
        print(f"  ❌ DockerRegistryAssociationService 服务不可用: {e}")


def check_docker_api_endpoints():
    """检查 Docker API 端点"""
    print_section("检查 Docker API 端点")
    
    # 检查 URL 配置是否存在
    try:
        from docker_integration.urls import urlpatterns
        print(f"  ✅ Docker API URL 配置: {len(urlpatterns)} 个端点")
        
        # 列出主要端点
        endpoints = [
            'registries/',
            'images/',
            'containers/',
            'compose/',
            'system/info/',
            'system/stats/'
        ]
        
        for endpoint in endpoints:
            print(f"    📡 {endpoint}")
            
    except ImportError as e:
        print(f"  ❌ Docker API URL 配置不可用: {e}")


def check_frontend_docker_components():
    """检查前端 Docker 组件"""
    print_section("检查前端 Docker 组件")
    
    frontend_files = [
        '/Users/creed/Workspace/OpenSource/ansflow/frontend/src/components/pipeline/DockerStepConfig.tsx',
        '/Users/creed/Workspace/OpenSource/ansflow/frontend/src/components/pipeline/EnhancedDockerStepConfig.tsx',
        '/Users/creed/Workspace/OpenSource/ansflow/frontend/src/hooks/useDockerStepConfig.ts',
        '/Users/creed/Workspace/OpenSource/ansflow/frontend/src/services/dockerRegistryService.ts',
        '/Users/creed/Workspace/OpenSource/ansflow/frontend/src/types/docker.ts'
    ]
    
    for file_path in frontend_files:
        if os.path.exists(file_path):
            print(f"  ✅ {os.path.basename(file_path)}")
        else:
            print(f"  ❌ {os.path.basename(file_path)} 不存在")


def check_docker_registry_status():
    """检查 Docker 注册表状态"""
    print_section("检查 Docker 注册表状态")
    
    registries = DockerRegistry.objects.all()
    
    if not registries:
        print("  ⚠️  没有配置的 Docker 注册表")
        return
    
    for registry in registries:
        status_icon = "✅" if registry.status == 'active' else "❌"
        default_icon = "⭐" if registry.is_default else ""
        
        print(f"  {status_icon} {registry.name} ({registry.registry_type})")
        print(f"    📍 URL: {registry.url}")
        print(f"    📊 状态: {registry.status} {default_icon}")
        if registry.description:
            print(f"    📝 描述: {registry.description}")


def generate_summary_report():
    """生成总结报告"""
    print_header("Docker 功能集成总结报告")
    
    # 检查各个模块
    models_info = check_docker_models()
    pipeline_info = check_pipeline_docker_integration()
    check_docker_services()
    check_docker_api_endpoints()
    check_frontend_docker_components()
    check_docker_registry_status()
    
    # 生成总结
    print_section("功能完成度评估")
    
    completion_score = 0
    total_features = 8
    
    # 评估各项功能
    if models_info['DockerRegistry'] > 0:
        print("  ✅ Docker 注册表配置")
        completion_score += 1
    else:
        print("  ❌ Docker 注册表配置")
    
    if pipeline_info['total_docker_steps'] > 0:
        print("  ✅ Docker 流水线步骤")
        completion_score += 1
    else:
        print("  ❌ Docker 流水线步骤")
    
    if pipeline_info['steps_with_registry'] > 0:
        print("  ✅ 步骤-注册表关联")
        completion_score += 1
    else:
        print("  ❌ 步骤-注册表关联")
    
    # 检查服务是否可用
    try:
        from pipelines.services.docker_step_defaults import DockerStepDefaults
        print("  ✅ Docker 步骤默认参数服务")
        completion_score += 1
    except:
        print("  ❌ Docker 步骤默认参数服务")
    
    try:
        from pipelines.services.docker_registry_association import DockerRegistryAssociationService
        print("  ✅ Docker 注册表关联服务")
        completion_score += 1
    except:
        print("  ❌ Docker 注册表关联服务")
    
    # 检查前端组件
    frontend_files = [
        '/Users/creed/Workspace/OpenSource/ansflow/frontend/src/components/pipeline/EnhancedDockerStepConfig.tsx',
        '/Users/creed/Workspace/OpenSource/ansflow/frontend/src/hooks/useDockerStepConfig.ts',
        '/Users/creed/Workspace/OpenSource/ansflow/frontend/src/services/dockerRegistryService.ts'
    ]
    
    frontend_complete = all(os.path.exists(f) for f in frontend_files)
    if frontend_complete:
        print("  ✅ 前端 Docker 组件")
        completion_score += 1
    else:
        print("  ❌ 前端 Docker 组件")
    
    # API 端点
    try:
        from docker_integration.urls import urlpatterns
        print("  ✅ Docker API 端点")
        completion_score += 1
    except:
        print("  ❌ Docker API 端点")
    
    # 执行器
    try:
        from pipelines.services.docker_executor import DockerStepExecutor
        print("  ✅ Docker 步骤执行器")
        completion_score += 1
    except:
        print("  ❌ Docker 步骤执行器")
    
    # 计算完成度
    completion_percentage = (completion_score / total_features) * 100
    
    print(f"\n📊 整体完成度: {completion_score}/{total_features} ({completion_percentage:.1f}%)")
    
    if completion_percentage >= 80:
        print("🎉 Docker 功能集成基本完成！")
    elif completion_percentage >= 60:
        print("⚡ Docker 功能大部分可用，还需要一些完善")
    else:
        print("🔧 Docker 功能需要更多开发工作")
    
    return {
        'completion_score': completion_score,
        'total_features': total_features,
        'completion_percentage': completion_percentage,
        'models_info': models_info,
        'pipeline_info': pipeline_info
    }


def main():
    """主函数"""
    print_header("AnsFlow Docker 功能集成验证")
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 运行验证
        summary = generate_summary_report()
        
        # 保存报告
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'recommendations': []
        }
        
        # 生成建议
        if summary['completion_percentage'] < 100:
            print_section("改进建议")
            
            if summary['models_info']['DockerRegistry'] == 0:
                rec = "创建默认的 Docker 注册表配置"
                report_data['recommendations'].append(rec)
                print(f"  📝 {rec}")
            
            if summary['pipeline_info']['steps_with_registry'] == 0:
                rec = "为现有 Docker 步骤关联注册表"
                report_data['recommendations'].append(rec)
                print(f"  📝 {rec}")
            
            if summary['pipeline_info']['total_docker_steps'] == 0:
                rec = "创建示例 Docker 流水线步骤"
                report_data['recommendations'].append(rec)
                print(f"  📝 {rec}")
        
        # 保存详细报告
        report_file = f"docker_integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
    except Exception as e:
        print(f"\n❌ 验证过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
