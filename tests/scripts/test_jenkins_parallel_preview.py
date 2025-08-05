#!/usr/bin/env python3
"""
测试Jenkins流水线预览中的并行组功能
验证前端发送的并行组数据能正确转换为Jenkins Pipeline的parallel语法
"""

import json
import requests
import sys
import os

# 添加Django路径
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

try:
    import django
    django.setup()
    DJANGO_AVAILABLE = True
except Exception as e:
    print(f"Django环境设置失败: {e}")
    DJANGO_AVAILABLE = False

def test_jenkins_parallel_preview_api():
    """测试Jenkins并行预览API"""
    print("=" * 80)
    print("测试Jenkins流水线预览中的并行组功能")
    print("=" * 80)
    
    # 测试数据：包含明确并行组的步骤
    test_steps = [
        {
            "id": 1,
            "name": "代码检出",
            "step_type": "fetch_code",
            "parameters": {
                "repository": "https://github.com/example/project.git",
                "branch": "main"
            },
            "order": 1,
            "description": "从Git仓库检出代码"
        },
        {
            "id": 2,
            "name": "单元测试",
            "step_type": "test",
            "parameters": {
                "test_command": "npm test",
                "coverage": True
            },
            "order": 2,
            "parallel_group": "test_group_123",  # 明确指定并行组
            "description": "运行单元测试"
        },
        {
            "id": 3,
            "name": "集成测试",
            "step_type": "test",
            "parameters": {
                "test_command": "npm run test:integration",
                "database": "postgres"
            },
            "order": 2,
            "parallel_group": "test_group_123",  # 同一个并行组
            "description": "运行集成测试"
        },
        {
            "id": 4,
            "name": "安全扫描",
            "step_type": "security",
            "parameters": {
                "scan_type": "sast",
                "tools": ["sonarqube", "snyk"]
            },
            "order": 2,
            "parallel_group": "test_group_123",  # 同一个并行组
            "description": "执行安全扫描"
        },
        {
            "id": 5,
            "name": "构建应用",
            "step_type": "build",
            "parameters": {
                "build_tool": "npm",
                "output_dir": "dist"
            },
            "order": 3,
            "description": "构建前端应用"
        },
        {
            "id": 6,
            "name": "部署测试环境",
            "step_type": "deploy",
            "parameters": {
                "environment": "staging",
                "health_check": True
            },
            "order": 4,
            "parallel_group": "deploy_group_456",  # 另一个并行组
            "description": "部署到测试环境"
        },
        {
            "id": 7,
            "name": "部署预览环境",
            "step_type": "deploy",
            "parameters": {
                "environment": "preview",
                "temporary": True
            },
            "order": 4,
            "parallel_group": "deploy_group_456",  # 同一个并行组
            "description": "部署到预览环境"
        }
    ]
    
    # API请求数据
    request_data = {
        'pipeline_id': 999,
        'steps': test_steps,
        'execution_mode': 'jenkins',
        'ci_tool_type': 'jenkins',
        'preview_mode': True,
        'environment': {'NODE_ENV': 'test'},
        'timeout': 1800
    }
    
    print(f"📝 测试步骤数据:")
    print(f"  总步骤数: {len(test_steps)}")
    print(f"  并行组: test_group_123 (3个步骤), deploy_group_456 (2个步骤)")
    print(f"  顺序步骤: 代码检出, 构建应用")
    print()
    
    if DJANGO_AVAILABLE:
        print("🔧 测试Django内部API...")
        try:
            from cicd_integrations.views.pipeline_preview import pipeline_preview
            from django.http import HttpRequest
            from django.test import RequestFactory
            
            # 创建请求对象
            factory = RequestFactory()
            request = factory.post('/api/pipeline-preview/', 
                                 data=json.dumps(request_data),
                                 content_type='application/json')
            
            # 调用API
            response = pipeline_preview(request)
            
            if response.status_code == 200:
                result = json.loads(response.content)
                print("✅ Django API调用成功")
                
                # 检查结果
                if 'jenkinsfile' in result or 'content' in result:
                    jenkinsfile = result.get('jenkinsfile') or result.get('content', '')
                    print(f"📄 生成的Jenkinsfile长度: {len(jenkinsfile)} 字符")
                    
                    # 检查是否包含parallel关键字
                    if 'parallel {' in jenkinsfile:
                        print("✅ 检测到Jenkins parallel语法")
                        
                        # 统计parallel块数量
                        parallel_count = jenkinsfile.count('parallel {')
                        print(f"📊 发现 {parallel_count} 个parallel块")
                        
                        # 输出Jenkinsfile内容（截取部分）
                        print("\n📋 生成的Jenkinsfile内容预览:")
                        print("-" * 60)
                        lines = jenkinsfile.split('\\n')
                        for i, line in enumerate(lines[:50]):  # 显示前50行
                            print(f"{i+1:2d}: {line}")
                        if len(lines) > 50:
                            print(f"... (还有 {len(lines) - 50} 行)")
                        print("-" * 60)
                        
                    else:
                        print("❌ 未检测到Jenkins parallel语法")
                        print("📋 生成的Jenkinsfile内容:")
                        print("-" * 60)
                        print(jenkinsfile[:1000])  # 显示前1000字符
                        print("-" * 60)
                
                # 检查workflow摘要
                if 'workflow_summary' in result:
                    summary = result['workflow_summary']
                    print(f"\n📊 工作流摘要:")
                    print(f"  总步骤数: {summary.get('total_steps', 0)}")
                    print(f"  并行组数: {summary.get('parallel_groups', 0)}")
                    print(f"  并行步骤数: {summary.get('parallel_steps', 0)}")
                    print(f"  预估时长: {summary.get('estimated_duration', 'N/A')}")
                    print(f"  数据来源: {summary.get('data_source', 'N/A')}")
                
            else:
                print(f"❌ Django API调用失败: {response.status_code}")
                print(f"响应内容: {response.content}")
                
        except Exception as e:
            print(f"❌ Django API测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 测试HTTP API（如果后端服务在运行）
    print(f"\n🌐 测试HTTP API...")
    try:
        api_url = "http://localhost:8000/api/pipelines/preview/"
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        response = requests.post(api_url, json=request_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ HTTP API调用成功")
            
            if 'jenkinsfile' in result or 'content' in result:
                jenkinsfile = result.get('jenkinsfile') or result.get('content', '')
                
                if 'parallel {' in jenkinsfile:
                    print("✅ HTTP API也检测到Jenkins parallel语法")
                    parallel_count = jenkinsfile.count('parallel {')
                    print(f"📊 发现 {parallel_count} 个parallel块")
                else:
                    print("❌ HTTP API未检测到Jenkins parallel语法")
            
        else:
            print(f"❌ HTTP API调用失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ HTTP API不可用: {e}")
    
    print("\n" + "=" * 80)

def test_parallel_analysis_directly():
    """直接测试并行组分析逻辑"""
    print("=" * 80)
    print("直接测试并行组分析逻辑")
    print("=" * 80)
    
    if not DJANGO_AVAILABLE:
        print("❌ Django环境不可用，跳过直接测试")
        return
    
    try:
        from pipelines.services.parallel_execution import ParallelExecutionService
        
        service = ParallelExecutionService()
        
        # 测试步骤（同上面的测试数据）
        test_steps = [
            {
                "id": 1,
                "name": "代码检出",
                "step_type": "fetch_code",
                "order": 1
            },
            {
                "id": 2,
                "name": "单元测试",
                "step_type": "test",
                "order": 2,
                "parallel_group": "test_group_123"
            },
            {
                "id": 3,
                "name": "集成测试",
                "step_type": "test",
                "order": 2,
                "parallel_group": "test_group_123"
            },
            {
                "id": 4,
                "name": "安全扫描",
                "step_type": "security",
                "order": 2,
                "parallel_group": "test_group_123"
            },
            {
                "id": 5,
                "name": "构建应用",
                "step_type": "build",
                "order": 3
            },
            {
                "id": 6,
                "name": "部署测试环境",
                "step_type": "deploy",
                "order": 4,
                "parallel_group": "deploy_group_456"
            },
            {
                "id": 7,
                "name": "部署预览环境",
                "step_type": "deploy",
                "order": 4,
                "parallel_group": "deploy_group_456"
            }
        ]
        
        print(f"📝 分析 {len(test_steps)} 个步骤...")
        
        parallel_groups = service.analyze_parallel_groups(test_steps)
        
        print(f"📊 分析结果:")
        print(f"  检测到 {len(parallel_groups)} 个并行组")
        
        for i, group in enumerate(parallel_groups, 1):
            print(f"\n  并行组 {i}:")
            print(f"    ID: {group.get('id', 'N/A')}")
            print(f"    名称: {group.get('name', 'N/A')}")
            print(f"    Order: {group.get('order', 'N/A')}")
            print(f"    步骤数: {len(group.get('steps', []))}")
            print(f"    同步策略: {group.get('sync_policy', 'N/A')}")
            
            for j, step in enumerate(group.get('steps', []), 1):
                print(f"      步骤 {j}: {step.get('name', 'N/A')} ({step.get('step_type', 'N/A')})")
        
        if len(parallel_groups) == 2:
            print("\n✅ 并行组检测正确！")
        else:
            print(f"\n❌ 并行组检测异常，期望2个，实际{len(parallel_groups)}个")
            
    except Exception as e:
        print(f"❌ 直接测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)

def main():
    """主函数"""
    print("🧪 AnsFlow Jenkins并行组预览功能测试")
    print(f"时间: {json.dumps({'timestamp': str(sys.version)})}")
    print()
    
    # 测试1: 直接分析并行组
    test_parallel_analysis_directly()
    print()
    
    # 测试2: 完整的API调用
    test_jenkins_parallel_preview_api()
    
    print("\n🎯 测试完成!")
    print("如果看到✅标记，说明并行组功能正常工作")
    print("如果看到❌标记，请检查相应的错误信息")

if __name__ == "__main__":
    main()
