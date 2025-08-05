#!/usr/bin/env python
"""
测试 Integration Test Pipeline 的 Jenkinsfile 生成
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

def test_integration_pipeline_jenkinsfile():
    """测试 Integration Test Pipeline 的 Jenkinsfile 生成"""
    
    print("=" * 60)
    print("🧪 测试 Integration Test Pipeline Jenkinsfile 生成")
    print("=" * 60)
    
    try:
        # 查找 Integration Test Pipeline
        pipeline = Pipeline.objects.get(name="Integration Test Pipeline")
        print(f"✅ 找到流水线: {pipeline.name}")
        print(f"📊 执行模式: {pipeline.execution_mode}")
        
        # 获取原子步骤
        atomic_steps = AtomicStep.objects.filter(pipeline=pipeline).order_by('order')
        print(f"📦 原子步骤数量: {atomic_steps.count()}")
        
        # 显示步骤详情
        steps_data = []
        for step in atomic_steps:
            print(f"\n🔹 步骤 {step.order}: {step.name}")
            print(f"   类型: {step.step_type}")
            print(f"   描述: {step.description}")
            print(f"   参数: {step.parameters}")
            
            steps_data.append({
                'name': step.name,
                'type': step.step_type,
                'parameters': step.parameters,
                'description': step.description
            })
        
        # 创建 Jenkins 适配器实例
        adapter = JenkinsAdapter(
            base_url='http://localhost:8080',
            username='admin',
            token='test-token'
        )
        
        # 生成 Jenkinsfile
        print(f"\n📄 生成 Jenkinsfile:")
        print("=" * 40)
        
        jenkinsfile_content = adapter._convert_atomic_steps_to_jenkinsfile(steps_data)
        
        # 完整的 Jenkinsfile 模板
        full_jenkinsfile = f"""pipeline {{
    agent any
    
    options {{
        timeout(time: 60, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }}
    
    stages {{{jenkinsfile_content}
    }}
    
    post {{
        always {{
            cleanWs()
        }}
        success {{
            echo 'Pipeline completed successfully!'
        }}
        failure {{
            echo 'Pipeline failed!'
        }}
    }}
}}"""
        
        print(full_jenkinsfile)
        print("=" * 40)
        
        # 验证关键内容
        print(f"\n🔍 验证结果:")
        
        # 检查是否包含用户自定义命令
        if "echo helloworld" in jenkinsfile_content:
            print("✅ 步骤1命令正确: echo helloworld")
        else:
            print("❌ 步骤1命令缺失: echo helloworld")
            
        if "sleep 10" in jenkinsfile_content:
            print("✅ 步骤2命令正确: sleep 10")
        else:
            print("❌ 步骤2命令缺失: sleep 10")
            
        # 检查步骤名称
        if "测试步骤1" in jenkinsfile_content:
            print("✅ 步骤1名称正确: 测试步骤1")
        else:
            print("❌ 步骤1名称错误")
            
        if "测试步骤2" in jenkinsfile_content:
            print("✅ 步骤2名称正确: 测试步骤2")
        else:
            print("❌ 步骤2名称错误")
        
        return True
        
    except Pipeline.DoesNotExist:
        print("❌ 未找到 'Integration Test Pipeline' 流水线")
        print("请检查数据库中是否存在该流水线")
        return False
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integration_pipeline_jenkinsfile()
    print(f"\n🎯 测试结果: {'通过' if success else '失败'}")
