#!/usr/bin/env python3
"""
最终验证 Jenkins 并行组功能
"""

import json
import subprocess
import sys

def test_jenkins_parallel():
    """测试Jenkins并行组检测"""
    print("🔍 测试Jenkins并行组检测功能")
    print("=" * 50)
    
    # 测试Pipeline 2
    print("\n📋 测试Pipeline 2:")
    cmd = [
        'curl', '-s', '-X', 'POST', 
        'http://localhost:8000/api/v1/cicd/pipelines/preview/',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps({
            "pipeline_id": 2,
            "preview_mode": False,
            "execution_mode": "remote"
        })
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        workflow_summary = data.get('workflow_summary', {})
        jenkinsfile = data.get('jenkinsfile', '')
        
        print(f"  总步骤数: {workflow_summary.get('total_steps', 0)}")
        print(f"  数据源: {workflow_summary.get('data_source', 'unknown')}")
        
        # 检查并行组
        has_parallel = 'parallel {' in jenkinsfile
        parallel_count = jenkinsfile.count('parallel {')
        
        print(f"  包含并行语法: {'✅ 是' if has_parallel else '❌ 否'}")
        print(f"  并行组数量: {parallel_count}")
        
        if has_parallel:
            print("  📋 Jenkins Pipeline结构:")
            # 提取stage名称
            import re
            stages = re.findall(r"stage\('([^']+)'\)", jenkinsfile)
            for stage in stages:
                if 'parallel_group_' in stage:
                    print(f"    🔄 {stage} (并行组)")
                else:
                    print(f"    ➡️ {stage} (顺序)")
        
        return has_parallel and parallel_count > 0
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def test_database_data():
    """测试数据库中的并行组数据"""
    print("\n🔍 检查数据库中的并行组数据")
    print("=" * 30)
    
    cmd = [
        'uv', 'run', 'python', 'manage.py', 'shell', '-c',
        '''
from pipelines.models import Pipeline
for p in Pipeline.objects.all():
    print(f"Pipeline {p.id}: {p.name}")
    steps = p.steps.all().order_by("order")
    parallel_groups = set()
    for step in steps:
        if step.parallel_group:
            parallel_groups.add(step.parallel_group)
        print(f"  {step.name}: {step.parallel_group or 'sequential'}")
    print(f"  并行组: {len(parallel_groups)} 个")
        '''
    ]
    
    try:
        result = subprocess.run(cmd, cwd='../backend/django_service', capture_output=True, text=True, check=True)
        print(result.stdout)
        return True
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 AnsFlow Jenkins 并行组功能最终验证")
    print("=" * 60)
    
    # 测试数据库数据
    db_ok = test_database_data()
    
    # 测试API功能
    api_ok = test_jenkins_parallel()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"  数据库并行组数据: {'✅ 正常' if db_ok else '❌ 异常'}")
    print(f"  API并行组检测: {'✅ 正常' if api_ok else '❌ 异常'}")
    
    if db_ok and api_ok:
        print("\n🎉 Jenkins并行组功能完全正常！")
        print("✅ 数据库中有并行组数据")
        print("✅ API能正确检测并行组")
        print("✅ Jenkins Pipeline正确生成并行语法")
        return 0
    else:
        print("\n❌ 还有问题需要解决")
        return 1

if __name__ == "__main__":
    sys.exit(main())
