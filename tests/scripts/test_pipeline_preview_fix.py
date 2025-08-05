#!/usr/bin/env python3
"""
测试Pipeline预览修复
验证并行组转换和格式化是否正常工作
"""

import requests
import json

def test_pipeline_preview_with_parallel_groups():
    """测试包含并行组的Pipeline预览"""
    
    # 测试数据 - 包含并行组
    test_data = {
        "pipeline_id": 2,  # 使用已有的pipeline ID
        "preview_mode": False,  # 使用数据库模式
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
                },
                "parallel_group": ""
            },
            {
                "name": "构建前端",
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
                },
                "parallel_group": ""
            }
        ]
    }
    
    try:
        print("🔍 测试Pipeline预览API（包含并行组）...")
        response = requests.post(
            "http://localhost:8000/api/v1/cicd/pipelines/preview/",
            headers={
                "Content-Type": "application/json"
            },
            json=test_data,
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # 检查workflow_summary
            summary = result.get('workflow_summary', {})
            print(f"\n📊 工作流摘要:")
            print(f"- 总步骤数: {summary.get('total_steps', 0)}")
            print(f"- 并行组数: {summary.get('parallel_groups', 0)}")
            print(f"- 并行步骤数: {summary.get('parallel_steps', 0)}")
            print(f"- 数据来源: {summary.get('data_source', 'unknown')}")
            
            # 检查Jenkins Pipeline内容
            content = result.get('content') or result.get('jenkinsfile', '')
            print(f"\n🔧 Jenkins Pipeline:")
            print(f"- 内容长度: {len(content)} 字符")
            
            if content:
                print("\n📝 Jenkins Pipeline 内容:")
                print("=" * 80)
                print(content)
                print("=" * 80)
                
                # 检查关键字
                checks = {
                    "格式化": "\\n" not in content and "\n" in content,
                    "包含parallel": "parallel" in content.lower(),
                    "包含stages": "stages" in content.lower(),
                    "包含pipeline": "pipeline" in content.lower()
                }
                
                print("\n✅ 检查结果:")
                for check_name, result in checks.items():
                    status = "✅" if result else "❌"
                    print(f"  {status} {check_name}: {result}")
                
                # 统计parallel关键字出现次数
                parallel_count = content.lower().count("parallel")
                print(f"  📊 parallel关键字出现次数: {parallel_count}")
                
            else:
                print("❌ 没有获取到Jenkins Pipeline内容")
            
            return True
            
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_database_mode_vs_preview_mode():
    """测试数据库模式 vs 预览模式的差异"""
    
    print("\n🔄 测试数据库模式 vs 预览模式...")
    
    base_data = {
        "pipeline_id": 2,
        "execution_mode": "jenkins",
        "ci_tool_type": "jenkins"
    }
    
    # 测试两种模式
    modes = [
        {"preview_mode": False, "name": "数据库模式"},
        {"preview_mode": True, "name": "预览模式"}
    ]
    
    results = {}
    
    for mode in modes:
        try:
            test_data = {**base_data, **mode}
            response = requests.post(
                "http://localhost:8000/api/v1/cicd/pipelines/preview/",
                headers={"Content-Type": "application/json"},
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get('workflow_summary', {})
                content = result.get('content', '')
                
                results[mode['name']] = {
                    "total_steps": summary.get('total_steps', 0),
                    "parallel_groups": summary.get('parallel_groups', 0),
                    "content_length": len(content),
                    "has_parallel": "parallel" in content.lower()
                }
                
                print(f"\n📊 {mode['name']}:")
                print(f"  - 步骤数: {results[mode['name']]['total_steps']}")
                print(f"  - 并行组: {results[mode['name']]['parallel_groups']}")
                print(f"  - 内容长度: {results[mode['name']]['content_length']}")
                print(f"  - 包含并行: {results[mode['name']]['has_parallel']}")
            else:
                print(f"❌ {mode['name']} 失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {mode['name']} 出错: {e}")
    
    return results

def main():
    """主函数"""
    print("🧪 Pipeline预览修复验证")
    print("=" * 60)
    
    # 测试包含并行组的预览
    success = test_pipeline_preview_with_parallel_groups()
    
    # 测试不同模式
    mode_results = test_database_mode_vs_preview_mode()
    
    print("\n" + "=" * 60)
    
    if success:
        print("✅ 基本测试通过")
        
        # 比较模式结果
        if len(mode_results) == 2:
            db_mode = mode_results.get('数据库模式', {})
            preview_mode = mode_results.get('预览模式', {})
            
            if db_mode.get('parallel_groups', 0) > 0:
                print("✅ 数据库模式检测到并行组")
            else:
                print("⚠️ 数据库模式未检测到并行组")
                
            if preview_mode.get('parallel_groups', 0) > 0:
                print("✅ 预览模式检测到并行组")
            else:
                print("⚠️ 预览模式未检测到并行组")
    else:
        print("❌ 测试失败")
    
    print("\n测试完成")

if __name__ == "__main__":
    main()
