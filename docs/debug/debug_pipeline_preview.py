#!/usr/bin/env python3
"""
调试Pipeline预览功能
检查并行组转换和格式化问题
"""

import requests
import json
import sys

def test_pipeline_preview():
    """测试Pipeline预览API"""
    
    # 构造测试数据 - 包含并行组
    test_data = {
        "pipeline_id": 1,
        "preview_mode": True,
        "execution_mode": "jenkins",
        "ci_tool_type": "jenkins",
        "steps": [
            {
                "name": "获取代码",
                "step_type": "git_clone",
                "order": 1,
                "parameters": {
                    "repository_url": "https://github.com/example/repo.git",
                    "branch": "main"
                }
            },
            {
                "name": "构建项目",
                "step_type": "shell_command",
                "order": 2,
                "parameters": {
                    "command": "npm install && npm run build"
                },
                "parallel_group": "build_and_test"
            },
            {
                "name": "运行测试",
                "step_type": "test_execution",
                "order": 3,
                "parameters": {
                    "test_command": "npm test"
                },
                "parallel_group": "build_and_test"
            },
            {
                "name": "代码扫描",
                "step_type": "shell_command",
                "order": 4,
                "parameters": {
                    "command": "eslint src/"
                },
                "parallel_group": "build_and_test"
            },
            {
                "name": "部署应用",
                "step_type": "shell_command",
                "order": 5,
                "parameters": {
                    "command": "kubectl apply -f deployment.yaml"
                }
            }
        ],
        "environment": {
            "NODE_ENV": "production"
        },
        "timeout": 1800
    }
    
    # 调用API
    try:
        print("🔍 调用Pipeline预览API...")
        response = requests.post(
            "http://localhost:8000/api/v1/cicd/pipelines/preview/",
            headers={
                "Content-Type": "application/json"
            },
            json=test_data,
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n📊 API响应结构:")
            print(f"- workflow_summary: {json.dumps(result.get('workflow_summary', {}), indent=2, ensure_ascii=False)}")
            
            # 检查Jenkins Pipeline内容
            jenkinsfile = result.get('jenkinsfile') or result.get('content', '')
            print(f"\n🔧 Jenkins Pipeline 长度: {len(jenkinsfile)} 字符")
            
            if jenkinsfile:
                print("\n📝 Jenkins Pipeline 内容 (前500字符):")
                print("=" * 60)
                print(jenkinsfile[:500])
                print("=" * 60)
                
                # 检查格式化问题
                if "\\n" in jenkinsfile:
                    print("⚠️  发现格式化问题: 包含 \\n 转义字符")
                
                # 检查并行组
                if "parallel" in jenkinsfile:
                    print("✅ 包含并行组关键字")
                    parallel_count = jenkinsfile.count("parallel")
                    print(f"并行关键字出现次数: {parallel_count}")
                else:
                    print("❌ 未发现并行组")
                
                # 检查stage结构
                stage_count = jenkinsfile.count("stage(")
                print(f"Stage数量: {stage_count}")
                
            else:
                print("❌ 没有获取到Jenkins Pipeline内容")
            
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_parallel_group_analysis():
    """测试并行组分析功能"""
    print("\n🧪 测试并行组分析...")
    
    # 模拟步骤数据
    steps = [
        {
            "name": "获取代码",
            "step_type": "git_clone",
            "order": 1,
            "parallel_group": ""
        },
        {
            "name": "构建项目",
            "step_type": "shell_command", 
            "order": 2,
            "parallel_group": "build_and_test"
        },
        {
            "name": "运行测试",
            "step_type": "test_execution",
            "order": 3,
            "parallel_group": "build_and_test"
        },
        {
            "name": "代码扫描",
            "step_type": "shell_command",
            "order": 4,
            "parallel_group": "build_and_test"  
        },
        {
            "name": "部署应用",
            "step_type": "shell_command",
            "order": 5,
            "parallel_group": ""
        }
    ]
    
    try:
        # 导入并使用并行执行服务
        import django
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_service.settings')
        django.setup()
        
        from pipelines.services.parallel_execution import ParallelExecutionService
        
        parallel_service = ParallelExecutionService()
        parallel_groups = parallel_service.analyze_parallel_groups(steps)
        
        print(f"检测到并行组数量: {len(parallel_groups)}")
        for group in parallel_groups:
            print(f"- 并行组 '{group['name']}': {len(group['steps'])} 个步骤")
            for step in group['steps']:
                print(f"  - {step['name']}")
        
    except Exception as e:
        print(f"❌ 并行组分析失败: {e}")

def main():
    """主函数"""
    print("🔍 Pipeline预览调试工具")
    print("=" * 50)
    
    # 测试API调用
    test_pipeline_preview()
    
    # 测试并行组分析
    test_parallel_group_analysis()
    
    print("\n" + "=" * 50)
    print("调试完成")

if __name__ == "__main__":
    main()
