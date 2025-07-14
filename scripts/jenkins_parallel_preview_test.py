#!/usr/bin/env python3
"""
Jenkins并行组预览测试脚本
专门测试Jenkins流水线预览中的并行组生成
"""

import sys
import os
import requests
import json
from datetime import datetime

def test_jenkins_pipeline_preview():
    """测试Jenkins流水线预览中的并行组功能"""
    
    print("🔍 测试Jenkins流水线预览并行组功能")
    print("=" * 60)
    
    # 测试数据 - 包含明确的并行组
    test_pipeline_data = {
        "name": "并行组测试流水线",
        "description": "测试Jenkins并行组生成",
        "steps": [
            {
                "name": "代码检出",
                "type": "fetch_code",
                "order": 1,
                "parameters": {
                    "repository": "https://github.com/example/repo.git",
                    "branch": "main"
                }
            },
            {
                "name": "单元测试",
                "type": "test",
                "order": 2,
                "parallel_group": "test_group_1",
                "parameters": {
                    "test_command": "npm test"
                }
            },
            {
                "name": "集成测试", 
                "type": "test",
                "order": 2,
                "parallel_group": "test_group_1",
                "parameters": {
                    "test_command": "npm run test:integration"
                }
            },
            {
                "name": "安全扫描",
                "type": "security",
                "order": 2, 
                "parallel_group": "test_group_1",
                "parameters": {
                    "scan_type": "sast"
                }
            },
            {
                "name": "构建应用",
                "type": "build",
                "order": 3,
                "parameters": {
                    "build_tool": "docker"
                }
            },
            {
                "name": "部署测试环境",
                "type": "deploy",
                "order": 4,
                "parallel_group": "deploy_group",
                "parameters": {
                    "environment": "staging"
                }
            },
            {
                "name": "部署预览环境",
                "type": "deploy", 
                "order": 4,
                "parallel_group": "deploy_group",
                "parameters": {
                    "environment": "preview"
                }
            }
        ],
        "parallel_groups": [
            {
                "id": "test_group_1",
                "name": "测试并行组",
                "sync_policy": "wait_all",
                "timeout_seconds": 600
            },
            {
                "id": "deploy_group", 
                "name": "部署并行组",
                "sync_policy": "wait_all",
                "timeout_seconds": 300
            }
        ]
    }
    
    # 测试多个预览端点
    test_endpoints = [
        {
            "name": "pipelines/preview/",
            "url": "http://localhost:8000/api/pipelines/preview/",
            "data": {
                "steps": test_pipeline_data["steps"],
                "parallel_groups": test_pipeline_data["parallel_groups"],
                "ci_tool_type": "jenkins",
                "preview_mode": True
            }
        },
        {
            "name": "cicd_integrations/pipeline_preview/",
            "url": "http://localhost:8000/api/cicd_integrations/pipeline_preview/",
            "data": {
                "steps": test_pipeline_data["steps"],
                "parallel_groups": test_pipeline_data["parallel_groups"],
                "execution_mode": "local",
                "ci_tool_type": "jenkins",
                "preview_mode": True
            }
        }
    ]
    
    results = []
    
    for endpoint in test_endpoints:
        print(f"\n📡 测试端点: {endpoint['name']}")
        print(f"URL: {endpoint['url']}")
        
        try:
            response = requests.post(
                endpoint['url'],
                json=endpoint['data'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result_data = response.json()
                print("✅ 请求成功")
                
                # 检查响应中的Jenkins内容
                jenkins_content = ""
                if 'content' in result_data:
                    jenkins_content = result_data['content']
                elif 'jenkinsfile' in result_data:
                    jenkins_content = result_data['jenkinsfile']
                elif 'pipeline_content' in result_data:
                    jenkins_content = result_data['pipeline_content']
                else:
                    print("⚠️ 响应中没有找到Jenkins内容")
                    print(f"响应键: {list(result_data.keys())}")
                    jenkins_content = str(result_data)
                
                # 分析Jenkins内容中的并行组
                parallel_detected = analyze_jenkins_parallel_content(jenkins_content)
                
                results.append({
                    'endpoint': endpoint['name'],
                    'status': 'success',
                    'parallel_detected': parallel_detected,
                    'content_length': len(jenkins_content),
                    'jenkins_content': jenkins_content[:500] + "..." if len(jenkins_content) > 500 else jenkins_content
                })
                
            else:
                print(f"❌ 请求失败: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"错误信息: {error_data}")
                except:
                    print(f"错误信息: {response.text[:200]}")
                
                results.append({
                    'endpoint': endpoint['name'],
                    'status': 'failed',
                    'status_code': response.status_code,
                    'error': response.text[:200]
                })
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            results.append({
                'endpoint': endpoint['name'],
                'status': 'error',
                'error': str(e)
            })
    
    # 生成测试报告
    generate_test_report(results, test_pipeline_data)
    
    return results

def analyze_jenkins_parallel_content(content):
    """分析Jenkins内容中的并行组"""
    parallel_info = {
        'has_parallel_keyword': False,
        'parallel_blocks_count': 0,
        'parallel_stages': [],
        'analysis': []
    }
    
    if not content:
        parallel_info['analysis'].append("❌ 内容为空")
        return parallel_info
    
    content_lower = content.lower()
    
    # 检查是否包含parallel关键字
    if 'parallel' in content_lower:
        parallel_info['has_parallel_keyword'] = True
        parallel_info['analysis'].append("✅ 找到 'parallel' 关键字")
        
        # 计算parallel块的数量
        parallel_count = content_lower.count('parallel {')
        parallel_info['parallel_blocks_count'] = parallel_count
        
        if parallel_count > 0:
            parallel_info['analysis'].append(f"✅ 找到 {parallel_count} 个并行块")
        else:
            parallel_info['analysis'].append("⚠️ 有parallel关键字但没有并行块结构")
    else:
        parallel_info['analysis'].append("❌ 没有找到 'parallel' 关键字")
    
    # 检查stage结构
    stage_count = content_lower.count('stage(')
    parallel_info['analysis'].append(f"📊 总共找到 {stage_count} 个stage")
    
    # 查找具体的并行stage
    lines = content.split('\n')
    in_parallel_block = False
    current_parallel_stages = []
    
    for line in lines:
        line_stripped = line.strip()
        if 'parallel {' in line_stripped:
            in_parallel_block = True
            current_parallel_stages = []
        elif in_parallel_block and line_stripped == '}':
            if current_parallel_stages:
                parallel_info['parallel_stages'].extend(current_parallel_stages)
                current_parallel_stages = []
            in_parallel_block = False
        elif in_parallel_block and "'" in line_stripped and ':' in line_stripped:
            # 提取并行stage名称
            stage_name = line_stripped.split("'")[1] if "'" in line_stripped else "unknown"
            current_parallel_stages.append(stage_name)
    
    if parallel_info['parallel_stages']:
        parallel_info['analysis'].append(f"🔄 并行stages: {', '.join(parallel_info['parallel_stages'])}")
    
    return parallel_info

def generate_test_report(results, test_data):
    """生成测试报告"""
    
    print("\n" + "=" * 60)
    print("📊 Jenkins并行组预览测试报告")
    print("=" * 60)
    
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试步骤数: {len(test_data['steps'])}")
    print(f"预期并行组数: {len(test_data['parallel_groups'])}")
    
    # 统计结果
    successful_tests = [r for r in results if r['status'] == 'success']
    failed_tests = [r for r in results if r['status'] != 'success']
    
    print(f"\n📈 测试结果统计:")
    print(f"成功: {len(successful_tests)}/{len(results)}")
    print(f"失败: {len(failed_tests)}/{len(results)}")
    
    # 详细结果
    print(f"\n📋 详细结果:")
    for result in results:
        print(f"\n🔸 {result['endpoint']}:")
        
        if result['status'] == 'success':
            parallel_info = result.get('parallel_detected', {})
            print(f"  ✅ 状态: 成功")
            print(f"  📄 内容长度: {result['content_length']} 字符")
            print(f"  🔄 并行关键字: {'是' if parallel_info.get('has_parallel_keyword') else '否'}")
            print(f"  📊 并行块数量: {parallel_info.get('parallel_blocks_count', 0)}")
            
            if parallel_info.get('parallel_stages'):
                print(f"  🎯 并行stages: {', '.join(parallel_info['parallel_stages'])}")
            
            for analysis in parallel_info.get('analysis', []):
                print(f"      {analysis}")
                
        else:
            print(f"  ❌ 状态: {result['status']}")
            if 'status_code' in result:
                print(f"  📟 状态码: {result['status_code']}")
            if 'error' in result:
                print(f"  🚨 错误: {result['error']}")
    
    # 问题诊断
    print(f"\n🔍 问题诊断:")
    has_any_parallel = any(
        r.get('parallel_detected', {}).get('has_parallel_keyword', False) 
        for r in successful_tests
    )
    
    if not has_any_parallel:
        print("❌ 所有端点都没有生成并行Jenkins语法")
        print("   可能的原因:")
        print("   1. 后端并行组检测逻辑有问题")
        print("   2. parallel_group字段没有正确传递")
        print("   3. Jenkins生成器没有处理并行组")
        print("   4. API端点路由到了错误的处理器")
    else:
        print("✅ 至少有一个端点生成了并行语法")
    
    if not successful_tests:
        print("❌ 所有API调用都失败了")
        print("   请检查:")
        print("   1. Django服务是否正在运行")
        print("   2. API端点是否正确配置")
        print("   3. 请求数据格式是否正确")
    
    # 保存详细结果
    report_file = f"jenkins_parallel_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_time': datetime.now().isoformat(),
            'test_data': test_data,
            'results': results,
            'summary': {
                'total_tests': len(results),
                'successful_tests': len(successful_tests),
                'failed_tests': len(failed_tests),
                'has_parallel_output': has_any_parallel
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 详细报告已保存到: {report_file}")
    print("=" * 60)

def main():
    """主函数"""
    try:
        print("🚀 开始Jenkins并行组预览测试...")
        results = test_jenkins_pipeline_preview()
        
        # 检查是否有任何成功的并行组检测
        has_parallel = any(
            r.get('parallel_detected', {}).get('has_parallel_keyword', False) 
            for r in results if r['status'] == 'success'
        )
        
        if has_parallel:
            print("\n🎉 测试完成：检测到并行组生成!")
            return 0
        else:
            print("\n⚠️ 测试完成：未检测到并行组生成")
            return 1
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
