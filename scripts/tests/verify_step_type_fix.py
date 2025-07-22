#!/usr/bin/env python
"""
简单的步骤类型映射验证脚本
验证修复后的映射函数是否正确工作
"""
import os
import sys

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

import django
django.setup()

from pipelines.serializers import PipelineSerializer


def main():
    """验证步骤类型映射"""
    print("🔍 验证步骤类型映射修复")
    print("="*50)
    
    # 创建序列化器实例
    serializer = PipelineSerializer()
    
    # 测试关键的Docker步骤类型
    docker_types = ['docker_build', 'docker_run', 'docker_push', 'docker_pull']
    k8s_types = ['k8s_deploy', 'k8s_scale', 'k8s_delete']
    
    print("\n📦 测试Docker步骤类型映射:")
    all_correct = True
    
    for step_type in docker_types:
        mapped = serializer._map_step_type(step_type)
        is_correct = (mapped == step_type)
        
        if is_correct:
            print(f"  ✅ {step_type} → {mapped}")
        else:
            print(f"  ❌ {step_type} → {mapped} (期望: {step_type})")
            all_correct = False
    
    print("\n🚢 测试Kubernetes步骤类型映射:")
    for step_type in k8s_types:
        mapped = serializer._map_step_type(step_type)
        is_correct = (mapped == step_type)
        
        if is_correct:
            print(f"  ✅ {step_type} → {mapped}")
        else:
            print(f"  ❌ {step_type} → {mapped} (期望: {step_type})")
            all_correct = False
    
    # 测试未支持类型
    print("\n⚠️  测试未支持类型映射:")
    unsupported = ['unknown_type', 'invalid_step']
    for step_type in unsupported:
        mapped = serializer._map_step_type(step_type)
        is_correct = (mapped == 'custom')
        
        if is_correct:
            print(f"  ✅ {step_type} → {mapped}")
        else:
            print(f"  ❌ {step_type} → {mapped} (期望: custom)")
            all_correct = False
    
    print("\n" + "="*50)
    if all_correct:
        print("🎉 所有步骤类型映射正确!")
        print("✅ 修复成功: Docker和Kubernetes步骤类型不会再被错误映射为custom")
        return True
    else:
        print("❌ 存在映射错误，需要进一步检查")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
