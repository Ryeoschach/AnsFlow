#!/usr/bin/env python3
"""
端到端测试各种步骤类型的保存与回显
确保所有步骤类型都能正确保存，不会被错误地映射为command
"""

import os
import sys
import json
import django
from datetime import datetime

# 设置Django环境
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth.models import User
from pipelines.models import Pipeline, PipelineStep
from pipelines.serializers import PipelineSerializer
from project_management.models import Project

class StepTypesE2ETest:
    def __init__(self):
        self.test_user = None
        self.test_project = None
        self.test_pipeline = None
        
    def setup_test_data(self):
        """创建测试所需的基础数据"""
        print("🔧 创建测试基础数据...")
        
        # 创建测试用户
        self.test_user, created = User.objects.get_or_create(
            username='test_step_types_user',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        print(f"   ✓ 测试用户: {self.test_user.username} ({'新创建' if created else '已存在'})")
        
        # 创建测试项目
        self.test_project, created = Project.objects.get_or_create(
            name='Step_Types_Test_Project',
            defaults={
                'description': '步骤类型测试项目',
                'owner': self.test_user
            }
        )
        print(f"   ✓ 测试项目: {self.test_project.name} ({'新创建' if created else '已存在'})")
        
        # 创建测试流水线
        self.test_pipeline, created = Pipeline.objects.get_or_create(
            name='Step_Types_Test_Pipeline',
            defaults={
                'description': '步骤类型测试流水线',
                'project': self.test_project,
                'created_by': self.test_user,
                'is_active': True,
                'execution_mode': 'local'
            }
        )
        print(f"   ✓ 流水线: {self.test_pipeline.name} (ID: {self.test_pipeline.id}) ({'新创建' if created else '已存在'})")
        
    def test_all_step_types(self):
        """测试所有步骤类型的保存与回显"""
        print("\n🧪 测试所有步骤类型的保存与回显...")
        
        # 定义所有前端步骤类型
        step_types = [
            {'type': 'fetch_code', 'name': '代码拉取步骤', 'params': {'repo_url': 'https://github.com/test/repo.git'}},
            {'type': 'build', 'name': '构建步骤', 'params': {'build_tool': 'maven', 'target': 'clean install'}},
            {'type': 'test', 'name': '测试步骤', 'params': {'test_framework': 'junit', 'coverage': True}},
            {'type': 'security_scan', 'name': '安全扫描步骤', 'params': {'scanner': 'sonarqube', 'quality_gate': True}},
            {'type': 'deploy', 'name': '部署步骤', 'params': {'environment': 'production', 'strategy': 'blue-green'}},
            {'type': 'notify', 'name': '通知步骤', 'params': {'channel': 'slack', 'webhook_url': 'https://hooks.slack.com/test'}},
            {'type': 'custom', 'name': '自定义步骤', 'params': {'script': 'echo "Custom step executed"'}},
        ]
        
        # 构建包含所有步骤类型的流水线数据
        steps_data = []
        for i, step_info in enumerate(step_types):
            step_data = {
                'name': step_info['name'],
                'step_type': step_info['type'],
                'description': f"测试{step_info['name']}",
                'parameters': step_info['params'],
                'order': i + 1,
                'is_active': True
            }
            steps_data.append(step_data)
        
        pipeline_update_data = {
            'name': self.test_pipeline.name,
            'description': self.test_pipeline.description,
            'project': self.test_project.id,
            'is_active': True,
            'execution_mode': 'local',
            'steps': steps_data
        }
        
        print(f"   📤 发送包含 {len(steps_data)} 个步骤的流水线数据:")
        for step in steps_data:
            print(f"      - {step['name']} (类型: {step['step_type']})")
        
        # 使用序列化器保存流水线
        serializer = PipelineSerializer(instance=self.test_pipeline, data=pipeline_update_data, partial=True)
        
        if serializer.is_valid():
            updated_pipeline = serializer.save()
            print(f"   ✓ 流水线更新成功")
            
            # 检查步骤是否正确创建
            created_steps = PipelineStep.objects.filter(pipeline=updated_pipeline).order_by('order')
            print(f"   ✓ 创建了 {created_steps.count()} 个步骤")
            
            # 验证每个步骤的类型
            print(f"   📥 验证步骤类型:")
            all_correct = True
            for i, step in enumerate(created_steps):
                expected_type = step_types[i]['type']
                actual_type = step.step_type
                is_correct = expected_type == actual_type
                status = "✓" if is_correct else "❌"
                print(f"      {status} 步骤 {i+1}: {step.name}")
                print(f"         期望类型: {expected_type}, 实际类型: {actual_type}")
                if not is_correct:
                    all_correct = False
            
            return all_correct
        else:
            print(f"   ❌ 序列化器验证失败: {serializer.errors}")
            return False
            
    def test_step_retrieval(self):
        """测试步骤的检索回显"""
        print("\n🔍 测试步骤的检索回显...")
        
        # 使用序列化器获取流水线数据
        serializer = PipelineSerializer(instance=self.test_pipeline)
        pipeline_data = serializer.data
        
        print(f"   📤 获取的流水线数据:")
        print(f"      - 流水线名称: {pipeline_data['name']}")
        print(f"      - 步骤数量: {len(pipeline_data.get('steps', []))}")
        
        if 'steps' in pipeline_data and pipeline_data['steps']:
            print(f"   📥 回显的步骤类型:")
            all_correct = True
            for i, step_data in enumerate(pipeline_data['steps']):
                print(f"      - 步骤 {i+1}: {step_data.get('name')} (类型: {step_data.get('step_type')})")
                if step_data.get('step_type') == 'command':
                    print(f"        ⚠️  警告: 步骤类型被错误地映射为command")
                    all_correct = False
            return all_correct
        else:
            print("   ❌ 未找到任何步骤")
            return False
            
    def cleanup_test_data(self):
        """清理测试数据"""
        print("\n🧹 清理测试数据...")
        
        # 删除测试步骤
        step_count = PipelineStep.objects.filter(pipeline=self.test_pipeline).count()
        PipelineStep.objects.filter(pipeline=self.test_pipeline).delete()
        print(f"   ✓ 删除了 {step_count} 个测试步骤")
        
        # 删除测试流水线
        if self.test_pipeline:
            self.test_pipeline.delete()
            print(f"   ✓ 删除测试流水线")
        
        # 删除测试项目
        if self.test_project:
            self.test_project.delete()
            print(f"   ✓ 删除测试项目")
        
        # 删除测试用户
        if self.test_user:
            self.test_user.delete()
            print(f"   ✓ 删除测试用户")
    
    def run_full_test(self):
        """运行完整的步骤类型测试"""
        print("🚀 开始步骤类型端到端测试")
        print("=" * 60)
        
        try:
            # 1. 设置测试数据
            self.setup_test_data()
            
            # 2. 测试所有步骤类型的保存
            save_success = self.test_all_step_types()
            if not save_success:
                print("❌ 步骤类型保存测试失败")
                return False
                
            # 3. 测试步骤的检索回显
            retrieval_success = self.test_step_retrieval()
            if not retrieval_success:
                print("❌ 步骤类型检索测试失败")
                return False
            
            print("\n" + "=" * 60)
            print("🎉 所有测试通过！步骤类型保存和回显功能正常")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 测试过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            # 清理测试数据
            self.cleanup_test_data()
            
if __name__ == '__main__':
    test = StepTypesE2ETest()
    success = test.run_full_test()
    
    if success:
        print("\n✅ 测试结果: 成功")
        sys.exit(0)
    else:
        print("\n❌ 测试结果: 失败")
        sys.exit(1)
