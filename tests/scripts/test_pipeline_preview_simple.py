#!/usr/bin/env python3
"""
简化的流水线预览并行组功能测试
"""

import sys
import os
import django
import json

# 设置 Django 环境
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

def test_parallel_analysis():
    """测试并行组分析功能"""
    
    print("=== 测试并行组分析功能 ===")
    
    try:
        from pipelines.services.parallel_execution import ParallelExecutionService
        
        parallel_service = ParallelExecutionService()
        
        # 测试步骤 - 包含可以并行的步骤
        test_steps = [
            {"name": "代码检出", "step_type": "fetch_code", "order": 1},
            {"name": "单元测试", "step_type": "test", "order": 2},
            {"name": "集成测试", "step_type": "test", "order": 2},
            {"name": "代码质量检查", "step_type": "test", "order": 2},
            {"name": "构建应用", "step_type": "build", "order": 3},
            {"name": "部署测试", "step_type": "deploy", "order": 4},
            {"name": "部署生产", "step_type": "deploy", "order": 4}
        ]
        
        print(f"   输入步骤: {len(test_steps)} 个")
        for step in test_steps:
            print(f"     - {step['name']} (order: {step['order']})")
        
        # 分析并行组
        parallel_groups = parallel_service.analyze_parallel_groups(test_steps)
        
        print(f"\n   ✅ 并行组分析成功")
        print(f"   🔄 找到 {len(parallel_groups)} 个并行组")
        
        for i, group in enumerate(parallel_groups):
            print(f"\n   📦 并行组 {i+1}: {group['name']}")
            print(f"      - Order: {group['order']}")
            print(f"      - 包含 {len(group['steps'])} 个步骤")
            for step in group['steps']:
                print(f"        • {step['name']} ({step['step_type']})")
                
        return parallel_groups
        
    except Exception as e:
        print(f"   ❌ 并行组分析失败: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_pipeline_preview_api():
    """测试流水线预览API"""
    
    print("\n=== 测试流水线预览API ===")
    
    try:
        from cicd_integrations.views.pipeline_preview import pipeline_preview
        from django.http import HttpRequest
        
        # 创建模拟请求
        request = HttpRequest()
        request.method = 'POST'
        
        # 测试步骤数据
        test_steps = [
            {
                "name": "代码检出",
                "step_type": "fetch_code",
                "parameters": {"repository": "https://github.com/example/repo.git"},
                "order": 1
            },
            {
                "name": "单元测试",
                "step_type": "test",
                "parameters": {"test_command": "npm test"},
                "order": 2
            },
            {
                "name": "集成测试",
                "step_type": "test",
                "parameters": {"test_command": "npm run test:integration"},
                "order": 2
            },
            {
                "name": "代码质量检查",
                "step_type": "test",
                "parameters": {"test_command": "npm run lint"},
                "order": 2
            },
            {
                "name": "构建应用",
                "step_type": "build",
                "parameters": {"build_tool": "npm"},
                "order": 3
            }
        ]
        
        request_data = {
            'pipeline_id': 123,
            'steps': test_steps,
            'execution_mode': 'local',
            'preview_mode': True,
            'ci_tool_type': 'jenkins',
            'environment': {'APP_ENV': 'test'},
            'timeout': 3600
        }
        
        request._body = json.dumps(request_data).encode('utf-8')
        
        print(f"   请求步骤数: {len(test_steps)}")
        
        # 调用预览函数
        response = pipeline_preview(request)
        
        if response.status_code == 200:
            data = json.loads(response.content)
            
            print(f"   ✅ 预览生成成功")
            print(f"   📊 总步骤数: {data['workflow_summary']['total_steps']}")
            print(f"   📊 数据来源: {data['workflow_summary'].get('data_source', 'unknown')}")
            
            # 检查并行组信息
            if 'parallel_groups' in data['workflow_summary']:
                print(f"   🔄 并行组数量: {data['workflow_summary']['parallel_groups']}")
                print(f"   🔄 并行步骤数: {data['workflow_summary']['parallel_steps']}")
            
            # 检查Jenkins Pipeline内容
            jenkins_content = data.get('content', data.get('jenkinsfile', ''))
            
            if jenkins_content:
                if 'parallel' in jenkins_content:
                    print(f"   ✅ Jenkins Pipeline包含parallel语法")
                    parallel_count = jenkins_content.count('parallel {')
                    print(f"   🔄 发现 {parallel_count} 个parallel块")
                else:
                    print(f"   ⚠️  Jenkins Pipeline未包含parallel语法")
                
                # 显示Pipeline的关键部分
                lines = jenkins_content.split('\n')
                print(f"\n   📝 Jenkins Pipeline结构:")
                
                in_stages = False
                in_parallel = False
                indent_level = 0
                
                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    
                    # 检测stages区域
                    if 'stages {' in line_stripped:
                        in_stages = True
                        print(f"      {i+1:2d}: {line}")
                        continue
                        
                    if in_stages:
                        # 检测parallel块
                        if 'parallel {' in line_stripped:
                            in_parallel = True
                            print(f"      {i+1:2d}: {line} ← 🔄 并行块开始")
                            continue
                            
                        # 检测stage
                        if 'stage(' in line_stripped:
                            marker = " ← 🔄 并行步骤" if in_parallel else " ← 📝 顺序步骤"
                            print(f"      {i+1:2d}: {line}{marker}")
                            continue
                            
                        # 检测块结束
                        if line_stripped == '}' and in_parallel:
                            print(f"      {i+1:2d}: {line} ← 🔄 并行块结束")
                            in_parallel = False
                            continue
                            
                        if line_stripped == '}' and in_stages:
                            print(f"      {i+1:2d}: {line} ← 📝 stages结束")
                            in_stages = False
                            break
            else:
                print(f"   ❌ 未生成Jenkins Pipeline内容")
                
        else:
            print(f"   ❌ 预览生成失败: {response.status_code}")
            error_content = response.content.decode()
            print(f"   错误内容: {error_content[:200]}...")
            
    except Exception as e:
        print(f"   ❌ API测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始测试流水线预览的并行组功能...\n")
    
    # 1. 测试并行组分析
    parallel_groups = test_parallel_analysis()
    
    # 2. 测试预览API
    test_pipeline_preview_api()
    
    print("\n✅ 测试完成!")
