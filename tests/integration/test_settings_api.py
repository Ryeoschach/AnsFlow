#!/usr/bin/env python3
"""
Settings API 联调测试脚本
用于验证前端与后端 Settings API 的连接和数据交互
"""

import requests
import json
import sys
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000/api/v1"
# 需要先获取有效的 JWT token
TOKEN = "your_jwt_token_here"  # 请替换为实际的 JWT token

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_api_endpoint(method, url, data=None, description=""):
    """测试 API 端点"""
    print(f"\n=== {description} ===")
    print(f"{method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS)
        elif method == "POST":
            response = requests.post(url, headers=HEADERS, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=HEADERS, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=HEADERS)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code < 400:
            print("✅ 成功")
            try:
                result = response.json()
                if isinstance(result, dict) and 'results' in result:
                    print(f"数据条数: {len(result['results'])}")
                    print(f"总数: {result.get('count', 'N/A')}")
                elif isinstance(result, list):
                    print(f"数据条数: {len(result)}")
                else:
                    print("单条数据返回")
                return result
            except:
                print("非 JSON 响应")
                return response.text
        else:
            print("❌ 失败")
            try:
                error = response.json()
                print(f"错误信息: {error}")
            except:
                print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None

def main():
    """主测试函数"""
    print("🚀 开始 Settings API 联调测试")
    print(f"基础URL: {BASE_URL}")
    print(f"测试时间: {datetime.now()}")
    
    # 1. 测试用户管理 API
    print("\n" + "="*50)
    print("用户管理 API 测试")
    print("="*50)
    
    users = test_api_endpoint("GET", f"{BASE_URL}/settings/users/", 
                             description="获取用户列表")
    
    # 测试获取当前用户
    current_user = test_api_endpoint("GET", f"{BASE_URL}/auth/users/me/", 
                                   description="获取当前用户信息")
    
    # 2. 测试审计日志 API
    print("\n" + "="*50)
    print("审计日志 API 测试")
    print("="*50)
    
    audit_logs = test_api_endpoint("GET", f"{BASE_URL}/settings/audit-logs/", 
                                  description="获取审计日志")
    
    # 测试带参数的审计日志查询
    audit_logs_filtered = test_api_endpoint("GET", f"{BASE_URL}/settings/audit-logs/?page_size=5", 
                                           description="获取审计日志（分页）")
    
    # 3. 测试系统告警 API
    print("\n" + "="*50)
    print("系统告警 API 测试")
    print("="*50)
    
    alerts = test_api_endpoint("GET", f"{BASE_URL}/settings/system-alerts/", 
                              description="获取系统告警")
    
    # 测试创建系统告警
    alert_data = {
        "title": "API测试告警",
        "message": "这是一个API联调测试产生的告警",
        "alert_type": "info"
    }
    new_alert = test_api_endpoint("POST", f"{BASE_URL}/settings/system-alerts/", 
                                 data=alert_data, description="创建系统告警")
    
    # 4. 测试全局配置 API
    print("\n" + "="*50)
    print("全局配置 API 测试")
    print("="*50)
    
    configs = test_api_endpoint("GET", f"{BASE_URL}/settings/global-configs/", 
                               description="获取全局配置")
    
    # 测试创建全局配置
    config_data = {
        "key": "api_test_config",
        "value": "test_value",
        "description": "API联调测试配置",
        "config_type": "string",
        "category": "test"
    }
    new_config = test_api_endpoint("POST", f"{BASE_URL}/settings/global-configs/", 
                                  data=config_data, description="创建全局配置")
    
    # 5. 测试通知配置 API
    print("\n" + "="*50)
    print("通知配置 API 测试")
    print("="*50)
    
    notifications = test_api_endpoint("GET", f"{BASE_URL}/settings/notification-configs/", 
                                     description="获取通知配置")
    
    # 6. 测试备份记录 API
    print("\n" + "="*50)
    print("备份记录 API 测试")
    print("="*50)
    
    backups = test_api_endpoint("GET", f"{BASE_URL}/settings/backup-records/", 
                               description="获取备份记录")
    
    # 测试创建备份
    backup_data = {
        "backup_type": "configuration",
        "metadata": {"test": "api_test"}
    }
    new_backup = test_api_endpoint("POST", f"{BASE_URL}/settings/backup-records/", 
                                  data=backup_data, description="创建备份记录")
    
    # 7. 测试系统监控 API
    print("\n" + "="*50)
    print("系统监控 API 测试")
    print("="*50)
    
    monitoring = test_api_endpoint("GET", f"{BASE_URL}/settings/system-monitoring/", 
                                  description="获取系统监控数据")
    
    health = test_api_endpoint("GET", f"{BASE_URL}/settings/system-monitoring/health/", 
                              description="获取系统健康状态")
    
    # 8. 测试用户配置文件 API
    print("\n" + "="*50)
    print("用户配置文件 API 测试")
    print("="*50)
    
    profiles = test_api_endpoint("GET", f"{BASE_URL}/settings/user-profiles/", 
                                description="获取用户配置文件")
    
    current_profile = test_api_endpoint("GET", f"{BASE_URL}/settings/user-profiles/current/", 
                                       description="获取当前用户配置文件")
    
    print("\n" + "="*50)
    print("🎉 测试完成！")
    print("="*50)
    print("\n请检查上述测试结果，确保所有关键API都能正常工作。")
    print("如果有错误，请检查：")
    print("1. 后端服务是否正常运行")
    print("2. JWT token 是否有效")
    print("3. 数据库连接是否正常")
    print("4. API 路由配置是否正确")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        TOKEN = sys.argv[1]
        HEADERS["Authorization"] = f"Bearer {TOKEN}"
    
    if TOKEN == "your_jwt_token_here":
        print("⚠️  警告: 请提供有效的 JWT token")
        print("使用方法: python test_settings_api.py <your_jwt_token>")
        print("\n或者在脚本中修改 TOKEN 变量")
        sys.exit(1)
    
    main()
