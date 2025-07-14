#!/usr/bin/env python3
"""
测试并行组API
"""

import sys
import os

# 设置Django环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')

import django
django.setup()

from pipelines.models import Pipeline, PipelineStep
from pipelines.views import PipelineViewSet
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import User

def test_parallel_groups_api():
    """测试并行组API"""
    print("🧪 测试并行组API")
    print("=" * 30)
    
    # 创建请求工厂
    factory = APIRequestFactory()
    
    # 创建模拟请求
    request = factory.get('/api/v1/pipelines/parallel-groups/', {'pipeline': '2'})
    
    # 创建视图实例
    view = PipelineViewSet()
    view.format_kwarg = None
    
    try:
        # 调用get_parallel_groups方法
        response = view.get_parallel_groups(request)
        
        print(f"状态码: {response.status_code}")
        print(f"响应数据: {response.data}")
        
        if response.status_code == 200:
            data = response.data
            parallel_groups = data.get('parallel_groups', [])
            total_groups = data.get('total_groups', 0)
            total_steps = data.get('total_steps', 0)
            
            print(f"\n✅ API调用成功:")
            print(f"  并行组数量: {total_groups}")
            print(f"  总步骤数: {total_steps}")
            
            for i, group in enumerate(parallel_groups):
                print(f"  并行组 {i+1}: {group['name']}")
                for step in group['steps']:
                    print(f"    - {step['name']} (ID: {step['id']})")
                    
            return total_groups > 0
        else:
            print(f"❌ API调用失败: {response.data}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database_directly():
    """直接检查数据库数据"""
    print("\n🔍 直接检查数据库数据")
    print("=" * 30)
    
    try:
        pipeline = Pipeline.objects.get(id=2)
        steps = pipeline.steps.all().order_by('order')
        
        print(f"Pipeline ID: {pipeline.id}")
        print(f"Pipeline名称: {pipeline.name}")
        print(f"步骤数量: {len(steps)}")
        
        parallel_groups = {}
        print("\n步骤详情:")
        for step in steps:
            print(f"  {step.id}: {step.name} -> parallel_group='{step.parallel_group}'")
            if step.parallel_group:
                if step.parallel_group not in parallel_groups:
                    parallel_groups[step.parallel_group] = []
                parallel_groups[step.parallel_group].append(step)
        
        print(f"\n并行组分析:")
        print(f"  检测到 {len(parallel_groups)} 个并行组")
        for group_name, group_steps in parallel_groups.items():
            print(f"  {group_name}: {len(group_steps)} 个步骤")
            for step in group_steps:
                print(f"    - {step.name}")
                
        return len(parallel_groups) > 0
        
    except Pipeline.DoesNotExist:
        print("❌ Pipeline 2 不存在")
        return False
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 AnsFlow 并行组API测试")
    print("=" * 50)
    
    # 首先检查数据库
    db_ok = check_database_directly()
    
    # 然后测试API
    if db_ok:
        api_ok = test_parallel_groups_api()
        
        print("\n" + "=" * 50)
        print("📊 测试结果汇总:")
        print(f"  数据库并行组数据: {'✅ 正常' if db_ok else '❌ 异常'}")
        print(f"  API并行组检测: {'✅ 正常' if api_ok else '❌ 异常'}")
        
        if db_ok and api_ok:
            print("\n🎉 并行组API功能完全正常！")
        else:
            print("\n❌ 仍有问题需要解决")
    else:
        print("\n❌ 数据库中没有并行组数据，跳过API测试")
