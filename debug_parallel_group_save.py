#!/usr/bin/env python3
"""
并行组步骤关联保存详细调试脚本
用于验证前端发送的数据与后端处理的完整流程
"""

import os
import sys
import json
from datetime import datetime

# 添加Django项目路径
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from pipelines.models import Pipeline, PipelineStep, AtomicStep, ParallelGroup
from pipelines.serializers import PipelineSerializer
from rest_framework.test import APIRequestFactory
from django.contrib.auth import get_user_model
from django.test import RequestFactory

User = get_user_model()

def debug_pipeline_save_process():
    """详细调试流水线保存过程"""
    print("=" * 80)
    print("🔍 并行组步骤关联保存详细调试")
    print("=" * 80)
    
    try:
        # 1. 获取测试用户
        user = User.objects.first()
        if not user:
            print("❌ 没有找到测试用户")
            return
            
        print(f"👤 使用测试用户: {user.username}")
        
        # 2. 查找现有的流水线
        pipeline = Pipeline.objects.first()
        if not pipeline:
            print("❌ 没有找到测试流水线")
            return
            
        print(f"📋 使用测试流水线: {pipeline.name} (ID: {pipeline.id})")
        
        # 3. 获取现有步骤
        existing_steps = list(pipeline.steps.all())
        existing_atomic_steps = list(pipeline.atomic_steps.all())
        
        print(f"📝 现有 PipelineStep 数量: {len(existing_steps)}")
        print(f"📝 现有 AtomicStep 数量: {len(existing_atomic_steps)}")
        
        # 显示现有步骤
        for step in existing_steps:
            print(f"  - PipelineStep: {step.name} (ID: {step.id}) - parallel_group: {step.parallel_group}")
        
        for step in existing_atomic_steps:
            print(f"  - AtomicStep: {step.name} (ID: {step.id})")
        
        # 4. 获取现有并行组
        existing_parallel_groups = list(pipeline.parallel_groups.all())
        print(f"🔗 现有并行组数量: {len(existing_parallel_groups)}")
        
        for group in existing_parallel_groups:
            print(f"  - ParallelGroup: {group.name} (ID: {group.id}) - steps: {group.steps}")
        
        # 5. 模拟前端发送的数据
        print("\n📤 模拟前端发送的更新数据...")
        
        # 构造测试数据
        test_parallel_group_id = "test_parallel_group_1"
        
        # 先确保有并行组
        parallel_group, created = ParallelGroup.objects.get_or_create(
            id=test_parallel_group_id,
            pipeline=pipeline,
            defaults={
                'name': '测试并行组',
                'steps': []
            }
        )
        
        if created:
            print(f"✅ 创建了测试并行组: {parallel_group.name}")
        else:
            print(f"📋 使用现有并行组: {parallel_group.name}")
        
        # 模拟前端发送的步骤数据
        mock_steps_data = []
        
        # 获取前两个步骤分配到并行组
        step_count = 0
        for step in existing_steps[:2]:  # 只取前两个步骤
            step_count += 1
            mock_steps_data.append({
                'id': step.id,
                'name': step.name,
                'step_type': step.step_type,
                'description': step.description or '',
                'parameters': step.ansible_parameters or {},
                'order': step_count,
                'is_active': True,
                'parallel_group': test_parallel_group_id,  # 关键：分配到并行组
                'git_credential': None
            })
        
        # 其他步骤不分配到并行组
        for step in existing_steps[2:]:
            step_count += 1
            mock_steps_data.append({
                'id': step.id,
                'name': step.name,
                'step_type': step.step_type,
                'description': step.description or '',
                'parameters': step.ansible_parameters or {},
                'order': step_count,
                'is_active': True,
                'parallel_group': '',  # 不分配到并行组
                'git_credential': None
            })
        
        # 6. 构造完整的更新数据
        update_data = {
            'name': pipeline.name,
            'description': pipeline.description,
            'project': pipeline.project_id,
            'is_active': pipeline.is_active,
            'execution_mode': pipeline.execution_mode,
            'execution_tool': pipeline.execution_tool,
            'tool_job_name': pipeline.tool_job_name,
            'tool_job_config': pipeline.tool_job_config,
            'steps': mock_steps_data
        }
        
        print(f"📊 准备保存 {len(mock_steps_data)} 个步骤:")
        for step in mock_steps_data:
            if step['parallel_group']:
                print(f"  - 步骤 {step['name']} (ID: {step['id']}) → 并行组: {step['parallel_group']}")
            else:
                print(f"  - 步骤 {step['name']} (ID: {step['id']}) → 无并行组")
        
        # 7. 使用序列化器保存数据
        print("\n💾 使用序列化器保存数据...")
        
        serializer = PipelineSerializer(pipeline, data=update_data, partial=True)
        
        if serializer.is_valid():
            print("✅ 数据验证通过")
            
            # 保存数据
            updated_pipeline = serializer.save()
            print(f"✅ 流水线更新成功: {updated_pipeline.name}")
            
            # 8. 验证保存结果
            print("\n🔍 验证保存结果...")
            
            # 重新查询步骤
            updated_steps = list(updated_pipeline.steps.all())
            updated_atomic_steps = list(updated_pipeline.atomic_steps.all())
            
            print(f"📝 更新后 PipelineStep 数量: {len(updated_steps)}")
            print(f"📝 更新后 AtomicStep 数量: {len(updated_atomic_steps)}")
            
            # 检查步骤的并行组分配
            print("\n🔗 步骤的并行组分配结果:")
            for step in updated_steps:
                if step.parallel_group:
                    print(f"  ✅ 步骤 {step.name} (ID: {step.id}) → 并行组: {step.parallel_group}")
                else:
                    print(f"  ⚪ 步骤 {step.name} (ID: {step.id}) → 无并行组")
            
            # 9. 验证并行组的步骤列表
            print("\n🔗 验证并行组的步骤列表...")
            updated_parallel_groups = list(updated_pipeline.parallel_groups.all())
            for group in updated_parallel_groups:
                print(f"  - 并行组 {group.name} (ID: {group.id}) - steps: {group.steps}")
                
                # 检查步骤列表是否正确
                if group.steps:
                    assigned_steps = [step for step in updated_steps if step.parallel_group == group.id]
                    print(f"    实际分配到该组的步骤: {[s.name for s in assigned_steps]}")
            
            # 10. 总结结果
            print("\n📊 保存结果总结:")
            successful_assignments = [step for step in updated_steps if step.parallel_group]
            print(f"✅ 成功分配到并行组的步骤: {len(successful_assignments)}")
            
            if successful_assignments:
                print("🎉 并行组步骤关联保存成功！")
                return True
            else:
                print("❌ 并行组步骤关联保存失败！")
                return False
                
        else:
            print("❌ 数据验证失败:")
            print(json.dumps(serializer.errors, indent=2, ensure_ascii=False))
            return False
            
    except Exception as e:
        print(f"❌ 调试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_model_fields():
    """检查模型字段定义"""
    print("\n🔍 检查模型字段定义...")
    
    # 检查 PipelineStep 模型
    from pipelines.models import PipelineStep
    
    print("📋 PipelineStep 模型字段:")
    for field in PipelineStep._meta.fields:
        if field.name == 'parallel_group':
            print(f"  - {field.name}: {field.__class__.__name__} (max_length: {getattr(field, 'max_length', 'N/A')}, blank: {field.blank}, null: {field.null})")
        elif 'parallel' in field.name.lower():
            print(f"  - {field.name}: {field.__class__.__name__}")
    
    # 检查 ParallelGroup 模型
    from pipelines.models import ParallelGroup
    
    print("\n🔗 ParallelGroup 模型字段:")
    for field in ParallelGroup._meta.fields:
        print(f"  - {field.name}: {field.__class__.__name__}")

if __name__ == "__main__":
    print("🚀 启动并行组步骤关联保存详细调试...")
    
    # 检查模型字段
    check_model_fields()
    
    # 执行调试
    success = debug_pipeline_save_process()
    
    if success:
        print("\n🎉 调试完成：并行组步骤关联功能正常工作！")
    else:
        print("\n❌ 调试完成：发现问题，需要进一步修复。")
