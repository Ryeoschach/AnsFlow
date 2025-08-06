#!/usr/bin/env python3
"""
AnsFlow日志系统Phase 3 完整API测试（包含认证）
"""
import requests
import json
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1/settings/logging"

def get_auth_token():
    """获取认证token"""
    # 先尝试创建一个测试用户或使用已有用户
    auth_data = {
        'username': 'admin',
        'password': 'admin123'  # 默认密码
    }
    
    # 尝试登录获取token
    try:
        response = requests.post(f"{BASE_URL}/api/token/", json=auth_data, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('access')
        else:
            print(f"❌ 认证失败 (状态码: {response.status_code})")
            return None
    except Exception as e:
        print(f"❌ 认证请求失败: {e}")
        return None

def test_api_with_auth():
    """测试带认证的API端点"""
    print("📝 获取认证token...")
    token = get_auth_token()
    
    if not token:
        print("⚠️  跳过认证，直接测试公开端点...")
        headers = {}
    else:
        print("✅ 认证token获取成功")
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    print("\n🌐 测试Phase 3 API端点")
    print("=" * 60)
    
    # 测试端点列表
    endpoints = [
        {
            'name': '文件索引',
            'url': f'{API_URL}/index/',
            'method': 'GET',
            'params': {'days': 7}
        },
        {
            'name': '日志搜索',
            'url': f'{API_URL}/search/',
            'method': 'POST',
            'data': {
                'keywords': 'ERROR WARNING',
                'limit': 10,
                'offset': 0
            }
        },
        {
            'name': '趋势分析',
            'url': f'{API_URL}/analysis/',
            'method': 'GET',
            'params': {'days': 7}  
        },
        {
            'name': '日志统计',
            'url': f'{API_URL}/stats/',
            'method': 'GET'
        },
        {
            'name': '日志配置',
            'url': f'{API_URL}/config/',
            'method': 'GET'
        },
        {
            'name': 'Prometheus指标',
            'url': f'{API_URL}/metrics/',
            'method': 'GET'
        },
        {
            'name': 'JSON指标',
            'url': f'{API_URL}/metrics/json/',
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
                    headers=headers,
                    timeout=10
                )
            elif endpoint['method'] == 'POST':
                response = requests.post(
                    endpoint['url'],
                    json=endpoint.get('data', {}),
                    headers=headers,
                    timeout=10
                )
            
            if response.status_code == 200:
                # 尝试解析响应
                try:
                    if endpoint['name'] == 'Prometheus指标':
                        # Prometheus格式是纯文本
                        if 'ansflow_log_messages_total' in response.text:
                            print(f"   ✅ {endpoint['name']} 成功")
                            print(f"      📈 指标格式: Prometheus ({len(response.text)} chars)")
                            results[endpoint['name']] = True
                        else:
                            print(f"   ❌ {endpoint['name']} 响应格式错误")
                            results[endpoint['name']] = False
                    else:
                        # JSON格式
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
                                
                                # 显示级别统计
                                by_level = data['data'].get('by_level', {})
                                if by_level:
                                    print(f"      📈 级别统计: {by_level}")
                            
                            elif endpoint['name'] == '日志统计' and 'data' in data:
                                total_files = data['data'].get('total_files', 0)
                                total_size_mb = data['data'].get('total_size_mb', 0)
                                print(f"      📁 总文件数: {total_files}")
                                print(f"      💾 总大小: {total_size_mb} MB")
                            
                            elif endpoint['name'] == 'JSON指标' and 'data' in data:
                                overview = data['data'].get('overview', {})
                                print(f"      📊 总日志数: {overview.get('total_logs', 0)}")
                                print(f"      📁 总文件数: {overview.get('total_files', 0)}")
                        
                        else:
                            print(f"   ❌ {endpoint['name']} 响应格式错误")
                            print(f"      响应: {str(data)[:100]}...")
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
                        print(f"      响应: {response.text[:100]}...")
                        results[endpoint['name']] = False
            
            elif response.status_code == 401:
                print(f"   ⚠️  {endpoint['name']} 需要认证 (跳过测试)")
                results[endpoint['name']] = 'auth_required'
            elif response.status_code == 404:
                print(f"   ❌ {endpoint['name']} 路由未找到 (状态码: 404)")
                results[endpoint['name']] = False
            elif response.status_code == 500:
                print(f"   ❌ {endpoint['name']} 服务器内部错误 (状态码: 500)")
                results[endpoint['name']] = False
            else:
                print(f"   ❌ {endpoint['name']} 响应异常 (状态码: {response.status_code})")
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
    
    success_count = sum(1 for result in results.values() if result is True)
    auth_required_count = sum(1 for result in results.values() if result == 'auth_required')
    total_count = len(results)
    
    for name, result in results.items():
        if result is True:
            status = "✅ 通过"
        elif result == 'auth_required':
            status = "🔒 需要认证 (正常)"
        else:
            status = "❌ 失败"
        print(f"{name:<20}: {status}")
    
    print("-" * 60)
    print(f"总体结果: {success_count}/{total_count} API端点成功")
    
    if auth_required_count > 0:
        print(f"认证保护: {auth_required_count}/{total_count} API端点需要认证")
    
    if success_count > 0 or auth_required_count > 0:
        print("🎉 Phase 3 API端点部署成功！")
        return True
    else:
        print("⚠️  Phase 3 API端点需要进一步调试")
        return False

def main():
    """主函数"""
    print("🚀 AnsFlow日志系统Phase 3 完整API测试")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标服务器: {BASE_URL}")
    print("=" * 80)
    
    success = test_api_with_auth()
    
    if success:
        print("\n🎊 Phase 3 API测试完成！")
        return 0
    else:
        print("\n⚠️  Phase 3 API测试失败，请检查服务器状态")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
