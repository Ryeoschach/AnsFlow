#!/usr/bin/env python
"""
测试 Jenkins Job 配置更新功能
"""
import os
import sys
import django

# 设置 Django 环境
os.chdir('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
sys.path.insert(0, '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_service.settings')

django.setup()

from cicd_integrations.models import AtomicStep
from pipelines.models import Pipeline
from cicd_integrations.adapters.jenkins import JenkinsAdapter
from cicd_integrations.adapters import PipelineDefinition

async def test_job_update():
    """测试 Jenkins Job 配置更新"""
    
    print("=" * 60)
    print("🔄 测试 Jenkins Job 配置更新功能")
    print("=" * 60)
    
    try:
        # 查找 Integration Test Pipeline
        pipeline = Pipeline.objects.get(name="Integration Test Pipeline")
        
        # 获取原子步骤
        atomic_steps = AtomicStep.objects.filter(pipeline=pipeline).order_by('order')
        
        # 构建步骤数据
        steps_data = []
        for step in atomic_steps:
            steps_data.append({
                'name': step.name,
                'type': step.step_type,
                'parameters': step.parameters,
                'description': step.description
            })
        
        print(f"📋 流水线: {pipeline.name}")
        print(f"📦 步骤数量: {len(steps_data)}")
        
        for i, step in enumerate(steps_data):
            print(f"  {i+1}. {step['name']} ({step['type']})")
            print(f"     参数: {step['parameters']}")
        
        # 创建 Jenkins 适配器
        adapter = JenkinsAdapter(
            base_url='http://localhost:8080',
            username='admin',
            token='test-token'
        )
        
        # 构建流水线定义
        pipeline_definition = PipelineDefinition(
            name=pipeline.name,
            steps=steps_data,
            triggers={},
            environment={},
            artifacts=[],
            timeout=3600
        )
        
        print(f"\n🔧 测试 Jenkins Job 创建/更新...")
        
        # 创建/更新 Jenkins Job
        job_name = await adapter.create_pipeline(pipeline_definition)
        print(f"✅ Jenkins Job: {job_name}")
        
        # 生成最新的 Jenkinsfile 内容
        jenkinsfile = await adapter.create_pipeline_file(pipeline_definition)
        
        print(f"\n📄 最新生成的 Jenkinsfile:")
        print("=" * 40)
        print(jenkinsfile)
        print("=" * 40)
        
        # 验证关键内容
        print(f"\n🔍 内容验证:")
        
        success_checks = []
        
        if "echo helloworld" in jenkinsfile:
            print("✅ 包含 'echo helloworld' 命令")
            success_checks.append(True)
        else:
            print("❌ 缺失 'echo helloworld' 命令")
            success_checks.append(False)
            
        if "sleep 10" in jenkinsfile:
            print("✅ 包含 'sleep 10' 命令")
            success_checks.append(True)
        else:
            print("❌ 缺失 'sleep 10' 命令")
            success_checks.append(False)
            
        if "测试步骤1" in jenkinsfile and "测试步骤2" in jenkinsfile:
            print("✅ 包含正确的步骤名称")
            success_checks.append(True)
        else:
            print("❌ 步骤名称不正确")
            success_checks.append(False)
        
        # 检查是否移除了默认命令
        if "npm ci" not in jenkinsfile:
            print("✅ 已移除默认的 npm ci 命令")
            success_checks.append(True)
        else:
            print("❌ 仍包含不应该的 npm ci 命令")
            success_checks.append(False)
        
        all_passed = all(success_checks)
        
        print(f"\n🎯 测试结果: {'通过' if all_passed else '失败'}")
        
        if all_passed:
            print("\n🎉 Jenkins Job 配置更新功能正常!")
            print("您现在可以重新运行 Integration Test Pipeline，")
            print("Jenkins 中的 job 应该会包含您配置的自定义命令。")
        else:
            print("\n⚠️ 请检查配置是否正确")
        
        return all_passed
        
    except Pipeline.DoesNotExist:
        print("❌ 未找到 'Integration Test Pipeline' 流水线")
        return False
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_job_update())
    print(f"\n🎯 最终结果: {'成功' if success else '失败'}")
