#!/usr/bin/env python3
"""
AnsFlow日志系统Phase 3 API端点测试
测试Django服务上的API端点
"""
import requests
import json
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8000/api/v1/settings/logging"

def test_api_endpoints():
    """测试Phase 3 API端点"""
    print("🌐 测试Phase 3 API端点")
    print("=" * 60)
    
    # 测试端点列表
    endpoints = [
        {
            'name': '文件索引',
            'url': f'{BASE_URL}/index/',
            'method': 'GET',
            'params': {'days': 7}
        },
        {
            'name': '日志搜索',
            'url': f'{BASE_URL}/search/',
            'method': 'POST',
            'data': {
                'keywords': 'ERROR WARNING',
                'limit': 10,
                'offset': 0
            }
        },
        {
            'name': '趋势分析',
            'url': f'{BASE_URL}/analysis/',
            'method': 'GET',
            'params': {'days': 7}
        },
        {
            'name': '日志统计',
            'url': f'{BASE_URL}/stats/',
            'method': 'GET'
        },
        {
            'name': '日志配置',
            'url': f'{BASE_URL}/config/',
            'method': 'GET'
        },
        {
            'name': 'Prometheus指标',
            'url': f'{BASE_URL}/metrics/',
            'method': 'GET'
        },
        {
            'name': 'JSON指标',
            'url': f'{BASE_URL}/metrics/json/',
            'method': 'GET'
        }
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            print(f"🔍 测试 {endpoint['name']}: {endpoint['method']} {endpoint['url']}")
            
            if endpoint['method'] == 'GET':
                response = requests.get(
                    endpoint['url'],
                    params=endpoint.get('params', {}),
                    timeout=10
                )
            elif endpoint['method'] == 'POST':
                response = requests.post(
                    endpoint['url'],
                    json=endpoint.get('data', {}),
                    timeout=10
                )
            
            if response.status_code == 200:
                # 尝试解析JSON响应
                try:
                    data = response.json()
                    if isinstance(data, dict) and data.get('success'):
                        print(f"   ✅ {endpoint['name']} 成功")
                        results[endpoint['name']] = True
                        
                        # 显示部分响应数据
                        if endpoint['name'] == '文件索引' and 'data' in data:
                            files_count = len(data['data'].get('files', []))
                            total_size = data['data'].get('total_size', 0)
                            print(f"      📁 文件数量: {files_count}")
                            print(f"      💾 总大小: {total_size} bytes")
                        
                        elif endpoint['name'] == '日志搜索' and 'data' in data:
                            logs_count = data['data'].get('total_count', 0)
                            files_searched = data['data'].get('files_searched', 0)
                            print(f"      📋 日志数量: {logs_count}")
                            print(f"      🔍 搜索文件: {files_searched}")
                        
                        elif endpoint['name'] == '趋势分析' and 'data' in data:
                            total_logs = data['data']['summary'].get('total_logs', 0)
                            files_analyzed = data['data']['summary'].get('files_analyzed', 0)
                            print(f"      📊 总日志数: {total_logs}")
                            print(f"      📁 分析文件: {files_analyzed}")
                        
                        elif endpoint['name'] == '日志统计' and 'data' in data:
                            total_files = data['data'].get('total_files', 0)
                            total_size_mb = data['data'].get('total_size_mb', 0)
                            print(f"      📁 总文件数: {total_files}")
                            print(f"      💾 总大小: {total_size_mb} MB")
                    
                    elif endpoint['name'] == 'Prometheus指标':
                        # Prometheus格式是纯文本
                        if 'ansflow_log_messages_total' in response.text:
                            print(f"   ✅ {endpoint['name']} 成功")
                            print(f"      📈 指标格式: Prometheus")
                            results[endpoint['name']] = True
                        else:
                            print(f"   ❌ {endpoint['name']} 响应格式错误")
                            results[endpoint['name']] = False
                    
                    else:
                        print(f"   ❌ {endpoint['name']} 响应格式错误")
                        results[endpoint['name']] = False
                        
                except json.JSONDecodeError:
                    if endpoint['name'] == 'Prometheus指标':
                        # Prometheus指标是纯文本，不是JSON
                        if 'ansflow_log_messages_total' in response.text:
                            print(f"   ✅ {endpoint['name']} 成功")
                            results[endpoint['name']] = True
                        else:
                            print(f"   ❌ {endpoint['name']} 响应格式错误")
                            results[endpoint['name']] = False
                    else:
                        print(f"   ❌ {endpoint['name']} JSON解析失败")
                        results[endpoint['name']] = False
            
            else:
                print(f"   ❌ {endpoint['name']} 响应异常 (状态码: {response.status_code})")
                if response.status_code == 404:
                    print(f"      路由未找到，可能URL配置有问题")
                elif response.status_code == 500:
                    print(f"      服务器内部错误")
                results[endpoint['name']] = False
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ {endpoint['name']} 连接失败 (服务器未运行?)")
            results[endpoint['name']] = False
        except requests.exceptions.Timeout:
            print(f"   ❌ {endpoint['name']} 请求超时")
            results[endpoint['name']] = False
        except Exception as e:
            print(f"   ❌ {endpoint['name']} 请求异常: {e}")
            results[endpoint['name']] = False
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 API测试总结")
    print("=" * 60)
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    for name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name:<20}: {status}")
    
    print("-" * 60)
    print(f"总体结果: {success_count}/{total_count} API端点正常")
    
    if success_count == total_count:
        print("🎉 所有API端点测试通过！")
        return True
    else:
        print("⚠️  部分API端点失败，请检查服务器配置")
        return False

def main():
    """主函数"""
    print("🚀 AnsFlow日志系统Phase 3 API测试")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标服务器: {BASE_URL}")
    print("=" * 80)
    
    success = test_api_endpoints()
    
    if success:
        print("\n🎊 Phase 3 API测试完成！所有端点工作正常")
        return 0
    else:
        print("\n⚠️  Phase 3 API测试失败，请检查服务器状态")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
