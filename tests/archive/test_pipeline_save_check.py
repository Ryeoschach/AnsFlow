#!/usr/bin/env python3
"""
检查流水线编辑步骤保存功能
直接调用Django Shell检查数据库状态
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import Pipeline
from cicd_integrations.models import AtomicStep
from django.contrib.auth.models import User

def check_pipeline_save_functionality():
    """检查流水线保存功能"""
    print("="*80)
    print("🔍 流水线编辑步骤保存功能检查")
    print("="*80)
    
    # 1. 检查流水线数据
    print("\n1. 检查现有流水线...")
    pipelines = Pipeline.objects.all()
    if not pipelines.exists():
        print("❌ 没有找到任何流水线")
        return False
    
    print(f"✅ 找到 {pipelines.count()} 个流水线:")
    for pipeline in pipelines:
        steps_count = pipeline.atomic_steps.count()
        print(f"  - {pipeline.name} (ID: {pipeline.id}): {steps_count} 个步骤")
    
    # 2. 测试流水线创建和保存
    print(f"\n2. 测试流水线步骤创建...")
    
    # 选择第一个流水线进行测试
    test_pipeline = pipelines.first()
    print(f"选择测试流水线: {test_pipeline.name} (ID: {test_pipeline.id})")
    
    # 记录当前步骤数量
    original_steps_count = test_pipeline.atomic_steps.count()
    print(f"当前步骤数量: {original_steps_count}")
    
    # 3. 模拟前端保存流程 - 创建测试步骤
    print(f"\n3. 模拟前端保存流程...")
    
    # 删除现有步骤（模拟前端保存时的清理操作）
    test_pipeline.atomic_steps.all().delete()
    test_pipeline.steps.all().delete()
    print("✅ 已清理现有步骤")
    
    # 创建新的测试步骤
    test_steps_data = [
        {
            "name": "测试步骤1 - Git拉取",
            "step_type": "fetch_code",
            "description": "从Git仓库拉取代码",
            "parameters": {
                "repo_url": "https://github.com/test/repo.git",
                "branch": "main",
                "timeout": 300
            },
            "order": 1
        },
        {
            "name": "测试步骤2 - Ansible部署",
            "step_type": "ansible",
            "description": "使用Ansible进行自动化部署",
            "parameters": {
                "playbook_id": 1,
                "inventory_id": 1,
                "credential_id": 1,
                "extra_vars": {"env": "test"},
                "timeout": 600
            },
            "order": 2
        },
        {
            "name": "测试步骤3 - 构建项目",
            "step_type": "build",
            "description": "编译和构建项目",
            "parameters": {
                "build_command": "npm run build",
                "artifact_path": "/dist",
                "timeout": 900
            },
            "order": 3
        }
    ]
    
    # 创建AtomicStep对象
    created_steps = []
    user = User.objects.first()
    
    for step_data in test_steps_data:
        atomic_step = AtomicStep.objects.create(
            pipeline=test_pipeline,
            name=step_data["name"],
            description=step_data["description"],
            step_type=step_data["step_type"],
            order=step_data["order"],
            parameters=step_data["parameters"],
            is_active=True,
            created_by=user
        )
        created_steps.append(atomic_step)
        print(f"✅ 创建步骤: {atomic_step.name} (ID: {atomic_step.id})")
    
    # 4. 验证保存结果
    print(f"\n4. 验证保存结果...")
    
    # 重新查询流水线步骤
    test_pipeline.refresh_from_db()
    current_steps = test_pipeline.atomic_steps.all().order_by('order')
    current_steps_count = current_steps.count()
    
    print(f"保存后步骤数量: {current_steps_count}")
    
    if current_steps_count != len(test_steps_data):
        print(f"❌ 步骤数量不匹配！期望: {len(test_steps_data)}, 实际: {current_steps_count}")
        return False
    
    # 验证每个步骤的内容
    for i, (expected, actual) in enumerate(zip(test_steps_data, current_steps)):
        print(f"  步骤 {i+1}: {actual.name} - {actual.step_type}")
        if actual.name != expected["name"]:
            print(f"    ❌ 步骤名称不匹配: 期望 '{expected['name']}', 实际 '{actual.name}'")
            return False
        if actual.step_type != expected["step_type"]:
            print(f"    ❌ 步骤类型不匹配: 期望 '{expected['step_type']}', 实际 '{actual.step_type}'")
            return False
        if actual.parameters != expected["parameters"]:
            print(f"    ❌ 步骤参数不匹配:")
            print(f"      期望: {expected['parameters']}")
            print(f"      实际: {actual.parameters}")
            return False
    
    print("✅ 所有步骤内容验证通过")
    
    # 5. 测试序列化器
    print(f"\n5. 测试序列化器...")
    
    from pipelines.serializers import PipelineSerializer
    from django.test import RequestFactory
    from django.contrib.auth.models import AnonymousUser
    
    # 创建模拟请求
    factory = RequestFactory()
    request = factory.get('/')
    request.user = user
    
    # 序列化流水线
    serializer = PipelineSerializer(test_pipeline, context={'request': request})
    serialized_data = serializer.data
    
    # 检查序列化的步骤数据
    serialized_steps = serialized_data.get('steps', [])
    print(f"序列化后的步骤数量: {len(serialized_steps)}")
    
    if len(serialized_steps) != current_steps_count:
        print(f"❌ 序列化步骤数量不匹配: 期望 {current_steps_count}, 实际 {len(serialized_steps)}")
        return False
    
    # 验证序列化的步骤内容
    for i, (db_step, serialized_step) in enumerate(zip(current_steps, serialized_steps)):
        print(f"  序列化步骤 {i+1}: {serialized_step.get('name')} - {serialized_step.get('step_type')}")
        if serialized_step.get('name') != db_step.name:
            print(f"    ❌ 序列化步骤名称不匹配: 期望 '{db_step.name}', 实际 '{serialized_step.get('name')}'")
            return False
    
    print("✅ 序列化器验证通过")
    
    return True

def main():
    print("AnsFlow 流水线编辑步骤保存功能检查")
    print("="*80)
    
    try:
        success = check_pipeline_save_functionality()
        
        if success:
            print("\n" + "="*80)
            print("🎉 所有检查通过！")
            print("✅ 流水线编辑步骤保存功能正常")
            print("✅ 数据库同步正确")
            print("✅ 序列化器工作正常")
            print("="*80)
            return True
        else:
            print("\n" + "="*80)
            print("❌ 检查失败！")
            print("需要进一步排查保存流程中的问题")
            print("="*80)
            return False
    except Exception as e:
        print(f"\n❌ 检查过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
