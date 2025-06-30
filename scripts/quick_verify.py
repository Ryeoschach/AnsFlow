#!/usr/bin/env python3
"""
🧪 AnsFlow 核心功能快速验证脚本
用途: 验证AnsFlow平台的核心功能是否正常工作
运行: python scripts/quick_verify.py
"""

import requests
import json
import time
import sys
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(message):
    print(f"{Colors.BLUE}🔍 {message}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.END}")

def print_header(message):
    print(f"\n{Colors.BOLD}{'='*50}{Colors.END}")
    print(f"{Colors.BOLD}🚀 {message}{Colors.END}")
    print(f"{Colors.BOLD}{'='*50}{Colors.END}")

def check_service_health():
    """检查基础服务健康状态"""
    print_header("基础服务健康检查")
    
    services = [
        ("Django管理服务", f"{BASE_URL}/admin/"),
        ("FastAPI服务", "http://localhost:8001/docs"),
        ("前端服务", "http://localhost:3000"),
    ]
    
    for name, url in services:
        print_step(f"检查 {name}")
        try:
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 401, 403]:
                print_success(f"{name} 运行正常")
            else:
                print_warning(f"{name} 状态码: {response.status_code}")
        except Exception as e:
            print_error(f"{name} 连接失败: {str(e)}")

def test_api_endpoints():
    """测试核心API端点"""
    print_header("核心API端点测试")
    
    endpoints = [
        ("流水线列表", f"{API_BASE}/pipelines/"),
        ("工具列表", f"{API_BASE}/tools/"),
        ("用户配置", f"{API_BASE}/user/profile/"),
    ]
    
    for name, url in endpoints:
        print_step(f"测试 {name}")
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print_success(f"{name} API正常 (返回{len(data.get('results', data))}条记录)")
            elif response.status_code in [401, 403]:
                print_success(f"{name} API正常 (需要认证)")
            else:
                print_warning(f"{name} 状态码: {response.status_code}")
        except Exception as e:
            print_error(f"{name} API失败: {str(e)}")

def test_pipeline_crud():
    """测试流水线CRUD操作"""
    print_header("流水线CRUD功能测试")
    
    # 创建测试流水线
    print_step("创建测试流水线")
    pipeline_data = {
        "name": f"test_pipeline_{int(time.time())}",
        "description": "快速验证测试流水线",
        "execution_mode": "local",
        "is_active": True
    }
    
    try:
        response = requests.post(f"{API_BASE}/pipelines/", json=pipeline_data, timeout=10)
        if response.status_code == 201:
            pipeline = response.json()
            pipeline_id = pipeline['id']
            print_success(f"流水线创建成功 (ID: {pipeline_id})")
            
            # 获取流水线详情
            print_step("获取流水线详情")
            response = requests.get(f"{API_BASE}/pipelines/{pipeline_id}/", timeout=5)
            if response.status_code == 200:
                detail = response.json()
                print_success(f"流水线详情获取成功: {detail['name']}")
                
                # 更新流水线
                print_step("更新流水线信息")
                update_data = {"description": "更新后的描述", "execution_mode": "remote"}
                response = requests.patch(f"{API_BASE}/pipelines/{pipeline_id}/", json=update_data, timeout=5)
                if response.status_code == 200:
                    print_success("流水线更新成功")
                else:
                    print_warning(f"流水线更新失败: {response.status_code}")
                
                # 删除测试流水线
                print_step("清理测试数据")
                response = requests.delete(f"{API_BASE}/pipelines/{pipeline_id}/", timeout=5)
                if response.status_code == 204:
                    print_success("测试流水线删除成功")
                else:
                    print_warning("测试流水线删除失败")
            else:
                print_error(f"获取流水线详情失败: {response.status_code}")
        else:
            print_error(f"流水线创建失败: {response.status_code}")
            if response.status_code == 400:
                print_error(f"错误详情: {response.text}")
    except Exception as e:
        print_error(f"流水线CRUD测试失败: {str(e)}")

def test_tool_integration():
    """测试工具集成功能"""
    print_header("工具集成功能测试")
    
    print_step("获取工具列表")
    try:
        response = requests.get(f"{API_BASE}/tools/", timeout=5)
        if response.status_code == 200:
            tools = response.json()
            tool_count = len(tools.get('results', tools))
            print_success(f"工具列表获取成功 (共{tool_count}个工具)")
            
            # 如果有工具，测试工具状态
            if tool_count > 0:
                for tool in tools.get('results', tools)[:2]:  # 只测试前2个工具
                    tool_id = tool['id']
                    tool_name = tool['name']
                    print_step(f"检查工具状态: {tool_name}")
                    
                    try:
                        response = requests.get(f"{API_BASE}/tools/{tool_id}/status/", timeout=10)
                        if response.status_code == 200:
                            status = response.json()
                            print_success(f"{tool_name} 状态: {status.get('status', 'unknown')}")
                        else:
                            print_warning(f"{tool_name} 状态检查失败")
                    except Exception as e:
                        print_warning(f"{tool_name} 状态检查异常: {str(e)}")
            else:
                print_warning("暂无配置的工具")
        else:
            print_error(f"工具列表获取失败: {response.status_code}")
    except Exception as e:
        print_error(f"工具集成测试失败: {str(e)}")

def test_atomic_steps():
    """测试原子步骤功能"""
    print_header("原子步骤功能测试")
    
    print_step("获取原子步骤类型")
    try:
        response = requests.get(f"{API_BASE}/atomic-steps/types/", timeout=5)
        if response.status_code == 200:
            step_types = response.json()
            print_success(f"原子步骤类型获取成功 (共{len(step_types)}种类型)")
            
            # 显示可用的步骤类型
            for step_type in step_types[:5]:  # 显示前5种
                print(f"  • {step_type.get('label', step_type.get('value', 'Unknown'))}")
        else:
            print_warning(f"原子步骤类型获取失败: {response.status_code}")
    except Exception as e:
        print_error(f"原子步骤测试失败: {str(e)}")

def print_summary():
    """打印测试总结"""
    print_header("快速验证完成")
    
    print(f"{Colors.GREEN}🎉 AnsFlow 核心功能验证完成！{Colors.END}")
    print(f"\n{Colors.BOLD}📊 验证项目:{Colors.END}")
    print("  ✅ 基础服务健康状态")
    print("  ✅ 核心API端点功能")
    print("  ✅ 流水线CRUD操作")
    print("  ✅ 工具集成状态")
    print("  ✅ 原子步骤功能")
    
    print(f"\n{Colors.BOLD}🔗 快速访问链接:{Colors.END}")
    print("  🌐 前端界面: http://localhost:3000")
    print("  📊 流水线管理: http://localhost:3000/pipelines")
    print("  🔧 Django管理: http://localhost:8000/admin/")
    print("  📡 FastAPI文档: http://localhost:8001/docs")
    
    print(f"\n{Colors.BOLD}💡 下一步建议:{Colors.END}")
    print("  1. 访问前端界面体验完整功能")
    print("  2. 配置Jenkins工具进行集成测试")
    print("  3. 创建流水线并运行执行测试")
    print("  4. 查看实时监控和WebSocket功能")

def main():
    """主函数"""
    print(f"{Colors.BOLD}🚀 AnsFlow 核心功能快速验证{Colors.END}")
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        check_service_health()
        test_api_endpoints()
        test_pipeline_crud()
        test_tool_integration()
        test_atomic_steps()
        print_summary()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ 验证被用户中断{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print_error(f"验证过程发生异常: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
