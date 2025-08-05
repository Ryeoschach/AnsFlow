#!/usr/bin/env python3
"""
测试并行组API修复
"""

import sys
import os

# 添加Django项目路径
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')

import django
django.setup()

from pipelines.models import Pipeline
from pipelines.views import PipelineViewSet
from django.test import RequestFactory
from unittest.mock import Mock

def test_parallel_groups_api():
    """测试并行组API"""
    print("🔍 测试并行组API修复")
    print("=" * 40)
    
    # 创建模拟请求
    factory = RequestFactory()
    request = factory.get('/api/v1/pipelines/parallel-groups/?pipeline=2')
    
    # 模拟query_params
    request.query_params = {'pipeline': '2'}
    
    # 创建视图实例
    view = PipelineViewSet()
    view.request = request
    
    try:
        # 调用get_parallel_groups方法
        response = view.get_parallel_groups(request)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应数据: {response.data}")
        
        if response.status_code == 200:
            data = response.data
            groups = data.get('parallel_groups', [])
            print(f"\n✅ 成功！找到 {len(groups)} 个并行组")
            
            for i, group in enumerate(groups, 1):
                print(f"  并行组 {i}: {group['name']}")
                print(f"    步骤数: {len(group['steps'])}")
                for step in group['steps']:
                    print(f"      - {step['name']} (ID: {step['id']})")
            
            return True
        else:
            print(f"❌ API调用失败: {response.data}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_data():
    """验证数据库数据"""
    print("\n🔍 验证数据库数据")
    print("=" * 25)
    
    try:
        pipeline = Pipeline.objects.get(id=2)
        steps = pipeline.steps.all().order_by('order')
        
        print(f"Pipeline: {pipeline.name}")
        print(f"总步骤数: {len(steps)}")
        
        parallel_groups = set()
        for step in steps:
            print(f"  {step.name}: {step.parallel_group or 'sequential'}")
            if step.parallel_group:
                parallel_groups.add(step.parallel_group)
        
        print(f"并行组数: {len(parallel_groups)}")
        return len(parallel_groups) > 0
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 并行组API修复验证")
    print("=" * 50)
    
    # 验证数据库数据
    db_ok = test_database_data()
    
    # 测试API
    api_ok = test_parallel_groups_api()
    
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"  数据库数据: {'✅ 正常' if db_ok else '❌ 异常'}")
    print(f"  API修复: {'✅ 成功' if api_ok else '❌ 失败'}")
    
    if db_ok and api_ok:
        print("\n🎉 并行组API修复成功！")
        print("前端现在应该能正确获取并行组数据")
        return 0
    else:
        print("\n❌ 还有问题需要解决")
        return 1

if __name__ == "__main__":
    sys.exit(main())
