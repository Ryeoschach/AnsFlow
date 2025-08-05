#!/usr/bin/env python3
"""
快速检查高级工作流API端点的可用性
"""

import requests
import json
from datetime import datetime

# 后端URL配置
BACKEND_URL = "http://localhost:8000"

def check_api_endpoints():
    """检查API端点可用性"""
    
    endpoints_to_check = [
        # 基础端点
        "/api/pipelines/health/",
        "/api/pipelines/pipelines/",
        
        # 高级工作流端点
        "/api/pipelines/parallel-groups/",
        "/api/pipelines/approval-requests/", 
        "/api/pipelines/workflow-executions/",
        "/api/pipelines/step-execution-history/",
        "/api/pipelines/pipeline-mappings/",
    ]
    
    print("🔍 检查高级工作流API端点可用性...")
    print("=" * 60)
    
    results = []
    
    for endpoint in endpoints_to_check:
        url = f"{BACKEND_URL}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            
            # 对于需要认证的端点，401是正常的
            if response.status_code in [200, 401, 403]:
                status = "✅ 可用"
                available = True
            else:
                status = f"❌ 错误 ({response.status_code})"
                available = False
                
        except requests.exceptions.ConnectionError:
            status = "❌ 连接失败"
            available = False
        except requests.exceptions.Timeout:
            status = "❌ 超时"
            available = False
        except Exception as e:
            status = f"❌ 异常: {str(e)[:50]}"
            available = False
        
        results.append({
            "endpoint": endpoint,
            "url": url,
            "available": available,
            "status": status
        })
        
        print(f"{status:<15} {endpoint}")
    
    print("\n" + "=" * 60)
    
    available_count = len([r for r in results if r["available"]])
    total_count = len(results)
    
    if available_count == total_count:
        print(f"🎉 所有 {total_count} 个API端点都可用！")
        success = True
    else:
        print(f"⚠️  {available_count}/{total_count} 个API端点可用")
        success = False
    
    # 检查Django管理是否可访问
    try:
        admin_response = requests.get(f"{BACKEND_URL}/admin/", timeout=5)
        if admin_response.status_code in [200, 302]:
            print("✅ Django Admin 可访问")
        else:
            print(f"❌ Django Admin 不可访问 ({admin_response.status_code})")
    except:
        print("❌ Django Admin 连接失败")
    
    # 检查API文档是否可访问
    try:
        docs_response = requests.get(f"{BACKEND_URL}/api/schema/swagger-ui/", timeout=5)
        if docs_response.status_code == 200:
            print("✅ API文档 (Swagger) 可访问")
        else:
            print(f"❌ API文档不可访问 ({docs_response.status_code})")
    except:
        print("❌ API文档连接失败")
    
    # 保存检查结果
    report = {
        "timestamp": datetime.now().isoformat(),
        "backend_url": BACKEND_URL,
        "total_endpoints": total_count,
        "available_endpoints": available_count,
        "success_rate": f"{(available_count/total_count)*100:.1f}%",
        "details": results
    }
    
    with open("api_availability_check.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 详细报告已保存到: api_availability_check.json")
    
    return success

def main():
    print("AnsFlow 高级工作流API可用性检查")
    print("=" * 50)
    print(f"后端URL: {BACKEND_URL}")
    print()
    
    # 首先检查后端服务是否运行
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        print("✅ 后端服务正在运行")
        print()
    except:
        print("❌ 后端服务未运行或无法访问")
        print("   请确保后端服务已启动并在端口8000运行")
        print("   启动命令: cd backend/django_service && uv run python manage.py runserver")
        return False
    
    return check_api_endpoints()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 后端高级工作流API已准备就绪！")
    else:
        print("\n⚠️  请检查后端配置和服务状态")
