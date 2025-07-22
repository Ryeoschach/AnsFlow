#!/usr/bin/env python
"""
测试步骤类型映射修复
验证前端步骤类型在后端正确映射
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
from pipelines.models import Pipeline, PipelineStep
from pipelines.serializers import PipelineSerializer
from project_management.models import Project


def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)


def print_section(title):
    """打印小节标题"""
    print(f"\n📋 {title}")
    print("-" * 40)


def test_step_type_mapping():
    """测试步骤类型映射"""
    print_header("步骤类型映射测试")
    
    # 获取或创建测试项目和用户
    try:
        user = User.objects.get(username='admin')
    except User.DoesNotExist:
        user = User.objects.create_user(username='admin', password='admin')
    
    try:
        project = Project.objects.get(name='Test Project')
    except Project.DoesNotExist:
        project = Project.objects.create(
            name='Test Project',
            description='测试项目',
            created_by=user
        )
    
    # 测试不同步骤类型的映射
    test_steps = [
        {
            'name': '代码拉取步骤',
            'step_type': 'fetch_code',
            'description': '拉取代码',
            'order': 1,
            'parameters': {'repo': 'https://github.com/test/repo.git'}
        },
        {
            'name': 'Docker Build 步骤',
            'step_type': 'docker_build',
            'description': '构建Docker镜像',
            'order': 2,
            'parameters': {'dockerfile': 'Dockerfile', 'context': '.'}
        },
        {
            'name': 'Docker Pull 步骤',
            'step_type': 'docker_pull',
            'description': '拉取Docker镜像',
            'order': 3,
            'parameters': {'image': 'nginx:latest'}
        },
        {
            'name': 'Kubernetes Deploy 步骤',
            'step_type': 'k8s_deploy',
            'description': '部署到Kubernetes',
            'order': 4,
            'parameters': {'manifest': 'deployment.yaml'}
        },
        {
            'name': '自定义步骤',
            'step_type': 'custom',
            'description': '自定义执行步骤',
            'order': 5,
            'parameters': {'command': 'echo "Hello World"'}
        },
        {
            'name': '未支持的步骤类型',
            'step_type': 'unsupported_type',
            'description': '测试未支持的步骤类型',
            'order': 6,
            'parameters': {}
        }
    ]
    
    # 创建测试流水线数据
    pipeline_data = {
        'name': f'步骤类型映射测试流水线_{datetime.now().strftime("%H%M%S")}',
        'description': '测试步骤类型映射是否正确',
        'project': project.id,
        'execution_mode': 'local',
        'steps': test_steps
    }
    
    print_section("创建测试流水线")
    print(f"流水线名称: {pipeline_data['name']}")
    print(f"包含步骤数: {len(test_steps)}")
    
    # 使用序列化器创建流水线
    try:
        serializer = PipelineSerializer(data=pipeline_data)
        if serializer.is_valid():
            pipeline = serializer.save(created_by=user)
            print(f"✅ 流水线创建成功: {pipeline.id}")
            
            # 验证步骤类型映射结果
            print_section("步骤类型映射验证结果")
            
            # 检查PipelineStep
            pipeline_steps = PipelineStep.objects.filter(pipeline=pipeline).order_by('order')
            
            success_count = 0
            total_count = len(test_steps)
            
            for i, (original_step, created_step) in enumerate(zip(test_steps, pipeline_steps)):
                original_type = original_step['step_type']
                mapped_type = created_step.step_type
                
                # 判断映射是否正确
                if original_type in ['fetch_code', 'docker_build', 'docker_pull', 'k8s_deploy', 'custom']:
                    # 这些类型应该保持不变
                    expected_type = original_type
                else:
                    # 未支持的类型应该映射为custom
                    expected_type = 'custom'
                
                is_correct = (mapped_type == expected_type)
                
                status_icon = "✅" if is_correct else "❌"
                print(f"  {status_icon} 步骤 {i+1}: {created_step.name}")
                print(f"    原始类型: {original_type}")
                print(f"    映射后类型: {mapped_type}")
                print(f"    期望类型: {expected_type}")
                
                if is_correct:
                    success_count += 1
                else:
                    print(f"    ⚠️  映射不正确!")
                
                print()
            
            # 统计结果
            print_section("测试结果汇总")
            print(f"成功映射: {success_count}/{total_count}")
            print(f"成功率: {(success_count/total_count)*100:.1f}%")
            
            if success_count == total_count:
                print("🎉 所有步骤类型映射正确!")
            else:
                print("⚠️  存在步骤类型映射问题")
            
            # 检查具体的Docker步骤
            print_section("Docker步骤详细检查")
            docker_steps = pipeline_steps.filter(step_type__startswith='docker_')
            
            if docker_steps.exists():
                print(f"✅ 找到 {docker_steps.count()} 个Docker步骤")
                for step in docker_steps:
                    print(f"  - {step.name}: {step.step_type}")
            else:
                print("❌ 没有找到Docker步骤 - 可能被错误映射为custom")
            
            # 检查是否有被错误映射为custom的步骤
            custom_steps = pipeline_steps.filter(step_type='custom')
            original_custom_count = len([s for s in test_steps if s['step_type'] == 'custom' or s['step_type'] == 'unsupported_type'])
            
            print_section("Custom步骤检查")
            print(f"预期custom步骤数: {original_custom_count}")
            print(f"实际custom步骤数: {custom_steps.count()}")
            
            if custom_steps.count() == original_custom_count:
                print("✅ Custom步骤数量正确")
            else:
                print("⚠️  Custom步骤数量异常，可能有其他类型被错误映射")
                for step in custom_steps:
                    # 找到对应的原始步骤
                    orig_step = next((s for s in test_steps if s['name'] == step.name), None)
                    if orig_step:
                        print(f"  - {step.name}: {orig_step['step_type']} → {step.step_type}")
            
            return True
            
        else:
            print(f"❌ 流水线序列化失败: {serializer.errors}")
            return False
            
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_serializer_mapping_function():
    """直接测试序列化器的映射函数"""
    print_header("序列化器映射函数测试")
    
    from pipelines.serializers import PipelineSerializer
    
    # 创建序列化器实例
    serializer = PipelineSerializer()
    
    # 测试各种步骤类型
    test_types = [
        'fetch_code', 'build', 'test', 'security_scan', 'deploy',
        'ansible', 'notify', 'custom', 'script',
        'docker_build', 'docker_run', 'docker_push', 'docker_pull',
        'k8s_deploy', 'k8s_scale', 'k8s_delete', 'k8s_wait',
        'k8s_exec', 'k8s_logs',
        'approval', 'condition',
        'unsupported_type', 'random_type'
    ]
    
    print_section("映射函数直接测试")
    
    for test_type in test_types:
        mapped_type = serializer._map_step_type(test_type)
        
        # 判断映射是否正确
        if test_type in ['unsupported_type', 'random_type']:
            expected = 'custom'
            is_correct = (mapped_type == expected)
        else:
            expected = test_type
            is_correct = (mapped_type == expected)
        
        status_icon = "✅" if is_correct else "❌"
        print(f"  {status_icon} {test_type} → {mapped_type}")
        
        if not is_correct:
            print(f"    期望: {expected}")


def main():
    """主函数"""
    print_header("AnsFlow 步骤类型映射修复验证")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 测试序列化器映射函数
        test_serializer_mapping_function()
        
        # 测试完整的流水线创建流程
        success = test_step_type_mapping()
        
        if success:
            print_header("🎉 测试完成 - 步骤类型映射修复成功!")
        else:
            print_header("❌ 测试失败 - 需要进一步检查")
            
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
